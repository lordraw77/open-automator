"""
Unit Tests per oa-system.py
Test operazioni di sistema (comandi locali/remoti, SSH, SCP)
"""
import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestOaSystem(unittest.TestCase):
    """Test per modulo oa-system"""

    def setUp(self):
        """Setup prima di ogni test"""
        # Import dinamico
        import importlib.util
        spec = importlib.util.spec_from_file_location("oa_system", "./modules/oa-system.py")
        self.oa_system = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.oa_system)

        self.oa_system.gdict = {'_wallet': None}
        self.mock_self = Mock()
        self.mock_self.gdict = self.oa_system.gdict

    @patch('subprocess.run')
    def test_runcmd_success(self, mock_run):
        """Test esecuzione comando locale con successo"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'Command output'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        param = {
            'command': 'echo "test"'
        }

        success, output = self.oa_system.runcmd(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['stdout'], 'Command output')
        self.assertEqual(output['return_code'], 0)

    @patch('subprocess.run')
    def test_runcmd_failure(self, mock_run):
        """Test comando con exit code non-zero"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Error occurred'
        mock_run.return_value = mock_result

        param = {
            'command': 'false'
        }

        success, output = self.oa_system.runcmd(self.mock_self, param)

        self.assertFalse(success)
        self.assertEqual(output['return_code'], 1)

    @patch('subprocess.run')
    def test_runcmd_timeout(self, mock_run):
        """Test comando con timeout"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('cmd', 5)

        param = {
            'command': 'sleep 100',
            'timeout': 5
        }

        success, output = self.oa_system.runcmd(self.mock_self, param)

        self.assertFalse(success)
        self.assertIn('timeout', output['error'].lower())

    @patch('subprocess.run')
    def test_runcmd_with_input_propagation(self, mock_run):
        """Test runcmd con input dal task precedente"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'output'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        param = {
            'input': {
                'command': 'ls -la'
            }
        }

        success, output = self.oa_system.runcmd(self.mock_self, param)

        self.assertTrue(success)

    @patch('oacommon.sshremotecommand')
    def test_systemd_start_service(self, mock_ssh):
        """Test avvio servizio systemd"""
        mock_ssh.return_value = b'Service started'

        param = {
            'remoteserver': 'server.local',
            'remoteuser': 'admin',
            'remotepassword': 'pass',
            'remoteport': '22',
            'servicename': 'nginx',
            'servicestate': 'start'
        }

        success, output = self.oa_system.systemd(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['service'], 'nginx')
        self.assertEqual(output['state'], 'start')
        mock_ssh.assert_called_once()

    @patch('oacommon.sshremotecommand')
    def test_systemd_restart_service(self, mock_ssh):
        """Test restart servizio"""
        mock_ssh.return_value = b'Service restarted'

        param = {
            'remoteserver': 'server.local',
            'remoteuser': 'admin',
            'remotepassword': 'pass',
            'remoteport': '22',
            'servicename': 'postgresql',
            'servicestate': 'restart'
        }

        success, output = self.oa_system.systemd(self.mock_self, param)

        self.assertTrue(success)
        self.assertIn('postgresql', str(mock_ssh.call_args))

    @patch('oacommon.sshremotecommand')
    def test_remotecommand_success(self, mock_ssh):
        """Test esecuzione comando remoto"""
        mock_ssh.return_value = b'Remote command output'

        param = {
            'remoteserver': 'remote.host',
            'remoteuser': 'user',
            'remotepassword': 'secret',
            'remoteport': '22',
            'command': 'uptime'
        }

        success, output = self.oa_system.remotecommand(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['output'], 'Remote command output')
        self.assertEqual(output['command'], 'uptime')

    def test_scp_upload(self):
        """Test upload file via SCP - mock a livello modulo"""
        # Mock SCPClient direttamente nel modulo caricato
        mock_scp_class = MagicMock()
        mock_scp_instance = MagicMock()
        mock_scp_class.return_value = mock_scp_instance

        # Sostituisci SCPClient nel modulo
        original_scp = self.oa_system.SCPClient
        self.oa_system.SCPClient = mock_scp_class

        try:
            with patch('oacommon.createSSHClient') as mock_ssh:
                mock_ssh_instance = MagicMock()
                mock_ssh.return_value = mock_ssh_instance

                param = {
                    'remoteserver': 'server.local',
                    'remoteuser': 'user',
                    'remotepassword': 'pass',
                    'remoteport': '22',
                    'localpath': '/tmp/file.txt',
                    'remotepath': '/remote/file.txt',
                    'recursive': False,
                    'direction': 'localtoremote'
                }

                success, output = self.oa_system.scp(self.mock_self, param)

                self.assertTrue(success)
                self.assertEqual(output['direction'], 'localtoremote')
                self.assertEqual(output['files_transferred'], 1)
        finally:
            # Ripristina
            self.oa_system.SCPClient = original_scp

    def test_scp_download(self):
        """Test download file via SCP"""
        mock_scp_class = MagicMock()
        mock_scp_instance = MagicMock()
        mock_scp_class.return_value = mock_scp_instance

        original_scp = self.oa_system.SCPClient
        self.oa_system.SCPClient = mock_scp_class

        try:
            with patch('oacommon.createSSHClient') as mock_ssh:
                mock_ssh_instance = MagicMock()
                mock_ssh.return_value = mock_ssh_instance

                param = {
                    'remoteserver': 'server.local',
                    'remoteuser': 'user',
                    'remotepassword': 'pass',
                    'remoteport': '22',
                    'localpath': '/tmp/download.txt',
                    'remotepath': '/remote/source.txt',
                    'recursive': False,
                    'direction': 'remotetolocal'
                }

                success, output = self.oa_system.scp(self.mock_self, param)

                self.assertTrue(success)
                self.assertEqual(output['direction'], 'remotetolocal')
        finally:
            self.oa_system.SCPClient = original_scp

    def test_scp_multipath(self):
        """Test SCP con percorsi multipli"""
        mock_scp_class = MagicMock()
        mock_scp_instance = MagicMock()
        mock_scp_class.return_value = mock_scp_instance

        original_scp = self.oa_system.SCPClient
        self.oa_system.SCPClient = mock_scp_class

        try:
            with patch('oacommon.createSSHClient') as mock_ssh:
                mock_ssh_instance = MagicMock()
                mock_ssh.return_value = mock_ssh_instance

                param = {
                    'remoteserver': 'server.local',
                    'remoteuser': 'user',
                    'remotepassword': 'pass',
                    'remoteport': '22',
                    'localpath': ['/tmp/file1.txt', '/tmp/file2.txt'],
                    'remotepath': ['/remote/file1.txt', '/remote/file2.txt'],
                    'recursive': False,
                    'direction': 'localtoremote'
                }

                success, output = self.oa_system.scp(self.mock_self, param)

                self.assertTrue(success)
                self.assertEqual(output['files_transferred'], 2)
                self.assertTrue(output['multipath'])
        finally:
            self.oa_system.SCPClient = original_scp

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_execute_script_python(self, mock_exists, mock_run):
        """Test esecuzione script Python"""
        mock_exists.return_value = True

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'Script output'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        param = {
            'script_path': '/tmp/test.py',
            'args': ['arg1', 'arg2']
        }

        success, output = self.oa_system.execute_script(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['interpreter'], 'python3')
        self.assertEqual(output['stdout'], 'Script output')

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_execute_script_bash(self, mock_exists, mock_run):
        """Test esecuzione script Bash"""
        mock_exists.return_value = True

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'Bash output'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        param = {
            'script_path': '/tmp/script.sh'
        }

        success, output = self.oa_system.execute_script(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['interpreter'], 'bash')

    def test_execute_script_not_found(self):
        """Test esecuzione script inesistente"""
        param = {
            'script_path': '/nonexistent/script.py'
        }

        success, output = self.oa_system.execute_script(self.mock_self, param)

        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
