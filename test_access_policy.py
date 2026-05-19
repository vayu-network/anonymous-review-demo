from __future__ import annotations

import threading

import pytest

from access_policy import Policy


def test_can_returns_true_after_grant() -> None:
    policy = Policy()
    policy.grant("admin", "document", "read")
    assert policy.can("admin", "document", "read") is True


def test_can_returns_false_after_revoke() -> None:
    policy = Policy()
    policy.grant("admin", "document", "read")
    policy.revoke("admin", "document", "read")
    assert policy.can("admin", "document", "read") is False


def test_can_returns_false_for_never_granted_role() -> None:
    policy = Policy()
    assert policy.can("guest", "document", "write") is False


def test_can_returns_false_for_unrelated_permission() -> None:
    policy = Policy()
    policy.grant("editor", "document", "read")
    assert policy.can("editor", "document", "write") is False
    assert policy.can("editor", "image", "read") is False


def test_revoke_nonexistent_permission_does_not_raise() -> None:
    policy = Policy()
    # Should not raise even if no permission was ever granted
    policy.revoke("nobody", "resource", "action")

    # Also should not raise if the role exists but the specific permission doesn't
    policy.grant("admin", "document", "read")
    policy.revoke("admin", "document", "write")  # never granted


def test_roles_with_access_returns_correct_roles() -> None:
    policy = Policy()
    policy.grant("admin", "document", "read")
    policy.grant("editor", "document", "read")
    policy.grant("viewer", "document", "write")  # different action

    roles = policy.roles_with_access("document", "read")
    assert sorted(roles) == ["admin", "editor"]


def test_roles_with_access_excludes_revoked_roles() -> None:
    policy = Policy()
    policy.grant("admin", "document", "read")
    policy.grant("editor", "document", "read")
    policy.revoke("editor", "document", "read")

    roles = policy.roles_with_access("document", "read")
    assert roles == ["admin"]


def test_roles_with_access_returns_empty_when_none() -> None:
    policy = Policy()
    roles = policy.roles_with_access("document", "delete")
    assert roles == []


def test_roles_with_access_exact_resource_and_action_match() -> None:
    policy = Policy()
    policy.grant("admin", "document", "read")
    policy.grant("admin", "image", "read")
    policy.grant("admin", "document", "write")

    # Only the exact pair should match
    roles_doc_read = policy.roles_with_access("document", "read")
    assert roles_doc_read == ["admin"]

    roles_image_write = policy.roles_with_access("image", "write")
    assert roles_image_write == []


def test_permissions_are_additive() -> None:
    policy = Policy()
    policy.grant("admin", "document", "read")
    policy.grant("admin", "document", "write")
    policy.grant("admin", "image", "delete")

    assert policy.can("admin", "document", "read") is True
    assert policy.can("admin", "document", "write") is True
    assert policy.can("admin", "image", "delete") is True
    assert policy.can("admin", "image", "read") is False


def test_thread_safety() -> None:
    policy = Policy()
    errors: list[Exception] = []

    def grant_permissions() -> None:
        try:
            for i in range(100):
                policy.grant(f"role_{i}", "resource", "action")
        except Exception as exc:
            errors.append(exc)

    def revoke_permissions() -> None:
        try:
            for i in range(100):
                policy.revoke(f"role_{i}", "resource", "action")
        except Exception as exc:
            errors.append(exc)

    def check_permissions() -> None:
        try:
            for i in range(100):
                policy.can(f"role_{i}", "resource", "action")
        except Exception as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=grant_permissions),
        threading.Thread(target=revoke_permissions),
        threading.Thread(target=check_permissions),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Thread safety errors: {errors}"
