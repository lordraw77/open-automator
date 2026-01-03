"""
Open-Automator Web UI Module - PATCHED WITH WORKFLOW MANAGER
Espone API REST per gestione workflow via interfaccia web
CON GESTIONE CENTRALIZZATA DEI WORKFLOW
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

# ========================================
# IMPORT WORKFLOW MANAGER CENTRALIZZATO
# ========================================
from workflow_manager import (
    WorkflowManagerFacade,
    WorkflowExecutionStatus,
    WorkflowMetadata,
    WorkflowExecution
)

logger = AutomatorLogger.get_logger("oa-webui")

# ========================================
# CONFIGURAZIONE
# ========================================
gdict = {}
oacommon.setgdict(oacommon, gdict)

# Environment variables
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")

API_KEY = os.getenv("API_KEY", None)
JWT_SECRET = os.getenv("JWT_SECRET", None)

OA_WALLET_FILE = os.getenv("OA_WALLET_FILE", None)
OA_WALLET_PASSWORD = os.getenv("OA_WALLET_PASSWORD", None)

OA_LOG_LEVEL = os.getenv("OA_LOG_LEVEL", "INFO")

OA_WORKFLOWS_DIR = os.getenv("OA_WORKFLOWS_DIR", os.path.join(os.getcwd(), "workflows"))
OA_DATA_DIR = os.getenv("OA_DATA_DIR", os.path.join(os.getcwd(), "data"))
OA_LOGS_DIR = os.getenv("OA_LOGS_DIR", os.path.join(os.getcwd(), "logs"))

MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))
JOB_TIMEOUT_SECONDS = int(os.getenv("JOB_TIMEOUT_SECONDS", "3600"))

ENABLE_CORS = os.getenv("ENABLE_CORS", "true").lower() in ("true", "1", "yes")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]

# Crea directory se non esistono
for directory in [OA_WORKFLOWS_DIR, OA_DATA_DIR, OA_LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ========================================
# FASTAPI APP
# ========================================
app = FastAPI(
    title="Open-Automator Web UI",
    description="API per gestione workflow automation con Workflow Manager Centralizzato",
    version="3.0.0"
)

if ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ========================================
# WORKFLOW MANAGER CENTRALIZZATO (SOSTITUISCE WorkflowState)
# ========================================
workflow_manager = WorkflowManagerFacade(max_concurrent_executions=MAX_CONCURRENT_JOBS)

# ========================================
# WALLET STATE
# ========================================
active_wallet = None
wallet_lock = threading.Lock()

# ========================================
# WEBSOCKET MANAGER
# ========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, workflow_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[workflow_id] = websocket
        logger.info(f"WebSocket connected for workflow {workflow_id}")

    def disconnect(self, workflow_id: str):
        if workflow_id in self.active_connections:
            del self.active_connections[workflow_id]
            logger.info(f"WebSocket disconnected for workflow {workflow_id}")

    async def send_update(self, workflow_id: str, message: dict):
        if workflow_id in self.active_connections:
            try:
                await self.active_connections[workflow_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")

manager = ConnectionManager()

# ========================================
# HELPER FUNCTIONS
# ========================================
def serialize_results(context: WorkflowContext) -> dict:
    """Serializza i risultati del context per JSON"""
    results = {}
    for name, task_result in context.get_all_results().items():
        results[name] = {
            "task_name": task_result.task_name,
            "status": task_result.status.value,
            "output": make_serializable(task_result.output),
            "error": task_result.error,
            "duration": task_result.duration,
            "timestamp": task_result.timestamp.isoformat()
        }
    return results

def make_serializable(obj):
    """Converte oggetti in formato serializzabile JSON"""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

# ========================================
# STARTUP FUNCTIONS
# ========================================
def load_workflows_from_directory():
    """Carica tutti i workflow dalla directory OA_WORKFLOWS_DIR all'avvio"""
    if not os.path.exists(OA_WORKFLOWS_DIR):
        logger.warning(f"Directory workflow non trovata: {OA_WORKFLOWS_DIR}")
        os.makedirs(OA_WORKFLOWS_DIR, exist_ok=True)
        logger.info(f"Creata directory workflow: {OA_WORKFLOWS_DIR}")
        return

    loaded_count = 0
    error_count = 0

    logger.info(f"📂 Caricamento workflow da {OA_WORKFLOWS_DIR}")

    for filename in os.listdir(OA_WORKFLOWS_DIR):
        if filename.endswith((".yaml", ".yml")):
            workflow_path = os.path.join(OA_WORKFLOWS_DIR, filename)
            workflow_id = os.path.splitext(filename)[0]

            try:
                with open(workflow_path, "r", encoding="utf-8") as f:
                    yaml_content = yaml.safe_load(f)

                # Registra nel workflow manager
                workflow_manager.register_workflow(
                    workflow_id=f"wf_{workflow_id}",
                    name=filename,
                    content=yaml_content,
                    filepath=workflow_path,
                    description=f"Auto-loaded from {OA_WORKFLOWS_DIR}",
                    tags=["autoload", "fastapi"]
                )

                loaded_count += 1
                logger.info(f"✅ Workflow caricato: {workflow_id} ({filename})")

            except Exception as e:
                error_count += 1
                logger.error(f"❌ Errore caricamento workflow {filename}: {e}")

    logger.info(f"📊 Caricamento completato: {loaded_count} workflow caricati, {error_count} errori")

def load_wallet_if_configured():
    """Carica il wallet se OA_WALLET_FILE è configurato"""
    global active_wallet

    if not OA_WALLET_FILE:
        logger.info("Nessun wallet configurato (OA_WALLET_FILE non impostato)")
        return

    if not os.path.exists(OA_WALLET_FILE):
        logger.warning(f"File wallet non trovato: {OA_WALLET_FILE}")
        return

    try:
        with wallet_lock:
            if OA_WALLET_PASSWORD:
                # Wallet cifrato
                active_wallet = Wallet(OA_WALLET_FILE, OA_WALLET_PASSWORD)
                active_wallet.load_wallet(OA_WALLET_PASSWORD)
                logger.info(f"🔐 Wallet cifrato caricato: {OA_WALLET_FILE} ({len(active_wallet.secrets)} secrets)")
            else:
                # Wallet plain
                active_wallet = PlainWallet(OA_WALLET_FILE)
                active_wallet.load_wallet()
                logger.info(f"🔓 Wallet plain caricato: {OA_WALLET_FILE} ({len(active_wallet.secrets)} secrets)")

            gdict["wallet"] = active_wallet

    except Exception as e:
        logger.error(f"❌ Errore caricamento wallet: {e}")
        active_wallet = None

# ========================================
# STARTUP EVENT
# ========================================
@app.on_event("startup")
async def startup_event():
    """Evento di avvio dell'applicazione"""
    print()
    print("=" * 70)
    print("Open-Automator apirest - Avvio (Workflow Manager v3.0)")
    print("=" * 70)
    logger.info(f"🌐 Server: {FASTAPI_HOST}:{FASTAPI_PORT}")
    logger.info(f"📁 Workflows Dir: {OA_WORKFLOWS_DIR}")
    logger.info(f"💾 Data Dir: {OA_DATA_DIR}")
    logger.info(f"📋 Logs Dir: {OA_LOGS_DIR}")
    logger.info(f"⚙️  Max Concurrent Jobs: {MAX_CONCURRENT_JOBS}")
    logger.info(f"⏱️  Job Timeout: {JOB_TIMEOUT_SECONDS}s")
    logger.info(f"🌍 CORS: {'Abilitato' if ENABLE_CORS else 'Disabilitato'}")
    logger.info(f"🔒 Log Level: {OA_LOG_LEVEL}")

    if API_KEY:
        logger.info("🔑 API Key: Configurata")
    if JWT_SECRET:
        logger.info("🔐 JWT Secret: Configurato")

    print("-" * 70)

    # Carica wallet se configurato
    load_wallet_if_configured()

    # Carica workflow dalla directory
    load_workflows_from_directory()

    print("-" * 70)
    print("✅ Avvio completato")
    print("=" * 70)
    print()

# ========================================
# ROOT & HEALTH ENDPOINTS
# ========================================
# @app.get("/", response_class=HTMLResponse)
# async def serve_dashboard():
#     """Serve la dashboard HTML"""
#     dashboard_path = os.path.join(os.getcwd(), "dashboard.html")

#     if not os.path.exists(dashboard_path):
#         return HTMLResponse(
#             content=f"""
#             <html>
#             <head><title>Dashboard Not Found</title></head>
#             <body style="font-family: Arial; padding: 50px; text-align: center;">
#                 <h1>📊 Dashboard file not found</h1>
#                 <p>Please ensure <code>dashboard.html</code> is in {os.getcwd()}</p>
#             </body>
#             </html>
#             """,
#             status_code=404
#         )

#     with open(dashboard_path, "r", encoding="utf-8") as f:
#         content = f.read()

#     return HTMLResponse(content=content)

@app.get("/readme", response_class=HTMLResponse)
async def serve_readme():
    """Serve il file README_MODULES.html"""
    readme_path = os.path.join(os.getcwd(), "README_MODULES.html")

    if not os.path.exists(readme_path):
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head><title>README Not Found</title></head>
            <body>
                <h1>README_MODULES.html not found</h1>
                <p>Please ensure <code>README_MODULES.html</code> is in {}</p>
            </body>
            </html>
            """.format(os.getcwd()),
            status_code=404
        )

    return FileResponse(readme_path)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    wallet_status = "loaded" if active_wallet and active_wallet.loaded else "not_loaded"
    workflows = workflow_manager.list_workflows()

    return {
        "status": "running",
        "service": "Open-Automator Web UI",
        "version": "2.0.0",
        "workflows_loaded": len(workflows),
        "wallet_status": wallet_status
    }

# ========================================
# WALLET ENDPOINTS
# ========================================
@app.get("/api/wallet/status")
async def get_wallet_status():
    """Ottiene lo stato del wallet corrente"""
    with wallet_lock:
        if active_wallet is None:
            return {"loaded": False, "message": "No wallet loaded"}

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

            gdict["wallet"] = active_wallet
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
                with open(wallet_file, "w") as f:
                    json.dump(secrets_dict, f, indent=2)

                active_wallet = PlainWallet(wallet_file)
                active_wallet.load_wallet()

            gdict["wallet"] = active_wallet
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
                with open(active_wallet.wallet_file, "w") as f:
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
                with open(active_wallet.wallet_file, "w") as f:
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
        gdict["wallet"] = None
        logger.info("Wallet unloaded")

    return {"success": True, "message": "Wallet unloaded successfully"}

# ========================================
# WORKFLOW ENDPOINTS (CON WORKFLOW MANAGER)
# ========================================
@app.post("/api/workflows/upload")
async def upload_workflow(file: UploadFile = File(...)):
    """Upload di un file workflow YAML"""
    try:
        content = await file.read()
        yaml_content = yaml.safe_load(content.decode("utf-8"))

        if not yaml_content or not isinstance(yaml_content, list) or "tasks" not in yaml_content[0]:
            raise HTTPException(400, "Invalid YAML structure")

        # Genera workflow_id univoco
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Registra nel workflow manager
        metadata = workflow_manager.register_workflow(
            workflow_id=workflow_id,
            name=file.filename,
            content=yaml_content,
            description=f"Uploaded: {file.filename}",
            tags=["uploaded", "fastapi"]
        )

        logger.info(f"Workflow uploaded: {workflow_id} ({metadata.task_count} tasks)")

        return {
            "workflow_id": workflow_id,
            "task_count": metadata.task_count,
            "status": "loaded",
            "message": f"Workflow loaded with {metadata.task_count} tasks"
        }

    except yaml.YAMLError as e:
        raise HTTPException(400, f"Invalid YAML: {str(e)}")
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(500, f"Upload failed: {str(e)}")

@app.get("/api/workflows")
async def list_workflows():
    """Lista tutti i workflow registrati"""
    workflows = workflow_manager.list_workflows()

    workflow_list = []
    for wf in workflows:
        # Recupera ultima esecuzione
        history = workflow_manager.get_workflow_history(wf.workflow_id)
        last_exec = history[-1] if history else None

        workflow_list.append({
            "id": wf.workflow_id,
            "name": wf.name,
            "task_count": wf.task_count,
            "created_at": wf.created_at.isoformat(),
            "tags": wf.tags,
            "status": last_exec.status.value if last_exec else "never_executed",
            "last_execution": {
                "timestamp": last_exec.started_at.isoformat() if last_exec and last_exec.started_at else None,
                "success": last_exec.status == WorkflowExecutionStatus.COMPLETED if last_exec else None,
                "duration": last_exec.duration if last_exec else None
            } if last_exec else None
        })

    return {
        "workflows": workflow_list,
        "count": len(workflow_list)
    }

@app.get("/api/workflows/{workflow_id}")
async def get_workflow_details(workflow_id: str):
    """Ottiene i dettagli di un workflow specifico"""
    metadata = workflow_manager.get_workflow(workflow_id)

    if not metadata:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    # Recupera history
    history = workflow_manager.get_workflow_history(workflow_id)

    return {
        "id": metadata.workflow_id,
        "name": metadata.name,
        "filepath": metadata.filepath,
        "task_count": metadata.task_count,
        "description": metadata.description,
        "tags": metadata.tags,
        "created_at": metadata.created_at.isoformat(),
        "executions_count": len(history),
        "last_execution": {
            "execution_id": history[-1].execution_id,
            "status": history[-1].status.value,
            "started_at": history[-1].started_at.isoformat() if history[-1].started_at else None,
            "duration": history[-1].duration
        } if history else None
    }

@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str):
    """Esegue un workflow tramite il workflow manager centralizzato"""
    metadata = workflow_manager.get_workflow(workflow_id)

    if not metadata:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    try:
        yaml_content = metadata.content

        # STEP 1: Risolvi placeholder WALLET/ENV/VAULT
        if active_wallet and active_wallet.loaded:
            from wallet import resolve_dict_placeholders
            logger.info(f"Resolving WALLET/ENV/VAULT placeholders for workflow {workflow_id}")
            yaml_content = resolve_dict_placeholders(yaml_content, active_wallet)
            logger.debug("Placeholders resolved")

        # STEP 2: Prepara gdict con variabili header
        workflow_vars = {k: v for k, v in yaml_content[0].items() if k != "tasks"}
        exec_gdict = dict(gdict)
        exec_gdict.update(workflow_vars)

        # STEP 3: Aggiungi wallet per get_param nei moduli
        if active_wallet and active_wallet.loaded:
            exec_gdict["wallet"] = active_wallet
            logger.info(f"Wallet attached ({len(active_wallet.secrets)} secrets)")

        # STEP 4: Sincronizza gdict di oacommon
        oacommon.gdict = exec_gdict

        # STEP 5: Esegui tramite workflow manager
        logger.info(f"Starting workflow execution: {workflow_id}")

        execution_id, success, context = workflow_manager.execute_workflow(
            workflow_id=workflow_id,
            gdict=exec_gdict,
            wallet=active_wallet if active_wallet and active_wallet.loaded else None,
            debug=False,
            debug2=False,
            async_mode=True  # ← Asincrono per FastAPI
        )

        logger.info(f"Workflow {workflow_id} started (execution_id: {execution_id})")

        return {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "status": "running",
            "message": "Workflow execution started"
        }

    except Exception as e:
        logger.error(f"Failed to start workflow: {e}", exc_info=True)
        raise HTTPException(500, f"Execution failed: {str(e)}")

@app.get("/api/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Ottiene lo stato corrente di un workflow"""
    metadata = workflow_manager.get_workflow(workflow_id)

    if not metadata:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    # Recupera ultima esecuzione
    history = workflow_manager.get_workflow_history(workflow_id)
    last_exec = history[-1] if history else None

    response = {
        "workflow_id": workflow_id,
        "name": metadata.name,
        "status": last_exec.status.value if last_exec else "never_executed"
    }

    if last_exec:
        response["last_execution"] = {
            "execution_id": last_exec.execution_id,
            "status": last_exec.status.value,
            "started_at": last_exec.started_at.isoformat() if last_exec.started_at else None,
            "completed_at": last_exec.completed_at.isoformat() if last_exec.completed_at else None,
            "duration": last_exec.duration,
            "error": last_exec.error
        }

        # Se è ancora in esecuzione, recupera i risultati parziali
        if last_exec.status == WorkflowExecutionStatus.RUNNING:
            execution = workflow_manager.get_execution(last_exec.execution_id)
            if execution and execution.context:
                response["current_results"] = serialize_results(execution.context)

    return response

@app.get("/api/workflows/{workflow_id}/results")
async def get_workflow_results(workflow_id: str):
    """Ottiene i risultati dell'ultima esecuzione di un workflow"""
    metadata = workflow_manager.get_workflow(workflow_id)

    if not metadata:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    # Recupera ultima esecuzione
    history = workflow_manager.get_workflow_history(workflow_id)
    last_exec = history[-1] if history else None

    if not last_exec:
        raise HTTPException(404, "No execution results available")

    return {
        "workflow_id": workflow_id,
        "execution_id": last_exec.execution_id,
        "status": last_exec.status.value,
        "results": last_exec.results,
        "started_at": last_exec.started_at.isoformat() if last_exec.started_at else None,
        "completed_at": last_exec.completed_at.isoformat() if last_exec.completed_at else None,
        "duration": last_exec.duration
    }

@app.get("/api/workflows/{workflow_id}/history")
async def get_workflow_history(workflow_id: str):
    """Ottiene lo storico completo delle esecuzioni di un workflow"""
    metadata = workflow_manager.get_workflow(workflow_id)

    if not metadata:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    history = workflow_manager.get_workflow_history(workflow_id)

    executions_list = []
    for exec in history:
        executions_list.append({
            "execution_id": exec.execution_id,
            "status": exec.status.value,
            "started_at": exec.started_at.isoformat() if exec.started_at else None,
            "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
            "duration": exec.duration,
            "error": exec.error,
            "results_count": len(exec.results) if exec.results else 0
        })

    return {
        "workflow_id": workflow_id,
        "workflow_name": metadata.name,
        "total_executions": len(executions_list),
        "executions": executions_list
    }

# ========================================
# EXECUTION ENDPOINTS (NUOVI)
# ========================================
@app.get("/api/executions/{execution_id}")
async def get_execution_status(execution_id: str):
    """Ottiene lo stato di una specifica esecuzione"""
    execution = workflow_manager.get_execution(execution_id)

    if not execution:
        raise HTTPException(404, f"Execution not found: {execution_id}")

    return {
        "execution_id": execution.execution_id,
        "workflow_id": execution.workflow_id,
        "status": execution.status.value,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "duration": execution.duration,
        "error": execution.error,
        "results": execution.results,
        "logs": execution.logs
    }

# ========================================
# STATS ENDPOINT (NUOVO)
# ========================================
@app.get("/api/stats")
async def get_stats():
    """Ottiene statistiche del workflow manager"""
    stats = workflow_manager.get_stats()

    return {
        "workflows": stats["workflows"],
        "executions": stats["executions"],
        "system": {
            "wallet_loaded": active_wallet is not None and active_wallet.loaded,
            "max_concurrent_jobs": MAX_CONCURRENT_JOBS
        }
    }

# ========================================
# WEBSOCKET ENDPOINT
# ========================================
@app.websocket("/ws/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    """WebSocket per aggiornamenti real-time di un workflow"""
    await manager.connect(workflow_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()

            if data == "get_status":
                # Recupera ultima esecuzione
                history = workflow_manager.get_workflow_history(workflow_id)
                last_exec = history[-1] if history else None

                if last_exec:
                    await websocket.send_json({
                        "type": "status_update",
                        "execution_id": last_exec.execution_id,
                        "status": last_exec.status.value,
                        "results": last_exec.results
                    })
                else:
                    await websocket.send_json({
                        "type": "status_update",
                        "status": "never_executed"
                    })

    except WebSocketDisconnect:
        manager.disconnect(workflow_id)

# ========================================
# GRAPH ENDPOINT (MANTENUTO COMPATIBILE)
# ========================================
@app.get("/api/workflows/{workflow_id}/graph")
async def get_workflow_graph(workflow_id: str):
    """Genera la struttura del workflow per visualizzazione grafica (Mermaid)"""
    metadata = workflow_manager.get_workflow(workflow_id)

    if not metadata:
        raise HTTPException(404, f"Workflow not found: {workflow_id}")

    try:
        yaml_content = metadata.content
        tasks = yaml_content[0]["tasks"]

        # Trova entry point
        referenced = set()
        for task in tasks:
            if task.get("on_success"):
                referenced.add(task["on_success"])
            if task.get("on_failure"):
                referenced.add(task["on_failure"])

        entry_point = None
        for task in tasks:
            name = task.get("name")
            if name and name not in referenced:
                entry_point = name
                break

        if not entry_point and tasks:
            entry_point = tasks[0].get("name")

        # Parole riservate Mermaid
        MERMAID_KEYWORDS = [
            "end", "start", "graph", "subgraph", "class", "classDef",
            "click", "style", "linkStyle", "direction", "TB", "TD", "BT", "RL", "LR"
        ]

        def sanitize_id(name):
            import re
            safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", str(name))
            if safe_id.lower() in MERMAID_KEYWORDS or (safe_id and safe_id[0].isdigit()):
                safe_id = f"node_{safe_id}"
            return safe_id

        def sanitize_label(text):
            if not text:
                return ""
            text = str(text).replace('"', '\"').replace("'", "\'").replace("\n", " ")
            return text

        nodes = []
        edges = []

        # Recupera ultima esecuzione per gli stati
        history = workflow_manager.get_workflow_history(workflow_id)
        last_exec = history[-1] if history else None

        for task in tasks:
            name = task.get("name", "unnamed")
            module = task.get("module", "")
            function = task.get("function", "")

            # Stato del task
            status = None
            if last_exec and last_exec.results and name in last_exec.results:
                task_result = last_exec.results[name]
                status = task_result.get("status")

            nodes.append({
                "id": sanitize_id(name),
                "name": name,
                "label": sanitize_label(name),
                "module": sanitize_label(module),
                "function": sanitize_label(function),
                "status": status,
                "is_entry": name == entry_point
            })

            if task.get("on_success"):
                edges.append({
                    "from": sanitize_id(name),
                    "to": sanitize_id(task["on_success"]),
                    "type": "success"
                })

            if task.get("on_failure"):
                edges.append({
                    "from": sanitize_id(name),
                    "to": sanitize_id(task["on_failure"]),
                    "type": "failure"
                })

        # Genera Mermaid syntax
        mermaid_lines = ["flowchart TD"]

        # Aggiungi nodi
        for node in nodes:
            label = f"{node['label']}"

            if node["module"] and node["function"]:
                info = f"{node['module']}.{node['function']}"
                mermaid_lines.append(f'    {node["id"]}["{label}"]')
                mermaid_lines.append(f'    click {node["id"]} callback "{info}"')
            else:
                mermaid_lines.append(f'    {node["id"]}["{label}"]')

        # Aggiungi edge
        for edge in edges:
            if edge["type"] == "success":
                mermaid_lines.append(f'    {edge["from"]} --> {edge["to"]}')
            else:
                mermaid_lines.append(f'    {edge["from"]} -.- {edge["to"]}')

        # Aggiungi stili
        mermaid_lines.append("")
        mermaid_lines.append('    classDef successNode fill:#d4edda,stroke:#28a745,stroke-width:3px')
        mermaid_lines.append('    classDef failedNode fill:#f8d7da,stroke:#dc3545,stroke-width:3px')
        mermaid_lines.append('    classDef runningNode fill:#fff3cd,stroke:#ffc107,stroke-width:3px')
        mermaid_lines.append('    classDef entryNode fill:#cfe2ff,stroke:#0d6efd,stroke-width:3px')

        # Assegna classi
        for node in nodes:
            if node["status"] == "success":
                mermaid_lines.append(f'    class {node["id"]} successNode')
            elif node["status"] == "failed":
                mermaid_lines.append(f'    class {node["id"]} failedNode')
            elif node["status"] == "running":
                mermaid_lines.append(f'    class {node["id"]} runningNode')
            elif node["is_entry"]:
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

# ========================================
# MODULE INTEGRATION
# ========================================
def setgdict(self, gdict_param):
    """Funzione per compatibilità con moduli esterni"""
    global gdict
    gdict = gdict_param

# ========================================
# MAIN
# ========================================
if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("Open-Automator apirest (Workflow Manager v3.0)")
    print("=" * 70)
    #print(f"📊 Dashboard: http://localhost:{FASTAPI_PORT}/")
    print(f"📖 API Docs: http://localhost:{FASTAPI_PORT}/docs")
    print(f"💚 Health: http://localhost:{FASTAPI_PORT}/health")
    print(f"📈 Stats: http://localhost:{FASTAPI_PORT}/api/stats")
    print(f"📁 Workflows: {OA_WORKFLOWS_DIR}")
    print(f"⚙️  Max Jobs: {MAX_CONCURRENT_JOBS}")
    print("=" * 70)

    uvicorn.run(app, host=FASTAPI_HOST, port=FASTAPI_PORT, log_level=OA_LOG_LEVEL.lower())