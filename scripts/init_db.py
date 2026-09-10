"""Create production tables and optionally seed users from config/rbac.yaml.

For production, set DATABASE_URL and run this once. The YAML seed is intended
only for first-time migration; afterwards manage users in PostgreSQL.
"""
from pathlib import Path
import sys
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.database import Database


def main() -> None:
    db = Database()
    db.initialize()
    policy_path = Path(__file__).resolve().parents[1] / "config" / "rbac.yaml"
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    for username, user in policy.get("users", {}).items():
        db.upsert_user(username, user["password_hash"], user["role"])
    print("PostgreSQL schema initialized and configured users migrated.")


if __name__ == "__main__":
    main()
