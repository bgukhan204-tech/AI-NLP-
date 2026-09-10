"""Create/update a PostgreSQL application user without storing plaintext passwords."""
from getpass import getpass
from pathlib import Path
import base64
import hashlib
import secrets
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.database import Database


def password_hash(password: str, iterations: int = 310000) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    enc = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    return f"pbkdf2_sha256${iterations}${enc(salt)}${enc(digest)}"


def main() -> None:
    username = input("Username: ").strip()
    role = input("Role: ").strip()
    password = getpass("Password: ")
    confirm = getpass("Confirm password: ")
    if not username or not password or password != confirm:
        raise SystemExit("Invalid username or passwords do not match.")

    policy = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "rbac.yaml").read_text())
    if role not in policy["roles"]:
        raise SystemExit(f"Unknown role. Choose one of: {', '.join(policy['roles'])}")

    db = Database()
    db.initialize()
    db.upsert_user(username, password_hash(password), role)
    print(f"User '{username}' provisioned with role '{role}'.")


if __name__ == "__main__":
    main()
