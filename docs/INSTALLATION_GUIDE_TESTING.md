# 📦 GUIDA INSTALLAZIONE UNIT TEST - Open-Automator

## Struttura Directory Finale

Dopo aver scaricato e installato tutti i file, la struttura del progetto sarà:

```
open-automator/
│
├── automator.py                     # Main script (refactored)
├── oacommon.py                      # Common utilities (refactored)
├── logger_config.py                 # Logging system ⭐
├── oa-system.py                     # System module (refactored)
├── oa-network.py                    # Network module (refactored)
├── oa-io.py                         # I/O module (refactored)
├── oa-utility.py                    # Utility module (refactored)
│
├── requirements.txt                 # Project dependencies
├── requirements-test.txt            # Testing dependencies ⭐
│
├── Makefile                         # Quick commands ⭐
├── pytest.ini                       # Pytest configuration ⭐
├── conftest.py                      # Pytest fixtures ⭐
│
├── setup_testing.sh                 # Setup automation script ⭐
├── run_tests.py                     # Test runner CLI ⭐
│
├── tests/                           # Test directory ⭐
│   ├── __init__.py
│   ├── test_logger_config.py       # Logger tests (13 tests)
│   ├── test_oacommon.py            # Common utils tests (19 tests)
│   ├── test_oa_network.py          # Network tests (template)
│   ├── test_oa_io.py               # I/O tests (13 tests)
│   ├── test_oa_utility.py          # Utility tests (9 tests)
│   └── test_config.py              # Test runner
│
├── logs/                            # Production logs
├── logs_test/                       # Test logs ⭐
├── htmlcov/                         # Coverage reports (generated) ⭐
│
├── docs/                            # Documentation
│   ├── README_LOGGING.md
│   ├── README_TESTING.md           ⭐
│   ├── TESTING_SUMMARY.md          ⭐
│   └── TESTING_QUICK_REFERENCE.md  ⭐
│
└── backup_YYYYMMDD_HHMMSS/         # Backup files (if using install script)

⭐ = File/directory nuovi per testing
```

## 🚀 Installazione Step-by-Step

### Step 1: Organizza i File Scaricati

Hai scaricato 16 file. Organizzali così:

```bash
# Test files → tests/
mv test_*.py tests/
mv tests_init.py tests/__init__.py

# Configuration files → root
mv conftest.py .
mv pytest.ini .
mv requirements-test.txt .
mv Makefile .

# Scripts → root
mv setup_testing.sh .
mv run_tests.py .
chmod +x setup_testing.sh run_tests.py

# Documentation → docs/ (opzionale)
mkdir -p docs
mv README_TESTING.md docs/
mv TESTING_SUMMARY.md docs/
mv TESTING_QUICK_REFERENCE.md docs/
```

### Step 2: Verifica Struttura

```bash
# Verifica che i file siano al posto giusto
ls -la tests/
ls -la *.ini
ls -la Makefile
ls -la setup_testing.sh
```

Output atteso:
```
tests/test_logger_config.py
tests/test_oacommon.py
tests/test_oa_network.py
tests/test_oa_io.py
tests/test_oa_utility.py
tests/__init__.py
pytest.ini
Makefile
setup_testing.sh
run_tests.py
```

### Step 3: Esegui Setup Automatico

```bash
# Rendi eseguibile lo script
chmod +x setup_testing.sh

# Esegui setup
./setup_testing.sh
```

Lo script:
1. ✓ Verifica Python 3 e pip
2. ✓ Opzionalmente crea virtual environment
3. ✓ Installa dipendenze progetto
4. ✓ Installa dipendenze testing
5. ✓ Crea directory necessarie
6. ✓ Verifica installazione pytest
7. ✓ Esegue test di prova

### Step 4: Verifica Installazione

```bash
# Test che pytest funzioni
python3 -m pytest --version

# Lista test disponibili
pytest --collect-only tests/

# Esegui un test semplice
pytest tests/test_oa_utility.py -v
```

Output atteso:
```
============================= test session starts ==============================
collected 9 items

tests/test_oa_utility.py::TestSetSleep::test_sleep_duration PASSED       [ 11%]
tests/test_oa_utility.py::TestPrintVar::test_print_simple_variable PASSED [ 22%]
...
============================== 9 passed in 0.15s ===============================
```

### Step 5: Esegui Test Completi

```bash
# Con make
make test

# Con pytest diretto
pytest tests/ -v

# Con test runner
./run_tests.py
```

### Step 6: Genera Coverage

```bash
# Con make
make coverage

# Con pytest diretto
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Apri report
open htmlcov/index.html        # macOS
xdg-open htmlcov/index.html    # Linux
start htmlcov/index.html       # Windows
```

## 🔧 Installazione Manuale (Alternativa)

Se preferisci non usare lo script automatico:

### 1. Crea Virtual Environment (Raccomandato)

```bash
python3 -m venv venv

# Attiva
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate          # Windows
```

### 2. Installa Dipendenze

```bash
# Dipendenze progetto
pip install -r requirements.txt

# Dipendenze testing
pip install -r requirements-test.txt
```

### 3. Crea Directory

```bash
mkdir -p tests logs logs_test
```

### 4. Copia File di Test

```bash
# Se hai i file separati
cp test_*.py tests/
echo "" > tests/__init__.py
```

### 5. Verifica

```bash
pytest tests/ -v
```

## 🐛 Troubleshooting

### Problema: ModuleNotFoundError per logger_config

**Causa**: Python non trova il modulo

**Soluzione**:
```bash
# Verifica che logger_config.py sia nella root
ls -la logger_config.py

# Aggiungi PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Oppure installa il progetto in development mode
pip install -e .
```

### Problema: pytest non trovato

**Causa**: pytest non installato

**Soluzione**:
```bash
pip install pytest pytest-cov pytest-mock
```

### Problema: Import errors tra moduli

**Causa**: Struttura import non corretta

**Soluzione**:
```bash
# Verifica che __init__.py esista in tests/
touch tests/__init__.py

# Esegui da root directory
cd /path/to/open-automator
pytest tests/
```

### Problema: Permission denied su script

**Causa**: Script non eseguibili

**Soluzione**:
```bash
chmod +x setup_testing.sh
chmod +x run_tests.py
```

### Problema: Test falliscono per dipendenze mancanti

**Causa**: Moduli refactored non presenti

**Soluzione**:
```bash
# Verifica che tutti i moduli refactored siano installati
ls -la oa*.py
ls -la automator.py
ls -la oacommon.py
ls -la logger_config.py

# Se mancano, copia i file _refactored.py e rinomina
cp automator_refactored.py automator.py
cp oacommon_refactored.py oacommon.py
# etc.
```

## ✅ Checklist Post-Installazione

Verifica che tutto sia configurato correttamente:

- [ ] Python 3.7+ installato
- [ ] pip installato e aggiornato
- [ ] Virtual environment creato (opzionale ma consigliato)
- [ ] requirements.txt installato
- [ ] requirements-test.txt installato
- [ ] Directory tests/ esiste
- [ ] File test_*.py in tests/
- [ ] tests/__init__.py esiste
- [ ] conftest.py nella root
- [ ] pytest.ini nella root
- [ ] Makefile nella root
- [ ] `pytest --version` funziona
- [ ] `pytest --collect-only tests/` mostra i test
- [ ] `make test` esegue i test
- [ ] `make coverage` genera il report

## 📊 Verifica Finale

Esegui questi comandi per verificare l'installazione:

```bash
# 1. Info Python
python3 --version
pip3 --version

# 2. Pytest installato
pytest --version

# 3. Lista test
pytest --collect-only tests/ -q

# 4. Esegui test rapido
pytest tests/test_oa_utility.py -v

# 5. Verifica coverage
pytest tests/ --cov=. --cov-report=term-missing

# 6. Test con make
make test
```

Se tutti i comandi funzionano correttamente, l'installazione è completa! ✅

## 🎯 Prossimi Passi

1. **Esplora i Test**
   ```bash
   cat tests/test_logger_config.py
   ```

2. **Leggi Documentazione**
   ```bash
   cat docs/README_TESTING.md
   cat docs/TESTING_QUICK_REFERENCE.md
   ```

3. **Esegui Test Specifici**
   ```bash
   pytest tests/test_logger_config.py::TestAutomatorLogger -v
   ```

4. **Genera Coverage Dettagliato**
   ```bash
   make coverage
   open htmlcov/index.html
   ```

5. **Scrivi Nuovi Test**
   - Copia template da test esistenti
   - Aggiungi in tests/
   - Esegui con pytest

## 📞 Supporto

- **Quick Reference**: `cat docs/TESTING_QUICK_REFERENCE.md`
- **Full Docs**: `cat docs/README_TESTING.md`
- **Summary**: `cat docs/TESTING_SUMMARY.md`
- **Help Command**: `./run_tests.py --help`
- **Pytest Help**: `pytest --help`

---

**Nota Importante**: Assicurati di aver prima installato il sistema di logging refactored.
I test dipendono da `logger_config.py` e dai moduli refactored.

**Versione**: 1.0.0
**Data**: Dicembre 2025
