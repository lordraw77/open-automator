# Open-Automator – Documentazione Moduli

Sistema di workflow automation modulare per orchestrare operazioni su file, rete, database, sistema operativo, notifiche, Git e utilità generiche.

Ogni funzione di modulo ha la stessa firma logica lato YAML:

name: task_name
module: nome-modulo
function: nome-funzione

parametri specifici...

Tutti i task supportano opzionalmente:
- `task_id`: identificativo univoco del task
- `task_store`: oggetto di store dei risultati

---

## Modulo `oa-io` – File & ZIP

Operazioni su file, directory e testi.

### copy

Copia file o directory.

Parametri:
- `srcpath` (str): percorso sorgente.
- `dstpath` (str): percorso destinazione.
- `recursive` (bool): se `true`, copia directory in modo ricorsivo.

Esempio:

module: oa-io
function: copy
srcpath: "/tmp/src"
dstpath: "/tmp/dst"
recursive: true


### zip

Crea un archivio ZIP.

Parametri:
- `zipfilename` (str): path del file ZIP di output.
- `pathtozip` (list|str): percorso o lista di percorsi da comprimere.
- `zipfilter` (str): filtro sui file (es. `"*"` o `".log"`).

### unzip

Estrae un archivio ZIP.

Parametri:
- `zipfilename` (str): file ZIP di origine.
- `pathwhereunzip` (str): cartella di destinazione.

### readfile

Legge il contenuto di un file e lo salva in una variabile globale.

Parametri:
- `filename` (str): file da leggere.
- `varname` (str): nome della variabile in cui salvare il contenuto.

### writefile

Scrive il contenuto di una variabile su file.

Parametri:
- `filename` (str): file di destinazione.
- `varname` (str): nome variabile da scrivere.

### replace

Sostituisce testo nel contenuto di una variabile.

Parametri:
- `varname` (str): variabile di input.
- `leftvalue` (str): testo da cercare.
- `rightvalue` (str): testo sostitutivo.

---

## Modulo `oa-network` – HTTP/HTTPS

Chiamate HTTP/HTTPS semplici per health-check, API, etc.

### httpget

Esegue una richiesta HTTP GET.

Parametri:
- `host` (str): hostname o IP.
- `port` (int): porta HTTP.
- `get` (str): path (es. `"/api/status"`).
- `printout` (bool, opzionale): log del body.
- `saveonvar` (str, opzionale): salva il body in `gdict[saveonvar]`.

Esempio:

module: oa-network
function: httpget
host: "example.com"
port: 80
get: "/status"
printout: true
saveonvar: "status_body"


### httpsget

Esegue una richiesta HTTPS GET.

Parametri:
- `host` (str): hostname o IP.
- `port` (int): porta HTTPS.
- `get` (str): path.
- `verify` (bool, opzionale): verifica certificato SSL (default `true`).
- `printout` (bool, opzionale).
- `saveonvar` (str, opzionale).

---

## Modulo `oa-notify` – Notifiche

Invio di notifiche via Telegram e email.

### sendtelegramnotify

Invia un messaggio Telegram.

Parametri:
- `tokenid` (str): token del bot.
- `chatid` (list[str]): lista di chat_id destinatari.
- `message` (str): testo del messaggio (supporta Markdown).
- `printresponse` (bool, opzionale): stampa la risposta JSON dell’API.

Esempio:

module: oa-notify
function: sendtelegramnotify
tokenid: "1234:ABCD"
chatid: ["123456789"]
message: "Deploy completato"
printresponse: false


### sendmailbygmail

Invia email tramite Gmail (SMTP SSL).

Parametri:
- `senderemail` (str): indirizzo mittente.
- `receiveremail` (str): destinatario.
- `senderpassword` (str): password / app password di Gmail.
- `subject` (str): oggetto email.
- `messagetext` (str, opzionale): corpo plain text.
- `messagehtml` (str, opzionale): corpo HTML.

Esempio:

module: oa-notify
function: sendmailbygmail
senderemail: "me@gmail.com"
receiveremail: "you@example.com"
senderpassword: "APP_PASSWORD"
subject: "Workflow status"
messagetext: "Workflow completato con successo"


---

## Modulo `oa-pg` – PostgreSQL

Operazioni su database PostgreSQL con propagazione dei dati.

### select

Esegue una query `SELECT`.

Parametri principali:
- `pgdatabase`, `pgdbhost`, `pgdbusername`, `pgdbpassword`, `pgdbport`
- `statement` (str): query SQL.
- `printout` (bool, opzionale): stampa tabella.
- `tojsonfile` (str, opzionale): salva risultato in JSON.
- `saveonvar` (str, opzionale): salva il resultset.
- `format` (str, opzionale): `'rows' | 'dict' | 'json'` (default `dict`).
- `input` (opzionale): può contenere statement/parametri ereditati da un task precedente.

Return (logico):  
`(success, output_data)` dove `output_data` contiene:
- `rows`, `row_count`, `columns`, `statement`, `host`, `database`.

### execute

Esegue `INSERT/UPDATE/DELETE`.

Parametri principali:
- stessi parametri di connessione di `select`.
- `statement` (str): SQL DML.
- `printout` (bool, opzionale): stampa righe affette.
- `fail_on_zero` (bool, opzionale): se `true`, 0 righe affette = failure logica.
- `tojsonfile` (str, opzionale).

### insert (helper)

Esegue `INSERT` usando dati in input.

Parametri:
- `pgdatabase`, `pgdbhost`, `pgdbusername`, `pgdbpassword`, `pgdbport`
- `table` (str): tabella di destinazione.
- `data` (dict | list[dict], opzionale).
- `input` (opzionale): può contenere `rows` da task precedente.

---

## Modulo `oa-system` – Comandi locali, SSH, SCP, systemd

### runcmd

Esegue un comando locale.

Parametri:
- `command` (str): comando shell.
- `printout` (bool, opzionale).
- `shell` (bool, opzionale, default `true`).
- `timeout` (int, opzionale).
- `saveonvar` (str, opzionale): salva stdout.
- `input` (opzionale): se `command` mancante, può fornire script/comando.

Return: `(success, {stdout, stderr, return_code, command})`.

### systemd

Gestisce servizi systemd su server remoto (via SSH).

Parametri:
- `remoteserver`, `remoteuser`, `remotepassword`, `remoteport`
- `servicename` (str).
- `servicestate` (str): es. `start|stop|restart|status|daemon-reload`.
- `saveonvar` (str, opzionale).
- `input` (opzionale): può fornire `servicename`.

### remotecommand

Esegue un comando remoto via SSH.

Parametri:
- `remoteserver`, `remoteuser`, `remotepassword`, `remoteport`
- `command` (str).
- `saveonvar` (str, opzionale).
- `input` (opzionale): può contenere `command` o script.

### scp

Trasferisce file/directory via SCP.

Parametri:
- `remoteserver`, `remoteuser`, `remotepassword`, `remoteport`
- `localpath` (str | list[str])
- `remotepath` (str | list[str])
- `recursive` (bool)
- `direction` (str): `"localtoremote"` o `"remotetolocal"`.
- `input` (opzionale): può fornire `localpath`.

### execute_script

Esegue script locali con auto-detection interprete.

Parametri:
- `script_path` (str).
- `args` (list[str], opzionale).
- `interpreter` (str, opzionale: es. `python3`, `bash`).
- `timeout` (int, opzionale).
- `input` (opzionale): può fornire `script_path`.

---

## Modulo `oa-utility` – Utility, variabili, trasformazioni

### setsleep

Pausa l’esecuzione.

Parametri:
- `seconds` (int).
- `input` (opzionale): viene propagato in output.

### printvar

Stampa il valore di una variabile o dell’input.

Parametri:
- `varname` (str, opzionale).
- `input` (opzionale).

### setvar

Imposta una variabile.

Parametri:
- `varname` (str).
- `varvalue` (opzionale): se assente, usa `input`.

### dumpvar

Dump di tutte le variabili in JSON.

Parametri:
- `savetofile` (str, opzionale): path JSON.
- `include_input` (bool, opzionale).
- `input` (opzionale).

### transform

Trasformazioni dati comuni.

Parametri:
- `operation` (str): `'filter'|'map'|'extract'|'aggregate'|'passthrough'`.
- `field` / `fields` (a seconda dell’operazione).
- `condition` (dict, per `filter`).
- `agg_type` (str, per `aggregate`: `sum|count|avg`).
- `input`: dati da trasformare (tipicamente lista di dict).

### conditional

Valuta una condizione, utile per branching.

Parametri:
- `condition_type`: `'equals'|'not_equals'|'contains'|'greater'|'less'|'exists'|'is_empty'`.
- `left_value` (opzionale) o `input` + `field`.
- `right_value` (se richiesto).

### merge

Unisce output di più task.

Parametri:
- `merge_type`: `'dict'|'list'|'concat'`.
- `sources`: lista di nomi di task da cui recuperare output via `workflow_context`.
- `input` (opzionale).
- `separator` (per `concat`).

---

## Modulo `oa-git` – Operazioni Git

### clone

Clona un repository.

Parametri:
- `repo_url` (str): HTTPS o SSH.
- `dest_path` (str): path locale.
- `branch` (str, opzionale).
- `depth` (int, opzionale): shallow clone.
- `recursive` (bool, opzionale): submodules.
- `username`, `password` (opzionali, per HTTPS).
- `input` (opzionale): può contenere `repo_url`.

### pull

Esegue `git pull`.

Parametri:
- `repo_path` (str): repo locale.
- `branch` (str, opzionale).
- `rebase` (bool, opzionale).

### push

Esegue `git push`.

Parametri:
- `repo_path` (str).
- `branch` (str, opzionale).
- `remote` (str, default `origin`).
- `force` (bool, opzionale).
- `tags` (bool, opzionale): push dei tag.

### tag

Gestione tag: crea, lista, elimina.

Parametri comuni:
- `repo_path` (str).
- `operation` (str): `'create'|'list'|'delete'`.

Per `create`:
- `tag_name` (str).
- `message` (str, opzionale).
- `commit` (str, opzionale).
- `push` (bool, opzionale).

Per `delete`:
- `tag_name` (str).
- `push` (bool, opzionale).

### branch

Gestione branch: crea, lista, elimina, checkout.

---

## Modulo `oa-pg` – PostgreSQL

Operazioni su database PostgreSQL con propagazione dei dati.

### select

Esegue una query `SELECT`.

Parametri principali:
- `pgdatabase`, `pgdbhost`, `pgdbusername`, `pgdbpassword`, `pgdbport`
- `statement` (str): query SQL.
- `printout` (bool, opzionale): stampa tabella.
- `tojsonfile` (str, opzionale): salva risultato in JSON.
- `saveonvar` (str, opzionale): salva il resultset.
- `format` (str, opzionale): `'rows' | 'dict' | 'json'` (default `dict`).
- `input` (opzionale): può contenere statement/parametri ereditati da un task precedente.

Return (logico):  
`(success, output_data)` dove `output_data` contiene:
- `rows`, `row_count`, `columns`, `statement`, `host`, `database`.

### execute

Esegue `INSERT/UPDATE/DELETE`.

Parametri principali:
- stessi parametri di connessione di `select`.
- `statement` (str): SQL DML.
- `printout` (bool, opzionale): stampa righe affette.
- `fail_on_zero` (bool, opzionale): se `true`, 0 righe affette = failure logica.
- `tojsonfile` (str, opzionale).

### insert (helper)

Esegue `INSERT` usando dati in input.

Parametri:
- `pgdatabase`, `pgdbhost`, `pgdbusername`, `pgdbpassword`, `pgdbport`
- `table` (str): tabella di destinazione.
- `data` (dict | list[dict], opzionale).
- `input` (opzionale): può contenere `rows` da task precedente.

---

## Modulo `oa-system` – Comandi locali, SSH, SCP, systemd

### runcmd

Esegue un comando locale.

Parametri:
- `command` (str): comando shell.
- `printout` (bool, opzionale).
- `shell` (bool, opzionale, default `true`).
- `timeout` (int, opzionale).
- `saveonvar` (str, opzionale): salva stdout.
- `input` (opzionale): se `command` mancante, può fornire script/comando.

Return: `(success, {stdout, stderr, return_code, command})`.

### systemd

Gestisce servizi systemd su server remoto (via SSH).

Parametri:
- `remoteserver`, `remoteuser`, `remotepassword`, `remoteport`
- `servicename` (str).
- `servicestate` (str): es. `start|stop|restart|status|daemon-reload`.
- `saveonvar` (str, opzionale).
- `input` (opzionale): può fornire `servicename`.

### remotecommand

Esegue un comando remoto via SSH.

Parametri:
- `remoteserver`, `remoteuser`, `remotepassword`, `remoteport`
- `command` (str).
- `saveonvar` (str, opzionale).
- `input` (opzionale): può contenere `command` o script.

### scp

Trasferisce file/directory via SCP.

Parametri:
- `remoteserver`, `remoteuser`, `remotepassword`, `remoteport`
- `localpath` (str | list[str])
- `remotepath` (str | list[str])
- `recursive` (bool)
- `direction` (str): `"localtoremote"` o `"remotetolocal"`.
- `input` (opzionale): può fornire `localpath`.

### execute_script

Esegue script locali con auto-detection interprete.

Parametri:
- `script_path` (str).
- `args` (list[str], opzionale).
- `interpreter` (str, opzionale: es. `python3`, `bash`).
- `timeout` (int, opzionale).
- `input` (opzionale): può fornire `script_path`.

---

## Modulo `oa-utility` – Utility, variabili, trasformazioni

### setsleep

Pausa l’esecuzione.

Parametri:
- `seconds` (int).
- `input` (opzionale): viene propagato in output.

### printvar

Stampa il valore di una variabile o dell’input.

Parametri:
- `varname` (str, opzionale).
- `input` (opzionale).

### setvar

Imposta una variabile.

Parametri:
- `varname` (str).
- `varvalue` (opzionale): se assente, usa `input`.

### dumpvar

Dump di tutte le variabili in JSON.

Parametri:
- `savetofile` (str, opzionale): path JSON.
- `include_input` (bool, opzionale).
- `input` (opzionale).

### transform

Trasformazioni dati comuni.

Parametri:
- `operation` (str): `'filter'|'map'|'extract'|'aggregate'|'passthrough'`.
- `field` / `fields` (a seconda dell’operazione).
- `condition` (dict, per `filter`).
- `agg_type` (str, per `aggregate`: `sum|count|avg`).
- `input`: dati da trasformare (tipicamente lista di dict).

### conditional

Valuta una condizione, utile per branching.

Parametri:
- `condition_type`: `'equals'|'not_equals'|'contains'|'greater'|'less'|'exists'|'is_empty'`.
- `left_value` (opzionale) o `input` + `field`.
- `right_value` (se richiesto).

### merge

Unisce output di più task.

Parametri:
- `merge_type`: `'dict'|'list'|'concat'`.
- `sources`: lista di nomi di task da cui recuperare output via `workflow_context`.
- `input` (opzionale).
- `separator` (per `concat`).

---

## Modulo `oa-git` – Operazioni Git

### clone

Clona un repository.

Parametri:
- `repo_url` (str): HTTPS o SSH.
- `dest_path` (str): path locale.
- `branch` (str, opzionale).
- `depth` (int, opzionale): shallow clone.
- `recursive` (bool, opzionale): submodules.
- `username`, `password` (opzionali, per HTTPS).
- `input` (opzionale): può contenere `repo_url`.

### pull

Esegue `git pull`.

Parametri:
- `repo_path` (str): repo locale.
- `branch` (str, opzionale).
- `rebase` (bool, opzionale).

### push

Esegue `git push`.

Parametri:
- `repo_path` (str).
- `branch` (str, opzionale).
- `remote` (str, default `origin`).
- `force` (bool, opzionale).
- `tags` (bool, opzionale): push dei tag.

### tag

Gestione tag: crea, lista, elimina.

Parametri comuni:
- `repo_path` (str).
- `operation` (str): `'create'|'list'|'delete'`.

Per `create`:
- `tag_name` (str).
- `message` (str, opzionale).
- `commit` (str, opzionale).
- `push` (bool, opzionale).

Per `delete`:
- `tag_name` (str).
- `push` (bool, opzionale).

### branch

Gestione branch: crea, lista, elimina, checkout.

Parametri comuni:
- `repo_path` (str).
- `operation` (str): `'create'|'list'|'delete'|'checkout'`.

Per `create`:
- `branch_name` (str).
- `from_branch` (str, opzionale).

Per `delete`:
- `branch_name` (str).
- `force` (bool, opzionale).

Per `checkout`:
- `branch_name` (str).

### status

Mostra lo stato del repository.

Parametri:
- `repo_path` (str).
- `short` (bool, opzionale): formato compatto.

---

## Modulo `oa-pg` – PostgreSQL

Operazioni su database PostgreSQL con propagazione dei dati.

### select

Esegue una query `SELECT`.

Parametri principali:
- `pgdatabase`, `pgdbhost`, `pgdbusername`, `pgdbpassword`, `pgdbport`
- `statement` (str): query SQL.
- `printout` (bool, opzionale): stampa tabella.
- `tojsonfile` (str, opzionale): salva risultato in JSON.
- `saveonvar` (str, opzionale): salva il resultset.
- `format` (str, opzionale): `'rows' | 'dict' | 'json'` (default `dict`).
- `input` (opzionale): può contenere statement/parametri ereditati da un task precedente.

Return (logico):  
`(success, output_data)` dove `output_data` contiene:
- `rows`, `row_count`, `columns`, `statement`, `host`, `database`.

### execute

Esegue `INSERT/UPDATE/DELETE`.

Parametri principali:
- stessi parametri di connessione di `select`.
- `statement` (str): SQL DML.
- `printout` (bool, opzionale): stampa righe affette.
- `fail_on_zero` (bool, opzionale): se `true`, 0 righe affette = failure logica.
- `tojsonfile` (str, opzionale).

### insert (helper)

Esegue `INSERT` usando dati in input.

Parametri:
- `pgdatabase`, `pgdbhost`, `pgdbusername`, `pgdbpassword`, `pgdbport`
- `table` (str): tabella di destinazione.
- `data` (dict | list[dict], opzionale).
- `input` (opzionale): può contenere `rows` da task precedente.

---

## Modulo `oa-system` – Comandi locali, SSH, SCP, systemd

### runcmd

Esegue un comando locale.

Parametri:
- `command` (str): comando shell.
- `printout` (bool, opzionale).
- `shell` (bool, opzionale, default `true`).
- `timeout` (int, opzionale).
- `saveonvar` (str, opzionale): salva stdout.
- `input` (opzionale): se `command` mancante, può fornire script/comando.

Return: `(success, {stdout, stderr, return_code, command})`.

### systemd

Gestisce servizi systemd su server remoto (via SSH).

Parametri:
- `remoteserver`, `remoteuser`, `remotepassword`, `remoteport`
- `servicename` (str).
- `servicestate` (str): es. `start|stop|restart|status|daemon-reload`.
- `saveonvar` (str, opzionale).
- `input` (opzionale): può fornire `servicename`.

### remotecommand

Esegue un comando remoto via SSH.

Parametri:
- `remoteserver`, `remoteuser`, `remotepassword`, `remoteport`
- `command` (str).
- `saveonvar` (str, opzionale).
- `input` (opzionale): può contenere `command` o script.

### scp

Trasferisce file/directory via SCP.

Parametri:
- `remoteserver`, `remoteuser`, `remotepassword`, `remoteport`
- `localpath` (str | list[str])
- `remotepath` (str | list[str])
- `recursive` (bool)
- `direction` (str): `"localtoremote"` o `"remotetolocal"`.
- `input` (opzionale): può fornire `localpath`.

### execute_script

Esegue script locali con auto-detection interprete.

Parametri:
- `script_path` (str).
- `args` (list[str], opzionale).
- `interpreter` (str, opzionale: es. `python3`, `bash`).
- `timeout` (int, opzionale).
- `input` (opzionale): può fornire `script_path`.

---

## Modulo `oa-utility` – Utility, variabili, trasformazioni

### setsleep

Pausa l’esecuzione.

Parametri:
- `seconds` (int).
- `input` (opzionale): viene propagato in output.

### printvar

Stampa il valore di una variabile o dell’input.

Parametri:
- `varname` (str, opzionale).
- `input` (opzionale).

### setvar

Imposta una variabile.

Parametri:
- `varname` (str).
- `varvalue` (opzionale): se assente, usa `input`.

### dumpvar

Dump di tutte le variabili in JSON.

Parametri:
- `savetofile` (str, opzionale): path JSON.
- `include_input` (bool, opzionale).
- `input` (opzionale).

### transform

Trasformazioni dati comuni.

Parametri:
- `operation` (str): `'filter'|'map'|'extract'|'aggregate'|'passthrough'`.
- `field` / `fields` (a seconda dell’operazione).
- `condition` (dict, per `filter`).
- `agg_type` (str, per `aggregate`: `sum|count|avg`).
- `input`: dati da trasformare (tipicamente lista di dict).

### conditional

Valuta una condizione, utile per branching.

Parametri:
- `condition_type`: `'equals'|'not_equals'|'contains'|'greater'|'less'|'exists'|'is_empty'`.
- `left_value` (opzionale) o `input` + `field`.
- `right_value` (se richiesto).

### merge

Unisce output di più task.

Parametri:
- `merge_type`: `'dict'|'list'|'concat'`.
- `sources`: lista di nomi di task da cui recuperare output via `workflow_context`.
- `input` (opzionale).
- `separator` (per `concat`).

---

## Modulo `oa-git` – Operazioni Git

### clone

Clona un repository.

Parametri:
- `repo_url` (str): HTTPS o SSH.
- `dest_path` (str): path locale.
- `branch` (str, opzionale).
- `depth` (int, opzionale): shallow clone.
- `recursive` (bool, opzionale): submodules.
- `username`, `password` (opzionali, per HTTPS).
- `input` (opzionale): può contenere `repo_url`.

### pull

Esegue `git pull`.

Parametri:
- `repo_path` (str): repo locale.
- `branch` (str, opzionale).
- `rebase` (bool, opzionale).

### push

Esegue `git push`.

Parametri:
- `repo_path` (str).
- `branch` (str, opzionale).
- `remote` (str, default `origin`).
- `force` (bool, opzionale).
- `tags` (bool, opzionale): push dei tag.

### tag

Gestione tag: crea, lista, elimina.

Parametri comuni:
- `repo_path` (str).
- `operation` (str): `'create'|'list'|'delete'`.

Per `create`:
- `tag_name` (str).
- `message` (str, opzionale).
- `commit` (str, opzionale).
- `push` (bool, opzionale).

Per `delete`:
- `tag_name` (str).
- `push` (bool, opzionale).

### branch

Gestione branch: crea, lista, elimina, checkout.

Parametri comuni:
- `repo_path` (str).
- `operation` (str): `'create'|'list'|'delete'|'checkout'`.

Per `create`:
- `branch_name` (str).
- `from_branch` (str, opzionale).

Per `delete`:
- `branch_name` (str).
- `force` (bool, opzionale).

Per `checkout`:
- `branch_name` (str).

### status

Mostra lo stato del repository.

Parametri:
- `repo_path` (str).
- `short` (bool, opzionale): formato compatto.

Parametri comuni:
- `repo_path` (str).
- `operation` (str): `'create'|'list'|'delete'|'checkout'`.

Per `create`:
- `branch_name` (str).
- `from_branch` (str, opzionale).

Per `delete`:
- `branch_name` (str).
- `force` (bool, opzionale).

Per `checkout`:
- `branch_name` (str).

### status

Mostra lo stato del repository.

Parametri:
- `repo_path` (str).
- `short` (bool, opzionale): formato compatto.
