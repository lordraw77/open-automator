"""
Open-Automator IO Module

Manages file and directory operations (copy, zip, read, write) with data propagation
Support for wallet, placeholder {WALLET:key}, {ENV:var} and {VAULT:key}
"""

import oacommon
import os
import shutil
import zipfile
import glob
import json
import re
from jinja2 import Environment, BaseLoader
import inspect
import logging
from logger_config import AutomatorLogger

# Logger for this module
logger = AutomatorLogger.get_logger('oa-io')

gdict = {}
myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdict_param):
    """Sets the global dictionary"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

@oacommon.trace
def copy(self, param):
    """
    Copies files or directories with data propagation

    Args:
        param: dict with:
            - srcpath: source path - supports {WALLET:key}, {ENV:var}
            - dstpath: destination path - supports {WALLET:key}, {ENV:var}
            - recursive: True for directories, False for single file
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with copy information

    Example YAML:
        # Copy single file
        - name: backup_config
          module: oa-io
          function: copy
          srcpath: "/etc/app/config.yaml"
          dstpath: "/backup/config.yaml"
          recursive: false

        # Copy entire directory recursively
        - name: backup_data_folder
          module: oa-io
          function: copy
          srcpath: "{ENV:DATA_DIR}"
          dstpath: "/backup/data"
          recursive: true

        # Copy from previous task output
        - name: copy_generated_file
          module: oa-io
          function: copy
          # srcpath from previous task 'filepath' field
          dstpath: "/output/result.txt"
          recursive: false
    """
    func_name = myself()
    logger.info("Copying file/directory")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = ['srcpath', 'dstpath', 'recursive']

    try:
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        srcpath = oacommon.get_param(param, 'srcpath', wallet) or gdict.get('srcpath')
        dstpath = oacommon.get_param(param, 'dstpath', wallet) or gdict.get('dstpath')
        recursive = gdict['recursive']

        logger.info(f"Copy: {srcpath} -> {dstpath} (recursive: {recursive})")

        if not os.path.exists(srcpath):
            raise FileNotFoundError(f"Source path not found: {srcpath}")

        if recursive:
            logger.debug("Recursive directory copy")
            shutil.copytree(srcpath, dstpath, dirs_exist_ok=True)
            # Count copied files
            file_count = sum(len(files) for _, _, files in os.walk(dstpath))
        else:
            logger.debug("Single file copy")
            shutil.copy(srcpath, dstpath)
            file_count = 1

        logger.info("Copy completed successfully")

        # Output data for propagation
        output_data = {
            'srcpath': srcpath,
            'dstpath': dstpath,
            'recursive': recursive,
            'files_copied': file_count
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Copy operation failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    # Return tuple (success, output)
    return task_success, output_data

def zipdir(paths, zipfilter, ziph, wallet=None):
    """
    Helper function to compress directories with placeholder support.

    Args:
        paths: list of paths to compress
        zipfilter: file filter
        ziph: ZIP file handle
        wallet: wallet instance to resolve placeholders

    Note: Internal helper function, not a task
    and doesn't handle task_id / task_store.
    """
    for path in paths:
        # Resolve placeholder in path if wallet present
        if wallet and isinstance(path, str) and ('{WALLET:' in path or '{ENV:' in path or '{VAULT:' in path):
            from wallet import resolve_placeholders
            path = resolve_placeholders(path, wallet)
        else:
            path = oacommon.effify(path)

        logger.debug(f"Processing path for ZIP: {path}")

        for root, dirs, files in os.walk(path):
            for file in files:
                if '*' in zipfilter or zipfilter in file:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, os.path.join(path, '..'))
                    ziph.write(filepath, arcname)
                    logger.debug(f"Added to ZIP: {arcname}")

@oacommon.trace
def zip(self, param):
    """
    Creates a ZIP archive with data propagation

    Args:
        param: dict with:
            - zipfilename: ZIP file name - supports {WALLET:key}, {ENV:var}
            - pathtozip: path to compress (can use input from previous task) - supports {ENV:var}
            - zipfilter: file filter (e.g., "*.txt" or "*")
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with ZIP info

    Example YAML:
        # Create ZIP of directory with all files
        - name: create_backup_zip
          module: oa-io
          function: zip
          zipfilename: "/backup/data.zip"
          pathtozip:
            - "/workspace/project"
          zipfilter: "*"

        # Create ZIP with filter (only .txt files)
        - name: zip_text_files
          module: oa-io
          function: zip
          zipfilename: "{ENV:OUTPUT_DIR}/texts.zip"
          pathtozip:
            - "/documents"
          zipfilter: "*.txt"

        # ZIP from previous copy task output
        - name: zip_copied_files
          module: oa-io
          function: zip
          zipfilename: "/backup/copied.zip"
          # pathtozip from previous task 'dstpath'
          zipfilter: "*"

        # ZIP multiple directories
        - name: zip_multiple_dirs
          module: oa-io
          function: zip
          zipfilename: "/backup/combined.zip"
          pathtozip:
            - "/data/folder1"
            - "/data/folder2"
            - "{WALLET:custom_path}"
          zipfilter: "*"
    """
    func_name = myself()
    logger.info("Creating ZIP archive")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = ['zipfilename', 'pathtozip', 'zipfilter']

    try:
        # If pathtozip not specified, use input from previous task
        if 'pathtozip' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'dstpath' in prev_input:
                param['pathtozip'] = [prev_input['dstpath']]
                logger.info(f"Using path from previous task: {param['pathtozip']}")

        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        zipfilename = oacommon.get_param(param, 'zipfilename', wallet) or gdict.get('zipfilename')
        pathtozip = gdict['pathtozip']
        zipfilter = oacommon.get_param(param, 'zipfilter', wallet) or gdict.get('zipfilter')

        logger.info(f"ZIP file: {zipfilename}")
        logger.debug(f"Paths to compress: {pathtozip}")
        logger.debug(f"Filter: {zipfilter}")

        with zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipdir(pathtozip, zipfilter, zipf, wallet)

        zip_size = os.path.getsize(zipfilename)
        logger.info(f"ZIP archive created successfully: {zipfilename} ({zip_size} bytes)")

        # Output data for propagation
        output_data = {
            'zipfilename': zipfilename,
            'zip_size': zip_size,
            'paths_compressed': pathtozip,
            'filter': zipfilter
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"ZIP creation failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def unzip(self, param):
    """
    Extracts a ZIP archive with data propagation

    Args:
        param: dict with:
            - zipfilename: ZIP file to extract (can use input from previous task) - supports {ENV:var}
            - pathwhereunzip: destination directory - supports {ENV:var}
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with extraction info

    Example YAML:
        # Extract ZIP archive
        - name: extract_backup
          module: oa-io
          function: unzip
          zipfilename: "/backup/data.zip"
          pathwhereunzip: "/restore/data"

        # Extract from environment path
        - name: extract_download
          module: oa-io
          function: unzip
          zipfilename: "{ENV:DOWNLOAD_DIR}/archive.zip"
          pathwhereunzip: "{ENV:EXTRACT_DIR}"

        # Extract ZIP from previous zip task
        - name: extract_created_zip
          module: oa-io
          function: unzip
          # zipfilename from previous task
          pathwhereunzip: "/tmp/extracted"
    """
    func_name = myself()
    logger.info("Extracting ZIP archive")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = ['zipfilename', 'pathwhereunzip']

    try:
        # If zipfilename not specified, use input from previous task
        if 'zipfilename' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'zipfilename' in prev_input:
                param['zipfilename'] = prev_input['zipfilename']
                logger.info(f"Using ZIP from previous task: {param['zipfilename']}")

        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        zipfilename = oacommon.get_param(param, 'zipfilename', wallet) or gdict.get('zipfilename')
        pathwhereunzip = oacommon.get_param(param, 'pathwhereunzip', wallet) or gdict.get('pathwhereunzip')

        logger.info(f"Extracting: {zipfilename} -> {pathwhereunzip}")

        if not os.path.exists(zipfilename):
            raise FileNotFoundError(f"ZIP file not found: {zipfilename}")

        os.makedirs(pathwhereunzip, exist_ok=True)

        with zipfile.ZipFile(zipfilename, 'r', zipfile.ZIP_DEFLATED) as zipf:
            file_count = len(zipf.namelist())
            logger.debug(f"Extracting {file_count} files")
            zipf.extractall(pathwhereunzip)

        logger.info(f"ZIP extraction completed: {file_count} files extracted")

        # Output data for propagation
        output_data = {
            'zipfilename': zipfilename,
            'extract_path': pathwhereunzip,
            'files_extracted': file_count
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"ZIP extraction failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def readfile(self, param):
    """
    Reads file content with data propagation

    Args:
        param: dict with:
            - filename: file to read (can use input from previous task) - supports {WALLET:key}, {ENV:var}
            - varname: (optional) if you only want to return content
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, file_content) - file content is propagated

    Example YAML:
        # Read config file
        - name: read_config
          module: oa-io
          function: readfile
          filename: "/etc/app/config.yaml"

        # Read from environment path
        - name: read_log
          module: oa-io
          function: readfile
          filename: "{ENV:LOG_FILE}"

        # Read file from previous task
        - name: read_generated_file
          module: oa-io
          function: readfile
          # filename from previous writefile task

        # Read and save to variable (legacy)
        - name: read_template
          module: oa-io
          function: readfile
          filename: "/templates/email.html"
          varname: email_template
    """
    func_name = myself()
    logger.info("Reading file")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # If filename not specified, use input from previous task
        if 'filename' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                # Look for various possible fields
                if 'dstpath' in prev_input:
                    param['filename'] = prev_input['dstpath']
                elif 'filepath' in prev_input:
                    param['filename'] = prev_input['filepath']
                elif 'filename' in prev_input:
                    param['filename'] = prev_input['filename']
                logger.info(f"Using filename from previous task: {param.get('filename')}")

        if not oacommon.checkandloadparam(self, myself, 'filename', param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        filename = oacommon.get_param(param, 'filename', wallet) or gdict.get('filename')
        varname = gdict.get('varname')  # Optional

        logger.info(f"Reading file: {filename}")

        content = oacommon.readfile(filename)

        # Save in gdict if varname is specified (backward compatibility)
        if varname:
            gdict[varname] = content
            logger.debug(f"Content saved to variable: {varname}")

        logger.info(f"File read successfully: {len(content)} characters")

        # Output data for propagation - returns content
        output_data = {
            'filename': filename,
            'content': content,
            'size': len(content)
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Failed to read file: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def writefile(self, param):
    """
    Writes content to a file with data propagation

    Args:
        param: dict with:
            - filename: file to write - supports {WALLET:key}, {ENV:var}
            - varname: (optional if there's input from previous task)
            - content: (optional, alternative to varname) - supports {WALLET:key}, {ENV:var}
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with file info

    Example YAML:
        # Write static content
        - name: write_config
          module: oa-io
          function: writefile
          filename: "/tmp/config.txt"
          content: "server_url=https://api.example.com"

        # Write with placeholder
        - name: write_dynamic
          module: oa-io
          function: writefile
          filename: "{ENV:OUTPUT_DIR}/result.txt"
          content: "Result: {WALLET:result_value}"

        # Write content from previous task
        - name: write_processed_data
          module: oa-io
          function: writefile
          filename: "/output/processed.json"
          # content from previous task (e.g., from readfile or API call)

        # Write from variable (legacy)
        - name: write_from_var
          module: oa-io
          function: writefile
          filename: "/output/data.txt"
          varname: my_data_variable
    """
    func_name = myself()
    logger.info("Writing file")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Determine content to write
        content = None

        # 1. If there's explicit 'content', use it (with placeholder support)
        if 'content' in param:
            content = oacommon.get_param(param, 'content', wallet)
            if content is None:
                content = str(param['content'])
            logger.debug("Using explicit 'content' parameter")

        # 2. If there's input from previous task, use it
        elif 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'content' in prev_input:
                content = prev_input['content']
                logger.info("Using content from previous task")
            elif isinstance(prev_input, str):
                content = prev_input
                logger.info("Using string input from previous task")
            elif isinstance(prev_input, (dict, list)):
                content = json.dumps(prev_input, indent=2)
                logger.info("Converting dict/list input to JSON")

        # 3. Otherwise use varname from gdict (backward compatibility)
        elif 'varname' in param:
            if not oacommon.checkandloadparam(self, myself, 'varname', param=param):
                raise ValueError("varname not found in gdict")
            varname = gdict['varname']
            if varname not in gdict:
                raise ValueError(f"Variable '{varname}' not found in gdict")
            content = str(gdict[varname])
            logger.debug(f"Using content from gdict variable: {varname}")

        if content is None:
            raise ValueError("No content to write (provide 'content', 'varname', or pipe from previous task)")

        if not oacommon.checkandloadparam(self, myself, 'filename', param=param):
            raise ValueError(f"Missing required parameter 'filename' for {func_name}")

        # Use get_param to support placeholders
        filename = oacommon.get_param(param, 'filename', wallet) or gdict.get('filename')

        logger.info(f"Writing to file: {filename}")

        oacommon.writefile(filename, content)

        logger.info(f"File written successfully: {len(content)} characters")

        # Output data for propagation
        output_data = {
            'filename': filename,
            'bytes_written': len(content),
            'filepath': os.path.abspath(filename)
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Failed to write file: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def replace(self, param):
    """
    Replaces text in a variable with data propagation

    Args:
        param: dict with:
            - varname: (optional if there's input)
            - leftvalue: text to search for
            - rightvalue: replacement text
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, modified_content)

    Example YAML:
        # Replace in static content
        - name: replace_placeholder
          module: oa-io
          function: replace
          varname: email_template
          leftvalue: "{{NAME}}"
          rightvalue: "John Doe"

        # Replace from previous task content
        - name: replace_in_content
          module: oa-io
          function: replace
          # content from previous readfile task
          leftvalue: "localhost"
          rightvalue: "production.example.com"

        # Chain replacements
        - name: replace_url
          module: oa-io
          function: replace
          leftvalue: "http://"
          rightvalue: "https://"

        - name: replace_port
          module: oa-io
          function: replace
          # content from previous replace task
          leftvalue: ":8080"
          rightvalue: ":443"
    """
    func_name = myself()
    logger.info("Replacing text in variable")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = ['leftvalue', 'rightvalue']

    try:
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # leftvalue and rightvalue might contain placeholders
        leftvalue = oacommon.get_param(param, 'leftvalue', wallet) or gdict.get('leftvalue')
        rightvalue = oacommon.get_param(param, 'rightvalue', wallet) or gdict.get('rightvalue')

        # Determine content to operate on
        original = None

        # 1. If there's input from previous task
        if 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'content' in prev_input:
                original = prev_input['content']
                logger.info("Using content from previous task")
            elif isinstance(prev_input, str):
                original = prev_input

        # 2. Otherwise use varname (backward compatibility)
        if original is None:
            if not oacommon.checkandloadparam(self, myself, 'varname', param=param):
                raise ValueError("No input data and varname not specified")
            varname = gdict['varname']
            if varname not in gdict:
                raise ValueError(f"Variable '{varname}' not found")
            original = gdict[varname]

        logger.debug(f"Replace: '{leftvalue}' -> '{rightvalue}'")

        modified = str(original).replace(leftvalue, rightvalue)

        # Save in gdict if varname is specified (backward compatibility)
        if 'varname' in gdict:
            gdict[gdict['varname']] = modified

        occurrences = str(original).count(leftvalue)
        logger.info(f"Replaced {occurrences} occurrence(s)")

        # Output data for propagation
        output_data = {
            'content': modified,
            'occurrences': occurrences,
            'leftvalue': leftvalue,
            'rightvalue': rightvalue
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Text replacement failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data

@oacommon.trace
def loadvarfromjson(self, param):
    """
    Loads variables from a JSON file into gdict with data propagation

    Args:
        param: dict with:
            - filename: JSON file (can use input from previous task) - supports {WALLET:key}, {ENV:var}
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, json_data) - returns parsed JSON data

    Example YAML:
        # Load config from JSON
        - name: load_config
          module: oa-io
          function: loadvarfromjson
          filename: "/etc/app/config.json"

        # Load from environment path
        - name: load_settings
          module: oa-io
          function: loadvarfromjson
          filename: "{ENV:CONFIG_DIR}/settings.json"

        # Load JSON from previous task
        - name: load_generated_json
          module: oa-io
          function: loadvarfromjson
          # filename from previous writefile task

        # All JSON keys are loaded as gdict variables
        # Example JSON: {"db_host": "localhost", "db_port": 5432}
        # After loadvarfromjson, you can use {db_host} and {db_port}
    """
    func_name = myself()
    logger.info("Loading variables from JSON file")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # If filename not specified, use input from previous task
        if 'filename' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'filepath' in prev_input:
                    param['filename'] = prev_input['filepath']
                elif 'filename' in prev_input:
                    param['filename'] = prev_input['filename']
                logger.info(f"Using filename from previous task: {param.get('filename')}")

        if not oacommon.checkandloadparam(self, myself, 'filename', param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        filename = oacommon.get_param(param, 'filename', wallet) or gdict.get('filename')

        logger.info(f"Loading JSON: {filename}")

        if not os.path.exists(filename):
            raise FileNotFoundError(f"JSON file not found: {filename}")

        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()

        jdata = json.loads(data)

        var_count = 0
        for key in jdata.keys():
            gdict[key] = jdata.get(key)
            var_count += 1
            logger.debug(f"Loaded variable: {key}")

        logger.info(f"Loaded {var_count} variables from JSON")

        # Output data for propagation - returns JSON data
        output_data = jdata

    except json.JSONDecodeError as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Invalid JSON in file {filename}: {e}")
    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Failed to load JSON file: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data