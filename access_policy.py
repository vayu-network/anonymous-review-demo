from __future__ import annotations

import threading
from collections import defaultdict


class Policy:
    def __init__(self) -> None:
        self._permissions: dict[str, set[tuple[str, str]]] = defaultdict(set)
        self._lock = threading.Lock()

    def grant(self, role: str, resource: str, action: str) -> None:
        with self._lock:
            self._permissions[role].add((resource, action))

    def revoke(self, role: str, resource: str, action: str) -> None:
        with self._lock:
            self._permissions[role].discard((resource, action))

    def can(self, role: str, resource: str, action: str) -> bool:
        with self._lock:
            return (resource, action) in self._permissions[role]

    def roles_with_access(self, resource: str, action: str) -> list[str]:
        with self._lock:
            return [
                role
                for role, perms in self._permissions.items()
                if (resource, action) in perms
            ]
