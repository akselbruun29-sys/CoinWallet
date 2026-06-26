"""Startup validation for production secrets."""
from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)

WEAK_SECRETS = {
    "SESSION_SECRET": {"change-me-in-production", "change-this-to-a-random-string"},
    "WALLET_ENCRYPTION_KEY": {
        "change-this-to-a-long-random-secret-key",
        "",
    },
}


def validate_secrets(strict: bool | None = None) -> None:
    if strict is None:
        strict = os.getenv("STRICT_SECRETS", "false").lower() in ("true", "1", "yes")

    issues: list[str] = []
    for key, weak in WEAK_SECRETS.items():
        value = os.getenv(key, "").strip()
        if value in weak or (key == "WALLET_ENCRYPTION_KEY" and len(value) < 32):
            issues.append(f"{key} is missing or too weak")

    if not issues:
        return

    message = "Security configuration: " + "; ".join(issues)
    if strict:
        logger.error(message)
        sys.exit(1)
    logger.warning(message)
