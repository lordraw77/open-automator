#!/bin/bash
# Script di setup per testing Open-Automator

set -e  # Exit on error

echo "======================================"
echo "Open-Automator Testing Setup"
echo "======================================"
echo ""

# Colori per output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verifica Python
echo "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "${RED}❌ Python 3 non trovato. Installare Python 3.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
echo "${GREEN}✓ Python $PYTHON_VERSION trovato${NC}"
echo ""

# Verifica pip
echo "Verificando pip..."
if ! command -v pip3 &> /dev/null; then
    echo "${RED}❌ pip3 non trovato.${NC}"
    exit 1
fi
echo "${GREEN}✓ pip3 trovato${NC}"
echo ""

# Crea virtual environment (opzionale ma consigliato)
read -p "Creare virtual environment? (consigliato) [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creando virtual environment..."
    python3 -m venv venv

    # Attiva venv
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi

    echo "${GREEN}✓ Virtual environment creato e attivato${NC}"
    echo ""
fi

# Installa dipendenze progetto
echo "Installando dipendenze progetto..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    echo "${GREEN}✓ Dipendenze progetto installate${NC}"
else
    echo "${YELLOW}⚠ requirements.txt non trovato${NC}"
fi
echo ""

# Installa dipendenze testing
echo "Installando dipendenze testing..."
if [ -f "requirements-test.txt" ]; then
    pip3 install -r requirements-test.txt
    echo "${GREEN}✓ Dipendenze testing installate${NC}"
else
    echo "${RED}❌ requirements-test.txt non trovato${NC}"
    exit 1
fi
echo ""

# Crea directory tests se non esiste
if [ ! -d "tests" ]; then
    echo "Creando directory tests..."
    mkdir -p tests
    touch tests/__init__.py
    echo "${GREEN}✓ Directory tests creata${NC}"
else
    echo "${GREEN}✓ Directory tests già esistente${NC}"
fi
echo ""

# Crea directory logs_test
if [ ! -d "logs_test" ]; then
    mkdir -p logs_test
    echo "${GREEN}✓ Directory logs_test creata${NC}"
fi
echo ""

# Verifica installazione pytest
echo "Verificando installazione pytest..."
if python3 -c "import pytest" 2>/dev/null; then
    PYTEST_VERSION=$(python3 -c "import pytest; print(pytest.__version__)")
    echo "${GREEN}✓ pytest $PYTEST_VERSION installato${NC}"
else
    echo "${RED}❌ pytest non installato correttamente${NC}"
    exit 1
fi
echo ""

# Esegui test di prova
echo "Eseguendo test di prova..."
if [ -d "tests" ] && [ "$(ls -A tests/test_*.py 2>/dev/null)" ]; then
    python3 -m pytest tests/ --collect-only -q
    echo ""

    read -p "Eseguire tutti i test ora? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        python3 -m pytest tests/ -v
    fi
else
    echo "${YELLOW}⚠ Nessun file di test trovato in tests/${NC}"
fi
echo ""

# Summary
echo "======================================"
echo "${GREEN}✓ Setup completato con successo!${NC}"
echo "======================================"
echo ""
echo "Comandi disponibili:"
echo "  make test         - Esegue tutti i test"
echo "  make coverage     - Genera coverage report"
echo "  make test-verbose - Test con output dettagliato"
echo "  pytest tests/     - Esegue test con pytest"
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "NOTA: Virtual environment attivo."
    echo "Per attivarlo in futuro:"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "  source venv/Scripts/activate  # Windows"
    else
        echo "  source venv/bin/activate      # Linux/macOS"
    fi
    echo ""
fi

echo "Per iniziare:"
echo "  cd tests/"
echo "  pytest -v"
echo ""
