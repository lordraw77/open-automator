"""
Open-Automator Docker Module
Gestisce operazioni Docker con data propagation
Supporto per wallet, placeholder WALLET{key}, ENV{var} e VAULT{key}
"""

import oacommon
import inspect
import subprocess
import json
import logging
from logger_config import AutomatorLogger

logger = AutomatorLogger.getlogger("oa-docker")

gdict = {}

myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdictparam):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdictparam
    self.gdict = gdictparam


@oacommon.trace
def container_run(self, param):
    """
    Avvia un container Docker con data propagation

    Args:
        param (dict) con:
            - image: nome immagine Docker - supporta WALLET{key}, ENV{var}
            - name: (opzionale) nome del container - supporta ENV{var}
            - ports: (opzionale) dict port mapping es. {"8080": "80"}
            - volumes: (opzionale) dict volume mapping
            - env: (opzionale) dict variabili ambiente
            - detach: (opzionale) run in background (default: True)
            - remove: (opzionale) auto-remove al termine (default: False)
            - command: (opzionale) comando da eseguire
            - input: (opzionale) dati dal task precedente
            - workflowcontext: (opzionale) contesto workflow
            - taskid: (opzionale) id univoco del task
            - taskstore: (opzionale) istanza di TaskResultStore

    Returns:
        tuple (success, outputdict) con info sul container
    """
    funcname = myself()
    logger.info(f"Running Docker container")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    requiredparams = ["image"]

    try:
        # Validazione parametri
        if not oacommon.checkandloadparam(self, myself, requiredparams, param=param):
            raise ValueError(f"Missing required parameters for {funcname}")

        # Recupera wallet
        wallet = gdict.get("wallet")

        # Estrai parametri
        image = oacommon.getparam(param, "image", wallet) or gdict.get("image")
        name = oacommon.getparam(param, "name", wallet) or param.get("name")
        ports = param.get("ports", {})
        volumes = param.get("volumes", {})
        envvars = param.get("env", {})
        detach = param.get("detach", True)
        remove = param.get("remove", False)
        command = oacommon.getparam(param, "command", wallet) or param.get("command")

        logger.info(f"Image: {image}")
        if name:
            logger.debug(f"Container name: {name}")

        # Costruisci comando docker run
        cmd = ["docker", "run"]

        if detach:
            cmd.append("-d")

        if remove:
            cmd.append("--rm")

        if name:
            cmd.extend(["--name", name])

        # Aggiungi port mapping
        for host_port, container_port in ports.items():
            cmd.extend(["-p", f"{host_port}:{container_port}"])
            logger.debug(f"Port mapping: {host_port}->{container_port}")

        # Aggiungi volume mapping
        for host_path, container_path in volumes.items():
            cmd.extend(["-v", f"{host_path}:{container_path}"])
            logger.debug(f"Volume mapping: {host_path}->{container_path}")

        # Aggiungi variabili ambiente
        for key, value in envvars.items():
            # Supporta placeholder nelle variabili ambiente
            resolved_value = oacommon.getparam(f"{key}={value}", key, wallet) if isinstance(value, str) else value
            cmd.extend(["-e", f"{key}={resolved_value}"])

        # Aggiungi immagine
        cmd.append(image)

        # Aggiungi comando opzionale
        if command:
            if isinstance(command, str):
                cmd.extend(command.split())
            else:
                cmd.extend(command)

        logger.debug(f"Docker command: {' '.join(cmd)}")

        # Esegui comando
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )

        container_id = result.stdout.strip()

        if result.returncode != 0:
            tasksuccess = False
            errormsg = f"Docker run failed: {result.stderr}"
            logger.error(errormsg)
        else:
            logger.info(f"Container started successfully: {container_id[:12]}")

        # Output data per propagation
        outputdata = {
            "container_id": container_id,
            "container_name": name,
            "image": image,
            "detached": detach,
            "ports": ports,
            "volumes": volumes,
            "returncode": result.returncode,
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:
        tasksuccess = False
        errormsg = "Docker run timeout after 300s"
        logger.error(errormsg)

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"Docker container_run failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata


@oacommon.trace
def container_stop(self, param):
    """
    Ferma un container Docker con data propagation

    Args:
        param (dict) con:
            - container: nome o ID del container (può usare input da task precedente)
            - timeout: (opzionale) timeout in secondi (default: 10)
            - input: (opzionale) dati dal task precedente
            - workflowcontext: (opzionale) contesto workflow
            - taskid: (opzionale) id univoco del task
            - taskstore: (opzionale) istanza di TaskResultStore

    Returns:
        tuple (success, outputdict) con info sul container fermato
    """
    funcname = myself()
    logger.info("Stopping Docker container")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        # Data propagation: usa input se container non specificato
        if "container" not in param and "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "container_id" in previnput:
                    param["container"] = previnput["container_id"]
                elif "container_name" in previnput:
                    param["container"] = previnput["container_name"]
            logger.info("Using container from previous task")

        if not oacommon.checkandloadparam(self, myself, ["container"], param=param):
            raise ValueError(f"Missing required parameter 'container' for {funcname}")

        wallet = gdict.get("wallet")
        container = oacommon.getparam(param, "container", wallet) or gdict.get("container")
        timeout = param.get("timeout", 10)

        logger.info(f"Stopping container: {container}")

        # Esegui docker stop
        cmd = ["docker", "stop", "-t", str(timeout), container]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 30
        )

        if result.returncode != 0:
            tasksuccess = False
            errormsg = f"Docker stop failed: {result.stderr}"
            logger.error(errormsg)
        else:
            logger.info(f"Container stopped successfully: {container}")

        outputdata = {
            "container": container,
            "stopped": result.returncode == 0,
            "timeout": timeout,
            "stderr": result.stderr
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"Docker container_stop failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata


@oacommon.trace
def container_logs(self, param):
    """
    Recupera i log di un container Docker

    Args:
        param (dict) con:
            - container: nome o ID (può usare input da task precedente)
            - tail: (opzionale) numero righe (default: all)
            - follow: (opzionale) segui log in real-time (default: False)
            - timestamps: (opzionale) mostra timestamps (default: False)
            - saveonvar: (opzionale) salva log in variabile
            - input: (opzionale) dati dal task precedente
            - taskid, taskstore, workflowcontext

    Returns:
        tuple (success, logs) - propaga i log
    """
    funcname = myself()
    logger.info("Retrieving Docker container logs")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        # Data propagation
        if "container" not in param and "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict) and "container_id" in previnput:
                param["container"] = previnput["container_id"]
            logger.info("Using container from previous task")

        if not oacommon.checkandloadparam(self, myself, ["container"], param=param):
            raise ValueError(f"Missing required parameter 'container'")

        wallet = gdict.get("wallet")
        container = oacommon.getparam(param, "container", wallet) or gdict.get("container")
        tail = param.get("tail")
        timestamps = param.get("timestamps", False)

        logger.info(f"Container: {container}")

        cmd = ["docker", "logs"]

        if tail:
            cmd.extend(["--tail", str(tail)])

        if timestamps:
            cmd.append("--timestamps")

        cmd.append(container)

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        logs = result.stdout + result.stderr

        if result.returncode != 0:
            tasksuccess = False
            errormsg = f"Docker logs failed"
            logger.error(errormsg)

        logger.info(f"Retrieved {len(logs)} bytes of logs")

        # Salva in variabile se richiesto
        if oacommon.checkparam("saveonvar", param):
            saveonvar = param["saveonvar"]
            gdict[saveonvar] = logs
            logger.debug(f"Logs saved to variable {saveonvar}")

        outputdata = {
            "container": container,
            "logs": logs,
            "size": len(logs)
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"Docker container_logs failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata
