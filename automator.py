"""
Open-Automator - Task automation framework
Main entry point with logging support
"""

import yaml
import argparse
import os
import inspect
import sys
from datetime import datetime
from logger_config import AutomatorLogger, TaskLogger
import oacommon

# Inizializza logger per questo modulo
logger = AutomatorLogger.get_logger('automator')

gdict = {}
cwd = os.getcwd()
oacommon.setgdict(oacommon, gdict)

modulepath = os.path.join(cwd, 'modules')
if os.path.exists(modulepath):
    sys.path.append(modulepath)

myself = lambda: inspect.stack()[1][3]
findinlist = lambda y, list: [x for x in list if y in x]


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

        currtask = 1
        failed_tasks = []

        for task in tasks:
            for key in task.keys():
                if 'name' != key:
                    task_name = task.get('name', f'Unnamed task {currtask}')

                    # Usa context manager per task logging
                    try:
                        with TaskLogger(logger, task_name, currtask, sizetask):
                            if DEBUG:
                                logger.debug(f"Task module.function: {key}")
                                logger.debug(f"Task parameters: {task.get(key)}")

                            if '.' in key:
                                # Importa modulo dinamicamente
                                module_name = key.split('.')[0]
                                func_name = key.split('.')[1]

                                logger.debug(f"Loading module: {module_name}, function: {func_name}")

                                if DEBUG2:
                                    logger.debug(f"Global dict state: {list(gdict.keys())}")

                                m = __import__(module_name)

                                # Imposta gdict nel modulo
                                mfunc = getattr(m, 'setgdict')
                                mfunc(m, gdict)

                                # Esegui funzione
                                func = getattr(m, func_name)
                                func(m, task.get(key))
                            else:
                                # Funzione globale
                                logger.debug(f"Executing global function: {key}")
                                func = globals()[key]
                                func(task.get(key))

                    except Exception as e:
                        logger.error(f"Task execution failed: {e}", exc_info=DEBUG2)
                        failed_tasks.append({
                            'task_num': currtask,
                            'task_name': task_name,
                            'error': str(e)
                        })
                        # Opzionale: continua con altri task invece di interrompere
                        # Se vuoi interrompere all'errore, decommentare: raise

                    currtask += 1

        nowend = datetime.now()
        delta = (nowend - nowstart).total_seconds()

        logger.info("=" * 70)
        if failed_tasks:
            logger.warning(f"Open-Automator completed with {len(failed_tasks)} FAILED tasks")
            for ft in failed_tasks:
                logger.warning(f"  - Task {ft['task_num']}: {ft['task_name']} - {ft['error']}")
        else:
            logger.info("Open-Automator completed SUCCESSFULLY")

        logger.info(f"Total tasks: {sizetask} | Failed: {len(failed_tasks)} | Succeeded: {sizetask - len(failed_tasks)}")
        logger.info(f"Start: {nowstart.strftime('%Y-%m-%d %H:%M:%S')} | End: {nowend.strftime('%Y-%m-%d %H:%M:%S')}")
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