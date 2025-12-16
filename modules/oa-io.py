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
    Copia file o directory

    Args:
        param: dict con:
            - srcpath: percorso sorgente
            - dstpath: percorso destinazione
            - recursive: True per directory ricorsive
    """
    func_name = myself()
    logger.info("Copying file/directory")

    required_params = ['srcpath', 'dstpath', 'recursive']

    if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
        raise ValueError(f"Missing required parameters for {func_name}")

    srcpath = oacommon.effify(gdict['srcpath'])
    dstpath = oacommon.effify(gdict['dstpath'])
    recursive = gdict['recursive']

    logger.info(f"Copy: {srcpath} -> {dstpath} (recursive: {recursive})")

    try:
        if not os.path.exists(srcpath):
            raise FileNotFoundError(f"Source path not found: {srcpath}")

        if recursive:
            logger.debug("Recursive directory copy")
            shutil.copytree(srcpath, dstpath, dirs_exist_ok=True)
        else:
            logger.debug("Single file copy")
            shutil.copy(srcpath, dstpath)

        logger.info(f"Copy completed successfully")

    except Exception as e:
        logger.error(f"Copy operation failed: {e}", exc_info=True)
        raise


def zipdir(paths, zipfilter, ziph):
    """Helper function per comprimere directory"""
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
    Crea un archivio ZIP

    Args:
        param: dict con:
            - zipfilename: nome file ZIP da creare
            - pathtozip: lista di percorsi da comprimere
            - zipfilter: filtro file (es. "*.txt" o "*")
    """
    func_name = myself()
    logger.info("Creating ZIP archive")

    required_params = ['zipfilename', 'pathtozip', 'zipfilter']

    if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
        raise ValueError(f"Missing required parameters for {func_name}")

    zipfilename = oacommon.effify(gdict['zipfilename'])
    pathtozip = gdict['pathtozip']
    zipfilter = gdict['zipfilter']

    logger.info(f"ZIP file: {zipfilename}")
    logger.debug(f"Paths to compress: {pathtozip}")
    logger.debug(f"Filter: {zipfilter}")

    try:
        with zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipdir(pathtozip, zipfilter, zipf)

        zip_size = os.path.getsize(zipfilename)
        logger.info(f"ZIP archive created successfully: {zipfilename} ({zip_size} bytes)")

    except Exception as e:
        logger.error(f"ZIP creation failed: {e}", exc_info=True)
        raise


@oacommon.trace
def unzip(self, param):
    """
    Estrae un archivio ZIP

    Args:
        param: dict con:
            - zipfilename: file ZIP da estrarre
            - pathwhereunzip: directory di destinazione
    """
    func_name = myself()
    logger.info("Extracting ZIP archive")

    required_params = ['zipfilename', 'pathwhereunzip']

    if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
        raise ValueError(f"Missing required parameters for {func_name}")

    zipfilename = oacommon.effify(gdict['zipfilename'])
    pathwhereunzip = oacommon.effify(gdict['pathwhereunzip'])

    logger.info(f"Extracting: {zipfilename} -> {pathwhereunzip}")

    try:
        if not os.path.exists(zipfilename):
            raise FileNotFoundError(f"ZIP file not found: {zipfilename}")

        os.makedirs(pathwhereunzip, exist_ok=True)

        with zipfile.ZipFile(zipfilename, 'r', zipfile.ZIP_DEFLATED) as zipf:
            file_count = len(zipf.namelist())
            logger.debug(f"Extracting {file_count} files")
            zipf.extractall(pathwhereunzip)

        logger.info(f"ZIP extraction completed: {file_count} files extracted")

    except Exception as e:
        logger.error(f"ZIP extraction failed: {e}", exc_info=True)
        raise


@oacommon.trace
def readfile(self, param):
    """
    Legge il contenuto di un file

    Args:
        param: dict con:
            - filename: path del file
            - varname: nome variabile dove salvare il contenuto
    """
    func_name = myself()
    logger.info("Reading file")

    required_params = ['filename', 'varname']

    if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
        raise ValueError(f"Missing required parameters for {func_name}")

    filename = oacommon.effify(gdict['filename'])
    varname = gdict['varname']

    logger.info(f"Reading file: {filename}")

    try:
        content = oacommon.readfile(filename)
        gdict[varname] = content

        logger.info(f"File read successfully: {len(content)} characters")
        logger.debug(f"Content saved to variable: {varname}")

    except Exception as e:
        logger.error(f"Failed to read file {filename}: {e}", exc_info=True)
        raise


@oacommon.trace
def writefile(self, param):
    """
    Scrive contenuto in un file

    Args:
        param: dict con:
            - filename: path del file
            - varname: nome variabile con il contenuto da scrivere
    """
    func_name = myself()
    logger.info("Writing file")

    required_params = ['filename', 'varname']

    if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
        raise ValueError(f"Missing required parameters for {func_name}")

    filename = oacommon.effify(gdict['filename'])
    varname = gdict['varname']

    logger.info(f"Writing to file: {filename}")

    try:
        if varname not in gdict:
            raise ValueError(f"Variable '{varname}' not found in gdict")

        content = str(gdict[varname])
        oacommon.writefile(filename, content)

        logger.info(f"File written successfully: {len(content)} characters")

    except Exception as e:
        logger.error(f"Failed to write file {filename}: {e}", exc_info=True)
        raise


@oacommon.trace
def replace(self, param):
    """
    Sostituisce testo in una variabile

    Args:
        param: dict con:
            - varname: nome variabile da modificare
            - leftvalue: testo da cercare
            - rightvalue: testo sostitutivo
    """
    func_name = myself()
    logger.info("Replacing text in variable")

    required_params = ['varname', 'leftvalue', 'rightvalue']

    if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
        raise ValueError(f"Missing required parameters for {func_name}")

    varname = gdict['varname']
    leftvalue = gdict['leftvalue']
    rightvalue = gdict['rightvalue']

    logger.debug(f"Variable: {varname}, Replace: '{leftvalue}' -> '{rightvalue}'")

    try:
        if varname not in gdict:
            raise ValueError(f"Variable '{varname}' not found")

        original = gdict[varname]
        modified = str(original).replace(leftvalue, rightvalue)
        gdict[varname] = modified

        occurrences = original.count(leftvalue)
        logger.info(f"Replaced {occurrences} occurrence(s) in variable '{varname}'")

    except Exception as e:
        logger.error(f"Text replacement failed: {e}", exc_info=True)
        raise


@oacommon.trace
def loadvarfromjson(self, param):
    """
    Carica variabili da un file JSON nel gdict

    Args:
        param: dict con:
            - filename: path del file JSON
    """
    func_name = myself()
    logger.info("Loading variables from JSON file")

    if not oacommon.checkandloadparam(self, myself, 'filename', param=param):
        raise ValueError(f"Missing required parameters for {func_name}")

    filename = oacommon.effify(gdict['filename'])

    logger.info(f"Loading JSON: {filename}")

    try:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"JSON file not found: {filename}")

        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()

        jdata = json.loads(data)

        # Carica nel gdict
        var_count = 0
        for key in jdata.keys():
            gdict[key] = jdata.get(key)
            var_count += 1
            logger.debug(f"Loaded variable: {key}")

        logger.info(f"Loaded {var_count} variables from JSON")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {filename}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load JSON file: {e}", exc_info=True)
        raise
