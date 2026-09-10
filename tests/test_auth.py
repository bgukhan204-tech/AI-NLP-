import base64
import hashlib
import os

from src.auth import decode_token, issue_token, verify_password


def make_hash(password: str) -> str:
    salt = b"test-salt"
    iterations = 310000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    enc = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    return f"pbkdf2_sha256${iterations}${enc(salt)}${enc(digest)}"


def test_password_verification():
    encoded = make_hash("correct-password")
    assert verify_password("correct-password", encoded)
    assert not verify_password("wrong-password", encoded)


def test_jwt_round_trip():
    session = {"username": "alice", "role": "employee", "allowed_departments": ["general"]}
    token = issue_token(session)
    claims = decode_token(token)
    assert claims["sub"] == "alice"
    assert claims["role"] == "employee"
    assert claims["allowed_departments"] == ["general"]
