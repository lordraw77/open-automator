# Open-Automator - Guida Docker Completa

Documentazione dettagliata per la costruzione e l'utilizzo di tutti i container Docker del progetto Open-Automator.

---

## Indice
1. [Dockerfile.streamlit - Interfaccia Web](#dockerfile-streamlit)
2. [Dockerfile.shell - Automazioni CLI](#dockerfile-shell)
3. [Dockerfile.wallet - Gestione Wallet](#dockerfile-wallet)
4. [Dockerfile.fastapi - Backend API REST](#dockerfile-fastapi)
5. [Docker Compose - Orchestrazione Completa](#docker-compose)

---

## Dockerfile.streamlit - Interfaccia Web Streamlit

### Descrizione
Container per l'interfaccia web grafica Streamlit che permette di gestire Open-Automator tramite browser.

### Costruzione
```bash
docker build -f Dockerfile.streamlit -t open-automator-streamlit:latest .
```

### File Richiesti
- `requirements.txt` - Dipendenze Python
- `.streamlit/config.toml` - Configurazione Streamlit
- `streamlit_app.py` - Applicazione principale
- Tutti i file `*.py` nella root
- Cartella `modules/` con i moduli Python

### Esecuzione Base
```bash
docker run -d \
  --name oa-streamlit \
  -p 8502:8502 \
  -v $(pwd)/data:/data \
  -v $(pwd)/workflows:/workflows \
  open-automator-streamlit:latest
```

### Configurazione Avanzata
```bash
docker run -d \
  --name oa-streamlit \
  -p 8502:8502 \
  -v $(pwd)/data:/data \
  -v $(pwd)/workflows:/workflows \
  -v $(pwd)/.streamlit:/home/automator/.streamlit \
  --restart unless-stopped \
  open-automator-streamlit:latest
```

### Caratteristiche Tecniche
- **Immagine base:** python:3.12-slim-bookworm
- **Porta esposta:** 8502
- **Utente:** automator (UID 1000)
- **Healthcheck:** `http://localhost:8502/_stcore/health` (ogni 30s)
- **Directory persistenti:** `/data`, `/workflows`
- **Comando:** `streamlit run streamlit_app.py --server.port 8502 --server.address 0.0.0.0`

### Accesso
Apri il browser su: `http://localhost:8502`

### Variabili d'Ambiente Opzionali
```bash
-e STREAMLIT_SERVER_PORT=8502
-e STREAMLIT_SERVER_ADDRESS=0.0.0.0
-e STREAMLIT_SERVER_HEADLESS=true
```

---

## Dockerfile.shell - Container per Automazioni CLI

### Descrizione
Container ottimizzato per eseguire automazioni da riga di comando con accesso a Git, PostgreSQL e SSH.

### Costruzione
```bash
docker build -f Dockerfile.shell -t open-automator-shell:latest .
```

### File Richiesti
- `requirements.txt` - Dipendenze Python
- `automator.py` - Script principale (entry point)
- Tutti i file `*.py` nella root
- Cartella `modules/` con i moduli Python
- `dashboard.html`

### Esecuzione Interattiva
```bash
docker run -it --rm \
  --name oa-shell \
  -v $(pwd)/data:/data \
  -v $(pwd)/workflows:/workflows \
  -e OA_WALLET_FILE=/data/wallet.enc \
  -e OA_WALLET_PASSWORD=tuapassword \
  open-automator-shell:latest [comando]
```

### Esempi di Utilizzo

#### Visualizza Help
```bash
docker run --rm open-automator-shell:latest --help
```

#### Esegui un Workflow
```bash
docker run --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/workflows:/workflows \
  -e OA_WALLET_FILE=/data/wallet.enc \
  -e OA_WALLET_PASSWORD=miapwd \
  open-automator-shell:latest run workflow1
```

#### Modalità Daemon
```bash
docker run -d \
  --name oa-daemon \
  -v $(pwd)/data:/data \
  -v $(pwd)/workflows:/workflows \
  -e OA_WALLET_FILE=/data/wallet.enc \
  -e OA_WALLET_PASSWORD=miapwd \
  --restart unless-stopped \
  open-automator-shell:latest daemon
```

#### Lista Workflows
```bash
docker run --rm \
  -v $(pwd)/workflows:/workflows \
  open-automator-shell:latest list
```

#### Debug Mode
```bash
docker run -it --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/workflows:/workflows \
  -e OA_WALLET_FILE=/data/wallet.enc \
  -e OA_WALLET_PASSWORD=miapwd \
  open-automator-shell:latest --debug /workflows/mywf.yaml
```

### Caratteristiche Tecniche
- **Immagine base:** python:3.12-slim-bookworm
- **Utente:** automator (UID 1000)
- **Entry point:** `python3.12 automator.py`
- **Strumenti inclusi:** curl, git, openssh-client, postgresql-client, ca-certificates, build-essential
- **Directory persistenti:** `/data`, `/workflows`

### Variabili d'Ambiente
| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `OA_WALLET_FILE` | `/data/wallet.enc` | Percorso del wallet criptato |
| `OA_WALLET_PASSWORD` | `changeme` | Password per decifrare il wallet |
| `PYTHONUNBUFFERED` | `1` | Output Python non bufferizzato |

### Mounting di File SSH/Git
```bash
docker run -it --rm \
  -v $(pwd)/data:/data \
  -v ~/.ssh:/home/automator/.ssh:ro \
  -v ~/.gitconfig:/home/automator/.gitconfig:ro \
  open-automator-shell:latest [comando]
```

---

## Dockerfile.wallet - Tool Gestione Wallet

### Descrizione
Container leggero dedicato alla gestione sicura delle credenziali (wallet criptato).

### Costruzione
```bash
docker build -f Dockerfile.wallet -t open-automator-wallet:latest .
```

### File Richiesti
- `requirements-wallet.txt` - Dipendenze minime per il wallet
- `wallet.py` - Libreria wallet
- `wallet-tool.py` - Tool CLI (entry point)
- `logger_config.py` - Configurazione logging

### Esecuzione Interattiva
```bash
docker run -it --rm \
  --name oa-wallet \
  -v $(pwd)/data:/data \
  open-automator-wallet:latest [comando]
```

### Comandi Disponibili

#### Visualizza Help
```bash
docker run --rm open-automator-wallet:latest --help
```

#### Crea Nuovo Wallet
```bash
docker run -it --rm \
  -v $(pwd)/data:/data \
  open-automator-wallet:latest create
```

#### Aggiungi Credenziale
```bash
docker run -it --rm \
  -v $(pwd)/data:/data \
  open-automator-wallet:latest add
```

#### Lista Credenziali
```bash
docker run -it --rm \
  -v $(pwd)/data:/data \
  open-automator-wallet:latest list
```

#### Mostra Credenziale
```bash
docker run -it --rm \
  -v $(pwd)/data:/data \
  open-automator-wallet:latest get nome_credenziale
```

#### Elimina Credenziale
```bash
docker run -it --rm \
  -v $(pwd)/data:/data \
  open-automator-wallet:latest delete nome_credenziale
```

#### Esporta Wallet
```bash
docker run -it --rm \
  -v $(pwd)/data:/data \
  open-automator-wallet:latest export > wallet_backup.json
```

#### Importa Wallet
```bash
docker run -it --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/wallet_backup.json:/tmp/backup.json:ro \
  open-automator-wallet:latest import /tmp/backup.json
```

#### Cambia Password
```bash
docker run -it --rm \
  -v $(pwd)/data:/data \
  open-automator-wallet:latest change-password
```

### Caratteristiche Tecniche
- **Immagine base:** python:3.12-slim-bookworm
- **Utente:** automator (UID 1000)
- **Entry point:** `python3.12 wallet-tool.py`
- **Strumenti inclusi:** curl (minimo)
- **Directory persistenti:** `/data`
- **Ottimizzazione:** Container minimalista solo con dipendenze wallet

### Best Practices
- Usa sempre volumi per persistere `/data`
- Esegui con `--rm` per rimuovere il container dopo l'uso
- Non salvare la password in variabili d'ambiente
- Fai backup regolari del wallet con `export`

---

## Dockerfile.fastapi - Backend API REST

### Descrizione
Container FastAPI per esporre tutte le funzionalità di Open-Automator tramite API REST.

### Costruzione
```bash
docker build -f Dockerfile.fastapi -t open-automator-fastapi:latest .
```

### File Richiesti
- `requirements.txt` - Dipendenze Python (incluso FastAPI e Uvicorn)
- `oa-webui.py` - Applicazione FastAPI
- Tutti i file `*.py` nella root
- Cartella `modules/` con i moduli Python
- `dashboard.html`

### Esecuzione Base
```bash
docker run -d \
  --name oa-fastapi \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  -v $(pwd)/workflows:/workflows \
  open-automator-fastapi:latest
```

### Esecuzione con Configurazione Custom
```bash
docker run -d \
  --name oa-fastapi \
  -p 8000:8000 \
  -v $(pwd)/data:/data \
  -v $(pwd)/workflows:/workflows \
  -e OA_WALLET_FILE=/data/wallet.enc \
  -e OA_WALLET_PASSWORD=miapwd \
  -e UVICORN_LOG_LEVEL=info \
  --restart unless-stopped \
  open-automator-fastapi:latest
```

### Modalità Development
```bash
docker run -d \
  --name oa-fastapi-dev \
  -p 8000:8000 \
  -v $(pwd):/app \
  -e UVICORN_RELOAD=true \
  open-automator-fastapi:latest \
  uvicorn oa-webui:app --host 0.0.0.0 --port 8000 --reload
```

### Caratteristiche Tecniche
- **Immagine base:** python:3.12-slim-bookworm
- **Porta esposta:** 8000
- **Utente:** automator (UID 1000)
- **Server:** Uvicorn ASGI
- **Healthcheck:** `http://localhost:8000/health` (ogni 30s)
- **Directory persistenti:** `/data`, `/workflows`
- **Comando:** `uvicorn oa-webui:app --host 0.0.0.0 --port 8000`

### Endpoint Principali
- **Documentazione interattiva (Swagger):** `http://localhost:8000/docs`
- **Documentazione alternativa (ReDoc):** `http://localhost:8000/redoc`
- **Health check:** `http://localhost:8000/health`
- **OpenAPI schema:** `http://localhost:8000/openapi.json`

### Esempi di Chiamate API
```bash
# Health check
curl http://localhost:8000/health

# Lista workflows
curl http://localhost:8000/api/workflows

# Esegui workflow
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow_name": "test"}'
```

### Variabili d'Ambiente
| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `UVICORN_LOG_LEVEL` | `info` | Livello log (debug, info, warning, error) |
| `UVICORN_RELOAD` | `false` | Hot reload (solo development) |
| `OA_WALLET_FILE` | - | Percorso wallet criptato |
| `OA_WALLET_PASSWORD` | - | Password wallet |

### Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name automator.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Docker Compose - Orchestrazione Completa

### File docker-compose.yml
```yaml
version: '3.8'

services:
  # Backend API
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile.fastapi
    container_name: oa-fastapi
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
      - ./workflows:/workflows
    environment:
      - OA_WALLET_FILE=/data/wallet.enc
      - OA_WALLET_PASSWORD=${WALLET_PASSWORD}
      - UVICORN_LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  # Web UI Streamlit
  streamlit:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    container_name: oa-streamlit
    ports:
      - "8502:8502"
    volumes:
      - ./data:/data
      - ./workflows:/workflows
    restart: unless-stopped
    depends_on:
      - fastapi
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8502/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  # Automator Daemon
  automator:
    build:
      context: .
      dockerfile: Dockerfile.shell
    container_name: oa-automator
    volumes:
      - ./data:/data
      - ./workflows:/workflows
      - ~/.ssh:/home/automator/.ssh:ro
    environment:
      - OA_WALLET_FILE=/data/wallet.enc
      - OA_WALLET_PASSWORD=${WALLET_PASSWORD}
    command: daemon
    restart: unless-stopped
    depends_on:
      - fastapi

volumes:
  data:
  workflows:
```

### File .env
```bash
# Crea un file .env nella stessa directory
WALLET_PASSWORD=your_secure_password_here
```

### Comandi Docker Compose

#### Avvio Completo
```bash
# Prima build
docker-compose build

# Avvio servizi
docker-compose up -d

# Visualizza logs
docker-compose logs -f

# Visualizza logs di un singolo servizio
docker-compose logs -f streamlit
```

#### Gestione Servizi
```bash
# Stop tutti i servizi
docker-compose stop

# Start tutti i servizi
docker-compose start

# Restart tutti i servizi
docker-compose restart

# Stop e rimuovi container
docker-compose down

# Stop, rimuovi container e volumi
docker-compose down -v
```

#### Build e Update
```bash
# Rebuild dopo modifiche
docker-compose build --no-cache

# Rebuild e restart
docker-compose up -d --build

# Rebuild singolo servizio
docker-compose build fastapi
docker-compose up -d fastapi
```

#### Scaling
```bash
# Scala il servizio automator
docker-compose up -d --scale automator=3
```

#### Esecuzione Comandi nei Container
```bash
# Shell nel container fastapi
docker-compose exec fastapi bash

# Esegui comando nel container shell
docker-compose exec automator python automator.py --help

# Gestione wallet
docker-compose run --rm wallet-tool list
```

### Docker Compose con Wallet Tool
```yaml
# Aggiungi al docker-compose.yml
  wallet-tool:
    build:
      context: .
      dockerfile: Dockerfile.wallet
    container_name: oa-wallet
    volumes:
      - ./data:/data
    profiles:
      - tools
```

Utilizzo:
```bash
# Esegui con profilo tools
docker-compose --profile tools run --rm wallet-tool create
docker-compose --profile tools run --rm wallet-tool list
```

---

## Troubleshooting Comune

### Problema: Container non si avvia
```bash
# Verifica logs
docker logs oa-fastapi

# Verifica configurazione
docker inspect oa-fastapi
```

### Problema: Permessi sui volumi
```bash
# Correggi ownership
sudo chown -R 1000:1000 ./data ./workflows
```

### Problema: Porta già in uso
```bash
# Cambia porta nel docker-compose.yml
ports:
  - "8001:8000"  # Invece di 8000:8000
```

### Problema: Healthcheck fallisce
```bash
# Disabilita temporaneamente healthcheck
docker run -d --no-healthcheck oa-fastapi
```

---

## Best Practices

1. **Sicurezza**
   - Non committare file `.env` su Git
   - Usa secrets per password in produzione
   - Esegui sempre come utente non-root

2. **Performance**
   - Usa volumi named per dati persistenti
   - Limita risorse con `--memory` e `--cpus`
   - Usa multi-stage build per immagini più leggere

3. **Manutenzione**
   - Fai backup regolari del wallet
   - Monitora logs con `docker-compose logs`
   - Aggiorna regolarmente le immagini base

4. **Development**
   - Usa volumi bind mount per hot reload
   - Separa environment dev/prod
   - Usa `docker-compose.override.yml` per config locali

---

## Comandi Utili

```bash
# Pulizia container stopped
docker container prune

# Pulizia immagini unused
docker image prune -a

# Pulizia completa sistema Docker
docker system prune -a --volumes

# Visualizza uso spazio
docker system df

# Backup del wallet
docker run --rm -v $(pwd)/data:/data open-automator-wallet:latest export > backup_$(date +%Y%m%d).json

# Restore del wallet
docker run -it --rm -v $(pwd)/data:/data -v $(pwd)/backup.json:/tmp/backup.json:ro \
  open-automator-wallet:latest import /tmp/backup.json
```

---

## Supporto e Contributi

Per ulteriori informazioni, consulta la documentazione completa del progetto Open-Automator.
