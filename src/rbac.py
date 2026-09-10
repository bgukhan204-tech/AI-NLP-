from pathlib import Path
import yaml

from .database import Database

POLICY_PATH = Path(__file__).resolve().parents[1] / "config" / "rbac.yaml"
with POLICY_PATH.open("r", encoding="utf-8") as f:
    POLICY = yaml.safe_load(f)


def _role_permissions(role: str) -> list[str]:
    try:
        return POLICY["roles"][role]["allowed_departments"]
    except KeyError as exc:
        raise ValueError("Unknown role") from exc


def authenticate(username: str, password: str) -> dict:
    from .auth import verify_password

    user = Database().get_user(username)
    if not user or not user["active"] or not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid username or password")
    role = user["role"]
    return {"username": username, "role": role, "allowed_departments": _role_permissions(role)}


def session_from_claims(claims: dict) -> dict:
    username = claims.get("sub")
    role = claims.get("role")
    if not username or not role:
        raise ValueError("Invalid authentication claims")
    allowed = _role_permissions(role)
    if claims.get("allowed_departments") != allowed:
        raise ValueError("Authentication claims are stale or invalid")
    user = Database().get_user(username)
    if not user or not user["active"] or user["role"] != role:
        raise ValueError("Invalid authentication claims")
    return {"username": username, "role": role, "allowed_departments": allowed}


def can_access(metadata: dict, session: dict) -> bool:
    return metadata.get("department", "general") in session["allowed_departments"]
