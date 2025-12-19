"""
Open-Automator Utility Module
Funzioni di utilità (variabili, sleep, dump, transform) con data propagation
Supporto per wallet, placeholder {WALLET:key}, {ENV:var} e {VAULT:key}
"""

import oacommon
import time
import inspect
import json
import logging
from datetime import datetime
from logger_config import AutomatorLogger

# Logger per questo modulo
logger = AutomatorLogger.get_logger('oa-utility')

gdict = {}
myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdict_param):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

@oacommon.trace
def setsleep(self, param):
    """
    Pausa l'esecuzione per un numero di secondi con data propagation

    Args:
        param: dict con:
            - seconds: numero di secondi da attendere - supporta {WALLET:key}, {ENV:var}
            - input: (opzionale) dati dal task precedente (passthrough)
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale)
            - task_store: (opzionale)

    Returns:
        tuple: (success, input_data) - propaga l'input ricevuto
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

        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        # Usa get_param per supportare placeholder (es. delay dinamico da ENV)
        seconds_str = oacommon.get_param(param, 'seconds', wallet) or gdict.get('seconds')
        seconds = float(seconds_str) if isinstance(seconds_str, str) else seconds_str

        logger.info(f"Sleeping for {seconds} seconds...")

        start_time = datetime.now()
        time.sleep(seconds)
        end_time = datetime.now()

        actual_sleep = (end_time - start_time).total_seconds()
        logger.info(f"Sleep completed (actual: {actual_sleep:.2f}s)")

        # Propaga l'input ricevuto (passthrough)
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
    Stampa il valore di una variabile o dell'input con data propagation

    Args:
        param: dict con:
            - varname: (opzionale) nome della variabile da stampare - supporta {WALLET:key}, {ENV:var}
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale)
            - task_store: (opzionale)

    Returns:
        tuple: (success, printed_value) - propaga il valore stampato
    """
    func_name = myself()
    logger.info("Printing variable/input")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        value = None
        source = "unknown"

        # Priorità: 1) varname specificato, 2) input dal task precedente
        if 'varname' in param:
            if not oacommon.checkandloadparam(self, myself, 'varname', param=param):
                raise ValueError(f"Missing required parameters for {func_name}")

            # Risolvi placeholder nel varname
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
            # Log appropriato in base al tipo e dimensione
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

        # Output: propaga il valore stampato
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
    Imposta il valore di una variabile con data propagation

    Args:
        param: dict con:
            - varname: nome della variabile - supporta {WALLET:key}, {ENV:var}
            - varvalue: valore da assegnare (può usare input) - supporta {WALLET:key}, {ENV:var}
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale)
            - task_store: (opzionale)

    Returns:
        tuple: (success, set_value) - propaga il valore impostato
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

        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        # Risolvi placeholder nel varname
        varname = oacommon.get_param(param, 'varname', wallet) or gdict.get('varname')

        # Se varvalue non è specificato, usa input
        if 'varvalue' not in param and 'input' in param:
            varvalue = param['input']
            logger.info("Using input from previous task as varvalue")
        elif 'varvalue' in param:
            # Risolvi placeholder nel varvalue (IMPORTANTE!)
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

        # Output: propaga il valore impostato
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
    Esporta tutte le variabili del gdict in un file JSON con data propagation

    Args:
        param: dict con:
            - savetofile: (opzionale) path del file JSON di output - supporta {WALLET:key}, {ENV:var}
            - include_input: (opzionale) include anche input nel dump
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale)
            - task_store: (opzionale)

    Returns:
        tuple: (success, variables_dict) - propaga tutte le variabili
    """
    func_name = myself()
    logger.info("Dumping all variables")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    # Recupera wallet per risoluzione placeholder
    wallet = gdict.get('_wallet')

    # Risolvi placeholder nel savetofile (es. path dinamico)
    savetofile = None
    if 'savetofile' in param:
        savetofile = oacommon.get_param(param, 'savetofile', wallet) or param.get('savetofile')

    include_input = param.get('include_input', False)

    try:
        # Filtra variabili di sistema
        filtered_gdict = {
            k: v for k, v in self.gdict.items()
            if not k.startswith('_') and k not in ['DEBUG', 'DEBUG2', 'TRACE']
        }

        # Include input se richiesto
        if include_input and 'input' in param:
            filtered_gdict['__input__'] = param['input']

        json_output = json.dumps(filtered_gdict, indent=4, sort_keys=True, default=str)

        logger.info(f"Variables dump ({len(filtered_gdict)} variables):")
        if len(json_output) > 2000:
            logger.info(f"{json_output[:2000]}...")
            logger.info(f"(truncated, total: {len(json_output)} chars)")
        else:
            logger.info(json_output)

        if savetofile:
            with open(savetofile, 'w', encoding='utf-8') as f:
                f.write(json_output)
            logger.info(f"Variables saved to: {savetofile}")

        # Output: tutte le variabili
        output_data = filtered_gdict

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Failed to dump variables: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def transform(self, param):
    """
    Trasforma dati con operazioni comuni (filter, map, extract)

    Args:
        param: dict con:
            - operation: 'filter'|'map'|'extract'|'aggregate'
            - field: (opzionale) campo su cui operare - supporta {WALLET:key}, {ENV:var}
            - condition: (opzionale) per filter - supporta {WALLET:key}, {ENV:var} nei valori
            - expression: (opzionale) per map
            - fields: (opzionale) lista campi per extract
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale)
            - task_store: (opzionale)

    Returns:
        tuple: (success, transformed_data)
    """
    func_name = myself()
    logger.info("Transforming data")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        if 'input' not in param:
            raise ValueError("No input data to transform")

        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        data = param['input']
        operation = param.get('operation', 'passthrough')

        logger.info(f"Transform operation: {operation}")
        logger.debug(f"Input type: {type(data).__name__}")

        if operation == 'filter':
            # Filtra lista di dict in base a condizione
            field = param.get('field')
            if field and isinstance(field, str):
                field = oacommon.get_param({'field': field}, 'field', wallet) or field

            condition = param.get('condition')  # es: {'operator': '==', 'value': 'active'}

            if not isinstance(data, list):
                raise ValueError("Filter operation requires list input")

            if isinstance(data[0], dict) and field:
                operator = condition.get('operator', '==')
                value = condition.get('value')

                # Risolvi placeholder nel value della condition
                if isinstance(value, str):
                    value = oacommon.get_param({'value': value}, 'value', wallet) or value

                if operator == '==':
                    filtered = [item for item in data if item.get(field) == value]
                elif operator == '!=':
                    filtered = [item for item in data if item.get(field) != value]
                elif operator == '>':
                    filtered = [item for item in data if item.get(field, 0) > value]
                elif operator == '<':
                    filtered = [item for item in data if item.get(field, 0) < value]
                elif operator == 'contains':
                    filtered = [item for item in data if value in str(item.get(field, ''))]
                else:
                    filtered = data

                output_data = filtered
                logger.info(f"Filtered {len(data)} -> {len(filtered)} items")
            else:
                output_data = data

        elif operation == 'map':
            # Estrai campo specifico da lista di dict
            field = param.get('field')
            if field and isinstance(field, str):
                field = oacommon.get_param({'field': field}, 'field', wallet) or field

            if not isinstance(data, list):
                raise ValueError("Map operation requires list input")

            if isinstance(data[0], dict) and field:
                mapped = [item.get(field) for item in data]
                output_data = mapped
                logger.info(f"Mapped {len(data)} items to field '{field}'")
            else:
                output_data = data

        elif operation == 'extract':
            # Estrai campi specifici
            fields = param.get('fields', [])

            if isinstance(data, dict):
                extracted = {k: data.get(k) for k in fields if k in data}
                output_data = extracted
                logger.info(f"Extracted {len(extracted)} fields from dict")
            elif isinstance(data, list) and isinstance(data[0], dict):
                extracted = []
                for item in data:
                    extracted.append({k: item.get(k) for k in fields if k in item})
                output_data = extracted
                logger.info(f"Extracted {len(fields)} fields from {len(data)} items")
            else:
                output_data = data

        elif operation == 'aggregate':
            # Aggrega valori (sum, count, avg)
            agg_type = param.get('agg_type', 'count')
            field = param.get('field')
            if field and isinstance(field, str):
                field = oacommon.get_param({'field': field}, 'field', wallet) or field

            if not isinstance(data, list):
                raise ValueError("Aggregate operation requires list input")

            if agg_type == 'count':
                result = len(data)
            elif agg_type == 'sum' and field:
                result = sum(item.get(field, 0) for item in data if isinstance(item, dict))
            elif agg_type == 'avg' and field:
                values = [item.get(field, 0) for item in data if isinstance(item, dict)]
                result = sum(values) / len(values) if values else 0
            else:
                result = len(data)

            output_data = {
                'aggregation': agg_type,
                'field': field,
                'result': result,
                'count': len(data)
            }
            logger.info(f"Aggregated: {agg_type} = {result}")

        else:  # passthrough
            output_data = data
            logger.info("Passthrough: no transformation applied")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Data transformation failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def conditional(self, param):
    """
    Valuta una condizione e propaga risultato

    Args:
        param: dict con:
            - condition_type: 'equals'|'contains'|'greater'|'less'|'exists'
            - left_value: valore sinistro (può usare input) - supporta {WALLET:key}, {ENV:var}
            - right_value: valore destro - supporta {WALLET:key}, {ENV:var}
            - field: (opzionale) campo da estrarre da input - supporta {WALLET:key}, {ENV:var}
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale)
            - task_store: (opzionale)

    Returns:
        tuple: (condition_result, evaluation_details)
    """
    func_name = myself()
    logger.info("Evaluating condition")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        condition_type = param.get('condition_type', 'equals')

        # Determina left_value con supporto placeholder
        if 'left_value' in param:
            left_value_param = param['left_value']
            if isinstance(left_value_param, str):
                left_value = oacommon.get_param({'left_value': left_value_param}, 'left_value', wallet) or left_value_param
            else:
                left_value = left_value_param
        elif 'input' in param:
            input_data = param['input']
            field = param.get('field')

            # Risolvi placeholder nel field
            if field and isinstance(field, str):
                field = oacommon.get_param({'field': field}, 'field', wallet) or field

            if field and isinstance(input_data, dict):
                left_value = input_data.get(field)
            else:
                left_value = input_data
        else:
            raise ValueError("No left_value or input provided")

        # Risolvi placeholder nel right_value
        right_value_param = param.get('right_value')
        if isinstance(right_value_param, str):
            right_value = oacommon.get_param({'right_value': right_value_param}, 'right_value', wallet) or right_value_param
        else:
            right_value = right_value_param

        logger.info(f"Condition: {left_value} {condition_type} {right_value}")

        # Valuta condizione
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

        # task_success = result della condizione
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
    Unisce dati da più sorgenti

    Args:
        param: dict con:
            - merge_type: 'dict'|'list'|'concat'
            - sources: lista di chiavi da workflow_context
            - separator: (opzionale) per concat - supporta {WALLET:key}, {ENV:var}
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale)
            - task_store: (opzionale)

    Returns:
        tuple: (success, merged_data)
    """
    func_name = myself()
    logger.info("Merging data")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        merge_type = param.get('merge_type', 'dict')
        workflow_context = param.get('workflow_context')

        if not workflow_context:
            raise ValueError("workflow_context required for merge operation")

        sources = param.get('sources', [])

        logger.info(f"Merge type: {merge_type}, sources: {sources}")

        if merge_type == 'dict':
            # Unisci dict
            merged = {}
            for source in sources:
                data = workflow_context.get_task_output(source)
                if isinstance(data, dict):
                    merged.update(data)

            # Include anche input se presente
            if 'input' in param and isinstance(param['input'], dict):
                merged.update(param['input'])

            output_data = merged
            logger.info(f"Merged {len(sources)} dicts, result: {len(merged)} keys")

        elif merge_type == 'list':
            # Unisci liste
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
            # Concatena stringhe
            parts = []
            for source in sources:
                data = workflow_context.get_task_output(source)
                parts.append(str(data))

            if 'input' in param:
                parts.append(str(param['input']))

            # Risolvi placeholder nel separator
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
