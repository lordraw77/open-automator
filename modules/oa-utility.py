"""
Open-Automator Utility Module

Utility functions (variables, sleep, dump, transform) with data propagation
Support for wallet, placeholder {WALLET:key}, {ENV:var} and {VAULT:key}
"""

import oacommon
import time
import inspect
import json
import logging
from datetime import datetime
from logger_config import AutomatorLogger

# Logger for this module
logger = AutomatorLogger.get_logger('oa-utility')

gdict = {}
myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdict_param):
    """Sets the global dictionary"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

@oacommon.trace
def setsleep(self, param):
    """
    Pauses execution for a specified number of seconds with data propagation

    Args:
        param: dict with:
            - seconds: number of seconds to wait - supports {WALLET:key}, {ENV:var}
            - input: (optional) data from previous task (passthrough)
            - workflow_context: (optional) workflow context
            - task_id: (optional)
            - task_store: (optional)

    Returns:
        tuple: (success, input_data) - propagates received input

    Example YAML:
        # Simple sleep for 5 seconds
        - name: wait_5_seconds
          module: oa-utility
          function: setsleep
          seconds: 5
          on_success: next_task

        # Dynamic delay from environment variable
        - name: wait_dynamic
          module: oa-utility
          function: setsleep
          seconds: "{ENV:DELAY_SECONDS}"
          on_success: continue_workflow
    """
    func_name = myself()
    logger.info("Sleep/pause execution")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        if not oacommon.checkandloadparam(self, myself, 'seconds', param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        wallet = gdict.get('_wallet')
        seconds_str = oacommon.get_param(param, 'seconds', wallet) or gdict.get('seconds')
        seconds = float(seconds_str) if isinstance(seconds_str, str) else seconds_str

        logger.info(f"Sleeping for {seconds} seconds...")
        start_time = datetime.now()
        time.sleep(seconds)
        end_time = datetime.now()
        actual_sleep = (end_time - start_time).total_seconds()

        logger.info(f"Sleep completed (actual: {actual_sleep:.2f}s)")

        if 'input' in param:
            output_data = param['input']
            logger.debug("Passing through input data")
        else:
            output_data = {
                'slept_seconds': actual_sleep,
                'requested_seconds': seconds
            }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Sleep operation failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def printvar(self, param):
    """
    Prints the value of a variable or input with data propagation

    Args:
        param: dict with:
            - varname: (optional) variable name to print - supports {WALLET:key}, {ENV:var}
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional)
            - task_store: (optional)

    Returns:
        tuple: (success, printed_value) - propagates the printed value

    Example YAML:
        # Print a specific variable
        - name: print_result
          module: oa-utility
          function: printvar
          varname: my_result

        # Print data from previous task
        - name: print_previous_output
          module: oa-utility
          function: printvar
          on_success: next_step
    """
    func_name = myself()
    logger.info("Printing variable/input")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        wallet = gdict.get('_wallet')
        value = None
        source = "unknown"

        if 'varname' in param:
            if not oacommon.checkandloadparam(self, myself, 'varname', param=param):
                raise ValueError(f"Missing required parameters for {func_name}")

            varname = oacommon.get_param(param, 'varname', wallet) or gdict.get('varname')

            if varname not in gdict:
                logger.warning(f"Variable '{varname}' not found in gdict")
                task_success = False
                error_msg = f"Variable '{varname}' not found"
            else:
                value = gdict[varname]
                source = f"gdict['{varname}']"

        elif 'input' in param:
            value = param['input']
            source = "previous task input"
            logger.info("Printing input from previous task")

        else:
            raise ValueError("No varname or input provided to print")

        if value is not None:
            logger.info(f"=== Value from {source} ===")
            if isinstance(value, (dict, list)):
                formatted = json.dumps(value, indent=2, default=str)
                logger.info(f"Type: {type(value).__name__}")
                logger.info(f"Content:\n{formatted}")
            elif isinstance(value, str) and len(value) > 500:
                logger.info(f"Type: string (length: {len(value)} chars)")
                logger.info(f"Content (first 500 chars):\n{value[:500]}...")
            else:
                logger.info(f"Type: {type(value).__name__}")
                logger.info(f"Content: {value}")
            logger.info("=" * 40)

            output_data = value

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Failed to print variable/input: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def setvar(self, param):
    """
    Sets the value of a variable with data propagation

    Args:
        param: dict with:
            - varname: variable name - supports {WALLET:key}, {ENV:var}
            - varvalue: value to assign (can use input) - supports {WALLET:key}, {ENV:var}
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional)
            - task_store: (optional)

    Returns:
        tuple: (success, set_value) - propagates the set value

    Example YAML:
        # Set a static variable
        - name: set_counter
          module: oa-utility
          function: setvar
          varname: counter
          varvalue: 0

        # Set variable from environment
        - name: set_api_url
          module: oa-utility
          function: setvar
          varname: api_url
          varvalue: "{ENV:API_ENDPOINT}"

        # Set variable from previous task output
        - name: save_response
          module: oa-utility
          function: setvar
          varname: api_response
          # varvalue not specified, uses input from previous task
    """
    func_name = myself()
    logger.info("Setting variable")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        if not oacommon.checkandloadparam(self, myself, 'varname', param=param):
            raise ValueError(f"Missing required parameter 'varname' for {func_name}")

        wallet = gdict.get('_wallet')
        varname = oacommon.get_param(param, 'varname', wallet) or gdict.get('varname')

        if 'varvalue' not in param and 'input' in param:
            varvalue = param['input']
            logger.info("Using input from previous task as varvalue")
        elif 'varvalue' in param:
            varvalue_param = param['varvalue']
            if isinstance(varvalue_param, str):
                varvalue = oacommon.get_param(param, 'varvalue', wallet) or varvalue_param
            else:
                varvalue = varvalue_param
        else:
            raise ValueError("No varvalue or input provided")

        logger.info(f"Setting: {varname} = {varvalue}")
        gdict[varname] = varvalue
        logger.debug(f"Variable '{varname}' set successfully")

        output_data = {
            'varname': varname,
            'varvalue': varvalue
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Failed to set variable: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def dumpvar(self, param):
    """
    Exports all gdict variables to a JSON file with data propagation

    Args:
        param: dict with:
            - savetofile: (optional) JSON output file path - supports {WALLET:key}, {ENV:var}
            - include_input: (optional) also include input in dump
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional)
            - task_store: (optional)

    Returns:
        tuple: (success, variables_dict) - propagates all variables

    Example YAML:
        # Dump all variables to file
        - name: export_variables
          module: oa-utility
          function: dumpvar
          savetofile: "/tmp/workflow_vars.json"

        # Dump variables with dynamic path
        - name: export_to_env_path
          module: oa-utility
          function: dumpvar
          savetofile: "{ENV:OUTPUT_DIR}/vars.json"
    """
    func_name = myself()
    logger.info("Dumping all variables")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    wallet = gdict.get('_wallet')

    try:
        variables_dump = dict(gdict)

        if param.get('include_input') and 'input' in param:
            variables_dump['_input'] = param['input']

        # Remove internal variables
        for key in ['_wallet', 'task_id', 'task_store', 'workflow_context']:
            variables_dump.pop(key, None)

        logger.info(f"Dumping {len(variables_dump)} variable(s)")

        if oacommon.checkparam('savetofile', param):
            savetofile = oacommon.get_param(param, 'savetofile', wallet) or param.get('savetofile')

            json_content = json.dumps(variables_dump, indent=2, default=str, ensure_ascii=False)
            oacommon.writefile(savetofile, json_content)
            logger.info(f"Variables dumped to file: {savetofile}")

        output_data = variables_dump

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Variable dump failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def transform(self, param):
    """
    Transforms data with various operations (upper, lower, strip, etc.)

    Args:
        param: dict with:
            - operation: transformation type ('upper', 'lower', 'strip', 'replace', 'split', 'join')
            - data: (optional) data to transform
            - input: (optional) data from previous task
            - options: (optional) dict with operation-specific options
            - workflow_context: (optional) workflow context
            - task_id: (optional)
            - task_store: (optional)

    Returns:
        tuple: (success, transformed_data)

    Example YAML:
        # Convert to uppercase
        - name: uppercase_text
          module: oa-utility
          function: transform
          operation: upper
          data: "hello world"

        # Transform previous task output
        - name: clean_output
          module: oa-utility
          function: transform
          operation: strip
          # Uses input from previous task

        # Split string
        - name: split_csv
          module: oa-utility
          function: transform
          operation: split
          data: "a,b,c,d"
          options:
            separator: ","
    """
    func_name = myself()
    logger.info("Transforming data")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        wallet = gdict.get('_wallet')

        if not oacommon.checkandloadparam(self, myself, 'operation', param=param):
            raise ValueError(f"Missing required parameter 'operation' for {func_name}")

        operation = gdict.get('operation')

        # Get data to transform
        if 'data' in param:
            data = oacommon.get_param(param, 'data', wallet) or param.get('data')
        elif 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'content' in prev_input:
                data = prev_input['content']
            else:
                data = prev_input
            logger.info("Using data from previous task")
        else:
            raise ValueError("No data to transform")

        options = param.get('options', {})

        logger.info(f"Operation: {operation}")

        # Apply transformation
        if operation == 'upper':
            result = str(data).upper()
        elif operation == 'lower':
            result = str(data).lower()
        elif operation == 'strip':
            result = str(data).strip()
        elif operation == 'replace':
            old_val = options.get('old', '')
            new_val = options.get('new', '')
            result = str(data).replace(old_val, new_val)
        elif operation == 'split':
            separator = options.get('separator', ',')
            result = str(data).split(separator)
        elif operation == 'join':
            separator = options.get('separator', '')
            if isinstance(data, list):
                result = separator.join([str(item) for item in data])
            else:
                raise ValueError("Join operation requires list data")
        else:
            raise ValueError(f"Unsupported operation: {operation}")

        logger.info(f"Transformation completed: {operation}")

        output_data = {
            'result': result,
            'operation': operation,
            'original_type': type(data).__name__,
            'result_type': type(result).__name__
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Transform operation failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def condition(self, param):
    """
    Evaluates a condition for workflow branching

    Args:
        param: dict with:
            - left: left operand - supports {WALLET:key}, {ENV:var}
            - right: right operand - supports {WALLET:key}, {ENV:var}
            - operator: comparison operator ('equals', 'not_equals', 'contains', 'greater', 'less', 'exists', 'is_empty')
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional)
            - task_store: (optional)

    Returns:
        tuple: (condition_result, output_dict) - task_success reflects condition result

    Example YAML:
        # Check if value equals expected
        - name: check_status
          module: oa-utility
          function: condition
          left: "{WALLET:status}"
          operator: equals
          right: "success"
          on_success: success_handler
          on_failure: error_handler

        # Check if variable exists
        - name: check_var_exists
          module: oa-utility
          function: condition
          left: "{WALLET:result}"
          operator: exists

        # Numeric comparison
        - name: check_count
          module: oa-utility
          function: condition
          left: "{WALLET:count}"
          operator: greater
          right: 100
    """
    func_name = myself()
    logger.info("Evaluating condition")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        wallet = gdict.get('_wallet')

        if not oacommon.checkandloadparam(self, myself, 'operator', param=param):
            raise ValueError(f"Missing required parameter 'operator' for {func_name}")

        condition_type = gdict.get('operator')
        left_value = oacommon.get_param(param, 'left', wallet) if 'left' in param else None
        right_value = oacommon.get_param(param, 'right', wallet) if 'right' in param else None

        logger.info(f"Condition: {left_value} {condition_type} {right_value}")

        # Evaluate condition
        result = False
        if condition_type == 'equals':
            result = left_value == right_value
        elif condition_type == 'not_equals':
            result = left_value != right_value
        elif condition_type == 'contains':
            result = right_value in str(left_value)
        elif condition_type == 'greater':
            result = float(left_value) > float(right_value)
        elif condition_type == 'less':
            result = float(left_value) < float(right_value)
        elif condition_type == 'exists':
            result = left_value is not None
        elif condition_type == 'is_empty':
            result = not bool(left_value)

        # task_success = condition result
        task_success = result
        logger.info(f"Condition result: {result}")

        output_data = {
            'condition_result': result,
            'condition_type': condition_type,
            'left_value': left_value,
            'right_value': right_value
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Condition evaluation failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def merge(self, param):
    """
    Merges data from multiple sources

    Args:
        param: dict with:
            - merge_type: 'dict'|'list'|'concat'
            - sources: list of keys from workflow_context
            - separator: (optional) for concat - supports {WALLET:key}, {ENV:var}
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional)
            - task_store: (optional)

    Returns:
        tuple: (success, merged_data)

    Example YAML:
        # Merge dictionaries
        - name: merge_configs
          module: oa-utility
          function: merge
          merge_type: dict
          sources:
            - task1_output
            - task2_output

        # Concatenate strings with separator
        - name: join_messages
          module: oa-utility
          function: merge
          merge_type: concat
          sources:
            - msg1
            - msg2
          separator: " | "

        # Merge lists
        - name: combine_arrays
          module: oa-utility
          function: merge
          merge_type: list
          sources:
            - list1
            - list2
    """
    func_name = myself()
    logger.info("Merging data")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        wallet = gdict.get('_wallet')
        merge_type = param.get('merge_type', 'dict')
        workflow_context = param.get('workflow_context')

        if not workflow_context:
            raise ValueError("workflow_context required for merge operation")

        sources = param.get('sources', [])
        logger.info(f"Merge type: {merge_type}, sources: {sources}")

        if merge_type == 'dict':
            merged = {}
            for source in sources:
                data = workflow_context.get_task_output(source)
                if isinstance(data, dict):
                    merged.update(data)

            if 'input' in param and isinstance(param['input'], dict):
                merged.update(param['input'])

            output_data = merged
            logger.info(f"Merged {len(sources)} dicts, result: {len(merged)} keys")

        elif merge_type == 'list':
            merged = []
            for source in sources:
                data = workflow_context.get_task_output(source)
                if isinstance(data, list):
                    merged.extend(data)

            if 'input' in param and isinstance(param['input'], list):
                merged.extend(param['input'])

            output_data = merged
            logger.info(f"Merged {len(sources)} lists, result: {len(merged)} items")

        elif merge_type == 'concat':
            parts = []
            for source in sources:
                data = workflow_context.get_task_output(source)
                parts.append(str(data))

            if 'input' in param:
                parts.append(str(param['input']))

            separator_param = param.get('separator', '\n')
            separator = oacommon.get_param({'separator': separator_param}, 'separator', wallet) or separator_param

            output_data = separator.join(parts)
            logger.info(f"Concatenated {len(parts)} strings")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Merge operation failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data