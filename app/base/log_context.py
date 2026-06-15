import threading
from typing import Optional

_thread_local = threading.local()


def init_log_context(request_id: str) -> None:
    _thread_local.request_id = request_id


def get_request_id() -> Optional[str]:
    return getattr(_thread_local, "request_id", None)


def clear_log_context() -> None:
    if hasattr(_thread_local, "request_id"):
        delattr(_thread_local, "request_id")
