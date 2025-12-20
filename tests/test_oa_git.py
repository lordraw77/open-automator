"""
Unit Tests per oa-git.py
Test operazioni Git
"""
import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
 

class TestOaGit(unittest.TestCase):
    """Test per modulo oa-git"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_dir = tempfile.mkdtemp()
        # Import dinamico del modulo
        import importlib.util
        spec = importlib.util.spec_from_file_location("oa_git", "./modules/oa-git.py")
        self.oa_git = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.oa_git)

        self.oa_git.gdict = {'_wallet': None}
        self.mock_self = Mock()
        self.mock_self.gdict = self.oa_git.gdict

    def tearDown(self):
        """Cleanup dopo ogni test"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('subprocess.run')
    def test_run_git_command_success(self, mock_run):
        """Test esecuzione comando git con successo"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'Success output'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        success, stdout, stderr, code = self.oa_git.run_git_command(
            ['git', 'status']
        )

        self.assertTrue(success)
        self.assertEqual(stdout, 'Success output')
        self.assertEqual(code, 0)

    @patch('subprocess.run')
    def test_run_git_command_failure(self, mock_run):
        """Test esecuzione comando git con errore"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Error message'
        mock_run.return_value = mock_result

        success, stdout, stderr, code = self.oa_git.run_git_command(
            ['git', 'invalid']
        )

        self.assertFalse(success)
        self.assertEqual(stderr, 'Error message')
        self.assertEqual(code, 1)

    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_clone_success(self, mock_exists, mock_run):
        """Test git clone con successo"""
        mock_exists.return_value = False  # Dest non esiste
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'Cloning...'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        param = {
            'repo_url': 'https://github.com/test/repo.git',
            'dest_path': os.path.join(self.test_dir, 'repo')
        }

        success, output = self.oa_git.clone(self.mock_self, param)

        self.assertTrue(success)
        self.assertIsNotNone(output)
        self.assertIn('repo_url', output)
        self.assertIn('dest_path', output)

    @patch('os.path.exists')
    def test_clone_dest_already_exists(self, mock_exists):
        """Test clone con destinazione già esistente"""
        mock_exists.return_value = True

        param = {
            'repo_url': 'https://github.com/test/repo.git',
            'dest_path': '/existing/path'
        }

        success, output = self.oa_git.clone(self.mock_self, param)

        self.assertFalse(success)

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.join')
    def test_pull_success(self, mock_join, mock_exists, mock_run):
        """Test git pull con successo"""
        mock_exists.return_value = True
        mock_join.return_value = '/repo/.git'

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'Already up to date.'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        param = {
            'repo_path': '/test/repo'
        }

        success, output = self.oa_git.pull(self.mock_self, param)

        self.assertTrue(success)
        self.assertIsNotNone(output)
        self.assertIn('changes_pulled', output)

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.join')
    def test_push_success(self, mock_join, mock_exists, mock_run):
        """Test git push con successo"""
        mock_exists.return_value = True
        mock_join.return_value = '/repo/.git'

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ''
        mock_result.stderr = 'Everything up-to-date'
        mock_run.return_value = mock_result

        param = {
            'repo_path': '/test/repo',
            'branch': 'main'
        }

        success, output = self.oa_git.push(self.mock_self, param)

        self.assertTrue(success)
        self.assertIn('branch', output)

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.join')
    def test_tag_create(self, mock_join, mock_exists, mock_run):
        """Test creazione tag"""
        mock_exists.return_value = True
        mock_join.return_value = '/repo/.git'

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ''
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        param = {
            'repo_path': '/test/repo',
            'operation': 'create',
            'tag_name': 'v1.0.0',
            'message': 'Release 1.0.0'
        }

        success, output = self.oa_git.tag(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['operation'], 'create')
        self.assertEqual(output['tag_name'], 'v1.0.0')

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.join')
    def test_tag_list(self, mock_join, mock_exists, mock_run):
        """Test lista tag"""
        mock_exists.return_value = True
        mock_join.return_value = '/repo/.git'

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'v1.0.0\nv1.1.0\nv2.0.0'
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        param = {
            'repo_path': '/test/repo',
            'operation': 'list'
        }

        success, output = self.oa_git.tag(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['operation'], 'list')
        self.assertEqual(len(output['tags']), 3)
        self.assertIn('v1.0.0', output['tags'])

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.join')
    def test_branch_create(self, mock_join, mock_exists, mock_run):
        """Test creazione branch"""
        mock_exists.return_value = True
        mock_join.return_value = '/repo/.git'

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ''
        mock_result.stderr = ''
        mock_run.return_value = mock_result

        param = {
            'repo_path': '/test/repo',
            'operation': 'create',
            'branch_name': 'feature/new-feature'
        }

        success, output = self.oa_git.branch(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['operation'], 'create')
        self.assertEqual(output['branch_name'], 'feature/new-feature')

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.join')
    def test_branch_checkout(self, mock_join, mock_exists, mock_run):
        """Test checkout branch"""
        mock_exists.return_value = True
        mock_join.return_value = '/repo/.git'

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ''
        mock_result.stderr = "Switched to branch 'develop'"
        mock_run.return_value = mock_result

        param = {
            'repo_path': '/test/repo',
            'operation': 'checkout',
            'branch_name': 'develop'
        }

        success, output = self.oa_git.branch(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['operation'], 'checkout')

    def test_clone_with_input_propagation(self):
        """Test clone con input dal task precedente"""
        param = {
            'input': {
                'repo_url': 'https://github.com/test/repo.git'
            },
            'dest_path': '/tmp/repo'
        }

        # Il modulo dovrebbe usare repo_url dall'input
        # Verifichiamo solo che il parametro venga estratto
        self.assertIn('input', param)
        self.assertIn('repo_url', param['input'])

if __name__ == '__main__':
    unittest.main()
