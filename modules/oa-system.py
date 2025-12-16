"""
Open-Automator System Module
Gestisce operazioni di sistema locale e remoto (SSH, SCP, comandi)
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
    Esegue un comando shell locale

    Args:
        param: dict con:
            - command: comando da eseguire
            - printout: (opzionale) stampa output
            - saveonvar: (opzionale) salva output in variabile
    """
    func_name = myself()
    logger.info("Executing local shell command")

    if not oacommon.checkandloadparam(self, myself, 'command', 'printout', param=param):
        raise ValueError(f"Missing required parameters for {func_name}")

    command = oacommon.effify(gdict['command'])
    printout = gdict['printout']

    logger.info(f"Command: {command}")

    try:
        output = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE
        ).stdout.read()

        decoded_output = output.decode('UTF-8')
        logger.info(f"Command executed successfully, output size: {len(decoded_output)} chars")

        if printout:
            logger.info(f"Command output:\n{decoded_output}")
        else:
            # Preview in debug
            preview = decoded_output[:200] + '...' if len(decoded_output) > 200 else decoded_output
            logger.debug(f"Output preview: {preview}")

        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = decoded_output
            logger.debug(f"Output saved to variable: {saveonvar}")

        return decoded_output

    except Exception as e:
        logger.error(f"Command execution failed: {e}", exc_info=True)
        raise


@oacommon.trace
def systemd(self, param):
    """
    Gestisce servizi systemd su server remoto

    Args:
        param: dict con remoteserver, remoteuser, remotepassword, remoteport,
               servicename, servicestate
    """
    func_name = myself()
    logger.info("Managing systemd service")

    required_params = ['remoteserver', 'remoteuser', 'remotepassword', 
                      'remoteport', 'servicename', 'servicestate']

    if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
        raise ValueError(f"Missing required parameters for {func_name}")

    remoteserver = oacommon.effify(gdict['remoteserver'])
    remoteuser = oacommon.effify(gdict['remoteuser'])
    remotepassword = oacommon.effify(gdict['remotepassword'])
    remoteport = oacommon.effify(gdict['remoteport'])
    servicename = oacommon.effify(gdict['servicename'])
    servicestate = gdict['servicestate']

    logger.info(f"Service: {servicename}, State: {servicestate} on {remoteserver}")

    try:
        if 'daemon-reload' in servicestate:
            command = 'systemctl daemon-reload'
        else:
            command = f'systemctl {servicestate} {servicename}'

        logger.debug(f"Systemd command: {command}")

        output = oacommon.sshremotecommand(
            remoteserver, remoteport, remoteuser, remotepassword, command
        )

        logger.info(f"Systemd operation completed successfully")
        logger.debug(f"Output: {output.decode('utf-8', errors='ignore')}")

        return output

    except Exception as e:
        logger.error(f"Systemd operation failed: {e}", exc_info=True)
        raise


@oacommon.trace
def remotecommand(self, param):
    """
    Esegue un comando remoto via SSH

    Args:
        param: dict con remoteserver, remoteuser, remotepassword, remoteport,
               command, saveonvar (opzionale)
    """
    func_name = myself()
    logger.info("Executing remote SSH command")

    required_params = ['remoteserver', 'remoteuser', 'remotepassword', 'remoteport', 'command']

    if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
        raise ValueError(f"Missing required parameters for {func_name}")

    remoteserver = oacommon.effify(gdict['remoteserver'])
    remoteuser = oacommon.effify(gdict['remoteuser'])
    remotepassword = oacommon.effify(gdict['remotepassword'])
    remoteport = oacommon.effify(gdict['remoteport'])
    command = oacommon.effify(gdict['command'])

    logger.info(f"Target: {remoteuser}@{remoteserver}:{remoteport}")
    logger.debug(f"Command: {command}")

    try:
        output = oacommon.sshremotecommand(
            remoteserver, remoteport, remoteuser, remotepassword, command
        )

        decoded_output = output.decode('utf-8', errors='ignore')

        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = decoded_output
            logger.debug(f"Output saved to variable: {saveonvar}")

        # Log output appropriato
        if len(decoded_output) > 500:
            logger.info(f"Command output (first 500 chars): {decoded_output[:500]}...")
        else:
            logger.info(f"Command output: {decoded_output}")

        return decoded_output

    except Exception as e:
        logger.error(f"Remote command failed on {remoteserver}: {e}", exc_info=True)
        raise


@oacommon.trace
def scp(self, param):
    """
    Trasferisce file/directory via SCP

    Args:
        param: dict con remoteserver, remoteuser, remotepassword, remoteport,
               localpath, remotepath, recursive, direction
    """
    func_name = myself()
    logger.info("Starting SCP transfer")

    required_params = ['remoteserver', 'remoteuser', 'remotepassword', 'remoteport',
                      'localpath', 'remotepath', 'recursive', 'direction']

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

    try:
        # Validazione multi-path
        if isinstance(localpath, list) and isinstance(remotepath, list):
            if len(localpath) != len(remotepath):
                error_msg = "Multipath: local and remote path lists must have same length"
                logger.error(error_msg)
                raise ValueError(error_msg)

            res = ','.join([f"{l}|{r}" for l, r in zip(localpath, remotepath)])
            lres = res.split(',')
            ismultipath = True
            logger.info(f"Multipath transfer: {len(localpath)} file(s)")

        elif isinstance(localpath, list) or isinstance(remotepath, list):
            error_msg = "If one path is a list, both must be lists"
            logger.error(error_msg)
            raise ValueError(error_msg)

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
            else:
                logger.debug(f"Uploading: {localpath} -> {remotepath}")
                scp_client.put(localpath, recursive=recursive, remote_path=remotepath)

        elif 'remotetolocal' in direction:
            if ismultipath:
                for i, res in enumerate(lres, 1):
                    lp, rp = res.split('|')
                    lp = oacommon.effify(lp)
                    rp = oacommon.effify(rp)
                    logger.debug(f"[{i}/{len(lres)}] Downloading: {rp} -> {lp}")
                    scp_client.get(remote_path=rp, local_path=lp, recursive=recursive)
            else:
                logger.debug(f"Downloading: {remotepath} -> {localpath}")
                scp_client.get(remote_path=remotepath, local_path=localpath, recursive=recursive)

        logger.info("SCP transfer completed successfully")

    except Exception as e:
        logger.error(f"SCP transfer failed: {e}", exc_info=True)
        raise

    finally:
        # Cleanup
        try:
            if 'scp_client' in locals():
                scp_client.close()
            if 'ssh' in locals():
                ssh.close()
            logger.debug("SCP connections closed")
        except Exception as cleanup_error:
            logger.warning(f"Error during connection cleanup: {cleanup_error}")
