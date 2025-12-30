# Guida completa: Estendere i moduli Open-Automator

## 📋 Indice

1. [Struttura di un modulo](#struttura-modulo)
2. [Componenti obbligatori](#componenti-obbligatori)
3. [Pattern di sviluppo](#pattern-sviluppo)
4. [Data Propagation](#data-propagation)
5. [Supporto Placeholder](#supporto-placeholder)
6. [Esempi pratici](#esempi-pratici)

---

## 🏗️ Struttura di un modulo <a name="struttura-modulo"></a>

Ogni modulo Open-Automator segue questa struttura standard:

```python
"""
Open-Automator <NomeModulo> Module
Descrizione delle funzionalità
Supporto per wallet, placeholder WALLET{key}, ENV{var} e VAULT{key}
"""

# Import obbligatori
import oacommon
import inspect
import logging
from loggerconfig import AutomatorLogger

# Logger per il modulo
logger = AutomatorLogger.getlogger("oa-nomemodulo")

# Dizionario globale per condivisione dati tra task
gdict = {}

# Lambda per ottenere il nome della funzione corrente
myself = lambda: inspect.stack()[1][3]

def setgdict(self, gdictparam):
    """Imposta il dizionario globale"""
    global gdict
    gdict = gdictparam
    self.gdict = gdictparam
```

---

## ✅ Componenti obbligatori <a name="componenti-obbligatori"></a>

### 1. Decorator `@oacommon.trace`

Ogni funzione task deve avere questo decorator:

```python
@oacommon.trace
def mia_funzione(self, param):
    # codice...
```

### 2. Struttura standard della funzione

```python
@oacommon.trace
def mia_funzione(self, param):
    """
    Descrizione della funzione

    Args:
        param (dict) con:
            - parametro1: descrizione - supporta WALLET{key}, ENV{var}
            - parametro2: descrizione opzionale
            - input: opzionale dati dal task precedente
            - workflowcontext: opzionale contesto workflow
            - taskid: opzionale id univoco del task
            - taskstore: opzionale istanza di TaskResultStore

    Returns:
        tuple (success, outputdata)
    """
    # 1. Inizializzazione
    funcname = myself()
    logger.info(f"{funcname} - Starting execution")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    # 2. Lista parametri obbligatori
    requiredparams = ["parametro1", "parametro2"]

    try:
        # 3. Validazione parametri
        if not oacommon.checkandloadparam(self, myself, requiredparams, param=param):
            raise ValueError(f"Missing required parameters for {funcname}")

        # 4. Recupera wallet per placeholder
        wallet = gdict.get("wallet")

        # 5. Estrai parametri con supporto placeholder
        param1 = oacommon.getparam(param, "parametro1", wallet) or gdict.get("parametro1")
        param2 = oacommon.getparam(param, "parametro2", wallet) or gdict.get("parametro2")

        # 6. Logica principale
        # ... il tuo codice qui ...

        # 7. Output data per propagation
        outputdata = {
            "result": "valore",
            "status": "completed"
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"{funcname} failed: {e}", exc_info=True)

    finally:
        # 8. Registra risultato nel task store
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    # 9. Return obbligatorio
    return tasksuccess, outputdata
```

---

## 🔄 Data Propagation <a name="data-propagation"></a>

La **data propagation** permette ai task di passare dati automaticamente al task successivo.

### Pattern standard per ricevere input

```python
# Se un parametro non è specificato, prova a usare l'input dal task precedente
if "mioparametro" not in param and "input" in param:
    previnput = param.get("input")

    if isinstance(previnput, dict):
        # Cerca campi specifici
        if "mioparametro" in previnput:
            param["mioparametro"] = previnput["mioparametro"]

        logger.info("Using mioparametro from previous task")

    elif isinstance(previnput, str):
        # Se è una stringa, usala direttamente
        param["mioparametro"] = previnput
```

### Esempi pratici

**Esempio 1: Propagare un file path**

```python
# Task 1: Legge un file
if "filename" not in param and "input" in param:
    previnput = param.get("input")
    if isinstance(previnput, dict):
        if "filepath" in previnput:
            param["filename"] = previnput["filepath"]
        elif "dstpath" in previnput:
            param["filename"] = previnput["dstpath"]
```

**Esempio 2: Propagare dati JSON**

```python
# Task 2: Invia dati via HTTP
if "data" not in param and "input" in param:
    previnput = param.get("input")
    if isinstance(previnput, dict):
        if "json" in previnput:
            param["data"] = previnput["json"]
        else:
            param["data"] = previnput
```

---

## 🔐 Supporto Placeholder <a name="supporto-placeholder"></a>

I placeholder permettono di usare valori da:
- **WALLET{chiave}** - Credenziali sicure
- **ENV{variabile}** - Variabili d'ambiente
- **VAULT{chiave}** - Vault segreti

### Come implementare il supporto

```python
# 1. Recupera il wallet
wallet = gdict.get("wallet")

# 2. Usa oacommon.getparam per risolvere placeholder
valore = oacommon.getparam(param, "chiave", wallet) or gdict.get("chiave")

# 3. Per dict con più valori
headers = {}
headersparam = param.get("headers", {})
if isinstance(headersparam, dict):
    for key, value in headersparam.items():
        if isinstance(value, str):
            # Risolvi placeholder nel valore
            headers[key] = oacommon.getparam(f"{key}={value}", key, wallet) or value
        else:
            headers[key] = value
```

### Esempio in YAML

```yaml
- name: api_call
  module: oa-network
  function: httpsget
  host: "api.example.com"
  port: 443
  get: "/api/data"
  headers:
    Authorization: "Bearer WALLET{api_token}"
    X-Api-Key: "ENV{MY_API_KEY}"
```

---

## 💡 Esempi pratici <a name="esempi-pratici"></a>

### Esempio 1: Aggiungere HTTP PUT a oa-network

Vedi file: `network_extension_httpput.py`

**Workflow YAML di utilizzo:**

```yaml
---
name: UpdateResourceWorkflow
description: Aggiorna una risorsa via HTTP PUT

tasks:
  - name: prepara_dati
    module: oa-utility
    function: setvar
    varname: "resource_data"
    varvalue:
      name: "test"
      value: 123
    onsuccess: aggiorna_risorsa

  - name: aggiorna_risorsa
    module: oa-network
    function: httpput
    host: "api.example.com"
    port: 8080
    path: "/api/resources/1"
    headers:
      Authorization: "Bearer WALLET{api_token}"
    # 'data' viene preso automaticamente dall'input del task precedente
    onsuccess: verifica_risultato

  - name: verifica_risultato
    module: oa-utility
    function: printvar
    onsuccess: END
```

### Esempio 2: Nuovo modulo Docker

Vedi file: `oa-docker.py`

**Workflow YAML di utilizzo:**

```yaml
---
name: DockerNginxWorkflow
description: Avvia container Nginx e recupera i log

tasks:
  - name: avvia_nginx
    module: oa-docker
    function: container_run
    image: "nginx:latest"
    name: "my-nginx"
    ports:
      "8080": "80"
    env:
      NGINX_HOST: "localhost"
      NGINX_PORT: "80"
    detach: true
    onsuccess: attendi
    onfailure: errore

  - name: attendi
    module: oa-utility
    function: sleep
    seconds: 5
    onsuccess: recupera_logs

  - name: recupera_logs
    module: oa-docker
    function: container_logs
    # 'container' viene preso automaticamente da 'avvia_nginx'
    tail: 100
    timestamps: true
    onsuccess: ferma_container

  - name: ferma_container
    module: oa-docker
    function: container_stop
    # 'container' viene propagato automaticamente
    timeout: 10
    onsuccess: END

  - name: errore
    module: oa-utility
    function: printvar
    onsuccess: END
```

### Esempio 3: Estendere oa-utility con nuova funzione

```python
@oacommon.trace
def jsonvalidate(self, param):
    """
    Valida un JSON contro uno schema JSON Schema

    Args:
        param (dict) con:
            - jsondata: JSON da validare (può usare input)
            - schema: JSON Schema per validazione
            - strict: opzionale strict validation (default: True)
            - input: opzionale dati dal task precedente

    Returns:
        tuple (success, validation_result)
    """
    import jsonschema
    from jsonschema import validate

    funcname = myself()
    logger.info("Validating JSON data")

    taskid = param.get("taskid")
    taskstore = param.get("taskstore")
    tasksuccess = True
    errormsg = ""
    outputdata = None

    try:
        wallet = gdict.get("wallet")

        # Data propagation
        jsondata = None
        if "jsondata" in param:
            jsondata = param["jsondata"]
        elif "input" in param:
            previnput = param.get("input")
            if isinstance(previnput, dict):
                if "json" in previnput:
                    jsondata = previnput["json"]
                else:
                    jsondata = previnput
            logger.info("Using JSON from previous task")

        if jsondata is None:
            raise ValueError("No JSON data to validate")

        schema = param.get("schema")
        if not schema:
            raise ValueError("JSON Schema is required")

        strict = param.get("strict", True)

        # Valida JSON
        try:
            validate(instance=jsondata, schema=schema)
            validation_passed = True
            validation_errors = []
            logger.info("JSON validation passed")

        except jsonschema.exceptions.ValidationError as e:
            validation_passed = False
            validation_errors = [str(e)]
            logger.warning(f"JSON validation failed: {e}")

            if strict:
                tasksuccess = False
                errormsg = f"JSON validation failed: {e}"

        outputdata = {
            "valid": validation_passed,
            "errors": validation_errors,
            "data": jsondata,
            "strict_mode": strict
        }

    except Exception as e:
        tasksuccess = False
        errormsg = str(e)
        logger.error(f"JSON validation failed: {e}", exc_info=True)

    finally:
        if taskstore and taskid:
            taskstore.setresult(taskid, tasksuccess, errormsg)

    return tasksuccess, outputdata
```

**Workflow YAML:**

```yaml
---
name: ValidateAPIResponse
description: Valida risposta API contro schema

tasks:
  - name: chiama_api
    module: oa-network
    function: httpget
    host: "api.example.com"
    port: 443
    get: "/api/users/1"
    onsuccess: valida_risposta

  - name: valida_risposta
    module: oa-utility
    function: jsonvalidate
    # jsondata viene preso automaticamente dall'output di chiama_api
    schema:
      type: "object"
      required: ["id", "name", "email"]
      properties:
        id:
          type: "integer"
        name:
          type: "string"
        email:
          type: "string"
          format: "email"
    strict: true
    onsuccess: salva_risultato
    onfailure: gestisci_errore

  - name: salva_risultato
    module: oa-io
    function: writefile
    filename: "/tmp/validated_user.json"
    onsuccess: END

  - name: gestisci_errore
    module: oa-notify
    function: sendtelegramnotify
    tokenid: "WALLET{telegram_bot_token}"
    chatid: ["WALLET{telegram_chat_id}"]
    message: "⚠️ Validazione JSON fallita!"
    onsuccess: END
```

---

## 📝 Checklist per creare un nuovo modulo

- [ ] Import di `oacommon`, `inspect`, `logging`
- [ ] Configurazione `logger = AutomatorLogger.getlogger("oa-modulename")`
- [ ] Definizione `gdict = {}` e `myself = lambda: inspect.stack()[1][3]`
- [ ] Implementazione `setgdict(self, gdictparam)`
- [ ] Decorator `@oacommon.trace` su ogni funzione task
- [ ] Docstring completa con parametri e return
- [ ] Inizializzazione `funcname`, `taskid`, `taskstore`, `tasksuccess`, `errormsg`, `outputdata`
- [ ] Validazione parametri con `checkandloadparam`
- [ ] Supporto data propagation da `input`
- [ ] Risoluzione placeholder con `getparam` e `wallet`
- [ ] Gestione errori con try/except/finally
- [ ] Logging appropriato (info, debug, warning, error)
- [ ] Registrazione risultato con `taskstore.setresult`
- [ ] Return `(tasksuccess, outputdata)`

---

## 🚀 Best Practices

1. **Logging intelligente**: Usa livelli appropriati
   - `INFO`: Operazioni principali
   - `DEBUG`: Dettagli tecnici
   - `WARNING`: Situazioni anomale ma gestibili
   - `ERROR`: Errori critici

2. **Gestione errori specifica**: Cattura eccezioni specifiche prima di `Exception`

```python
except FileNotFoundError as e:
    tasksuccess = False
    errormsg = f"File not found: {str(e)}"
except PermissionError as e:
    tasksuccess = False
    errormsg = f"Permission denied: {str(e)}"
except Exception as e:
    tasksuccess = False
    errormsg = str(e)
```

3. **Data propagation flessibile**: Supporta più formati di input

```python
if "param" not in param and "input" in param:
    previnput = param.get("input")

    # Supporta dict
    if isinstance(previnput, dict):
        param["param"] = previnput.get("campo1") or previnput.get("campo2")

    # Supporta string
    elif isinstance(previnput, str):
        param["param"] = previnput

    # Supporta list
    elif isinstance(previnput, list) and len(previnput) > 0:
        param["param"] = previnput[0]
```

4. **Output strutturato**: Ritorna sempre dict con informazioni utili

```python
outputdata = {
    "status": "success",
    "result": result_value,
    "metadata": {
        "execution_time": elapsed_time,
        "items_processed": count
    }
}
```

---

## 📚 Risorse

- File template: `oa-moduletemplate.py`
- Moduli esistenti da studiare:
  - `oa-network.py` - HTTP/HTTPS requests
  - `oa-io.py` - File operations
  - `oa-git.py` - Git operations
  - `oa-utility.py` - Utility functions

---

**Creato il:** 30 Dicembre 2025  
**Versione:** 1.0
