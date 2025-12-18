"""
Open-Automator Module Template
Template per creare nuovi moduli custom con data propagation
"""

import oacommon
import inspect
import logging
from logger_config import AutomatorLogger

# Logger per questo modulo
logger = AutomatorLogger.get_logger('oa-moduletemplate')

# Global dict per sincronizzazione variabili tra moduli
gdict = {}

def setgdict(self, gdict_param):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

# Recupera nome funzione corrente
myself = lambda: inspect.stack()[1][3]


#### TEMPLATE FOR FUNCTION ####

@oacommon.trace
def templatefunction(self, param):
    """
    Descrizione della funzione con data propagation
    
    Args:
        param: dict con:
            - param1: (tipo) descrizione parametro obbligatorio
            - param2: (tipo) descrizione parametro obbligatorio (supporta {var})
            - param3: (tipo, opzionale) descrizione parametro opzionale
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_data) dove output_data contiene i risultati
    
    Example YAML:
        - name: example_task
          module: oa-moduletemplate
          function: templatefunction
          param1: "value1"
          param2: "value2 with {variable}"
          param3: "optional_value"
          on_success: next_task
          on_failure: error_handler
    """
    func_name = myself()
    logger.info(f"{func_name} - Starting execution")
    
    # Gestione task store per multi-threading
    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None
    
    # Lista parametri obbligatori
    required_params = ['param1', 'param2']
    
    try:
        # ---- DATA PROPAGATION: Auto-detection input ----
        # Se param1 manca, prova a usare input dal task precedente
        if 'param1' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'param1' in prev_input:
                param['param1'] = prev_input['param1']
                logger.info("Using param1 from previous task")
        
        # ---- VALIDAZIONE PARAMETRI ----
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")
        
        # ---- ESTRAZIONE PARAMETRI ----
        param1 = oacommon.effify(gdict['param1'])
        param2 = oacommon.effify(gdict['param2'])
        
        # Parametri opzionali
        param3 = param.get('param3', False)  # default False
        
        logger.info(f"Parameters: param1={param1}, param2={param2}, param3={param3}")
        
        # ---- LOGICA BUSINESS ----
        # Inserisci qui il tuo codice principale
        result = perform_operation(param1, param2, param3)
        
        logger.info(f"Operation completed successfully: {result}")
        
        # ---- OUTPUT DATA PER PROPAGATION ----
        output_data = {
            'result': result,
            'param1': param1,
            'param2': param2,
            'param3': param3,
            'status': 'completed'
        }
        
        # ---- SALVATAGGIO IN VARIABILE (opzionale, retrocompatibilità) ----
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
        # Registra risultato nel task store (per multi-threading)
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)
    
    # Return (success, output_data) per data propagation
    return task_success, output_data


def perform_operation(param1, param2, param3):
    """
    Helper function - implementa la logica business
    
    Args:
        param1: primo parametro
        param2: secondo parametro
        param3: terzo parametro opzionale
    
    Returns:
        result: risultato dell'operazione
    """
    # Esempio di logica
    result = f"{param1} + {param2}"
    
    if param3:
        result += f" + {param3}"
    
    return result


# ---- ESEMPIO FUNZIONE AVANZATA CON MULTIPLE OPERATIONS ----

@oacommon.trace
def advanced_function(self, param):
    """
    Funzione avanzata con supporto per operazioni multiple
    
    Args:
        param: dict con:
            - operation: (str) 'create'|'read'|'update'|'delete'
            - target: (str) target dell'operazione
            - data: (dict, opzionale) dati per l'operazione
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_data)
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
    """Gestisce operazione CREATE"""
    logger.debug(f"Creating {target} with data: {data}")
    # Implementa logica
    return {'created': target, 'data': data}


def handle_read(target):
    """Gestisce operazione READ"""
    logger.debug(f"Reading {target}")
    # Implementa logica
    return {'target': target, 'content': 'example'}


def handle_update(target, data):
    """Gestisce operazione UPDATE"""
    logger.debug(f"Updating {target} with data: {data}")
    # Implementa logica
    return {'updated': target, 'data': data}


def handle_delete(target):
    """Gestisce operazione DELETE"""
    logger.debug(f"Deleting {target}")
    # Implementa logica
    return {'deleted': target}
