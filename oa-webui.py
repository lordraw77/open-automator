"""
Open-Automator Web UI Module
Espone API REST per gestione workflow via interfaccia web
CON GESTIONE WALLET INTEGRATA
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
    description="API per gestione workflow automation con Wallet",
    version="1.1.0"
)

# CORS per sviluppo
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
        with self._lock:
            self._workflows[workflow_id] = {
                'id': workflow_id,
                'content': yaml_content,
                'status': 'loaded',
                'created_at': datetime.now().isoformat(),
                'last_execution': None
            }

    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        with self._lock:
            return self._workflows.get(workflow_id)

    def list_workflows(self):
        with self._lock:
            return list(self._workflows.values())

    def set_engine(self, workflow_id: str, engine: WorkflowEngine):
        with self._lock:
            self._active_engines[workflow_id] = engine

    def get_engine(self, workflow_id: str) -> Optional[WorkflowEngine]:
        with self._lock:
            return self._active_engines.get(workflow_id)

workflow_state = WorkflowState()

# Wallet state
active_wallet = None
wallet_lock = threading.Lock()

# ============= WEBSOCKET MANAGER =============

class ConnectionManager:
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
        if workflow_id in self.active_connections:
            try:
                await self.active_connections[workflow_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")

manager = ConnectionManager()

# ============= ROOT & HEALTH =============

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    dashboard_path = os.path.join(os.getcwd(), "dashboard.html")

    if not os.path.exists(dashboard_path):
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Dashboard Not Found</title></head>
                <body style="font-family: Arial; padding: 50px; text-align: center;">
                    <h1>⚠️ Dashboard file not found</h1>
                    <p>Please ensure <code>dashboard.html</code> is in: {os.getcwd()}</p>
                </body>
            </html>
            """,
            status_code=404
        )

    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return HTMLResponse(content=content)


@app.get("/readme", response_class=HTMLResponse)
async def serve_readme():
    """Serve il file README_MODULES.html"""
    readme_path = os.path.join(os.getcwd(), "README_MODULES.html")
    if not os.path.exists(readme_path):
        return HTMLResponse(
            content=f"""
<!DOCTYPE html>
<html>
<head><title>README Not Found</title></head>
<body>
<h1>README_MODULES.html not found</h1>
<p>Please ensure <code>README_MODULES.html</code> is in: {os.getcwd()}</p>
</body>
</html>
""",
            status_code=404
        )
    return FileResponse(readme_path)

@app.get("/health")
async def health_check():
    wallet_status = "loaded" if active_wallet and active_wallet.loaded else "not_loaded"

    return {
        "status": "running",
        "service": "Open-Automator Web UI",
        "version": "1.1.0",
        "workflows_loaded": len(workflow_state.list_workflows()),
        "wallet_status": wallet_status
    }

# ============= WALLET MANAGEMENT ENDPOINTS =============

@app.get("/api/wallet/status")
async def get_wallet_status():
    """Ottiene lo stato del wallet corrente"""
    with wallet_lock:
        if active_wallet is None:
            return {
                "loaded": False,
                "message": "No wallet loaded"
            }

        return {
            "loaded": active_wallet.loaded,
            "wallet_type": "encrypted" if isinstance(active_wallet, Wallet) else "plain",
            "secrets_count": len(active_wallet.secrets) if active_wallet.loaded else 0,
            "wallet_file": active_wallet.wallet_file
        }

@app.post("/api/wallet/load")
async def load_wallet(
    wallet_file: str = Form(...),
    master_password: str = Form(None),
    wallet_type: str = Form("encrypted")
):
    """Carica un wallet esistente"""
    global active_wallet

    try:
        if not os.path.exists(wallet_file):
            raise HTTPException(404, f"Wallet file not found: {wallet_file}")

        with wallet_lock:
            if wallet_type == "encrypted":
                if not master_password:
                    raise HTTPException(400, "Master password required for encrypted wallet")

                active_wallet = Wallet(wallet_file, master_password)
                active_wallet.load_wallet(master_password)
            else:
                active_wallet = PlainWallet(wallet_file)
                active_wallet.load_wallet()

            gdict['_wallet'] = active_wallet

            logger.info(f"Wallet loaded: {wallet_file} ({len(active_wallet.secrets)} secrets)")

            return {
                "success": True,
                "message": "Wallet loaded successfully",
                "secrets_count": len(active_wallet.secrets),
                "wallet_type": wallet_type,
                "wallet_file": wallet_file
            }

    except ValueError:
        raise HTTPException(401, "Invalid master password or corrupted wallet")
    except Exception as e:
        logger.error(f"Failed to load wallet: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to load wallet: {str(e)}")

@app.post("/api/wallet/create")
async def create_wallet(
    wallet_file: str = Form(...),
    master_password: str = Form(None),
    wallet_type: str = Form("encrypted"),
    secrets: str = Form("{}")
):
    """Crea un nuovo wallet"""
    global active_wallet

    try:
        secrets_dict = json.loads(secrets)

        if os.path.exists(wallet_file):
            raise HTTPException(400, f"Wallet file already exists: {wallet_file}")

        with wallet_lock:
            if wallet_type == "encrypted":
                if not master_password:
                    raise HTTPException(400, "Master password required")

                active_wallet = Wallet(wallet_file, master_password)
                active_wallet.create_wallet(secrets_dict, master_password)
                active_wallet.load_wallet(master_password)
            else:
                with open(wallet_file, 'w') as f:
                    json.dump(secrets_dict, f, indent=2)

                active_wallet = PlainWallet(wallet_file)
                active_wallet.load_wallet()

            gdict['_wallet'] = active_wallet

            logger.info(f"Wallet created: {wallet_file} ({len(secrets_dict)} secrets)")

            return {
                "success": True,
                "message": "Wallet created and loaded successfully",
                "secrets_count": len(secrets_dict),
                "wallet_type": wallet_type,
                "wallet_file": wallet_file
            }

    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON format for secrets")
    except Exception as e:
        logger.error(f"Failed to create wallet: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to create wallet: {str(e)}")

@app.get("/api/wallet/secrets")
async def list_wallet_secrets():
    """Lista le chiavi dei segreti (senza valori)"""
    with wallet_lock:
        if active_wallet is None or not active_wallet.loaded:
            raise HTTPException(400, "No wallet loaded")

        return {
            "secrets": list(active_wallet.secrets.keys()),
            "count": len(active_wallet.secrets)
        }

@app.post("/api/wallet/secret/add")
async def add_wallet_secret(
    key: str = Form(...),
    value: str = Form(...),
    master_password: str = Form(None)
):
    """Aggiunge un nuovo secret al wallet"""
    with wallet_lock:
        if active_wallet is None or not active_wallet.loaded:
            raise HTTPException(400, "No wallet loaded")

        try:
            active_wallet.secrets[key] = value

            if isinstance(active_wallet, Wallet):
                if not master_password:
                    raise HTTPException(400, "Master password required")
                active_wallet.create_wallet(active_wallet.secrets, master_password)
            else:
                with open(active_wallet.wallet_file, 'w') as f:
                    json.dump(active_wallet.secrets, f, indent=2)

            logger.info(f"Secret added: {key}")

            return {
                "success": True,
                "message": f"Secret '{key}' added successfully",
                "secrets_count": len(active_wallet.secrets)
            }

        except Exception as e:
            logger.error(f"Failed to add secret: {e}", exc_info=True)
            raise HTTPException(500, f"Failed to add secret: {str(e)}")

@app.post("/api/wallet/secret/delete")
async def delete_wallet_secret(
    key: str = Form(...),
    master_password: str = Form(None)
):
    """Rimuove un secret dal wallet"""
    with wallet_lock:
        if active_wallet is None or not active_wallet.loaded:
            raise HTTPException(400, "No wallet loaded")

        if key not in active_wallet.secrets:
            raise HTTPException(404, f"Secret '{key}' not found")

        try:
            del active_wallet.secrets[key]

            if isinstance(active_wallet, Wallet):
                if not master_password:
                    raise HTTPException(400, "Master password required")
                active_wallet.create_wallet(active_wallet.secrets, master_password)
            else:
                with open(active_wallet.wallet_file, 'w') as f:
                    json.dump(active_wallet.secrets, f, indent=2)

            logger.info(f"Secret removed: {key}")

            return {
                "success": True,
                "message": f"Secret '{key}' removed successfully",
                "secrets_count": len(active_wallet.secrets)
            }

        except Exception as e:
            logger.error(f"Failed to remove secret: {e}", exc_info=True)
            raise HTTPException(500, f"Failed to remove secret: {str(e)}")

@app.post("/api/wallet/unload")
async def unload_wallet():
    """Scarica il wallet corrente dalla memoria"""
    global active_wallet

    with wallet_lock:
        if active_wallet is None:
            return {"success": True, "message": "No wallet was loaded"}

        active_wallet = None
        gdict['_wallet'] = None

        logger.info("Wallet unloaded")

        return {
            "success": True,
            "message": "Wallet unloaded successfully"
        }

# ============= WORKFLOW ENDPOINTS =============

@app.post("/api/workflows/upload")
async def upload_workflow(file: UploadFile = File(...)):
    try:
        content = await file.read()
        yaml_content = yaml.safe_load(content.decode('utf-8'))

        if not yaml_content or not isinstance(yaml_content, list) or 'tasks' not in yaml_content[0]:
            raise HTTPException(400, "Invalid YAML structure")

        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_state.register_workflow(workflow_id, yaml_content)

        tasks = yaml_content[0]['tasks']
        logger.info(f"Workflow uploaded: {workflow_id} ({len(tasks)} tasks)")

        return {
            "workflow_id": workflow_id,
            "task_count": len(tasks),
            "status": "loaded",
            "message": f"Workflow loaded with {len(tasks)} tasks"
        }

    except yaml.YAMLError as e:
        raise HTTPException(400, f"Invalid YAML: {str(e)}")
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(500, f"Upload failed: {str(e)}")

@app.get("/api/workflows")
async def list_workflows():
    workflows = workflow_state.list_workflows()
    return {"workflows": workflows, "count": len(workflows)}

@app.get("/api/workflows/{workflow_id}")
async def get_workflow_details(workflow_id: str):
    workflow = workflow_state.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")
    return workflow

@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str):
    workflow = workflow_state.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")
    
    try:
        yamlcontent = workflow["content"]
        
        # ✅ STEP 1: Risolvi placeholder WALLET/ENV/VAULT come fa automator.py
        if active_wallet and active_wallet.loaded:
            from wallet import resolve_dict_placeholders
            logger.info(f"Resolving WALLET/ENV/VAULT placeholders for workflow {workflow_id}")
            yamlcontent = resolve_dict_placeholders(yamlcontent, active_wallet)
            logger.debug("Placeholders resolved")
        
        tasks = yamlcontent[0]["tasks"]
        workflowvars = {k: v for k, v in yamlcontent[0].items() if k != "tasks"}
        
        # ✅ STEP 2: Prepara gdict con variabili header
        exec_gdict = dict(gdict)
        exec_gdict.update(workflowvars)
        
        # ✅ STEP 3: Aggiungi wallet per get_param nei moduli
        if active_wallet and active_wallet.loaded:
            exec_gdict["_wallet"] = active_wallet
            exec_gdict["wallet"] = active_wallet
            logger.info(f"Wallet attached ({len(active_wallet.secrets)} secrets)")
        
        # ✅ STEP 4: Sincronizza gdict di oacommon
        import oacommon
        oacommon.gdict = exec_gdict
        
        taskstore = TaskResultStore()
        engine = WorkflowEngine(tasks, exec_gdict, taskstore, debug=False, debug2=False)
        workflow_state.set_engine(workflow_id, engine)
        
        def run_workflow():
            try:
                logger.info(f"Starting workflow: {workflow_id}")
                success, context = engine.execute()
                workflow["status"] = "completed" if success else "failed"
                
                # ✅ Usa _serialize_results (con underscore)
                workflow["last_execution"] = {
                    "timestamp": datetime.now().isoformat(),
                    "success": success,
                    "results": _serialize_results(context)
                }
                logger.info(f"Workflow {workflow_id}: {'SUCCESS' if success else 'FAILED'}")
            except Exception as e:
                logger.error(f"Workflow failed: {e}", exc_info=True)
                workflow["status"] = "error"
                workflow["last_execution"] = {
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": str(e)
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

@app.get("/api/workflows/{workflow_id}/graph")
async def get_workflow_graph(workflow_id: str):
    """Genera la struttura del workflow per visualizzazione grafica"""
    workflow = workflow_state.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")
    
    try:
        yamlcontent = workflow["content"]
        tasks = yamlcontent[0]["tasks"]
        
        # Trova entry point
        referenced = set()
        for task in tasks:
            if task.get('on_success'):
                referenced.add(task['on_success'])
            if task.get('on_failure'):
                referenced.add(task['on_failure'])
        
        entry_point = None
        for task in tasks:
            name = task.get('name')
            if name and name not in referenced:
                entry_point = name
                break
        
        if not entry_point and tasks:
            entry_point = tasks[0].get('name')
        
        # Parole riservate Mermaid che devono essere evitate
        MERMAID_KEYWORDS = {'end', 'start', 'graph', 'subgraph', 'class', 'classDef', 
                            'click', 'style', 'linkStyle', 'direction', 'TB', 'TD', 
                            'BT', 'RL', 'LR'}
        
        def sanitize_id(name):
            """Converti nome in ID valido per Mermaid, evitando parole riservate"""
            import re
            # Rimuovi caratteri speciali
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
            # Aggiungi prefisso se è parola riservata o inizia con numero
            if safe_id.lower() in MERMAID_KEYWORDS or (safe_id and safe_id[0].isdigit()):
                safe_id = f'node_{safe_id}'
            return safe_id
        
        def sanitize_label(text):
            """Escapa label per Mermaid"""
            if not text:
                return ""
            # Sostituisci caratteri problematici
            text = str(text).replace('"', "'").replace('\n', ' ').replace('\r', '')
            return text
        
        # Costruisci nodi ed edge
        nodes = []
        edges = []
        
        for task in tasks:
            name = task.get('name', 'unnamed')
            module = task.get('module', '')
            function = task.get('function', '')
            
            # Recupera lo stato del task
            status = None
            engine = workflow_state.get_engine(workflow_id)
            if engine:
                task_result = engine.context.get_task_result(name)
                if task_result:
                    status = task_result.status.value
            
            nodes.append({
                'id': sanitize_id(name),
                'name': name,
                'label': sanitize_label(name),
                'module': sanitize_label(module),
                'function': sanitize_label(function),
                'status': status,
                'is_entry': name == entry_point
            })
            
            if task.get('on_success'):
                edges.append({
                    'from': sanitize_id(name),
                    'to': sanitize_id(task['on_success']),
                    'type': 'success'
                })
            if task.get('on_failure'):
                edges.append({
                    'from': sanitize_id(name),
                    'to': sanitize_id(task['on_failure']),
                    'type': 'failure'
                })
        
        # Genera Mermaid syntax
        mermaid_lines = ["flowchart TD"]
        
        # Aggiungi nodi con info modulo/funzione nel tooltip
        for node in nodes:
            label = f"{node['label']}"
            # Info aggiuntiva come tooltip (opzionale)
            if node['module'] and node['function']:
                info = f"{node['module']}.{node['function']}"
                mermaid_lines.append(f'    {node["id"]}["{label}"]')
                mermaid_lines.append(f'    click {node["id"]} callback "{info}"')
            else:
                mermaid_lines.append(f'    {node["id"]}["{label}"]')
        
        # Aggiungi edge
        for edge in edges:
            if edge['type'] == 'success':
                mermaid_lines.append(f'    {edge["from"]} -->|✓| {edge["to"]}')
            else:
                mermaid_lines.append(f'    {edge["from"]} -.->|✗| {edge["to"]}')
        
        # Applica stili
        mermaid_lines.append("")
        mermaid_lines.append("    classDef successNode fill:#d4edda,stroke:#28a745,stroke-width:3px")
        mermaid_lines.append("    classDef failedNode fill:#f8d7da,stroke:#dc3545,stroke-width:3px")
        mermaid_lines.append("    classDef runningNode fill:#fff3cd,stroke:#ffc107,stroke-width:3px")
        mermaid_lines.append("    classDef entryNode fill:#cfe2ff,stroke:#0d6efd,stroke-width:3px")
        
        # Assegna classi
        for node in nodes:
            if node['status'] == 'success':
                mermaid_lines.append(f'    class {node["id"]} successNode')
            elif node['status'] == 'failed':
                mermaid_lines.append(f'    class {node["id"]} failedNode')
            elif node['status'] == 'running':
                mermaid_lines.append(f'    class {node["id"]} runningNode')
            elif node['is_entry']:
                mermaid_lines.append(f'    class {node["id"]} entryNode')
        
        mermaid_code = "\n".join(mermaid_lines)
        
        logger.debug(f"Generated Mermaid code:\n{mermaid_code}")
        
        return {
            "workflow_id": workflow_id,
            "nodes": nodes,
            "edges": edges,
            "mermaid": mermaid_code,
            "entry_point": entry_point
        }
    
    except Exception as e:
        logger.error(f"Failed to generate workflow graph: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to generate graph: {str(e)}")




@app.get("/api/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    workflow = workflow_state.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    engine = workflow_state.get_engine(workflow_id)

    response = {
        "workflow_id": workflow_id,
        "status": workflow['status'],
        "last_execution": workflow.get('last_execution')
    }

    if engine:
        results = _serialize_results(engine.context)
        response['current_results'] = results

    return response

@app.get("/api/workflows/{workflow_id}/results")
async def get_workflow_results(workflow_id: str):
    workflow = workflow_state.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    engine = workflow_state.get_engine(workflow_id)
    if not engine:
        if workflow.get('last_execution'):
            return workflow['last_execution']
        raise HTTPException(404, "No execution results available")

    results = _serialize_results(engine.context)

    return {
        "workflow_id": workflow_id,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    await manager.connect(workflow_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()

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

# ============= HELPER FUNCTIONS =============

def _serialize_results(context: WorkflowContext) -> dict:
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
    return str(obj)

# ============= MODULE INTEGRATION =============

def setgdict(self, gdict_param):
    global gdict
    gdict = gdict_param

# ============= STARTUP =============

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 Open-Automator Web UI Server (with Wallet Management)")
    print("=" * 70)
    print(f"📍 Dashboard: http://localhost:8000")
    print(f"📍 API Docs: http://localhost:8000/docs")
    print(f"📍 Health: http://localhost:8000/health")
    print(f"🔐 Wallet API: http://localhost:8000/api/wallet/status")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
