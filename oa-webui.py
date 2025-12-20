"""
Open-Automator Web UI Module
Espone API REST per gestione workflow via interfaccia web
"""

import oacommon
import inspect
import logging
import os
import yaml
import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from logger_config import AutomatorLogger
from automator import WorkflowEngine, WorkflowContext, TaskResult, TaskStatus
from taskstore import TaskResultStore
from wallet import Wallet, PlainWallet

logger = AutomatorLogger.get_logger('oa-webui')
gdict = {}

# ============= FASTAPI APP =============

app = FastAPI(
    title="Open-Automator Web UI",
    description="API per gestione workflow automation",
    version="1.0.0"
)

# CORS per sviluppo (rimuovi in produzione)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= STATE MANAGEMENT =============

class WorkflowState:
    """Gestisce lo stato dei workflow in esecuzione"""

    def __init__(self):
        self._lock = threading.Lock()
        self._workflows: Dict[str, Dict] = {}
        self._active_engines: Dict[str, WorkflowEngine] = {}

    def register_workflow(self, workflow_id: str, yaml_content: dict):
        """Registra un nuovo workflow"""
        with self._lock:
            self._workflows[workflow_id] = {
                'id': workflow_id,
                'content': yaml_content,
                'status': 'loaded',
                'created_at': datetime.now().isoformat(),
                'last_execution': None
            }

    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Recupera un workflow"""
        with self._lock:
            return self._workflows.get(workflow_id)

    def list_workflows(self):
        """Lista tutti i workflow"""
        with self._lock:
            return list(self._workflows.values())

    def set_engine(self, workflow_id: str, engine: WorkflowEngine):
        """Registra engine in esecuzione"""
        with self._lock:
            self._active_engines[workflow_id] = engine

    def get_engine(self, workflow_id: str) -> Optional[WorkflowEngine]:
        """Recupera engine attivo"""
        with self._lock:
            return self._active_engines.get(workflow_id)

workflow_state = WorkflowState()

# ============= PYDANTIC MODELS =============

class WorkflowExecuteRequest(BaseModel):
    workflow_yaml: str
    debug: bool = False
    debug2: bool = False
    variables: Optional[Dict[str, Any]] = None

class TaskStatusResponse(BaseModel):
    task_name: str
    status: str
    output: Any = None
    error: str = ""
    duration: float = 0.0
    timestamp: str

# ============= WEBSOCKET MANAGER =============

class ConnectionManager:
    """Gestisce connessioni WebSocket per aggiornamenti real-time"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, workflow_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[workflow_id] = websocket
        logger.info(f"WebSocket connected for workflow: {workflow_id}")

    def disconnect(self, workflow_id: str):
        if workflow_id in self.active_connections:
            del self.active_connections[workflow_id]
            logger.info(f"WebSocket disconnected for workflow: {workflow_id}")

    async def send_update(self, workflow_id: str, message: dict):
        """Invia aggiornamento al client"""
        if workflow_id in self.active_connections:
            try:
                await self.active_connections[workflow_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")

manager = ConnectionManager()

# ============= STATIC FILES & ROOT =============

# Servi dashboard.html come root
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve la dashboard HTML"""
    dashboard_path = os.path.join(os.getcwd(), "dashboard.html")

    if not os.path.exists(dashboard_path):
        return HTMLResponse(
            content="""
            <html>
                <head><title>Dashboard Not Found</title></head>
                <body style="font-family: Arial; padding: 50px; text-align: center;">
                    <h1>⚠️ Dashboard file not found</h1>
                    <p>Please ensure <code>dashboard.html</code> is in the current directory.</p>
                    <p>Current directory: {}</p>
                </body>
            </html>
            """.format(os.getcwd()),
            status_code=404
        )

    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return HTMLResponse(content=content)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "running",
        "service": "Open-Automator Web UI",
        "version": "1.0.0",
        "workflows_loaded": len(workflow_state.list_workflows())
    }

# ============= API ENDPOINTS =============

@app.post("/api/workflows/upload")
async def upload_workflow(file: UploadFile = File(...)):
    """
    Upload di un file YAML workflow
    """
    try:
        content = await file.read()
        yaml_content = yaml.safe_load(content.decode('utf-8'))

        # Valida struttura base
        if not yaml_content or not isinstance(yaml_content, list) or 'tasks' not in yaml_content[0]:
            raise HTTPException(400, "Invalid YAML structure - expected 'tasks' key")

        # Genera workflow ID
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Registra workflow
        workflow_state.register_workflow(workflow_id, yaml_content)

        tasks = yaml_content[0]['tasks']
        task_count = len(tasks)

        logger.info(f"Workflow uploaded: {workflow_id} ({task_count} tasks)")

        return {
            "workflow_id": workflow_id,
            "task_count": task_count,
            "status": "loaded",
            "message": f"Workflow loaded successfully with {task_count} tasks"
        }

    except yaml.YAMLError as e:
        raise HTTPException(400, f"Invalid YAML syntax: {str(e)}")
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(500, f"Upload failed: {str(e)}")

@app.get("/api/workflows")
async def list_workflows():
    """
    Lista tutti i workflow caricati
    """
    workflows = workflow_state.list_workflows()
    return {"workflows": workflows, "count": len(workflows)}

@app.get("/api/workflows/{workflow_id}")
async def get_workflow_details(workflow_id: str):
    """
    Dettagli di un workflow specifico
    """
    workflow = workflow_state.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    return workflow

@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str):
    """
    Esegue un workflow in background thread
    """
    workflow = workflow_state.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    try:
        # Prepara configurazione
        yaml_content = workflow['content']
        tasks = yaml_content[0]['tasks']
        workflow_vars = {k: v for k, v in yaml_content[0].items() if k != 'tasks'}

        # Prepara gdict
        exec_gdict = dict(gdict)
        exec_gdict.update(workflow_vars)

        # Carica wallet se disponibile
        wallet_file = os.environ.get('OA_WALLET_FILE', 'wallet.enc')
        wallet_password = os.environ.get('OA_WALLET_PASSWORD')
        if os.path.exists(wallet_file):
            try:
                if wallet_file.endswith('.enc'):
                    wallet_instance = Wallet(wallet_file, wallet_password)
                elif wallet_file.endswith('.json'):
                    wallet_instance = PlainWallet(wallet_file)
                wallet_instance.load_wallet()
                exec_gdict['_wallet'] = wallet_instance
            except Exception as e:
                logger.warning(f"Wallet load failed: {e}")

        # Crea TaskStore e Engine
        task_store = TaskResultStore()
        engine = WorkflowEngine(tasks, exec_gdict, task_store, debug=False, debug2=False)

        # Registra engine
        workflow_state.set_engine(workflow_id, engine)

        # Esegui in thread separato
        def run_workflow():
            try:
                logger.info(f"Starting workflow execution: {workflow_id}")
                success, context = engine.execute()

                # Aggiorna stato
                workflow['status'] = 'completed' if success else 'failed'
                workflow['last_execution'] = {
                    'timestamp': datetime.now().isoformat(),
                    'success': success,
                    'results': _serialize_results(context)
                }

                logger.info(f"Workflow {workflow_id} completed: {'SUCCESS' if success else 'FAILED'}")

            except Exception as e:
                logger.error(f"Workflow execution failed: {e}", exc_info=True)
                workflow['status'] = 'error'
                workflow['last_execution'] = {
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                }

        thread = threading.Thread(target=run_workflow, daemon=True)
        thread.start()

        return {
            "workflow_id": workflow_id,
            "status": "running",
            "message": "Workflow execution started"
        }

    except Exception as e:
        logger.error(f"Failed to start workflow: {e}", exc_info=True)
        raise HTTPException(500, f"Execution failed: {str(e)}")

@app.get("/api/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """
    Ottiene lo stato corrente di un workflow
    """
    workflow = workflow_state.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    engine = workflow_state.get_engine(workflow_id)

    response = {
        "workflow_id": workflow_id,
        "status": workflow['status'],
        "last_execution": workflow.get('last_execution')
    }

    # Se engine attivo, aggiungi context real-time
    if engine:
        results = _serialize_results(engine.context)
        response['current_results'] = results

    return response

@app.get("/api/workflows/{workflow_id}/results")
async def get_workflow_results(workflow_id: str):
    """
    Recupera i risultati completi di un workflow
    """
    workflow = workflow_state.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    engine = workflow_state.get_engine(workflow_id)
    if not engine:
        # Usa last_execution se disponibile
        if workflow.get('last_execution'):
            return workflow['last_execution']
        raise HTTPException(404, "No execution results available")

    # Serializza risultati da context
    results = _serialize_results(engine.context)

    return {
        "workflow_id": workflow_id,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    """
    WebSocket per aggiornamenti real-time durante l'esecuzione
    """
    await manager.connect(workflow_id, websocket)
    try:
        while True:
            # Mantieni connessione aperta
            data = await websocket.receive_text()

            # Client può richiedere status update
            if data == "get_status":
                engine = workflow_state.get_engine(workflow_id)
                if engine:
                    results = _serialize_results(engine.context)
                    await websocket.send_json({
                        "type": "status_update",
                        "results": results
                    })

    except WebSocketDisconnect:
        manager.disconnect(workflow_id)

@app.get("/api/logs/{workflow_id}")
async def get_workflow_logs(workflow_id: str):
    """
    Recupera i log di un workflow
    """
    # Implementa lettura log file se necessario
    log_dir = "./logs"
    log_file = os.path.join(log_dir, f"{workflow_id}.log")

    if os.path.exists(log_file):
        return FileResponse(log_file)
    else:
        raise HTTPException(404, "Log file not found")

# ============= HELPER FUNCTIONS =============

def _serialize_results(context: WorkflowContext) -> dict:
    """Serializza WorkflowContext per JSON response"""
    results = {}

    for name, task_result in context.get_all_results().items():
        results[name] = {
            "task_name": task_result.task_name,
            "status": task_result.status.value,
            "output": _make_serializable(task_result.output),
            "error": task_result.error,
            "duration": task_result.duration,
            "timestamp": task_result.timestamp.isoformat()
        }

    return results

def _make_serializable(obj):
    """Converte oggetti complessi in formato JSON-serializable"""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    # Fallback: converti in stringa
    return str(obj)

# ============= MODULE INTEGRATION =============

def setgdict(self, gdict_param):
    """Imposta global dict (compatibilità con altri moduli)"""
    global gdict
    gdict = gdict_param

@oacommon.trace
def start_server(self, param):
    """
    Avvia il server web UI

    Args:
        param: dict con:
            - host: indirizzo IP (default: 0.0.0.0)
            - port: porta (default: 8000)
            - reload: hot reload per sviluppo (default: False)

    Returns:
        tuple: (success, server_info)
    """
    import uvicorn

    host = param.get('host', '0.0.0.0')
    port = param.get('port', 8000)
    reload = param.get('reload', False)

    logger.info(f"Starting Web UI server on {host}:{port}")

    try:
        uvicorn.run(app, host=host, port=port, reload=reload)
        return True, {"host": host, "port": port}
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return False, {"error": str(e)}

# ============= STARTUP =============

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 Open-Automator Web UI Server")
    print("=" * 70)
    print(f"📍 Dashboard URL: http://localhost:8000")
    print(f"📍 API Docs: http://localhost:8000/docs")
    print(f"📍 Health Check: http://localhost:8000/health")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
