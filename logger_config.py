"""
Open-Automator Logging Configuration Module
Gestisce la configurazione centralizzata del logging per tutti i moduli
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional


class AutomatorLogger:
    """Gestisce la configurazione centralizzata del logging per Open-Automator"""

    _loggers = {}
    _file_handler = None
    _console_handler = None

    @classmethod
    def setup_logging(cls, 
                     log_dir: str = './logs',
                     console_level: str = 'INFO',
                     file_level: str = 'DEBUG',
                     max_bytes: int = 10485760,  # 10MB
                     backup_count: int = 5) -> None:
        """
        Configura il sistema di logging globale

        Args:
            log_dir: Directory dove salvare i log file
            console_level: Livello minimo per output console (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            file_level: Livello minimo per file log
            max_bytes: Dimensione massima file log prima della rotazione
            backup_count: Numero di file di backup da mantenere
        """

        # Crea directory log se non esiste
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Nome file log con timestamp
        log_file = log_path / f'automator_{datetime.now().strftime("%Y%m%d")}.log'

        # Formato dettagliato per file
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Formato semplificato per console
        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )

        # Handler per file con rotazione
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, file_level.upper()))
        file_handler.setFormatter(file_formatter)

        # Handler per console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, console_level.upper()))
        console_handler.setFormatter(console_formatter)

        # Configura root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Cattura tutto, i handler filtrano

        # Rimuovi handler esistenti per evitare duplicati
        root_logger.handlers.clear()

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        cls._file_handler = file_handler
        cls._console_handler = console_handler

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Ottiene un logger per un modulo specifico

        Args:
            name: Nome del modulo (es. 'oa-system', 'oa-io')

        Returns:
            Logger configurato per il modulo
        """
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        return cls._loggers[name]

    @classmethod
    def set_console_level(cls, level: str) -> None:
        """Cambia dinamicamente il livello di log della console"""
        if cls._console_handler:
            cls._console_handler.setLevel(getattr(logging, level.upper()))

    @classmethod
    def set_file_level(cls, level: str) -> None:
        """Cambia dinamicamente il livello di log del file"""
        if cls._file_handler:
            cls._file_handler.setLevel(getattr(logging, level.upper()))


class TaskLogger:
    """Context manager per logging di singoli task con indicazione finale esito"""

    def __init__(self, logger: logging.Logger, task_name: str, task_num: int, total_tasks: int):
        self.logger = logger
        self.task_name = task_name
        self.task_num = task_num
        self.total_tasks = total_tasks
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        separator = "-" * 70
        self.logger.info(separator)
        self.logger.info(f"▶ [{self.task_num}/{self.total_tasks}] STARTING: '{self.task_name}'")
        self.logger.info(separator)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        separator = "=" * 70

        if exc_type is not None:
            # Task FALLITO
            self.logger.error(separator)
            self.logger.error(
                f"✗ [{self.task_num}/{self.total_tasks}] FAILED: '{self.task_name}' "
                f"(duration: {duration:.2f}s)"
            )
            self.logger.error(f"Error: {exc_type.__name__}: {exc_val}")
            self.logger.error(separator)
            self.logger.error("")  # Riga vuota per separazione

            # Log stack trace completo solo in DEBUG
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("Full stack trace:", exc_info=True)

            return False  # Propaga l'eccezione
        else:
            # Task COMPLETATO CON SUCCESSO
            self.logger.info(separator)
            self.logger.info(
                f"✓ [{self.task_num}/{self.total_tasks}] SUCCESS: '{self.task_name}' "
                f"(duration: {duration:.2f}s)"
            )
            self.logger.info(separator)
            self.logger.info("")  # Riga vuota per separazione

        return True
