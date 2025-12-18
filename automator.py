import yaml
import argparse
import os
import inspect
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
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


# ============= WORKFLOW ENGINE =============
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    """Risultato di un task con output data"""
    task_name: str
    status: TaskStatus
    output: Any = None
    error: str = ""
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class WorkflowContext:
    """Contesto condiviso tra task con data propagation"""
    
    def __init__(self):
        self._results: Dict[str, TaskResult] = {}
        self._global_data: Dict[str, Any] = {}
    
    def set_task_result(self, task_name: str, result: TaskResult):
        """Salva risultato di un task"""
        self._results[task_name] = result
        logger.debug(f"Stored result for task '{task_name}'")
    
    def get_task_result(self, task_name: str) -> Optional[TaskResult]:
        """Recupera risultato di un task"""
        return self._results.get(task_name)
    
    def get_task_output(self, task_name: str) -> Any:
        """Recupera solo l'output di un task"""
        result = self._results.get(task_name)
        return result.output if result else None
    
    def get_last_output(self) -> Any:
        """Recupera l'output dell'ultimo task eseguito"""
        if not self._results:
            return None
        last_task = max(self._results.keys(), 
                       key=lambda k: self._results[k].timestamp)
        return self._results[last_task].output
    
    def set_global(self, key: str, value: Any):
        """Imposta variabile globale del workflow"""
        self._global_data[key] = value
    
    def get_global(self, key: str, default=None) -> Any:
        """Recupera variabile globale"""
        return self._global_data.get(key, default)
    
    def get_all_outputs(self) -> Dict[str, Any]:
        """Recupera tutti gli output dei task"""
        return {name: result.output 
                for name, result in self._results.items()}
    
    def get_all_results(self) -> Dict[str, TaskResult]:
        """Recupera tutti i risultati"""
        return dict(self._results)


class WorkflowEngine:
    """Engine per esecuzione workflow con data propagation"""
    
    def __init__(self, tasks: List[Dict], gdict: Dict, task_store: TaskResultStore, debug: bool = False, debug2: bool = False):
        self.tasks = tasks
        self.gdict = gdict
        self.context = WorkflowContext()
        self.task_store = task_store
        self.debug = debug
        self.debug2 = debug2
        self.tasks_map = {t.get('name'): t for t in tasks if t.get('name')}
        
    def execute(self) -> Tuple[bool, WorkflowContext]:
        """
        Esegue il workflow completo
        Returns: (success, context)
        """
        logger.info("=" * 70)
        logger.info("WORKFLOW ENGINE - EXECUTION START")
        logger.info("=" * 70)
        logger.info("")
        
        # Trova entry point
        entry_point = self._find_entry_point()
        if not entry_point:
            logger.error("No entry point found in workflow")
            return False, self.context
        
        logger.debug(f"Entry point: {entry_point}")
        
        # Esegui workflow
        current_task = entry_point
        executed_count = 0
        max_iterations = len(self.tasks) * 100
        
        while current_task and current_task != 'end':
            executed_count += 1
            
            if executed_count > max_iterations:
                logger.error("✗ Maximum workflow iterations reached (possible infinite loop)")
                return False, self.context
            
            # Esegui task corrente
            success = self._execute_task(current_task, executed_count)
            
            # Determina prossimo task
            task_def = self.tasks_map.get(current_task)
            if not task_def:
                logger.info(f"✓ Task '{current_task}' completed - no task definition found")
                break
                
            if success:
                next_task = task_def.get('on_success')
                if next_task:
                    logger.info(f"→ Branching on SUCCESS to: '{next_task}'")
            else:
                next_task = task_def.get('on_failure')
                if next_task:
                    logger.info(f"→ Branching on FAILURE to: '{next_task}'")
            
            # Se non c'è branching, termina
            if not next_task:
                logger.info(f"✓ Workflow completed (no next task after '{current_task}')")
                break
            
            current_task = next_task
        
        if current_task == 'end':
            logger.info("✓ Workflow reached 'end' marker")
        
        # Valuta risultato finale
        failed_count = sum(
            1 for r in self.context._results.values() 
            if r.status == TaskStatus.FAILED
        )
        success_count = sum(
            1 for r in self.context._results.values() 
            if r.status == TaskStatus.SUCCESS
        )
        
        all_success = failed_count == 0
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("WORKFLOW EXECUTION SUMMARY")
        logger.info("=" * 70)
        
        # Log tasks riusciti
        if success_count > 0:
            logger.info(f"✓ SUCCEEDED TASKS ({success_count}):")
            for name, result in self.context._results.items():
                if result.status == TaskStatus.SUCCESS:
                    logger.info(f"   ✓ {name} ({result.duration:.2f}s)")
        
        # Log tasks falliti
        if failed_count > 0:
            logger.warning(f"✗ FAILED TASKS ({failed_count}):")
            for name, result in self.context._results.items():
                if result.status == TaskStatus.FAILED:
                    logger.warning(f"   ✗ {name} - {result.error} ({result.duration:.2f}s)")
        
        logger.info("=" * 70)
        if all_success:
            logger.info(f"✓ Workflow completed SUCCESSFULLY")
        else:
            logger.warning(f"⚠ Workflow completed with ERRORS")
        
        logger.info(f"Total: {executed_count} | Succeeded: {success_count} | Failed: {failed_count}")
        logger.info("=" * 70)
        
        return all_success, self.context
    
    def _find_entry_point(self) -> Optional[str]:
        """Trova il task di ingresso (non referenziato da altri)"""
        referenced = set()
        for task in self.tasks:
            if task.get('on_success'):
                referenced.add(task.get('on_success'))
            if task.get('on_failure'):
                referenced.add(task.get('on_failure'))
        
        for task in self.tasks:
            name = task.get('name')
            if name and name not in referenced:
                return name
        
        # Fallback: primo task
        return self.tasks[0].get('name') if self.tasks else None
    
    def _execute_task(self, task_name: str, task_num: int) -> bool:
        """Esegue un singolo task con data propagation"""
        task_def = self.tasks_map.get(task_name)
        if not task_def:
            logger.error(f"Task '{task_name}' not found in workflow definition")
            return False
        
        logger.info(f"▶ [{task_num}] Executing task: '{task_name}'")
        start_time = datetime.now()
        
        try:
            # Estrai module e function
            module_name, func_name, task_params = self._parse_task_definition(task_def)
            
            if self.debug:
                logger.debug(f"   Module: {module_name}, Function: {func_name}")
                logger.debug(f"   Parameters: {task_params}")
            
            # === DATA PROPAGATION ===
            # Inietta output del task precedente
            last_output = self.context.get_last_output()
            if last_output is not None:
                task_params['input'] = last_output
                logger.debug(f"   Injected previous output into '{task_name}'")
            
            # Inietta context per accesso a tutti gli output
            task_params['workflow_context'] = self.context
            
            # Inietta task_store (retrocompatibilità)
            task_id = f"task_{task_num}_{task_name}"
            task_params['task_id'] = task_id
            task_params['task_store'] = self.task_store
            
            # Carica ed esegui modulo
            if self.debug:
                logger.debug(f"   Loading module: {module_name}")
            
            module = __import__(module_name)
            
            # Set gdict nel modulo
            if hasattr(module, 'setgdict'):
                module.setgdict(module, self.gdict)
            
            if self.debug2:
                logger.debug(f"   Global dict state: {list(self.gdict.keys())}")
            
            func = getattr(module, func_name)
            result = func(module, task_params)
            
            # Gestisci risultato (bool o tupla)
            if isinstance(result, tuple) and len(result) == 2:
                success, output = result
                logger.debug(f"   Task returned tuple: success={success}, output={type(output)}")
            else:
                success = bool(result)
                output = None
                logger.debug(f"   Task returned bool: {success}")
            
            # Salva risultato
            duration = (datetime.now() - start_time).total_seconds()
            task_result = TaskResult(
                task_name=task_name,
                status=TaskStatus.SUCCESS if success else TaskStatus.FAILED,
                output=output,
                error="" if success else "Task returned False",
                duration=duration
            )
            self.context.set_task_result(task_name, task_result)
            
            # Salva anche in task_store per retrocompatibilità
            if self.task_store:
                self.task_store.set_result(task_id, success, task_result.error)
            
            if success:
                logger.info(f"   ✓ Task '{task_name}' SUCCEEDED ({duration:.2f}s)")
            else:
                logger.warning(f"   ✗ Task '{task_name}' FAILED ({duration:.2f}s)")
            
            return success
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"   ✗ Task '{task_name}' EXCEPTION: {e}", exc_info=self.debug2)
            
            task_result = TaskResult(
                task_name=task_name,
                status=TaskStatus.FAILED,
                error=str(e),
                duration=duration
            )
            self.context.set_task_result(task_name, task_result)
            
            # Salva anche in task_store
            if self.task_store:
                task_id = f"task_{task_num}_{task_name}"
                self.task_store.set_result(task_id, False, str(e))
            
            return False
    
    def _parse_task_definition(self, task_def: Dict) -> Tuple[str, str, Dict]:
        """Estrae module, function e parametri da task definition"""
        # Formato 1: module e function espliciti
        if 'module' in task_def and 'function' in task_def:
            module_name = task_def['module']
            func_name = task_def['function']
            params = {k: v for k, v in task_def.items()
                     if k not in ['name', 'module', 'function', 'on_success', 'on_failure']}
            return module_name, func_name, params
        
        # Formato 2: module.function come chiave
        for key in task_def.keys():
            if key not in ['name', 'on_success', 'on_failure'] and '.' in key:
                module_name, func_name = key.split('.', 1)
                params = task_def.get(key) or {}
                if not isinstance(params, dict):
                    params = {}
                return module_name, func_name, params
        
        raise ValueError(f"Invalid task definition: no module.function found in {task_def}")


# ============= WORKFLOW MAP VISUALIZATION =============
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


# ============= MAIN =============
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
    
    # istanza unica per tutti i task (retrocompatibilità)
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
        
        # ===== ESEGUI CON WORKFLOW ENGINE =====
        engine = WorkflowEngine(tasks, gdict, task_store, DEBUG, DEBUG2)
        workflow_success, context = engine.execute()
        
        # Calcola tempo totale
        nowend = datetime.now()
        delta = (nowend - nowstart).total_seconds()
        
        logger.info("")
        logger.info(f"Start: {nowstart.strftime('%Y-%m-%d %H:%M:%S')} | "
                   f"End: {nowend.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total execution time: {delta:.2f} seconds")
        logger.info("=" * 70)
        
        return 0 if workflow_success else 1
        
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

# Example usage:
#export OA_WALLET_PASSWORD="your_master_password"
#python3.12 ./automator.py ./mywf.yaml
