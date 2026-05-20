import pytest
from access_policy import Policy


def test_can_returns_true_after_grant() -> None:
    p = Policy()
    p.grant("admin", "documents", "read")
    assert p.can("admin", "documents", "read") is True


def test_can_returns_false_after_revoke() -> None:
    p = Policy()
    p.grant("admin", "documents", "read")
    p.revoke("admin", "documents", "read")
    assert p.can("admin", "documents", "read") is False


def test_can_returns_false_for_never_granted_role() -> None:
    p = Policy()
    assert p.can("stranger", "documents", "read") is False


def test_roles_with_access_returns_only_exact_match() -> None:
    p = Policy()
    p.grant("admin", "documents", "read")
    p.grant("editor", "documents", "write")
    p.grant("viewer", "documents", "read")

    roles = p.roles_with_access("documents", "read")
    assert set(roles) == {"admin", "viewer"}
    assert "editor" not in roles


def test_roles_with_access_empty_when_none_match() -> None:
    p = Policy()
    p.grant("admin", "documents", "write")
    assert p.roles_with_access("documents", "read") == []


def test_revoke_non_existent_does_not_raise() -> None:
    p = Policy()
    # Should not raise even if role has no permissions at all
    p.revoke("ghost", "documents", "read")

    # Should not raise even if role exists but lacks this specific permission
    p.grant("admin", "documents", "write")
    p.revoke("admin", "documents", "read")


def test_permissions_are_additive() -> None:
    p = Policy()
    p.grant("admin", "documents", "read")
    p.grant("admin", "documents", "write")
    p.grant("admin", "images", "read")

    assert p.can("admin", "documents", "read") is True
    assert p.can("admin", "documents", "write") is True
    assert p.can("admin", "images", "read") is True
    assert p.can("admin", "images", "write") is False


def test_roles_with_access_excludes_revoked() -> None:
    p = Policy()
    p.grant("admin", "files", "delete")
    p.grant("superuser", "files", "delete")
    p.revoke("admin", "files", "delete")

    roles = p.roles_with_access("files", "delete")
    assert "superuser" in roles
    assert "admin" not in roles


def test_multiple_roles_independence() -> None:
    p = Policy()
    p.grant("roleA", "res1", "act1")
    p.grant("roleB", "res2", "act2")

    assert p.can("roleA", "res1", "act1") is True
    assert p.can("roleA", "res2", "act2") is False
    assert p.can("roleB", "res1", "act1") is False
    assert p.can("roleB", "res2", "act2") is True
