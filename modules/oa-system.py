"""
Open-Automator System Module
Gestisce operazioni di sistema locale e remoto (SSH, SCP, comandi) con data propagation
"""

import oacommon
import inspect
from scp import SCPClient
import os
import subprocess
import logging
from logger_config import AutomatorLogger

# Logger per questo modulo
logger = AutomatorLogger.get_logger('oa-system')

gdict = {}
myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdict_param):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param


@oacommon.trace
def runcmd(self, param):
    """
    Esegue un comando shell locale con data propagation

    Args:
        param: dict con:
            - command: comando da eseguire (può usare input da task precedente)
            - printout: (opzionale) stampa output, default False
            - saveonvar: (opzionale) salva output in variabile
            - shell: (opzionale) usa shell, default True
            - timeout: (opzionale) timeout in secondi
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con output del comando
    """
    func_name = myself()
    logger.info("Executing local shell command")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se command non è specificato, prova a costruirlo dall'input
        if 'command' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'command' in prev_input:
                    param['command'] = prev_input['command']
                elif 'filepath' in prev_input:
                    # Se l'input ha un filepath, costruisci comando su quel file
                    param['command'] = f"cat {prev_input['filepath']}"
                logger.info("Using command from previous task")
            elif isinstance(prev_input, str):
                param['command'] = prev_input
        
        if not oacommon.checkandloadparam(self, myself, "command", param=param):
            raise ValueError(f"Missing required parameter 'command' for {func_name}")

        command = oacommon.effify(gdict["command"])
        printout = param.get("printout", False)
        use_shell = param.get("shell", True)
        timeout = param.get("timeout", None)

        logger.info(f"Command: {command}")
        if timeout:
            logger.debug(f"Timeout: {timeout}s")

        # Esegui comando con subprocess
        try:
            result = subprocess.run(
                command,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                text=True
            )
            
            stdout = result.stdout
            stderr = result.stderr
            return_code = result.returncode

            logger.info(f"Command completed with return code: {return_code}")
            logger.debug(f"Output size: {len(stdout)} chars")

            # Considera return code != 0 come failure
            if return_code != 0:
                task_success = False
                error_msg = f"Command returned non-zero exit code: {return_code}"
                if stderr:
                    error_msg += f"\nStderr: {stderr}"
                logger.warning(error_msg)

            # Printout
            if printout:
                if len(stdout) > 1000:
                    logger.info(f"Command output (first 1000 chars):\n{stdout[:1000]}...")
                else:
                    logger.info(f"Command output:\n{stdout}")
                if stderr:
                    logger.warning(f"Command stderr:\n{stderr}")

            # Salva in variabile (retrocompatibilità)
            if oacommon.checkparam("saveonvar", param):
                saveonvar = param["saveonvar"]
                gdict[saveonvar] = stdout
                logger.debug(f"Output saved to variable: {saveonvar}")

            # Output data per propagation
            output_data = {
                'stdout': stdout,
                'stderr': stderr,
                'return_code': return_code,
                'command': command,
                'success': return_code == 0
            }

        except subprocess.TimeoutExpired as e:
            task_success = False
            error_msg = f"Command timeout after {timeout}s"
            logger.error(error_msg)
            output_data = {
                'error': error_msg,
                'command': command,
                'timeout': timeout
            }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Command execution failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def systemd(self, param):
    """
    Gestisce servizi systemd su server remoto con data propagation

    Args:
        param: dict con:
            - remoteserver, remoteuser, remotepassword, remoteport
            - servicename: nome del servizio
            - servicestate: start|stop|restart|status|daemon-reload
            - saveonvar: (opzionale) salva output in variabile
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con output systemd
    """
    func_name = myself()
    logger.info("Managing systemd service")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = [
        'remoteserver', 'remoteuser', 'remotepassword',
        'remoteport', 'servicename', 'servicestate'
    ]

    try:
        # Se servicename non è specificato, prova dall'input
        if 'servicename' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'servicename' in prev_input:
                param['servicename'] = prev_input['servicename']
                logger.info("Using servicename from previous task")
        
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        remoteserver = oacommon.effify(gdict['remoteserver'])
        remoteuser = oacommon.effify(gdict['remoteuser'])
        remotepassword = oacommon.effify(gdict['remotepassword'])
        remoteport = oacommon.effify(gdict['remoteport'])
        servicename = oacommon.effify(gdict['servicename'])
        servicestate = gdict['servicestate']

        logger.info(f"Service: {servicename}, State: {servicestate} on {remoteserver}")

        if 'daemon-reload' in servicestate:
            command = 'systemctl daemon-reload'
        else:
            command = f'systemctl {servicestate} {servicename}'

        logger.debug(f"Systemd command: {command}")

        output = oacommon.sshremotecommand(
            remoteserver, remoteport, remoteuser, remotepassword, command
        )

        decoded_output = output.decode('utf-8', errors='ignore')

        logger.info("Systemd operation completed successfully")
        logger.debug(f"Output: {decoded_output}")

        # Salva in variabile (retrocompatibilità)
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = decoded_output
            logger.debug(f"Systemd output saved to variable: {saveonvar}")

        # Output data per propagation
        output_data = {
            'output': decoded_output,
            'service': servicename,
            'state': servicestate,
            'server': remoteserver,
            'success': True
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Systemd operation failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def remotecommand(self, param):
    """
    Esegue un comando remoto via SSH con data propagation

    Args:
        param: dict con:
            - remoteserver, remoteuser, remotepassword, remoteport
            - command: comando da eseguire (può usare input da task precedente)
            - saveonvar: (opzionale) salva output in variabile
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con output del comando remoto
    """
    func_name = myself()
    logger.info("Executing remote SSH command")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = ['remoteserver', 'remoteuser', 'remotepassword', 'remoteport', 'command']

    try:
        # Se command non è specificato, prova dall'input
        if 'command' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'command' in prev_input:
                    param['command'] = prev_input['command']
                elif 'script' in prev_input:
                    param['command'] = prev_input['script']
                logger.info("Using command from previous task")
            elif isinstance(prev_input, str):
                param['command'] = prev_input
        
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        remoteserver = oacommon.effify(gdict['remoteserver'])
        remoteuser = oacommon.effify(gdict['remoteuser'])
        remotepassword = oacommon.effify(gdict['remotepassword'])
        remoteport = oacommon.effify(gdict['remoteport'])
        command = oacommon.effify(gdict['command'])

        logger.info(f"Target: {remoteuser}@{remoteserver}:{remoteport}")
        logger.debug(f"Command: {command}")

        output = oacommon.sshremotecommand(
            remoteserver, remoteport, remoteuser, remotepassword, command
        )

        decoded_output = output.decode('utf-8', errors='ignore')

        # Salva in variabile (retrocompatibilità)
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = decoded_output
            logger.debug(f"Output saved to variable: {saveonvar}")

        # Log output
        if len(decoded_output) > 500:
            logger.info(f"Command output (first 500 chars): {decoded_output[:500]}...")
        else:
            logger.info(f"Command output: {decoded_output}")

        # Output data per propagation
        output_data = {
            'output': decoded_output,
            'command': command,
            'server': remoteserver,
            'user': remoteuser,
            'port': remoteport
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Remote command failed on {remoteserver}: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def scp(self, param):
    """
    Trasferisce file/directory via SCP con data propagation

    Args:
        param: dict con:
            - remoteserver, remoteuser, remotepassword, remoteport
            - localpath: path locale (può usare input da task precedente)
            - remotepath: path remoto
            - recursive: True/False
            - direction: localtoremote|remotetolocal
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con info sul trasferimento
    """
    func_name = myself()
    logger.info("Starting SCP transfer")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = [
        'remoteserver', 'remoteuser', 'remotepassword', 'remoteport',
        'localpath', 'remotepath', 'recursive', 'direction'
    ]

    ssh = None
    scp_client = None

    try:
        # Se localpath non è specificato, usa input dal task precedente
        if 'localpath' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'filepath' in prev_input:
                    param['localpath'] = prev_input['filepath']
                elif 'filename' in prev_input:
                    param['localpath'] = prev_input['filename']
                elif 'dstpath' in prev_input:
                    param['localpath'] = prev_input['dstpath']
                logger.info("Using localpath from previous task")
        
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        remoteserver = oacommon.effify(gdict['remoteserver'])
        remoteuser = oacommon.effify(gdict['remoteuser'])
        remotepassword = oacommon.effify(gdict['remotepassword'])
        remoteport = oacommon.effify(gdict['remoteport'])
        direction = gdict['direction']
        recursive = gdict['recursive']

        # Gestione multi-path
        if isinstance(gdict['localpath'], list):
            localpath = list(gdict['localpath'])
        else:
            localpath = oacommon.effify(gdict['localpath'])

        if isinstance(gdict['remotepath'], list):
            remotepath = list(gdict['remotepath'])
        else:
            remotepath = oacommon.effify(gdict['remotepath'])

        logger.info(f"Direction: {direction} | Target: {remoteuser}@{remoteserver}:{remoteport}")
        logger.debug(f"Local: {localpath} | Remote: {remotepath} | Recursive: {recursive}")

        ismultipath = False
        lres = []
        files_transferred = 0

        # Validazione multi-path
        if isinstance(localpath, list) and isinstance(remotepath, list):
            if len(localpath) != len(remotepath):
                raise ValueError("Multipath: local and remote path lists must have same length")

            res = ','.join([f"{l}|{r}" for l, r in zip(localpath, remotepath)])
            lres = res.split(',')
            ismultipath = True
            logger.info(f"Multipath transfer: {len(localpath)} file(s)")

        elif isinstance(localpath, list) or isinstance(remotepath, list):
            raise ValueError("If one path is a list, both must be lists")

        # Connessione SSH
        ssh = oacommon.createSSHClient(remoteserver, remoteport, remoteuser, remotepassword)
        scp_client = SCPClient(ssh.get_transport())

        # Esegui trasferimento
        if 'localtoremote' in direction:
            if ismultipath:
                for i, res in enumerate(lres, 1):
                    lp, rp = res.split('|')
                    lp = oacommon.effify(lp)
                    rp = oacommon.effify(rp)
                    logger.debug(f"[{i}/{len(lres)}] Uploading: {lp} -> {rp}")
                    scp_client.put(lp, recursive=recursive, remote_path=rp)
                    files_transferred += 1
            else:
                logger.debug(f"Uploading: {localpath} -> {remotepath}")
                scp_client.put(localpath, recursive=recursive, remote_path=remotepath)
                files_transferred = 1

        elif 'remotetolocal' in direction:
            if ismultipath:
                for i, res in enumerate(lres, 1):
                    lp, rp = res.split('|')
                    lp = oacommon.effify(lp)
                    rp = oacommon.effify(rp)
                    logger.debug(f"[{i}/{len(lres)}] Downloading: {rp} -> {lp}")
                    scp_client.get(remote_path=rp, local_path=lp, recursive=recursive)
                    files_transferred += 1
            else:
                logger.debug(f"Downloading: {remotepath} -> {localpath}")
                scp_client.get(remote_path=remotepath, local_path=localpath, recursive=recursive)
                files_transferred = 1

        logger.info(f"SCP transfer completed successfully: {files_transferred} transfer(s)")

        # Output data per propagation
        output_data = {
            'files_transferred': files_transferred,
            'direction': direction,
            'server': remoteserver,
            'localpath': localpath,
            'remotepath': remotepath,
            'recursive': recursive,
            'multipath': ismultipath
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"SCP transfer failed: {e}", exc_info=True)

    finally:
        # Cleanup
        try:
            if scp_client:
                scp_client.close()
            if ssh:
                ssh.close()
            logger.debug("SCP connections closed")
        except Exception as cleanup_error:
            logger.warning(f"Error during connection cleanup: {cleanup_error}")

        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def execute_script(self, param):
    """
    Esegue uno script locale e propaga l'output

    Args:
        param: dict con:
            - script_path: path dello script (può usare input da task precedente)
            - args: (opzionale) lista di argomenti
            - interpreter: (opzionale) interprete (es. 'python3', 'bash'), default auto-detect
            - timeout: (opzionale) timeout in secondi
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con output dello script
    """
    func_name = myself()
    logger.info("Executing local script")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se script_path non è specificato, usa input
        if 'script_path' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'filepath' in prev_input:
                    param['script_path'] = prev_input['filepath']
                elif 'script_path' in prev_input:
                    param['script_path'] = prev_input['script_path']
                logger.info("Using script path from previous task")
        
        if not oacommon.checkandloadparam(self, myself, "script_path", param=param):
            raise ValueError(f"Missing required parameter 'script_path' for {func_name}")

        script_path = oacommon.effify(gdict["script_path"])
        args = param.get("args", [])
        interpreter = param.get("interpreter")
        timeout = param.get("timeout", None)

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")

        # Auto-detect interpreter
        if not interpreter:
            ext = os.path.splitext(script_path)[1]
            interpreter_map = {
                '.py': 'python3',
                '.sh': 'bash',
                '.rb': 'ruby',
                '.js': 'node',
                '.pl': 'perl'
            }
            interpreter = interpreter_map.get(ext)

        # Costruisci comando
        if interpreter:
            command = [interpreter, script_path] + args
        else:
            command = [script_path] + args

        logger.info(f"Executing script: {' '.join(command)}")

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True
        )

        stdout = result.stdout
        stderr = result.stderr
        return_code = result.returncode

        logger.info(f"Script completed with return code: {return_code}")

        if return_code != 0:
            task_success = False
            error_msg = f"Script returned non-zero exit code: {return_code}"
            if stderr:
                error_msg += f"\nStderr: {stderr}"
            logger.warning(error_msg)

        # Output data
        output_data = {
            'stdout': stdout,
            'stderr': stderr,
            'return_code': return_code,
            'script_path': script_path,
            'interpreter': interpreter,
            'args': args
        }

    except subprocess.TimeoutExpired as e:
        task_success = False
        error_msg = f"Script timeout after {timeout}s"
        logger.error(error_msg)
    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Script execution failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data
