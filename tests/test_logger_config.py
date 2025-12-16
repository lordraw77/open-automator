"""
Unit Tests per logger_config.py
Test del sistema di logging centralizzato
"""

import unittest
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch
import sys
import os

# Aggiungi la directory parent al path per importare i moduli
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logger_config import AutomatorLogger, TaskLogger


class TestAutomatorLogger(unittest.TestCase):
    """Test per la classe AutomatorLogger"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_log_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Cleanup dopo ogni test"""
        # Rimuovi handler per evitare interferenze tra test
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Rimuovi directory temporanea
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)

    def test_setup_logging_creates_directory(self):
        """Test che setup_logging crei la directory dei log"""
        AutomatorLogger.setup_logging(log_dir=self.test_log_dir)

        self.assertTrue(os.path.exists(self.test_log_dir))
        self.assertTrue(os.path.isdir(self.test_log_dir))

    def test_setup_logging_creates_log_file(self):
        """Test che venga creato il file di log"""
        AutomatorLogger.setup_logging(log_dir=self.test_log_dir)

        # Verifica che esista un file log con il formato corretto
        log_files = list(Path(self.test_log_dir).glob('automator_*.log'))
        self.assertEqual(len(log_files), 1)

        # Verifica il formato del nome file
        expected_date = datetime.now().strftime("%Y%m%d")
        self.assertIn(expected_date, log_files[0].name)

    def test_setup_logging_configures_handlers(self):
        """Test che vengano configurati file handler e console handler"""
        AutomatorLogger.setup_logging(
            log_dir=self.test_log_dir,
            console_level='INFO',
            file_level='DEBUG'
        )

        root_logger = logging.getLogger()
        self.assertEqual(len(root_logger.handlers), 2)

        # Verifica tipi di handler
        handler_types = [type(h).__name__ for h in root_logger.handlers]
        self.assertIn('RotatingFileHandler', handler_types)
        self.assertIn('StreamHandler', handler_types)

    def test_get_logger_returns_logger(self):
        """Test che get_logger restituisca un logger valido"""
        AutomatorLogger.setup_logging(log_dir=self.test_log_dir)

        logger = AutomatorLogger.get_logger('test_module')

        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'test_module')

    def test_get_logger_caches_loggers(self):
        """Test che i logger vengano cachati"""
        AutomatorLogger.setup_logging(log_dir=self.test_log_dir)

        logger1 = AutomatorLogger.get_logger('test_module')
        logger2 = AutomatorLogger.get_logger('test_module')

        self.assertIs(logger1, logger2)

    def test_set_console_level(self):
        """Test che set_console_level cambi il livello"""
        AutomatorLogger.setup_logging(log_dir=self.test_log_dir, console_level='INFO')

        AutomatorLogger.set_console_level('DEBUG')

        # Trova console handler
        root_logger = logging.getLogger()
        console_handler = None
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not hasattr(handler, 'baseFilename'):
                console_handler = handler
                break

        self.assertIsNotNone(console_handler)
        self.assertEqual(console_handler.level, logging.DEBUG)

    def test_set_file_level(self):
        """Test che set_file_level cambi il livello"""
        AutomatorLogger.setup_logging(log_dir=self.test_log_dir, file_level='INFO')

        AutomatorLogger.set_file_level('WARNING')

        # Trova file handler
        root_logger = logging.getLogger()
        file_handler = None
        for handler in root_logger.handlers:
            if hasattr(handler, 'baseFilename'):
                file_handler = handler
                break

        self.assertIsNotNone(file_handler)
        self.assertEqual(file_handler.level, logging.WARNING)


class TestTaskLogger(unittest.TestCase):
    """Test per la classe TaskLogger"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_log_dir = tempfile.mkdtemp()
        AutomatorLogger.setup_logging(log_dir=self.test_log_dir)
        self.logger = AutomatorLogger.get_logger('test_task')

    def tearDown(self):
        """Cleanup dopo ogni test"""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)

    def test_task_logger_success(self):
        """Test TaskLogger con task che ha successo"""
        with patch.object(self.logger, 'info') as mock_info:
            with TaskLogger(self.logger, 'test_task', 1, 5):
                pass  # Task che ha successo

            # Verifica che siano stati loggati inizio e fine
            self.assertGreater(mock_info.call_count, 0)

            # Verifica che ci sia il messaggio di successo
            success_calls = [call for call in mock_info.call_args_list 
                           if 'SUCCESS' in str(call)]
            self.assertGreater(len(success_calls), 0)

    def test_task_logger_failure(self):
        """Test TaskLogger con task che fallisce"""
        with patch.object(self.logger, 'error') as mock_error:
            try:
                with TaskLogger(self.logger, 'failing_task', 2, 5):
                    raise ValueError("Test error")
            except ValueError:
                pass  # Atteso

            # Verifica che sia stato loggato l'errore
            self.assertGreater(mock_error.call_count, 0)

            # Verifica che ci sia il messaggio di fallimento
            fail_calls = [call for call in mock_error.call_args_list 
                         if 'FAILED' in str(call)]
            self.assertGreater(len(fail_calls), 0)

    def test_task_logger_tracks_duration(self):
        """Test che TaskLogger tracci la durata"""
        import time

        with patch.object(self.logger, 'info') as mock_info:
            with TaskLogger(self.logger, 'timed_task', 1, 1):
                time.sleep(0.1)

            # Cerca chiamata con durata
            duration_calls = [call for call in mock_info.call_args_list 
                            if 'duration:' in str(call)]
            self.assertGreater(len(duration_calls), 0)

    def test_task_logger_includes_task_info(self):
        """Test che TaskLogger includa le informazioni del task"""
        task_name = 'important_task'
        task_num = 3
        total_tasks = 10

        with patch.object(self.logger, 'info') as mock_info:
            with TaskLogger(self.logger, task_name, task_num, total_tasks):
                pass

            # Verifica che le info del task siano presenti
            all_calls_str = str(mock_info.call_args_list)
            self.assertIn(task_name, all_calls_str)
            self.assertIn(f'[{task_num}/{total_tasks}]', all_calls_str)


class TestLoggingIntegration(unittest.TestCase):
    """Test di integrazione per il sistema di logging"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_log_dir = tempfile.mkdtemp()
        AutomatorLogger.setup_logging(
            log_dir=self.test_log_dir,
            console_level='DEBUG',
            file_level='DEBUG'
        )

    def tearDown(self):
        """Cleanup dopo ogni test"""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)

    def test_log_file_contains_messages(self):
        """Test che i messaggi vengano scritti nel file di log"""
        logger = AutomatorLogger.get_logger('integration_test')
        test_message = 'Integration test message'

        logger.info(test_message)

        # Forza flush degli handler
        for handler in logging.getLogger().handlers:
            handler.flush()

        # Leggi il file di log
        log_files = list(Path(self.test_log_dir).glob('automator_*.log'))
        self.assertEqual(len(log_files), 1)

        with open(log_files[0], 'r') as f:
            log_content = f.read()

        self.assertIn(test_message, log_content)

    def test_different_log_levels(self):
        """Test che diversi livelli di log vengano registrati correttamente"""
        logger = AutomatorLogger.get_logger('level_test')

        logger.debug('Debug message')
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')

        # Forza flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        # Leggi il file di log
        log_files = list(Path(self.test_log_dir).glob('automator_*.log'))
        with open(log_files[0], 'r') as f:
            log_content = f.read()

        # Verifica che tutti i livelli siano presenti
        self.assertIn('DEBUG', log_content)
        self.assertIn('INFO', log_content)
        self.assertIn('WARNING', log_content)
        self.assertIn('ERROR', log_content)


if __name__ == '__main__':
    unittest.main()
