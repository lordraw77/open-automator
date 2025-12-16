"""
Pytest configuration and fixtures per Open-Automator
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Crea una directory temporanea per i test"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture
def test_file(temp_dir):
    """Crea un file di test temporaneo"""
    file_path = os.path.join(temp_dir, 'test.txt')
    with open(file_path, 'w') as f:
        f.write('test content')
    return file_path


@pytest.fixture
def test_yaml_file(temp_dir):
    """Crea un file YAML di test"""
    yaml_content = """
name: test_workflow
tasks:
  - name: test task
    oa-utility.setvar:
      varname: test_var
      varvalue: test_value
"""
    file_path = os.path.join(temp_dir, 'test.yaml')
    with open(file_path, 'w') as f:
        f.write(yaml_content)
    return file_path


@pytest.fixture
def mock_gdict():
    """Fornisce un gdict mock per i test"""
    return {
        'DEBUG': False,
        'DEBUG2': False,
        'TRACE': False
    }


@pytest.fixture(autouse=True)
def setup_logging(temp_dir):
    """Setup automatico del logging per ogni test"""
    from logger_config import AutomatorLogger

    log_dir = os.path.join(temp_dir, 'logs_test')
    AutomatorLogger.setup_logging(
        log_dir=log_dir,
        console_level='ERROR',  # Silenzioso durante i test
        file_level='DEBUG'
    )

    yield

    # Cleanup logging handlers
    import logging
    root_logger = logging.getLogger()
    root_logger.handlers.clear()


@pytest.fixture
def mock_ssh_client():
    """Mock per SSH client"""
    from unittest.mock import MagicMock

    mock_client = MagicMock()
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b'command output'
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b''

    mock_client.exec_command.return_value = (
        MagicMock(),  # stdin
        mock_stdout,
        mock_stderr
    )

    return mock_client


@pytest.fixture
def mock_http_response():
    """Mock per HTTP response"""
    from unittest.mock import MagicMock

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.reason = 'OK'
    mock_response.content = b'{"result": "success"}'
    mock_response.text = '{"result": "success"}'

    return mock_response
