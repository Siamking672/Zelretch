# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Input validators for the setup wizard.

Every validator returns ``(ok: bool, message: str)``. The web layer uses the
message to render inline errors next to the relevant field.

Sensitive values are validated structurally only - we never make a network
call that would expose the secret in logs.
"""

from __future__ import annotations

import re
from typing import Tuple

# Telegram API ID is a positive integer, typically 5-9 digits.
_API_ID_RE = re.compile(r"^\d{4,12}$")
# API HASH is a 32-char hex string.
_API_HASH_RE = re.compile(r"^[0-9a-fA-F]{32}$")
# Bot token: "<bot_id>:<35-char-token>"
_BOT_TOKEN_RE = re.compile(r"^\d{6,12}:[A-Za-z0-9_-]{30,}$")
# MongoDB URI: scheme://...
_MONGO_RE = re.compile(r"^mongodb(?:\+srv)?://.+", re.IGNORECASE)
# Postgres URL: postgres:// or postgresql://
_POSTGRES_RE = re.compile(r"^postgres(?:ql)?://.+", re.IGNORECASE)
# Redis URI: host:port (no scheme).
_REDIS_RE = re.compile(r"^[\w.-]+:\d{2,5}$")
# Telegram user IDs are positive integers up to ~10 digits.
_TG_ID_RE = re.compile(r"^-?\d{4,15}$")
# Kurigram (Pyrogram v2) session strings are long base64-ish blobs.
_SESSION_MIN_LEN = 80


def _ok() -> Tuple[bool, str]:
    return True, ""


def _err(msg: str) -> Tuple[bool, str]:
    return False, msg


def validate_api_id(value: str) -> Tuple[bool, str]:
    if not value:
        return _err("API ID is required.")
    if not _API_ID_RE.match(str(value).strip()):
        return _err("API ID must be a 4-12 digit number from my.telegram.org.")
    return _ok()


def validate_api_hash(value: str) -> Tuple[bool, str]:
    if not value:
        return _err("API Hash is required.")
    if not _API_HASH_RE.match(str(value).strip()):
        return _err("API Hash must be a 32-character hex string.")
    return _ok()


def validate_bot_token(value: str) -> Tuple[bool, str]:
    if not value:
        return _ok()  # optional
    if not _BOT_TOKEN_RE.match(str(value).strip()):
        return _err("Bot token should look like 123456:ABC-DEF...")
    return _ok()


def validate_owner_id(value: str) -> Tuple[bool, str]:
    if not value:
        return _ok()  # auto-filled on login
    if not _TG_ID_RE.match(str(value).strip()):
        return _err("Telegram IDs are numeric (use @userinfobot to find yours).")
    return _ok()


def validate_database_type(value: str) -> Tuple[bool, str]:
    if value not in {"local", "mongo", "redis", "sql"}:
        return _err("Pick one of: local, mongo, redis, sql.")
    return _ok()


def validate_mongo_uri(value: str) -> Tuple[bool, str]:
    if not value:
        return _err("MongoDB URI is required when DATABASE_TYPE=mongo.")
    if not _MONGO_RE.match(str(value).strip()):
        return _err("MongoDB URI should start with mongodb:// or mongodb+srv://")
    return _ok()


def validate_redis_uri(value: str) -> Tuple[bool, str]:
    if not value:
        return _err("Redis URI is required when DATABASE_TYPE=redis.")
    if not _REDIS_RE.match(str(value).strip()):
        return _err("Redis URI should look like host:port (no scheme).")
    return _ok()


def validate_redis_password(value: str) -> Tuple[bool, str]:
    if not value:
        return _ok()  # some Redis instances have no password
    return _ok()


def validate_database_url(value: str) -> Tuple[bool, str]:
    if not value:
        return _err("PostgreSQL URL is required when DATABASE_TYPE=sql.")
    if not _POSTGRES_RE.match(str(value).strip()):
        return _err("PostgreSQL URL should start with postgres:// or postgresql://")
    return _ok()


def validate_session(value: str) -> Tuple[bool, str]:
    if not value:
        return _err("Session string is required. Use the in-wizard generator or sessiongen.")
    if len(str(value).strip()) < _SESSION_MIN_LEN:
        return _err("Session string looks too short - it may be truncated.")
    return _ok()


def validate_handler(value: str) -> Tuple[bool, str]:
    if not value:
        return _err("Handler is required.")
    if len(value) > 4:
        return _err("Handler should be 1-4 characters (e.g. '.' or '!').")
    return _ok()


def validate_log_channel(value: str) -> Tuple[bool, str]:
    if not value:
        return _ok()  # optional - autopilot creates one
    if not _TG_ID_RE.match(str(value).strip()):
        return _err("Log channel must be a numeric chat ID (use -100...).")
    return _ok()


def validate_port(value) -> Tuple[bool, str]:
    try:
        p = int(value)
    except (TypeError, ValueError):
        return _err("Port must be an integer.")
    if not (1 <= p <= 65535):
        return _err("Port must be between 1 and 65535.")
    return _ok()


def validate_field(key: str, value: str) -> Tuple[bool, str]:
    """Dispatch on schema key."""
    dispatch = {
        "API_ID": validate_api_id,
        "API_HASH": validate_api_hash,
        "BOT_TOKEN": validate_bot_token,
        "OWNER_ID": validate_owner_id,
        "DATABASE_TYPE": validate_database_type,
        "MONGO_URI": validate_mongo_uri,
        "REDIS_URI": validate_redis_uri,
        "REDIS_PASSWORD": validate_redis_password,
        "DATABASE_URL": validate_database_url,
        "SESSION": validate_session,
        "HNDLR": validate_handler,
        "LOG_CHANNEL": validate_log_channel,
        "PORT": validate_port,
    }
    fn = dispatch.get(key)
    if not fn:
        return _ok()
    return fn(value)


def validate_payload(payload: dict) -> dict:
    """Validate a whole wizard step. Returns ``{key: error_message}`` (empty if ok)."""
    errors: dict = {}
    for key, value in payload.items():
        ok, msg = validate_field(key, value)
        if not ok:
            errors[key] = msg
    return errors
