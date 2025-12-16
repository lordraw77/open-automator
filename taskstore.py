import threading

class TaskResultStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}

    def set_result(self, task_id, success, error_msg=""):
        with self._lock:
            self._data[task_id] = {
                "success": bool(success),
                "error": str(error_msg) if error_msg else ""
            }

    def get_result(self, task_id):
        with self._lock:
            return self._data.get(task_id)

    def all_results(self):
        with self._lock:
            return dict(self._data)
