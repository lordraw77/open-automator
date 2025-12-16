"""
Open-Automator Workflow Module

Esegue una lista di step come workflow, con branching su success/failure.
"""

import oacommon
import inspect
import logging
from logger_config import AutomatorLogger

logger = AutomatorLogger.get_logger('oa-workflow')

gdict = {}
myself = lambda: inspect.stack()[1][3]


def setgdict(self, gdict_param):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param


@oacommon.trace
def runworkflow(self, param):
    func_name = myself()
    logger.info("Starting workflow execution")

    task_id = param.get("task_id")
    task_store = param.get("task_store")

    task_success = True
    error_msg = ""

    try:
        required_params = ['start_step', 'steps']
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        start_step = gdict['start_step']    
        steps_list = gdict['steps']         

        if not isinstance(steps_list, list):
            raise ValueError("Parameter 'steps' must be a list")

        steps_map = {s.get('name'): s for s in steps_list}

        if start_step not in steps_map:
            raise ValueError(f"Start step '{start_step}' not found in steps")

        current_step_name = start_step
        max_steps = len(steps_list) * 10
        executed_count = 0

        while current_step_name and current_step_name != "end":
            executed_count += 1
            if executed_count > max_steps:
                raise RuntimeError("Max workflow steps exceeded (possible loop)")

            step = steps_map.get(current_step_name)
            if not step:
                raise ValueError(f"Step '{current_step_name}' not defined in steps")

            step_module_name = step.get('module')
            step_function_name = step.get('function')
            step_params = step.get('params', {}) or {}

            logger.info(f"Executing step '{current_step_name}' "
                        f"-> {step_module_name}.{step_function_name}")

            # Import dinamico modulo
            step_module = __import__(step_module_name)
            if not hasattr(step_module, step_function_name):
                raise AttributeError(
                    f"Module '{step_module_name}' has no function '{step_function_name}'"
                )
            step_func = getattr(step_module, step_function_name)

            # Propaga task_id / task_store
            if task_id:
                step_params["task_id"] = f"{task_id}:{current_step_name}"
            if task_store:
                step_params["task_store"] = task_store

            # Esecuzione: deve ritornare True/False
            step_result = step_func(self, step_params)
            logger.info(f"Step '{current_step_name}' result: {step_result}")

            if step_result:
                next_step = step.get('on_success')
            else:
                next_step = step.get('on_failure')

            if not next_step or next_step == "end":
                logger.info(f"Workflow finished after step '{current_step_name}'")
                break

            if next_step not in steps_map and next_step != "end":
                raise ValueError(
                    f"Next step '{next_step}' (from '{current_step_name}') "
                    f"not found in steps"
                )

            current_step_name = next_step

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Workflow execution failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success
