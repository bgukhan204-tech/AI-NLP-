from pathlib import Path
import yaml

POLICY_PATH = Path(__file__).resolve().parents[1] / "config" / "rbac.yaml"
with POLICY_PATH.open("r", encoding="utf-8") as f:
    POLICY = yaml.safe_load(f)

def authenticate(username: str) -> dict:
    user = POLICY["users"].get(username)
    if not user:
        raise ValueError("Unknown user")
    role = user["role"]
    return {"username": username, "role": role,
            "allowed_departments": POLICY["roles"][role]["allowed_departments"]}

def can_access(metadata: dict, session: dict) -> bool:
    return metadata.get("department", "general") in session["allowed_departments"]
