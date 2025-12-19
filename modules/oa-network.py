"""
Open-Automator Network Module
Gestisce operazioni di rete (HTTP, HTTPS) con data propagation
Supporto per wallet, placeholder {WALLET:key}, {ENV:var} e {VAULT:key}
"""

import requests
import oacommon
import inspect
import http.client
import json
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
    Esegue una richiesta HTTP GET con data propagation

    Args:
        param: dict con:
            - host: hostname o IP (può derivare da input precedente) - supporta {WALLET:key}, {ENV:var}
            - port: porta HTTP - supporta {ENV:var}
            - get: path della richiesta - supporta {WALLET:key}, {ENV:var}
            - printout: (opzionale) stampa response
            - saveonvar: (opzionale) salva response in variabile
            - headers: (opzionale) dict con headers custom - supporta {WALLET:key} nei valori
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore

    Returns:
        tuple: (success, output_dict) con response data
    """
    func_name = myself()
    logger.info("Executing HTTP GET request")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = ['host', 'port', 'get']
    connection = None

    try:
        # Se host/port/get non specificati, prova a derivarli dall'input
        if 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'host' not in param and 'host' in prev_input:
                    param['host'] = prev_input['host']
                if 'port' not in param and 'port' in prev_input:
                    param['port'] = prev_input['port']
                if 'url' in prev_input:
                    # Parse URL completo
                    from urllib.parse import urlparse
                    parsed = urlparse(prev_input['url'])
                    if not param.get('host'):
                        param['host'] = parsed.hostname
                    if not param.get('port'):
                        param['port'] = parsed.port or 80
                    if not param.get('get'):
                        param['get'] = parsed.path or '/'
                    logger.info(f"Using URL from previous task: {prev_input['url']}")

        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        # Usa get_param per supportare placeholder
        host = oacommon.get_param(param, 'host', wallet) or gdict.get('host')
        port_str = oacommon.get_param(param, 'port', wallet) or gdict.get('port')
        port = int(port_str)
        get_path = oacommon.get_param(param, 'get', wallet) or gdict.get('get')

        # Headers custom con supporto placeholder nei valori
        custom_headers = {}
        if oacommon.checkparam('headers', param):
            headers_param = param['headers']
            if isinstance(headers_param, dict):
                for key, value in headers_param.items():
                    if isinstance(value, str):
                        custom_headers[key] = oacommon.get_param({key: value}, key, wallet) or value
                    else:
                        custom_headers[key] = value
                logger.debug(f"Custom headers with placeholders resolved")

        logger.info(f"HTTP GET: http://{host}:{port}{get_path}")

        connection = http.client.HTTPConnection(host, port, timeout=30)

        # Prepara headers
        if custom_headers:
            for key, value in custom_headers.items():
                connection.putheader(key, value)

        connection.request('GET', get_path)
        response = connection.getresponse()

        logger.info(f"HTTP Status: {response.status} {response.reason}")

        # Leggi response body
        response_body = response.read().decode('utf-8', errors='ignore')

        # Prova a parsare come JSON
        parsed_json = None
        content_type = response.getheader('Content-Type', '')
        if 'application/json' in content_type:
            try:
                parsed_json = json.loads(response_body)
                logger.debug("Response parsed as JSON")
            except json.JSONDecodeError:
                logger.debug("Failed to parse response as JSON")

        # Se vuoi considerare status >=400 come failure
        if response.status >= 400:
            task_success = False
            error_msg = f"HTTP error {response.status} {response.reason}"

        # Gestione printout
        if oacommon.checkparam('printout', param):
            printout = param['printout']
            if printout:
                if len(response_body) > 1000:
                    logger.info(f"Response (first 1000 chars):\n{response_body[:1000]}...")
                else:
                    logger.info(f"Response:\n{response_body}")

        # Salva in variabile (retrocompatibilità)
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = response_body
            logger.debug(f"Response saved to variable: {saveonvar}")

        logger.info(f"HTTP GET completed, response size: {len(response_body)} bytes")

        # Output data per propagation
        output_data = {
            'status_code': response.status,
            'reason': response.reason,
            'content': response_body,
            'size': len(response_body),
            'headers': dict(response.getheaders()),
            'url': f"http://{host}:{port}{get_path}"
        }

        # Se parsato come JSON, aggiungi anche quello
        if parsed_json is not None:
            output_data['json'] = parsed_json

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

    return task_success, output_data

@oacommon.trace
def httpsget(self, param):
    """
    Esegue una richiesta HTTPS GET con data propagation

    Args:
        param: dict con:
            - host: hostname o IP (può derivare da input precedente) - supporta {WALLET:key}, {ENV:var}
            - port: porta HTTPS - supporta {ENV:var}
            - get: path della richiesta - supporta {WALLET:key}, {ENV:var}
            - verify: (opzionale) verifica certificato SSL, default True
            - printout: (opzionale) stampa response
            - saveonvar: (opzionale) salva response in variabile
            - headers: (opzionale) dict con headers custom - supporta {WALLET:key} nei valori (es. token)
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore

    Returns:
        tuple: (success, output_dict) con response data
    """
    func_name = myself()
    logger.info("Executing HTTPS GET request")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = ['host', 'port', 'get']

    try:
        # Se host/port/get non specificati, prova a derivarli dall'input
        if 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'host' not in param and 'host' in prev_input:
                    param['host'] = prev_input['host']
                if 'port' not in param and 'port' in prev_input:
                    param['port'] = prev_input['port']
                if 'url' in prev_input:
                    # Parse URL completo
                    from urllib.parse import urlparse
                    parsed = urlparse(prev_input['url'])
                    if not param.get('host'):
                        param['host'] = parsed.hostname
                    if not param.get('port'):
                        param['port'] = parsed.port or 443
                    if not param.get('get'):
                        param['get'] = parsed.path or '/'
                    logger.info(f"Using URL from previous task: {prev_input['url']}")

        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        # Usa get_param per supportare placeholder
        host = oacommon.get_param(param, 'host', wallet) or gdict.get('host')
        port_str = oacommon.get_param(param, 'port', wallet) or gdict.get('port')
        port = int(port_str)
        get_path = oacommon.get_param(param, 'get', wallet) or gdict.get('get')

        # SSL verify
        verify = True
        if oacommon.checkparam('verify', param):
            verify = param['verify']
            if not verify:
                logger.warning("SSL certificate verification DISABLED - insecure connection!")

        # Headers custom con supporto placeholder (importante per API token!)
        headers = {}
        if oacommon.checkparam('headers', param):
            headers_param = param['headers']
            if isinstance(headers_param, dict):
                for key, value in headers_param.items():
                    if isinstance(value, str):
                        # Risolvi placeholder nei valori degli header (es. Bearer {WALLET:api_token})
                        headers[key] = oacommon.get_param({key: value}, key, wallet) or value
                    else:
                        headers[key] = value
                logger.debug(f"Custom headers with placeholders resolved (tokens hidden)")

        url = f"https://{host}:{port}{get_path}"
        logger.info(f"HTTPS GET: {url}")
        logger.debug(f"SSL verify: {verify}")

        # Disabilita warning solo se verify=False
        if not verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.get(url, verify=verify, headers=headers, timeout=30)

        logger.info(f"HTTPS Status: {response.status_code} {response.reason}")

        response_body = response.content.decode('utf-8', errors='ignore')

        # Prova a parsare come JSON
        parsed_json = None
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            try:
                parsed_json = response.json()
                logger.debug("Response parsed as JSON")
            except json.JSONDecodeError:
                logger.debug("Failed to parse response as JSON")

        # Considera status >=400 come failure
        if response.status_code >= 400:
            task_success = False
            error_msg = f"HTTPS error {response.status_code} {response.reason}"

        # Gestione printout
        if oacommon.checkparam('printout', param):
            printout = param['printout']
            if printout:
                if len(response_body) > 1000:
                    logger.info(f"Response (first 1000 chars):\n{response_body[:1000]}...")
                else:
                    logger.info(f"Response:\n{response_body}")

        # Salva in variabile (retrocompatibilità)
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = response_body
            logger.debug(f"Response saved to variable: {saveonvar}")

        logger.info(f"HTTPS GET completed, response size: {len(response_body)} bytes")

        # Output data per propagation
        output_data = {
            'status_code': response.status_code,
            'reason': response.reason,
            'content': response_body,
            'size': len(response_body),
            'headers': dict(response.headers),
            'url': url,
            'elapsed_ms': response.elapsed.total_seconds() * 1000
        }

        # Se parsato come JSON, aggiungi anche quello
        if parsed_json is not None:
            output_data['json'] = parsed_json

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

    return task_success, output_data

@oacommon.trace
def httppost(self, param):
    """
    Esegue una richiesta HTTP POST con data propagation

    Args:
        param: dict con:
            - host: hostname o IP - supporta {WALLET:key}, {ENV:var}
            - port: porta HTTP - supporta {ENV:var}
            - path: path della richiesta - supporta {WALLET:key}, {ENV:var}
            - data: dati da inviare (può venire da input precedente) - supporta {WALLET:key}
            - headers: (opzionale) dict con headers custom - supporta {WALLET:key} nei valori
            - content_type: (opzionale) default 'application/json'
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore

    Returns:
        tuple: (success, output_dict) con response data
    """
    func_name = myself()
    logger.info("Executing HTTP POST request")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        # Determina i dati da inviare
        post_data = None

        # 1. Se c'è 'data' esplicito (con supporto placeholder)
        if 'data' in param:
            data_param = param['data']
            # Se è una stringa, risolvi placeholder
            if isinstance(data_param, str):
                post_data = oacommon.get_param(param, 'data', wallet) or data_param
            # Se è dict/list, usa com'è (ma potrebbe avere placeholder nei valori)
            elif isinstance(data_param, dict):
                # Risolvi placeholder ricorsivamente nel dict
                post_data = {}
                for key, value in data_param.items():
                    if isinstance(value, str):
                        post_data[key] = oacommon.get_param({key: value}, key, wallet) or value
                    else:
                        post_data[key] = value
            else:
                post_data = data_param
        # 2. Altrimenti usa input dal task precedente
        elif 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                # Se c'è campo 'json', usalo
                if 'json' in prev_input:
                    post_data = prev_input['json']
                # Altrimenti usa tutto l'input
                else:
                    post_data = prev_input
            elif isinstance(prev_input, str):
                post_data = prev_input
            logger.info("Using data from previous task")

        if post_data is None:
            raise ValueError("No data to POST (provide 'data' or pipe from previous task)")

        required_params = ['host', 'port', 'path']
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Usa get_param per supportare placeholder
        host = oacommon.get_param(param, 'host', wallet) or gdict.get('host')
        port_str = oacommon.get_param(param, 'port', wallet) or gdict.get('port')
        port = int(port_str)
        path = oacommon.get_param(param, 'path', wallet) or gdict.get('path')

        # Headers con supporto placeholder
        content_type = param.get('content_type', 'application/json')
        headers = param.get('headers', {})

        # Risolvi placeholder negli headers
        if isinstance(headers, dict):
            resolved_headers = {}
            for key, value in headers.items():
                if isinstance(value, str):
                    resolved_headers[key] = oacommon.get_param({key: value}, key, wallet) or value
                else:
                    resolved_headers[key] = value
            headers = resolved_headers

        headers['Content-Type'] = content_type

        # Se i dati sono dict/list, converti in JSON
        if isinstance(post_data, (dict, list)):
            post_body = json.dumps(post_data)
        else:
            post_body = str(post_data)

        url = f"http://{host}:{port}{path}"
        logger.info(f"HTTP POST: {url}")
        logger.debug(f"Data size: {len(post_body)} bytes")

        response = requests.post(url, data=post_body, headers=headers, timeout=30)

        logger.info(f"HTTP Status: {response.status_code} {response.reason}")

        response_body = response.content.decode('utf-8', errors='ignore')

        # Prova a parsare come JSON
        parsed_json = None
        if 'application/json' in response.headers.get('Content-Type', ''):
            try:
                parsed_json = response.json()
            except:
                pass

        if response.status_code >= 400:
            task_success = False
            error_msg = f"HTTP error {response.status_code} {response.reason}"

        logger.info(f"HTTP POST completed, response size: {len(response_body)} bytes")

        # Output data
        output_data = {
            'status_code': response.status_code,
            'reason': response.reason,
            'content': response_body,
            'size': len(response_body),
            'headers': dict(response.headers),
            'url': url
        }

        if parsed_json is not None:
            output_data['json'] = parsed_json

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"HTTP POST request failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def httpspost(self, param):
    """
    Esegue una richiesta HTTPS POST con data propagation

    Args:
        param: dict con:
            - host: hostname o IP - supporta {WALLET:key}, {ENV:var}
            - port: porta HTTPS - supporta {ENV:var}
            - path: path della richiesta - supporta {WALLET:key}, {ENV:var}
            - data: dati da inviare (può venire da input precedente) - supporta {WALLET:key}
            - headers: (opzionale) dict con headers custom - supporta {WALLET:key} nei valori (es. API key)
            - content_type: (opzionale) default 'application/json'
            - verify: (opzionale) verifica certificato SSL, default True
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore

    Returns:
        tuple: (success, output_dict) con response data
    """
    func_name = myself()
    logger.info("Executing HTTPS POST request")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Recupera wallet per risoluzione placeholder
        wallet = gdict.get('_wallet')

        # Determina i dati da inviare (stesso meccanismo di httppost)
        post_data = None

        if 'data' in param:
            data_param = param['data']
            if isinstance(data_param, str):
                post_data = oacommon.get_param(param, 'data', wallet) or data_param
            elif isinstance(data_param, dict):
                post_data = {}
                for key, value in data_param.items():
                    if isinstance(value, str):
                        post_data[key] = oacommon.get_param({key: value}, key, wallet) or value
                    else:
                        post_data[key] = value
            else:
                post_data = data_param
        elif 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'json' in prev_input:
                    post_data = prev_input['json']
                else:
                    post_data = prev_input
            elif isinstance(prev_input, str):
                post_data = prev_input
            logger.info("Using data from previous task")

        if post_data is None:
            raise ValueError("No data to POST (provide 'data' or pipe from previous task)")

        required_params = ['host', 'port', 'path']
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Usa get_param per supportare placeholder
        host = oacommon.get_param(param, 'host', wallet) or gdict.get('host')
        port_str = oacommon.get_param(param, 'port', wallet) or gdict.get('port')
        port = int(port_str)
        path = oacommon.get_param(param, 'path', wallet) or gdict.get('path')

        # SSL verify
        verify = param.get('verify', True)
        if not verify:
            logger.warning("SSL certificate verification DISABLED")
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Headers con supporto placeholder (importante per API keys!)
        content_type = param.get('content_type', 'application/json')
        headers = param.get('headers', {})

        if isinstance(headers, dict):
            resolved_headers = {}
            for key, value in headers.items():
                if isinstance(value, str):
                    resolved_headers[key] = oacommon.get_param({key: value}, key, wallet) or value
                else:
                    resolved_headers[key] = value
            headers = resolved_headers

        headers['Content-Type'] = content_type

        # Converti dati
        if isinstance(post_data, (dict, list)):
            post_body = json.dumps(post_data)
        else:
            post_body = str(post_data)

        url = f"https://{host}:{port}{path}"
        logger.info(f"HTTPS POST: {url}")
        logger.debug(f"Data size: {len(post_body)} bytes")

        response = requests.post(url, data=post_body, headers=headers, verify=verify, timeout=30)

        logger.info(f"HTTPS Status: {response.status_code} {response.reason}")

        response_body = response.content.decode('utf-8', errors='ignore')

        parsed_json = None
        if 'application/json' in response.headers.get('Content-Type', ''):
            try:
                parsed_json = response.json()
            except:
                pass

        if response.status_code >= 400:
            task_success = False
            error_msg = f"HTTPS error {response.status_code} {response.reason}"

        logger.info(f"HTTPS POST completed, response size: {len(response_body)} bytes")

        output_data = {
            'status_code': response.status_code,
            'reason': response.reason,
            'content': response_body,
            'size': len(response_body),
            'headers': dict(response.headers),
            'url': url,
            'elapsed_ms': response.elapsed.total_seconds() * 1000
        }

        if parsed_json is not None:
            output_data['json'] = parsed_json

    except requests.exceptions.SSLError as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"SSL verification failed: {e}")
    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"HTTPS POST request failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data