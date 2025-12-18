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

# Logger per questo modulo
logger = AutomatorLogger.get_logger('oa-io')

gdict = {}
myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdict_param):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

@oacommon.trace
def copy(self, param):
    """
    Copia file o directory con data propagation

    Args:
        param: dict con:
            - srcpath
            - dstpath
            - recursive
            - input (opzionale, da task precedente)
            - workflow_context (opzionale)
            - task_id (opzionale)
            - task_store (opzionale)
    
    Returns:
        tuple: (success, output_dict) con informazioni sulla copia
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

        srcpath = oacommon.effify(gdict['srcpath'])
        dstpath = oacommon.effify(gdict['dstpath'])
        recursive = gdict['recursive']

        logger.info(f"Copy: {srcpath} -> {dstpath} (recursive: {recursive})")

        if not os.path.exists(srcpath):
            raise FileNotFoundError(f"Source path not found: {srcpath}")

        if recursive:
            logger.debug("Recursive directory copy")
            shutil.copytree(srcpath, dstpath, dirs_exist_ok=True)
            # Conta file copiati
            file_count = sum(len(files) for _, _, files in os.walk(dstpath))
        else:
            logger.debug("Single file copy")
            shutil.copy(srcpath, dstpath)
            file_count = 1

        logger.info("Copy completed successfully")
        
        # Output data per propagation
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

    # Ritorna tupla (success, output)
    return task_success, output_data


def zipdir(paths, zipfilter, ziph):
    """
    Helper function per comprimere directory.
    
    Nota: funzione di supporto interna, non è un task
    e non gestisce task_id / task_store.
    """
    for path in paths:
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
    Crea un archivio ZIP con data propagation

    Args:
        param: dict con:
            - zipfilename
            - pathtozip (può usare input da task precedente)
            - zipfilter
            - input (opzionale, da task precedente)
            - workflow_context (opzionale)
            - task_id (opzionale)
            - task_store (opzionale)
    
    Returns:
        tuple: (success, output_dict) con info sul ZIP creato
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
        # Se pathtozip non è specificato, usa l'input dal task precedente
        if 'pathtozip' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'dstpath' in prev_input:
                param['pathtozip'] = [prev_input['dstpath']]
                logger.info(f"Using path from previous task: {param['pathtozip']}")
        
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        zipfilename = oacommon.effify(gdict['zipfilename'])
        pathtozip = gdict['pathtozip']
        zipfilter = gdict['zipfilter']

        logger.info(f"ZIP file: {zipfilename}")
        logger.debug(f"Paths to compress: {pathtozip}")
        logger.debug(f"Filter: {zipfilter}")

        with zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipdir(pathtozip, zipfilter, zipf)

        zip_size = os.path.getsize(zipfilename)
        logger.info(f"ZIP archive created successfully: {zipfilename} ({zip_size} bytes)")
        
        # Output data per propagation
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
    Estrae un archivio ZIP con data propagation

    Args:
        param: dict con:
            - zipfilename (può usare input da task precedente)
            - pathwhereunzip
            - input (opzionale, da task precedente)
            - workflow_context (opzionale)
            - task_id (opzionale)
            - task_store (opzionale)
    
    Returns:
        tuple: (success, output_dict) con info sull'estrazione
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
        # Se zipfilename non è specificato, usa l'input dal task precedente
        if 'zipfilename' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'zipfilename' in prev_input:
                param['zipfilename'] = prev_input['zipfilename']
                logger.info(f"Using ZIP from previous task: {param['zipfilename']}")
        
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        zipfilename = oacommon.effify(gdict['zipfilename'])
        pathwhereunzip = oacommon.effify(gdict['pathwhereunzip'])

        logger.info(f"Extracting: {zipfilename} -> {pathwhereunzip}")

        if not os.path.exists(zipfilename):
            raise FileNotFoundError(f"ZIP file not found: {zipfilename}")

        os.makedirs(pathwhereunzip, exist_ok=True)

        with zipfile.ZipFile(zipfilename, 'r', zipfile.ZIP_DEFLATED) as zipf:
            file_count = len(zipf.namelist())
            logger.debug(f"Extracting {file_count} files")
            zipf.extractall(pathwhereunzip)

        logger.info(f"ZIP extraction completed: {file_count} files extracted")
        
        # Output data per propagation
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
    Legge il contenuto di un file con data propagation

    Args:
        param: dict con:
            - filename (può usare input da task precedente)
            - varname (opzionale se si vuole solo ritornare il contenuto)
            - input (opzionale, da task precedente)
            - workflow_context (opzionale)
            - task_id (opzionale)
            - task_store (opzionale)
    
    Returns:
        tuple: (success, file_content) - il contenuto del file viene propagato
    """
    func_name = myself()
    logger.info("Reading file")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se filename non è specificato, usa l'input dal task precedente
        if 'filename' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                # Cerca vari campi possibili
                if 'dstpath' in prev_input:
                    param['filename'] = prev_input['dstpath']
                elif 'filepath' in prev_input:
                    param['filename'] = prev_input['filepath']
                logger.info(f"Using filename from previous task: {param.get('filename')}")
        
        if not oacommon.checkandloadparam(self, myself, 'filename', param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        filename = oacommon.effify(gdict['filename'])
        varname = gdict.get('varname')  # Opzionale

        logger.info(f"Reading file: {filename}")

        content = oacommon.readfile(filename)
        
        # Salva in gdict se varname è specificato (retrocompatibilità)
        if varname:
            gdict[varname] = content
            logger.debug(f"Content saved to variable: {varname}")

        logger.info(f"File read successfully: {len(content)} characters")
        
        # Output data per propagation - ritorna il contenuto
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
    Scrive contenuto in un file con data propagation

    Args:
        param: dict con:
            - filename
            - varname (opzionale se c'è input dal task precedente)
            - content (opzionale, alternativa a varname)
            - input (opzionale, da task precedente)
            - workflow_context (opzionale)
            - task_id (opzionale)
            - task_store (opzionale)
    
    Returns:
        tuple: (success, output_dict) con info sul file scritto
    """
    func_name = myself()
    logger.info("Writing file")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Determina il contenuto da scrivere
        content = None
        
        # 1. Se c'è 'content' esplicito, usalo
        if 'content' in param:
            content = str(param['content'])
            logger.debug("Using explicit 'content' parameter")
        
        # 2. Se c'è input dal task precedente, usalo
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
        
        # 3. Altrimenti usa varname da gdict (retrocompatibilità)
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

        filename = oacommon.effify(gdict['filename'])

        logger.info(f"Writing to file: {filename}")

        oacommon.writefile(filename, content)

        logger.info(f"File written successfully: {len(content)} characters")
        
        # Output data per propagation
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
    Sostituisce testo in una variabile con data propagation

    Args:
        param: dict con:
            - varname (opzionale se c'è input)
            - leftvalue
            - rightvalue
            - input (opzionale, da task precedente)
            - workflow_context (opzionale)
            - task_id (opzionale)
            - task_store (opzionale)
    
    Returns:
        tuple: (success, modified_content)
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

        leftvalue = gdict['leftvalue']
        rightvalue = gdict['rightvalue']

        # Determina il contenuto su cui operare
        original = None
        
        # 1. Se c'è input dal task precedente
        if 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'content' in prev_input:
                original = prev_input['content']
                logger.info("Using content from previous task")
            elif isinstance(prev_input, str):
                original = prev_input
        
        # 2. Altrimenti usa varname (retrocompatibilità)
        if original is None:
            if not oacommon.checkandloadparam(self, myself, 'varname', param=param):
                raise ValueError("No input data and varname not specified")
            varname = gdict['varname']
            if varname not in gdict:
                raise ValueError(f"Variable '{varname}' not found")
            original = gdict[varname]

        logger.debug(f"Replace: '{leftvalue}' -> '{rightvalue}'")

        modified = str(original).replace(leftvalue, rightvalue)
        
        # Salva in gdict se varname è specificato (retrocompatibilità)
        if 'varname' in gdict:
            gdict[gdict['varname']] = modified

        occurrences = str(original).count(leftvalue)
        logger.info(f"Replaced {occurrences} occurrence(s)")
        
        # Output data per propagation
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
    Carica variabili da un file JSON nel gdict con data propagation

    Args:
        param: dict con:
            - filename (può usare input da task precedente)
            - input (opzionale, da task precedente)
            - workflow_context (opzionale)
            - task_id (opzionale)
            - task_store (opzionale)
    
    Returns:
        tuple: (success, json_data) - ritorna i dati JSON parsati
    """
    func_name = myself()
    logger.info("Loading variables from JSON file")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se filename non è specificato, usa l'input dal task precedente
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

        filename = oacommon.effify(gdict['filename'])

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
        
        # Output data per propagation - ritorna i dati JSON
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
