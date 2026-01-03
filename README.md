# 🔄 Open Automator

**A powerful, modular workflow automation platform with encrypted secrets management, REST APIs, and multiple user interfaces.**

[![Docker Hub](https://img.shields.io/badge/Docker-Hub-blue?logo=docker)](https://hub.docker.com/u/lordraw)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/lordraw77/open-automator)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://python.org)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Images](#docker-images)
- [Usage](#usage)
- [Workflow Examples](#workflow-examples)
- [Configuration](#configuration)
- [Contributing](#contributing)

---

## 🎯 Overview

Open Automator is a comprehensive workflow automation system designed for DevOps, data pipelines, and integration tasks. It provides:

- **YAML-based workflow definitions** with conditional branching
- **Encrypted secrets management** (Wallet system with Fernet encryption)
- **Multiple interfaces**: CLI, REST API, FastAPI WebUI, Streamlit Dashboard
- **Modular task system** for easy extensibility
- **Centralized workflow management** with execution history
- **Docker-first architecture** for portability and scalability

---

## 🏗️ Architecture

Open Automator consists of **4 microservices** that can be deployed independently or together:

```
┌─────────────────────────────────────────────────────────────┐
│                    Open Automator Platform                  │
├─────────────────┬──────────────────┬──────────────┬─────────┤
│   Wallet        │   Streamlit UI   │  FastAPI     │  Shell  │
│   Service       │   Dashboard      │  WebUI       │  CLI    │
│                 │                  │              │         │
│  Port: N/A      │  Port: 8501/8502 │  Port: 8000  │  N/A    │
│  (Utility)      │  (Frontend)      │  (API)       │  (Tool) │
└─────────────────┴──────────────────┴──────────────┴─────────┘
         │                 │                 │           │
         └─────────────────┴─────────────────┴───────────┘
                           │
                    Shared Volumes:
                    - /app/workflows (YAML definitions)
                    - /app/data (secrets, state)
                    - /app/logs (execution logs)
```

### Component Roles

| Component | Docker Image | Purpose |
|-----------|--------------|---------|
| **Wallet** | `lordraw/open-automator-wallet` | Encrypted secrets management utility |
| **Streamlit** | `lordraw/open-automator-streamlit` | Interactive web dashboard for workflow management and api |
| **FastAPI** | `lordraw/open-automator-fastapi` | REST API server for programmatic access |
| **Shell** | `lordraw/open-automator-shell` | CLI tool for direct workflow execution |

---

## ✨ Features

### Core Capabilities

- ✅ **Workflow Engine**: YAML-based task orchestration with conditional branching
- 🔒 **Secure Secrets**: Encrypted wallet (PBKDF2 + Fernet) or plain JSON for development
- 🔄 **Task Chaining**: Pass outputs between tasks automatically
- 📊 **Execution Tracking**: Full history with results, duration, and error logs
- 🧩 **Modular Design**: Easy to add custom task modules
- 🌐 **Multiple Interfaces**: Choose CLI, REST API, FastAPI WebUI, or Streamlit
- 🐳 **Docker Native**: All components containerized for easy deployment

### Advanced Features

- **Parallel Execution**: Configurable concurrent workflow limit
- **WebSocket Support**: Real-time execution updates (FastAPI)
- **Workflow Visualization**: Mermaid diagrams in Streamlit UI
- **Environment Placeholders**: `${ENV:VAR}`, `${WALLET:key}`, `${VAULT:key}`
- **Task Store**: Persistent result storage across executions
- **CORS Enabled**: API ready for frontend integration

---

## 📦 Prerequisites

- **Docker** 20.10+ and **Docker Compose** 1.29+
- **Python 3.8+** (for local development)
- **Git** (to clone repository)

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/lordraw77/open-automator.git
cd open-automator
```

### 2. Create Directory Structure

```bash
mkdir -p workflows data logs
```

### 3. Create Sample Workflow

Create `workflows/hello.yaml`:

```yaml
name: hello_world
description: Simple hello world workflow
variables:
  MESSAGE: "Hello from Open Automator!"

tasks:
  - name: print_message
    module: oautils
    function: print_text
    text: "${MESSAGE}"
    on_success: end
```

### 4. Launch with Docker Compose

```bash
docker-compose up -d
```

### 5. Access Interfaces

- **Streamlit Dashboard**: http://localhost:8501
- **Streamlit API**: http://localhost:8502
- **FastAPI WebUI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 6. Execute Your First Workflow

**Via Streamlit**: Open browser → Select workflow → Click "Execute"

**Via API**:
```bash
curl "http://localhost:8502/?WORKFLOW=op-deploydata.yaml"
```
**Via REST API**:
```bash
 curl -X 'POST' \
  'http://localhost:8000/api/workflows/wf_20260103155033/execute' \
  -H 'accept: application/json' \
  -d ''
```

**Via CLI**:
```bash
docker exec open-automator-shell python automator.py workflows/hello.yaml
```

---

## 🐳 Docker Images

All images are available on Docker Hub: `lordraw/open-automator-*`

### Pull Images

```bash
docker pull lordraw/open-automator-wallet:latest
docker pull lordraw/open-automator-streamlit:latest
docker pull lordraw/open-automator-fastapi:latest
docker pull lordraw/open-automator-shell:latest
```

### Build Locally

```bash
# Build all images
./buildWellet.sh      # Wallet utility
./buildStreamlit.sh   # Streamlit UI
./buildFastapi.sh     # FastAPI server
./buildShell.sh       # CLI tool

# Or build specific image
docker build -f Dockerfile.streamlit -t lordraw/open-automator-streamlit:latest .
```

---

## 📖 Usage

### Workflow Definition (YAML)

```yaml
name: data_pipeline
description: Extract, transform, load data
variables:
  API_URL: "https://api.example.com/data"
  DB_HOST: "${ENV:DATABASE_HOST}"
  DB_PASSWORD: "${WALLET:db_password}"

tasks:
  - name: fetch_data
    module: oahttp
    function: get_request
    url: "${API_URL}"
    on_success: transform_data
    on_failure: notify_error

  - name: transform_data
    module: oautils
    function: process_json
    on_success: save_to_db
    on_failure: notify_error

  - name: save_to_db
    module: oadatabase
    function: insert_records
    host: "${DB_HOST}"
    password: "${DB_PASSWORD}"
    on_success: end
    on_failure: notify_error

  - name: notify_error
    module: oanotify
    function: send_alert
    message: "Pipeline failed"
    on_success: end
```

### Creating Encrypted Wallet

```bash
# Interactive mode
docker exec -it open-automator-wallet python wallet.py create

# Programmatic mode
docker exec open-automator-wallet python -c "
from wallet import Wallet
wallet = Wallet('data/wallet.enc')
secrets = {
    'api_key': 'sk-1234567890',
    'db_password': 'supersecret',
    'oauth_token': 'ya29.xxxxx'
}
wallet.create_wallet(secrets, 'my_master_password')
"
```

### Environment Variables

Configure via `.env` file or `docker-compose.yml`:

```bash
# Wallet Configuration
OA_WALLET_FILE=/app/data/wallet.enc
OA_WALLET_PASSWORD=your_master_password

# API Configuration
FASTAPI_PORT=8000
FASTAPI_HOST=0.0.0.0
MAX_CONCURRENT_JOBS=5

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Paths
OA_WORKFLOWS_DIR=/app/workflows
OA_DATA_DIR=/app/data
OA_LOGS_DIR=/app/logs

# Logging
OA_LOG_LEVEL=INFO
```

---

## 📝 Workflow Examples

### Example 1: HTTP API Integration

```yaml
tasks:
  - name: get_weather
    module: oahttp
    function: get_request
    url: "https://api.openweathermap.org/data/2.5/weather"
    params:
      q: "London"
      appid: "${WALLET:weather_api_key}"
    on_success: parse_response

  - name: parse_response
    module: oautils
    function: extract_field
    field: "main.temp"
    on_success: send_notification

  - name: send_notification
    module: oanotify
    function: send_email
    to: "user@example.com"
    subject: "Weather Update"
    on_success: end
```

### Example 2: File Processing Pipeline

```yaml
tasks:
  - name: read_csv
    module: oafiles
    function: read_csv
    filepath: "/app/data/input.csv"
    on_success: filter_rows

  - name: filter_rows
    module: oadataframe
    function: filter
    condition: "age > 18"
    on_success: write_output

  - name: write_output
    module: oafiles
    function: write_json
    filepath: "/app/data/output.json"
    on_success: end
```

### Example 3: Conditional Branching

```yaml
tasks:
  - name: check_status
    module: oahttp
    function: get_request
    url: "https://status.example.com/health"
    on_success: process_success
    on_failure: trigger_alert

  - name: process_success
    module: oautils
    function: log_message
    message: "Service is healthy"
    on_success: end

  - name: trigger_alert
    module: oanotify
    function: send_alert
    severity: "critical"
    message: "Service is down!"
    on_success: end
```

---

## ⚙️ Configuration

### Docker Compose Example

```yaml
version: '3.8'

services:
  fastapi:
    image: lordraw/open-automator-fastapi:latest
    container_name: open-automator-api
    ports:
      - "8000:8000"
    environment:
      - FASTAPI_PORT=8000
      - OA_WALLET_FILE=/app/data/wallet.enc
      - OA_WALLET_PASSWORD=changeme
      - MAX_CONCURRENT_JOBS=10
    volumes:
      - ./workflows:/app/workflows
      - ./data:/app/data
      - ./logs:/app/logs

  streamlit:
    image: lordraw/open-automator-streamlit:latest
    container_name: open-automator-ui
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - OA_WORKFLOWS_DIR=/app/workflows
    volumes:
      - ./workflows:/app/workflows
      - ./data:/app/data
      - ./logs:/app/logs

  shell:
    image: lordraw/open-automator-shell:latest
    container_name: open-automator-cli
    stdin_open: true
    tty: true
    volumes:
      - ./workflows:/app/workflows
      - ./data:/app/data
      - ./logs:/app/logs
```

---

## 🛠️ Development

### Project Structure

```
open-automator/
├── automator.py              # Core workflow engine
├── workflow_manager.py       # Centralized execution manager
├── wallet.py                 # Secrets management
├── api_server.py            # Flask API (legacy)
├── oa-webui.py              # FastAPI server
├── streamlit_app.py         # Streamlit dashboard
├── modules/                 # Task modules
│   ├── oahttp.py           # HTTP requests
│   ├── oautils.py          # Utilities
│   ├── oadatabase.py       # Database operations
│   └── ...
├── Dockerfile.wallet        # Wallet image
├── Dockerfile.streamlit     # Streamlit image
├── Dockerfile.fastapi       # FastAPI image
├── Dockerfile.shell         # Shell image
├── VERSION                   # version file
```

### Adding Custom Modules
visit [Extending-Modules](https://github.com/lordraw77/open-automator/wiki/Extending-Modules) for detailed instructions.



---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the MIT License.

---

## 🔗 Links

- **Docker Hub**: [lordraw/open-automator-*](https://hub.docker.com/u/lordraw)
- **GitHub**: [github.com/lordraw77/open-automator](https://github.com/lordraw77/open-automator)
- **Issues**: [GitHub Issues](https://github.com/lordraw77/open-automator/issues)

---

## 📞 Support

For questions and support:

- Open an issue on GitHub
- Check existing discussions
- Review documentation in `wiki`

---

**Built with ❤️ for the automation community**
