"""Generate Streamlit OIDC secrets.toml from runtime environment variables."""
from __future__ import annotations

import json
import os
from pathlib import Path


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required OIDC environment variable: {name}")
    return value


def quote(value: str) -> str:
    return json.dumps(value)


def main() -> None:
    enabled = os.getenv("OIDC_ENABLED", "true").strip().lower() == "true"
    if not enabled:
        return

    google_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    google_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    microsoft_id = os.getenv("MICROSOFT_CLIENT_ID", "").strip()
    microsoft_secret = os.getenv("MICROSOFT_CLIENT_SECRET", "").strip()
    microsoft_tenant = os.getenv("MICROSOFT_TENANT_ID", "").strip()

    google_configured = bool(google_id and google_secret)
    microsoft_configured = bool(microsoft_id and microsoft_secret and microsoft_tenant)

    # OIDC remains optional until at least one provider is configured.
    if not google_configured and not microsoft_configured:
        return

    redirect_uri = required("OIDC_REDIRECT_URI")
    cookie_secret = required("OIDC_COOKIE_SECRET")

    lines = [
        "[auth]",
        f"redirect_uri = {quote(redirect_uri)}",
        f"cookie_secret = {quote(cookie_secret)}",
        "",
    ]

    if google_configured:
        lines.extend(
            [
                "[auth.google]",
                f"client_id = {quote(google_id)}",
                f"client_secret = {quote(google_secret)}",
                'server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"',
                "",
            ]
        )

    if microsoft_configured:
        lines.extend(
            [
                "[auth.microsoft]",
                f"client_id = {quote(microsoft_id)}",
                f"client_secret = {quote(microsoft_secret)}",
                f'server_metadata_url = "https://login.microsoftonline.com/{microsoft_tenant}/v2.0/.well-known/openid-configuration"',
                "",
            ]
        )

    target = Path(".streamlit/secrets.toml")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    try:
        target.chmod(0o600)
    except OSError:
        pass


if __name__ == "__main__":
    main()
