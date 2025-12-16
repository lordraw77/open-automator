# 🚀 QUICK REFERENCE - Testing Open-Automator

## Setup (Prima volta)

```bash
chmod +x setup_testing.sh
./setup_testing.sh
```

## Comandi Quotidiani

```bash
# Test tutti
make test

# Coverage
make coverage

# Test specifico
pytest tests/test_logger_config.py -v

# Fail fast
pytest tests/ -x
```

## Test Runner CLI

```bash
# Con coverage
./run_tests.py -c

# Verbose
./run_tests.py -v

# Test specifico
./run_tests.py -t test_logger_config.py

# Solo unit
./run_tests.py -m unit

# Parallelo
./run_tests.py -p
```

## Pytest Markers

```bash
-m unit          # Unit test
-m integration   # Integration
-m "not slow"    # Esclude lenti
-m network       # Solo network
```

## Coverage Commands

```bash
# HTML
pytest --cov=. --cov-report=html

# Terminal
pytest --cov=. --cov-report=term

# XML (CI)
pytest --cov=. --cov-report=xml
```

## Debug

```bash
# Con print
pytest tests/ -s

# Con pdb
pytest tests/ --pdb

# Verbose + output
pytest tests/ -vv -s

# Local vars on fail
pytest tests/ -l
```

## Files Overview

```
tests/
├── test_logger_config.py  # Logging (13 test)
├── test_oacommon.py       # Common utils (19 test)
├── test_oa_network.py     # Network (template)
├── test_oa_io.py          # I/O (13 test)
├── test_oa_utility.py     # Utility (9 test)
└── conftest.py            # Fixtures

pytest.ini              # Config
Makefile               # Commands
requirements-test.txt  # Dependencies
README_TESTING.md      # Full docs
```

## Fixtures Disponibili

```python
temp_dir           # Temporary directory
test_file          # Test file
test_yaml_file     # YAML file
mock_gdict         # Global dict
mock_ssh_client    # SSH mock
mock_http_response # HTTP mock
```

## Makefile Targets

```bash
make install      # Install deps
make test         # Run tests
make test-unit    # Unit only
make coverage     # Coverage report
make lint         # Lint code
make clean        # Clean temp files
```

## Common Issues

**Import Error**
→ `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

**Fixture Not Found**
→ Check conftest.py location

**Coverage Low**
→ `pytest --cov=. --cov-report=term-missing`

**Slow Tests**
→ `pytest --durations=10`

## Next Steps

1. ✅ Setup done
2. Run: `make test`
3. Check: `make coverage`
4. Read: `README_TESTING.md`
5. Write: more tests!

---

**Quick Help**: `./run_tests.py --help` or `pytest --help`
