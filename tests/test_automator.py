"""
Unit Tests per automator.py
Test del workflow engine e componenti correlati
"""
import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from automator import WorkflowContext, WorkflowEngine, TaskResult, TaskStatus
from taskstore import TaskResultStore

class TestTaskStatus(unittest.TestCase):
    """Test per l'enum TaskStatus"""

    def test_task_status_values(self):
        """Test valori enum TaskStatus"""
        self.assertEqual(TaskStatus.PENDING.value, "pending")
        self.assertEqual(TaskStatus.RUNNING.value, "running")
        self.assertEqual(TaskStatus.SUCCESS.value, "success")
        self.assertEqual(TaskStatus.FAILED.value, "failed")
        self.assertEqual(TaskStatus.SKIPPED.value, "skipped")

class TestTaskResult(unittest.TestCase):
    """Test per la classe TaskResult"""

    def test_task_result_creation(self):
        """Test creazione TaskResult"""
        result = TaskResult(
            task_name="test_task",
            status=TaskStatus.SUCCESS,
            output={"key": "value"},
            duration=1.5
        )

        self.assertEqual(result.task_name, "test_task")
        self.assertEqual(result.status, TaskStatus.SUCCESS)
        self.assertEqual(result.output, {"key": "value"})
        self.assertEqual(result.duration, 1.5)
        self.assertIsInstance(result.timestamp, datetime)

    def test_task_result_defaults(self):
        """Test valori default di TaskResult"""
        result = TaskResult(
            task_name="minimal_task",
            status=TaskStatus.PENDING
        )

        self.assertIsNone(result.output)
        self.assertEqual(result.error, "")
        self.assertEqual(result.duration, 0.0)

class TestWorkflowContext(unittest.TestCase):
    """Test per la classe WorkflowContext"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.context = WorkflowContext()

    def test_context_initialization(self):
        """Test inizializzazione context"""
        self.assertIsInstance(self.context._results, dict)
        self.assertIsInstance(self.context._global_data, dict)
        self.assertEqual(len(self.context._results), 0)

    def test_set_and_get_task_result(self):
        """Test salvataggio e recupero risultato task"""
        result = TaskResult("task1", TaskStatus.SUCCESS, output="test_output")
        self.context.set_task_result("task1", result)

        retrieved = self.context.get_task_result("task1")
        self.assertEqual(retrieved, result)
        self.assertEqual(retrieved.output, "test_output")

    def test_get_task_output(self):
        """Test recupero solo output di un task"""
        result = TaskResult("task2", TaskStatus.SUCCESS, output={"data": 123})
        self.context.set_task_result("task2", result)

        output = self.context.get_task_output("task2")
        self.assertEqual(output, {"data": 123})

    def test_get_task_output_nonexistent(self):
        """Test recupero output di task inesistente"""
        output = self.context.get_task_output("nonexistent")
        self.assertIsNone(output)

    def test_get_last_output(self):
        """Test recupero ultimo output"""
        result1 = TaskResult("task1", TaskStatus.SUCCESS, output="first")
        result2 = TaskResult("task2", TaskStatus.SUCCESS, output="second")

        self.context.set_task_result("task1", result1)
        self.context.set_task_result("task2", result2)

        last_output = self.context.get_last_output()
        self.assertEqual(last_output, "second")

    def test_get_last_output_empty(self):
        """Test get_last_output su context vuoto"""
        output = self.context.get_last_output()
        self.assertIsNone(output)

    def test_set_and_get_global(self):
        """Test variabili globali"""
        self.context.set_global("config_key", "config_value")
        value = self.context.get_global("config_key")
        self.assertEqual(value, "config_value")

    def test_get_global_with_default(self):
        """Test get_global con default"""
        value = self.context.get_global("nonexistent", "default_value")
        self.assertEqual(value, "default_value")

    def test_get_all_outputs(self):
        """Test recupero tutti gli output"""
        result1 = TaskResult("task1", TaskStatus.SUCCESS, output="out1")
        result2 = TaskResult("task2", TaskStatus.SUCCESS, output="out2")

        self.context.set_task_result("task1", result1)
        self.context.set_task_result("task2", result2)

        all_outputs = self.context.get_all_outputs()
        self.assertEqual(all_outputs, {"task1": "out1", "task2": "out2"})

    def test_get_all_results(self):
        """Test recupero tutti i risultati"""
        result1 = TaskResult("task1", TaskStatus.SUCCESS)
        result2 = TaskResult("task2", TaskStatus.FAILED, error="error")

        self.context.set_task_result("task1", result1)
        self.context.set_task_result("task2", result2)

        all_results = self.context.get_all_results()
        self.assertEqual(len(all_results), 2)
        self.assertIn("task1", all_results)
        self.assertIn("task2", all_results)

class TestWorkflowEngine(unittest.TestCase):
    """Test per WorkflowEngine"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.gdict = {}
        self.task_store = TaskResultStore()

    def test_find_entry_point_unreferenced_task(self):
        """Test ricerca entry point (task non referenziato)"""
        tasks = [
            {'name': 'task1', 'on_success': 'task2'},
            {'name': 'task2', 'on_success': 'end'}
        ]

        engine = WorkflowEngine(tasks, self.gdict, self.task_store)
        entry = engine._find_entry_point()
        self.assertEqual(entry, 'task1')

    def test_find_entry_point_fallback_first(self):
        """Test fallback a primo task se tutti referenziati"""
        tasks = [
            {'name': 'task1', 'on_success': 'task2'},
            {'name': 'task2', 'on_success': 'task1'}  # Loop
        ]

        engine = WorkflowEngine(tasks, self.gdict, self.task_store)
        entry = engine._find_entry_point()
        self.assertEqual(entry, 'task1')

    def test_parse_task_definition_explicit_format(self):
        """Test parsing task con module e function espliciti"""
        task_def = {
            'name': 'test',
            'module': 'oa-io',
            'function': 'copy',
            'src': '/tmp/file',
            'dst': '/tmp/dest'
        }

        engine = WorkflowEngine([], self.gdict, self.task_store)
        module, func, params = engine._parse_task_definition(task_def)

        self.assertEqual(module, 'oa-io')
        self.assertEqual(func, 'copy')
        self.assertIn('src', params)
        self.assertIn('dst', params)
        self.assertNotIn('module', params)
        self.assertNotIn('function', params)

    def test_parse_task_definition_dotted_format(self):
        """Test parsing task con formato module.function"""
        task_def = {
            'name': 'test',
            'oa-io.copy': {
                'src': '/tmp/file',
                'dst': '/tmp/dest'
            }
        }

        engine = WorkflowEngine([], self.gdict, self.task_store)
        module, func, params = engine._parse_task_definition(task_def)

        self.assertEqual(module, 'oa-io')
        self.assertEqual(func, 'copy')
        self.assertEqual(params['src'], '/tmp/file')

    @patch('automator.logger')
    def test_execute_task_success_with_tuple_return(self, mock_logger):
        """Test esecuzione task che ritorna tupla (success, output)"""
        # Mock del modulo
        mock_module = MagicMock()
        mock_func = MagicMock(return_value=(True, {"result": "data"}))
        mock_module.test_func = mock_func

        task_def = {
            'name': 'test_task',
            'module': 'mock_module',
            'function': 'test_func'
        }

        tasks = [task_def]
        engine = WorkflowEngine(tasks, self.gdict, self.task_store)

        with patch('builtins.__import__', return_value=mock_module):
            success = engine._execute_task('test_task', 1)

        self.assertTrue(success)
        result = engine.context.get_task_result('test_task')
        self.assertEqual(result.status, TaskStatus.SUCCESS)
        self.assertEqual(result.output, {"result": "data"})

    @patch('automator.logger')
    def test_execute_task_failure(self, mock_logger):
        """Test esecuzione task che fallisce"""
        mock_module = MagicMock()
        mock_func = MagicMock(return_value=False)
        mock_module.test_func = mock_func

        task_def = {
            'name': 'failing_task',
            'module': 'mock_module',
            'function': 'test_func'
        }

        tasks = [task_def]
        engine = WorkflowEngine(tasks, self.gdict, self.task_store)

        with patch('builtins.__import__', return_value=mock_module):
            success = engine._execute_task('failing_task', 1)

        self.assertFalse(success)
        result = engine.context.get_task_result('failing_task')
        self.assertEqual(result.status, TaskStatus.FAILED)

if __name__ == '__main__':
    unittest.main()
