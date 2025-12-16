"""
Unit Tests per oacommon.py
Test delle funzioni utility comuni
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import paramiko

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import del modulo REALE (non mockato)
import oacommon


class TestEffify(unittest.TestCase):
    """Test per la funzione effify (interpolazione variabili)"""

    def setUp(self):
        """Setup prima di ogni test"""
        # Salva lo stato originale di gdict
        self.original_gdict = oacommon.gdict.copy() if hasattr(oacommon, 'gdict') and oacommon.gdict else {}
        oacommon.gdict = {}

    def tearDown(self):
        """Ripristina stato originale"""
        oacommon.gdict = self.original_gdict

    def test_effify_simple_variable(self):
        """Test interpolazione variabile semplice"""
        oacommon.gdict = {'name': 'test'}
        result = oacommon.effify('{name}')
        self.assertEqual(result, 'test')

    def test_effify_multiple_variables(self):
        """Test interpolazione multiple variabili"""
        oacommon.gdict = {'host': '127.0.0.1', 'port': '8080'}
        result = oacommon.effify('{host}:{port}')
        print (result, '127.0.0.1:8080')
        self.assertEqual(result, '127.0.0.1:8080')

    def test_effify_no_variables(self):
        """Test stringa senza variabili"""
        result = oacommon.effify('plain text')
        self.assertEqual(result, 'plain text')

    def test_effify_with_error_returns_original(self):
        """Test che errori restituiscano la stringa originale"""
        oacommon.gdict = {}
        result = oacommon.effify('{undefined_var}')
        # Se la variabile non esiste, dovrebbe restituire la stringa originale
        # o sollevare un'eccezione - dipende dall'implementazione
        self.assertIsInstance(result, str)


class TestCheckAndLoadParam(unittest.TestCase):
    """Test per checkandloadparam"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.mock_self = Mock()
        self.mock_self.gdict = {}

    def test_all_params_present(self):
        """Test con tutti i parametri presenti"""
        param = {'host': '127.0.0.1', 'port': 8080, 'path': '/'}

        result = oacommon.checkandloadparam(
            self.mock_self,
            lambda: 'test_func',
            'host', 'port', 'path',
            param=param
        )

        self.assertTrue(result)
        self.assertEqual(self.mock_self.gdict['host'], '127.0.0.1')
        self.assertEqual(self.mock_self.gdict['port'], 8080)
        self.assertEqual(self.mock_self.gdict['path'], '/')

    def test_missing_params(self):
        """Test con parametri mancanti"""
        param = {'host': '127.0.0.1'}

        result = oacommon.checkandloadparam(
            self.mock_self,
            lambda: 'test_func',
            'host', 'port', 'path',
            param=param
        )

        self.assertFalse(result)
        self.assertEqual(self.mock_self.gdict['host'], '127.0.0.1')
        self.assertNotIn('port', self.mock_self.gdict)

    def test_empty_params(self):
        """Test con parametri vuoti"""
        param = {}

        result = oacommon.checkandloadparam(
            self.mock_self,
            lambda: 'test_func',
            'host',
            param=param
        )

        self.assertFalse(result)


class TestCheckParam(unittest.TestCase):
    """Test per checkparam"""

    def test_param_exists(self):
        """Test parametro presente"""
        param = {'optional_field': 'value'}
        result = oacommon.checkparam('optional_field', param)
        self.assertTrue(result)

    def test_param_not_exists(self):
        """Test parametro assente"""
        param = {}
        result = oacommon.checkparam('optional_field', param)
        self.assertFalse(result)


class TestCreateSSHClient(unittest.TestCase):
    """Test per createSSHClient"""

    @patch('paramiko.SSHClient')
    def test_create_ssh_client_success(self, mock_ssh_class):
        """Test creazione client SSH con successo"""
        mock_client = MagicMock()
        mock_ssh_class.return_value = mock_client

        result = oacommon.createSSHClient('localhost', 22, 'user', 'pass')

        self.assertEqual(result, mock_client)
        mock_client.load_system_host_keys.assert_called_once()
        mock_client.set_missing_host_key_policy.assert_called_once()
        mock_client.connect.assert_called_once_with('localhost', 22, 'user', 'pass', timeout=30)

    @patch('paramiko.SSHClient')
    def test_create_ssh_client_auth_failure(self, mock_ssh_class):
        """Test fallimento autenticazione SSH"""
        mock_client = MagicMock()
        mock_client.connect.side_effect = paramiko.AuthenticationException('Auth failed')
        mock_ssh_class.return_value = mock_client

        with self.assertRaises(paramiko.AuthenticationException):
            oacommon.createSSHClient('localhost', 22, 'user', 'wrong_pass')


class TestSSHRemoteCommand(unittest.TestCase):
    """Test per sshremotecommand"""

    @patch('oacommon.createSSHClient')
    def test_ssh_remote_command_success(self, mock_create_ssh):
        """Test esecuzione comando remoto con successo"""
        # Setup mock SSH client
        mock_ssh = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'command output'
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b''

        mock_ssh.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)
        mock_create_ssh.return_value = mock_ssh

        result = oacommon.sshremotecommand('localhost', 22, 'user', 'pass', 'ls -la')

        self.assertEqual(result, b'command output')
        mock_ssh.exec_command.assert_called_once_with('ls -la')
        mock_ssh.close.assert_called_once()

    @patch('oacommon.createSSHClient')
    def test_ssh_remote_command_with_stderr(self, mock_create_ssh):
        """Test comando con stderr"""
        mock_ssh = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'output'
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b'warning message'

        mock_ssh.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)
        mock_create_ssh.return_value = mock_ssh

        result = oacommon.sshremotecommand('localhost', 22, 'user', 'pass', 'command')

        self.assertEqual(result, b'output')


class TestFileOperations(unittest.TestCase):
    """Test per operazioni su file"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'test.txt')

    def tearDown(self):
        """Cleanup dopo ogni test"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_writefile_creates_file(self):
        """Test che writefile crei il file"""
        content = 'Test content'
        oacommon.writefile(self.test_file, content)

        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), content)

    def test_readfile_reads_content(self):
        """Test che readfile legga il contenuto"""
        content = 'Test content for reading'
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(content)

        result = oacommon.readfile(self.test_file)
        self.assertEqual(result, content)

    def test_appendfile_appends_content(self):
        """Test che appendfile appenda al file"""
        initial_content = 'Initial content\n'
        append_content = 'Appended content'

        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(initial_content)

        oacommon.appendfile(self.test_file, append_content)

        with open(self.test_file, 'r', encoding='utf-8') as f:
            result = f.read()

        self.assertEqual(result, initial_content + append_content)

    @patch('chardet.detect')
    def test_findenc_detects_encoding(self, mock_detect):
        """Test rilevamento encoding"""
        mock_detect.return_value = {'encoding': 'utf-8', 'confidence': 0.99}

        with open(self.test_file, 'wb') as f:
            f.write(b'test content')

        result = oacommon.findenc(self.test_file)

        self.assertEqual(result, 'utf-8')
        mock_detect.assert_called_once()


class TestTraceDecorator(unittest.TestCase):
    """Test per il decorator @trace"""

    def setUp(self):
        """Setup prima di ogni test"""
        # Salva stato originale
        self.original_gdict = oacommon.gdict.copy() if hasattr(oacommon, 'gdict') and oacommon.gdict else {}
        oacommon.gdict = {'TRACE': True}

    def tearDown(self):
        """Ripristina stato"""
        oacommon.gdict = self.original_gdict

    def test_trace_decorator_executes_function(self):
        """Test che il decorator esegua la funzione"""
        @oacommon.trace
        def test_func(x, y):
            return x + y

        result = test_func(2, 3)
        self.assertEqual(result, 5)

    def test_trace_decorator_with_trace_disabled(self):
        """Test decorator con TRACE disabilitato"""
        oacommon.gdict = {'TRACE': False}

        @oacommon.trace
        def test_func(x):
            return x * 2

        result = test_func(5)
        self.assertEqual(result, 10)


if __name__ == '__main__':
    unittest.main()
