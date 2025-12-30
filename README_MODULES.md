# Open-Automator - Documentazione Moduli

Documentazione automatica dei moduli e funzioni disponibili.

---

## 📑 Indice Moduli

- [oa-docker](#oadocker) - 3 funzioni
- [oa-git](#oagit) - 6 funzioni
- [oa-io](#oaio) - 7 funzioni
- [oa-json](#oajson) - 7 funzioni
- [oa-moduletemplate](#oamoduletemplate) - 2 funzioni
- [oa-network](#oanetwork) - 4 funzioni
- [oa-notify](#oanotify) - 3 funzioni
- [oa-pg](#oapg) - 3 funzioni
- [oa-system](#oasystem) - 5 funzioni
- [oa-utility](#oautility) - 7 funzioni

---

## oa-docker

### 📋 Funzioni disponibili (3)

- [`container_run()`](#oadocker-container_run) - Avvia un container Docker con data propagation
- [`container_stop()`](#oadocker-container_stop) - Ferma un container Docker con data propagation
- [`container_logs()`](#oadocker-container_logs) - Recupera i log di un container Docker

---

### `container_run()` {#oadocker-container_run}

Avvia un container Docker con data propagation

**Parametri:**

- `param (dict) con`: 
- `image`: nome immagine Docker - supporta WALLET{key}, ENV{var}
- `name`: (opzionale) nome del container - supporta ENV{var}
- `ports`: (opzionale) dict port mapping es. {"8080": "80"}
- `volumes`: (opzionale) dict volume mapping
- `env`: (opzionale) dict variabili ambiente
- `detach`: (opzionale) run in background (default: True)
- `remove`: (opzionale) auto-remove al termine (default: False)
- `command`: (opzionale) comando da eseguire
- `input`: (opzionale) dati dal task precedente
- `workflowcontext`: (opzionale) contesto workflow
- `taskid`: (opzionale) id univoco del task
- `taskstore`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple (success, outputdict) con info sul container

---

### `container_stop()` {#oadocker-container_stop}

Ferma un container Docker con data propagation

**Parametri:**

- `param (dict) con`: 
- `container`: nome o ID del container (può usare input da task precedente)
- `timeout`: (opzionale) timeout in secondi (default: 10)
- `input`: (opzionale) dati dal task precedente
- `workflowcontext`: (opzionale) contesto workflow
- `taskid`: (opzionale) id univoco del task
- `taskstore`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple (success, outputdict) con info sul container fermato

---

### `container_logs()` {#oadocker-container_logs}

Recupera i log di un container Docker

**Parametri:**

- `param (dict) con`: 
- `container`: nome o ID (può usare input da task precedente)
- `tail`: (opzionale) numero righe (default: all)
- `follow`: (opzionale) segui log in real-time (default: False)
- `timestamps`: (opzionale) mostra timestamps (default: False)
- `saveonvar`: (opzionale) salva log in variabile
- `input`: (opzionale) dati dal task precedente
- taskid, taskstore, workflowcontext

**Ritorna:**

tuple (success, logs) - propaga i log

---

## oa-git

### 📋 Funzioni disponibili (6)

- [`clone()`](#oagit-clone) - Clona un repository Git con data propagation
- [`pull()`](#oagit-pull) - Esegue git pull su un repository esistente con data propagation
- [`push()`](#oagit-push) - Esegue git push con data propagation
- [`tag()`](#oagit-tag) - Crea, lista o elimina tag Git con data propagation
- [`branch()`](#oagit-branch) - Gestisce branch Git (crea, lista, elimina, checkout) con data propagation
- [`status()`](#oagit-status) - Ottiene lo status del repository Git con data propagation

---

### `clone()` {#oagit-clone}

Clona un repository Git con data propagation

**Parametri:**

- `param`: dict con:
- `repo_url`: URL del repository (https o ssh) - supporta {WALLET:key}, {ENV:var}
- `dest_path`: path di destinazione locale
- `branch`: (opzionale) branch specifico da clonare
- `depth`: (opzionale) clone shallow con depth specificato
- `recursive`: (opzionale) clone ricorsivo dei submodules, default False
- `username`: (opzionale) username per HTTPS auth - supporta {WALLET:key}, {ENV:var}
- `password`: (opzionale) password/token per HTTPS auth - supporta {WALLET:key}, {ENV:var}
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con info sul clone

---

### `pull()` {#oagit-pull}

Esegue git pull su un repository esistente con data propagation

**Parametri:**

- `param`: dict con:
- `repo_path`: path del repository locale - supporta {ENV:var}
- `branch`: (opzionale) branch da pullare
- `rebase`: (opzionale) usa rebase invece di merge, default False
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con info sul pull

---

### `push()` {#oagit-push}

Esegue git push con data propagation

**Parametri:**

- `param`: dict con:
- `repo_path`: path del repository locale - supporta {ENV:var}
- `branch`: (opzionale) branch da pushare
- `remote`: (opzionale) remote name, default 'origin'
- `force`: (opzionale) force push, default False
- `tags`: (opzionale) push tags, default False
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con info sul push

---

### `tag()` {#oagit-tag}

Crea, lista o elimina tag Git con data propagation

**Parametri:**

- `param`: dict con:
- `repo_path`: path del repository locale - supporta {ENV:var}
- `operation`: 'create'|'list'|'delete'
- `tag_name`: (opzionale) nome del tag (per create/delete) - supporta {ENV:var}
- `message`: (opzionale) messaggio del tag annotato
- `commit`: (opzionale) commit su cui creare il tag
- `push`: (opzionale) push del tag dopo creazione, default False
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con info sui tag

---

### `branch()` {#oagit-branch}

Gestisce branch Git (crea, lista, elimina, checkout) con data propagation

**Parametri:**

- `param`: dict con:
- `repo_path`: path del repository locale - supporta {ENV:var}
- `operation`: 'create'|'list'|'delete'|'checkout'
- `branch_name`: (opzionale) nome del branch (per create/delete/checkout) - supporta {ENV:var}
- `from_branch`: (opzionale) branch/commit sorgente per create
- `force`: (opzionale) force delete, default False
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con info sui branch

---

### `status()` {#oagit-status}

Ottiene lo status del repository Git con data propagation

**Parametri:**

- `param`: dict con:
- `repo_path`: path del repository locale - supporta {ENV:var}
- `short`: (opzionale) formato short, default False
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con status info

---

## oa-io

### 📋 Funzioni disponibili (7)

- [`copy()`](#oaio-copy) - Copia file o directory con data propagation
- [`zip()`](#oaio-zip) - Crea un archivio ZIP con data propagation
- [`unzip()`](#oaio-unzip) - Estrae un archivio ZIP con data propagation
- [`readfile()`](#oaio-readfile) - Legge il contenuto di un file con data propagation
- [`writefile()`](#oaio-writefile) - Scrive contenuto in un file con data propagation
- [`replace()`](#oaio-replace) - Sostituisce testo in una variabile con data propagation
- [`loadvarfromjson()`](#oaio-loadvarfromjson) - Carica variabili da un file JSON nel gdict con data propagation

---

### `copy()` {#oaio-copy}

Copia file o directory con data propagation

**Parametri:**

- `param`: dict con:
- `srcpath`: path sorgente - supporta {WALLET:key}, {ENV:var}
- `dstpath`: path destinazione - supporta {WALLET:key}, {ENV:var}
- `recursive`: True per directory, False per file singolo
- input (opzionale, da task precedente)
- workflow_context (opzionale)
- task_id (opzionale)
- task_store (opzionale)

**Ritorna:**

tuple: (success, output_dict) con informazioni sulla copia

---

### `zip()` {#oaio-zip}

Crea un archivio ZIP con data propagation

**Parametri:**

- `param`: dict con:
- `zipfilename`: nome file ZIP - supporta {WALLET:key}, {ENV:var}
- `pathtozip`: path da comprimere (può usare input da task precedente) - supporta {ENV:var}
- `zipfilter`: filtro file (es. "*.txt" o "*")
- input (opzionale, da task precedente)
- workflow_context (opzionale)
- task_id (opzionale)
- task_store (opzionale)

**Ritorna:**

tuple: (success, output_dict) con info sul ZIP creato

---

### `unzip()` {#oaio-unzip}

Estrae un archivio ZIP con data propagation

**Parametri:**

- `param`: dict con:
- `zipfilename`: file ZIP da estrarre (può usare input da task precedente) - supporta {ENV:var}
- `pathwhereunzip`: directory destinazione - supporta {ENV:var}
- input (opzionale, da task precedente)
- workflow_context (opzionale)
- task_id (opzionale)
- task_store (opzionale)

**Ritorna:**

tuple: (success, output_dict) con info sull'estrazione

---

### `readfile()` {#oaio-readfile}

Legge il contenuto di un file con data propagation

**Parametri:**

- `param`: dict con:
- `filename`: file da leggere (può usare input da task precedente) - supporta {WALLET:key}, {ENV:var}
- varname (opzionale se si vuole solo ritornare il contenuto)
- input (opzionale, da task precedente)
- workflow_context (opzionale)
- task_id (opzionale)
- task_store (opzionale)

**Ritorna:**

tuple: (success, file_content) - il contenuto del file viene propagato

---

### `writefile()` {#oaio-writefile}

Scrive contenuto in un file con data propagation

**Parametri:**

- `param`: dict con:
- `filename`: file da scrivere - supporta {WALLET:key}, {ENV:var}
- varname (opzionale se c'è input dal task precedente)
- `content (opzionale, alternativa a varname) - supporta {WALLET`: key}, {ENV:var}
- input (opzionale, da task precedente)
- workflow_context (opzionale)
- task_id (opzionale)
- task_store (opzionale)

**Ritorna:**

tuple: (success, output_dict) con info sul file scritto

---

### `replace()` {#oaio-replace}

Sostituisce testo in una variabile con data propagation

**Parametri:**

- `param`: dict con:
- varname (opzionale se c'è input)
- `leftvalue`: testo da cercare
- `rightvalue`: testo sostitutivo
- input (opzionale, da task precedente)
- workflow_context (opzionale)
- task_id (opzionale)
- task_store (opzionale)

**Ritorna:**

tuple: (success, modified_content)

---

### `loadvarfromjson()` {#oaio-loadvarfromjson}

Carica variabili da un file JSON nel gdict con data propagation

**Parametri:**

- `param`: dict con:
- `filename`: file JSON (può usare input da task precedente) - supporta {WALLET:key}, {ENV:var}
- input (opzionale, da task precedente)
- workflow_context (opzionale)
- task_id (opzionale)
- task_store (opzionale)

**Ritorna:**

tuple: (success, json_data) - ritorna i dati JSON parsati

---

## oa-json

### 📋 Funzioni disponibili (7)

- [`jsonfilter()`](#oajson-jsonfilter) - Filtra elementi in un array JSON basandosi su condizioni
- [`jsonextract()`](#oajson-jsonextract) - Estrae campi specifici da oggetti JSON
- [`jsontransform()`](#oajson-jsontransform) - Trasforma dati JSON applicando mapping e trasformazioni
- [`jsonmerge()`](#oajson-jsonmerge) - Unisce più oggetti/array JSON
- [`jsonaggregate()`](#oajson-jsonaggregate) - Aggrega dati JSON (sum, avg, count, min, max, group)
- [`jsonvalidate()`](#oajson-jsonvalidate) - Valida JSON contro un JSON Schema
- [`jsonsort()`](#oajson-jsonsort) - Ordina array JSON per campo

---

### `jsonfilter()` {#oajson-jsonfilter}

Filtra elementi in un array JSON basandosi su condizioni

**Parametri:**

- `param (dict) con`: 
- `data`: opzionale dati JSON (può usare input da task precedente)
- `field`: campo su cui filtrare - supporta WALLET{key}, ENV{var}
- `operator`: ==, !=, >, <, >=, <=, contains, in, exists
- `value`: valore di confronto - supporta WALLET{key}, ENV{var}
- `case_sensitive`: opzionale (default: True)
- `saveonvar`: opzionale salva risultato in variabile
- `input`: opzionale dati dal task precedente
- `workflowcontext`: opzionale contesto workflow
- `taskid`: opzionale id univoco del task
- `taskstore`: opzionale istanza di TaskResultStore

**Ritorna:**

tuple (success, filtered_data)

Example:

Input: [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

Filter: field="age", operator=">", value=26

Output: [{"name": "Alice", "age": 30}]

---

### `jsonextract()` {#oajson-jsonextract}

Estrae campi specifici da oggetti JSON

**Parametri:**

- `param (dict) con`: 
- `data`: opzionale dati JSON (può usare input)
- `fields`: lista di campi da estrarre - supporta WALLET{key}, ENV{var}
- `flatten`: opzionale appiattisce oggetti nested (default: False)
- `keep_nulls`: opzionale mantieni campi null (default: False)
- `saveonvar`: opzionale salva risultato
- `input`: opzionale dati dal task precedente
- taskid, taskstore, workflowcontext

**Ritorna:**

tuple (success, extracted_data)

Example:

Input: [{"name": "Alice", "age": 30, "city": "Rome"}]

Fields: ["name", "city"]

Output: [{"name": "Alice", "city": "Rome"}]

---

### `jsontransform()` {#oajson-jsontransform}

Trasforma dati JSON applicando mapping e trasformazioni

**Parametri:**

- `param (dict) con`: 
- `data`: opzionale dati JSON (può usare input)
- `mapping`: dict con {new_field: old_field} o {new_field: "function:old_field"}
- `functions`: opzionale dict con funzioni custom
- `add_fields`: opzionale dict con nuovi campi statici
- `remove_fields`: opzionale lista campi da rimuovere
- `saveonvar`: opzionale
- `input`: opzionale dati dal task precedente

**Ritorna:**

tuple (success, transformed_data)

Example:

Input: {"first_name": "Alice", "last_name": "Smith", "age": 30}

Mapping: {"name": "first_name", "years": "age"}

Output: {"name": "Alice", "years": 30}

---

### `jsonmerge()` {#oajson-jsonmerge}

Unisce più oggetti/array JSON

**Parametri:**

- `param (dict) con`: 
- `sources`: lista di chiavi da workflowcontext o lista di dati diretti
- `merge_type`: "dict" (merge objects), "array" (concatena arrays), "deep" (deep merge)
- `overwrite`: opzionale per dict merge (default: True)
- `unique`: opzionale rimuovi duplicati in array merge (default: False)
- `saveonvar`: opzionale
- `input`: opzionale dati dal task precedente (viene aggiunto al merge)
- `workflowcontext`: opzionale contesto workflow

**Ritorna:**

tuple (success, merged_data)

---

### `jsonaggregate()` {#oajson-jsonaggregate}

Aggrega dati JSON (sum, avg, count, min, max, group)

**Parametri:**

- `param (dict) con`: 
- `data`: opzionale dati JSON array (può usare input)
- `operation`: sum, avg, count, min, max, group
- `field`: campo su cui aggregare - supporta WALLET{key}, ENV{var}
- `group_by`: opzionale campo per raggruppamento
- `saveonvar`: opzionale
- `input`: opzionale dati dal task precedente

**Ritorna:**

tuple (success, aggregated_data)

Example:

Input: [{"category": "A", "value": 10}, {"category": "A", "value": 20}]

Operation: sum, Field: value, Group_by: category

Output: {"A": 30}

---

### `jsonvalidate()` {#oajson-jsonvalidate}

Valida JSON contro un JSON Schema

**Parametri:**

- `param (dict) con`: 
- `data`: opzionale dati JSON (può usare input)
- `schema`: JSON Schema per validazione
- `strict`: opzionale fail on validation error (default: True)
- `saveonvar`: opzionale
- `input`: opzionale dati dal task precedente

**Ritorna:**

tuple (success, validation_result)

---

### `jsonsort()` {#oajson-jsonsort}

Ordina array JSON per campo

**Parametri:**

- `param (dict) con`: 
- `data`: opzionale dati JSON array (può usare input)
- `sort_by`: campo per ordinamento - supporta WALLET{key}, ENV{var}
- `reverse`: opzionale ordine decrescente (default: False)
- `numeric`: opzionale ordina come numeri (default: auto-detect)
- `saveonvar`: opzionale
- `input`: opzionale dati dal task precedente

**Ritorna:**

tuple (success, sorted_data)

---

## oa-moduletemplate

### 📋 Funzioni disponibili (2)

- [`templatefunction()`](#oamoduletemplate-templatefunction) - Descrizione della funzione con data propagation
- [`advanced_function()`](#oamoduletemplate-advanced_function) - Funzione avanzata con supporto per operazioni multiple

---

### `templatefunction()` {#oamoduletemplate-templatefunction}

Descrizione della funzione con data propagation

**Parametri:**

- `param`: dict con:
- `param1`: (tipo) descrizione parametro obbligatorio
- `param2`: (tipo) descrizione parametro obbligatorio (supporta {var})
- `param3`: (tipo, opzionale) descrizione parametro opzionale
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_data) dove output_data contiene i risultati

Example YAML:

- name: example_task

module: oa-moduletemplate

function: templatefunction

param1: "value1"

param2: "value2 with {variable}"

param3: "optional_value"

on_success: next_task

on_failure: error_handler

---

### `advanced_function()` {#oamoduletemplate-advanced_function}

Funzione avanzata con supporto per operazioni multiple

**Parametri:**

- `param`: dict con:
- `operation`: (str) 'create'|'read'|'update'|'delete'
- `target`: (str) target dell'operazione
- `data`: (dict, opzionale) dati per l'operazione
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_data)

---

## oa-network

### 📋 Funzioni disponibili (4)

- [`httpget()`](#oanetwork-httpget) - Esegue una richiesta HTTP GET con data propagation
- [`httpsget()`](#oanetwork-httpsget) - Esegue una richiesta HTTPS GET con data propagation
- [`httppost()`](#oanetwork-httppost) - Esegue una richiesta HTTP POST con data propagation
- [`httpspost()`](#oanetwork-httpspost) - Esegue una richiesta HTTPS POST con data propagation

---

### `httpget()` {#oanetwork-httpget}

Esegue una richiesta HTTP GET con data propagation

**Parametri:**

- `param`: dict con:
- `host`: hostname o IP (può derivare da input precedente) - supporta {WALLET:key}, {ENV:var}
- `port`: porta HTTP - supporta {ENV:var}
- `get`: path della richiesta - supporta {WALLET:key}, {ENV:var}
- `printout`: (opzionale) stampa response
- `saveonvar`: (opzionale) salva response in variabile
- `headers`: (opzionale) dict con headers custom - supporta {WALLET:key} nei valori
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con response data

---

### `httpsget()` {#oanetwork-httpsget}

Esegue una richiesta HTTPS GET con data propagation

**Parametri:**

- `param`: dict con:
- `host`: hostname o IP (può derivare da input precedente) - supporta {WALLET:key}, {ENV:var}
- `port`: porta HTTPS - supporta {ENV:var}
- `get`: path della richiesta - supporta {WALLET:key}, {ENV:var}
- `verify`: (opzionale) verifica certificato SSL, default True
- `printout`: (opzionale) stampa response
- `saveonvar`: (opzionale) salva response in variabile
- `headers`: (opzionale) dict con headers custom - supporta {WALLET:key} nei valori (es. token)
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con response data

---

### `httppost()` {#oanetwork-httppost}

Esegue una richiesta HTTP POST con data propagation

**Parametri:**

- `param`: dict con:
- `host`: hostname o IP - supporta {WALLET:key}, {ENV:var}
- `port`: porta HTTP - supporta {ENV:var}
- `path`: path della richiesta - supporta {WALLET:key}, {ENV:var}
- `data`: dati da inviare (può venire da input precedente) - supporta {WALLET:key}
- `headers`: (opzionale) dict con headers custom - supporta {WALLET:key} nei valori
- `content_type`: (opzionale) default 'application/json'
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con response data

---

### `httpspost()` {#oanetwork-httpspost}

Esegue una richiesta HTTPS POST con data propagation

**Parametri:**

- `param`: dict con:
- `host`: hostname o IP - supporta {WALLET:key}, {ENV:var}
- `port`: porta HTTPS - supporta {ENV:var}
- `path`: path della richiesta - supporta {WALLET:key}, {ENV:var}
- `data`: dati da inviare (può venire da input precedente) - supporta {WALLET:key}
- `headers`: (opzionale) dict con headers custom - supporta {WALLET:key} nei valori (es. API key)
- `content_type`: (opzionale) default 'application/json'
- `verify`: (opzionale) verifica certificato SSL, default True
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con response data

---

## oa-notify

### 📋 Funzioni disponibili (3)

- [`sendtelegramnotify()`](#oanotify-sendtelegramnotify) - Invia un messaggio Telegram con bot API e data propagation
- [`sendmailbygmail()`](#oanotify-sendmailbygmail) - Invia email tramite Gmail SMTP SSL con data propagation
- [`formatmessage()`](#oanotify-formatmessage) - Formatta un messaggio da dati strutturati (helper per notifiche)

---

### `sendtelegramnotify()` {#oanotify-sendtelegramnotify}

Invia un messaggio Telegram con bot API e data propagation

**Parametri:**

- `param`: dict con:
- `tokenid`: token del bot Telegram - supporta {WALLET:key}, {ENV:var}
- `chatid`: lista di chat_id - supporta {WALLET:key}, {ENV:var}
- `message`: messaggio da inviare (può venire da input precedente) - supporta {WALLET:key}, {ENV:var}
- `printresponse`: (opzionale) stampa response
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con info sull'invio

---

### `sendmailbygmail()` {#oanotify-sendmailbygmail}

Invia email tramite Gmail SMTP SSL con data propagation

**Parametri:**

- `param`: dict con:
- `senderemail`: email mittente - supporta {WALLET:key}, {ENV:var}
- `receiveremail`: email destinatario - supporta {WALLET:key}, {ENV:var}
- `senderpassword`: password mittente - supporta {WALLET:key}, {VAULT:key}
- `subject`: oggetto email - supporta {WALLET:key}, {ENV:var}
- `messagetext`: (opzionale) testo plain - supporta {WALLET:key}, {ENV:var}
- `messagehtml`: (opzionale) testo HTML - supporta {WALLET:key}, {ENV:var}
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con info sull'invio

---

### `formatmessage()` {#oanotify-formatmessage}

Formatta un messaggio da dati strutturati (helper per notifiche)

**Parametri:**

- `param`: dict con:
- `template`: (opzionale) template del messaggio con placeholder {key} - supporta {WALLET:key}, {ENV:var}
- `data`: (opzionale) dict con dati da formattare
- `format`: (opzionale) 'json', 'text', 'markdown'
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, formatted_message)

---

## oa-pg

### 📋 Funzioni disponibili (3)

- [`select()`](#oapg-select) - Esegue SELECT su PostgreSQL con data propagation
- [`execute()`](#oapg-execute) - Esegue INSERT/UPDATE/DELETE su PostgreSQL con data propagation
- [`insert()`](#oapg-insert) - Helper per INSERT con data propagation da input precedente

---

### `select()` {#oapg-select}

Esegue SELECT su PostgreSQL con data propagation

**Parametri:**

- `param`: dict con:
- `pgdatabase`: nome database - supporta {WALLET:key}, {ENV:var}
- `pgdbhost`: host - supporta {WALLET:key}, {ENV:var}
- `pgdbusername`: username - supporta {WALLET:key}, {ENV:var}
- `pgdbpassword`: password - supporta {WALLET:key}, {VAULT:key}
- `pgdbport`: porta - supporta {ENV:var}
- `statement`: query SQL (può usare input da task precedente) - supporta {WALLET:key}, {ENV:var}
- `printout`: (opzionale) stampa risultato, default False
- `tojsonfile`: (opzionale) percorso file JSON
- `saveonvar`: (opzionale) salva in variabile
- `format`: (opzionale) 'rows', 'dict', 'json' - default 'dict'
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_data) con risultati query

---

### `execute()` {#oapg-execute}

Esegue INSERT/UPDATE/DELETE su PostgreSQL con data propagation

**Parametri:**

- `param`: dict con:
- `pgdatabase`: nome database - supporta {WALLET:key}, {ENV:var}
- `pgdbhost`: host - supporta {WALLET:key}, {ENV:var}
- `pgdbusername`: username - supporta {WALLET:key}, {ENV:var}
- `pgdbpassword`: password - supporta {WALLET:key}, {VAULT:key}
- `pgdbport`: porta - supporta {ENV:var}
- `statement`: statement SQL (può usare input da task precedente) - supporta {WALLET:key}, {ENV:var}
- `printout`: (opzionale) stampa risultato, default False
- `fail_on_zero`: (opzionale) fallisce se 0 righe affette, default False
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_data) con numero righe affette

---

### `insert()` {#oapg-insert}

Helper per INSERT con data propagation da input precedente

**Parametri:**

- `param`: dict con:
- `pgdatabase, pgdbhost, pgdbusername, pgdbpassword, pgdbport - supportano {WALLET`: key}, {ENV:var}
- `table`: nome tabella - supporta {WALLET:key}, {ENV:var}
- `data`: (opzionale) dict o lista di dict da inserire
- `input`: (opzionale) dati dal task precedente (se formato corretto)
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_data)

---

## oa-system

### 📋 Funzioni disponibili (5)

- [`runcmd()`](#oasystem-runcmd) - Esegue un comando shell locale con data propagation
- [`systemd()`](#oasystem-systemd) - Gestisce servizi systemd su server remoto con data propagation
- [`remotecommand()`](#oasystem-remotecommand) - Esegue un comando remoto via SSH con data propagation
- [`scp()`](#oasystem-scp) - Trasferisce file/directory via SCP con data propagation
- [`execute_script()`](#oasystem-execute_script) - Esegue uno script locale e propaga l'output

---

### `runcmd()` {#oasystem-runcmd}

Esegue un comando shell locale con data propagation

**Parametri:**

- `param`: dict con:
- `command`: comando da eseguire (può usare input da task precedente) - supporta {WALLET:key}, {ENV:var}
- `printout`: (opzionale) stampa output, default False
- `saveonvar`: (opzionale) salva output in variabile
- `shell`: (opzionale) usa shell, default True
- `timeout`: (opzionale) timeout in secondi
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con output del comando

---

### `systemd()` {#oasystem-systemd}

Gestisce servizi systemd su server remoto con data propagation

**Parametri:**

- `param`: dict con:
- `remoteserver`: host remoto - supporta {WALLET:key}, {ENV:var}
- `remoteuser`: username SSH - supporta {WALLET:key}, {ENV:var}
- `remotepassword`: password SSH - supporta {WALLET:key}, {VAULT:key}
- `remoteport`: porta SSH - supporta {ENV:var}
- `servicename`: nome del servizio - supporta {WALLET:key}, {ENV:var}
- `servicestate`: start|stop|restart|status|daemon-reload
- `saveonvar`: (opzionale) salva output in variabile
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con output systemd

---

### `remotecommand()` {#oasystem-remotecommand}

Esegue un comando remoto via SSH con data propagation

**Parametri:**

- `param`: dict con:
- `remoteserver`: host remoto - supporta {WALLET:key}, {ENV:var}
- `remoteuser`: username SSH - supporta {WALLET:key}, {ENV:var}
- `remotepassword`: password SSH - supporta {WALLET:key}, {VAULT:key}
- `remoteport`: porta SSH - supporta {ENV:var}
- `command`: comando da eseguire (può usare input da task precedente) - supporta {WALLET:key}, {ENV:var}
- `saveonvar`: (opzionale) salva output in variabile
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con output del comando remoto

---

### `scp()` {#oasystem-scp}

Trasferisce file/directory via SCP con data propagation

**Parametri:**

- `param`: dict con:
- `remoteserver`: host remoto - supporta {WALLET:key}, {ENV:var}
- `remoteuser`: username SSH - supporta {WALLET:key}, {ENV:var}
- `remotepassword`: password SSH - supporta {WALLET:key}, {VAULT:key}
- `remoteport`: porta SSH - supporta {ENV:var}
- `localpath`: path locale (può usare input da task precedente) - supporta {WALLET:key}, {ENV:var}
- `remotepath`: path remoto - supporta {WALLET:key}, {ENV:var}
- `recursive`: True/False
- `direction`: localtoremote|remotetolocal
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con info sul trasferimento

---

### `execute_script()` {#oasystem-execute_script}

Esegue uno script locale e propaga l'output

**Parametri:**

- `param`: dict con:
- `script_path`: path dello script (può usare input da task precedente) - supporta {WALLET:key}, {ENV:var}
- `args`: (opzionale) lista di argomenti - supporta {WALLET:key}, {ENV:var}
- `interpreter`: (opzionale) interprete (es. 'python3', 'bash'), default auto-detect
- `timeout`: (opzionale) timeout in secondi
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale) id univoco del task
- `task_store`: (opzionale) istanza di TaskResultStore

**Ritorna:**

tuple: (success, output_dict) con output dello script

---

## oa-utility

### 📋 Funzioni disponibili (7)

- [`setsleep()`](#oautility-setsleep) - Pausa l'esecuzione per un numero di secondi con data propagation
- [`printvar()`](#oautility-printvar) - Stampa il valore di una variabile o dell'input con data propagation
- [`setvar()`](#oautility-setvar) - Imposta il valore di una variabile con data propagation
- [`dumpvar()`](#oautility-dumpvar) - Esporta tutte le variabili del gdict in un file JSON con data propagation
- [`transform()`](#oautility-transform) - Trasforma dati con operazioni comuni (filter, map, extract)
- [`conditional()`](#oautility-conditional) - Valuta una condizione e propaga risultato
- [`merge()`](#oautility-merge) - Unisce dati da più sorgenti

---

### `setsleep()` {#oautility-setsleep}

Pausa l'esecuzione per un numero di secondi con data propagation

**Parametri:**

- `param`: dict con:
- `seconds`: numero di secondi da attendere - supporta {WALLET:key}, {ENV:var}
- `input`: (opzionale) dati dal task precedente (passthrough)
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale)
- `task_store`: (opzionale)

**Ritorna:**

tuple: (success, input_data) - propaga l'input ricevuto

---

### `printvar()` {#oautility-printvar}

Stampa il valore di una variabile o dell'input con data propagation

**Parametri:**

- `param`: dict con:
- `varname`: (opzionale) nome della variabile da stampare - supporta {WALLET:key}, {ENV:var}
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale)
- `task_store`: (opzionale)

**Ritorna:**

tuple: (success, printed_value) - propaga il valore stampato

---

### `setvar()` {#oautility-setvar}

Imposta il valore di una variabile con data propagation

**Parametri:**

- `param`: dict con:
- `varname`: nome della variabile - supporta {WALLET:key}, {ENV:var}
- `varvalue`: valore da assegnare (può usare input) - supporta {WALLET:key}, {ENV:var}
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale)
- `task_store`: (opzionale)

**Ritorna:**

tuple: (success, set_value) - propaga il valore impostato

---

### `dumpvar()` {#oautility-dumpvar}

Esporta tutte le variabili del gdict in un file JSON con data propagation

**Parametri:**

- `param`: dict con:
- `savetofile`: (opzionale) path del file JSON di output - supporta {WALLET:key}, {ENV:var}
- `include_input`: (opzionale) include anche input nel dump
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale)
- `task_store`: (opzionale)

**Ritorna:**

tuple: (success, variables_dict) - propaga tutte le variabili

---

### `transform()` {#oautility-transform}

Trasforma dati con operazioni comuni (filter, map, extract)

**Parametri:**

- `param`: dict con:
- `operation`: 'filter'|'map'|'extract'|'aggregate'
- `field`: (opzionale) campo su cui operare - supporta {WALLET:key}, {ENV:var}
- `condition`: (opzionale) per filter - supporta {WALLET:key}, {ENV:var} nei valori
- `expression`: (opzionale) per map
- `fields`: (opzionale) lista campi per extract
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale)
- `task_store`: (opzionale)

**Ritorna:**

tuple: (success, transformed_data)

---

### `conditional()` {#oautility-conditional}

Valuta una condizione e propaga risultato

**Parametri:**

- `param`: dict con:
- `condition_type`: 'equals'|'contains'|'greater'|'less'|'exists'
- `left_value`: valore sinistro (può usare input) - supporta {WALLET:key}, {ENV:var}
- `right_value`: valore destro - supporta {WALLET:key}, {ENV:var}
- `field`: (opzionale) campo da estrarre da input - supporta {WALLET:key}, {ENV:var}
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale)
- `task_store`: (opzionale)

**Ritorna:**

tuple: (condition_result, evaluation_details)

---

### `merge()` {#oautility-merge}

Unisce dati da più sorgenti

**Parametri:**

- `param`: dict con:
- `merge_type`: 'dict'|'list'|'concat'
- `sources`: lista di chiavi da workflow_context
- `separator`: (opzionale) per concat - supporta {WALLET:key}, {ENV:var}
- `input`: (opzionale) dati dal task precedente
- `workflow_context`: (opzionale) contesto workflow
- `task_id`: (opzionale)
- `task_store`: (opzionale)

**Ritorna:**

tuple: (success, merged_data)

---


---

*Documentazione generata automaticamente da `generate_readme.py`*
