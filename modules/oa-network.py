"""
Open-Automator Network Module
Gestisce operazioni di rete (HTTP, HTTPS)
"""

import requests
import oacommon
import inspect
import http.client
import logging
from logger_config import AutomatorLogger

# Logger per questo modulo
logger = AutomatorLogger.get_logger('oa-network')

gdict = {}
myself = lambda: inspect.stack()[1][3]


def setgdict(self, gdict_param):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

@oacommon.trace
def httpget(self, param):
    """
    Esegue una richiesta HTTP GET

    Args:
        param: dict con:
            - host: hostname o IP
            - port: porta HTTP
            - get: path della richiesta
            - printout: (opzionale) stampa response
            - saveonvar: (opzionale) salva response in variabile
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    """
    func_name = myself()
    logger.info("Executing HTTP GET request")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output = ""

    required_params = ['host', 'port', 'get']

    connection = None

    try:
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        host = oacommon.effify(gdict['host'])
        port = int(oacommon.effify(gdict['port']))
        get_path = gdict['get']

        logger.info(f"HTTP GET: http://{host}:{port}{get_path}")

        connection = http.client.HTTPConnection(host, port, timeout=30)
        connection.request('GET', get_path)
        response = connection.getresponse()

        logger.info(f"HTTP Status: {response.status} {response.reason}")

        output = response.read().decode('utf-8', errors='ignore')

        # se vuoi considerare status >=400 come failure
        if response.status >= 400:
            task_success = False
            error_msg = f"HTTP error {response.status} {response.reason}"

        # Gestione printout
        if oacommon.checkparam('printout', param):
            printout = param['printout']
            if printout:
                if len(output) > 1000:
                    logger.info(f"Response (first 1000 chars):\n{output[:1000]}...")
                else:
                    logger.info(f"Response:\n{output}")

        # Salva in variabile
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = output
            logger.debug(f"Response saved to variable: {saveonvar}")

        logger.info(f"HTTP GET completed, response size: {len(output)} bytes")

    except http.client.HTTPException as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"HTTP connection error to {host}:{port}: {e}", exc_info=True)
    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"HTTP GET request failed: {e}", exc_info=True)
    finally:
        if connection:
            connection.close()
            logger.debug("HTTP connection closed")
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success


@oacommon.trace
def httpsget(self, param):
    """
    Esegue una richiesta HTTPS GET

    Args:
        param: dict con:
            - host: hostname o IP
            - port: porta HTTPS
            - get: path della richiesta
            - verify: (opzionale) verifica certificato SSL, default True
            - printout: (opzionale) stampa response
            - saveonvar: (opzionale) salva response in variabile
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    """
    func_name = myself()
    logger.info("Executing HTTPS GET request")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output = ""

    required_params = ['host', 'port', 'get']

    try:
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        host = oacommon.effify(gdict['host'])
        port = int(oacommon.effify(gdict['port']))
        get_path = gdict['get']

        # SSL verify
        verify = True
        if oacommon.checkparam('verify', param):
            verify = param['verify']
            if not verify:
                logger.warning("SSL certificate verification DISABLED - insecure connection!")

        url = f"https://{host}:{port}{get_path}"
        logger.info(f"HTTPS GET: {url}")
        logger.debug(f"SSL verify: {verify}")

        # Disabilita warning solo se verify=False
        if not verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.get(url, verify=verify, timeout=30)

        logger.info(f"HTTPS Status: {response.status_code} {response.reason}")

        output = response.content.decode('utf-8', errors='ignore')

        # considera status >=400 come failure
        if response.status_code >= 400:
            task_success = False
            error_msg = f"HTTPS error {response.status_code} {response.reason}"

        # Gestione printout
        if oacommon.checkparam('printout', param):
            printout = param['printout']
            if printout:
                if len(output) > 1000:
                    logger.info(f"Response (first 1000 chars):\n{output[:1000]}...")
                else:
                    logger.info(f"Response:\n{output}")

        # Salva in variabile
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = output
            logger.debug(f"Response saved to variable: {saveonvar}")

        logger.info(f"HTTPS GET completed, response size: {len(output)} bytes")

    except requests.exceptions.SSLError as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"SSL verification failed for {url}: {e}")
        logger.error("Consider setting verify: False in YAML (NOT recommended for production)")
    except requests.exceptions.ConnectionError as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Connection error to {url}: {e}", exc_info=True)
    except requests.exceptions.Timeout as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Request timeout to {url}: {e}")
    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"HTTPS GET request failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success

