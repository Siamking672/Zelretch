# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Zelretch configuration manager.

Unlike the original Ultroid, which read every runtime value from OS environment
variables via ``python-decouple``, Zelretch stores its configuration inside the
database that the user picks during the web setup wizard. The environment is
only consulted as a *fallback* (so legacy deployments still work) and for a
handful of bootstrap keys (``PORT``, ``HOST``) that the wizard itself needs
before any database has been chosen.

Public API
----------
``Var``
    A lazily-evaluated proxy that always reflects the *current* value of a
    configuration key. Reads go through the runtime config cache; writes are
    routed through :func:`set_var` so that callers cannot accidentally bypass
    the database.

``get_var(key, default=None, cast=None)``
    Pull a single config value.

``set_var(key, value)``
    Persist a config value (also updates the in-memory cache).

``del_var(key)``
    Remove a config value.

``all_vars()``
    Return a snapshot dict of every known config key.

``CONFIG_SCHEMA``
    A declarative description of every variable the bot understands. The web
    setup wizard iterates over this to build its forms, and the validators use
    it to enforce types and presence.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, List, Optional

# ``decouple`` is kept as an optional dependency so that legacy users with an
# existing ``.env`` can still bootstrap the very first run. After the wizard
# has written its first snapshot to the database, the env file is ignored.
try:
    from decouple import config as _decouple_config  # type: ignore
except Exception:  # pragma: no cover - decouple is optional
    _decouple_config = None

try:
    from dotenv import load_dotenv as _load_dotenv  # type: ignore
    _load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass


# ---------------------------------------------------------------------------
# Configuration schema
# ---------------------------------------------------------------------------
#
# Each entry declares:
#   key         - canonical name (also used as DB key)
#   label       - human-readable label shown in the wizard
#   category    - grouping in the wizard UI ("core", "database", "session",
#                 "runtime", "deployment", "advanced")
#   required    - whether the wizard blocks Deploy without a value
#   secret      - whether the value is masked in the UI and never logged
#   default     - default value if unset (None == no default)
#   cast        - one of "int", "bool", "str"
#   help        - short help string shown next to the field
#   choices     - optional list of allowed values (renders as a <select>)
#   placeholder - placeholder text for the input
# ---------------------------------------------------------------------------

CONFIG_SCHEMA: List[Dict[str, Any]] = [
    # --- core Telegram credentials ----------------------------------------
    {
        "key": "API_ID",
        "label": "Telegram API ID",
        "category": "core",
        "required": True,
        "secret": False,
        "default": None,
        "cast": "int",
        "help": "From https://my.telegram.org → API development tools.",
        "placeholder": "1234567",
    },
    {
        "key": "API_HASH",
        "label": "Telegram API Hash",
        "category": "core",
        "required": True,
        "secret": True,
        "default": None,
        "cast": "str",
        "help": "From https://my.telegram.org → API development tools.",
        "placeholder": "abcdef0123456789abcdef0123456789",
    },
    {
        "key": "BOT_TOKEN",
        "label": "Assistant Bot Token (optional)",
        "category": "core",
        "required": False,
        "secret": True,
        "default": None,
        "cast": "str",
        "help": "Create a bot via @BotFather to enable dual-mode (bot + userbot).",
        "placeholder": "123456:ABC-DEF...",
    },
    {
        "key": "OWNER_ID",
        "label": "Owner Telegram User ID",
        "category": "core",
        "required": False,
        "secret": False,
        "default": None,
        "cast": "int",
        "help": "Auto-filled on first successful login if left blank.",
        "placeholder": "123456789",
    },
    # --- database ----------------------------------------------------------
    {
        "key": "DATABASE_TYPE",
        "label": "Database Backend",
        "category": "database",
        "required": True,
        "secret": False,
        "default": "local",
        "cast": "str",
        "help": "Pick the database that will persist Zelretch configuration, plugin "
                "data and runtime preferences.",
        "choices": ["local", "mongo", "redis", "sql"],
    },
    {
        "key": "MONGO_URI",
        "label": "MongoDB Connection URI",
        "category": "database",
        "required": False,
        "secret": True,
        "default": None,
        "cast": "str",
        "help": "Required when Database Backend = mongo. Get it from "
                "https://mongodb.com/atlas.",
        "placeholder": "mongodb+srv://user:pass@cluster0.mongodb.net",
    },
    {
        "key": "REDIS_URI",
        "label": "Redis URI (host:port)",
        "category": "database",
        "required": False,
        "secret": False,
        "default": None,
        "cast": "str",
        "help": "Required when Database Backend = redis. e.g. redis-12345.c1.us-east-1.example.cloud.redislabs.com:12345",
        "placeholder": "host:port",
    },
    {
        "key": "REDIS_PASSWORD",
        "label": "Redis Password",
        "category": "database",
        "required": False,
        "secret": True,
        "default": None,
        "cast": "str",
        "help": "Required when Database Backend = redis.",
    },
    {
        "key": "DATABASE_URL",
        "label": "PostgreSQL URL",
        "category": "database",
        "required": False,
        "secret": True,
        "default": None,
        "cast": "str",
        "help": "Required when Database Backend = sql. Get it from "
                "https://elephantsql.com or any Postgres provider.",
        "placeholder": "postgres://user:pass@host:5432/dbname",
    },
    # --- session -----------------------------------------------------------
    {
        "key": "SESSION",
        "label": "Kurigram Session String",
        "category": "session",
        "required": True,
        "secret": True,
        "default": None,
        "cast": "str",
        "help": "Generate one with the bundled `sessiongen` script or via the "
                "in-wizard generator. This is the most sensitive credential in "
                "the deployment - treat it like a password.",
        "placeholder": "ZQAAAAA...long-string...==",
    },
    {
        "key": "VC_SESSION",
        "label": "Voice-Chat Session String (optional)",
        "category": "session",
        "required": False,
        "secret": True,
        "default": None,
        "cast": "str",
        "help": "Separate session for the voice-chat music bot. Leave empty to "
                "reuse the main session.",
    },
    # --- runtime preferences ----------------------------------------------
    {
        "key": "HNDLR",
        "label": "Command Handler (prefix)",
        "category": "runtime",
        "required": False,
        "secret": False,
        "default": ".",
        "cast": "str",
        "help": "Single character used to trigger userbot commands.",
        "placeholder": ".",
    },
    {
        "key": "DUAL_HNDLR",
        "label": "Assistant Bot Command Handler",
        "category": "runtime",
        "required": False,
        "secret": False,
        "default": "/",
        "cast": "str",
        "help": "Prefix for commands handled by the assistant bot (dual mode).",
        "placeholder": "/",
    },
    {
        "key": "LOG_CHANNEL",
        "label": "Log Channel ID (-100...)",
        "category": "runtime",
        "required": False,
        "secret": False,
        "default": 0,
        "cast": "int",
        "help": "Private channel where Zelretch posts errors, crash logs and "
                "deployment notifications.",
        "placeholder": "-1001234567890",
    },
    {
        "key": "LANGUAGE",
        "label": "Interface Language",
        "category": "runtime",
        "required": False,
        "secret": False,
        "default": "en",
        "cast": "str",
        "help": "ISO 639-1 code for the bot's reply strings.",
        "choices": ["en"],
    },
    {
        "key": "ADDONS",
        "label": "Load Addons Repository",
        "category": "runtime",
        "required": False,
        "secret": False,
        "default": True,
        "cast": "bool",
        "help": "When true, Zelretch will load plugins from the `addons/` folder "
                "next to the main project (or from a configured plugin channel).",
    },
    {
        "key": "VCBOT",
        "label": "Enable Voice-Chat Music Bot",
        "category": "runtime",
        "required": False,
        "secret": False,
        "default": False,
        "cast": "bool",
        "help": "Requires pyTgCalls. Disable on hosts that do not support voice "
                "calls (e.g. Hugging Face Spaces).",
    },
    {
        "key": "BOTMODE",
        "label": "Run as Bot Only (no userbot)",
        "category": "runtime",
        "required": False,
        "secret": False,
        "default": False,
        "cast": "bool",
        "help": "When true, Zelretch operates as a regular bot without the "
                "user-account client. Requires BOT_TOKEN.",
    },
    {
        "key": "DUAL_MODE",
        "label": "Dual Mode (userbot + assistant)",
        "category": "runtime",
        "required": False,
        "secret": False,
        "default": False,
        "cast": "bool",
        "help": "Mirror userbot commands through the assistant bot so they can "
                "be invoked from chats where the user account is not present.",
    },
    # --- deployment --------------------------------------------------------
    {
        "key": "HOSTED_ON",
        "label": "Hosting Platform",
        "category": "deployment",
        "required": False,
        "secret": False,
        "default": "local",
        "cast": "str",
        "help": "Used for telemetry and platform-specific behaviour.",
        "choices": ["local", "heroku", "okteto", "huggingface", "termux", "docker"],
    },
    {
        "key": "HEROKU_APP_NAME",
        "label": "Heroku App Name (optional)",
        "category": "deployment",
        "required": False,
        "secret": False,
        "default": None,
        "cast": "str",
    },
    {
        "key": "HEROKU_API",
        "label": "Heroku API Key (optional)",
        "category": "deployment",
        "required": False,
        "secret": True,
        "default": None,
        "cast": "str",
    },
    # --- web setup wizard bootstrap --------------------------------------
    {
        "key": "PORT",
        "label": "Web Setup Wizard Port",
        "category": "advanced",
        "required": False,
        "secret": False,
        "default": 7860,
        "cast": "int",
        "help": "Port the setup wizard listens on. Defaults to 7860 to match "
                "Hugging Face Spaces.",
    },
    {
        "key": "HOST",
        "label": "Web Setup Wizard Host",
        "category": "advanced",
        "required": False,
        "secret": False,
        "default": "0.0.0.0",
        "cast": "str",
        "help": "Bind address for the setup wizard. Use 0.0.0.0 on containers "
                "and Hugging Face Spaces; use 127.0.0.1 for local-only access.",
    },
    {
        "key": "SETUP_COMPLETE",
        "label": "Setup Wizard Completed",
        "category": "advanced",
        "required": False,
        "secret": False,
        "default": False,
        "cast": "bool",
        "help": "Internal flag - flipped to True after the user clicks Deploy. "
                "When False, the launcher only runs the web wizard and refuses "
                "to start the bot.",
    },
]


# Index for O(1) lookup by key.
_SCHEMA_BY_KEY: Dict[str, Dict[str, Any]] = {item["key"]: item for item in CONFIG_SCHEMA}


# ---------------------------------------------------------------------------
# Bootstrap loader
# ---------------------------------------------------------------------------
#
# Order of precedence for the *initial* read (before the wizard has written
# anything to the DB):
#
#   1. ``ZELRETCH_*`` environment variables (set by ``startup`` / Docker /
#      HF Spaces secrets). Example: ``ZELRETCH_API_ID=12345``.
#   2. Bare environment variables (``API_ID`` etc.) - kept for legacy Ultroid
#      compatibility.
#   3. ``.env`` file via python-decouple, if installed.
#   4. ``default`` from the schema.
#
# After the wizard has flipped ``SETUP_COMPLETE`` to True, environment
# variables are only consulted for the four bootstrap keys
# (``PORT``, ``HOST``, ``HOSTED_ON``, ``DATABASE_TYPE``) that the wizard
# itself needs to find the right DB before the rest can be loaded.

_BOOTSTRAP_KEYS = {"PORT", "HOST", "HOSTED_ON", "DATABASE_TYPE"}


def _env_lookup(key: str) -> Optional[str]:
    """Return the raw string value for *key* from the environment, if any."""
    val = os.environ.get(f"ZELRETCH_{key}")
    if val is not None:
        return val
    val = os.environ.get(key)
    if val is not None:
        return val
    if _decouple_config is not None:
        try:
            return _decouple_config(key, default=None)
        except Exception:
            return None
    return None


def _cast(value: Any, cast: str) -> Any:
    """Apply the declared type cast."""
    if value is None:
        return None
    if cast == "int":
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None
    if cast == "bool":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on", "y"}
    return str(value)


# ---------------------------------------------------------------------------
# Runtime cache + DB bridge
# ---------------------------------------------------------------------------
#
# The DB bridge is wired in lazily by ``pyZelretch.startup._database`` once it
# knows which backend the user picked. Before that, the cache is seeded from
# the environment so the wizard can render its very first page.

_cache: Dict[str, Any] = {}
_db_bridge = None  # populated by _database.py via ``_install_db_bridge``


def _install_db_bridge(bridge) -> None:
    """Hook used by ``pyZelretch.startup._database`` to attach a real backend."""
    global _db_bridge
    _db_bridge = bridge
    # Warm the cache with everything currently in the DB.
    if _db_bridge is not None:
        for key in _SCHEMA_BY_KEY:
            _cache[key] = _db_bridge.get_key(key)


def _read(key: str) -> Any:
    """Read a config key, preferring DB over env, falling back to default.

    Bootstrap keys (PORT, HOST, HOSTED_ON, DATABASE_TYPE) are *always* read
    from the environment first - they are needed before the DB is even
    selected.
    """
    if key in _cache and key not in _BOOTSTRAP_KEYS:
        return _cache[key]
    schema = _SCHEMA_BY_KEY.get(key, {})
    cast = schema.get("cast", "str")
    default = schema.get("default")
    # Env takes precedence for bootstrap keys; otherwise DB first.
    if key in _BOOTSTRAP_KEYS:
        raw = _env_lookup(key)
        if raw is not None:
            _cache[key] = _cast(raw, cast)
            return _cache[key]
    if _db_bridge is not None:
        raw = _db_bridge.get_key(key)
        if raw is not None:
            _cache[key] = _cast(raw, cast)
            return _cache[key]
    # Env fallback for non-bootstrap keys.
    if _db_bridge is None:
        raw = _env_lookup(key)
        if raw is not None:
            _cache[key] = _cast(raw, cast)
            return _cache[key]
    _cache[key] = default
    return default


def _write(key: str, value: Any) -> None:
    """Persist a config key to DB + cache."""
    _cache[key] = value
    if _db_bridge is not None:
        _db_bridge.set_key(key, value)


def _delete(key: str) -> None:
    _cache.pop(key, None)
    if _db_bridge is not None:
        _db_bridge.del_key(key)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_var(key: str, default: Any = None, cast: Optional[str] = None) -> Any:
    """Return the current value of *key*.

    If *key* is not in the schema, returns *default* (env lookup still
    attempted for ad-hoc keys used by plugins).
    """
    if key not in _SCHEMA_BY_KEY:
        # Ad-hoc plugin key - check in-process cache first, then DB, then env.
        if key in _cache:
            return _cache[key]
        if _db_bridge is not None:
            v = _db_bridge.get_key(key)
            if v is not None:
                return v
        v = _env_lookup(key)
        return v if v is not None else default
    schema = _SCHEMA_BY_KEY[key]
    value = _read(key)
    if value is None:
        return default
    if cast is not None:
        return _cast(value, cast)
    return value


def set_var(key: str, value: Any) -> None:
    """Persist *value* under *key* in both the cache and the DB."""
    schema = _SCHEMA_BY_KEY.get(key)
    if schema is not None:
        value = _cast(value, schema.get("cast", "str"))
    _write(key, value)


def del_var(key: str) -> None:
    """Remove *key* from both the cache and the DB."""
    _delete(key)


def all_vars() -> Dict[str, Any]:
    """Return a snapshot dict of every schema-declared config key."""
    return {item["key"]: _read(item["key"]) for item in CONFIG_SCHEMA}


def schema_for(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return schema entries, optionally filtered by *category*."""
    if category is None:
        return list(CONFIG_SCHEMA)
    return [item for item in CONFIG_SCHEMA if item["category"] == category]


def is_setup_complete() -> bool:
    """True when the wizard has flipped ``SETUP_COMPLETE``."""
    return bool(_read("SETUP_COMPLETE"))


def reset_setup_state() -> None:
    """Force the wizard to run again on next launch."""
    _write("SETUP_COMPLETE", False)


class _VarProxy:
    """Lazy attribute-style accessor mirroring the original ``Var`` class.

    Example: ``Var.API_ID`` resolves to ``get_var("API_ID")`` at call time.
    """

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return get_var(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            set_var(name, value)

    def __contains__(self, key: str) -> bool:
        return key in _SCHEMA_BY_KEY


Var = _VarProxy()
