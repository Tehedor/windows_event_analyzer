# state/locks.py

from threading import Lock
from typing import Dict


class QueryLockManager:
    """
    Evita que una misma query se ejecute dos veces en paralelo.
    """

    def __init__(self):
        self._locks: Dict[str, Lock] = {}

    def acquire(self, query_id: str) -> Lock:
        if query_id not in self._locks:
            self._locks[query_id] = Lock()
        return self._locks[query_id]
