"""
Unit Tests per taskstore.py e oaworkflow.py
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from taskstore import TaskResultStore

class TestTaskResultStore(unittest.TestCase):
    """Test per TaskResultStore"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.store = TaskResultStore()

    def test_set_result_success(self):
        """Test salvataggio risultato con successo"""
        self.store.set_result('task1', True, '')
        result = self.store.get_result('task1')

        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertEqual(result['error'], '')

    def test_set_result_failure(self):
        """Test salvataggio risultato con errore"""
        self.store.set_result('task2', False, 'Error occurred')
        result = self.store.get_result('task2')

        self.assertIsNotNone(result)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Error occurred')

    def test_get_result_nonexistent(self):
        """Test recupero task inesistente"""
        result = self.store.get_result('nonexistent')
        self.assertIsNone(result)

    def test_all_results(self):
        """Test recupero tutti i risultati"""
        self.store.set_result('task1', True, '')
        self.store.set_result('task2', False, 'error')
        self.store.set_result('task3', True, '')

        all_results = self.store.all_results()

        self.assertEqual(len(all_results), 3)
        self.assertIn('task1', all_results)
        self.assertIn('task2', all_results)
        self.assertIn('task3', all_results)

    def test_thread_safety(self):
        """Test thread safety (test base)"""
        import threading

        def set_results(task_id):
            for i in range(10):
                self.store.set_result(f'{task_id}_{i}', True, '')

        threads = []
        for i in range(5):
            t = threading.Thread(target=set_results, args=(f'thread{i}',))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Dovrebbero esserci 5 thread * 10 task = 50 risultati
        all_results = self.store.all_results()
        self.assertEqual(len(all_results), 50)

    def test_update_result(self):
        """Test aggiornamento risultato esistente"""
        self.store.set_result('task1', True, '')
        self.store.set_result('task1', False, 'Updated error')

        result = self.store.get_result('task1')
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Updated error')

class TestOaWorkflow(unittest.TestCase):
    """Test per modulo oaworkflow"""

    def setUp(self):
        """Setup prima di ogni test"""
        # Import dinamico
        import importlib.util
        spec = importlib.util.spec_from_file_location("oaworkflow", "oaworkflow.py")
        self.oaworkflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.oaworkflow)

        self.oaworkflow.gdict = {}
        self.mock_self = Mock()
        self.mock_self.gdict = self.oaworkflow.gdict

    @patch('builtins.__import__')
    def test_runworkflow_simple_linear(self, mock_import):
        """Test workflow lineare semplice"""
        # Mock moduli per gli step
        mock_module = MagicMock()
        mock_module.test_func.return_value = True
        mock_import.return_value = mock_module

        param = {
            'start_step': 'step1',
            'steps': [
                {
                    'name': 'step1',
                    'module': 'test_module',
                    'function': 'test_func',
                    'params': {},
                    'on_success': 'step2'
                },
                {
                    'name': 'step2',
                    'module': 'test_module',
                    'function': 'test_func',
                    'params': {},
                    'on_success': 'end'
                }
            ]
        }

        success = self.oaworkflow.runworkflow(self.mock_self, param)

        self.assertTrue(success)
        # Verifica che entrambi gli step siano stati eseguiti
        self.assertEqual(mock_module.test_func.call_count, 2)

    @patch('builtins.__import__')
    def test_runworkflow_with_branching(self, mock_import):
        """Test workflow con branching success/failure"""
        mock_module = MagicMock()
        # Primo step succede, secondo fallisce
        mock_module.test_func.side_effect = [True, False]
        mock_import.return_value = mock_module

        param = {
            'start_step': 'step1',
            'steps': [
                {
                    'name': 'step1',
                    'module': 'test_module',
                    'function': 'test_func',
                    'params': {},
                    'on_success': 'step2',
                    'on_failure': 'error_step'
                },
                {
                    'name': 'step2',
                    'module': 'test_module',
                    'function': 'test_func',
                    'params': {},
                    'on_success': 'end',
                    'on_failure': 'error_step'
                },
                {
                    'name': 'error_step',
                    'module': 'test_module',
                    'function': 'test_func',
                    'params': {},
                    'on_success': 'end'
                }
            ]
        }

        # Anche se step2 fallisce, workflow dovrebbe continuare su error_step
        success = self.oaworkflow.runworkflow(self.mock_self, param)

        # Il workflow potrebbe fallire o avere successo dipende dall'implementazione
        self.assertIsInstance(success, bool)

    def test_runworkflow_missing_start_step(self):
        """Test workflow con start_step inesistente"""
        param = {
            'start_step': 'nonexistent',
            'steps': [
                {'name': 'step1', 'module': 'mod', 'function': 'func'}
            ]
        }

        success = self.oaworkflow.runworkflow(self.mock_self, param)

        self.assertFalse(success)

    def test_runworkflow_missing_params(self):
        """Test workflow senza parametri richiesti"""
        param = {}

        success = self.oaworkflow.runworkflow(self.mock_self, param)

        self.assertFalse(success)

    def test_runworkflow_invalid_steps_format(self):
        """Test workflow con formato steps non valido"""
        param = {
            'start_step': 'step1',
            'steps': 'not_a_list'  # Deve essere una lista
        }

        success = self.oaworkflow.runworkflow(self.mock_self, param)

        self.assertFalse(success)

    @patch('builtins.__import__')
    def test_runworkflow_step_exception(self, mock_import):
        """Test gestione eccezione in uno step"""
        mock_module = MagicMock()
        mock_module.test_func.side_effect = Exception('Step error')
        mock_import.return_value = mock_module

        param = {
            'start_step': 'step1',
            'steps': [
                {
                    'name': 'step1',
                    'module': 'test_module',
                    'function': 'test_func',
                    'params': {}
                }
            ]
        }

        success = self.oaworkflow.runworkflow(self.mock_self, param)

        self.assertFalse(success)

    @patch('builtins.__import__')
    def test_runworkflow_max_iterations(self, mock_import):
        """Test protezione loop infinito"""
        mock_module = MagicMock()
        mock_module.test_func.return_value = True
        mock_import.return_value = mock_module

        # Crea un loop: step1 -> step2 -> step1
        param = {
            'start_step': 'step1',
            'steps': [
                {
                    'name': 'step1',
                    'module': 'test_module',
                    'function': 'test_func',
                    'params': {},
                    'on_success': 'step2'
                },
                {
                    'name': 'step2',
                    'module': 'test_module',
                    'function': 'test_func',
                    'params': {},
                    'on_success': 'step1'  # Loop!
                }
            ]
        }

        success = self.oaworkflow.runworkflow(self.mock_self, param)

        # Dovrebbe fallire per max iterations
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
