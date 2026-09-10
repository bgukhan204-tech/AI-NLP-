import os
import hashlib
import base64
import pytest

from src.database import Database


def make_hash(password: str) -> str:
    salt = b"ci-salt"
    iterations = 310000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    enc = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    return f"pbkdf2_sha256${iterations}${enc(salt)}${enc(digest)}"


@pytest.mark.integration
def test_postgres_user_and_audit_round_trip():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")
    db = Database()
    db.initialize()
    username = "ci_integration_user"
    db.upsert_user(username, make_hash("ci-password"), "employee")
    user = db.get_user(username)
    assert user is not None
    assert user["role"] == "employee"
    db.audit("ci_test", username=username, role="employee", details={"ok": True})
