import yaml
import argparse
import os
import inspect
import sys
from datetime import datetime
from logger_config import AutomatorLogger, TaskLogger
import oacommon
from taskstore import TaskResultStore
from wallet import Wallet, PlainWallet, resolve_dict_placeholders

logger = AutomatorLogger.get_logger('automator')

gdict = {}
cwd = os.getcwd()
oacommon.setgdict(oacommon, gdict)
modulepath = os.path.join(cwd, 'modules')
if os.path.exists(modulepath):
    sys.path.append(modulepath)

myself = lambda: inspect.stack()[1][3]
findinlist = lambda y, list: [x for x in list if y in x]


def print_workflow_map(tasks):
    """
    Stampa una mappa visuale del workflow prima dell'esecuzione
    """
    logger.info("=" * 70)
    logger.info("WORKFLOW MAP")
    logger.info("=" * 70)
    
    # Identifica entry point (primo task o task senza predecessori)
    tasks_map = {t.get('name'): t for t in tasks if t.get('name')}
    
    # Trova tutti i task referenziati
    referenced = set()
    for t in tasks:
        if t.get('on_success'):
            referenced.add(t.get('on_success'))
        if t.get('on_failure'):
            referenced.add(t.get('on_failure'))
    
    # Entry points sono task NON referenziati da altri (o il primo)
    entry_points = []
    for t in tasks:
        name = t.get('name')
        if name and name not in referenced:
            entry_points.append(name)
    
    if not entry_points:
        entry_points = [tasks[0].get('name')] if tasks else []
    
    logger.info(f"Entry point(s): {', '.join(entry_points)}")
    logger.info("")
    
    # Stampa ogni task con i suoi branching
    for task in tasks:
        name = task.get('name', 'unnamed')
        on_success = task.get('on_success')
        on_failure = task.get('on_failure')
        
        # Identifica module.function
        module_name = None
        func_name = None
        
        if 'module' in task and 'function' in task:
            module_name = task['module']
            func_name = task['function']
        else:
            for key in task.keys():
                if key not in ['name', 'on_success', 'on_failure'] and '.' in key:
                    module_name, func_name = key.split('.', 1)
                    break
        
        logger.info(f"  ┌{'─' * (len(name) + 2)}┐")
        logger.info(f"  │ {name} │")
        if module_name and func_name:
            logger.info(f"  │ {module_name}.{func_name} │")
        logger.info(f"  └{'─' * (len(name) + 2)}┘")
        
        if on_success or on_failure:
            if on_success:
                logger.info(f"    ✓ SUCCESS → {on_success}")
            if on_failure:
                logger.info(f"    ✗ FAILURE → {on_failure}")
        else:
            logger.info(f"    → (linear/end)")
        
        logger.info("")
    
    logger.info("=" * 70)
    logger.info("")


def analyze_workflow_paths(tasks):
    """
    Analizza tutti i possibili percorsi del workflow
    """
    tasks_map = {t.get('name'): t for t in tasks if t.get('name')}
    
    def trace_path(start_task, path_type="success", visited=None):
        if visited is None:
            visited = set()
        
        if start_task == 'end' or start_task is None:
            return []
        
        if start_task in visited:
            return [f"[LOOP: {start_task}]"]
        
        if start_task not in tasks_map:
            return [f"[NOT FOUND: {start_task}]"]
        
        visited = visited.copy()
        visited.add(start_task)
        
        task = tasks_map[start_task]
        path = [start_task]
        
        next_task = task.get('on_success')
        if next_task:
            path.extend(trace_path(next_task, "success", visited))
        
        return path
    
    # Trova entry point
    referenced = set()
    for t in tasks:
        if t.get('on_success'):
            referenced.add(t.get('on_success'))
        if t.get('on_failure'):
            referenced.add(t.get('on_failure'))
    
    entry_point = None
    for t in tasks:
        name = t.get('name')
        if name and name not in referenced:
            entry_point = name
            break
    
    if not entry_point and tasks:
        entry_point = tasks[0].get('name')
    
    logger.info("=" * 70)
    logger.info("WORKFLOW PATHS ANALYSIS")
    logger.info("=" * 70)
    
    if entry_point:
        # Percorso ottimale (tutti success)
        success_path = trace_path(entry_point, "success")
        logger.info(f"✓ SUCCESS PATH: {' → '.join(success_path)}")
        
        # Analizza failure paths per ogni task
        logger.info("")
        logger.info("✗ FAILURE SCENARIOS:")
        for task in tasks:
            name = task.get('name')
            on_failure = task.get('on_failure')
            if on_failure:
                failure_path = trace_path(on_failure, "failure")
                logger.info(f"  • If '{name}' fails → {' → '.join(failure_path)}")
    
    logger.info("=" * 70)
    logger.info("")


def main():
    """Main entry point for Open-Automator"""
    myparser = argparse.ArgumentParser(
        description='exec open-automator tasks',
        allow_abbrev=False
    )
    myparser.add_argument('tasks', metavar='tasks', type=str,
                          help='yaml for task description')
    myparser.add_argument('-d', action='store_true',
                          help='debug enable')
    myparser.add_argument('-d2', action='store_true',
                          help='debug2 enable')
    myparser.add_argument('-t', action='store_true',
                          help='trace enable')
    myparser.add_argument('--log-dir', type=str, default='./logs',
                          help='log directory path (default: ./logs)')
    myparser.add_argument('--console-level', type=str, default='INFO',
                          choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                          help='console log level (default: INFO)')
    myparser.add_argument('--file-level', type=str, default='DEBUG',
                          choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                          help='file log level (default: DEBUG)')
    myparser.add_argument('--dry-run', action='store_true',
                          help='show workflow map without executing')

    args = myparser.parse_args()

    # Setup logging PRIMA di tutto
    try:
        AutomatorLogger.setup_logging(
            log_dir=args.log_dir,
            console_level=args.console_level,
            file_level=args.file_level
        )
    except Exception as e:
        print(f"ERROR: Failed to setup logging: {e}")
        return 5

    tasksfile = args.tasks
    DEBUG = args.d
    DEBUG2 = args.d2
    TRACE = args.t

    gdict['DEBUG'] = args.d
    gdict['DEBUG2'] = args.d2
    gdict['TRACE'] = args.t

    # Adatta livello console se -d o -d2
    if DEBUG2:
        AutomatorLogger.set_console_level('DEBUG')
        logger.debug("DEBUG2 mode enabled - console level set to DEBUG")
    elif DEBUG:
        AutomatorLogger.set_console_level('INFO')
        logger.debug("DEBUG mode enabled")

    if not tasksfile:
        tasksfile = 'automator.yaml'

    logger.info("=" * 70)
    logger.info(f"Open-Automator started - Processing: {tasksfile}")
    logger.info("=" * 70)

    nowstart = datetime.now()

    # istanza unica per tutti i task
    task_store = TaskResultStore()

    try:
        # Carica configurazione YAML
        logger.debug(f"Loading YAML configuration from: {tasksfile}")

        if not os.path.exists(tasksfile):
            raise FileNotFoundError(f"Task file not found: {tasksfile}")

        with open(tasksfile) as file:
            conf = yaml.load(file, Loader=yaml.FullLoader)

        logger.debug("Configuration loaded successfully")

        if not conf or not isinstance(conf, list) or 'tasks' not in conf[0]:
            raise ValueError("Invalid YAML structure - expected 'tasks' key")

        tasks = conf[0]['tasks']
        sizetask = len(tasks)
        logger.info(f"Found {sizetask} tasks to execute")
        logger.info("")

        # ===== MOSTRA MAPPA WORKFLOW =====
        print_workflow_map(tasks)
        analyze_workflow_paths(tasks)

        # Se dry-run, esci qui
        if args.dry_run:
            logger.info("DRY-RUN mode - workflow execution skipped")
            return 0

        # Crea mappa task_name -> task_definition per workflow branching
        tasks_map = {}
        for t in tasks:
            name = t.get('name')
            if name:
                tasks_map[name] = t

        # Rileva se siamo in modalità workflow: almeno un task ha on_success/on_failure
        workflow_mode = any(
            t.get('on_success') or t.get('on_failure') 
            for t in tasks
        )

        if workflow_mode:
            logger.debug("Workflow mode detected (on_success/on_failure present)")
        else:
            logger.debug("Linear mode detected (no branching)")

        failed_tasks = []
        success_tasks = []
        executed_count = 0
        max_iterations = sizetask * 100  # protezione loop infiniti

        # Supporto workflow: se primo task ha 'name', parti da lì, altrimenti sequenziale
        current_task_index = 0
        current_task_name = None
        in_workflow = workflow_mode

        logger.info("=" * 70)
        logger.info("WORKFLOW EXECUTION START")
        logger.info("=" * 70)
        logger.info("")

        while executed_count < max_iterations:
            # Decidi quale task eseguire
            if current_task_name:
                # Modalità workflow: cerco task per nome
                if current_task_name == 'end':
                    logger.info("✓ Workflow reached 'end' marker")
                    break
                if current_task_name not in tasks_map:
                    logger.error(f"✗ Task '{current_task_name}' not found in workflow")
                    break
                task = tasks_map[current_task_name]
            else:
                # Modalità lineare: prendo task dalla lista
                if current_task_index >= len(tasks):
                    break
                task = tasks[current_task_index]

            executed_count += 1
            task_name = task.get('name', f'Unnamed task {executed_count}')

            # ===== SUPPORTO DUE FORMATI YAML =====
            module_name = None
            func_name = None
            task_param = {}
            
            # Controlla formato 1: module e function separate
            if 'module' in task and 'function' in task:
                module_name = task['module']
                func_name = task['function']
                task_param = {k: v for k, v in task.items() 
                             if k not in ['name', 'module', 'function', 'on_success', 'on_failure']}
                
            else:
                # Formato 2: cerca chiave module.function
                for key in task.keys():
                    if key not in ['name', 'on_success', 'on_failure'] and '.' in key:
                        module_name, func_name = key.split('.', 1)
                        task_param = task.get(key) or {}
                        break

            if not module_name or not func_name:
                logger.warning(f"⚠ Task '{task_name}' has no valid module.function, skipping")
                current_task_index += 1
                current_task_name = None
                continue

            if not isinstance(task_param, dict):
                task_param = {}

            # genera un id univoco per il task
            task_id = f"task_{executed_count}"

            # inietta task_id e task_store
            task_param['task_id'] = task_id
            task_param['task_store'] = task_store

            task_success = False
            task_start = datetime.now()

            try:
                with TaskLogger(logger, task_name, executed_count, sizetask):
                    if DEBUG:
                        logger.debug(f"Module: {module_name}, Function: {func_name}")
                        logger.debug(f"Parameters: {task_param}")

                    logger.debug(f"Loading module: {module_name}, function: {func_name}")

                    if DEBUG2:
                        logger.debug(f"Global dict state: {list(gdict.keys())}")

                    m = __import__(module_name)

                    # Imposta gdict nel modulo
                    mfunc = getattr(m, 'setgdict')
                    mfunc(m, gdict)

                    # Esegui funzione
                    func = getattr(m, func_name)
                    task_success = func(m, task_param)

                    task_end = datetime.now()
                    task_duration = (task_end - task_start).total_seconds()

                    # Log risultato task
                    if task_success:
                        logger.info(f"✓ Task '{task_name}' SUCCEEDED (duration: {task_duration:.2f}s)")
                        success_tasks.append({
                            'task_num': executed_count,
                            'task_name': task_name,
                            'duration': task_duration
                        })
                    else:
                        result = task_store.get_result(task_id)
                        err_msg = result.get('error') if result else 'Task returned False'
                        logger.warning(f"✗ Task '{task_name}' FAILED: {err_msg} (duration: {task_duration:.2f}s)")
                        failed_tasks.append({
                            'task_num': executed_count,
                            'task_name': task_name,
                            'error': err_msg,
                            'duration': task_duration
                        })

            except Exception as e:
                task_end = datetime.now()
                task_duration = (task_end - task_start).total_seconds()
                
                logger.error(f"✗ Task '{task_name}' FAILED with exception: {e} (duration: {task_duration:.2f}s)", exc_info=DEBUG2)
                failed_tasks.append({
                    'task_num': executed_count,
                    'task_name': task_name,
                    'error': str(e),
                    'duration': task_duration
                })
                task_success = False

            # =========== WORKFLOW BRANCHING LOGIC ===========
            on_success = task.get('on_success')
            on_failure = task.get('on_failure')

            if on_success or on_failure:
                # Task ha branching esplicito
                in_workflow = True
                if task_success:
                    next_task = on_success
                    if next_task:
                        logger.info(f"→ Branching on SUCCESS to: '{next_task}'")
                else:
                    next_task = on_failure
                    if next_task:
                        logger.info(f"→ Branching on FAILURE to: '{next_task}'")

                if next_task and next_task != 'end':
                    current_task_name = next_task
                else:
                    # Fine workflow
                    logger.info("✓ Workflow completed (reached end or no next task)")
                    break
            else:
                # Task NON ha branching
                if in_workflow:
                    # Se siamo già in modalità workflow, l'assenza di branching significa FINE
                    logger.info(f"✓ Task '{task_name}' has no branching - workflow ends here")
                    break
                else:
                    # Modalità lineare pura: continua con task successivo in lista
                    current_task_index += 1
                    current_task_name = None

        if executed_count >= max_iterations:
            logger.error("✗ Maximum workflow iterations reached (possible infinite loop)")

        nowend = datetime.now()
        delta = (nowend - nowstart).total_seconds()

        logger.info("")
        logger.info("=" * 70)
        logger.info("WORKFLOW EXECUTION SUMMARY")
        logger.info("=" * 70)
        
        # Log tasks riusciti
        if success_tasks:
            logger.info(f"✓ SUCCEEDED TASKS ({len(success_tasks)}):")
            for st in success_tasks:
                logger.info(f"  ✓ [{st['task_num']}] {st['task_name']} ({st['duration']:.2f}s)")
        
        # Log tasks falliti
        if failed_tasks:
            logger.warning(f"✗ FAILED TASKS ({len(failed_tasks)}):")
            for ft in failed_tasks:
                logger.warning(f"  ✗ [{ft['task_num']}] {ft['task_name']} - {ft['error']} ({ft['duration']:.2f}s)")
        
        logger.info("=" * 70)
        
        if failed_tasks:
            logger.warning(f"⚠ Workflow completed with ERRORS")
        else:
            logger.info(f"✓ Workflow completed SUCCESSFULLY")

        logger.info(
            f"Total: {executed_count} | Succeeded: {len(success_tasks)} | "
            f"Failed: {len(failed_tasks)}"
        )
        logger.info(
            f"Start: {nowstart.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"End: {nowend.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        logger.info(f"Total execution time: {delta:.2f} seconds")
        logger.info("=" * 70)

        return 0 if not failed_tasks else 1

    except FileNotFoundError as e:
        logger.critical(f"Configuration file error: {e}")
        return 2
    except yaml.YAMLError as e:
        logger.critical(f"Invalid YAML syntax in {tasksfile}: {e}")
        return 3
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 4


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)


#export OA_WALLET_PASSWORD="your_master_password"
#python3.12 ./automator.py ./mywf.yaml
