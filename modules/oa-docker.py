"""
Open-Automator Docker Module

Manages Docker operations with data propagation
Support for wallet, placeholder {WALLET:key}, {ENV:var} and {VAULT:key}
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
    """Sets the global dictionary"""
    global gdict
    gdict = gdictparam
    self.gdict = gdictparam

@oacommon.trace
def container_run(self, param):
    """
    Starts a Docker container with data propagation

    Args:
        param (dict) with:
            - image: Docker image name - supports {WALLET:key}, {ENV:var}
            - name: (optional) container name - supports {ENV:var}
            - ports: (optional) dict port mapping e.g. {"8080": "80"}
            - volumes: (optional) dict volume mapping
            - env: (optional) dict environment variables
            - detach: (optional) run in background (default: True)
            - remove: (optional) auto-remove on exit (default: False)
            - command: (optional) command to execute
            - input: (optional) data from previous task
            - workflowcontext: (optional) workflow context
            - taskid: (optional) unique task id
            - taskstore: (optional) TaskResultStore instance

    Returns:
        tuple (success, outputdict) with container info

    Example YAML:
        # Run simple container
        - name: run_nginx
          module: oa-docker
          function: container_run
          image: nginx:latest
          name: my_nginx
          ports:
            "8080": "80"
          detach: true

        # Run with environment variables from wallet
        - name: run_app
          module: oa-docker
          function: container_run
          image: myapp:v1
          env:
            API_KEY: "{WALLET:api_key}"
            DB_HOST: "{ENV:DATABASE_HOST}"
          volumes:
            "/host/data": "/container/data"
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
        if not oacommon.checkandloadparam(self, myself, requiredparams, param=param):
            raise ValueError(f"Missing required parameters for {funcname}")

        wallet = gdict.get("wallet")
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

        cmd = ["docker", "run"]
        if detach:
            cmd.append("-d")
        if remove:
            cmd.append("--rm")
        if name:
            cmd.extend(["--name", name])

        for host_port, container_port in ports.items():
            cmd.extend(["-p", f"{host_port}:{container_port}"])
            logger.debug(f"Port mapping: {host_port}->{container_port}")

        for host_path, container_path in volumes.items():
            cmd.extend(["-v", f"{host_path}:{container_path}"])
            logger.debug(f"Volume mapping: {host_path}->{container_path}")

        for key, value in envvars.items():
            resolved_value = oacommon.getparam(f"{key}={value}", key, wallet) if isinstance(value, str) else value
            cmd.extend(["-e", f"{key}={resolved_value}"])

        cmd.append(image)

        if command:
            if isinstance(command, str):
                cmd.extend(command.split())
            else:
                cmd.extend(command)

        logger.debug(f"Docker command: {' '.join(cmd)}")

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
    Stops a Docker container with data propagation

    Args:
        param (dict) with:
            - container: container name or ID (can use input from previous task)
            - timeout: (optional) timeout in seconds (default: 10)
            - input: (optional) data from previous task
            - workflowcontext: (optional) workflow context
            - taskid: (optional) unique task id
            - taskstore: (optional) TaskResultStore instance

    Returns:
        tuple (success, outputdict) with stopped container info

    Example YAML:
        # Stop specific container
        - name: stop_nginx
          module: oa-docker
          function: container_stop
          container: my_nginx
          timeout: 15

        # Stop container from previous task
        - name: stop_container
          module: oa-docker
          function: container_stop
          # Uses container_id from previous task output
    """
    funcname = myself()
    logger.info("Stopping Docker container")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
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
    Retrieves logs from a Docker container

    Args:
        param (dict) with:
            - container: container name or ID (can use input from previous task)
            - tail: (optional) number of lines (default: all)
            - follow: (optional) follow logs in real-time (default: False)
            - timestamps: (optional) show timestamps (default: False)
            - saveonvar: (optional) save logs to variable
            - input: (optional) data from previous task
            - taskid, taskstore, workflowcontext

    Returns:
        tuple (success, logs) - propagates the logs

    Example YAML:
        # Get last 100 lines of logs
        - name: get_logs
          module: oa-docker
          function: container_logs
          container: my_nginx
          tail: 100
          timestamps: true

        # Get logs from previous task container
        - name: check_logs
          module: oa-docker
          function: container_logs
          # Uses container_id from previous task
          saveonvar: container_output
    """
    funcname = myself()
    logger.info("Retrieving Docker container logs")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
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
