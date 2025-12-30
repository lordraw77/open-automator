"""
Open-Automator JSON Module
Gestisce operazioni avanzate su dati JSON con data propagation
Supporto per wallet, placeholder WALLET{key}, ENV{var} e VAULT{key}
"""

import oacommon
import inspect
import json
import logging
from logger_config import AutomatorLogger

logger = AutomatorLogger.getlogger("oa-json")

gdict = {}

myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdictparam):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdictparam
    self.gdict = gdictparam


@oacommon.trace
def jsonfilter(self, param):
    """
    Filtra elementi in un array JSON basandosi su condizioni

    Args:
        param (dict) con:
            - data: opzionale dati JSON (può usare input da task precedente)
            - field: campo su cui filtrare - supporta WALLET{key}, ENV{var}
            - operator: ==, !=, >, <, >=, <=, contains, in, exists
            - value: valore di confronto - supporta WALLET{key}, ENV{var}
            - case_sensitive: opzionale (default: True)
            - saveonvar: opzionale salva risultato in variabile
            - input: opzionale dati dal task precedente
            - workflowcontext: opzionale contesto workflow
            - taskid: opzionale id univoco del task
            - taskstore: opzionale istanza di TaskResultStore

    Returns:
        tuple (success, filtered_data)

    Example:
        Input: [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        Filter: field="age", operator=">", value=26
        Output: [{"name": "Alice", "age": 30}]
    """
    funcname = myself()
    logger.info("JSON Filter operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation: recupera dati JSON
        data = None
        if "data" in param:
            data = param["data"]
            # Se è stringa JSON, parsala
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                # Cerca campi comuni
                if "json" in previnput:
                    data = previnput["json"]
                elif "data" in previnput:
                    data = previnput["data"]
                elif "rows" in previnput:
                    data = previnput["rows"]
                elif "content" in previnput:
                    # Potrebbe essere stringa JSON
                    content = previnput["content"]
                    if isinstance(content, str):
                        data = json.loads(content)
                    else:
                        data = content
                else:
                    # Usa tutto l'input
                    data = previnput
            elif isinstance(previnput, list):
                data = previnput
            elif isinstance(previnput, str):
                data = json.loads(previnput)

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to filter: provide 'data' or pipe from previous task")

        if not isinstance(data, list):
            raise ValueError("Filter operation requires array/list data")

        # Validazione parametri
        requiredparams = ["field", "operator", "value"]
        if not oacommon.checkandloadparam(self, myself, requiredparams, param=param):
            raise ValueError(f"Missing required parameters for {funcname}")

        # Estrai parametri con supporto placeholder
        field = oacommon.getparam(param, "field", wallet) or gdict.get("field")
        operator = oacommon.getparam(param, "operator", wallet) or gdict.get("operator")
        value = oacommon.getparam(param, "value", wallet)
        if value is None:
            value = param.get("value")

        case_sensitive = param.get("case_sensitive", True)

        logger.info(f"Filter: {field} {operator} {value}")
        logger.debug(f"Input data: {len(data)} items")

        # Applica filtro
        filtered = []

        for item in data:
            if not isinstance(item, dict):
                logger.warning(f"Skipping non-dict item: {type(item)}")
                continue

            item_value = item.get(field)

            # Converti per confronto case-insensitive se necessario
            if not case_sensitive and isinstance(item_value, str) and isinstance(value, str):
                item_value = item_value.lower()
                compare_value = value.lower()
            else:
                compare_value = value

            # Applica operatore
            match = False

            try:
                if operator == "==":
                    match = item_value == compare_value
                elif operator == "!=":
                    match = item_value != compare_value
                elif operator == ">":
                    match = float(item_value) > float(compare_value)
                elif operator == "<":
                    match = float(item_value) < float(compare_value)
                elif operator == ">=":
                    match = float(item_value) >= float(compare_value)
                elif operator == "<=":
                    match = float(item_value) <= float(compare_value)
                elif operator == "contains":
                    match = compare_value in str(item_value)
                elif operator == "in":
                    # value deve essere una lista
                    if isinstance(compare_value, str):
                        compare_value = json.loads(compare_value)
                    match = item_value in compare_value
                elif operator == "exists":
                    match = field in item
                elif operator == "not_exists":
                    match = field not in item
                else:
                    raise ValueError(f"Unsupported operator: {operator}")

                if match:
                    filtered.append(item)

            except (ValueError, TypeError) as e:
                logger.warning(f"Comparison error for item {item}: {e}")
                continue

        logger.info(f"Filtered: {len(data)} -> {len(filtered)} items")

        # Salva in variabile se richiesto
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = filtered
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "filtered": filtered,
            "count": len(filtered),
            "original_count": len(data),
            "filter": {
                "field": field,
                "operator": operator,
                "value": value
            }
        }

    except json.JSONDecodeError as e:
        tasksuccess = False
        errormsg = f"Invalid JSON: {str(e)}"
        logger.error(errormsg)

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON filter failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata


@oacommon.trace
def jsonextract(self, param):
    """
    Estrae campi specifici da oggetti JSON

    Args:
        param (dict) con:
            - data: opzionale dati JSON (può usare input)
            - fields: lista di campi da estrarre - supporta WALLET{key}, ENV{var}
            - flatten: opzionale appiattisce oggetti nested (default: False)
            - keep_nulls: opzionale mantieni campi null (default: False)
            - saveonvar: opzionale salva risultato
            - input: opzionale dati dal task precedente
            - taskid, taskstore, workflowcontext

    Returns:
        tuple (success, extracted_data)

    Example:
        Input: [{"name": "Alice", "age": 30, "city": "Rome"}]
        Fields: ["name", "city"]
        Output: [{"name": "Alice", "city": "Rome"}]
    """
    funcname = myself()
    logger.info("JSON Extract operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation
        data = None
        if "data" in param:
            data = param["data"]
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "json" in previnput:
                    data = previnput["json"]
                elif "filtered" in previnput:
                    data = previnput["filtered"]
                elif "data" in previnput:
                    data = previnput["data"]
                else:
                    data = previnput
            elif isinstance(previnput, list):
                data = previnput
            elif isinstance(previnput, str):
                data = json.loads(previnput)

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to extract from")

        # Validazione parametri
        if not oacommon.checkandloadparam(self, myself, ["fields"], param=param):
            raise ValueError(f"Missing required parameter 'fields' for {funcname}")

        fields = param.get("fields")

        # Supporta stringa separata da virgola
        if isinstance(fields, str):
            # Risolvi placeholder se presente
            fields = oacommon.getparam(param, "fields", wallet) or fields
            fields = [f.strip() for f in fields.split(",")]

        flatten = param.get("flatten", False)
        keep_nulls = param.get("keep_nulls", False)

        logger.info(f"Extracting fields: {fields}")
        logger.debug(f"Flatten: {flatten}, Keep nulls: {keep_nulls}")

        # Estrai campi
        extracted = None

        if isinstance(data, dict):
            # Singolo oggetto
            result = {}
            for field in fields:
                # Supporta dot notation per nested fields
                if "." in field and flatten:
                    parts = field.split(".")
                    value = data
                    for part in parts:
                        if isinstance(value, dict):
                            value = value.get(part)
                        else:
                            value = None
                            break
                else:
                    value = data.get(field)

                if value is not None or keep_nulls:
                    result[field] = value

            extracted = result

        elif isinstance(data, list):
            # Array di oggetti
            results = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                result = {}
                for field in fields:
                    if "." in field and flatten:
                        parts = field.split(".")
                        value = item
                        for part in parts:
                            if isinstance(value, dict):
                                value = value.get(part)
                            else:
                                value = None
                                break
                    else:
                        value = item.get(field)

                    if value is not None or keep_nulls:
                        result[field] = value

                results.append(result)

            extracted = results

        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        logger.info(f"Extraction completed successfully")

        # Salva in variabile
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = extracted
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "extracted": extracted,
            "fields": fields,
            "count": len(extracted) if isinstance(extracted, list) else 1
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON extract failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata


@oacommon.trace
def jsontransform(self, param):
    """
    Trasforma dati JSON applicando mapping e trasformazioni

    Args:
        param (dict) con:
            - data: opzionale dati JSON (può usare input)
            - mapping: dict con {new_field: old_field} o {new_field: "function:old_field"}
            - functions: opzionale dict con funzioni custom
            - add_fields: opzionale dict con nuovi campi statici
            - remove_fields: opzionale lista campi da rimuovere
            - saveonvar: opzionale
            - input: opzionale dati dal task precedente

    Returns:
        tuple (success, transformed_data)

    Example:
        Input: {"first_name": "Alice", "last_name": "Smith", "age": 30}
        Mapping: {"name": "first_name", "years": "age"}
        Output: {"name": "Alice", "years": 30}
    """
    funcname = myself()
    logger.info("JSON Transform operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation
        data = None
        if "data" in param:
            data = param["data"]
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "extracted" in previnput:
                    data = previnput["extracted"]
                elif "filtered" in previnput:
                    data = previnput["filtered"]
                elif "json" in previnput:
                    data = previnput["json"]
                else:
                    data = previnput
            elif isinstance(previnput, list):
                data = previnput
            elif isinstance(previnput, str):
                data = json.loads(previnput)

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to transform")

        mapping = param.get("mapping", {})
        add_fields = param.get("add_fields", {})
        remove_fields = param.get("remove_fields", [])

        logger.info(f"Mapping: {len(mapping)} fields")
        if add_fields:
            logger.debug(f"Adding {len(add_fields)} static fields")
        if remove_fields:
            logger.debug(f"Removing {len(remove_fields)} fields")

        # Funzioni built-in per trasformazioni
        transform_functions = {
            "upper": lambda x: str(x).upper() if x else x,
            "lower": lambda x: str(x).lower() if x else x,
            "int": lambda x: int(x) if x else 0,
            "float": lambda x: float(x) if x else 0.0,
            "str": lambda x: str(x) if x is not None else "",
            "bool": lambda x: bool(x),
            "strip": lambda x: str(x).strip() if x else x,
        }

        # Aggiungi funzioni custom se fornite
        custom_functions = param.get("functions", {})

        def transform_item(item):
            """Trasforma un singolo item"""
            if not isinstance(item, dict):
                return item

            result = {}

            # Applica mapping
            for new_field, old_field in mapping.items():
                if isinstance(old_field, str):
                    # Controlla se c'è una funzione da applicare
                    if ":" in old_field:
                        func_name, field_name = old_field.split(":", 1)
                        value = item.get(field_name)

                        if func_name in transform_functions:
                            try:
                                value = transform_functions[func_name](value)
                            except Exception as e:
                                logger.warning(f"Transform function {func_name} failed: {e}")
                    else:
                        value = item.get(old_field)

                    result[new_field] = value

            # Copia campi non mappati (se non in remove_fields)
            for key, value in item.items():
                if key not in remove_fields and key not in mapping.values():
                    # Solo se non già presente nel result
                    if key not in result:
                        result[key] = value

            # Aggiungi campi statici
            for key, value in add_fields.items():
                # Risolvi placeholder nel valore
                if isinstance(value, str):
                    value = oacommon.getparam(f"{key}={value}", key, wallet) or value
                result[key] = value

            # Rimuovi campi specificati
            for field in remove_fields:
                result.pop(field, None)

            return result

        # Trasforma dati
        if isinstance(data, dict):
            transformed = transform_item(data)
        elif isinstance(data, list):
            transformed = [transform_item(item) for item in data if isinstance(item, dict)]
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

        logger.info("Transformation completed successfully")

        # Salva in variabile
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = transformed
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "transformed": transformed,
            "count": len(transformed) if isinstance(transformed, list) else 1
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON transform failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata


@oacommon.trace
def jsonmerge(self, param):
    """
    Unisce più oggetti/array JSON

    Args:
        param (dict) con:
            - sources: lista di chiavi da workflowcontext o lista di dati diretti
            - merge_type: "dict" (merge objects), "array" (concatena arrays), "deep" (deep merge)
            - overwrite: opzionale per dict merge (default: True)
            - unique: opzionale rimuovi duplicati in array merge (default: False)
            - saveonvar: opzionale
            - input: opzionale dati dal task precedente (viene aggiunto al merge)
            - workflowcontext: opzionale contesto workflow

    Returns:
        tuple (success, merged_data)
    """
    funcname = myself()
    logger.info("JSON Merge operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")
        merge_type = param.get("merge_type", "dict")
        overwrite = param.get("overwrite", True)
        unique = param.get("unique", False)

        # Raccogli dati da unire
        data_list = []

        # Da sources
        if "sources" in param:
            sources = param["sources"]
            workflowcontext = param.get("workflowcontext")

            if isinstance(sources, list):
                for source in sources:
                    if isinstance(source, str) and workflowcontext:
                        # Recupera da workflowcontext
                        data = workflowcontext.get_task_output(source)
                        if data:
                            data_list.append(data)
                    else:
                        # Dati diretti
                        data_list.append(source)

        # Aggiungi input se presente
        if "input" in param:
            previnput = param.get("input")
            if previnput:
                data_list.append(previnput)
                logger.info("Including input in merge")

        if len(data_list) < 2:
            raise ValueError("Need at least 2 data sources to merge")

        logger.info(f"Merging {len(data_list)} sources (type: {merge_type})")

        # Merge basato sul tipo
        merged = None

        if merge_type == "dict":
            # Merge di dict
            merged = {}
            for data in data_list:
                if isinstance(data, dict):
                    if overwrite:
                        merged.update(data)
                    else:
                        # Non sovrascrivere chiavi esistenti
                        for key, value in data.items():
                            if key not in merged:
                                merged[key] = value
                else:
                    logger.warning(f"Skipping non-dict data in dict merge: {type(data)}")

        elif merge_type == "array":
            # Concatena array
            merged = []
            for data in data_list:
                if isinstance(data, list):
                    merged.extend(data)
                elif isinstance(data, dict):
                    merged.append(data)
                else:
                    logger.warning(f"Skipping incompatible data in array merge: {type(data)}")

            # Rimuovi duplicati se richiesto
            if unique:
                # Per dict usa JSON string come chiave
                seen = set()
                unique_merged = []
                for item in merged:
                    item_str = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                    if item_str not in seen:
                        seen.add(item_str)
                        unique_merged.append(item)
                merged = unique_merged
                logger.debug(f"Removed {len(data_list) - len(merged)} duplicates")

        elif merge_type == "deep":
            # Deep merge ricorsivo per dict nested
            def deep_merge(dict1, dict2):
                result = dict1.copy()
                for key, value in dict2.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result

            merged = {}
            for data in data_list:
                if isinstance(data, dict):
                    merged = deep_merge(merged, data)
                else:
                    logger.warning(f"Skipping non-dict data in deep merge: {type(data)}")

        else:
            raise ValueError(f"Unsupported merge_type: {merge_type}")

        logger.info(f"Merge completed successfully")

        # Salva in variabile
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = merged
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "merged": merged,
            "sources_count": len(data_list),
            "merge_type": merge_type
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON merge failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata


@oacommon.trace
def jsonaggregate(self, param):
    """
    Aggrega dati JSON (sum, avg, count, min, max, group)

    Args:
        param (dict) con:
            - data: opzionale dati JSON array (può usare input)
            - operation: sum, avg, count, min, max, group
            - field: campo su cui aggregare - supporta WALLET{key}, ENV{var}
            - group_by: opzionale campo per raggruppamento
            - saveonvar: opzionale
            - input: opzionale dati dal task precedente

    Returns:
        tuple (success, aggregated_data)

    Example:
        Input: [{"category": "A", "value": 10}, {"category": "A", "value": 20}]
        Operation: sum, Field: value, Group_by: category
        Output: {"A": 30}
    """
    funcname = myself()
    logger.info("JSON Aggregate operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation
        data = None
        if "data" in param:
            data = param["data"]
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "filtered" in previnput:
                    data = previnput["filtered"]
                elif "transformed" in previnput:
                    data = previnput["transformed"]
                elif "json" in previnput:
                    data = previnput["json"]
                else:
                    # Cerca un array dentro l'input
                    for key, value in previnput.items():
                        if isinstance(value, list):
                            data = value
                            break
            elif isinstance(previnput, list):
                data = previnput

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to aggregate")

        if not isinstance(data, list):
            raise ValueError("Aggregate operation requires array data")

        # Validazione parametri
        requiredparams = ["operation"]
        if not oacommon.checkandloadparam(self, myself, requiredparams, param=param):
            raise ValueError(f"Missing required parameters for {funcname}")

        operation = oacommon.getparam(param, "operation", wallet) or gdict.get("operation")
        field = oacommon.getparam(param, "field", wallet) or param.get("field")
        group_by = oacommon.getparam(param, "group_by", wallet) or param.get("group_by")

        logger.info(f"Operation: {operation}, Field: {field}, Group by: {group_by}")

        result = None

        if operation == "count":
            if group_by:
                # Conta per gruppo
                counts = {}
                for item in data:
                    if isinstance(item, dict):
                        group_value = item.get(group_by, "null")
                        counts[str(group_value)] = counts.get(str(group_value), 0) + 1
                result = counts
            else:
                result = len(data)

        elif operation in ["sum", "avg", "min", "max"]:
            if not field:
                raise ValueError(f"Field is required for {operation} operation")

            if group_by:
                # Aggrega per gruppo
                groups = {}
                for item in data:
                    if not isinstance(item, dict):
                        continue

                    group_value = str(item.get(group_by, "null"))
                    field_value = item.get(field)

                    if field_value is not None:
                        if group_value not in groups:
                            groups[group_value] = []
                        try:
                            groups[group_value].append(float(field_value))
                        except (ValueError, TypeError):
                            logger.warning(f"Skipping non-numeric value: {field_value}")

                # Calcola aggregazione per ogni gruppo
                result = {}
                for group, values in groups.items():
                    if values:
                        if operation == "sum":
                            result[group] = sum(values)
                        elif operation == "avg":
                            result[group] = sum(values) / len(values)
                        elif operation == "min":
                            result[group] = min(values)
                        elif operation == "max":
                            result[group] = max(values)

            else:
                # Aggrega su tutto il dataset
                values = []
                for item in data:
                    if isinstance(item, dict):
                        field_value = item.get(field)
                        if field_value is not None:
                            try:
                                values.append(float(field_value))
                            except (ValueError, TypeError):
                                logger.warning(f"Skipping non-numeric value: {field_value}")

                if values:
                    if operation == "sum":
                        result = sum(values)
                    elif operation == "avg":
                        result = sum(values) / len(values)
                    elif operation == "min":
                        result = min(values)
                    elif operation == "max":
                        result = max(values)
                else:
                    result = 0

        elif operation == "group":
            # Raggruppa elementi
            if not group_by:
                raise ValueError("group_by is required for group operation")

            groups = {}
            for item in data:
                if isinstance(item, dict):
                    group_value = str(item.get(group_by, "null"))
                    if group_value not in groups:
                        groups[group_value] = []
                    groups[group_value].append(item)

            result = groups

        else:
            raise ValueError(f"Unsupported operation: {operation}")

        logger.info(f"Aggregation completed: {operation}")

        # Salva in variabile
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = result
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "result": result,
            "operation": operation,
            "field": field,
            "group_by": group_by,
            "input_count": len(data)
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON aggregate failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata


@oacommon.trace
def jsonvalidate(self, param):
    """
    Valida JSON contro un JSON Schema

    Args:
        param (dict) con:
            - data: opzionale dati JSON (può usare input)
            - schema: JSON Schema per validazione
            - strict: opzionale fail on validation error (default: True)
            - saveonvar: opzionale
            - input: opzionale dati dal task precedente

    Returns:
        tuple (success, validation_result)
    """
    funcname = myself()
    logger.info("JSON Validate operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        # Import opzionale di jsonschema
        try:
            import jsonschema
            from jsonschema import validate, ValidationError
        except ImportError:
            raise ImportError("jsonschema library not installed. Run: pip install jsonschema")

        wallet = gdict.get("wallet")

        # Data propagation
        data = None
        if "data" in param:
            data = param["data"]
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "json" in previnput:
                    data = previnput["json"]
                elif "transformed" in previnput:
                    data = previnput["transformed"]
                else:
                    data = previnput
            elif isinstance(previnput, str):
                data = json.loads(previnput)
            else:
                data = previnput

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to validate")

        if not oacommon.checkandloadparam(self, myself, ["schema"], param=param):
            raise ValueError(f"Missing required parameter 'schema' for {funcname}")

        schema = param.get("schema")
        strict = param.get("strict", True)

        logger.info("Validating JSON against schema")

        # Valida
        valid = True
        errors = []

        try:
            validate(instance=data, schema=schema)
            logger.info("✓ JSON validation passed")

        except ValidationError as e:
            valid = False
            errors.append({
                "message": e.message,
                "path": list(e.path),
                "validator": e.validator
            })
            logger.warning(f"✗ JSON validation failed: {e.message}")

            if strict:
                tasksuccess = False
                errormsg = f"JSON validation failed: {e.message}"

        # Salva in variabile
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = {"valid": valid, "errors": errors}
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "valid": valid,
            "errors": errors,
            "data": data,
            "strict_mode": strict
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON validate failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata


@oacommon.trace
def jsonsort(self, param):
    """
    Ordina array JSON per campo

    Args:
        param (dict) con:
            - data: opzionale dati JSON array (può usare input)
            - sort_by: campo per ordinamento - supporta WALLET{key}, ENV{var}
            - reverse: opzionale ordine decrescente (default: False)
            - numeric: opzionale ordina come numeri (default: auto-detect)
            - saveonvar: opzionale
            - input: opzionale dati dal task precedente

    Returns:
        tuple (success, sorted_data)
    """
    funcname = myself()
    logger.info("JSON Sort operation")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation
        data = None
        if "data" in param:
            data = param["data"]
            if isinstance(data, str):
                data = json.loads(data)
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "filtered" in previnput:
                    data = previnput["filtered"]
                elif "json" in previnput:
                    data = previnput["json"]
                else:
                    # Cerca array
                    for key, value in previnput.items():
                        if isinstance(value, list):
                            data = value
                            break
            elif isinstance(previnput, list):
                data = previnput

            logger.info("Using data from previous task")

        if data is None:
            raise ValueError("No data to sort")

        if not isinstance(data, list):
            raise ValueError("Sort operation requires array data")

        if not oacommon.checkandloadparam(self, myself, ["sort_by"], param=param):
            raise ValueError(f"Missing required parameter 'sort_by' for {funcname}")

        sort_by = oacommon.getparam(param, "sort_by", wallet) or gdict.get("sort_by")
        reverse = param.get("reverse", False)
        numeric = param.get("numeric", None)

        logger.info(f"Sorting by: {sort_by}, Reverse: {reverse}")

        # Determina se ordinare come numero
        if numeric is None:
            # Auto-detect: controlla il primo valore
            for item in data:
                if isinstance(item, dict):
                    value = item.get(sort_by)
                    if value is not None:
                        numeric = isinstance(value, (int, float))
                        break

        # Ordina
        def sort_key(item):
            if isinstance(item, dict):
                value = item.get(sort_by)
                if value is None:
                    return float('inf') if numeric else ''
                if numeric:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return float('inf')
                return str(value).lower()
            return item

        sorted_data = sorted(data, key=sort_key, reverse=reverse)

        logger.info(f"Sorted {len(sorted_data)} items")

        # Salva in variabile
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = sorted_data
            logger.debug(f"Result saved to variable {saveonvar}")

        outputdata = {
            "sorted": sorted_data,
            "count": len(sorted_data),
            "sort_by": sort_by,
            "reverse": reverse,
            "numeric": numeric
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON sort failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata
