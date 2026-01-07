"""
Open-Automator API Server - PATCHED WITH WORKFLOW MANAGER
Flask-based REST API per esecuzione workflow
CON GESTIONE CENTRALIZZATA
"""

import os
import sys
import yaml
import json
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from datetime import datetime
import logging

from logger_config import AutomatorLogger
from automator import WorkflowEngine, WorkflowContext
from taskstore import TaskResultStore
from wallet import Wallet, PlainWallet, resolve_dict_placeholders
import oacommon

# ========================================
# IMPORT WORKFLOW MANAGER CENTRALIZZATO
# ========================================
from workflow_manager import (
    WorkflowManagerFacade,
    WorkflowExecutionStatus,
    WorkflowMetadata
)
def read_version():
    """Legge la versione dal file VERSION"""
    version_file = os.path.join(os.path.dirname(__file__), "VERSION")
    
    try:
        with open(version_file, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"
    except Exception as e:
        logger.error(f"Failed to read version file: {e}")
        return "error"

APP_VERSION = read_version()


# ========================================
# CONFIGURAZIONE
# ========================================
logger = AutomatorLogger.get_logger("api-server")

gdict = {}
oacommon.setgdict(oacommon, gdict)

# Environment variables
API_PORT = int(os.getenv("API_PORT", "8503"))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
WORKFLOW_PATH = os.getenv("WORKFLOW_PATH", "./workflows")
OA_WALLET_FILE = os.getenv("OA_WALLET_FILE", None)
OA_WALLET_PASSWORD = os.getenv("OA_WALLET_PASSWORD", None)
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))

# ========================================
# FLASK APP
# ========================================
app = Flask(__name__)
CORS(app)

# ========================================
# WORKFLOW MANAGER CENTRALIZZATO
# ========================================
workflow_manager = WorkflowManagerFacade(max_concurrent_executions=MAX_CONCURRENT_JOBS)

# ========================================
# WALLET STATE
# ========================================
active_wallet = None

# ========================================
# STARTUP FUNCTIONS
# ========================================
def load_wallet_if_configured():
    """Carica il wallet se configurato"""
    global active_wallet

    if not OA_WALLET_FILE or not os.path.exists(OA_WALLET_FILE):
        logger.info("No wallet configured or file not found")
        return

    try:
        if OA_WALLET_PASSWORD:
            active_wallet = Wallet(OA_WALLET_FILE, OA_WALLET_PASSWORD)
            active_wallet.load_wallet(OA_WALLET_PASSWORD)
            logger.info(f"Wallet loaded: {OA_WALLET_FILE} ({len(active_wallet.secrets)} secrets)")
        else:
            active_wallet = PlainWallet(OA_WALLET_FILE)
            active_wallet.load_wallet()
            logger.info(f"Plain wallet loaded: {OA_WALLET_FILE} ({len(active_wallet.secrets)} secrets)")

        gdict["wallet"] = active_wallet

    except Exception as e:
        logger.error(f"Failed to load wallet: {e}")
        active_wallet = None

def load_workflows_from_directory():
    """Carica workflow dalla directory all'avvio"""
    if not os.path.exists(WORKFLOW_PATH):
        logger.warning(f"Workflow directory not found: {WORKFLOW_PATH}")
        os.makedirs(WORKFLOW_PATH, exist_ok=True)
        return

    loaded_count = 0

    logger.info(f"Loading workflows from {WORKFLOW_PATH}")

    for filename in os.listdir(WORKFLOW_PATH):
        if filename.endswith((".yaml", ".yml")):
            filepath = os.path.join(WORKFLOW_PATH, filename)
            workflow_id = f"wf_{os.path.splitext(filename)[0]}"

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    yaml_content = yaml.safe_load(f)

                workflow_manager.register_workflow(
                    workflow_id=workflow_id,
                    name=filename,
                    content=yaml_content,
                    filepath=filepath,
                    description=f"Auto-loaded from {WORKFLOW_PATH}",
                    tags=["autoload", "flask"]
                )

                loaded_count += 1
                logger.info(f"Workflow loaded: {workflow_id} ({filename})")

            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")

    logger.info(f"Loaded {loaded_count} workflows")

# ========================================
# HELPER FUNCTIONS
# ========================================
def serialize_results(context: WorkflowContext) -> dict:
    """Serializza risultati per JSON"""
    results = {}
    for name, task_result in context.get_all_results().items():
        results[name] = {
            "task_name": task_result.task_name,
            "status": task_result.status.value,
            "output": str(task_result.output) if task_result.output else None,
            "error": task_result.error,
            "duration": task_result.duration,
            "timestamp": task_result.timestamp.isoformat()
        }
    return results

# ========================================
# API ENDPOINTS
# ========================================
@app.route("/", methods=["GET"])
def index():
    """Root endpoint"""
    return jsonify({
        "service": "Open-Automator API Server",
        "version": APP_VERSION,
        "status": "running",
        "workflow_manager": "enabled",
        "endpoints": {
            "execute": "/execute?WORKFLOW=filename.yaml",
            "workflows": "/workflows",
            "executions": "/executions/<execution_id>",
            "stats": "/stats",
            "health": "/health"
        }
    })

@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    workflows = workflow_manager.list_workflows()
    stats = workflow_manager.get_stats()

    return jsonify({
        "status": "healthy",
        "workflows_loaded": len(workflows),
        "active_executions": stats["executions"]["active_executions"],
        "wallet_loaded": active_wallet is not None and active_wallet.loaded
    })

@app.route("/execute", methods=["GET"])
def execute():
    """
    Esegue un workflow tramite workflow manager
    Query params:
        - WORKFLOW: filename del workflow (es. test.yaml)
        - DEBUG: true/false (opzionale)
        - DEBUG2: true/false (opzionale)
    """
    workflow_name = request.args.get("WORKFLOW")

    if not workflow_name:
        return jsonify({"error": "Missing WORKFLOW parameter"}), 400

    # Determina path completo
    if os.path.isabs(workflow_name):
        workflow_file = workflow_name
    else:
        workflow_file = os.path.join(WORKFLOW_PATH, workflow_name)

    if not os.path.exists(workflow_file):
        return jsonify({"error": f"Workflow file not found: {workflow_name}"}), 404

    try:
        # Carica YAML
        with open(workflow_file, "r", encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)

        # Validazione supporta entrambe le sintassi
        has_tasks = False

        # Nuova sintassi: {name: ..., variable: {...}, tasks: [...]}
        if isinstance(yaml_content, dict) and "tasks" in yaml_content:
            has_tasks = True

        # Vecchia sintassi: [{VAR1: ..., tasks: [...]}]
        elif isinstance(yaml_content, list) and len(yaml_content) > 0 and "tasks" in yaml_content[0]:
            has_tasks = True

        if not has_tasks:
            return jsonify({"error": "Invalid YAML structure - missing 'tasks' key"}), 400

        # Risolvi placeholder
        if active_wallet:
            yaml_content = resolve_dict_placeholders(yaml_content, active_wallet)

        # Genera workflow_id
        workflow_id = f"flask_{os.path.basename(workflow_name).replace('.yaml', '').replace('.yml', '')}"

        # Verifica se già registrato, altrimenti registra
        if not workflow_manager.get_workflow(workflow_id):
            workflow_manager.register_workflow(
                workflow_id=workflow_id,
                name=os.path.basename(workflow_name),
                content=yaml_content,
                filepath=workflow_file,
                tags=["flask", "execute"]
            )
            logger.info(f"Workflow registered on-the-fly: {workflow_id}")

        # Prepara gdict - supporta entrambe le sintassi
        workflow_vars = {}

        # Nuova sintassi
        if isinstance(yaml_content, dict):
            if "variable" in yaml_content:
                workflow_vars = yaml_content["variable"]
            elif "variables" in yaml_content:
                workflow_vars = yaml_content["variables"]

        # Vecchia sintassi
        elif isinstance(yaml_content, list) and len(yaml_content) > 0:
            workflow_vars = {k: v for k, v in yaml_content[0].items() if k != "tasks"}

        exec_gdict = dict(gdict)
        exec_gdict.update(workflow_vars)


        if active_wallet:
            exec_gdict["wallet"] = active_wallet

        # Flags debug
        debug = request.args.get("DEBUG", "false").lower() == "true"
        debug2 = request.args.get("DEBUG2", "false").lower() == "true"

        exec_gdict["DEBUG"] = debug
        exec_gdict["DEBUG2"] = debug2

        # Sincronizza oacommon
        oacommon.gdict = exec_gdict

        # Esegui tramite workflow manager
        logger.info(f"Executing workflow: {workflow_id}")

        execution_id, success, context = workflow_manager.execute_workflow(
            workflow_id=workflow_id,
            gdict=exec_gdict,
            wallet=active_wallet,
            debug=debug,
            debug2=debug2,
            async_mode=False  # ← Flask è sincrono
        )

        logger.info(f"Workflow {workflow_id} executed (execution_id: {execution_id})")

        # Recupera execution per risultati
        execution = workflow_manager.get_execution(execution_id)

        response = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "success": success,
            "status": execution.status.value if execution else "unknown",
            "duration": execution.duration if execution else None,
            "results": execution.results if execution else None
        }

        if not success and execution:
            response["error"] = execution.error

        return jsonify(response), 200 if success else 500

    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/workflows", methods=["GET"])
def list_workflows():
    """Lista tutti i workflow registrati"""
    workflows = workflow_manager.list_workflows()

    workflow_list = []
    for wf in workflows:
        history = workflow_manager.get_workflow_history(wf.workflow_id)
        last_exec = history[-1] if history else None

        workflow_list.append({
            "id": wf.workflow_id,
            "name": wf.name,
            "filepath": wf.filepath,
            "task_count": wf.task_count,
            "tags": wf.tags,
            "created_at": wf.created_at.isoformat(),
            "executions_count": len(history),
            "last_execution": {
                "execution_id": last_exec.execution_id,
                "status": last_exec.status.value,
                "duration": last_exec.duration
            } if last_exec else None
        })

    return jsonify({
        "workflows": workflow_list,
        "count": len(workflow_list)
    })

@app.route("/workflows/<workflow_id>", methods=["GET"])
def get_workflow(workflow_id: str):
    """Dettagli di un workflow specifico"""
    metadata = workflow_manager.get_workflow(workflow_id)

    if not metadata:
        return jsonify({"error": f"Workflow not found: {workflow_id}"}), 404

    history = workflow_manager.get_workflow_history(workflow_id)

    return jsonify({
        "id": metadata.workflow_id,
        "name": metadata.name,
        "filepath": metadata.filepath,
        "task_count": metadata.task_count,
        "description": metadata.description,
        "tags": metadata.tags,
        "created_at": metadata.created_at.isoformat(),
        "executions_count": len(history)
    })

@app.route("/workflows/<workflow_id>/history", methods=["GET"])
def get_workflow_history_endpoint(workflow_id: str):
    """Storico esecuzioni di un workflow"""
    metadata = workflow_manager.get_workflow(workflow_id)

    if not metadata:
        return jsonify({"error": f"Workflow not found: {workflow_id}"}), 404

    history = workflow_manager.get_workflow_history(workflow_id)

    executions = []
    for exec in history:
        executions.append({
            "execution_id": exec.execution_id,
            "status": exec.status.value,
            "started_at": exec.started_at.isoformat() if exec.started_at else None,
            "duration": exec.duration,
            "error": exec.error
        })

    return jsonify({
        "workflow_id": workflow_id,
        "total_executions": len(executions),
        "executions": executions
    })

@app.route("/executions/<execution_id>", methods=["GET"])
def get_execution(execution_id: str):
    """Dettagli di una specifica esecuzione"""
    execution = workflow_manager.get_execution(execution_id)

    if not execution:
        return jsonify({"error": f"Execution not found: {execution_id}"}), 404

    return jsonify({
        "execution_id": execution.execution_id,
        "workflow_id": execution.workflow_id,
        "status": execution.status.value,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "duration": execution.duration,
        "error": execution.error,
        "results": execution.results
    })

@app.route("/stats", methods=["GET"])
def get_stats():
    """Statistiche del workflow manager"""
    stats = workflow_manager.get_stats()

    return jsonify({
        "workflows": stats["workflows"],
        "executions": stats["executions"],
        "system": {
            "wallet_loaded": active_wallet is not None and active_wallet.loaded,
            "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
            "workflow_path": WORKFLOW_PATH
        }
    })

# ========================================
# MAIN
# ========================================
if __name__ == "__main__":
    print("=" * 70)
    print("Open-Automator API Server (Workflow Manager v3.0)")
    print("=" * 70)
    print(f"🌐 API: http://{API_HOST}:{API_PORT}/")
    print(f"💚 Health: http://localhost:{API_PORT}/health")
    print(f"📈 Stats: http://localhost:{API_PORT}/stats")
    print(f"📁 Workflows: {WORKFLOW_PATH}")
    print(f"⚙️  Max Jobs: {MAX_CONCURRENT_JOBS}")
    print("=" * 70)

    # Load wallet
    load_wallet_if_configured()

    # Load workflows
    load_workflows_from_directory()

    print("✅ Server ready")
    print("=" * 70)

    # Start server
    app.run(host=API_HOST, port=API_PORT, debug=False)
