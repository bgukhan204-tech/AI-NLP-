"""Optional OpenID Connect / enterprise SSO bridge using Streamlit's OIDC support."""
from __future__ import annotations

from .database import Database
from .rbac import _role_permissions


def session_from_oidc_user(oidc_user: dict) -> dict:
    """Map a verified OIDC identity to an already-provisioned local user.

    The identity provider proves who the user is; PostgreSQL remains the source
    of truth for application roles and permissions.
    """
    username = oidc_user.get("email") or oidc_user.get("preferred_username") or oidc_user.get("sub")
    if not username:
        raise ValueError("OIDC identity has no usable username")

    user = Database().get_user(username)
    if not user or not user["active"]:
        raise ValueError("SSO user is not provisioned for this application")

    role = user["role"]
    return {
        "username": user["username"],
        "role": role,
        "allowed_departments": _role_permissions(role),
    }
