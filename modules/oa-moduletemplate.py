"""
Open-Automator Module Template

Template for creating new custom modules with data propagation
Use this as a starting point for building your own modules
"""

import oacommon
import inspect
import logging
from logger_config import AutomatorLogger

# Logger for this module
logger = AutomatorLogger.get_logger('oa-moduletemplate')

# Global dict for variable synchronization between modules
gdict = {}

def setgdict(self, gdict_param):
    """Sets the global dictionary"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

# Get current function name
myself = lambda: inspect.stack()[1][3]

#### TEMPLATE FOR FUNCTION ####

@oacommon.trace
def templatefunction(self, param):
    """
    Function description with data propagation

    This is a template function showing best practices for:
    - Data propagation from previous tasks
    - Parameter validation
    - Error handling
    - Output standardization
    - Logging

    Args:
        param: dict with:
            - param1: (type) required parameter description
            - param2: (type) required parameter description (supports {WALLET:key}, {ENV:var})
            - param3: (type, optional) optional parameter description
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_data) where output_data contains results

    Example YAML:
        # Basic usage
        - name: example_task
          module: oa-moduletemplate
          function: templatefunction
          param1: "value1"
          param2: "value2"
          param3: "optional_value"

        # With placeholders
        - name: secure_task
          module: oa-moduletemplate
          function: templatefunction
          param1: "{WALLET:api_key}"
          param2: "{ENV:TARGET_ENV}"

        # With data from previous task
        - name: chained_task
          module: oa-moduletemplate
          function: templatefunction
          # param1 auto-filled from previous task output
          param2: "additional_value"

        # With error handling
        - name: safe_task
          module: oa-moduletemplate
          function: templatefunction
          param1: "value1"
          param2: "value2"
          on_success: next_task
          on_failure: error_handler
    """
    func_name = myself()
    logger.info(f"{func_name} - Starting execution")

    # Task store management for multi-threading
    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    # List of required parameters
    required_params = ['param1', 'param2']

    try:
        # ---- DATA PROPAGATION: Auto-detection input ----
        # If param1 is missing, try to use input from previous task
        if 'param1' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'param1' in prev_input:
                param['param1'] = prev_input['param1']
                logger.info("Using param1 from previous task")

        # ---- PARAMETER VALIDATION ----
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # ---- PARAMETER EXTRACTION ----
        param1 = oacommon.effify(gdict['param1'])
        param2 = oacommon.effify(gdict['param2'])

        # Optional parameters
        param3 = param.get('param3', False)  # default False

        logger.info(f"Parameters: param1={param1}, param2={param2}, param3={param3}")

        # ---- BUSINESS LOGIC ----
        # Insert your main code here
        result = perform_operation(param1, param2, param3)

        logger.info(f"Operation completed successfully: {result}")

        # ---- OUTPUT DATA FOR PROPAGATION ----
        output_data = {
            'result': result,
            'param1': param1,
            'param2': param2,
            'param3': param3,
            'status': 'completed'
        }

        # ---- SAVE TO VARIABLE (optional, backward compatibility) ----
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = output_data
            logger.debug(f"Output saved to variable: {saveonvar}")

        logger.info(f"{func_name} - Execution completed successfully")

    except ValueError as e:
        task_success = False
        error_msg = f"Validation error: {str(e)}"
        logger.error(error_msg)
    except FileNotFoundError as e:
        task_success = False
        error_msg = f"File not found: {str(e)}"
        logger.error(error_msg, exc_info=True)
    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"{func_name} failed: {e}", exc_info=True)

    finally:
        # Register result in task store (for multi-threading)
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    # Return (success, output_data) for data propagation
    return task_success, output_data

def perform_operation(param1, param2, param3):
    """
    Helper function - implements business logic

    Args:
        param1: first parameter
        param2: second parameter
        param3: optional third parameter

    Returns:
        result: operation result
    """
    # Example logic
    result = f"{param1} + {param2}"

    if param3:
        result += f" + {param3}"

    return result

# ---- ADVANCED FUNCTION EXAMPLE WITH MULTIPLE OPERATIONS ----

@oacommon.trace
def advanced_function(self, param):
    """
    Advanced function with support for multiple operations

    This demonstrates how to implement CRUD-style operations
    with data propagation and proper error handling.

    Args:
        param: dict with:
            - operation: (str) 'create'|'read'|'update'|'delete'
            - target: (str) operation target - supports {WALLET:key}, {ENV:var}
            - data: (dict, optional) data for operation
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_data)

    Example YAML:
        # CREATE operation
        - name: create_resource
          module: oa-moduletemplate
          function: advanced_function
          operation: "create"
          target: "user_profile"
          data:
            name: "John Doe"
            email: "john@example.com"
            role: "admin"

        # READ operation
        - name: read_resource
          module: oa-moduletemplate
          function: advanced_function
          operation: "read"
          target: "config_settings"

        # UPDATE operation with data from previous task
        - name: update_resource
          module: oa-moduletemplate
          function: advanced_function
          operation: "update"
          target: "user_profile"
          # data from previous task

        # DELETE operation
        - name: delete_resource
          module: oa-moduletemplate
          function: advanced_function
          operation: "delete"
          target: "temp_file"

        # With placeholders
        - name: secure_operation
          module: oa-moduletemplate
          function: advanced_function
          operation: "create"
          target: "{ENV:TARGET_RESOURCE}"
          data:
            api_key: "{VAULT:api_secret}"
            user: "{WALLET:username}"

        # Chained operations
        - name: multi_step_process
          module: oa-moduletemplate
          function: advanced_function
          operation: "read"
          target: "source_data"

        - name: process_and_update
          module: oa-moduletemplate
          function: advanced_function
          operation: "update"
          # target from previous task
          data:
            processed: true
            timestamp: "{WALLET:current_time}"
    """
    func_name = myself()
    logger.info(f"{func_name} - Advanced operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = ['operation', 'target']

    try:
        # Auto-detection input
        if 'target' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'target' in prev_input:
                param['target'] = prev_input['target']
                logger.info("Using target from previous task")

        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        operation = gdict['operation']
        target = oacommon.effify(gdict['target'])
        data = param.get('data', {})

        logger.info(f"Operation: {operation} on target: {target}")

        # Switch operation
        if operation == 'create':
            result = handle_create(target, data)
        elif operation == 'read':
            result = handle_read(target)
        elif operation == 'update':
            result = handle_update(target, data)
        elif operation == 'delete':
            result = handle_delete(target)
        else:
            raise ValueError(f"Invalid operation: {operation}")

        logger.info(f"{operation.capitalize()} operation completed")

        # Output data
        output_data = {
            'operation': operation,
            'target': target,
            'result': result,
            'timestamp': oacommon.get_timestamp() if hasattr(oacommon, 'get_timestamp') else None
        }

    except ValueError as e:
        task_success = False
        error_msg = f"Validation error: {str(e)}"
        logger.error(error_msg)
    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"{func_name} failed: {e}", exc_info=True)

    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

# ---- HELPER FUNCTIONS ----

def handle_create(target, data):
    """
    Handles CREATE operation

    Args:
        target: resource to create
        data: creation data

    Returns:
        dict: creation result
    """
    logger.debug(f"Creating {target} with data: {data}")
    # Implement your logic here
    return {'created': target, 'data': data}

def handle_read(target):
    """
    Handles READ operation

    Args:
        target: resource to read

    Returns:
        dict: read result
    """
    logger.debug(f"Reading {target}")
    # Implement your logic here
    return {'target': target, 'content': 'example'}

def handle_update(target, data):
    """
    Handles UPDATE operation

    Args:
        target: resource to update
        data: update data

    Returns:
        dict: update result
    """
    logger.debug(f"Updating {target} with data: {data}")
    # Implement your logic here
    return {'updated': target, 'data': data}

def handle_delete(target):
    """
    Handles DELETE operation

    Args:
        target: resource to delete

    Returns:
        dict: deletion result
    """
    logger.debug(f"Deleting {target}")
    # Implement your logic here
    return {'deleted': target}

# ---- MODULE CREATION GUIDELINES ----
"""
BEST PRACTICES FOR MODULE DEVELOPMENT:

1. FUNCTION STRUCTURE:
   - Always use @oacommon.trace decorator
   - Return tuple (success, output_data)
   - Include task_store management
   - Implement proper error handling

2. DATA PROPAGATION:
   - Check for 'input' parameter
   - Auto-fill missing params from previous task
   - Standardize output_data format
   - Log data flow decisions

3. PARAMETER HANDLING:
   - Define required_params list
   - Use oacommon.checkandloadparam()
   - Support {WALLET:}, {ENV:}, {VAULT:} placeholders
   - Provide sensible defaults for optional params

4. ERROR HANDLING:
   - Use specific exception types
   - Log errors with context
   - Set task_success = False on error
   - Include error_msg in output

5. LOGGING:
   - Use AutomatorLogger
   - Log at appropriate levels (debug/info/warning/error)
   - Include function name and context
   - Don't log sensitive data (passwords, tokens)

6. DOCUMENTATION:
   - Write clear docstrings
   - Include YAML examples
   - Document all parameters
   - Explain return values

7. TESTING:
   - Test with various input types
   - Test data propagation scenarios
   - Test error conditions
   - Verify placeholder resolution

8. SECURITY:
   - Never hardcode credentials
   - Use {VAULT:} for passwords
   - Sanitize user inputs
   - Validate file paths

EXAMPLE WORKFLOW USING TEMPLATE:

tasks:
  - name: step1
    module: oa-moduletemplate
    function: templatefunction
    param1: "initial_value"
    param2: "{ENV:CONFIG_VALUE}"

  - name: step2
    module: oa-moduletemplate
    function: advanced_function
    operation: "create"
    # target auto-filled from step1 output
    data:
      source: "step1"

  - name: step3
    module: oa-moduletemplate
    function: advanced_function
    operation: "read"
    target: "{WALLET:resource_id}"
    on_success: step4
    on_failure: error_handler

  - name: error_handler
    module: oa-notify
    function: send_slack
    message: "Workflow failed at step3"
"""