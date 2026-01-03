"""
Workflow Manager - Sistema Centralizzato per Gestione Engine
Thread-safe, Singleton pattern, Memory management ottimizzato
FIXED: Nessun circular import con automator.py
"""

import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, field
import logging

# ========================================
# IMPORT CONDIZIONALE PER EVITARE CIRCULAR IMPORT
# ========================================
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import solo per type checking, non a runtime
    from automator import WorkflowEngine, WorkflowContext

# ========================================
# LOGGING
# ========================================
logger = logging.getLogger("workflow-manager")
registry_logger = logging.getLogger("workflow-registry")
engine_logger = logging.getLogger("workflow-engine-manager")
facade_logger = logging.getLogger("workflow-facade")

# ========================================
# ENUMS E DATACLASSES
# ========================================

class WorkflowExecutionStatus(Enum):
    """Stati possibili di un'esecuzione workflow"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ERROR = "error"

@dataclass
class WorkflowMetadata:
    """Metadati di un workflow registrato"""
    workflow_id: str
    name: str
    filepath: Optional[str]
    content: Dict[str, Any]
    created_at: datetime
    task_count: int
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Converte in dizionario serializzabile"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "filepath": self.filepath,
            "task_count": self.task_count,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at.isoformat()
        }

@dataclass
class WorkflowExecution:
    """Rappresenta un'esecuzione di un workflow"""
    execution_id: str
    workflow_id: str
    status: WorkflowExecutionStatus
    engine: Optional[Any] = None  # WorkflowEngine (Any per evitare circular import)
    context: Optional[Any] = None  # WorkflowContext (Any per evitare circular import)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)

    @property
    def duration(self) -> Optional[float]:
        """Calcola la durata in secondi"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict:
        """Converte in dizionario serializzabile"""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "error": self.error,
            "results": self.results,
            "logs": self.logs
        }

# ========================================
# WORKFLOW REGISTRY (SINGLETON)
# ========================================

class WorkflowRegistry:
    """
    Registry centralizzato per workflow (Singleton, Thread-safe)
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._workflows: Dict[str, WorkflowMetadata] = {}
            self._initialized = True
            registry_logger.info("WorkflowRegistry initialized (Singleton)")

    def register(self, workflow_id: str, metadata: WorkflowMetadata) -> None:
        """Registra un workflow nel registry"""
        with self._lock:
            self._workflows[workflow_id] = metadata
            registry_logger.info(f"Workflow registered: {workflow_id} ({metadata.name})")

    def unregister(self, workflow_id: str) -> bool:
        """Rimuove un workflow dal registry"""
        with self._lock:
            if workflow_id in self._workflows:
                del self._workflows[workflow_id]
                registry_logger.info(f"Workflow unregistered: {workflow_id}")
                return True
            return False

    def get(self, workflow_id: str) -> Optional[WorkflowMetadata]:
        """Recupera metadati di un workflow"""
        with self._lock:
            return self._workflows.get(workflow_id)

    def list_all(self) -> List[WorkflowMetadata]:
        """Lista tutti i workflow registrati"""
        with self._lock:
            return list(self._workflows.values())

    def exists(self, workflow_id: str) -> bool:
        """Verifica se un workflow esiste"""
        with self._lock:
            return workflow_id in self._workflows

    def clear(self) -> None:
        """Rimuove tutti i workflow (use with caution!)"""
        with self._lock:
            count = len(self._workflows)
            self._workflows.clear()
            registry_logger.warning(f"Registry cleared: {count} workflows removed")

# ========================================
# WORKFLOW ENGINE MANAGER (SINGLETON)
# ========================================

class WorkflowEngineManager:
    """
    Manager per il ciclo di vita degli engine (Singleton, Thread-safe)
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, max_concurrent_executions: int = 5):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_concurrent_executions: int = 5):
        if not hasattr(self, '_initialized'):
            self._executions: Dict[str, WorkflowExecution] = {}
            self._execution_history: List[WorkflowExecution] = []
            self._max_history_size = 100
            self._semaphore = threading.Semaphore(max_concurrent_executions)
            self._max_concurrent = max_concurrent_executions
            self._initialized = True
            engine_logger.info(f"WorkflowEngineManager initialized (max_concurrent: {max_concurrent_executions})")

    def create_execution(
        self,
        workflow_id: str,
        gdict: Dict[str, Any],
        wallet: Optional[Any] = None,
        debug: bool = False,
        debug2: bool = False
    ) -> str:
        """
        Crea una nuova esecuzione workflow
        Returns: execution_id
        """
        # Import runtime per evitare circular import
        from automator import WorkflowEngine, WorkflowContext
        from taskstore import TaskResultStore
        import oacommon

        execution_id = f"exec_{uuid.uuid4().hex[:16]}"

        with self._lock:
            # Recupera workflow dal registry
            registry = WorkflowRegistry()
            metadata = registry.get(workflow_id)

            if not metadata:
                raise ValueError(f"Workflow not found in registry: {workflow_id}")

            # Estrai tasks
            tasks = metadata.content[0].get("tasks", [])

            # Prepara gdict per esecuzione
            exec_gdict = dict(gdict)
            exec_gdict["DEBUG"] = debug
            exec_gdict["DEBUG2"] = debug2

            if wallet:
                exec_gdict["wallet"] = wallet

            # Sincronizza con oacommon
            oacommon.gdict = exec_gdict

            # Crea taskstore
            taskstore = TaskResultStore()

            # Crea engine
            engine = WorkflowEngine(tasks, exec_gdict, taskstore, debug, debug2)

            # Crea context vuoto (sarà popolato durante l'esecuzione)
            context = WorkflowContext()

            # Crea execution object
            execution = WorkflowExecution(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status=WorkflowExecutionStatus.PENDING,
                engine=engine,
                context=context,
                started_at=None,
                completed_at=None
            )

            self._executions[execution_id] = execution
            engine_logger.info(f"Execution created: {execution_id} for workflow {workflow_id}")

            return execution_id

    def start_execution(self, execution_id: str, async_mode: bool = False) -> Tuple[bool, Optional[Any]]:
        """
        Avvia l'esecuzione di un workflow
        Returns: (success, context)
        """
        with self._lock:
            execution = self._executions.get(execution_id)

            if not execution:
                raise ValueError(f"Execution not found: {execution_id}")

            if execution.status != WorkflowExecutionStatus.PENDING:
                raise ValueError(f"Execution {execution_id} already started (status: {execution.status.value})")

        def run_execution():
            try:
                # Acquisisce semaforo per concorrenza
                acquired = self._semaphore.acquire(timeout=1)

                if not acquired:
                    with self._lock:
                        execution.status = WorkflowExecutionStatus.QUEUED
                    engine_logger.warning(f"Execution {execution_id} queued (max concurrent reached)")

                    # Riprova ad acquisire (blocking)
                    self._semaphore.acquire()

                with self._lock:
                    execution.status = WorkflowExecutionStatus.RUNNING
                    execution.started_at = datetime.now()

                engine_logger.info(f"Execution started: {execution_id}")

                # Esegui workflow
                success, context = execution.engine.execute()

                with self._lock:
                    execution.context = context
                    execution.completed_at = datetime.now()
                    execution.status = WorkflowExecutionStatus.COMPLETED if success else WorkflowExecutionStatus.FAILED

                    # Serializza risultati
                    execution.results = self._serialize_context(context)

                engine_logger.info(f"Execution completed: {execution_id} (success: {success})")

                # Archivia l'esecuzione
                self._archive_execution(execution_id)

                return success, context

            except Exception as e:
                engine_logger.error(f"Execution error {execution_id}: {e}", exc_info=True)

                with self._lock:
                    execution.status = WorkflowExecutionStatus.ERROR
                    execution.error = str(e)
                    execution.completed_at = datetime.now()

                self._archive_execution(execution_id)

                return False, None

            finally:
                # Rilascia semaforo
                self._semaphore.release()

        if async_mode:
            # Esecuzione asincrona in thread separato
            thread = threading.Thread(target=run_execution, daemon=True)
            thread.start()
            return True, None  # Ritorna subito
        else:
            # Esecuzione sincrona
            return run_execution()

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Recupera un'esecuzione (attiva o dalla history)"""
        with self._lock:
            # Cerca nelle esecuzioni attive
            if execution_id in self._executions:
                return self._executions[execution_id]

            # Cerca nella history
            for exec in self._execution_history:
                if exec.execution_id == execution_id:
                    return exec

            return None

    def get_active_executions(self) -> List[WorkflowExecution]:
        """Ritorna tutte le esecuzioni attive"""
        with self._lock:
            return [
                exec for exec in self._executions.values()
                if exec.status == WorkflowExecutionStatus.RUNNING
            ]

    def get_workflow_executions(self, workflow_id: str) -> List[WorkflowExecution]:
        """Ritorna tutte le esecuzioni di un workflow (attive + history)"""
        with self._lock:
            executions = []

            # Attive
            for exec in self._executions.values():
                if exec.workflow_id == workflow_id:
                    executions.append(exec)

            # History
            for exec in self._execution_history:
                if exec.workflow_id == workflow_id:
                    executions.append(exec)

            return executions

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancella un'esecuzione (se possibile)"""
        with self._lock:
            execution = self._executions.get(execution_id)

            if not execution:
                return False

            if execution.status in [WorkflowExecutionStatus.COMPLETED, WorkflowExecutionStatus.FAILED, WorkflowExecutionStatus.ERROR]:
                return False

            execution.status = WorkflowExecutionStatus.CANCELLED
            execution.completed_at = datetime.now()

            self._archive_execution(execution_id)

            engine_logger.info(f"Execution cancelled: {execution_id}")
            return True

    def _archive_execution(self, execution_id: str) -> None:
        """Archivia un'esecuzione completata nella history"""
        with self._lock:
            execution = self._executions.get(execution_id)

            if not execution:
                return

            # Rimuovi engine e context per liberare memoria
            # Ma mantieni i risultati serializzati
            execution.engine = None
            execution.context = None

            # Aggiungi alla history
            self._execution_history.append(execution)

            # Rimuovi dalle esecuzioni attive
            del self._executions[execution_id]

            # Limita dimensione history
            if len(self._execution_history) > self._max_history_size:
                removed = self._execution_history.pop(0)
                engine_logger.debug(f"Removed old execution from history: {removed.execution_id}")

    def _serialize_context(self, context: Any) -> Dict[str, Any]:
        """Serializza i risultati del context"""
        try:
            results = {}
            # Ottieni tutti i risultati dal context
            for name, task_result in context.get_all_results().items():
                # Serializza l'output mantenendo la struttura
                output_serialized = None
                if task_result.output:
                    if isinstance(task_result.output, (dict, list)):
                        output_serialized = task_result.output  # ✅ Mantieni dict/list
                    elif isinstance(task_result.output, (str, int, float, bool)):
                        output_serialized = task_result.output
                    else:
                        output_serialized = str(task_result.output)
                
                results[name] = {
                    "task_name": task_result.task_name,
                    "status": task_result.status.value if hasattr(task_result.status, 'value') else str(task_result.status),
                    "output": output_serialized,  # ✅ CORRETTO
                    "error": task_result.error,
                    "duration": task_result.duration,
                    "timestamp": task_result.timestamp.isoformat() if task_result.timestamp else None
                }
            
            return results
        except Exception as e:
            engine_logger.error(f"Failed to serialize context: {e}")
            return {}


    def cleanup_completed(self, max_age_seconds: int = 3600) -> int:
        """
        Rimuove esecuzioni completate più vecchie di max_age_seconds
        Returns: numero di esecuzioni rimosse
        """
        with self._lock:
            now = datetime.now()
            removed_count = 0

            # Filtra history
            new_history = []
            for exec in self._execution_history:
                if exec.completed_at:
                    age = (now - exec.completed_at).total_seconds()
                    if age > max_age_seconds:
                        removed_count += 1
                        continue

                new_history.append(exec)

            self._execution_history = new_history

            if removed_count > 0:
                engine_logger.info(f"Cleanup: removed {removed_count} old executions")

            return removed_count

    def get_stats(self) -> Dict[str, Any]:
        """Ritorna statistiche del manager"""
        with self._lock:
            active_count = sum(1 for e in self._executions.values() if e.status == WorkflowExecutionStatus.RUNNING)
            completed_count = sum(1 for e in self._execution_history if e.status == WorkflowExecutionStatus.COMPLETED)
            failed_count = sum(1 for e in self._execution_history if e.status in [WorkflowExecutionStatus.FAILED, WorkflowExecutionStatus.ERROR])

            return {
                "total_executions": len(self._executions) + len(self._execution_history),
                "active_executions": active_count,
                "completed_executions": completed_count,
                "failed_executions": failed_count,
                "history_size": len(self._execution_history),
                "max_concurrent": self._max_concurrent,
                "available_slots": self._max_concurrent - active_count
            }

# ========================================
# WORKFLOW MANAGER FACADE
# ========================================

class WorkflowManagerFacade:
    """
    Interfaccia semplificata per gestione workflow
    Combina Registry ed EngineManager
    """

    def __init__(self, max_concurrent_executions: int = 5):
        self.registry = WorkflowRegistry()
        self.engine_manager = WorkflowEngineManager(max_concurrent_executions)
        facade_logger.info("WorkflowManagerFacade initialized")

    def register_workflow(
        self,
        workflow_id: str,
        name: str,
        content: Dict[str, Any],
        filepath: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> WorkflowMetadata:
        """Registra un nuovo workflow"""

        # Estrai task count
        task_count = 0
        if isinstance(content, list) and len(content) > 0:
            tasks = content[0].get("tasks", [])
            task_count = len(tasks)

        metadata = WorkflowMetadata(
            workflow_id=workflow_id,
            name=name,
            filepath=filepath,
            content=content,
            created_at=datetime.now(),
            task_count=task_count,
            description=description,
            tags=tags or []
        )

        self.registry.register(workflow_id, metadata)
        facade_logger.info(f"Workflow registered: {workflow_id} ({task_count} tasks)")

        return metadata

    def execute_workflow(
        self,
        workflow_id: str,
        gdict: Optional[Dict[str, Any]] = None,
        wallet: Optional[Any] = None,
        debug: bool = False,
        debug2: bool = False,
        async_mode: bool = False
    ) -> Tuple[str, bool, Optional[Any]]:
        """
        Esegue un workflow
        Returns: (execution_id, success, context)
        """

        if gdict is None:
            gdict = {}

        # Crea esecuzione
        execution_id = self.engine_manager.create_execution(
            workflow_id=workflow_id,
            gdict=gdict,
            wallet=wallet,
            debug=debug,
            debug2=debug2
        )

        # Avvia esecuzione
        success, context = self.engine_manager.start_execution(execution_id, async_mode)

        facade_logger.info(f"Workflow executed: {workflow_id} (execution_id: {execution_id}, async: {async_mode})")

        return execution_id, success, context

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowMetadata]:
        """Recupera metadati workflow"""
        return self.registry.get(workflow_id)

    def list_workflows(self) -> List[WorkflowMetadata]:
        """Lista tutti i workflow"""
        return self.registry.list_all()

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Recupera stato esecuzione"""
        return self.engine_manager.get_execution(execution_id)

    def get_workflow_history(self, workflow_id: str) -> List[WorkflowExecution]:
        """Recupera storico esecuzioni di un workflow"""
        return self.engine_manager.get_workflow_executions(workflow_id)

    def get_stats(self) -> Dict[str, Any]:
        """Recupera statistiche complete"""
        return {
            "workflows": {
                "total": len(self.registry.list_all())
            },
            "executions": self.engine_manager.get_stats()
        }

