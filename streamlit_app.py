"""
Open-Automator Streamlit Web UI
v1.3.0 - Auto-Load Workflows Edition
"""

import streamlit as st
import yaml
import json
import os
import time
import re
import glob
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from automator import WorkflowEngine, WorkflowContext, TaskResult, TaskStatus
    from taskstore import TaskResultStore
    from wallet import Wallet, PlainWallet, resolve_dict_placeholders
    from logger_config import AutomatorLogger
    import oacommon
except ImportError as e:
    st.error(f"⚠️ Import error: {e}")
    st.stop()

st.set_page_config(
    page_title="Open-Automator",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .stApp {
            background-color: #1e1e2e;
        }
        [data-testid="stSidebar"] {
            background-color: #2b2b3d;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #a0a0b0;
            font-size: 0.85em;
        }
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .main-header h1 {
            margin: 0;
            font-size: 2.2em;
            font-weight: 600;
        }
        .main-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }
        .section-header {
            background: #3a3a4d;
            padding: 0.8rem 1rem;
            border-radius: 8px;
            color: #e0e0e0;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        .selected-indicator, .wallet-info {
            color: #dc3545;
            font-size: 0.85em;
            margin: 0.5rem 0;
        }
        .secret-value {
            background: #2b2b3d;
            padding: 0.5rem;
            border-radius: 5px;
            font-family: monospace;
            color: #a0a0b0;
            margin: 0.5rem 0;
        }
    </style>
""", unsafe_allow_html=True)

def init_session_state():
    if 'workflows' not in st.session_state:
        st.session_state.workflows = {}
    if 'active_wallet' not in st.session_state:
        st.session_state.active_wallet = None
    if 'current_workflow_id' not in st.session_state:
        st.session_state.current_workflow_id = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'workflow'
    if 'last_uploaded_file' not in st.session_state:
        st.session_state.last_uploaded_file = None
    if 'show_secrets' not in st.session_state:
        st.session_state.show_secrets = {}
    if 'edit_secrets' not in st.session_state:
        st.session_state.edit_secrets = {}
    # NUOVO: Parametro per il path dei workflow
    if 'workflow_path' not in st.session_state:
        st.session_state.workflow_path = os.getenv('WORKFLOW_PATH', './workflows')
    # NUOVO: Auto-carica workflow all'avvio
    if 'workflows_loaded' not in st.session_state:
        st.session_state.workflows_loaded = False

init_session_state()

def serialize_results(context: WorkflowContext) -> dict:
    results = {}
    for name, task_result in context.get_all_results().items():
        results[name] = {
            'task_name': task_result.task_name,
            'status': task_result.status.value,
            'output': make_serializable(task_result.output),
            'error': task_result.error,
            'duration': task_result.duration,
            'timestamp': task_result.timestamp.isoformat()
        }
    return results

def make_serializable(obj):
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

def sanitize_node_id(name: str) -> str:
    if not name or not isinstance(name, str):
        return 'task_unnamed'

    replacements = {
        'end': 'finale',
        'start': 'inizio',
        'graph': 'grafo',
        'subgraph': 'sottografo',
        'class': 'classe',
        'classDef': 'classedef',
        'click': 'clicca',
        'style': 'stile',
        'link': 'collegamento'
    }

    name_lower = name.lower()
    if name_lower in replacements:
        name = replacements[name_lower]

    safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    safe_id = re.sub(r'_+', '_', safe_id)
    safe_id = safe_id.strip('_')

    if safe_id and safe_id[0].isdigit():
        safe_id = f'task_{safe_id}'

    if any(word in safe_id.lower() for word in replacements.keys()):
        safe_id = f'node_{safe_id}'

    return safe_id if safe_id else 'task_unnamed'

def sanitize_mermaid_label(label: str) -> str:
    if not label or not isinstance(label, str):
        return "unnamed"

    replacements = {
        'end': 'End Task',
        'start': 'Start Task',
        'graph': 'Graph',
        'class': 'Class'
    }

    if label.lower() in replacements:
        label = replacements[label.lower()]

    clean_label = label.replace('"', "'").replace('\n', ' ').replace('\r', '')
    clean_label = clean_label.strip()

    return clean_label[:60] if clean_label else "unnamed"

def generate_mermaid_code(workflow: dict) -> str:
    try:
        yaml_content = workflow['content']
        if not yaml_content or not isinstance(yaml_content, list):
            return "graph TD\n    A[Invalid workflow]"

        tasks = yaml_content[0].get('tasks', [])
        if not tasks:
            return "graph TD\n    A[No tasks]"

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
            entry_point = tasks[0].get('name', 'start')

        node_map = {}
        for idx, task in enumerate(tasks):
            name = task.get('name', f'task_{idx}')
            node_id = f'node{idx}_{sanitize_node_id(name)}'
            node_map[name] = node_id

        lines = ["%%{init: {'theme':'dark', 'flowchart':{'nodeSpacing': 100, 'rankSpacing': 120, 'padding': 20}}}%%"]
        lines.append("graph TD")

        for task in tasks:
            name = task.get('name', 'unnamed')
            node_id = node_map.get(name)
            if not node_id:
                continue
            label = sanitize_mermaid_label(name)
            lines.append(f'    {node_id}["{label}"]')

        for task in tasks:
            name = task.get('name', 'unnamed')
            node_id = node_map.get(name)
            if not node_id:
                continue

            if task.get('on_success'):
                success_name = task['on_success']
                success_id = node_map.get(success_name)
                if success_id:
                    lines.append(f'    {node_id} --> {success_id}')

            if task.get('on_failure'):
                failure_name = task['on_failure']
                failure_id = node_map.get(failure_name)
                if failure_id:
                    lines.append(f'    {node_id} -.-> {failure_id}')

        lines.append("")
        lines.append("classDef successNode fill:#28a745,stroke:#1e7e34,stroke-width:3px,color:#fff")
        lines.append("classDef failedNode fill:#dc3545,stroke:#bd2130,stroke-width:3px,color:#fff")
        lines.append("classDef runningNode fill:#ffc107,stroke:#e0a800,stroke-width:3px,color:#000")
        lines.append("classDef entryNode fill:#007bff,stroke:#0056b3,stroke-width:3px,color:#fff")

        for task in tasks:
            name = task.get('name', 'unnamed')
            node_id = node_map.get(name)
            if not node_id:
                continue

            status = None
            if workflow.get('last_execution') and workflow['last_execution'].get('results'):
                results = workflow['last_execution']['results']
                if name in results:
                    status = results[name].get('status')

            if status == 'success':
                lines.append(f'    class {node_id} successNode')
            elif status == 'failed':
                lines.append(f'    class {node_id} failedNode')
            elif status == 'running':
                lines.append(f'    class {node_id} runningNode')
            elif name == entry_point:
                lines.append(f'    class {node_id} entryNode')

        return "\n".join(lines)

    except Exception as e:
        return f"graph TD\n    A[Error: {str(e)[:50]}]"

def load_wallet(wallet_file: str, wallet_type: str, master_password: str = None):
    try:
        if not os.path.exists(wallet_file):
            st.error(f"❌ Wallet file not found: {wallet_file}")
            return

        if wallet_type == 'encrypted':
            if not master_password:
                st.error("❌ Master password required")
                return
            wallet = Wallet(wallet_file, master_password)
            wallet.load_wallet(master_password)
        else:
            wallet = PlainWallet(wallet_file)
            wallet.load_wallet()

        st.session_state.active_wallet = wallet
        st.success(f"✅ Wallet loaded: {len(wallet.secrets)} secrets")
        time.sleep(0.5)
        st.rerun()

    except ValueError:
        st.error("❌ Invalid master password")
    except Exception as e:
        st.error(f"❌ Failed to load wallet: {e}")

def create_wallet(wallet_file: str, wallet_type: str, master_password: str, secrets_json: str):
    try:
        secrets_dict = json.loads(secrets_json)

        if os.path.exists(wallet_file):
            st.error(f"❌ Wallet file already exists")
            return

        if wallet_type == 'encrypted':
            if not master_password:
                st.error("❌ Master password required")
                return
            wallet = Wallet(wallet_file, master_password)
            wallet.create_wallet(secrets_dict, master_password)
            wallet.load_wallet(master_password)
        else:
            with open(wallet_file, 'w') as f:
                json.dump(secrets_dict, f, indent=2)
            wallet = PlainWallet(wallet_file)
            wallet.load_wallet()

        st.session_state.active_wallet = wallet
        st.success(f"✅ Wallet created: {len(secrets_dict)} secrets")
        time.sleep(0.5)
        st.rerun()

    except json.JSONDecodeError:
        st.error("❌ Invalid JSON format")
    except Exception as e:
        st.error(f"❌ Failed to create wallet: {e}")

def add_secret(key: str, value: str, master_password: str = None):
    wallet = st.session_state.active_wallet
    if not wallet:
        return

    try:
        wallet.secrets[key] = value

        if isinstance(wallet, Wallet):
            if not master_password:
                st.error("❌ Master password required")
                return
            wallet.create_wallet(wallet.secrets, master_password)
        else:
            with open(wallet.wallet_file, 'w') as f:
                json.dump(wallet.secrets, f, indent=2)

        st.success(f"✅ Secret '{key}' added")
        time.sleep(0.3)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Failed: {e}")

def update_secret(key: str, new_value: str, master_password: str = None):
    """Aggiorna il valore di un secret esistente"""
    wallet = st.session_state.active_wallet
    if not wallet or key not in wallet.secrets:
        return

    try:
        wallet.secrets[key] = new_value

        if isinstance(wallet, Wallet):
            if not master_password:
                st.error("❌ Master password required")
                return
            wallet.create_wallet(wallet.secrets, master_password)
        else:
            with open(wallet.wallet_file, 'w') as f:
                json.dump(wallet.secrets, f, indent=2)

        st.success(f"✅ Secret '{key}' updated")
        st.session_state.edit_secrets[key] = False
        time.sleep(0.3)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Failed: {e}")

def delete_secret(key: str, master_password: str = None):
    wallet = st.session_state.active_wallet
    if not wallet or key not in wallet.secrets:
        return

    try:
        del wallet.secrets[key]

        if isinstance(wallet, Wallet):
            if not master_password:
                st.error("❌ Master password required")
                return
            wallet.create_wallet(wallet.secrets, master_password)
        else:
            with open(wallet.wallet_file, 'w') as f:
                json.dump(wallet.secrets, f, indent=2)

        st.success(f"✅ Secret '{key}' removed")
        time.sleep(0.3)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Failed: {e}")

def unload_wallet():
    st.session_state.active_wallet = None
    st.session_state.show_secrets = {}
    st.session_state.edit_secrets = {}
    st.success("✅ Wallet unloaded")
    time.sleep(0.3)
    st.rerun()

def load_workflows_from_directory(workflow_path: str = "./workflows"):
    """Carica tutti i workflow YAML dalla directory specificata"""
    if not os.path.exists(workflow_path):
        st.warning(f"📁 Directory non trovata: {workflow_path}")
        return 0

    loaded_count = 0
    workflow_files = []

    # Cerca file .yaml e .yml
    for ext in ['*.yaml', '*.yml']:
        workflow_files.extend(glob.glob(os.path.join(workflow_path, ext)))

    for filepath in workflow_files:
        try:
            filename = os.path.basename(filepath)

            # Controlla se già caricato
            existing_ids = [wf['filepath'] for wf in st.session_state.workflows.values() 
                          if 'filepath' in wf]
            if filepath in existing_ids:
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                yaml_content = yaml.safe_load(content)

            if not yaml_content or not isinstance(yaml_content, list) or 'tasks' not in yaml_content[0]:
                st.warning(f"⚠️ File non valido: {filename}")
                continue

            workflow_id = f"wf_{filename.replace('.yaml', '').replace('.yml', '')}"
            tasks = yaml_content[0]['tasks']

            st.session_state.workflows[workflow_id] = {
                'id': workflow_id,
                'name': filename,
                'filepath': filepath,
                'content': yaml_content,
                'status': 'loaded',
                'created_at': datetime.now().isoformat(),
                'last_execution': None
            }
            loaded_count += 1

        except Exception as e:
            st.warning(f"⚠️ Errore caricando {filename}: {e}")

    return loaded_count

def handle_workflow_upload(uploaded_file):
    try:
        file_identifier = f"{uploaded_file.name}_{uploaded_file.size}"

        if st.session_state.last_uploaded_file == file_identifier:
            return

        content = uploaded_file.read().decode('utf-8')
        yaml_content = yaml.safe_load(content)

        if not yaml_content or not isinstance(yaml_content, list) or 'tasks' not in yaml_content[0]:
            st.error("❌ Invalid YAML structure")
            return

        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tasks = yaml_content[0]['tasks']

        st.session_state.workflows[workflow_id] = {
            'id': workflow_id,
            'name': uploaded_file.name,
            'content': yaml_content,
            'status': 'loaded',
            'created_at': datetime.now().isoformat(),
            'last_execution': None
        }

        st.session_state.current_workflow_id = workflow_id
        st.session_state.last_uploaded_file = file_identifier

        st.success(f"✅ Workflow loaded: {len(tasks)} tasks")
        time.sleep(0.5)
        st.rerun()

    except yaml.YAMLError as e:
        st.error(f"❌ Invalid YAML: {e}")
    except Exception as e:
        st.error(f"❌ Upload failed: {e}")

def execute_workflow(workflow_id: str):
    workflow = st.session_state.workflows[workflow_id]
    yaml_content = workflow['content']

    try:
        if st.session_state.active_wallet:
            yaml_content = resolve_dict_placeholders(yaml_content, st.session_state.active_wallet)

        tasks = yaml_content[0]['tasks']
        workflow_vars = {k: v for k, v in yaml_content[0].items() if k != 'tasks'}
        exec_gdict = dict(workflow_vars)

        if st.session_state.active_wallet:
            exec_gdict['wallet'] = st.session_state.active_wallet

        oacommon.gdict = exec_gdict

        taskstore = TaskResultStore()
        engine = WorkflowEngine(tasks, exec_gdict, taskstore, debug=False, debug2=False)

        st.session_state.workflows[workflow_id]['status'] = 'running'
        success, context = engine.execute()

        st.session_state.workflows[workflow_id]['status'] = 'completed' if success else 'failed'
        st.session_state.workflows[workflow_id]['last_execution'] = {
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'results': serialize_results(context)
        }

        if success:
            st.success("✅ Workflow completed!")
        else:
            st.error("❌ Workflow failed")

    except Exception as e:
        st.session_state.workflows[workflow_id]['status'] = 'error'
        st.error(f"❌ Execution failed: {e}")

def render_sidebar():
    with st.sidebar:
        st.title("🔄 Open-Automator")
        st.divider()

        if st.button("📋 Workflows", use_container_width=True, 
                    type="primary" if st.session_state.current_page == 'workflow' else "secondary"):
            st.session_state.current_page = 'workflow'
            st.rerun()

        if st.session_state.current_workflow_id:
            wf = st.session_state.workflows[st.session_state.current_workflow_id]
            display_name = wf.get('name', wf['id'])
            st.markdown(f'<p class="selected-indicator">📌 Selected: {display_name}</p>', 
                       unsafe_allow_html=True)
            st.markdown(f'<p class="selected-indicator">Status: {wf["status"].upper()}</p>', 
                       unsafe_allow_html=True)

        st.divider()

        if st.button("🔐 Wallet", use_container_width=True, 
                    type="primary" if st.session_state.current_page == 'wallet' else "secondary"):
            st.session_state.current_page = 'wallet'
            st.rerun()

        if st.session_state.active_wallet:
            wallet = st.session_state.active_wallet
            wallet_type = "🔒 Encrypted" if isinstance(wallet, Wallet) else "📄 Plain"
            st.markdown(f'<p class="wallet-info">📌 Loaded: {wallet_type}</p>', 
                       unsafe_allow_html=True)
            st.markdown(f'<p class="wallet-info">Secrets: {len(wallet.secrets)}</p>', 
                       unsafe_allow_html=True)

        st.divider()
        st.caption("v1.3.0 - Auto-Load")

def render_workflow_page():
    st.markdown('''
    <div class="main-header">
        <h1>🔄 Workflow Management</h1>
        <p>Upload, execute and monitor your automation workflows</p>
    </div>
    ''', unsafe_allow_html=True)

    # NUOVA SEZIONE: Caricamento automatico
    if not st.session_state.workflows_loaded:
        with st.spinner('🔍 Caricamento workflow dalla directory...'):
            count = load_workflows_from_directory(st.session_state.workflow_path)
            if count > 0:
                st.success(f"✅ Caricati {count} workflow da {st.session_state.workflow_path}")
            st.session_state.workflows_loaded = True
            time.sleep(1)
            st.rerun()

    # Sezione configurazione path
    st.markdown('<div class="section-header">⚙️ Configurazione</div>', unsafe_allow_html=True)
    col_path, col_reload = st.columns([3, 1])

    with col_path:
        new_path = st.text_input(
            "Directory Workflow", 
            value=st.session_state.workflow_path,
            help="Path della directory contenente i file YAML dei workflow"
        )
        if new_path != st.session_state.workflow_path:
            st.session_state.workflow_path = new_path

    with col_reload:
        st.write("")
        st.write("")
        if st.button("🔄 Ricarica", use_container_width=True):
            st.session_state.workflows_loaded = False
            st.rerun()

    # Sezione upload manuale (opzionale)
    with st.expander("📤 Upload Manuale"):
        uploaded_file = st.file_uploader(
            "Choose YAML file", 
            type=['yaml', 'yml'],
            label_visibility='collapsed',
            key='workflow_uploader'
        )
        if uploaded_file:
            st.caption(f"📄 {uploaded_file.name}")
            handle_workflow_upload(uploaded_file)

    st.divider()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="section-header">📋 Workflow List</div>', unsafe_allow_html=True)

        if len(st.session_state.workflows) == 0:
            st.info("No workflows loaded")
        else:
            sorted_workflows = sorted(
                st.session_state.workflows.items(),
                key=lambda x: x[1]['created_at'],
                reverse=True
            )

            for wf_id, wf in sorted_workflows:
                is_selected = wf_id == st.session_state.current_workflow_id
                task_count = len(wf['content'][0]['tasks'])
                status = wf['status']
                status_emoji = {
                    'loaded': '📋',
                    'running': '⚙️',
                    'completed': '✅',
                    'failed': '❌',
                    'error': '⚠️'
                }.get(status, '📋')

                # Mostra il nome del file se disponibile
                display_name = wf.get('name', wf_id)

                if st.button(
                    f"{status_emoji} {display_name} ({task_count} tasks)",
                    key=f"sel_{wf_id}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    st.session_state.current_workflow_id = wf_id
                    st.rerun()

    with col2:
        if not st.session_state.current_workflow_id:
            st.info("📌 Select a workflow from the list")
        else:
            workflow = st.session_state.workflows[st.session_state.current_workflow_id]
            display_name = workflow.get('name', workflow['id'])

            st.markdown(f'<div class="section-header">📋 {display_name}</div>', unsafe_allow_html=True)

            cola, colb, colc = st.columns(3)

            cola.metric("Tasks", len(workflow['content'][0]['tasks']))

            status = workflow['status']
            status_emoji = {
                'loaded': '📋',
                'running': '⚙️',
                'completed': '✅',
                'failed': '❌',
                'error': '⚠️'
            }.get(status, '📋')
            colb.metric("Status", f"{status_emoji} {status.upper()}")

            if workflow.get('last_execution'):
                result = "✅ Success" if workflow['last_execution'].get('success') else "❌ Failed"
                colc.metric("Last Run", result)

            colx, coly = st.columns(2)

            with colx:
                if st.button("▶️ Execute Workflow", use_container_width=True, type="primary"):
                    with st.spinner("Executing..."):
                        execute_workflow(st.session_state.current_workflow_id)
                    st.rerun()

            with coly:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()

    if st.session_state.current_workflow_id:
        st.divider()

        workflow = st.session_state.workflows[st.session_state.current_workflow_id]

        st.markdown('<div class="section-header">📊 Execution Status</div>', unsafe_allow_html=True)

        if workflow.get('last_execution'):
            exec_data = workflow['last_execution']

            if exec_data.get('success'):
                st.success("✅ Execution successful")
            else:
                st.error("❌ Execution failed")

            if 'timestamp' in exec_data:
                ts = datetime.fromisoformat(exec_data['timestamp'])
                st.caption(f"🕒 {ts.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.info("ℹ️ No execution data")

        st.divider()

        st.markdown('<div class="section-header">🔀 Workflow Visualization</div>', unsafe_allow_html=True)

        try:
            mermaid_code = generate_mermaid_code(workflow)

            try:
                from streamlit_mermaid import st_mermaid
                st_mermaid(mermaid_code, height=700)
            except ImportError:
                st.info("💡 Install `pip install streamlit-mermaid` for visualization")

                tasks = workflow['content'][0]['tasks']
                for task in tasks:
                    name = task.get('name', 'unnamed')
                    module = task.get('module', 'N/A')
                    function = task.get('function', 'N/A')
                    st.markdown(f"- **{name}**: `{module}.{function}`")

        except Exception as e:
            st.error(f"❌ Graph error: {e}")

            with st.expander("🐛 Debug"):
                st.code(mermaid_code if 'mermaid_code' in locals() else str(e))

        st.divider()

        st.markdown('<div class="section-header">📝 Task Results</div>', unsafe_allow_html=True)

        if workflow.get('last_execution') and 'results' in workflow['last_execution']:
            results = workflow['last_execution']['results']

            if not results:
                st.info("ℹ️ No task results")
            else:
                for name, result in results.items():
                    status = result['status']
                    icon = {'success': '✅', 'failed': '❌'}.get(status, '⚙️')

                    st.markdown(f"### {icon} {result['task_name']}")

                    col1, col2 = st.columns([3, 1])
                    col2.metric("Duration", f"{result['duration']:.3f}s")

                    if result.get('error'):
                        st.error(result['error'])

                    if result.get('output'):
                        with st.expander("📤 Output"):
                            st.json(result['output'])

                    st.divider()
        else:
            st.info("ℹ️ Execute workflow to see results")

def render_wallet_page():
    st.markdown('''
    <div class="main-header">
        <h1>🔐 Wallet Management</h1>
        <p>Manage secure credentials for your workflows</p>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown('<div class="section-header">🔐 Wallet Status</div>', unsafe_allow_html=True)

    if st.session_state.active_wallet:
        wallet = st.session_state.active_wallet

        col1, col2, col3 = st.columns(3)
        col1.success("✅ Loaded")
        col2.metric("Type", "🔒 Encrypted" if isinstance(wallet, Wallet) else "📄 Plain")
        col3.metric("Secrets", len(wallet.secrets))

        st.caption(f"📁 {wallet.wallet_file}")
    else:
        st.warning("⚠️ No Wallet Loaded")

    st.divider()

    tab1, tab2 = st.tabs(["📂 Load", "➕ Create"])

    with tab1:
        with st.form("load_form"):
            wallet_file = st.text_input("Wallet File", "wallet.enc")
            wallet_type = st.selectbox("Type", ["encrypted", "plain"])
            master_pwd = st.text_input("Master Password", type="password") if wallet_type == "encrypted" else None

            if st.form_submit_button("🔓 Load", use_container_width=True):
                load_wallet(wallet_file, wallet_type, master_pwd)

    with tab2:
        with st.form("create_form"):
            new_file = st.text_input("Wallet File", "my_wallet.enc")
            new_type = st.selectbox("Type", ["encrypted", "plain"], key="ct")
            new_pwd = st.text_input("Master Password", type="password", key="cp") if new_type == "encrypted" else None
            secrets = st.text_area("Secrets (JSON)", '{"key": "value"}', height=100)

            if st.form_submit_button("➕ Create", use_container_width=True):
                create_wallet(new_file, new_type, new_pwd, secrets)

    if st.session_state.active_wallet:
        st.divider()

        st.markdown('<div class="section-header">🔑 Secrets</div>', unsafe_allow_html=True)

        wallet = st.session_state.active_wallet

        if len(wallet.secrets) == 0:
            st.info("ℹ️ No secrets")
        else:
            for idx, key in enumerate(list(wallet.secrets.keys())):
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])

                col1.code(key)

                show_key = f"show_{key}"
                if show_key not in st.session_state.show_secrets:
                    st.session_state.show_secrets[show_key] = False

                if col2.button("👁️" if not st.session_state.show_secrets[show_key] else "🙈", 
                             key=f"view_{idx}", help="Show/Hide value"):
                    st.session_state.show_secrets[show_key] = not st.session_state.show_secrets[show_key]
                    st.rerun()

                edit_key = f"edit_{key}"
                if edit_key not in st.session_state.edit_secrets:
                    st.session_state.edit_secrets[edit_key] = False

                if col3.button("✏️", key=f"edit_{idx}", help="Edit value"):
                    st.session_state.edit_secrets[edit_key] = True
                    st.rerun()

                if col4.button("🗑️", key=f"del_{idx}", help="Delete"):
                    st.session_state[f"confirm_del_{key}"] = True
                    st.rerun()

                if st.session_state.show_secrets.get(show_key, False):
                    value = wallet.secrets[key]
                    st.markdown(f'<div class="secret-value">{value}</div>', unsafe_allow_html=True)

                if st.session_state.edit_secrets.get(edit_key, False):
                    with st.container():
                        st.caption(f"✏️ Editing: {key}")
                        new_value = st.text_input("New Value", value=wallet.secrets[key], 
                                                 type="password", key=f"new_val_{idx}")

                        col_save, col_cancel = st.columns(2)

                        if isinstance(wallet, Wallet):
                            pwd = st.text_input("Master Password", type="password", key=f"pwd_edit_{idx}")
                            if col_save.button("💾 Save", key=f"save_{idx}") and pwd and new_value:
                                update_secret(key, new_value, pwd)
                        else:
                            if col_save.button("💾 Save", key=f"save_{idx}") and new_value:
                                update_secret(key, new_value)

                        if col_cancel.button("❌ Cancel", key=f"cancel_{idx}"):
                            st.session_state.edit_secrets[edit_key] = False
                            st.rerun()

                if st.session_state.get(f"confirm_del_{key}"):
                    st.warning(f"🗑️ Delete '{key}'?")
                    c1, c2 = st.columns(2)

                    if isinstance(wallet, Wallet):
                        pwd = st.text_input("Master Password", type="password", key=f"pwd_del_{idx}")
                        if c1.button("✅ Confirm", key=f"conf_{idx}") and pwd:
                            delete_secret(key, pwd)
                            st.session_state[f"confirm_del_{key}"] = False
                    else:
                        if c1.button("✅ Confirm", key=f"conf_{idx}"):
                            delete_secret(key)
                            st.session_state[f"confirm_del_{key}"] = False

                    if c2.button("❌ Cancel", key=f"canc_{idx}"):
                        st.session_state[f"confirm_del_{key}"] = False
                        st.rerun()

                st.divider()

        st.divider()

        with st.form("add_form"):
            st.subheader("➕ Add Secret")
            col1, col2 = st.columns(2)
            new_key = col1.text_input("Key")
            new_val = col2.text_input("Value", type="password")

            add_pwd = st.text_input("Master Password", type="password") if isinstance(wallet, Wallet) else None

            if st.form_submit_button("➕ Add"):
                if new_key and new_val:
                    add_secret(new_key, new_val, add_pwd)

        if st.button("🔓 Unload Wallet", type="secondary"):
            unload_wallet()

def main():
    render_sidebar()

    if st.session_state.current_page == 'workflow':
        render_workflow_page()
    else:
        render_wallet_page()

if __name__ == "__main__":
    main()

# Run with: streamlit run streamlit_app.py --server.port 8502
