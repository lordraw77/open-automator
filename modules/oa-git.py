"""
Open-Automator Git Module

Manages Git operations (clone, pull, push, tag, branch, status) with data propagation
Support for wallet, placeholder {WALLET:key}, {ENV:var} and {VAULT:key}
"""

import oacommon
import inspect
import subprocess
import os
import logging
from logger_config import AutomatorLogger

# Logger for this module
logger = AutomatorLogger.get_logger('oa-git')

gdict = {}
myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdict_param):
    """Sets the global dictionary"""
    global gdict
    gdict = gdict_param
    self.gdict = gdict_param

def run_git_command(command, cwd=None, timeout=300):
    """
    Helper to execute git commands

    Args:
        command: list with git command and arguments
        cwd: working directory
        timeout: timeout in seconds

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
    Clones a Git repository with data propagation

    Args:
        param: dict with:
            - repo_url: repository URL (https or ssh) - supports {WALLET:key}, {ENV:var}
            - dest_path: local destination path
            - branch: (optional) specific branch to clone
            - depth: (optional) shallow clone with specified depth
            - recursive: (optional) recursive submodule clone, default False
            - username: (optional) username for HTTPS auth - supports {WALLET:key}, {ENV:var}
            - password: (optional) password/token for HTTPS auth - supports {WALLET:key}, {ENV:var}
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with clone info

    Example YAML:
        # Clone public repository
        - name: clone_public_repo
          module: oa-git
          function: clone
          repo_url: "https://github.com/user/project.git"
          dest_path: "/workspace/project"

        # Clone specific branch with shallow depth
        - name: clone_develop_branch
          module: oa-git
          function: clone
          repo_url: "https://github.com/company/app.git"
          dest_path: "/tmp/app"
          branch: "develop"
          depth: 1

        # Clone private repo with authentication from wallet
        - name: clone_private
          module: oa-git
          function: clone
          repo_url: "https://github.com/company/private.git"
          dest_path: "/secure/repo"
          username: "{WALLET:git_username}"
          password: "{VAULT:git_token}"

        # Clone with recursive submodules
        - name: clone_with_submodules
          module: oa-git
          function: clone
          repo_url: "{ENV:REPO_URL}"
          dest_path: "/workspace/main"
          recursive: true
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
        # If repo_url not specified, use input
        if 'repo_url' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'repo_url' in prev_input:
                param['repo_url'] = prev_input['repo_url']
                logger.info("Using repo_url from previous task")

        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support WALLET/ENV placeholders
        repo_url = oacommon.get_param(param, 'repo_url', wallet) or gdict.get('repo_url')
        dest_path = oacommon.get_param(param, 'dest_path', wallet) or gdict.get('dest_path')
        branch = oacommon.get_param(param, 'branch', wallet)
        depth = param.get('depth')
        recursive = param.get('recursive', False)
        username = oacommon.get_param(param, 'username', wallet)
        password = oacommon.get_param(param, 'password', wallet)

        logger.info(f"Cloning repository: {repo_url}")
        logger.info(f"Destination: {dest_path}")

        # Verify destination doesn't already exist
        if os.path.exists(dest_path):
            raise ValueError(f"Destination path already exists: {dest_path}")

        # Build URL with authentication if provided
        clone_url = repo_url
        if username and password and repo_url.startswith('https://'):
            # Insert credentials in URL
            clone_url = repo_url.replace('https://', f'https://{username}:{password}@')
            logger.debug("Using HTTPS authentication (credentials from wallet/env)")

        # Build git clone command
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

        # Execute clone
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

        # Output data for propagation
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
    Executes git pull on an existing repository with data propagation

    Args:
        param: dict with:
            - repo_path: local repository path - supports {ENV:var}
            - branch: (optional) branch to pull
            - rebase: (optional) use rebase instead of merge, default False
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with pull info

    Example YAML:
        # Simple pull
        - name: update_repo
          module: oa-git
          function: pull
          repo_path: "/workspace/myproject"

        # Pull specific branch with rebase
        - name: pull_main_rebase
          module: oa-git
          function: pull
          repo_path: "{ENV:PROJECT_DIR}"
          branch: "main"
          rebase: true

        # Pull from previous clone task
        - name: pull_updates
          module: oa-git
          function: pull
          # repo_path comes from previous clone task
    """
    func_name = myself()
    logger.info("Git pull operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # If repo_path not specified, use input
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        repo_path = oacommon.get_param(param, 'repo_path', wallet) or gdict.get('repo_path')
        branch = oacommon.get_param(param, 'branch', wallet)
        rebase = param.get('rebase', False)

        logger.info(f"Pulling repository: {repo_path}")

        # Verify it's a git repository
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise ValueError(f"Not a git repository: {repo_path}")

        # Build git pull command
        command = ['git', 'pull']

        if rebase:
            command.append('--rebase')
            logger.debug("Using rebase mode")

        if branch:
            command.extend(['origin', branch])
            logger.debug(f"Branch: {branch}")

        # Execute pull
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

        # Get current commit info
        commit_success, commit_hash, _, _ = run_git_command(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path
        )

        # Output data for propagation
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
    Executes git push with data propagation

    Args:
        param: dict with:
            - repo_path: local repository path - supports {ENV:var}
            - branch: (optional) branch to push
            - remote: (optional) remote name, default 'origin'
            - force: (optional) force push, default False
            - tags: (optional) push tags, default False
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with push info

    Example YAML:
        # Simple push to origin
        - name: push_changes
          module: oa-git
          function: push
          repo_path: "/workspace/myproject"
          branch: "main"

        # Force push (use with caution!)
        - name: force_push
          module: oa-git
          function: push
          repo_path: "{ENV:REPO_PATH}"
          branch: "feature-branch"
          force: true

        # Push with tags
        - name: push_with_tags
          module: oa-git
          function: push
          repo_path: "/workspace/app"
          tags: true

        # Push to specific remote
        - name: push_to_backup
          module: oa-git
          function: push
          repo_path: "/workspace/repo"
          remote: "backup"
          branch: "main"
    """
    func_name = myself()
    logger.info("Git push operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # If repo_path not specified, use input
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        repo_path = oacommon.get_param(param, 'repo_path', wallet) or gdict.get('repo_path')
        branch = oacommon.get_param(param, 'branch', wallet)
        remote = oacommon.get_param(param, 'remote', wallet) or param.get('remote', 'origin')
        force = param.get('force', False)
        push_tags = param.get('tags', False)

        logger.info(f"Pushing repository: {repo_path}")

        # Verify it's a git repository
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise ValueError(f"Not a git repository: {repo_path}")

        # Build git push command
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

        # Execute push
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
            # Git push output goes to stderr even on success
            if stderr:
                logger.info(f"Push output: {stderr.strip()}")

        # Output data for propagation
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
    Creates, lists, or deletes Git tags with data propagation

    Args:
        param: dict with:
            - repo_path: local repository path - supports {ENV:var}
            - operation: 'create'|'list'|'delete'
            - tag_name: (optional) tag name (for create/delete) - supports {ENV:var}
            - message: (optional) message for annotated tag
            - commit: (optional) commit to tag
            - push: (optional) push tag after creation, default False
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with tag info

    Example YAML:
        # Create lightweight tag
        - name: create_tag
          module: oa-git
          function: tag
          repo_path: "/workspace/project"
          operation: create
          tag_name: "v1.0.0"

        # Create annotated tag with message
        - name: create_release_tag
          module: oa-git
          function: tag
          repo_path: "{ENV:REPO_PATH}"
          operation: create
          tag_name: "v2.0.0"
          message: "Release version 2.0.0"
          push: true

        # List all tags
        - name: list_tags
          module: oa-git
          function: tag
          repo_path: "/workspace/project"
          operation: list

        # Delete tag locally and remotely
        - name: delete_tag
          module: oa-git
          function: tag
          repo_path: "/workspace/project"
          operation: delete
          tag_name: "old-tag"
          push: true
    """
    func_name = myself()
    logger.info("Git tag operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # If repo_path not specified, use input
        if 'repo_path' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'repo_path' in prev_input:
                param['repo_path'] = prev_input['repo_path']
                logger.info("Using repo_path from previous task")

        required_params = ['repo_path', 'operation']
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        repo_path = oacommon.get_param(param, 'repo_path', wallet) or gdict.get('repo_path')
        operation = oacommon.get_param(param, 'operation', wallet) or gdict.get('operation')
        tag_name = oacommon.get_param(param, 'tag_name', wallet)
        message = oacommon.get_param(param, 'message', wallet)
        commit = oacommon.get_param(param, 'commit', wallet)
        push_tag = param.get('push', False)

        logger.info(f"Git tag operation: {operation}")

        # Verify it's a git repository
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise ValueError(f"Not a git repository: {repo_path}")

        if operation == 'create':
            if not tag_name:
                raise ValueError("tag_name required for create operation")

            # Build git tag command
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

            # Create tag
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

                # Push tag if requested
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
            # List all tags
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

            # Delete local tag
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

                # Delete remote tag if requested
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
    Manages Git branches (create, list, delete, checkout) with data propagation

    Args:
        param: dict with:
            - repo_path: local repository path - supports {ENV:var}
            - operation: 'create'|'list'|'delete'|'checkout'
            - branch_name: (optional) branch name (for create/delete/checkout) - supports {ENV:var}
            - from_branch: (optional) source branch/commit for create
            - force: (optional) force delete, default False
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with branch info

    Example YAML:
        # Create new branch
        - name: create_feature_branch
          module: oa-git
          function: branch
          repo_path: "/workspace/project"
          operation: create
          branch_name: "feature/new-feature"

        # Create branch from specific commit
        - name: create_from_commit
          module: oa-git
          function: branch
          repo_path: "{ENV:REPO_PATH}"
          operation: create
          branch_name: "hotfix/bug-123"
          from_branch: "main"

        # List all branches
        - name: list_branches
          module: oa-git
          function: branch
          repo_path: "/workspace/project"
          operation: list

        # Checkout branch
        - name: switch_to_develop
          module: oa-git
          function: branch
          repo_path: "/workspace/project"
          operation: checkout
          branch_name: "develop"

        # Delete branch (force)
        - name: delete_old_branch
          module: oa-git
          function: branch
          repo_path: "/workspace/project"
          operation: delete
          branch_name: "old-feature"
          force: true
    """
    func_name = myself()
    logger.info("Git branch operation")

    task_id = param.get("task_id")
    task_store = param.get("task_store")
    task_success = True
    error_msg = ""
    output_data = None

    try:
        # If repo_path not specified, use input
        if 'repo_path' not in param and 'input' in param:
            prev_input = param.get('input')
            if isinstance(prev_input, dict) and 'repo_path' in prev_input:
                param['repo_path'] = prev_input['repo_path']
                logger.info("Using repo_path from previous task")

        required_params = ['repo_path', 'operation']
        if not oacommon.checkandloadparam(self, myself, *required_params, param=param):
            raise ValueError(f"Missing required parameters for {func_name}")

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        repo_path = oacommon.get_param(param, 'repo_path', wallet) or gdict.get('repo_path')
        operation = oacommon.get_param(param, 'operation', wallet) or gdict.get('operation')
        branch_name = oacommon.get_param(param, 'branch_name', wallet)
        from_branch = oacommon.get_param(param, 'from_branch', wallet)
        force = param.get('force', False)

        logger.info(f"Git branch operation: {operation}")

        # Verify it's a git repository
        if not os.path.exists(os.path.join(repo_path, '.git')):
            raise ValueError(f"Not a git repository: {repo_path}")

        if operation == 'create':
            if not branch_name:
                raise ValueError("branch_name required for create operation")

            # Build git branch command
            command = ['git', 'branch', branch_name]

            if from_branch:
                command.append(from_branch)
                logger.debug(f"Creating branch '{branch_name}' from '{from_branch}'")
            else:
                logger.debug(f"Creating branch '{branch_name}' from current HEAD")

            # Create branch
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
            # List all branches
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

            # Delete branch
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
    Gets the Git repository status with data propagation

    Args:
        param: dict with:
            - repo_path: local repository path - supports {ENV:var}
            - short: (optional) short format, default False
            - input: (optional) data from previous task
            - workflow_context: (optional) workflow context
            - task_id: (optional) unique task id
            - task_store: (optional) TaskResultStore instance

    Returns:
        tuple: (success, output_dict) with status info

    Example YAML:
        # Get full status
        - name: check_status
          module: oa-git
          function: status
          repo_path: "/workspace/project"

        # Get short status
        - name: quick_status
          module: oa-git
          function: status
          repo_path: "{ENV:REPO_PATH}"
          short: true

        # Check status from previous task
        - name: verify_clean
          module: oa-git
          function: status
          # repo_path from previous clone/pull task
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

        # Get wallet for placeholder resolution
        wallet = gdict.get('_wallet')

        # Use get_param to support placeholders
        repo_path = oacommon.get_param(param, 'repo_path', wallet) or gdict.get('repo_path')
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

            # Check if there are changes
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