import threading
from typing import Set, Tuple, Dict, List


class Policy:
    def __init__(self) -> None:
        self._permissions: Dict[str, Set[Tuple[str, str]]] = {}
        self._lock: threading.Lock = threading.Lock()

    def grant(self, role: str, resource: str, action: str) -> None:
        with self._lock:
            if role not in self._permissions:
                self._permissions[role] = set()
            self._permissions[role].add((resource, action))

    def revoke(self, role: str, resource: str, action: str) -> None:
        with self._lock:
            if role in self._permissions:
                self._permissions[role].discard((resource, action))

    def can(self, role: str, resource: str, action: str) -> bool:
        with self._lock:
            return (resource, action) in self._permissions.get(role, set())

    def roles_with_access(self, resource: str, action: str) -> List[str]:
        with self._lock:
            return [
                role
                for role, perms in self._permissions.items()
                if (resource, action) in perms
            ]
