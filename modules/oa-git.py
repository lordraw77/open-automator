"""
Open-Automator Git Module
Gestisce operazioni Git (clone, pull, push, tag, branch) con data propagation
"""

import oacommon
import inspect
import subprocess
import os
import logging
from logger_config import AutomatorLogger

# Logger per questo modulo
logger = AutomatorLogger.get_logger('oa-git')

gdict = {}
myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdict_param):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param


def run_git_command(command, cwd=None, timeout=300):
    """
    Helper per eseguire comandi git
    
    Args:
        command: lista con comando git e argomenti
        cwd: directory di lavoro
        timeout: timeout in secondi
    
    Returns:
        tuple: (success, stdout, stderr, return_code)
    """
    try:
        logger.debug(f"Running git command: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True
        )
        
        success = result.returncode == 0
        return success, result.stdout, result.stderr, result.returncode
    
    except subprocess.TimeoutExpired as e:
        logger.error(f"Git command timeout after {timeout}s")
        return False, "", f"Timeout after {timeout}s", -1
    except Exception as e:
        logger.error(f"Git command failed: {e}")
        return False, "", str(e), -1


@oacommon.trace
def clone(self, param):
    """
    Clona un repository Git con data propagation

    Args:
        param: dict con:
            - repo_url: URL del repository (https o ssh)
            - dest_path: path di destinazione locale
            - branch: (opzionale) branch specifico da clonare
            - depth: (opzionale) clone shallow con depth specificato
            - recursive: (opzionale) clone ricorsivo dei submodules, default False
            - username: (opzionale) username per HTTPS auth
            - password: (opzionale) password/token per HTTPS auth
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con info sul clone
    """
    func_name = myself()
    logger.info("Git clone operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    required_params = ['repo_url', 'dest_path']

    try:
        # Se repo_url non è specificato, usa input
        if 'repo_url' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'repo_url' in prev_input:
                param['repo_url'] = prev_input['repo_url']
                logger.info("Using repo_url from previous task")
        
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        repo_url = oacommon.effify(gdict['repo_url'])
        dest_path = oacommon.effify(gdict['dest_path'])
        branch = param.get('branch')
        depth = param.get('depth')
        recursive = param.get('recursive', False)
        username = param.get('username')
        password = param.get('password')

        logger.info(f"Cloning repository: {repo_url}")
        logger.info(f"Destination: {dest_path}")

        # Verifica che la destinazione non esista già
        if os.path.exists(dest_path):
            raise ValueError(f"Destination path already exists: {dest_path}")

        # Costruisci URL con autenticazione se fornita
        clone_url = repo_url
        if username and password and repo_url.startswith('https://'):
            # Inserisci credenziali nell'URL
            clone_url = repo_url.replace('https://', f'https://{username}:{password}@')
            logger.debug("Using HTTPS authentication")

        # Costruisci comando git clone
        command = ['git', 'clone']
        
        if branch:
            command.extend(['-b', branch])
            logger.debug(f"Branch: {branch}")
        
        if depth:
            command.extend(['--depth', str(depth)])
            logger.debug(f"Shallow clone depth: {depth}")
        
        if recursive:
            command.append('--recursive')
            logger.debug("Recursive submodule clone enabled")
        
        command.extend([clone_url, dest_path])

        # Esegui clone
        success, stdout, stderr, return_code = run_git_command(
            command, 
            timeout=param.get('timeout', 600)
        )

        if not success:
            task_success = False
            error_msg = f"Git clone failed: {stderr}"
            logger.error(error_msg)
        else:
            logger.info("Git clone completed successfully")
            if stdout:
                logger.debug(f"Git output: {stdout}")

        # Output data per propagation
        output_data = {
            'repo_url': repo_url,
            'dest_path': os.path.abspath(dest_path),
            'branch': branch,
            'depth': depth,
            'recursive': recursive,
            'stdout': stdout,
            'stderr': stderr,
            'return_code': return_code
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Git clone failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def pull(self, param):
    """
    Esegue git pull su un repository esistente con data propagation

    Args:
        param: dict con:
            - repo_path: path del repository locale
            - branch: (opzionale) branch da pullare
            - rebase: (opzionale) usa rebase invece di merge, default False
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con info sul pull
    """
    func_name = myself()
    logger.info("Git pull operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se repo_path non è specificato, usa input
        if 'repo_path' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'dest_path' in prev_input:
                    param['repo_path'] = prev_input['dest_path']
                elif 'repo_path' in prev_input:
                    param['repo_path'] = prev_input['repo_path']
                logger.info("Using repo_path from previous task")
        
        if not oacommon.checkandloadparam(self, myself, 'repo_path', param=param):
            raise ValueError(f"Missing required parameter 'repo_path' for {func_name}")

        repo_path = oacommon.effify(gdict['repo_path'])
        branch = param.get('branch')
        rebase = param.get('rebase', False)

        logger.info(f"Pulling repository: {repo_path}")

        # Verifica che sia un repository git
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise ValueError(f"Not a git repository: {repo_path}")

        # Costruisci comando git pull
        command = ['git', 'pull']
        
        if rebase:
            command.append('--rebase')
            logger.debug("Using rebase mode")
        
        if branch:
            command.extend(['origin', branch])
            logger.debug(f"Branch: {branch}")

        # Esegui pull
        success, stdout, stderr, return_code = run_git_command(
            command, 
            cwd=repo_path,
            timeout=param.get('timeout', 300)
        )

        if not success:
            task_success = False
            error_msg = f"Git pull failed: {stderr}"
            logger.error(error_msg)
        else:
            logger.info("Git pull completed successfully")
            logger.info(f"Pull output: {stdout.strip()}")

        # Ottieni info sul commit corrente
        commit_success, commit_hash, _, _ = run_git_command(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path
        )

        # Output data per propagation
        output_data = {
            'repo_path': os.path.abspath(repo_path),
            'branch': branch,
            'rebase': rebase,
            'commit_hash': commit_hash.strip() if commit_success else None,
            'stdout': stdout,
            'stderr': stderr,
            'return_code': return_code,
            'changes_pulled': 'Already up to date' not in stdout
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Git pull failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def push(self, param):
    """
    Esegue git push con data propagation

    Args:
        param: dict con:
            - repo_path: path del repository locale
            - branch: (opzionale) branch da pushare
            - remote: (opzionale) remote name, default 'origin'
            - force: (opzionale) force push, default False
            - tags: (opzionale) push tags, default False
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con info sul push
    """
    func_name = myself()
    logger.info("Git push operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se repo_path non è specificato, usa input
        if 'repo_path' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict):
                if 'repo_path' in prev_input:
                    param['repo_path'] = prev_input['repo_path']
                elif 'dest_path' in prev_input:
                    param['repo_path'] = prev_input['dest_path']
                logger.info("Using repo_path from previous task")
        
        if not oacommon.checkandloadparam(self, myself, 'repo_path', param=param):
            raise ValueError(f"Missing required parameter 'repo_path' for {func_name}")

        repo_path = oacommon.effify(gdict['repo_path'])
        branch = param.get('branch')
        remote = param.get('remote', 'origin')
        force = param.get('force', False)
        push_tags = param.get('tags', False)

        logger.info(f"Pushing repository: {repo_path}")

        # Verifica che sia un repository git
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise ValueError(f"Not a git repository: {repo_path}")

        # Costruisci comando git push
        command = ['git', 'push']
        
        if force:
            command.append('--force')
            logger.warning("Force push enabled")
        
        if push_tags:
            command.append('--tags')
            logger.debug("Pushing tags")
        
        command.append(remote)
        
        if branch:
            command.append(branch)
            logger.debug(f"Branch: {branch}")

        # Esegui push
        success, stdout, stderr, return_code = run_git_command(
            command, 
            cwd=repo_path,
            timeout=param.get('timeout', 300)
        )

        if not success:
            task_success = False
            error_msg = f"Git push failed: {stderr}"
            logger.error(error_msg)
        else:
            logger.info("Git push completed successfully")
            # Git push output va su stderr anche in caso di successo
            if stderr:
                logger.info(f"Push output: {stderr.strip()}")

        # Output data per propagation
        output_data = {
            'repo_path': os.path.abspath(repo_path),
            'branch': branch,
            'remote': remote,
            'force': force,
            'tags_pushed': push_tags,
            'stdout': stdout,
            'stderr': stderr,
            'return_code': return_code
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Git push failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def tag(self, param):
    """
    Crea, lista o elimina tag Git con data propagation

    Args:
        param: dict con:
            - repo_path: path del repository locale
            - operation: 'create'|'list'|'delete'
            - tag_name: (opzionale) nome del tag (per create/delete)
            - message: (opzionale) messaggio del tag annotato
            - commit: (opzionale) commit su cui creare il tag
            - push: (opzionale) push del tag dopo creazione, default False
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con info sui tag
    """
    func_name = myself()
    logger.info("Git tag operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se repo_path non è specificato, usa input
        if 'repo_path' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'repo_path' in prev_input:
                param['repo_path'] = prev_input['repo_path']
                logger.info("Using repo_path from previous task")
        
        required_params = ['repo_path', 'operation']
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        repo_path = oacommon.effify(gdict['repo_path'])
        operation = gdict['operation']
        tag_name = param.get('tag_name')
        message = param.get('message')
        commit = param.get('commit')
        push_tag = param.get('push', False)

        logger.info(f"Git tag operation: {operation}")

        # Verifica che sia un repository git
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise ValueError(f"Not a git repository: {repo_path}")

        if operation == 'create':
            if not tag_name:
                raise ValueError("tag_name required for create operation")
            
            # Costruisci comando git tag
            command = ['git', 'tag']
            
            if message:
                command.extend(['-a', tag_name, '-m', message])
                logger.debug(f"Creating annotated tag: {tag_name}")
            else:
                command.append(tag_name)
                logger.debug(f"Creating lightweight tag: {tag_name}")
            
            if commit:
                command.append(commit)
                logger.debug(f"On commit: {commit}")
            
            # Crea tag
            success, stdout, stderr, return_code = run_git_command(
                command, 
                cwd=repo_path
            )
            
            if not success:
                task_success = False
                error_msg = f"Git tag create failed: {stderr}"
                logger.error(error_msg)
            else:
                logger.info(f"Tag '{tag_name}' created successfully")
                
                # Push del tag se richiesto
                if push_tag:
                    push_success, push_stdout, push_stderr, _ = run_git_command(
                        ['git', 'push', 'origin', tag_name],
                        cwd=repo_path
                    )
                    if push_success:
                        logger.info(f"Tag '{tag_name}' pushed to remote")
                    else:
                        logger.warning(f"Tag created but push failed: {push_stderr}")
            
            output_data = {
                'operation': 'create',
                'tag_name': tag_name,
                'message': message,
                'commit': commit,
                'pushed': push_tag and success,
                'repo_path': os.path.abspath(repo_path)
            }
        
        elif operation == 'list':
            # Lista tutti i tag
            command = ['git', 'tag', '-l']
            
            success, stdout, stderr, return_code = run_git_command(
                command, 
                cwd=repo_path
            )
            
            if not success:
                task_success = False
                error_msg = f"Git tag list failed: {stderr}"
                logger.error(error_msg)
            else:
                tags = [t.strip() for t in stdout.split('\n') if t.strip()]
                logger.info(f"Found {len(tags)} tag(s)")
                if tags:
                    logger.info(f"Tags: {', '.join(tags[:10])}" + 
                              (f" ... (+{len(tags)-10} more)" if len(tags) > 10 else ""))
            
            output_data = {
                'operation': 'list',
                'tags': tags if success else [],
                'tag_count': len(tags) if success else 0,
                'repo_path': os.path.abspath(repo_path)
            }
        
        elif operation == 'delete':
            if not tag_name:
                raise ValueError("tag_name required for delete operation")
            
            # Elimina tag locale
            command = ['git', 'tag', '-d', tag_name]
            
            success, stdout, stderr, return_code = run_git_command(
                command, 
                cwd=repo_path
            )
            
            if not success:
                task_success = False
                error_msg = f"Git tag delete failed: {stderr}"
                logger.error(error_msg)
            else:
                logger.info(f"Tag '{tag_name}' deleted locally")
                
                # Elimina tag remoto se richiesto
                if push_tag:
                    push_success, push_stdout, push_stderr, _ = run_git_command(
                        ['git', 'push', 'origin', f':refs/tags/{tag_name}'],
                        cwd=repo_path
                    )
                    if push_success:
                        logger.info(f"Tag '{tag_name}' deleted from remote")
                    else:
                        logger.warning(f"Tag deleted locally but remote delete failed: {push_stderr}")
            
            output_data = {
                'operation': 'delete',
                'tag_name': tag_name,
                'deleted_remote': push_tag and success,
                'repo_path': os.path.abspath(repo_path)
            }
        
        else:
            raise ValueError(f"Invalid operation: {operation}. Use 'create', 'list', or 'delete'")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Git tag operation failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def branch(self, param):
    """
    Gestisce branch Git (crea, lista, elimina, checkout) con data propagation

    Args:
        param: dict con:
            - repo_path: path del repository locale
            - operation: 'create'|'list'|'delete'|'checkout'
            - branch_name: (opzionale) nome del branch (per create/delete/checkout)
            - from_branch: (opzionale) branch/commit sorgente per create
            - force: (opzionale) force delete, default False
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con info sui branch
    """
    func_name = myself()
    logger.info("Git branch operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # Se repo_path non è specificato, usa input
        if 'repo_path' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'repo_path' in prev_input:
                param['repo_path'] = prev_input['repo_path']
                logger.info("Using repo_path from previous task")
        
        required_params = ['repo_path', 'operation']
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        repo_path = oacommon.effify(gdict['repo_path'])
        operation = gdict['operation']
        branch_name = param.get('branch_name')
        from_branch = param.get('from_branch')
        force = param.get('force', False)

        logger.info(f"Git branch operation: {operation}")

        # Verifica che sia un repository git
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise ValueError(f"Not a git repository: {repo_path}")

        if operation == 'create':
            if not branch_name:
                raise ValueError("branch_name required for create operation")
            
            # Costruisci comando git branch
            command = ['git', 'branch', branch_name]
            
            if from_branch:
                command.append(from_branch)
                logger.debug(f"Creating branch '{branch_name}' from '{from_branch}'")
            else:
                logger.debug(f"Creating branch '{branch_name}' from current HEAD")
            
            # Crea branch
            success, stdout, stderr, return_code = run_git_command(
                command, 
                cwd=repo_path
            )
            
            if not success:
                task_success = False
                error_msg = f"Git branch create failed: {stderr}"
                logger.error(error_msg)
            else:
                logger.info(f"Branch '{branch_name}' created successfully")
            
            output_data = {
                'operation': 'create',
                'branch_name': branch_name,
                'from_branch': from_branch,
                'repo_path': os.path.abspath(repo_path)
            }
        
        elif operation == 'list':
            # Lista tutti i branch
            command = ['git', 'branch', '-a']
            
            success, stdout, stderr, return_code = run_git_command(
                command, 
                cwd=repo_path
            )
            
            if not success:
                task_success = False
                error_msg = f"Git branch list failed: {stderr}"
                logger.error(error_msg)
            else:
                branches = [b.strip().replace('* ', '') for b in stdout.split('\n') if b.strip()]
                current_branch = next((b.replace('* ', '') for b in stdout.split('\n') if b.startswith('*')), None)
                
                logger.info(f"Found {len(branches)} branch(es)")
                logger.info(f"Current branch: {current_branch}")
                if branches:
                    logger.debug(f"Branches: {', '.join(branches[:10])}" + 
                               (f" ... (+{len(branches)-10} more)" if len(branches) > 10 else ""))
            
            output_data = {
                'operation': 'list',
                'branches': branches if success else [],
                'current_branch': current_branch if success else None,
                'branch_count': len(branches) if success else 0,
                'repo_path': os.path.abspath(repo_path)
            }
        
        elif operation == 'delete':
            if not branch_name:
                raise ValueError("branch_name required for delete operation")
            
            # Elimina branch
            command = ['git', 'branch']
            if force:
                command.append('-D')
                logger.warning(f"Force deleting branch '{branch_name}'")
            else:
                command.append('-d')
                logger.debug(f"Deleting branch '{branch_name}'")
            
            command.append(branch_name)
            
            success, stdout, stderr, return_code = run_git_command(
                command, 
                cwd=repo_path
            )
            
            if not success:
                task_success = False
                error_msg = f"Git branch delete failed: {stderr}"
                logger.error(error_msg)
            else:
                logger.info(f"Branch '{branch_name}' deleted successfully")
            
            output_data = {
                'operation': 'delete',
                'branch_name': branch_name,
                'force': force,
                'repo_path': os.path.abspath(repo_path)
            }
        
        elif operation == 'checkout':
            if not branch_name:
                raise ValueError("branch_name required for checkout operation")
            
            # Checkout branch
            command = ['git', 'checkout', branch_name]
            
            logger.debug(f"Checking out branch '{branch_name}'")
            
            success, stdout, stderr, return_code = run_git_command(
                command, 
                cwd=repo_path
            )
            
            if not success:
                task_success = False
                error_msg = f"Git checkout failed: {stderr}"
                logger.error(error_msg)
            else:
                logger.info(f"Checked out branch '{branch_name}'")
                logger.info(f"Checkout output: {stderr.strip()}")
            
            output_data = {
                'operation': 'checkout',
                'branch_name': branch_name,
                'repo_path': os.path.abspath(repo_path)
            }
        
        else:
            raise ValueError(f"Invalid operation: {operation}. Use 'create', 'list', 'delete', or 'checkout'")

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Git branch operation failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data


@oacommon.trace
def status(self, param):
    """
    Ottiene lo status del repository Git con data propagation

    Args:
        param: dict con:
            - repo_path: path del repository locale
            - short: (opzionale) formato short, default False
            - input: (opzionale) dati dal task precedente
            - workflow_context: (opzionale) contesto workflow
            - task_id: (opzionale) id univoco del task
            - task_store: (opzionale) istanza di TaskResultStore
    
    Returns:
        tuple: (success, output_dict) con status info
    """
    func_name = myself()
    logger.info("Git status operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        if 'repo_path' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'repo_path' in prev_input:
                param['repo_path'] = prev_input['repo_path']
        
        if not oacommon.checkandloadparam(self, myself, 'repo_path', param=param):
            raise ValueError(f"Missing required parameter 'repo_path' for {func_name}")

        repo_path = oacommon.effify(gdict['repo_path'])
        short_format = param.get('short', False)

        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise ValueError(f"Not a git repository: {repo_path}")

        command = ['git', 'status']
        if short_format:
            command.append('--short')

        success, stdout, stderr, return_code = run_git_command(command, cwd=repo_path)

        if not success:
            task_success = False
            error_msg = f"Git status failed: {stderr}"
            logger.error(error_msg)
        else:
            logger.info("Git status retrieved successfully")
            logger.info(f"Status:\n{stdout}")
            
            # Verifica se ci sono modifiche
            has_changes = bool(stdout.strip()) and 'nothing to commit' not in stdout

        output_data = {
            'repo_path': os.path.abspath(repo_path),
            'status': stdout,
            'has_changes': has_changes if success else None,
            'clean': not has_changes if success else None
        }

    except Exception as e:
        task_success = False
        error_msg = str(e)
        logger.error(f"Git status failed: {e}", exc_info=True)
    finally:
        if task_store and task_id:
            task_store.set_result(task_id, task_success, error_msg)

    return task_success, output_data
