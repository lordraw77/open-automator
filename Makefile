# Makefile per Open-Automator Testing

.PHONY: test coverage lint clean install help

# Variabili
PYTHON := python3.12
PIP := pip3.12
TEST_DIR := tests
SRC_DIR := .
export PYTHONPATH := $(shell pwd)

help:
	@echo "Comandi disponibili:"
	@echo "  make install      - Installa dipendenze"
	@echo "  make test         - Esegue tutti i test"
	@echo "  make test-unit    - Esegue solo unit test"
	@echo "  make coverage     - Genera report coverage"
	@echo "  make lint         - Esegue linting del codice"
	@echo "  make clean        - Pulisce file temporanei"
	@echo "  make build-shell      - Build Docker image per Shell"
	@echo "  make build-fastapi    - Build Docker image per FastAPI"
	@echo "  make build-streamlit  - Build Docker image per Streamlit"
	@echo "  make build-all        - Build tutte le Docker image"

build-shell:
	bash buildShell.sh
build-fastapi:
	bash buildFastapi.sh
build-streamlit:
	bash buildStreamlit.sh
b7uild-wellet:
	bash buildWellet.sh
build-all: build-shell build-fastapi build-streamlit build-wellet

install:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-test.txt

test:
	PYTHONPATH=.:$(PYTHONPATH) $(PYTHON) -m pytest $(TEST_DIR) -v

test-unit:
	PYTHONPATH=.:$(PYTHONPATH) $(PYTHON) -m pytest $(TEST_DIR) -v -k "not integration"

test-verbose:
	PYTHONPATH=.:$(PYTHONPATH) $(PYTHON) -m pytest $(TEST_DIR) -vv -s

coverage:
	PYTHONPATH=.:$(PYTHONPATH) $(PYTHON) -m pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	python3 -m http.server 8080

coverage-xml:
	PYTHONPATH=.:$(PYTHONPATH) $(PYTHON) -m pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=xml

lint:
	$(PYTHON) -m pylint $(SRC_DIR)/*.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf logs_test