# Open-Automator - Module Documentation

Automatic documentation of available modules and functions.

---

## 📑 Module Index

- [oa-docker](#oadocker) - 3 functions
- [oa-git](#oagit) - 6 functions
- [oa-io](#oaio) - 7 functions
- [oa-json](#oajson) - 7 functions
- [oa-moduletemplate](#oamoduletemplate) - 2 functions
- [oa-network](#oanetwork) - 4 functions
- [oa-notify](#oanotify) - 3 functions
- [oa-pg](#oapg) - 3 functions
- [oa-system](#oasystem) - 5 functions
- [oa-utility](#oautility) - 7 functions

---

## oa-docker

### 📋 Available functions (3)

- [`container_run()`](#oadocker-container_run) - Starts a Docker container with data propagation
- [`container_stop()`](#oadocker-container_stop) - Stops a Docker container with data propagation
- [`container_logs()`](#oadocker-container_logs) - Retrieves logs from a Docker container

---

### `container_run()` {#oadocker-container_run}

Starts a Docker container with data propagation

**Parameters:**

- `param (dict) with`: 
- `image`: Docker image name - supports {WALLET:key}, {ENV:var}
- `name`: (optional) container name - supports {ENV:var}
- `ports`: (optional) dict port mapping e.g. {"8080": "80"}
- `volumes`: (optional) dict volume mapping
- `env`: (optional) dict environment variables
- `detach`: (optional) run in background (default: True)
- `remove`: (optional) auto-remove on exit (default: False)
- `command`: (optional) command to execute
- `input`: (optional) data from previous task
- `workflowcontext`: (optional) workflow context
- `taskid`: (optional) unique task id
- `taskstore`: (optional) TaskResultStore instance

**Returns:**

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

---

### `container_stop()` {#oadocker-container_stop}

Stops a Docker container with data propagation

**Parameters:**

- `param (dict) with`: 
- `container`: container name or ID (can use input from previous task)
- `timeout`: (optional) timeout in seconds (default: 10)
- `input`: (optional) data from previous task
- `workflowcontext`: (optional) workflow context
- `taskid`: (optional) unique task id
- `taskstore`: (optional) TaskResultStore instance

**Returns:**

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

---

### `container_logs()` {#oadocker-container_logs}

Retrieves logs from a Docker container

**Parameters:**

- `param (dict) with`: 
- `container`: container name or ID (can use input from previous task)
- `tail`: (optional) number of lines (default: all)
- `follow`: (optional) follow logs in real-time (default: False)
- `timestamps`: (optional) show timestamps (default: False)
- `saveonvar`: (optional) save logs to variable
- `input`: (optional) data from previous task
- taskid, taskstore, workflowcontext

**Returns:**

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

---

## oa-git

### 📋 Available functions (6)

- [`clone()`](#oagit-clone) - Clones a Git repository with data propagation
- [`pull()`](#oagit-pull) - Executes git pull on an existing repository with data propagation
- [`push()`](#oagit-push) - Executes git push with data propagation
- [`tag()`](#oagit-tag) - Creates, lists, or deletes Git tags with data propagation
- [`branch()`](#oagit-branch) - Manages Git branches (create, list, delete, checkout) with data propagation
- [`status()`](#oagit-status) - Gets the Git repository status with data propagation

---

### `clone()` {#oagit-clone}

Clones a Git repository with data propagation

**Parameters:**

- `param`: dict with:
- `repo_url`: repository URL (https or ssh) - supports {WALLET:key}, {ENV:var}
- `dest_path`: local destination path
- `branch`: (optional) specific branch to clone
- `depth`: (optional) shallow clone with specified depth
- `recursive`: (optional) recursive submodule clone, default False
- `username`: (optional) username for HTTPS auth - supports {WALLET:key}, {ENV:var}
- `password`: (optional) password/token for HTTPS auth - supports {WALLET:key}, {ENV:var}
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `pull()` {#oagit-pull}

Executes git pull on an existing repository with data propagation

**Parameters:**

- `param`: dict with:
- `repo_path`: local repository path - supports {ENV:var}
- `branch`: (optional) branch to pull
- `rebase`: (optional) use rebase instead of merge, default False
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `push()` {#oagit-push}

Executes git push with data propagation

**Parameters:**

- `param`: dict with:
- `repo_path`: local repository path - supports {ENV:var}
- `branch`: (optional) branch to push
- `remote`: (optional) remote name, default 'origin'
- `force`: (optional) force push, default False
- `tags`: (optional) push tags, default False
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `tag()` {#oagit-tag}

Creates, lists, or deletes Git tags with data propagation

**Parameters:**

- `param`: dict with:
- `repo_path`: local repository path - supports {ENV:var}
- `operation`: 'create'|'list'|'delete'
- `tag_name`: (optional) tag name (for create/delete) - supports {ENV:var}
- `message`: (optional) message for annotated tag
- `commit`: (optional) commit to tag
- `push`: (optional) push tag after creation, default False
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `branch()` {#oagit-branch}

Manages Git branches (create, list, delete, checkout) with data propagation

**Parameters:**

- `param`: dict with:
- `repo_path`: local repository path - supports {ENV:var}
- `operation`: 'create'|'list'|'delete'|'checkout'
- `branch_name`: (optional) branch name (for create/delete/checkout) - supports {ENV:var}
- `from_branch`: (optional) source branch/commit for create
- `force`: (optional) force delete, default False
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `status()` {#oagit-status}

Gets the Git repository status with data propagation

**Parameters:**

- `param`: dict with:
- `repo_path`: local repository path - supports {ENV:var}
- `short`: (optional) short format, default False
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

## oa-io

### 📋 Available functions (7)

- [`copy()`](#oaio-copy) - Copies files or directories with data propagation
- [`zip()`](#oaio-zip) - Creates a ZIP archive with data propagation
- [`unzip()`](#oaio-unzip) - Extracts a ZIP archive with data propagation
- [`readfile()`](#oaio-readfile) - Reads file content with data propagation
- [`writefile()`](#oaio-writefile) - Writes content to a file with data propagation
- [`replace()`](#oaio-replace) - Replaces text in a variable with data propagation
- [`loadvarfromjson()`](#oaio-loadvarfromjson) - Loads variables from a JSON file into gdict with data propagation

---

### `copy()` {#oaio-copy}

Copies files or directories with data propagation

**Parameters:**

- `param`: dict with:
- `srcpath`: source path - supports {WALLET:key}, {ENV:var}
- `dstpath`: destination path - supports {WALLET:key}, {ENV:var}
- `recursive`: True for directories, False for single file
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `zip()` {#oaio-zip}

Creates a ZIP archive with data propagation

**Parameters:**

- `param`: dict with:
- `zipfilename`: ZIP file name - supports {WALLET:key}, {ENV:var}
- `pathtozip`: path to compress (can use input from previous task) - supports {ENV:var}
- `zipfilter`: file filter (e.g., "*.txt" or "*")
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `unzip()` {#oaio-unzip}

Extracts a ZIP archive with data propagation

**Parameters:**

- `param`: dict with:
- `zipfilename`: ZIP file to extract (can use input from previous task) - supports {ENV:var}
- `pathwhereunzip`: destination directory - supports {ENV:var}
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `readfile()` {#oaio-readfile}

Reads file content with data propagation

**Parameters:**

- `param`: dict with:
- `filename`: file to read (can use input from previous task) - supports {WALLET:key}, {ENV:var}
- `varname`: (optional) if you only want to return content
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `writefile()` {#oaio-writefile}

Writes content to a file with data propagation

**Parameters:**

- `param`: dict with:
- `filename`: file to write - supports {WALLET:key}, {ENV:var}
- `varname`: (optional if there's input from previous task)
- `content`: (optional, alternative to varname) - supports {WALLET:key}, {ENV:var}
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `replace()` {#oaio-replace}

Replaces text in a variable with data propagation

**Parameters:**

- `param`: dict with:
- `varname`: (optional if there's input)
- `leftvalue`: text to search for
- `rightvalue`: replacement text
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `loadvarfromjson()` {#oaio-loadvarfromjson}

Loads variables from a JSON file into gdict with data propagation

**Parameters:**

- `param`: dict with:
- `filename`: JSON file (can use input from previous task) - supports {WALLET:key}, {ENV:var}
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

## oa-json

### 📋 Available functions (7)

- [`jsonfilter()`](#oajson-jsonfilter) - Filters elements in a JSON array based on conditions
- [`jsonextract()`](#oajson-jsonextract) - Extracts specific fields from JSON objects
- [`jsontransform()`](#oajson-jsontransform) - Transforms JSON data by applying mapping and transformations
- [`jsonmerge()`](#oajson-jsonmerge) - Merges multiple JSON objects/arrays
- [`jsonaggregate()`](#oajson-jsonaggregate) - Aggregates JSON data (sum, avg, count, min, max, group)
- [`jsonvalidate()`](#oajson-jsonvalidate) - Validates JSON against a JSON Schema
- [`jsonsort()`](#oajson-jsonsort) - Sorts JSON array by field

---

### `jsonfilter()` {#oajson-jsonfilter}

Filters elements in a JSON array based on conditions

**Parameters:**

- `param (dict) with`: 
- `data`: optional JSON data (can use input from previous task)
- `field`: field to filter on - supports {WALLET:key}, {ENV:var}
- `operator`: ==, !=, >, <, >=, <=, contains, in, exists, not_exists
- `value`: comparison value - supports {WALLET:key}, {ENV:var}
- `case_sensitive`: optional (default: True)
- `saveonvar`: optional save result to variable
- `input`: optional data from previous task
- `workflowcontext`: optional workflow context
- `taskid`: optional unique task id
- `taskstore`: optional TaskResultStore instance

**Returns:**

tuple (success, filtered_data)

Example YAML:

# Filter users by age

- name: filter_adults

module: oa-json

function: jsonfilter

data:

- {name: "Alice", age: 30}

- {name: "Bob", age: 25}

- {name: "Charlie", age: 35}

field: age

operator: ">"

value: 26

# Output: [{name: "Alice", age: 30}, {name: "Charlie", age: 35}]

# Filter with contains operator

- name: filter_emails

module: oa-json

function: jsonfilter

field: email

operator: contains

value: "@gmail.com"

case_sensitive: false

# Filter from previous task

- name: filter_active_users

module: oa-json

function: jsonfilter

# data from previous API call or database query

field: status

operator: "=="

value: "active"

# Check field existence

- name: filter_has_address

module: oa-json

function: jsonfilter

field: address

operator: exists

value: true

# Filter with wallet value

- name: filter_by_category

module: oa-json

function: jsonfilter

field: category

operator: "=="

value: "{WALLET:target_category}"

---

### `jsonextract()` {#oajson-jsonextract}

Extracts specific fields from JSON objects

**Parameters:**

- `param (dict) with`: 
- `data`: optional JSON data (can use input)
- `fields`: list of fields to extract - supports {WALLET:key}, {ENV:var}
- `flatten`: optional flatten nested objects (default: False)
- `keep_nulls`: optional keep null fields (default: False)
- `saveonvar`: optional save result
- `input`: optional data from previous task
- taskid, taskstore, workflowcontext

**Returns:**

tuple (success, extracted_data)

Example YAML:

# Extract specific fields from array

- name: extract_user_info

module: oa-json

function: jsonextract

data:

- {name: "Alice", age: 30, city: "Rome", country: "Italy"}

- {name: "Bob", age: 25, city: "Milan", country: "Italy"}

fields:

- name

- city

# Output: [{name: "Alice", city: "Rome"}, {name: "Bob", city: "Milan"}]

# Extract with dot notation for nested fields

- name: extract_nested

module: oa-json

function: jsonextract

data:

user:

name: "Alice"

email: "alice@example.com"

address:

city: "Rome"

fields:

- user.name

- user.address.city

flatten: true

# Output: {"user.name": "Alice", "user.address.city": "Rome"}

# Extract from previous task

- name: extract_from_api

module: oa-json

function: jsonextract

# data from previous API call

fields: "id,name,email"  # comma-separated string also supported

# Keep null values

- name: extract_with_nulls

module: oa-json

function: jsonextract

fields:

- name

- optional_field

keep_nulls: true

---

### `jsontransform()` {#oajson-jsontransform}

Transforms JSON data by applying mapping and transformations

**Parameters:**

- `param (dict) with`: 
- `data`: optional JSON data (can use input)
- `mapping`: dict with {new_field: old_field} or {new_field: "function:old_field"}
- `functions`: optional dict with custom functions
- `add_fields`: optional dict with new static fields
- `remove_fields`: optional list of fields to remove
- `saveonvar`: optional
- `input`: optional data from previous task

**Returns:**

tuple (success, transformed_data)

Example YAML:

# Rename fields

- name: rename_user_fields

module: oa-json

function: jsontransform

data:

first_name: "Alice"

last_name: "Smith"

age: 30

mapping:

name: first_name

surname: last_name

years: age

# Output: {name: "Alice", surname: "Smith", years: 30}

# Transform with built-in functions

- name: transform_case

module: oa-json

function: jsontransform

mapping:

NAME: "upper:name"

email_lower: "lower:email"

age_int: "int:age"

# Built-in functions: upper, lower, int, float, str, bool, strip

# Add static fields

- name: add_metadata

module: oa-json

function: jsontransform

add_fields:

source: "import"

import_date: "2025-12-30"

version: 1

# Remove unwanted fields

- name: cleanup_data

module: oa-json

function: jsontransform

remove_fields:

- internal_id

- temp_field

- _metadata

# Complex transformation

- name: transform_users

module: oa-json

function: jsontransform

data:

- {first_name: "alice", email: "ALICE@EXAMPLE.COM", age: "30"}

mapping:

full_name: "upper:first_name"

email: "lower:email"

age: "int:age"

add_fields:

status: "active"

remove_fields:

- first_name

---

### `jsonmerge()` {#oajson-jsonmerge}

Merges multiple JSON objects/arrays

**Parameters:**

- `param (dict) with`: 
- `sources`: list of keys from workflowcontext or list of direct data
- `merge_type`: "dict" (merge objects), "array" (concatenate arrays), "deep" (deep merge)
- `overwrite`: optional for dict merge (default: True)
- `unique`: optional remove duplicates in array merge (default: False)
- `saveonvar`: optional
- `input`: optional data from previous task (added to merge)
- `workflowcontext`: optional workflow context

**Returns:**

tuple (success, merged_data)

Example YAML:

# Merge dict objects

- name: merge_configs

module: oa-json

function: jsonmerge

sources:

- task_config_base

- task_config_override

merge_type: dict

overwrite: true

# Later values overwrite earlier ones

# Concatenate arrays

- name: merge_user_lists

module: oa-json

function: jsonmerge

sources:

- users_from_db

- users_from_api

merge_type: array

unique: true

# Removes duplicate entries

# Deep merge nested objects

- name: deep_merge_settings

module: oa-json

function: jsonmerge

sources:

- {db: {host: "localhost", port: 5432}}

- {db: {user: "admin"}, cache: {enabled: true}}

merge_type: deep

# Output: {db: {host: "localhost", port: 5432, user: "admin"}, cache: {enabled: true}}

# Merge with input from previous task

- name: merge_with_previous

module: oa-json

function: jsonmerge

# input from previous task automatically included

sources:

- static_data

merge_type: dict

---

### `jsonaggregate()` {#oajson-jsonaggregate}

Aggregates JSON data (sum, avg, count, min, max, group)

**Parameters:**

- `param (dict) with`: 
- `data`: optional JSON array data (can use input)
- `operation`: sum, avg, count, min, max, group
- `field`: field to aggregate on - supports {WALLET:key}, {ENV:var}
- `group_by`: optional field for grouping
- `saveonvar`: optional
- `input`: optional data from previous task

**Returns:**

tuple (success, aggregated_data)

Example YAML:

# Count items

- name: count_users

module: oa-json

function: jsonaggregate

data:

- {name: "Alice", age: 30}

- {name: "Bob", age: 25}

operation: count

# Output: 2

# Sum values

- name: total_sales

module: oa-json

function: jsonaggregate

data:

- {product: "A", amount: 100}

- {product: "B", amount: 200}

- {product: "C", amount: 150}

operation: sum

field: amount

# Output: 450

# Average with grouping

- name: avg_age_by_department

module: oa-json

function: jsonaggregate

data:

- {name: "Alice", age: 30, dept: "IT"}

- {name: "Bob", age: 25, dept: "IT"}

- {name: "Charlie", age: 35, dept: "Sales"}

operation: avg

field: age

group_by: dept

# Output: {"IT": 27.5, "Sales": 35}

# Group by category

- name: group_products

module: oa-json

function: jsonaggregate

operation: group

group_by: category

# Groups all items by category field

# Min/Max

- name: price_range

module: oa-json

function: jsonaggregate

field: price

operation: min

# Find minimum price

---

### `jsonvalidate()` {#oajson-jsonvalidate}

Validates JSON against a JSON Schema

**Parameters:**

- `param (dict) with`: 
- `data`: optional JSON data (can use input)
- `schema`: JSON Schema for validation
- `strict`: optional fail on validation error (default: True)
- `saveonvar`: optional
- `input`: optional data from previous task

**Returns:**

tuple (success, validation_result)

Example YAML:

# Validate user data

- name: validate_user

module: oa-json

function: jsonvalidate

data:

name: "Alice"

email: "alice@example.com"

age: 30

schema:

type: object

required:

- name

- email

properties:

name:

type: string

email:

type: string

format: email

age:

type: integer

minimum: 0

strict: true

# Validate array of items

- name: validate_products

module: oa-json

function: jsonvalidate

schema:

type: array

items:

type: object

required:

- id

- name

- price

properties:

id:

type: integer

name:

type: string

price:

type: number

minimum: 0

# Non-strict validation (doesn't fail on error)

- name: check_optional_fields

module: oa-json

function: jsonvalidate

schema:

type: object

properties:

optional_field:

type: string

strict: false

# Continues even if validation fails

Note: Requires jsonschema library: pip install jsonschema

---

### `jsonsort()` {#oajson-jsonsort}

Sorts JSON array by field

**Parameters:**

- `param (dict) with`: 
- `data`: optional JSON array data (can use input)
- `sort_by`: field for sorting - supports {WALLET:key}, {ENV:var}
- `reverse`: optional descending order (default: False)
- `numeric`: optional sort as numbers (default: auto-detect)
- `saveonvar`: optional
- `input`: optional data from previous task

**Returns:**

tuple (success, sorted_data)

Example YAML:

# Sort by name (alphabetical)

- name: sort_users_by_name

module: oa-json

function: jsonsort

data:

- {name: "Charlie", age: 35}

- {name: "Alice", age: 30}

- {name: "Bob", age: 25}

sort_by: name

# Output: [{name: "Alice"...}, {name: "Bob"...}, {name: "Charlie"...}]

# Sort by age (numeric, descending)

- name: sort_by_age_desc

module: oa-json

function: jsonsort

sort_by: age

reverse: true

numeric: true

# Output: Oldest to youngest

# Sort from previous filter task

- name: sort_filtered_results

module: oa-json

function: jsonsort

# data from previous jsonfilter task

sort_by: created_date

reverse: true

# Auto-detect numeric sorting

- name: sort_by_price

module: oa-json

function: jsonsort

sort_by: price

# Automatically detects if price is numeric

# Sort with environment variable

- name: sort_dynamic

module: oa-json

function: jsonsort

sort_by: "{ENV:SORT_FIELD}"

reverse: false

---

## oa-moduletemplate

### 📋 Available functions (2)

- [`templatefunction()`](#oamoduletemplate-templatefunction) - Function description with data propagation
- [`advanced_function()`](#oamoduletemplate-advanced_function) - Advanced function with support for multiple operations

---

### `templatefunction()` {#oamoduletemplate-templatefunction}

Function description with data propagation This is a template function showing best practices for: - Data propagation from previous tasks - Parameter validation - Error handling - Output standardization - Logging

**Parameters:**

- `param`: dict with:
- `param1`: (type) required parameter description
- `param2`: (type) required parameter description (supports {WALLET:key}, {ENV:var})
- `param3`: (type, optional) optional parameter description
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_data) where output_data contains results

Example YAML:

# Basic usage

- name: example_task

module: oa-moduletemplate

function: templatefunction

param1: "value1"

param2: "value2"

param3: "optional_value"

# With placeholders

- name: secure_task

module: oa-moduletemplate

function: templatefunction

param1: "{WALLET:api_key}"

param2: "{ENV:TARGET_ENV}"

# With data from previous task

- name: chained_task

module: oa-moduletemplate

function: templatefunction

# param1 auto-filled from previous task output

param2: "additional_value"

# With error handling

- name: safe_task

module: oa-moduletemplate

function: templatefunction

param1: "value1"

param2: "value2"

on_success: next_task

on_failure: error_handler

---

### `advanced_function()` {#oamoduletemplate-advanced_function}

Advanced function with support for multiple operations This demonstrates how to implement CRUD-style operations with data propagation and proper error handling.

**Parameters:**

- `param`: dict with:
- `operation`: (str) 'create'|'read'|'update'|'delete'
- `target`: (str) operation target - supports {WALLET:key}, {ENV:var}
- `data`: (dict, optional) data for operation
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_data)

Example YAML:

# CREATE operation

- name: create_resource

module: oa-moduletemplate

function: advanced_function

operation: "create"

target: "user_profile"

data:

name: "John Doe"

email: "john@example.com"

role: "admin"

# READ operation

- name: read_resource

module: oa-moduletemplate

function: advanced_function

operation: "read"

target: "config_settings"

# UPDATE operation with data from previous task

- name: update_resource

module: oa-moduletemplate

function: advanced_function

operation: "update"

target: "user_profile"

# data from previous task

# DELETE operation

- name: delete_resource

module: oa-moduletemplate

function: advanced_function

operation: "delete"

target: "temp_file"

# With placeholders

- name: secure_operation

module: oa-moduletemplate

function: advanced_function

operation: "create"

target: "{ENV:TARGET_RESOURCE}"

data:

api_key: "{VAULT:api_secret}"

user: "{WALLET:username}"

# Chained operations

- name: multi_step_process

module: oa-moduletemplate

function: advanced_function

operation: "read"

target: "source_data"

- name: process_and_update

module: oa-moduletemplate

function: advanced_function

operation: "update"

# target from previous task

data:

processed: true

timestamp: "{WALLET:current_time}"

---

## oa-network

### 📋 Available functions (4)

- [`httpget()`](#oanetwork-httpget) - Executes an HTTP GET request with data propagation
- [`httpsget()`](#oanetwork-httpsget) - Executes an HTTPS GET request with data propagation
- [`httppost()`](#oanetwork-httppost) - Executes an HTTP POST request with data propagation
- [`httpspost()`](#oanetwork-httpspost) - Executes an HTTPS POST request with data propagation

---

### `httpget()` {#oanetwork-httpget}

Executes an HTTP GET request with data propagation

**Parameters:**

- `param`: dict with:
- `host`: hostname or IP (can derive from previous input) - supports {WALLET:key}, {ENV:var}
- `port`: HTTP port - supports {ENV:var}
- `get`: request path - supports {WALLET:key}, {ENV:var}
- `printout`: (optional) print response
- `saveonvar`: (optional) save response to variable
- `headers`: (optional) dict with custom headers - supports {WALLET:key} in values
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_dict) with response data

Example YAML:

# Simple HTTP GET request

- name: fetch_api_data

module: oa-network

function: httpget

host: "api.example.com"

port: 80

get: "/api/v1/users"

# With custom headers

- name: api_with_headers

module: oa-network

function: httpget

host: "api.example.com"

port: 80

get: "/api/data"

headers:

User-Agent: "Open-Automator/1.0"

Accept: "application/json"

# Using environment variables

- name: fetch_from_env

module: oa-network

function: httpget

host: "{ENV:API_HOST}"

port: 80

get: "{ENV:API_PATH}"

printout: true

# With authentication header from wallet

- name: authenticated_get

module: oa-network

function: httpget

host: "secure-api.example.com"

port: 80

get: "/api/protected"

headers:

Authorization: "Bearer {WALLET:api_token}"

# Using URL from previous task

- name: fetch_dynamic_url

module: oa-network

function: httpget

# host, port, get extracted from previous task's 'url' field

---

### `httpsget()` {#oanetwork-httpsget}

Executes an HTTPS GET request with data propagation

**Parameters:**

- `param`: dict with:
- `host`: hostname or IP (can derive from previous input) - supports {WALLET:key}, {ENV:var}
- `port`: HTTPS port - supports {ENV:var}
- `get`: request path - supports {WALLET:key}, {ENV:var}
- `verify`: (optional) verify SSL certificate, default True
- `printout`: (optional) print response
- `saveonvar`: (optional) save response to variable
- `headers`: (optional) dict with custom headers - supports {WALLET:key} in values (e.g., tokens)
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_dict) with response data

Example YAML:

# Simple HTTPS GET request

- name: fetch_secure_api

module: oa-network

function: httpsget

host: "api.example.com"

port: 443

get: "/api/v1/data"

# With Bearer token from wallet

- name: api_with_token

module: oa-network

function: httpsget

host: "api.github.com"

port: 443

get: "/user/repos"

headers:

Authorization: "Bearer {WALLET:github_token}"

Accept: "application/vnd.github.v3+json"

# Disable SSL verification (not recommended for production)

- name: insecure_api_call

module: oa-network

function: httpsget

host: "self-signed.example.com"

port: 443

get: "/api/data"

verify: false

# API with multiple headers from wallet

- name: complex_api_call

module: oa-network

function: httpsget

host: "{ENV:API_HOST}"

port: 443

get: "/api/protected/resource"

headers:

Authorization: "Bearer {VAULT:api_secret}"

X-API-Key: "{WALLET:api_key}"

User-Agent: "Open-Automator"

printout: true

# Call REST API and parse JSON

- name: fetch_json_data

module: oa-network

function: httpsget

host: "jsonplaceholder.typicode.com"

port: 443

get: "/posts/1"

# Response automatically parsed as JSON if Content-Type is application/json

---

### `httppost()` {#oanetwork-httppost}

Executes an HTTP POST request with data propagation

**Parameters:**

- `param`: dict with:
- `host`: hostname or IP - supports {WALLET:key}, {ENV:var}
- `port`: HTTP port - supports {ENV:var}
- `path`: request path - supports {WALLET:key}, {ENV:var}
- `data`: data to send (can come from previous input) - supports {WALLET:key}
- `headers`: (optional) dict with custom headers - supports {WALLET:key} in values
- `content_type`: (optional) default 'application/json'
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_dict) with response data

Example YAML:

# Simple POST with JSON data

- name: create_user

module: oa-network

function: httppost

host: "api.example.com"

port: 80

path: "/api/users"

data:

name: "John Doe"

email: "john@example.com"

age: 30

# POST with data from wallet

- name: send_credentials

module: oa-network

function: httppost

host: "{ENV:API_HOST}"

port: 80

path: "/api/login"

data:

username: "{WALLET:api_username}"

password: "{VAULT:api_password}"

# POST with custom headers

- name: api_post_with_headers

module: oa-network

function: httppost

host: "api.example.com"

port: 80

path: "/api/data"

headers:

Authorization: "Bearer {WALLET:token}"

X-Custom-Header: "value"

data:

field1: "value1"

field2: "value2"

# POST data from previous task

- name: submit_processed_data

module: oa-network

function: httppost

host: "api.example.com"

port: 80

path: "/api/submit"

# data automatically taken from previous task output

# POST with different content type

- name: post_xml_data

module: oa-network

function: httppost

host: "api.example.com"

port: 80

path: "/api/xml"

content_type: "application/xml"

data: "<xml>data</xml>"

---

### `httpspost()` {#oanetwork-httpspost}

Executes an HTTPS POST request with data propagation

**Parameters:**

- `param`: dict with:
- `host`: hostname or IP - supports {WALLET:key}, {ENV:var}
- `port`: HTTPS port - supports {ENV:var}
- `path`: request path - supports {WALLET:key}, {ENV:var}
- `data`: data to send (can come from previous input) - supports {WALLET:key}
- `headers`: (optional) dict with custom headers - supports {WALLET:key} in values (e.g., API key)
- `content_type`: (optional) default 'application/json'
- `verify`: (optional) verify SSL certificate, default True
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_dict) with response data

Example YAML:

# Simple HTTPS POST

- name: create_secure_resource

module: oa-network

function: httpspost

host: "api.example.com"

port: 443

path: "/api/v1/resources"

data:

name: "New Resource"

type: "important"

# POST with API key from vault

- name: secure_api_post

module: oa-network

function: httpspost

host: "api.github.com"

port: 443

path: "/repos/owner/repo/issues"

headers:

Authorization: "Bearer {VAULT:github_token}"

Accept: "application/vnd.github.v3+json"

data:

title: "Bug report"

body: "Description of the bug"

# POST with multiple credentials from wallet

- name: enterprise_api_call

module: oa-network

function: httpspost

host: "{ENV:ENTERPRISE_API}"

port: 443

path: "/api/submit"

headers:

X-API-Key: "{WALLET:api_key}"

X-Client-ID: "{WALLET:client_id}"

Authorization: "Bearer {VAULT:access_token}"

data:

user_id: "{WALLET:user_id}"

action: "create"

payload:

field1: "value1"

# POST data from previous task (e.g., after JSON transformation)

- name: submit_transformed_data

module: oa-network

function: httpspost

host: "api.example.com"

port: 443

path: "/api/bulk"

# data automatically from previous jsontransform task

# Disable SSL verification for self-signed cert

- name: internal_api_post

module: oa-network

function: httpspost

host: "internal-api.company.local"

port: 443

path: "/api/data"

verify: false

data:

internal_data: "sensitive"

---

## oa-notify

### 📋 Available functions (3)

- [`sendtelegramnotify()`](#oanotify-sendtelegramnotify) - Sends a Telegram message via bot API with data propagation
- [`sendmailbygmail()`](#oanotify-sendmailbygmail) - Sends email via Gmail SMTP SSL with data propagation
- [`formatmessage()`](#oanotify-formatmessage) - Formats a message from structured data (helper for notifications)

---

### `sendtelegramnotify()` {#oanotify-sendtelegramnotify}

Sends a Telegram message via bot API with data propagation

**Parameters:**

- `param`: dict with:
- `tokenid`: Telegram bot token - supports {WALLET:key}, {ENV:var}
- `chatid`: list of chat_ids - supports {WALLET:key}, {ENV:var}
- `message`: message to send (can come from previous task input) - supports {WALLET:key}, {ENV:var}
- `printresponse`: (optional) print response
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_dict) with sending info

Example YAML:

# Send simple message

- name: notify_success

module: oa-notify

function: sendtelegramnotify

tokenid: "{WALLET:telegram_bot_token}"

chatid:

- "{WALLET:telegram_chat_id}"

message: "Workflow completed successfully!"

# Send previous task output

- name: send_results

module: oa-notify

function: sendtelegramnotify

tokenid: "{ENV:TELEGRAM_TOKEN}"

chatid:

- "123456789"

- "987654321"

# message comes from previous task input

# Send with token from environment

- name: alert_team

module: oa-notify

function: sendtelegramnotify

tokenid: "{ENV:BOT_TOKEN}"

chatid: ["{ENV:CHAT_ID}"]

message: "Error occurred: {WALLET:error_message}"

---

### `sendmailbygmail()` {#oanotify-sendmailbygmail}

Sends email via Gmail SMTP SSL with data propagation

**Parameters:**

- `param`: dict with:
- `senderemail`: sender email - supports {WALLET:key}, {ENV:var}
- `receiveremail`: receiver email - supports {WALLET:key}, {ENV:var}
- `senderpassword`: sender password - supports {WALLET:key}, {VAULT:key}
- `subject`: email subject - supports {WALLET:key}, {ENV:var}
- `messagetext`: (optional) plain text - supports {WALLET:key}, {ENV:var}
- `messagehtml`: (optional) HTML text - supports {WALLET:key}, {ENV:var}
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_dict) with sending info

Example YAML:

# Send plain text email

- name: send_report

module: oa-notify

function: sendmailbygmail

senderemail: "{ENV:GMAIL_USER}"

receiveremail: "recipient@example.com"

senderpassword: "{VAULT:gmail_app_password}"

subject: "Daily Report"

messagetext: "Here is your daily report..."

# Send HTML email

- name: send_html_report

module: oa-notify

function: sendmailbygmail

senderemail: "bot@example.com"

receiveremail: "{WALLET:admin_email}"

senderpassword: "{WALLET:email_password}"

subject: "Workflow Results"

messagehtml: "<h1>Success</h1><p>Workflow completed</p>"

# Send previous task output as email

- name: email_results

module: oa-notify

function: sendmailbygmail

senderemail: "{ENV:SENDER}"

receiveremail: "{ENV:RECEIVER}"

senderpassword: "{VAULT:password}"

subject: "Task Output"

# messagetext comes from previous task

---

### `formatmessage()` {#oanotify-formatmessage}

Formats a message from structured data (helper for notifications)

**Parameters:**

- `param`: dict with:
- `template`: (optional) message template with {key} placeholders - supports {WALLET:key}, {ENV:var}
- `data`: (optional) dict with data to format
- `format`: (optional) 'json', 'text', 'markdown'
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, formatted_message)

Example YAML:

# Format with template

- name: format_alert

module: oa-notify

function: formatmessage

template: "Status: {status}, Count: {count}, Time: {timestamp}"

data:

status: "success"

count: 42

timestamp: "2025-12-30"

# Format as JSON

- name: format_json

module: oa-notify

function: formatmessage

format: json

# Uses input from previous task

# Format as markdown

- name: format_markdown

module: oa-notify

function: formatmessage

format: markdown

data:

title: "Report"

items: ["Item 1", "Item 2"]

---

## oa-pg

### 📋 Available functions (3)

- [`select()`](#oapg-select) - Executes SELECT on PostgreSQL with data propagation
- [`execute()`](#oapg-execute) - Executes INSERT/UPDATE/DELETE on PostgreSQL with data propagation
- [`insert()`](#oapg-insert) - Helper for INSERT with data propagation from previous input

---

### `select()` {#oapg-select}

Executes SELECT on PostgreSQL with data propagation

**Parameters:**

- `param`: dict with:
- `pgdatabase`: database name - supports {WALLET:key}, {ENV:var}
- `pgdbhost`: host - supports {WALLET:key}, {ENV:var}
- `pgdbusername`: username - supports {WALLET:key}, {ENV:var}
- `pgdbpassword`: password - supports {WALLET:key}, {VAULT:key}
- `pgdbport`: port - supports {ENV:var}
- `statement`: SQL query (can use input from previous task) - supports {WALLET:key}, {ENV:var}
- `printout`: (optional) print result, default False
- `tojsonfile`: (optional) JSON file path
- `saveonvar`: (optional) save to variable
- `format`: (optional) 'rows', 'dict', 'json' - default 'dict'
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_data) with query results

Example YAML:

# Simple SELECT query

- name: get_users

module: oa-pg

function: select

pgdatabase: "myapp"

pgdbhost: "localhost"

pgdbusername: "postgres"

pgdbpassword: "{VAULT:db_password}"

pgdbport: 5432

statement: "SELECT id, name, email FROM users WHERE active = true"

printout: true

# Query with credentials from wallet/vault

- name: query_production_db

module: oa-pg

function: select

pgdatabase: "{ENV:DB_NAME}"

pgdbhost: "{ENV:DB_HOST}"

pgdbusername: "{WALLET:db_user}"

pgdbpassword: "{VAULT:db_pass}"

pgdbport: 5432

statement: "SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'"

format: "dict"

# Save results to JSON file

- name: export_data

module: oa-pg

function: select

pgdatabase: "analytics"

pgdbhost: "db-server"

pgdbusername: "readonly"

pgdbpassword: "{VAULT:readonly_pass}"

pgdbport: 5432

statement: "SELECT user_id, COUNT(*) as orders FROM orders GROUP BY user_id"

tojsonfile: "/data/user_orders.json"

format: "json"

# Query with dynamic WHERE clause from wallet

- name: filtered_query

module: oa-pg

function: select

pgdatabase: "mydb"

pgdbhost: "localhost"

pgdbusername: "app"

pgdbpassword: "{VAULT:app_pass}"

pgdbport: 5432

statement: "SELECT * FROM products WHERE category = '{WALLET:target_category}'"

# Save to variable for next task

- name: get_pending_tasks

module: oa-pg

function: select

pgdatabase: "tasks"

pgdbhost: "{ENV:TASK_DB_HOST}"

pgdbusername: "{WALLET:db_user}"

pgdbpassword: "{VAULT:db_pass}"

pgdbport: 5432

statement: "SELECT task_id, description FROM tasks WHERE status = 'pending'"

saveonvar: pending_tasks

format: "dict"

# Complex JOIN query

- name: user_orders_report

module: oa-pg

function: select

pgdatabase: "ecommerce"

pgdbhost: "prod-db"

pgdbusername: "{WALLET:reporting_user}"

pgdbpassword: "{VAULT:reporting_pass}"

pgdbport: 5432

statement: |

SELECT u.name, u.email, COUNT(o.id) as order_count, SUM(o.total) as total_spent

FROM users u

LEFT JOIN orders o ON u.id = o.user_id

WHERE u.created_at > '2025-01-01'

GROUP BY u.id, u.name, u.email

ORDER BY total_spent DESC

LIMIT 100

format: "dict"

printout: true

# Query from previous task

- name: execute_dynamic_query

module: oa-pg

function: select

pgdatabase: "mydb"

pgdbhost: "localhost"

pgdbusername: "user"

pgdbpassword: "{VAULT:pass}"

pgdbport: 5432

# statement from previous task output

---

### `execute()` {#oapg-execute}

Executes INSERT/UPDATE/DELETE on PostgreSQL with data propagation

**Parameters:**

- `param`: dict with:
- `pgdatabase`: database name - supports {WALLET:key}, {ENV:var}
- `pgdbhost`: host - supports {WALLET:key}, {ENV:var}
- `pgdbusername`: username - supports {WALLET:key}, {ENV:var}
- `pgdbpassword`: password - supports {WALLET:key}, {VAULT:key}
- `pgdbport`: port - supports {ENV:var}
- `statement`: SQL statement (can use input from previous task) - supports {WALLET:key}, {ENV:var}
- `printout`: (optional) print result, default False
- `fail_on_zero`: (optional) fail if 0 rows affected, default False
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_data) with affected rows count

Example YAML:

# Simple UPDATE

- name: activate_user

module: oa-pg

function: execute

pgdatabase: "myapp"

pgdbhost: "localhost"

pgdbusername: "postgres"

pgdbpassword: "{VAULT:db_password}"

pgdbport: 5432

statement: "UPDATE users SET active = true WHERE id = 123"

printout: true

# INSERT with credentials from vault

- name: create_order

module: oa-pg

function: execute

pgdatabase: "{ENV:DB_NAME}"

pgdbhost: "{ENV:DB_HOST}"

pgdbusername: "{WALLET:db_user}"

pgdbpassword: "{VAULT:db_pass}"

pgdbport: 5432

statement: |

INSERT INTO orders (user_id, total, status, created_at)

VALUES (456, 99.99, 'pending', NOW())

# DELETE with fail_on_zero

- name: delete_expired_sessions

module: oa-pg

function: execute

pgdatabase: "sessions"

pgdbhost: "db-server"

pgdbusername: "cleanup"

pgdbpassword: "{VAULT:cleanup_pass}"

pgdbport: 5432

statement: "DELETE FROM sessions WHERE expires_at < NOW()"

fail_on_zero: false

printout: true

# UPDATE with dynamic values from wallet

- name: update_config

module: oa-pg

function: execute

pgdatabase: "config"

pgdbhost: "localhost"

pgdbusername: "admin"

pgdbpassword: "{VAULT:admin_pass}"

pgdbport: 5432

statement: "UPDATE settings SET value = '{WALLET:new_value}' WHERE key = 'api_endpoint'"

# Bulk INSERT

- name: insert_multiple_logs

module: oa-pg

function: execute

pgdatabase: "logs"

pgdbhost: "{ENV:LOG_DB_HOST}"

pgdbusername: "{WALLET:log_user}"

pgdbpassword: "{VAULT:log_pass}"

pgdbport: 5432

statement: |

INSERT INTO access_logs (user_id, action, timestamp)

VALUES

(1, 'login', NOW()),

(2, 'logout', NOW()),

(3, 'view_page', NOW())

# UPDATE with JOIN

- name: bulk_update_prices

module: oa-pg

function: execute

pgdatabase: "ecommerce"

pgdbhost: "prod-db"

pgdbusername: "{WALLET:admin_user}"

pgdbpassword: "{VAULT:admin_pass}"

pgdbport: 5432

statement: |

UPDATE products p

SET price = p.price * 1.1

FROM categories c

WHERE p.category_id = c.id

AND c.name = 'Electronics'

fail_on_zero: true

# Statement from previous task

- name: execute_dynamic_statement

module: oa-pg

function: execute

pgdatabase: "mydb"

pgdbhost: "localhost"

pgdbusername: "user"

pgdbpassword: "{VAULT:pass}"

pgdbport: 5432

# statement from previous task

# Save result to JSON file

- name: archive_old_data

module: oa-pg

function: execute

pgdatabase: "archive"

pgdbhost: "archive-db"

pgdbusername: "{WALLET:archive_user}"

pgdbpassword: "{VAULT:archive_pass}"

pgdbport: 5432

statement: "DELETE FROM old_records WHERE created_at < NOW() - INTERVAL '1 year'"

tojsonfile: "/logs/archive_result.json"

printout: true

---

### `insert()` {#oapg-insert}

Helper for INSERT with data propagation from previous input

**Parameters:**

- `param`: dict with:
- `pgdatabase, pgdbhost, pgdbusername, pgdbpassword, pgdbport - support {WALLET`: key}, {ENV:var}
- `table`: table name - supports {WALLET:key}, {ENV:var}
- `data`: (optional) dict or list of dicts to insert
- `input`: (optional) data from previous task (if correctly formatted)
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

tuple: (success, output_data)

Example YAML:

# Insert single row

- name: insert_user

module: oa-pg

function: insert

pgdatabase: "myapp"

pgdbhost: "localhost"

pgdbusername: "postgres"

pgdbpassword: "{VAULT:db_password}"

pgdbport: 5432

table: "users"

data:

name: "John Doe"

email: "john@example.com"

age: 30

active: true

# Insert multiple rows

- name: bulk_insert_products

module: oa-pg

function: insert

pgdatabase: "{ENV:DB_NAME}"

pgdbhost: "{ENV:DB_HOST}"

pgdbusername: "{WALLET:db_user}"

pgdbpassword: "{VAULT:db_pass}"

pgdbport: 5432

table: "products"

data:

- name: "Product A"

price: 19.99

stock: 100

- name: "Product B"

price: 29.99

stock: 50

- name: "Product C"

price: 39.99

stock: 75

# Insert with values from wallet

- name: insert_api_key

module: oa-pg

function: insert

pgdatabase: "config"

pgdbhost: "localhost"

pgdbusername: "admin"

pgdbpassword: "{VAULT:admin_pass}"

pgdbport: 5432

table: "api_keys"

data:

service_name: "{WALLET:service_name}"

api_key: "{VAULT:api_key}"

created_at: "NOW()"

# Insert from previous task (e.g., after JSON transformation)

- name: insert_transformed_data

module: oa-pg

function: insert

pgdatabase: "warehouse"

pgdbhost: "data-db"

pgdbusername: "{WALLET:etl_user}"

pgdbpassword: "{VAULT:etl_pass}"

pgdbport: 5432

table: "staging_data"

# data from previous jsontransform task

# Insert filtered results

- name: insert_filtered_users

module: oa-pg

function: insert

pgdatabase: "reports"

pgdbhost: "reporting-db"

pgdbusername: "{WALLET:report_user}"

pgdbpassword: "{VAULT:report_pass}"

pgdbport: 5432

table: "active_users_report"

# data from previous jsonfilter task

Note: Uses parameterized queries for SQL injection protection

---

## oa-system

### 📋 Available functions (5)

- [`runcmd()`](#oasystem-runcmd) - Executes a local shell command with data propagation
- [`systemd()`](#oasystem-systemd) - Manages systemd services on remote server with data propagation
- [`remotecommand()`](#oasystem-remotecommand) - Executes a remote command via SSH with data propagation
- [`scp()`](#oasystem-scp) - Transfers files/directories via SCP with data propagation
- [`execute_script()`](#oasystem-execute_script) - Executes a local script and propagates output

---

### `runcmd()` {#oasystem-runcmd}

Executes a local shell command with data propagation

**Parameters:**

- `param`: dict with:
- `command`: command to execute (can use input from previous task) - supports {WALLET:key}, {ENV:var}
- `printout`: (optional) print output, default False
- `saveonvar`: (optional) save output to variable
- `shell`: (optional) use shell, default True
- `timeout`: (optional) timeout in seconds
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `systemd()` {#oasystem-systemd}

Manages systemd services on remote server with data propagation

**Parameters:**

- `param`: dict with:
- `remoteserver`: remote host - supports {WALLET:key}, {ENV:var}
- `remoteuser`: SSH username - supports {WALLET:key}, {ENV:var}
- `remotepassword`: SSH password - supports {WALLET:key}, {VAULT:key}
- `remoteport`: SSH port - supports {ENV:var}
- `servicename`: service name - supports {WALLET:key}, {ENV:var}
- `servicestate`: start|stop|restart|status|daemon-reload
- `saveonvar`: (optional) save output to variable
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `remotecommand()` {#oasystem-remotecommand}

Executes a remote command via SSH with data propagation

**Parameters:**

- `param`: dict with:
- `remoteserver`: remote host - supports {WALLET:key}, {ENV:var}
- `remoteuser`: SSH username - supports {WALLET:key}, {ENV:var}
- `remotepassword`: SSH password - supports {WALLET:key}, {VAULT:key}
- `remoteport`: SSH port - supports {ENV:var}
- `command`: command to execute (can use input from previous task) - supports {WALLET:key}, {ENV:var}
- `saveonvar`: (optional) save output to variable
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `scp()` {#oasystem-scp}

Transfers files/directories via SCP with data propagation

**Parameters:**

- `param`: dict with:
- `remoteserver`: remote host - supports {WALLET:key}, {ENV:var}
- `remoteuser`: SSH username - supports {WALLET:key}, {ENV:var}
- `remotepassword`: SSH password - supports {WALLET:key}, {VAULT:key}
- `remoteport`: SSH port - supports {ENV:var}
- `localpath`: local path (can use input from previous task) - supports {WALLET:key}, {ENV:var}
- `remotepath`: remote path - supports {WALLET:key}, {ENV:var}
- `recursive`: True/False
- `direction`: localtoremote|remotetolocal
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

### `execute_script()` {#oasystem-execute_script}

Executes a local script and propagates output

**Parameters:**

- `param`: dict with:
- `script_path`: script path (can use input from previous task) - supports {WALLET:key}, {ENV:var}
- `args`: (optional) list of arguments - supports {WALLET:key}, {ENV:var}
- `interpreter`: (optional) interpreter (e.g., 'python3', 'bash'), default auto-detect
- `timeout`: (optional) timeout in seconds
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional) unique task id
- `task_store`: (optional) TaskResultStore instance

**Returns:**

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

---

## oa-utility

### 📋 Available functions (7)

- [`setsleep()`](#oautility-setsleep) - Pauses execution for a specified number of seconds with data propagation
- [`printvar()`](#oautility-printvar) - Prints the value of a variable or input with data propagation
- [`setvar()`](#oautility-setvar) - Sets the value of a variable with data propagation
- [`dumpvar()`](#oautility-dumpvar) - Exports all gdict variables to a JSON file with data propagation
- [`transform()`](#oautility-transform) - Transforms data with various operations (upper, lower, strip, etc.)
- [`condition()`](#oautility-condition) - Evaluates a condition for workflow branching
- [`merge()`](#oautility-merge) - Merges data from multiple sources

---

### `setsleep()` {#oautility-setsleep}

Pauses execution for a specified number of seconds with data propagation

**Parameters:**

- `param`: dict with:
- `seconds`: number of seconds to wait - supports {WALLET:key}, {ENV:var}
- `input`: (optional) data from previous task (passthrough)
- `workflow_context`: (optional) workflow context
- `task_id`: (optional)
- `task_store`: (optional)

**Returns:**

tuple: (success, input_data) - propagates received input

Example YAML:

# Simple sleep for 5 seconds

- name: wait_5_seconds

module: oa-utility

function: setsleep

seconds: 5

on_success: next_task

# Dynamic delay from environment variable

- name: wait_dynamic

module: oa-utility

function: setsleep

seconds: "{ENV:DELAY_SECONDS}"

on_success: continue_workflow

---

### `printvar()` {#oautility-printvar}

Prints the value of a variable or input with data propagation

**Parameters:**

- `param`: dict with:
- `varname`: (optional) variable name to print - supports {WALLET:key}, {ENV:var}
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional)
- `task_store`: (optional)

**Returns:**

tuple: (success, printed_value) - propagates the printed value

Example YAML:

# Print a specific variable

- name: print_result

module: oa-utility

function: printvar

varname: my_result

# Print data from previous task

- name: print_previous_output

module: oa-utility

function: printvar

on_success: next_step

---

### `setvar()` {#oautility-setvar}

Sets the value of a variable with data propagation

**Parameters:**

- `param`: dict with:
- `varname`: variable name - supports {WALLET:key}, {ENV:var}
- `varvalue`: value to assign (can use input) - supports {WALLET:key}, {ENV:var}
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional)
- `task_store`: (optional)

**Returns:**

tuple: (success, set_value) - propagates the set value

Example YAML:

# Set a static variable

- name: set_counter

module: oa-utility

function: setvar

varname: counter

varvalue: 0

# Set variable from environment

- name: set_api_url

module: oa-utility

function: setvar

varname: api_url

varvalue: "{ENV:API_ENDPOINT}"

# Set variable from previous task output

- name: save_response

module: oa-utility

function: setvar

varname: api_response

# varvalue not specified, uses input from previous task

---

### `dumpvar()` {#oautility-dumpvar}

Exports all gdict variables to a JSON file with data propagation

**Parameters:**

- `param`: dict with:
- `savetofile`: (optional) JSON output file path - supports {WALLET:key}, {ENV:var}
- `include_input`: (optional) also include input in dump
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional)
- `task_store`: (optional)

**Returns:**

tuple: (success, variables_dict) - propagates all variables

Example YAML:

# Dump all variables to file

- name: export_variables

module: oa-utility

function: dumpvar

savetofile: "/tmp/workflow_vars.json"

# Dump variables with dynamic path

- name: export_to_env_path

module: oa-utility

function: dumpvar

savetofile: "{ENV:OUTPUT_DIR}/vars.json"

---

### `transform()` {#oautility-transform}

Transforms data with various operations (upper, lower, strip, etc.)

**Parameters:**

- `param`: dict with:
- `operation`: transformation type ('upper', 'lower', 'strip', 'replace', 'split', 'join')
- `data`: (optional) data to transform
- `input`: (optional) data from previous task
- `options`: (optional) dict with operation-specific options
- `workflow_context`: (optional) workflow context
- `task_id`: (optional)
- `task_store`: (optional)

**Returns:**

tuple: (success, transformed_data)

Example YAML:

# Convert to uppercase

- name: uppercase_text

module: oa-utility

function: transform

operation: upper

data: "hello world"

# Transform previous task output

- name: clean_output

module: oa-utility

function: transform

operation: strip

# Uses input from previous task

# Split string

- name: split_csv

module: oa-utility

function: transform

operation: split

data: "a,b,c,d"

options:

separator: ","

---

### `condition()` {#oautility-condition}

Evaluates a condition for workflow branching

**Parameters:**

- `param`: dict with:
- `left`: left operand - supports {WALLET:key}, {ENV:var}
- `right`: right operand - supports {WALLET:key}, {ENV:var}
- `operator`: comparison operator ('equals', 'not_equals', 'contains', 'greater', 'less', 'exists', 'is_empty')
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional)
- `task_store`: (optional)

**Returns:**

tuple: (condition_result, output_dict) - task_success reflects condition result

Example YAML:

# Check if value equals expected

- name: check_status

module: oa-utility

function: condition

left: "{WALLET:status}"

operator: equals

right: "success"

on_success: success_handler

on_failure: error_handler

# Check if variable exists

- name: check_var_exists

module: oa-utility

function: condition

left: "{WALLET:result}"

operator: exists

# Numeric comparison

- name: check_count

module: oa-utility

function: condition

left: "{WALLET:count}"

operator: greater

right: 100

---

### `merge()` {#oautility-merge}

Merges data from multiple sources

**Parameters:**

- `param`: dict with:
- `merge_type`: 'dict'|'list'|'concat'
- `sources`: list of keys from workflow_context
- `separator`: (optional) for concat - supports {WALLET:key}, {ENV:var}
- `input`: (optional) data from previous task
- `workflow_context`: (optional) workflow context
- `task_id`: (optional)
- `task_store`: (optional)

**Returns:**

tuple: (success, merged_data)

Example YAML:

# Merge dictionaries

- name: merge_configs

module: oa-utility

function: merge

merge_type: dict

sources:

- task1_output

- task2_output

# Concatenate strings with separator

- name: join_messages

module: oa-utility

function: merge

merge_type: concat

sources:

- msg1

- msg2

separator: " | "

# Merge lists

- name: combine_arrays

module: oa-utility

function: merge

merge_type: list

sources:

- list1

- list2

---


---

*Documentation automatically generated by `generate_readme.py`*
