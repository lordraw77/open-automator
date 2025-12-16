# Open-Automator - Testing Suite

Suite completa di unit test per Open-Automator con coverage reporting e CI/CD integration.

## 📁 Struttura Testing

```
open-automator/
├── tests/
│   ├── __init__.py
│   ├── test_logger_config.py    # Test sistema logging
│   ├── test_oacommon.py         # Test utility comuni
│   ├── test_oa_network.py       # Test modulo network
│   ├── test_oa_io.py            # Test modulo I/O
│   ├── test_oa_utility.py       # Test modulo utility
│   ├── test_oa_system.py        # Test modulo system
│   └── conftest.py              # Pytest fixtures
├── pytest.ini                   # Configurazione pytest
├── Makefile                     # Comandi rapidi
├── requirements-test.txt        # Dipendenze testing
└── README_TESTING.md           # Questa guida
```

## ⚡ Quick Start

### 1. Installazione Dipendenze

```bash
# Installa dipendenze di testing
pip install -r requirements-test.txt

# Oppure con make
make install
```

### 2. Esecuzione Test

```bash
# Tutti i test
make test

# Solo unit test (esclude integration)
make test-unit

# Con output verbose
make test-verbose

# Test specifico
python -m pytest tests/test_logger_config.py -v
```

### 3. Coverage Report

```bash
# Genera report coverage
make coverage

# Apri report HTML
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 🧪 Comandi Disponibili

### Make Commands

```bash
make help         # Mostra tutti i comandi
make install      # Installa dipendenze
make test         # Esegue tutti i test
make test-unit    # Solo unit test
make coverage     # Genera coverage report
make lint         # Linting del codice
make clean        # Pulisce file temporanei
```

### Pytest Commands

```bash
# Test base
pytest tests/

# Con verbose output
pytest tests/ -v

# Con extra verbose (mostra print)
pytest tests/ -vv -s

# Test specifico file
pytest tests/test_logger_config.py

# Test specifico classe
pytest tests/test_logger_config.py::TestAutomatorLogger

# Test specifico metodo
pytest tests/test_logger_config.py::TestAutomatorLogger::test_setup_logging_creates_directory

# Test con marker specifico
pytest tests/ -m unit
pytest tests/ -m "not slow"

# Fail fast (ferma al primo errore)
pytest tests/ -x

# Mostra i 10 test più lenti
pytest tests/ --durations=10
```

## 📊 Coverage

### Generazione Report

```bash
# HTML report (consigliato)
pytest tests/ --cov=. --cov-report=html

# Terminal report
pytest tests/ --cov=. --cov-report=term

# XML report (per CI/CD)
pytest tests/ --cov=. --cov-report=xml

# Tutti i formati
pytest tests/ --cov=. --cov-report=html --cov-report=term --cov-report=xml
```

### Target Coverage

| Componente | Target Coverage | Attuale |
|------------|----------------|---------|
| logger_config.py | 90% | TBD |
| oacommon.py | 85% | TBD |
| oa-network.py | 80% | TBD |
| oa-io.py | 85% | TBD |
| oa-system.py | 75% | TBD |
| oa-utility.py | 90% | TBD |
| **Overall** | **80%** | **TBD** |

## 🏷️ Test Markers

I test sono marcati per esecuzione selettiva:

```python
@pytest.mark.unit          # Unit test puro
@pytest.mark.integration   # Test di integrazione
@pytest.mark.slow          # Test lento
@pytest.mark.network       # Richiede connessione rete
@pytest.mark.ssh           # Richiede SSH
```

### Esecuzione per Marker

```bash
# Solo unit test
pytest -m unit

# Esclude test lenti
pytest -m "not slow"

# Solo test di rete
pytest -m network

# Test unit e non lenti
pytest -m "unit and not slow"
```

## 🔧 Fixtures Disponibili

### File Fixtures (conftest.py)

```python
def test_with_temp_dir(temp_dir):
    """temp_dir fornisce directory temporanea"""
    assert os.path.exists(temp_dir)

def test_with_test_file(test_file):
    """test_file fornisce file di test già creato"""
    with open(test_file, 'r') as f:
        content = f.read()
    assert content == 'test content'

def test_with_yaml(test_yaml_file):
    """test_yaml_file fornisce YAML di test"""
    assert os.path.exists(test_yaml_file)
```

### Mock Fixtures

```python
def test_with_gdict(mock_gdict):
    """mock_gdict fornisce dizionario globale"""
    assert 'DEBUG' in mock_gdict

def test_with_ssh(mock_ssh_client):
    """mock_ssh_client fornisce client SSH mockato"""
    stdout, stderr = mock_ssh_client.exec_command('ls')

def test_with_http(mock_http_response):
    """mock_http_response fornisce response HTTP"""
    assert mock_http_response.status_code == 200
```

## 📝 Scrivere Nuovi Test

### Template Test Base

```python
"""
Unit Tests per nuovo_modulo.py
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import nuovo_modulo


class TestNuovaFunzione(unittest.TestCase):
    """Test per nuova_funzione"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_data = {'key': 'value'}

    def tearDown(self):
        """Cleanup dopo ogni test"""
        pass

    def test_funzione_con_successo(self):
        """Test caso di successo"""
        result = nuovo_modulo.nuova_funzione(self.test_data)
        self.assertEqual(result, 'expected')

    def test_funzione_con_errore(self):
        """Test caso di errore"""
        with self.assertRaises(ValueError):
            nuovo_modulo.nuova_funzione(None)


if __name__ == '__main__':
    unittest.main()
```

### Best Practices

1. **Naming Convention**
   - File: `test_<module>.py`
   - Classe: `Test<Feature>`
   - Metodo: `test_<what_it_tests>`

2. **Struttura Test**
   - Arrange: Setup dati di test
   - Act: Esegui funzione da testare
   - Assert: Verifica risultato

3. **Isolamento**
   - Ogni test deve essere indipendente
   - Usa setUp/tearDown per stato pulito
   - Mock dipendenze esterne

4. **Coverage**
   - Test casi positivi
   - Test casi negativi
   - Test edge cases
   - Test error handling

## 🔄 Integrazione CI/CD

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run tests
      run: pytest tests/ --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### GitLab CI

```yaml
test:
  stage: test
  image: python:3.9
  script:
    - pip install -r requirements.txt
    - pip install -r requirements-test.txt
    - pytest tests/ --cov=. --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## 🐛 Debugging Test

### Run singolo test con debugger

```bash
# Con pdb
pytest tests/test_logger_config.py::TestAutomatorLogger::test_setup -s --pdb

# Con ipdb
pytest tests/test_logger_config.py::TestAutomatorLogger::test_setup -s --pdb --pdbcls=IPython.terminal.debugger:Pdb
```

### Output dettagliato

```bash
# Mostra print statements
pytest tests/ -s

# Mostra log
pytest tests/ --log-cli-level=DEBUG

# Mostra variabili locali su failure
pytest tests/ -l
```

## 📈 Metriche Test

### Velocità

```bash
# Profiling test
pytest tests/ --durations=0

# Parallel execution (richiede pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto
```

### Report

```bash
# JUnit XML (per CI)
pytest tests/ --junitxml=report.xml

# HTML report (richiede pytest-html)
pip install pytest-html
pytest tests/ --html=report.html
```

## 🔍 Troubleshooting

### Problema: ModuleNotFoundError

**Soluzione**: Aggiungi path del progetto
```python
import sys
sys.path.insert(0, os.path.abspath('..'))
```

### Problema: Fixture non trovata

**Soluzione**: Verifica che conftest.py sia nella directory giusta

### Problema: Import errors tra moduli

**Soluzione**: Crea `__init__.py` in directory tests/

### Problema: Coverage incompleto

**Soluzione**: Specifica source directory
```bash
pytest --cov=. --cov-config=.coveragerc
```

## 📚 Risorse

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

## 🤝 Contribuire

1. Ogni nuova feature richiede test
2. Mantieni coverage > 80%
3. Tutti i test devono passare prima del merge
4. Documenta test complessi

---

**Maintainer**: Open-Automator Team
**Last Updated**: Dicembre 2025
