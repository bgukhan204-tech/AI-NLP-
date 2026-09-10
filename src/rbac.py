from pathlib import Path
import yaml

POLICY_PATH = Path(__file__).resolve().parents[1] / "config" / "rbac.yaml"
with POLICY_PATH.open("r", encoding="utf-8") as f:
    POLICY = yaml.safe_load(f)


def authenticate(username: str, password: str) -> dict:
    from .auth import verify_password

    user = POLICY["users"].get(username)
    if not user or not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid username or password")

    role = user["role"]
    return {
        "username": username,
        "role": role,
        "allowed_departments": POLICY["roles"][role]["allowed_departments"],
    }


def session_from_claims(claims: dict) -> dict:
    username = claims.get("sub")
    user = POLICY["users"].get(username)
    if not user or user["role"] != claims.get("role"):
        raise ValueError("Invalid authentication claims")
    allowed = POLICY["roles"][user["role"]]["allowed_departments"]
    if claims.get("allowed_departments") != allowed:
        raise ValueError("Authentication claims are stale or invalid")
    return {"username": username, "role": user["role"], "allowed_departments": allowed}


def can_access(metadata: dict, session: dict) -> bool:
    return metadata.get("department", "general") in session["allowed_departments"]
