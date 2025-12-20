Open-Automator Web UI
Architettura
text
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (dashboard.html)                 │
│  • Upload YAML workflows                                     │
│  • Visualizza workflow caricati                              │
│  • Esegui workflow manualmente                               │
│  • Monitora esecuzione real-time (WebSocket)                 │
│  • Visualizza risultati e output dei task                    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST API + WebSocket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (oa-webui.py - FastAPI)             │
│  • /api/workflows/upload - Carica YAML                       │
│  • /api/workflows - Lista workflows                          │
│  • /api/workflows/{id}/execute - Esegui workflow             │
│  • /api/workflows/{id}/status - Stato esecuzione             │
│  • /api/workflows/{id}/results - Risultati completi          │
│  • /ws/{id} - WebSocket per aggiornamenti real-time          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Core Engine (automator.py)                  │
│  • WorkflowEngine - Esecuzione workflow                      │
│  • WorkflowContext - Data propagation tra task               │
│  • TaskResultStore - Storage risultati thread-safe           │
│  • Wallet - Gestione credenziali sicure                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               Moduli di automazione                          │
│  • oa-pg.py - PostgreSQL operations                          │
│  • oa-git.py - Git operations                                │
│  • oa-io.py - File I/O operations                            │
│  • oa-network.py - HTTP/REST operations                      │
│  • oa-system.py - System commands                            │
│  • oa-utility.py - Utilities (sleep, vars, transform)        │
│  • oa-notify.py - Notifications                              │
└─────────────────────────────────────────────────────────────┘
Installazione
1. Installa dipendenze Web UI
bash
pip install -r requirements-webui.txt
2. Configura Wallet (opzionale ma raccomandato)
bash
# Crea wallet per credenziali sicure
export OA_WALLET_FILE="wallet.enc"
export OA_WALLET_PASSWORD="your_secure_password"
3. Avvia il server
bash
# Metodo 1: Direttamente con uvicorn
python -m uvicorn oa-webui:app --host 0.0.0.0 --port 8000 --reload

# Metodo 2: Script Python
python oa-webui.py
4. Apri il Dashboard
Apri il browser e vai su:

text
http://localhost:8000/dashboard.html
O copia il file dashboard.html in una directory statica e aprilo direttamente.

Funzionalità
📤 Upload Workflow
Clicca su "Choose YAML File"

Seleziona il tuo workflow YAML

Il workflow viene caricato e validato automaticamente

📋 Gestione Workflow
Lista Workflows: Visualizza tutti i workflow caricati

Selezione: Clicca su un workflow per vedere i dettagli

Status Badge: Indica lo stato (loaded, running, completed, failed)

▶️ Esecuzione
Seleziona un workflow dalla lista

Clicca su "Execute Workflow"

Monitora l'esecuzione in tempo reale via WebSocket

Visualizza i risultati di ogni task con:

Status (success/failed)

Output data (con data propagation)

Duration

Error messages (se presenti)

🔄 Aggiornamenti Real-Time
WebSocket Connection: Aggiornamenti automatici durante l'esecuzione

Polling Fallback: Refresh ogni 2 secondi se WebSocket non disponibile

Connection Status: Indicatore visuale in alto a destra

📊 Data Propagation Visualization
I risultati mostrano:

Output di ogni task

Data propagation tra task collegati

Variabili del WorkflowContext

Errori e stack trace

Esempio Workflow YAML
text
- tasks:
  - name: query_database
    module: oa-pg
    function: select
    pgdatabase: mydb
    pgdbhost: localhost
    pgdbusername: "${WALLET:db_user}"
    pgdbpassword: "${WALLET:db_pass}"
    pgdbport: 5432
    statement: "SELECT * FROM users WHERE active = true"
    format: dict
    on_success: transform_data
    on_failure: notify_error

  - name: transform_data
    module: oa-utility
    function: transform
    operation: extract
    fields: ['id', 'email', 'name']
    on_success: save_results

  - name: save_results
    module: oa-io
    function: writefile
    filename: /tmp/users.json
    on_success: end

  - name: notify_error
    module: oa-notify
    function: send
    message: "Database query failed"
    on_success: end
API Endpoints
Upload Workflow
bash
curl -X POST http://localhost:8000/api/workflows/upload \
  -F "file=@workflow.yaml"
List Workflows
bash
curl http://localhost:8000/api/workflows
Execute Workflow
bash
curl -X POST http://localhost:8000/api/workflows/{workflow_id}/execute
Get Status
bash
curl http://localhost:8000/api/workflows/{workflow_id}/status
Get Results
bash
curl http://localhost:8000/api/workflows/{workflow_id}/results
Integrazione con Moduli Esistenti
Il backend oa-webui.py si integra perfettamente con:

WorkflowEngine
python
engine = WorkflowEngine(tasks, gdict, task_store, debug, debug2)
success, context = engine.execute()
TaskResultStore
python
task_store = TaskResultStore()
# Thread-safe storage per risultati task
results = task_store.all_results()
Wallet (Placeholder Resolution)
python
# Supporto automatico per:
# ${WALLET:key} - Credenziali dal wallet criptato
# ${ENV:var} - Variabili d'ambiente
# ${VAULT:key} - Alias per WALLET
Data Propagation
python
# Ogni task riceve automaticamente:
task_params['input'] = last_output  # Output task precedente
task_params['workflow_context'] = context  # Contesto completo
task_params['task_id'] = task_id
task_params['task_store'] = task_store
Sicurezza
Produzione
Per deployment in produzione, modifica oa-webui.py:

python
# Rimuovi CORS permissivo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Solo domini specifici
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Aggiungi autenticazione
from fastapi.security import HTTPBearer
security = HTTPBearer()

@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, credentials: HTTPBearer = Depends(security)):
    # Valida token
    ...
HTTPS
Usa un reverse proxy (nginx, traefik) per HTTPS:

text
server {
    listen 443 ssl;
    server_name automator.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
Troubleshooting
WebSocket non si connette
Verifica che il server sia in esecuzione

Controlla firewall/proxy

Usa polling manuale con "Refresh Status"

Workflow non viene eseguito
Verifica sintassi YAML

Controlla log del server: tail -f ./logs/automator.log

Verifica wallet e credenziali

Errori di import moduli
Assicurati che i moduli oa-*.py siano nella stessa directory

Verifica path in sys.path

Estensioni Future
Autenticazione Multi-Utente
python
from fastapi_users import FastAPIUsers
# Integra sistema autenticazione
Scheduling
python
from apscheduler.schedulers.background import BackgroundScheduler
# Schedule automatico workflow
Notifiche
python
# Integra con oa-notify.py per notifiche email/Slack
Database Persistence
python
# Salva workflow e risultati in PostgreSQL
Licenza
Open-Automator è rilasciato sotto licenza MIT.

