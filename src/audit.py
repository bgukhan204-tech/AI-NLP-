"""Best-effort centralized audit logging."""
from __future__ import annotations

import logging
import os
import uuid

from .database import Database

logger = logging.getLogger(__name__)


def audit_event(
    event_type: str,
    *,
    username: str | None = None,
    role: str | None = None,
    details: dict | None = None,
) -> str:
    request_id = str(uuid.uuid4())
    if os.getenv("AUDIT_LOGGING", "true").lower() == "true":
        try:
            Database().audit(event_type, username, role, request_id, details)
        except Exception:
            # Never expose database/audit failures to the end user.
            logger.exception("Audit write failed: %s", event_type)
    logger.info("audit event=%s request_id=%s user=%s", event_type, request_id, username)
    return request_id
