"""
Open-Automator Utility Module
Funzioni di utilità (variabili, sleep, dump)
"""

import oacommon
import time
import inspect
import json
import logging
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
    Pausa l'esecuzione per un numero di secondi

    Args:
        param: dict con:
            - seconds: numero di secondi da attendere
            - task_id: (opzionale)
            - task_store: (opzionale)
    """
    func_name = myself()
    logger.info("Sleep/pause execution")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    try:
        if not oacommon.checkandloadparam(self, myself, 'seconds', param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        seconds = gdict['seconds']
        logger.info(f"Sleeping for {seconds} seconds...")

        time.sleep(seconds)
        logger.info("Sleep completed")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Sleep operation failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success


@oacommon.trace
def printvar(self, param):
    """
    Stampa il valore di una variabile

    Args:
        param: dict con:
            - varname: nome della variabile da stampare
            - task_id: (opzionale)
            - task_store: (opzionale)
    """
    func_name = myself()
    logger.info("Printing variable")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    try:
        if not oacommon.checkandloadparam(self, myself, 'varname', param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        varname = gdict['varname']

        if varname not in gdict:
            logger.warning(f"Variable '{varname}' not found in gdict")
            logger.info(f"Variable '{varname}' = <NOT FOUND>")
            task_success = False
            error_msg = f"Variable '{varname}' not found"
        else:
            value = gdict[varname]

            # Log appropriato in base al tipo e dimensione
            if isinstance(value, (dict, list)):
                logger.info(f"Variable '{varname}' (type: {type(value).__name__}):")
                logger.info(json.dumps(value, indent=2, default=str))
            elif isinstance(value, str) and len(value) > 500:
                logger.info(
                    f"Variable '{varname}' = {value[:500]}... "
                    f"(truncated, total: {len(value)} chars)"
                )
            else:
                logger.info(f"Variable '{varname}' = {value}")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Failed to print variable '{varname}': {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success


@oacommon.trace
def setvar(self, param):
    """
    Imposta il valore di una variabile

    Args:
        param: dict con:
            - varname: nome della variabile
            - varvalue: valore da assegnare
            - task_id: (opzionale)
            - task_store: (opzionale)
    """
    func_name = myself()
    logger.info("Setting variable")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    required_params = ['varname', 'varvalue']

    try:
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        varname = gdict['varname']
        varvalue = gdict['varvalue']

        logger.info(f"Setting: {varname} = {varvalue}")

        gdict[varname] = varvalue
        logger.debug(f"Variable '{varname}' set successfully")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Failed to set variable '{varname}': {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success


@oacommon.trace
def dumpvar(self, param):
    """
    Esporta tutte le variabili del gdict in un file JSON

    Args:
        param: dict con:
            - savetofile: (opzionale) path del file JSON di output
            - task_id: (opzionale)
            - task_store: (opzionale)
    """
    func_name = myself()
    logger.info("Dumping all variables")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""

    savetofile = None
    if oacommon.checkparam('savetofile', param):
        savetofile = param['savetofile']
        logger.debug(f"Output file: {savetofile}")

    try:
        # Filtra variabili di sistema
        filtered_gdict = {
            k: v for k, v in self.gdict.items()
            if not k.startswith('_') and k not in ['DEBUG', 'DEBUG2', 'TRACE']
        }

        json_output = json.dumps(filtered_gdict, indent=4, sort_keys=True, default=str)

        logger.info(f"Variables dump ({len(filtered_gdict)} variables):")
        logger.info(json_output)

        if savetofile:
            with open(savetofile, 'w', encoding='utf-8') as f:
                f.write(json_output)
            logger.info(f"Variables saved to: {savetofile}")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Failed to dump variables: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success
