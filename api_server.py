#!/usr/bin/env python3
"""
API Server per Open-Automator - compatibile con curl
Permette l'esecuzione di workflow via HTTP REST API
"""

from flask import Flask, request, jsonify
import os
import yaml
import io
import logging
from datetime import datetime
from automator import WorkflowEngine, WorkflowContext
from taskstore import TaskResultStore
from wallet import Wallet, PlainWallet, resolve_dict_placeholders
from logger_config import AutomatorLogger
import oacommon

app = Flask(__name__)

# Setup logging
AutomatorLogger.setup_logging(
    log_dir=os.getenv('LOG_DIR', './.logs'),
    console_level='INFO',
    file_level='DEBUG'
)

logger = AutomatorLogger.get_logger('api')

@app.route('/execute', methods=['GET', 'POST'])
def execute_workflow():
    """Endpoint per eseguire workflow via API"""

    # Ottieni parametri (da query string o JSON body)
    if request.method == 'POST':
        params = request.json or {}
    else:
        params = request.args.to_dict()

    workflow_name = params.get('WORKFLOW')
    wallet_file = params.get('OA_WALLET_FILE')
    wallet_password = params.get('OA_WALLET_PASSWORD')
    wallet_type = params.get('OA_WALLET_TYPE', 'plain')

    result = {
        'success': False,
        'workflow': workflow_name,
        'message': '',
        'execution_data': None,
        'timestamp': datetime.now().isoformat()
    }

    if not workflow_name:
        result['message'] = 'WORKFLOW parameter is required'
        return jsonify(result), 400

    # Buffer per catturare i log
    log_buffer = io.StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    log_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(formatter)

    automator_logger = logging.getLogger('automator')
    automator_logger.addHandler(log_handler)

    try:
        logger.info(f"Executing workflow: {workflow_name}")

        # 1. Carica wallet
        wallet = None
        if wallet_file:
            if not os.path.exists(wallet_file):
                result['message'] = f'Wallet file not found: {wallet_file}'
                return jsonify(result), 404

            is_encrypted = (
                wallet_file.endswith('.enc') or 
                wallet_type == 'encrypted' or 
                wallet_password is not None
            )

            if is_encrypted:
                if not wallet_password:
                    result['message'] = 'Encrypted wallet requires OA_WALLET_PASSWORD'
                    return jsonify(result), 400

                wallet = Wallet(wallet_file, wallet_password)
                wallet.load_wallet(wallet_password)
                logger.info(f"Encrypted wallet loaded: {len(wallet.secrets)} secrets")
            else:
                wallet = PlainWallet(wallet_file)
                wallet.load_wallet()
                logger.info(f"Plain wallet loaded: {len(wallet.secrets)} secrets")

        # 2. Carica workflow
        workflow_path = os.getenv('WORKFLOW_PATH', './workflows')
        potential_paths = [
            os.path.join(workflow_path, workflow_name),
            workflow_name
        ]

        workflow_file = None
        for path in potential_paths:
            if os.path.exists(path):
                workflow_file = path
                break

        if not workflow_file:
            result['message'] = f'Workflow not found: {workflow_name}'
            return jsonify(result), 404

        logger.info(f"Loading workflow from: {workflow_file}")

        with open(workflow_file, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f.read())

        if not yaml_content or not isinstance(yaml_content, list) or 'tasks' not in yaml_content[0]:
            result['message'] = 'Invalid workflow structure'
            return jsonify(result), 400

        # 3. Risolvi placeholder se c'è wallet
        if wallet:
            yaml_content = resolve_dict_placeholders(yaml_content, wallet)

        # 4. Esegui workflow
        tasks = yaml_content[0]['tasks']
        workflow_vars = {k: v for k, v in yaml_content[0].items() if k != 'tasks'}
        exec_gdict = dict(workflow_vars)

        if wallet:
            exec_gdict['wallet'] = wallet

        oacommon.gdict = exec_gdict

        taskstore = TaskResultStore()
        engine = WorkflowEngine(tasks, exec_gdict, taskstore, debug=False, debug2=False)

        logger.info(f"Starting workflow execution with {len(tasks)} tasks")
        success, context = engine.execute()

        # 5. Prepara risultato
        results = {}
        for name, task_result in context.get_all_results().items():
            results[name] = {
                'task_name': task_result.task_name,
                'status': task_result.status.value,
                'duration': task_result.duration,
                'error': task_result.error,
                'timestamp': task_result.timestamp.isoformat()
            }

        # Cattura i log
        logs = log_buffer.getvalue()

        result['success'] = success
        result['execution_data'] = {
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'results': results,
            'logs': logs
        }
        result['message'] = 'Workflow executed successfully' if success else 'Workflow execution failed'

        logger.info(f"Workflow completed: success={success}")

        return jsonify(result), 200 if success else 500

    except Exception as e:
        logger.error(f"Workflow execution error: {e}", exc_info=True)
        logs = log_buffer.getvalue()
        result['message'] = f'Error during execution: {str(e)}'
        result['error'] = str(e)
        result['logs'] = logs
        return jsonify(result), 500

    finally:
        automator_logger.removeHandler(log_handler)
        log_handler.close()

@app.route('/health', methods=['GET'])
def health():
    """Endpoint di health check"""
    return jsonify({
        'status': 'ok',
        'service': 'open-automator-api',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/workflows', methods=['GET'])
def list_workflows():
    """Elenca i workflow disponibili"""
    try:
        workflow_path = os.getenv('WORKFLOW_PATH', './workflows')

        if not os.path.exists(workflow_path):
            return jsonify({'workflows': [], 'message': f'Directory not found: {workflow_path}'}), 404

        import glob
        workflow_files = []
        for ext in ['*.yaml', '*.yml']:
            workflow_files.extend(glob.glob(os.path.join(workflow_path, ext)))

        workflows = []
        for filepath in workflow_files:
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    yaml_content = yaml.safe_load(f.read())
                    if yaml_content and isinstance(yaml_content, list) and 'tasks' in yaml_content[0]:
                        workflows.append({
                            'name': filename,
                            'path': filepath,
                            'tasks': len(yaml_content[0]['tasks'])
                        })
            except:
                pass

        return jsonify({
            'workflows': workflows,
            'count': len(workflows),
            'path': workflow_path
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 8503))
    host = os.getenv('API_HOST', '0.0.0.0')

    logger.info(f"Starting Open-Automator API Server on {host}:{port}")
    app.run(host=host, port=port, debug=False)