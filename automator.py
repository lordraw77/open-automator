"""
Open-Automator CLI - Complete with Workflow Manager Integration + Logging
"""

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

logger = AutomatorLogger.get_logger("automator")

# Inizializza gdict globale
gdict = {}
cwd = os.getcwd()
oacommon.setgdict(oacommon, gdict)

# Aggiungi modules al path
module_path = os.path.join(cwd, "modules")
if os.path.exists(module_path):
    sys.path.append(module_path)

# Helper functions
myself = lambda: inspect.stack()[1][3]
find_in_list = lambda y, list: [x for x in list if y in x]

# Environment config
ENV_CONFIG = {
    "OA_WALLET_FILE": os.environ.get("OA_WALLET_FILE", "data/wallet.enc"),
    "OA_WALLET_PASSWORD": os.environ.get("OA_WALLET_PASSWORD", "changeme"),
    "WORKFLOW_PATH": os.environ.get("WORKFLOW_PATH", "workflows"),
    "LOGLEVEL": os.environ.get("LOGLEVEL", "INFO"),
}

def get_env_config():
    return ENV_CONFIG.copy()

def log_environment_config():
    logger.info("Environment Configuration:")
    for key, value in ENV_CONFIG.items():
        if "PASSWORD" in key:
            logger.info(f"  {key:20} = {'*' * 8}")
        else:
            logger.info(f"  {key:20} = {value}")

# ========================================
# CLASSI ORIGINALI (identiche)
# ========================================

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TaskResult:
    task_name: str
    status: TaskStatus
    output: Any = None
    error: str = ""
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

class WorkflowContext:
    def __init__(self):
        self.results: Dict[str, TaskResult] = {}
        self.global_data: Dict[str, Any] = {}

    def set_task_result(self, task_name: str, result: TaskResult):
        self.results[task_name] = result
        logger.debug(f"Stored result for task: {task_name}")

    def get_task_result(self, task_name: str) -> Optional[TaskResult]:
        return self.results.get(task_name)

    def get_task_output(self, task_name: str) -> Any:
        result = self.results.get(task_name)
        return result.output if result else None

    def get_last_output(self) -> Any:
        if not self.results:
            return None
        last_task = max(self.results.keys(), key=lambda k: self.results[k].timestamp)
        return self.results[last_task].output

    def set_global(self, key: str, value: Any):
        self.global_data[key] = value

    def get_global(self, key: str, default=None) -> Any:
        return self.global_data.get(key, default)

    def get_all_outputs(self) -> Dict[str, Any]:
        return {name: result.output for name, result in self.results.items()}

    def get_all_results(self) -> Dict[str, TaskResult]:
        return dict(self.results)

class WorkflowEngine:
    def __init__(self, tasks: List[Dict], gdict: Dict, taskstore: TaskResultStore, 
                 debug: bool = False, debug2: bool = False):
        self.tasks = tasks
        self.gdict = gdict
        self.context = WorkflowContext()
        self.taskstore = taskstore
        self.debug = debug
        self.debug2 = debug2
        self.tasks_map = {t.get("name"): t for t in tasks if t.get("name")}

    def execute(self) -> Tuple[bool, WorkflowContext]:
        logger.info("=" * 70)
        logger.info("WORKFLOW ENGINE - EXECUTION START")
        logger.info("=" * 70)

        entry_point = self._find_entry_point()
        if not entry_point:
            logger.error("No entry point found in workflow")
            return False, self.context

        logger.debug(f"Entry point: {entry_point}")

        current_task = entry_point
        executed_count = 0
        max_iterations = len(self.tasks) * 100

        while current_task and current_task != "end":
            executed_count += 1

            if executed_count > max_iterations:
                logger.error("Maximum workflow iterations reached (possible infinite loop)")
                return False, self.context

            success = self._execute_task(current_task, executed_count)

            task_def = self.tasks_map.get(current_task)
            if not task_def:
                logger.info(f"Task '{current_task}' completed - no task definition found")
                break

            if success:
                next_task = task_def.get("on_success")
                if next_task:
                    logger.info(f"Branching on SUCCESS to: {next_task}")
            else:
                next_task = task_def.get("on_failure")
                if next_task:
                    logger.info(f"Branching on FAILURE to: {next_task}")

            if not next_task:
                logger.info(f"Workflow completed (no next task after '{current_task}')")
                break

            current_task = next_task

        if current_task == "end":
            logger.info("Workflow reached 'end' marker")

        failed_count = sum(1 for r in self.context.results.values() if r.status == TaskStatus.FAILED)
        success_count = sum(1 for r in self.context.results.values() if r.status == TaskStatus.SUCCESS)
        all_success = failed_count == 0

        logger.info("")
        logger.info("=" * 70)
        logger.info("WORKFLOW EXECUTION SUMMARY")
        logger.info("=" * 70)

        if success_count > 0:
            logger.info(f"SUCCEEDED TASKS: {success_count}")
            for name, result in self.context.results.items():
                if result.status == TaskStatus.SUCCESS:
                    logger.info(f"  ✅ {name} ({result.duration:.2f}s)")

        if failed_count > 0:
            logger.warning(f"FAILED TASKS: {failed_count}")
            for name, result in self.context.results.items():
                if result.status == TaskStatus.FAILED:
                    logger.warning(f"  ❌ {name} - {result.error} ({result.duration:.2f}s)")

        logger.info("=" * 70)

        if all_success:
            logger.info("✅ Workflow completed SUCCESSFULLY")
        else:
            logger.warning("❌ Workflow completed with ERRORS")

        logger.info(f"Total: {executed_count} | Succeeded: {success_count} | Failed: {failed_count}")
        logger.info("=" * 70)

        return all_success, self.context

    def _find_entry_point(self) -> Optional[str]:
        referenced = set()
        for task in self.tasks:
            if task.get("on_success"):
                referenced.add(task.get("on_success"))
            if task.get("on_failure"):
                referenced.add(task.get("on_failure"))

        for task in self.tasks:
            name = task.get("name")
            if name and name not in referenced:
                return name

        return self.tasks[0].get("name") if self.tasks else None

    def _execute_task(self, task_name: str, task_num: int) -> bool:
        task_def = self.tasks_map.get(task_name)

        if not task_def:
            logger.error(f"Task '{task_name}' not found in workflow definition")
            return False

        logger.info(f"[{task_num}] Executing task: {task_name}")
        start_time = datetime.now()

        try:
            module_name, func_name, task_params = self._parse_task_definition(task_def)

            if self.debug:
                logger.debug(f"  Module: {module_name}, Function: {func_name}")
                logger.debug(f"  Parameters: {task_params}")

            last_output = self.context.get_last_output()
            if last_output is not None:
                task_params["input"] = last_output
                logger.debug(f"  Injected previous output into '{task_name}'")

            task_params["workflow_context"] = self.context

            task_id = f"task{task_num}_{task_name}"
            task_params["task_id"] = task_id
            task_params["taskstore"] = self.taskstore

            if self.debug:
                logger.debug(f"  Loading module: {module_name}")

            module = __import__(module_name)

            if hasattr(module, "setgdict"):
                module.setgdict(module, self.gdict)

            if self.debug2:
                logger.debug(f"  Global dict state: {list(self.gdict.keys())}")

            func = getattr(module, func_name)
            result = func(module, task_params)

            if isinstance(result, tuple) and len(result) == 2:
                success, output = result
                logger.debug(f"  Task returned: (success={success}, output={type(output).__name__})")
            else:
                success = bool(result)
                output = None
                logger.debug(f"  Task returned: bool={success}")

            duration = (datetime.now() - start_time).total_seconds()

            task_result = TaskResult(
                task_name=task_name,
                status=TaskStatus.SUCCESS if success else TaskStatus.FAILED,
                output=output,
                error="" if success else "Task returned False",
                duration=duration
            )

            self.context.set_task_result(task_name, task_result)

            if self.taskstore:
                self.taskstore.set_result(task_id, success, task_result.error)

            if success:
                logger.info(f"  ✅ Task '{task_name}' SUCCEEDED ({duration:.2f}s)")
            else:
                logger.warning(f"  ❌ Task '{task_name}' FAILED ({duration:.2f}s)")

            return success

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"  ❌ Task '{task_name}' EXCEPTION: {e}", exc_info=self.debug2)

            task_result = TaskResult(
                task_name=task_name,
                status=TaskStatus.FAILED,
                error=str(e),
                duration=duration
            )

            self.context.set_task_result(task_name, task_result)

            if self.taskstore:
                task_id = f"task{task_num}_{task_name}"
                self.taskstore.set_result(task_id, False, str(e))

            return False

    def _parse_task_definition(self, task_def: Dict) -> Tuple[str, str, Dict]:
        if "module" in task_def and "function" in task_def:
            module_name = task_def["module"]
            func_name = task_def["function"]
            params = {k: v for k, v in task_def.items() 
                     if k not in ["name", "module", "function", "on_success", "on_failure"]}
            return module_name, func_name, params

        for key in task_def.keys():
            if key not in ["name", "on_success", "on_failure"] and "." in key:
                module_name, func_name = key.split(".", 1)
                params = task_def.get(key) or {}
                if not isinstance(params, dict):
                    params = {}
                return module_name, func_name, params

        raise ValueError(f"Invalid task definition: no module.function found in {task_def}")

def print_workflow_map(tasks):
    logger.info("=" * 70)
    logger.info("WORKFLOW MAP")
    logger.info("=" * 70)

    tasks_map = {t.get("name"): t for t in tasks if t.get("name")}

    referenced = set()
    for t in tasks:
        if t.get("on_success"):
            referenced.add(t.get("on_success"))
        if t.get("on_failure"):
            referenced.add(t.get("on_failure"))

    entry_points = []
    for t in tasks:
        name = t.get("name")
        if name and name not in referenced:
            entry_points.append(name)

    if not entry_points:
        entry_points = [tasks[0].get("name")] if tasks else []

    logger.info(f"Entry points: {', '.join(entry_points)}")
    logger.info("")

    for task in tasks:
        name = task.get("name", "unnamed")
        on_success = task.get("on_success")
        on_failure = task.get("on_failure")

        logger.info(f"  {'▶' * 3}")
        logger.info(f"  {name}")

        module_name = None
        func_name = None

        if "module" in task and "function" in task:
            module_name = task["module"]
            func_name = task["function"]
        else:
            for key in task.keys():
                if key not in ["name", "on_success", "on_failure"] and "." in key:
                    module_name, func_name = key.split(".", 1)
                    break

        if module_name and func_name:
            logger.info(f"    {module_name}.{func_name}")

        logger.info(f"  {'▶' * 3}")

        if on_success or on_failure:
            if on_success:
                logger.info(f"    ✅ SUCCESS → {on_success}")
            if on_failure:
                logger.info(f"    ❌ FAILURE → {on_failure}")
        else:
            logger.info(f"    → (linear/end)")

        logger.info("")

    logger.info("=" * 70)
    logger.info("")

def analyze_workflow_paths(tasks):
    tasks_map = {t.get("name"): t for t in tasks if t.get("name")}

    def trace_path(start_task, visited=None):
        if visited is None:
            visited = set()
        if start_task == "end" or start_task is None:
            return []
        if start_task in visited:
            return [f"LOOP:{start_task}"]
        if start_task not in tasks_map:
            return [f"NOT_FOUND:{start_task}"]

        visited = visited.copy()
        visited.add(start_task)
        task = tasks_map[start_task]
        path = [start_task]
        next_task = task.get("on_success")
        if next_task:
            path.extend(trace_path(next_task, visited))
        return path

    referenced = set()
    for t in tasks:
        if t.get("on_success"):
            referenced.add(t.get("on_success"))
        if t.get("on_failure"):
            referenced.add(t.get("on_failure"))

    entry_point = None
    for t in tasks:
        name = t.get("name")
        if name and name not in referenced:
            entry_point = name
            break

    if not entry_point and tasks:
        entry_point = tasks[0].get("name")

    logger.info("=" * 70)
    logger.info("WORKFLOW PATHS ANALYSIS")
    logger.info("=" * 70)

    if entry_point:
        success_path = trace_path(entry_point)
        logger.info(f"SUCCESS PATH: {' → '.join(success_path)}")
        logger.info("")

        logger.info("FAILURE SCENARIOS:")
        for task in tasks:
            name = task.get("name")
            on_failure = task.get("on_failure")
            if on_failure:
                failure_path = trace_path(on_failure)
                logger.info(f"  If '{name}' fails → {' → '.join(failure_path)}")

    logger.info("=" * 70)
    logger.info("")

# ========================================
# MAIN CON LOGGING SETUP
# ========================================

def main():
    myparser = argparse.ArgumentParser(
        description="exec open-automator tasks",
        allow_abbrev=False
    )
    myparser.add_argument("tasks", metavar="tasks", type=str, nargs="?",
                         help="yaml for task description")
    myparser.add_argument("-d", action="store_true", help="debug enable")
    myparser.add_argument("-d2", action="store_true", help="debug2 enable")
    myparser.add_argument("-t", action="store_true", help="trace enable")
    myparser.add_argument("--log-dir", type=str, default=".logs",
                         help="log directory path (default: .logs)")
    myparser.add_argument("--console-level", type=str, default=None,
                         choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                         help="console log level (default: from LOGLEVEL env or INFO)")
    myparser.add_argument("--file-level", type=str, default="DEBUG",
                         choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                         help="file log level (default: DEBUG)")
    myparser.add_argument("--dry-run", action="store_true",
                         help="show workflow map without executing")
    myparser.add_argument("--use-manager", action="store_true",
                         help="use workflow manager (experimental)")
    myparser.add_argument("--stats", action="store_true",
                         help="show workflow manager statistics (requires --use-manager)")

    args = myparser.parse_args()

    # ========================================
    # SETUP LOGGING (CRITICO!)
    # ========================================
    console_level = args.console_level if args.console_level else ENV_CONFIG["LOGLEVEL"]

    try:
        AutomatorLogger.setup_logging(
            log_dir=args.log_dir,
            console_level=console_level,
            file_level=args.file_level
        )
    except Exception as e:
        print(f"ERROR: Failed to setup logging: {e}")
        return 5

    # Flags debug
    DEBUG = args.d
    DEBUG2 = args.d2
    TRACE = args.t

    gdict["DEBUG"] = args.d
    gdict["DEBUG2"] = args.d2
    gdict["TRACE"] = args.t

    # Adatta livello console se -d o -d2
    if DEBUG2:
        AutomatorLogger.set_console_level("DEBUG")
        logger.debug("DEBUG2 mode enabled - console level set to DEBUG")
    elif DEBUG:
        AutomatorLogger.set_console_level("INFO")
        logger.debug("DEBUG mode enabled")

    log_environment_config()

    # ========================================
    # MODALITÀ CON WORKFLOW MANAGER (opzionale)
    # ========================================
    if args.use_manager or args.stats:
        try:
            from workflow_manager import WorkflowManagerFacade

            workflow_manager = WorkflowManagerFacade(max_concurrent_executions=5)

            if args.stats:
                logger.info("=" * 70)
                logger.info("WORKFLOW MANAGER STATISTICS")
                logger.info("=" * 70)

                stats = workflow_manager.get_stats()

                logger.info(f"\nWorkflows:")
                logger.info(f"  Total registered: {stats['workflows']['total']}")

                logger.info(f"\nExecutions:")
                logger.info(f"  Total: {stats['executions']['total_executions']}")
                logger.info(f"  Active: {stats['executions']['active_executions']}")
                logger.info(f"  Completed: {stats['executions']['completed_executions']}")
                logger.info(f"  Failed: {stats['executions']['failed_executions']}")

                logger.info("=" * 70)
                return 0

            # Esecuzione con workflow manager
            tasks_file = args.tasks or "automator.yaml"

            logger.info("=" * 70)
            logger.info(f"Using Workflow Manager - Processing {tasks_file}")
            logger.info("=" * 70)

            with open(tasks_file) as file:
                conf = yaml.load(file, Loader=yaml.FullLoader)

            workflow_id = f"cli_{os.path.basename(tasks_file).replace('.yaml', '')}"

            workflow_manager.register_workflow(
                workflow_id=workflow_id,
                name=os.path.basename(tasks_file),
                content=conf,
                filepath=os.path.abspath(tasks_file),
                tags=["cli", "automator"]
            )

            execution_id, success, context = workflow_manager.execute_workflow(
                workflow_id=workflow_id,
                gdict=gdict,
                debug=DEBUG,
                debug2=DEBUG2,
                async_mode=False
            )

            logger.info(f"Execution ID: {execution_id}")
            return 0 if success else 1

        except ImportError:
            logger.warning("workflow_manager not available, falling back to standard mode")

    # ========================================
    # MODALITÀ STANDARD
    # ========================================

    tasks_file = args.tasks
    if not tasks_file:
        workflow_path = ENV_CONFIG["WORKFLOW_PATH"]
        default_workflow = os.path.join(workflow_path, "automator.yaml")
        if os.path.exists(default_workflow):
            tasks_file = default_workflow
            logger.info(f"Using default workflow from WORKFLOW_PATH: {tasks_file}")
        else:
            tasks_file = "automator.yaml"

    logger.info("=" * 70)
    logger.info(f"Open-Automator started - Processing {tasks_file}")
    logger.info("=" * 70)

    now_start = datetime.now()

    try:
        wallet_instance = None
        wallet_file = ENV_CONFIG["OA_WALLET_FILE"]
        wallet_password = ENV_CONFIG["OA_WALLET_PASSWORD"]

        if os.path.exists(wallet_file):
            try:
                if wallet_file.endswith(".enc"):
                    logger.info(f"Loading encrypted wallet: {wallet_file}")
                    wallet_instance = Wallet(wallet_file, wallet_password)
                    wallet_instance.load_wallet()
                elif wallet_file.endswith(".json"):
                    logger.info(f"Loading plain wallet: {wallet_file}")
                    wallet_instance = PlainWallet(wallet_file)
                    wallet_instance.load_wallet()

                logger.info(f"✅ Wallet loaded successfully: {len(wallet_instance.secrets)} secrets")
            except Exception as e:
                logger.warning(f"Failed to load wallet: {e}")
        else:
            logger.debug(f"No wallet file found: {wallet_file}")

        gdict["wallet"] = wallet_instance

        logger.debug(f"Loading YAML configuration from {tasks_file}")

        if not os.path.exists(tasks_file):
            raise FileNotFoundError(f"Task file not found: {tasks_file}")

        with open(tasks_file) as file:
            conf = yaml.load(file, Loader=yaml.FullLoader)

        if wallet_instance:
            logger.debug("Resolving placeholders in workflow configuration")
            conf = resolve_dict_placeholders(conf, wallet_instance)
            logger.debug("Placeholders resolved")

        logger.debug("Configuration loaded successfully")

        workflowvars = {}
        tasks = []

        # Nuova sintassi: {name: ..., description: ..., variable: {...}, tasks: [...]}
        if isinstance(conf, dict) and 'tasks' in conf:
            logger.info("Detected NEW syntax (structured workflow)")
            
            # Carica metadati opzionali
            if 'name' in conf:
                gdict['workflow_name'] = conf['name']
                logger.info(f"Workflow name: {conf['name']}")
            
            if 'description' in conf:
                gdict['workflow_description'] = conf['description']
                logger.info(f"Workflow description: {conf['description']}")
            
            # Carica variabili dalla chiave 'variable' o 'variables'
            if 'variable' in conf:
                workflowvars = conf['variable']
            elif 'variables' in conf:
                workflowvars = conf['variables']
            
            tasks = conf['tasks']

        # Vecchia sintassi: [{DB_HOST: ..., tasks: [...]}]
        elif isinstance(conf, list) and len(conf) > 0 and 'tasks' in conf[0]:
            logger.info("Detected OLD syntax (list-based workflow)")
            
            # Estrae variabili (tutto tranne 'tasks')
            workflowvars = {k: v for k, v in conf[0].items() if k != 'tasks'}
            tasks = conf[0]['tasks']

        else:
            raise ValueError(
                "Invalid YAML structure. Expected:\n"
                "  NEW syntax: {name: ..., variable: {...}, tasks: [...]}\n"
                "  OLD syntax: [{VAR1: ..., VAR2: ..., tasks: [...]}]"
            )

        # Carica le variabili nel gdict
        if workflowvars:
            logger.info(f"Loading {len(workflowvars)} workflow variables into gdict")
            gdict.update(workflowvars)
            if DEBUG2:
                logger.debug(f"Workflow variables: {list(workflowvars.keys())}")

        if not tasks:
            raise ValueError("No tasks found in workflow configuration")

        logger.info(f"Found {len(tasks)} tasks to execute")
        logger.info("")
        print_workflow_map(tasks)
        analyze_workflow_paths(tasks)

        if args.dry_run:
            logger.info("DRY-RUN mode - workflow execution skipped")
            return 0

        gdict["envconfig"] = ENV_CONFIG

        taskstore = TaskResultStore()
        engine = WorkflowEngine(tasks, gdict, taskstore, DEBUG, DEBUG2)
        workflow_success, context = engine.execute()

        now_end = datetime.now()
        delta = (now_end - now_start).total_seconds()

        logger.info("")
        logger.info(f"Start: {now_start.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"End:   {now_end.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total execution time: {delta:.2f} seconds")
        logger.info("=" * 70)

        return 0 if workflow_success else 1

    except FileNotFoundError as e:
        logger.critical(f"Configuration file error: {e}")
        return 2
    except yaml.YAMLError as e:
        logger.critical(f"Invalid YAML syntax in {tasks_file}: {e}")
        return 3
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 4

if __name__ == "__main__":
    exitcode = main()
    sys.exit(exitcode)
