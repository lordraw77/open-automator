"""
Open-Automator Network Module

Manages network operations (HTTP, HTTPS) with data propagation
Support for wallet, placeholder {WALLET:key}, {ENV:var} and {VAULT:key}
"""

import requests
import oacommon
import inspect
import http.client
import json
import logging
from logger_config import AutomatorLogger

# Logger for this module
logger = AutomatorLogger.get_logger('oa-network')

gdict = {}
myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdict_param):
    """Sets the global dictionary"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

@oacommon.trace
def httpget(self, param):
    """
    Executes an HTTP GET request with data propagation

    Args:
        param: dict with:
            - host: hostname or IP (can derive from previous input) - supports {WALLET:key}, {ENV:var}
            - port: HTTP port - supports {ENV:var}
            - get: request path - supports {WALLET:key}, {ENV:var}
            - printout: (optional) print response
            - saveonvar: (optional) save response to variable
            - headers: (optional) dict with custom headers - supports {WALLET:key} in values
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with response data

    Example YAML:
        # Simple HTTP GET request
        - name: fetch_api_data
          module: oa-network
          function: httpget
          host: "api.example.com"
          port: 80
          get: "/api/v1/users"

        # With custom headers
        - name: api_with_headers
          module: oa-network
          function: httpget
          host: "api.example.com"
          port: 80
          get: "/api/data"
          headers:
            User-Agent: "Open-Automator/1.0"
            Accept: "application/json"

        # Using environment variables
        - name: fetch_from_env
          module: oa-network
          function: httpget
          host: "{ENV:API_HOST}"
          port: 80
          get: "{ENV:API_PATH}"
          printout: true

        # With authentication header from wallet
        - name: authenticated_get
          module: oa-network
          function: httpget
          host: "secure-api.example.com"
          port: 80
          get: "/api/protected"
          headers:
            Authorization: "Bearer {WALLET:api_token}"

        # Using URL from previous task
        - name: fetch_dynamic_url
          module: oa-network
          function: httpget
          # host, port, get extracted from previous task's 'url' field
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
        # If host/port/get not specified, try to derive from input
        if 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'host' not in param and 'host' in prev_input:
                    param['host'] = prev_input['host']
                if 'port' not in param and 'port' in prev_input:
                    param['port'] = prev_input['port']
                if 'url' in prev_input:
                    # Parse complete URL
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        host = oacommon.get_param(param, 'host', wallet) or gdict.get('host')
        port_str = oacommon.get_param(param, 'port', wallet) or gdict.get('port')
        port = int(port_str)
        get_path = oacommon.get_param(param, 'get', wallet) or gdict.get('get')

        # Custom headers with placeholder support in values
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

        # Prepare headers
        if custom_headers:
            for key, value in custom_headers.items():
                connection.putheader(key, value)

        connection.request('GET', get_path)
        response = connection.getresponse()

        logger.info(f"HTTP Status: {response.status} {response.reason}")

        # Read response body
        response_body = response.read().decode('utf-8', errors='ignore')

        # Try to parse as JSON
        parsed_json = None
        content_type = response.getheader('Content-Type', '')
        if 'application/json' in content_type:
            try:
                parsed_json = json.loads(response_body)
                logger.debug("Response parsed as JSON")
            except json.JSONDecodeError:
                logger.debug("Failed to parse response as JSON")

        # Consider status >=400 as failure
        if response.status >= 400:
            task_success = False
            error_msg = f"HTTP error {response.status} {response.reason}"

        # Handle printout
        if oacommon.checkparam('printout', param):
            printout = param['printout']
            if printout:
                if len(response_body) > 1000:
                    logger.info(f"Response (first 1000 chars):\n{response_body[:1000]}...")
                else:
                    logger.info(f"Response:\n{response_body}")

        # Save to variable (backward compatibility)
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = response_body
            logger.debug(f"Response saved to variable: {saveonvar}")

        logger.info(f"HTTP GET completed, response size: {len(response_body)} bytes")

        # Output data for propagation
        output_data = {
            'status_code': response.status,
            'reason': response.reason,
            'content': response_body,
            'size': len(response_body),
            'headers': dict(response.getheaders()),
            'url': f"http://{host}:{port}{get_path}"
        }

        # If parsed as JSON, add it too
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
    Executes an HTTPS GET request with data propagation

    Args:
        param: dict with:
            - host: hostname or IP (can derive from previous input) - supports {WALLET:key}, {ENV:var}
            - port: HTTPS port - supports {ENV:var}
            - get: request path - supports {WALLET:key}, {ENV:var}
            - verify: (optional) verify SSL certificate, default True
            - printout: (optional) print response
            - saveonvar: (optional) save response to variable
            - headers: (optional) dict with custom headers - supports {WALLET:key} in values (e.g., tokens)
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with response data

    Example YAML:
        # Simple HTTPS GET request
        - name: fetch_secure_api
          module: oa-network
          function: httpsget
          host: "api.example.com"
          port: 443
          get: "/api/v1/data"

        # With Bearer token from wallet
        - name: api_with_token
          module: oa-network
          function: httpsget
          host: "api.github.com"
          port: 443
          get: "/user/repos"
          headers:
            Authorization: "Bearer {WALLET:github_token}"
            Accept: "application/vnd.github.v3+json"

        # Disable SSL verification (not recommended for production)
        - name: insecure_api_call
          module: oa-network
          function: httpsget
          host: "self-signed.example.com"
          port: 443
          get: "/api/data"
          verify: false

        # API with multiple headers from wallet
        - name: complex_api_call
          module: oa-network
          function: httpsget
          host: "{ENV:API_HOST}"
          port: 443
          get: "/api/protected/resource"
          headers:
            Authorization: "Bearer {VAULT:api_secret}"
            X-API-Key: "{WALLET:api_key}"
            User-Agent: "Open-Automator"
          printout: true

        # Call REST API and parse JSON
        - name: fetch_json_data
          module: oa-network
          function: httpsget
          host: "jsonplaceholder.typicode.com"
          port: 443
          get: "/posts/1"
          # Response automatically parsed as JSON if Content-Type is application/json
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
        # If host/port/get not specified, try to derive from input
        if 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'host' not in param and 'host' in prev_input:
                    param['host'] = prev_input['host']
                if 'port' not in param and 'port' in prev_input:
                    param['port'] = prev_input['port']
                if 'url' in prev_input:
                    # Parse complete URL
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
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

        # Custom headers with placeholder support (important for API tokens!)
        headers = {}
        if oacommon.checkparam('headers', param):
            headers_param = param['headers']
            if isinstance(headers_param, dict):
                for key, value in headers_param.items():
                    if isinstance(value, str):
                        # Resolve placeholders in header values (e.g., Bearer {WALLET:api_token})
                        headers[key] = oacommon.get_param({key: value}, key, wallet) or value
                    else:
                        headers[key] = value
                logger.debug(f"Custom headers with placeholders resolved (tokens hidden)")

        url = f"https://{host}:{port}{get_path}"
        logger.info(f"HTTPS GET: {url}")
        logger.debug(f"SSL verify: {verify}")

        # Disable warnings only if verify=False
        if not verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.get(url, verify=verify, headers=headers, timeout=30)

        logger.info(f"HTTPS Status: {response.status_code} {response.reason}")

        response_body = response.content.decode('utf-8', errors='ignore')

        # Try to parse as JSON
        parsed_json = None
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            try:
                parsed_json = response.json()
                logger.debug("Response parsed as JSON")
            except json.JSONDecodeError:
                logger.debug("Failed to parse response as JSON")

        # Consider status >=400 as failure
        if response.status_code >= 400:
            task_success = False
            error_msg = f"HTTPS error {response.status_code} {response.reason}"

        # Handle printout
        if oacommon.checkparam('printout', param):
            printout = param['printout']
            if printout:
                if len(response_body) > 1000:
                    logger.info(f"Response (first 1000 chars):\n{response_body[:1000]}...")
                else:
                    logger.info(f"Response:\n{response_body}")

        # Save to variable (backward compatibility)
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = response_body
            logger.debug(f"Response saved to variable: {saveonvar}")

        logger.info(f"HTTPS GET completed, response size: {len(response_body)} bytes")

        # Output data for propagation
        output_data = {
            'status_code': response.status_code,
            'reason': response.reason,
            'content': response_body,
            'size': len(response_body),
            'headers': dict(response.headers),
            'url': url,
            'elapsed_ms': response.elapsed.total_seconds() * 1000
        }

        # If parsed as JSON, add it too
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
    Executes an HTTP POST request with data propagation

    Args:
        param: dict with:
            - host: hostname or IP - supports {WALLET:key}, {ENV:var}
            - port: HTTP port - supports {ENV:var}
            - path: request path - supports {WALLET:key}, {ENV:var}
            - data: data to send (can come from previous input) - supports {WALLET:key}
            - headers: (optional) dict with custom headers - supports {WALLET:key} in values
            - content_type: (optional) default 'application/json'
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with response data

    Example YAML:
        # Simple POST with JSON data
        - name: create_user
          module: oa-network
          function: httppost
          host: "api.example.com"
          port: 80
          path: "/api/users"
          data:
            name: "John Doe"
            email: "john@example.com"
            age: 30

        # POST with data from wallet
        - name: send_credentials
          module: oa-network
          function: httppost
          host: "{ENV:API_HOST}"
          port: 80
          path: "/api/login"
          data:
            username: "{WALLET:api_username}"
            password: "{VAULT:api_password}"

        # POST with custom headers
        - name: api_post_with_headers
          module: oa-network
          function: httppost
          host: "api.example.com"
          port: 80
          path: "/api/data"
          headers:
            Authorization: "Bearer {WALLET:token}"
            X-Custom-Header: "value"
          data:
            field1: "value1"
            field2: "value2"

        # POST data from previous task
        - name: submit_processed_data
          module: oa-network
          function: httppost
          host: "api.example.com"
          port: 80
          path: "/api/submit"
          # data automatically taken from previous task output

        # POST with different content type
        - name: post_xml_data
          module: oa-network
          function: httppost
          host: "api.example.com"
          port: 80
          path: "/api/xml"
          content_type: "application/xml"
          data: "<xml>data</xml>"
    """
    func_name = myself()
    logger.info("Executing HTTP POST request")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Determine data to send
        post_data = None

        # 1. If there's explicit 'data' (with placeholder support)
        if 'data' in param:
            data_param = param['data']
            # If it's a string, resolve placeholders
            if isinstance(data_param, str):
                post_data = oacommon.get_param(param, 'data', wallet) or data_param
            # If it's dict/list, use as is (but might have placeholders in values)
            elif isinstance(data_param, dict):
                # Recursively resolve placeholders in dict
                post_data = {}
                for key, value in data_param.items():
                    if isinstance(value, str):
                        post_data[key] = oacommon.get_param({key: value}, key, wallet) or value
                    else:
                        post_data[key] = value
            else:
                post_data = data_param
        # 2. Otherwise use input from previous task
        elif 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                # If there's 'json' field, use it
                if 'json' in prev_input:
                    post_data = prev_input['json']
                # Otherwise use all input
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

        # Use get_param to support placeholders
        host = oacommon.get_param(param, 'host', wallet) or gdict.get('host')
        port_str = oacommon.get_param(param, 'port', wallet) or gdict.get('port')
        port = int(port_str)
        path = oacommon.get_param(param, 'path', wallet) or gdict.get('path')

        # Headers with placeholder support
        content_type = param.get('content_type', 'application/json')
        headers = param.get('headers', {})

        # Resolve placeholders in headers
        if isinstance(headers, dict):
            resolved_headers = {}
            for key, value in headers.items():
                if isinstance(value, str):
                    resolved_headers[key] = oacommon.get_param({key: value}, key, wallet) or value
                else:
                    resolved_headers[key] = value
            headers = resolved_headers

        headers['Content-Type'] = content_type

        # If data is dict/list, convert to JSON
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

        # Try to parse as JSON
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
    Executes an HTTPS POST request with data propagation

    Args:
        param: dict with:
            - host: hostname or IP - supports {WALLET:key}, {ENV:var}
            - port: HTTPS port - supports {ENV:var}
            - path: request path - supports {WALLET:key}, {ENV:var}
            - data: data to send (can come from previous input) - supports {WALLET:key}
            - headers: (optional) dict with custom headers - supports {WALLET:key} in values (e.g., API key)
            - content_type: (optional) default 'application/json'
            - verify: (optional) verify SSL certificate, default True
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with response data

    Example YAML:
        # Simple HTTPS POST
        - name: create_secure_resource
          module: oa-network
          function: httpspost
          host: "api.example.com"
          port: 443
          path: "/api/v1/resources"
          data:
            name: "New Resource"
            type: "important"

        # POST with API key from vault
        - name: secure_api_post
          module: oa-network
          function: httpspost
          host: "api.github.com"
          port: 443
          path: "/repos/owner/repo/issues"
          headers:
            Authorization: "Bearer {VAULT:github_token}"
            Accept: "application/vnd.github.v3+json"
          data:
            title: "Bug report"
            body: "Description of the bug"

        # POST with multiple credentials from wallet
        - name: enterprise_api_call
          module: oa-network
          function: httpspost
          host: "{ENV:ENTERPRISE_API}"
          port: 443
          path: "/api/submit"
          headers:
            X-API-Key: "{WALLET:api_key}"
            X-Client-ID: "{WALLET:client_id}"
            Authorization: "Bearer {VAULT:access_token}"
          data:
            user_id: "{WALLET:user_id}"
            action: "create"
            payload:
              field1: "value1"

        # POST data from previous task (e.g., after JSON transformation)
        - name: submit_transformed_data
          module: oa-network
          function: httpspost
          host: "api.example.com"
          port: 443
          path: "/api/bulk"
          # data automatically from previous jsontransform task

        # Disable SSL verification for self-signed cert
        - name: internal_api_post
          module: oa-network
          function: httpspost
          host: "internal-api.company.local"
          port: 443
          path: "/api/data"
          verify: false
          data:
            internal_data: "sensitive"
    """
    func_name = myself()
    logger.info("Executing HTTPS POST request")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Determine data to send (same mechanism as httppost)
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

        # Use get_param to support placeholders
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

        # Headers with placeholder support (important for API keys!)
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

        # Convert data
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
