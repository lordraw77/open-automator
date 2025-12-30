"""
Open-Automator System Module

Manages local and remote system operations (SSH, SCP, commands) with data propagation
Support for wallet, placeholder {WALLET:key}, {ENV:var} and {VAULT:key}
"""

import oacommon
import inspect
from scp import SCPClient
import os
import subprocess
import logging
from logger_config import AutomatorLogger

# Logger for this module
logger = AutomatorLogger.get_logger('oa-system')

gdict = {}
myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdict_param):
    """Sets the global dictionary"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

@oacommon.trace
def runcmd(self, param):
    """
    Executes a local shell command with data propagation

    Args:
        param: dict with:
            - command: command to execute (can use input from previous task) - supports {WALLET:key}, {ENV:var}
            - printout: (optional) print output, default False
            - saveonvar: (optional) save output to variable
            - shell: (optional) use shell, default True
            - timeout: (optional) timeout in seconds
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with command output

    Example YAML:
        # Simple command
        - name: list_files
          module: oa-system
          function: runcmd
          command: "ls -la /var/log"
          printout: true

        # Command with environment variable
        - name: backup_database
          module: oa-system
          function: runcmd
          command: "mysqldump -u root -p{ENV:DB_PASSWORD} mydb > /backup/mydb.sql"

        # Command with timeout
        - name: long_running_process
          module: oa-system
          function: runcmd
          command: "python3 /scripts/process_data.py"
          timeout: 300
          printout: true

        # Command with wallet placeholder
        - name: secure_command
          module: oa-system
          function: runcmd
          command: "curl -H 'Authorization: Bearer {WALLET:api_token}' https://api.example.com/data"

        # Command from previous task
        - name: execute_generated_command
          module: oa-system
          function: runcmd
          # command taken from previous task output

        # Save output to variable
        - name: get_system_info
          module: oa-system
          function: runcmd
          command: "uname -a"
          saveonvar: system_info

        # Complex command with multiple placeholders
        - name: deploy_service
          module: oa-system
          function: runcmd
          command: "docker run -e API_KEY={VAULT:api_key} -e ENV={ENV:ENVIRONMENT} myapp:latest"
          shell: true
          timeout: 60
    """
    func_name = myself()
    logger.info("Executing local shell command")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # If command not specified, try to build it from input
        if 'command' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'command' in prev_input:
                    param['command'] = prev_input['command']
                elif 'filepath' in prev_input:
                    # If input has filepath, build command on that file
                    param['command'] = f"cat {prev_input['filepath']}"
                logger.info("Using command from previous task")
            elif isinstance(prev_input, str):
                param['command'] = prev_input

        if not oacommon.checkandloadparam(self, myself, "command", param=param):
            raise ValueError(f"Missing required parameter 'command' for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        command = oacommon.get_param(param, 'command', wallet) or gdict.get('command')

        printout = param.get("printout", False)
        use_shell = param.get("shell", True)
        timeout = param.get("timeout", None)

        logger.info(f"Command: {command[:100]}..." if len(command) > 100 else f"Command: {command}")
        if timeout:
            logger.debug(f"Timeout: {timeout}s")

        # Execute command with subprocess
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

            # Consider return code != 0 as failure
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

            # Save to variable (backward compatibility)
            if oacommon.checkparam("saveonvar", param):
                saveonvar = param["saveonvar"]
                gdict[saveonvar] = stdout
                logger.debug(f"Output saved to variable: {saveonvar}")

            # Output data for propagation
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
    Manages systemd services on remote server with data propagation

    Args:
        param: dict with:
            - remoteserver: remote host - supports {WALLET:key}, {ENV:var}
            - remoteuser: SSH username - supports {WALLET:key}, {ENV:var}
            - remotepassword: SSH password - supports {WALLET:key}, {VAULT:key}
            - remoteport: SSH port - supports {ENV:var}
            - servicename: service name - supports {WALLET:key}, {ENV:var}
            - servicestate: start|stop|restart|status|daemon-reload
            - saveonvar: (optional) save output to variable
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with systemd output

    Example YAML:
        # Start a service
        - name: start_nginx
          module: oa-system
          function: systemd
          remoteserver: "web-server-01"
          remoteuser: "admin"
          remotepassword: "{VAULT:ssh_password}"
          remoteport: 22
          servicename: "nginx"
          servicestate: "start"

        # Restart service with credentials from wallet
        - name: restart_app
          module: oa-system
          function: systemd
          remoteserver: "{ENV:APP_SERVER}"
          remoteuser: "{WALLET:ssh_user}"
          remotepassword: "{VAULT:ssh_pass}"
          remoteport: 22
          servicename: "myapp"
          servicestate: "restart"

        # Check service status
        - name: check_docker_status
          module: oa-system
          function: systemd
          remoteserver: "docker-host"
          remoteuser: "root"
          remotepassword: "{VAULT:root_password}"
          remoteport: 22
          servicename: "docker"
          servicestate: "status"
          saveonvar: docker_status

        # Reload systemd daemon
        - name: reload_systemd
          module: oa-system
          function: systemd
          remoteserver: "{ENV:TARGET_SERVER}"
          remoteuser: "admin"
          remotepassword: "{VAULT:admin_pass}"
          remoteport: 22
          servicename: ""
          servicestate: "daemon-reload"

        # Stop service
        - name: stop_service
          module: oa-system
          function: systemd
          remoteserver: "app-server"
          remoteuser: "{WALLET:deploy_user}"
          remotepassword: "{VAULT:deploy_pass}"
          remoteport: 22
          servicename: "old-service"
          servicestate: "stop"

        # Service name from previous task
        - name: manage_dynamic_service
          module: oa-system
          function: systemd
          remoteserver: "server-01"
          remoteuser: "admin"
          remotepassword: "{VAULT:ssh_pass}"
          remoteport: 22
          # servicename from previous task
          servicestate: "restart"
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
        # If servicename not specified, try from input
        if 'servicename' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'servicename' in prev_input:
                param['servicename'] = prev_input['servicename']
                logger.info("Using servicename from previous task")

        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders (CRITICAL for SSH password!)
        remoteserver = oacommon.get_param(param, 'remoteserver', wallet) or gdict.get('remoteserver')
        remoteuser = oacommon.get_param(param, 'remoteuser', wallet) or gdict.get('remoteuser')
        remotepassword = oacommon.get_param(param, 'remotepassword', wallet) or gdict.get('remotepassword')
        remoteport = oacommon.get_param(param, 'remoteport', wallet) or gdict.get('remoteport')
        servicename = oacommon.get_param(param, 'servicename', wallet) or gdict.get('servicename')
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

        # Save to variable (backward compatibility)
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = decoded_output
            logger.debug(f"Systemd output saved to variable: {saveonvar}")

        # Output data for propagation
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
    Executes a remote command via SSH with data propagation

    Args:
        param: dict with:
            - remoteserver: remote host - supports {WALLET:key}, {ENV:var}
            - remoteuser: SSH username - supports {WALLET:key}, {ENV:var}
            - remotepassword: SSH password - supports {WALLET:key}, {VAULT:key}
            - remoteport: SSH port - supports {ENV:var}
            - command: command to execute (can use input from previous task) - supports {WALLET:key}, {ENV:var}
            - saveonvar: (optional) save output to variable
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with remote command output

    Example YAML:
        # Simple remote command
        - name: check_disk_space
          module: oa-system
          function: remotecommand
          remoteserver: "web-server-01"
          remoteuser: "admin"
          remotepassword: "{VAULT:ssh_password}"
          remoteport: 22
          command: "df -h"

        # Remote command with credentials from wallet
        - name: deploy_app
          module: oa-system
          function: remotecommand
          remoteserver: "{ENV:PROD_SERVER}"
          remoteuser: "{WALLET:deploy_user}"
          remotepassword: "{VAULT:deploy_pass}"
          remoteport: 22
          command: "cd /opt/app && git pull && systemctl restart myapp"

        # Check Docker containers remotely
        - name: list_containers
          module: oa-system
          function: remotecommand
          remoteserver: "docker-host"
          remoteuser: "root"
          remotepassword: "{VAULT:root_password}"
          remoteport: 22
          command: "docker ps -a"
          saveonvar: container_list

        # Execute script on remote server
        - name: run_remote_script
          module: oa-system
          function: remotecommand
          remoteserver: "{ENV:APP_SERVER}"
          remoteuser: "{WALLET:ssh_user}"
          remotepassword: "{VAULT:ssh_pass}"
          remoteport: 22
          command: "/home/admin/scripts/backup.sh"

        # Command with environment variables
        - name: remote_deploy
          module: oa-system
          function: remotecommand
          remoteserver: "app-server"
          remoteuser: "deployer"
          remotepassword: "{VAULT:deployer_pass}"
          remoteport: 22
          command: "export ENV=production && /opt/deploy.sh"

        # Command from previous task
        - name: execute_generated_command
          module: oa-system
          function: remotecommand
          remoteserver: "remote-host"
          remoteuser: "admin"
          remotepassword: "{VAULT:ssh_pass}"
          remoteport: 22
          # command from previous task output

        # Complex multi-line command
        - name: setup_environment
          module: oa-system
          function: remotecommand
          remoteserver: "{ENV:TARGET_HOST}"
          remoteuser: "root"
          remotepassword: "{VAULT:root_pass}"
          remoteport: 22
          command: |
            cd /opt/app &&
            git pull origin main &&
            pip install -r requirements.txt &&
            systemctl restart myservice
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
        # If command not specified, try from input
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders (CRITICAL for SSH password!)
        remoteserver = oacommon.get_param(param, 'remoteserver', wallet) or gdict.get('remoteserver')
        remoteuser = oacommon.get_param(param, 'remoteuser', wallet) or gdict.get('remoteuser')
        remotepassword = oacommon.get_param(param, 'remotepassword', wallet) or gdict.get('remotepassword')
        remoteport = oacommon.get_param(param, 'remoteport', wallet) or gdict.get('remoteport')
        command = oacommon.get_param(param, 'command', wallet) or gdict.get('command')

        logger.info(f"Target: {remoteuser}@{remoteserver}:{remoteport}")
        logger.debug(f"Command: {command[:100]}..." if len(command) > 100 else f"Command: {command}")

        output = oacommon.sshremotecommand(
            remoteserver, remoteport, remoteuser, remotepassword, command
        )

        decoded_output = output.decode('utf-8', errors='ignore')

        # Save to variable (backward compatibility)
        if oacommon.checkparam('saveonvar', param):
            saveonvar = param['saveonvar']
            gdict[saveonvar] = decoded_output
            logger.debug(f"Output saved to variable: {saveonvar}")

        # Log output
        if len(decoded_output) > 500:
            logger.info(f"Command output (first 500 chars): {decoded_output[:500]}...")
        else:
            logger.info(f"Command output: {decoded_output}")

        # Output data for propagation
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
    Transfers files/directories via SCP with data propagation

    Args:
        param: dict with:
            - remoteserver: remote host - supports {WALLET:key}, {ENV:var}
            - remoteuser: SSH username - supports {WALLET:key}, {ENV:var}
            - remotepassword: SSH password - supports {WALLET:key}, {VAULT:key}
            - remoteport: SSH port - supports {ENV:var}
            - localpath: local path (can use input from previous task) - supports {WALLET:key}, {ENV:var}
            - remotepath: remote path - supports {WALLET:key}, {ENV:var}
            - recursive: True/False
            - direction: localtoremote|remotetolocal
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with transfer info

    Example YAML:
        # Upload file to remote server
        - name: upload_config
          module: oa-system
          function: scp
          remoteserver: "web-server-01"
          remoteuser: "admin"
          remotepassword: "{VAULT:ssh_password}"
          remoteport: 22
          localpath: "/local/config.yml"
          remotepath: "/etc/myapp/config.yml"
          recursive: false
          direction: "localtoremote"

        # Download file from remote server
        - name: download_logs
          module: oa-system
          function: scp
          remoteserver: "{ENV:PROD_SERVER}"
          remoteuser: "{WALLET:ssh_user}"
          remotepassword: "{VAULT:ssh_pass}"
          remoteport: 22
          localpath: "/backup/logs"
          remotepath: "/var/log/myapp/app.log"
          recursive: false
          direction: "remotetolocal"

        # Upload directory recursively
        - name: upload_website
          module: oa-system
          function: scp
          remoteserver: "web-server"
          remoteuser: "www-data"
          remotepassword: "{VAULT:web_pass}"
          remoteport: 22
          localpath: "/local/website/*"
          remotepath: "/var/www/html/"
          recursive: true
          direction: "localtoremote"

        # Download backup with credentials from wallet
        - name: download_backup
          module: oa-system
          function: scp
          remoteserver: "{ENV:BACKUP_SERVER}"
          remoteuser: "{WALLET:backup_user}"
          remotepassword: "{VAULT:backup_pass}"
          remoteport: 22
          localpath: "/local/backups/db-backup.sql.gz"
          remotepath: "/backups/database/latest.sql.gz"
          recursive: false
          direction: "remotetolocal"

        # Multiple file transfer
        - name: sync_configs
          module: oa-system
          function: scp
          remoteserver: "app-server"
          remoteuser: "deployer"
          remotepassword: "{VAULT:deploy_pass}"
          remoteport: 22
          localpath:
            - "/local/config1.yml"
            - "/local/config2.yml"
            - "/local/config3.yml"
          remotepath:
            - "/etc/app/config1.yml"
            - "/etc/app/config2.yml"
            - "/etc/app/config3.yml"
          recursive: false
          direction: "localtoremote"

        # Upload from previous task output
        - name: upload_generated_file
          module: oa-system
          function: scp
          remoteserver: "server-01"
          remoteuser: "admin"
          remotepassword: "{VAULT:ssh_pass}"
          remoteport: 22
          # localpath from previous task (e.g., writetofile output)
          remotepath: "/opt/data/uploaded.txt"
          recursive: false
          direction: "localtoremote"

        # Backup entire directory
        - name: backup_directory
          module: oa-system
          function: scp
          remoteserver: "{ENV:BACKUP_HOST}"
          remoteuser: "backup"
          remotepassword: "{VAULT:backup_password}"
          remoteport: 22
          localpath: "/backup/$(date +%Y%m%d)"
          remotepath: "/var/backups/myapp/"
          recursive: true
          direction: "remotetolocal"
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
        # If localpath not specified, use input from previous task
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders (CRITICAL for SSH password!)
        remoteserver = oacommon.get_param(param, 'remoteserver', wallet) or gdict.get('remoteserver')
        remoteuser = oacommon.get_param(param, 'remoteuser', wallet) or gdict.get('remoteuser')
        remotepassword = oacommon.get_param(param, 'remotepassword', wallet) or gdict.get('remotepassword')
        remoteport = oacommon.get_param(param, 'remoteport', wallet) or gdict.get('remoteport')
        direction = gdict['direction']
        recursive = gdict['recursive']

        # Multi-path handling with placeholder support
        localpath_param = gdict['localpath']
        remotepath_param = gdict['remotepath']

        # Resolve placeholders for localpath
        if isinstance(localpath_param, list):
            localpath = [oacommon.get_param({'path': p}, 'path', wallet) or p for p in localpath_param]
        else:
            localpath = oacommon.get_param(param, 'localpath', wallet) or localpath_param

        # Resolve placeholders for remotepath
        if isinstance(remotepath_param, list):
            remotepath = [oacommon.get_param({'path': p}, 'path', wallet) or p for p in remotepath_param]
        else:
            remotepath = oacommon.get_param(param, 'remotepath', wallet) or remotepath_param

        logger.info(f"Direction: {direction} | Target: {remoteuser}@{remoteserver}:{remoteport}")
        logger.debug(f"Local: {localpath} | Remote: {remotepath} | Recursive: {recursive}")

        ismultipath = False
        lres = []
        files_transferred = 0

        # Multi-path validation
        if isinstance(localpath, list) and isinstance(remotepath, list):
            if len(localpath) != len(remotepath):
                raise ValueError("Multipath: local and remote path lists must have same length")

            res = ','.join([f"{l}|{r}" for l, r in zip(localpath, remotepath)])
            lres = res.split(',')
            ismultipath = True
            logger.info(f"Multipath transfer: {len(localpath)} file(s)")

        elif isinstance(localpath, list) or isinstance(remotepath, list):
            raise ValueError("If one path is a list, both must be lists")

        # SSH connection
        ssh = oacommon.createSSHClient(remoteserver, remoteport, remoteuser, remotepassword)
        scp_client = SCPClient(ssh.get_transport())

        # Execute transfer
        if 'localtoremote' in direction:
            if ismultipath:
                for i, res in enumerate(lres, 1):
                    lp, rp = res.split('|')
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
                    logger.debug(f"[{i}/{len(lres)}] Downloading: {rp} -> {lp}")
                    scp_client.get(remote_path=rp, local_path=lp, recursive=recursive)
                    files_transferred += 1
            else:
                logger.debug(f"Downloading: {remotepath} -> {localpath}")
                scp_client.get(remote_path=remotepath, local_path=localpath, recursive=recursive)
                files_transferred = 1

        logger.info(f"SCP transfer completed successfully: {files_transferred} transfer(s)")

        # Output data for propagation
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
    Executes a local script and propagates output

    Args:
        param: dict with:
            - script_path: script path (can use input from previous task) - supports {WALLET:key}, {ENV:var}
            - args: (optional) list of arguments - supports {WALLET:key}, {ENV:var}
            - interpreter: (optional) interpreter (e.g., 'python3', 'bash'), default auto-detect
            - timeout: (optional) timeout in seconds
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with script output

    Example YAML:
        # Execute Python script
        - name: run_data_processor
          module: oa-system
          function: execute_script
          script_path: "/opt/scripts/process_data.py"
          interpreter: "python3"

        # Execute bash script with arguments
        - name: run_backup_script
          module: oa-system
          function: execute_script
          script_path: "/home/admin/backup.sh"
          args:
            - "/var/lib/myapp"
            - "/backup/$(date +%Y%m%d)"
          interpreter: "bash"

        # Auto-detect interpreter from extension
        - name: run_perl_script
          module: oa-system
          function: execute_script
          script_path: "/scripts/monitor.pl"
          # .pl extension auto-detects perl interpreter

        # Script with arguments from wallet
        - name: deploy_with_credentials
          module: oa-system
          function: execute_script
          script_path: "/opt/deploy.sh"
          args:
            - "{ENV:ENVIRONMENT}"
            - "{WALLET:deploy_key}"
            - "{VAULT:db_password}"
          interpreter: "bash"

        # Execute script with timeout
        - name: long_running_script
          module: oa-system
          function: execute_script
          script_path: "/scripts/import_data.py"
          interpreter: "python3"
          timeout: 600

        # Script path from previous task
        - name: run_generated_script
          module: oa-system
          function: execute_script
          # script_path from previous writetofile task
          interpreter: "bash"

        # Node.js script
        - name: run_node_script
          module: oa-system
          function: execute_script
          script_path: "/app/server.js"
          args:
            - "--port"
            - "3000"
          interpreter: "node"

        # Ruby script with environment variables
        - name: run_ruby_app
          module: oa-system
          function: execute_script
          script_path: "{ENV:APP_DIR}/app.rb"
          args:
            - "production"
          interpreter: "ruby"

        # Execute without interpreter (script with shebang)
        - name: run_executable
          module: oa-system
          function: execute_script
          script_path: "/usr/local/bin/custom_tool"
          args:
            - "--config"
            - "/etc/tool.conf"

    Note: Supported auto-detect extensions:
        - .py  -> python3
        - .sh  -> bash
        - .rb  -> ruby
        - .js  -> node
        - .pl  -> perl
    """
    func_name = myself()
    logger.info("Executing local script")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # If script_path not specified, use input
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        script_path = oacommon.get_param(param, 'script_path', wallet) or gdict.get('script_path')

        # Args with placeholder support
        args = param.get("args", [])
        if isinstance(args, list):
            resolved_args = []
            for arg in args:
                if isinstance(arg, str):
                    resolved_arg = oacommon.get_param({'arg': arg}, 'arg', wallet) or arg
                    resolved_args.append(resolved_arg)
                else:
                    resolved_args.append(arg)
            args = resolved_args

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

        # Build command
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
