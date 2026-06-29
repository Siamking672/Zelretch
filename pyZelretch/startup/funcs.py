# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Miscellaneous startup functions ported from Ultroid's ``startup/funcs.py``.

These helpers run *after* the database is wired but *before* the plugin
loader, so they can mutate configuration or push notifications to the log
channel.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Optional

from ..configs import Var, get_var, set_var

LOGS = logging.getLogger("Zelretch.funcs")


# ---------------------------------------------------------------------------
# Environment <-> DB synchronisation
# ---------------------------------------------------------------------------

def update_envs() -> None:
    """Copy legacy ``.env`` values into the DB on the very first run.

    This is the migration path for users coming from a stock Ultroid install:
    drop their ``.env`` next to ``startup``, run the launcher once, and every
    recognised variable is imported into the DB. After that, the ``.env``
    file is ignored.
    """
    from .. import udB
    if udB is None:
        return
    if udB.get_key("SETUP_COMPLETE"):
        return  # already migrated - env is no longer authoritative

    migrated = []
    for key in ("API_ID", "API_HASH", "BOT_TOKEN", "SESSION",
                "REDIS_URI", "REDIS_PASSWORD", "MONGO_URI", "DATABASE_URL",
                "LOG_CHANNEL", "HEROKU_APP_NAME", "HEROKU_API", "VC_SESSION"):
        env_val = os.environ.get(key) or os.environ.get(f"ZELRETCH_{key}")
        if env_val and not udB.get_key(key):
            udB.set_key(key, env_val)
            migrated.append(key)

    if migrated and "API_ID" in migrated and "SESSION" in migrated:
        LOGS.info(f"Imported {len(migrated)} variables from environment into DB: "
                  f"{', '.join(migrated)}")


# ---------------------------------------------------------------------------
# Auto-discovery of an assistant bot token
# ---------------------------------------------------------------------------

async def autobot() -> None:
    """Auto-create an assistant bot token via @BotFather if missing.

    The original Ultroid asked the user a series of questions through their
    own account and then talked to @BotFather to register a bot. The flow is
    complex and brittle - we keep it stubbed here so plugins can call it
    safely, but the recommended path is to provide ``BOT_TOKEN`` through the
    web setup wizard.
    """
    from .. import udB
    if udB and udB.get_key("BOT_TOKEN"):
        return
    LOGS.info("No BOT_TOKEN configured - dual-mode features will be disabled. "
              "Use the setup wizard to add one.")


async def enable_inline(client: Any, bot_username: Optional[str]) -> None:
    """Best-effort attempt to enable inline mode for the assistant bot.

    Kurigram doesn't expose a direct toggle - the operator needs to flip it
    in @BotFather. We just log a hint.
    """
    if not bot_username:
        return
    LOGS.info(f"Assistant bot is @{bot_username}. Make sure inline mode is "
              "enabled in @BotFather for dual-mode commands to work.")


# ---------------------------------------------------------------------------
# Customisation + readiness notifications
# ---------------------------------------------------------------------------

async def customize() -> None:
    """Apply cosmetic personalisation (kept as a no-op placeholder)."""
    return None


async def ready() -> None:
    """Send a "deployment ready" message to the log channel."""
    from .. import udB, zelretch_bot, asst
    if not (udB and asst):
        return
    log_channel = udB.get_key("LOG_CHANNEL")
    if not log_channel:
        return
    try:
        from ..version import zelretch_version, __version__
        text = (
            "🟢 **Zelretch has been deployed**\n\n"
            f"• **Version:** `{zelretch_version}`\n"
            f"• **Build:** `{__version__}`\n"
            f"• **Handler:** `{udB.get_key('HNDLR') or '.'}`\n"
            f"• **Dual Handler:** `{udB.get_key('DUAL_HNDLR') or '/'}`\n"
            f"• **Database:** `{udB.name}`\n\n"
            "Type `.help` in any chat to see available commands."
        )
        await asst.send_message(log_channel, text)
    except Exception as er:
        LOGS.warning(f"Could not post ready message to log channel: {er}")


# ---------------------------------------------------------------------------
# Restart-tracking (preserved from Ultroid)
# ---------------------------------------------------------------------------

async def WasItRestart(udB: Any) -> None:
    """Edit the 'restarting...' message left by the previous run, if any."""
    if not udB:
        return
    msg_id = udB.get_key("RESTART_MSG")
    chat_id = udB.get_key("RESTART_CHAT")
    if not (msg_id and chat_id):
        return
    from .. import asst
    try:
        if asst:
            await asst.edit_message_text(chat_id, msg_id, "✅ Zelretch restarted successfully.")
    except Exception as er:
        LOGS.info(f"Restart message edit failed: {er}")
    finally:
        udB.del_key("RESTART_MSG")
        udB.del_key("RESTART_CHAT")


# ---------------------------------------------------------------------------
# Misc helpers used by __main__
# ---------------------------------------------------------------------------

async def startup_stuff() -> None:
    """Hook for one-off startup tasks (kept for parity)."""
    return None


async def autopilot() -> None:
    """Auto-create log channel if missing (best-effort)."""
    from .. import udB, zelretch_bot
    if not (udB and zelretch_bot):
        return
    if udB.get_key("LOG_CHANNEL"):
        return
    try:
        # Try to create a private channel and store its ID.
        chat = await zelretch_bot.create_group("Zelretch Logs", "self")
        udB.set_key("LOG_CHANNEL", chat.id)
        LOGS.info(f"Created log channel {chat.id} for Zelretch.")
    except Exception as er:
        LOGS.info(f"Autopilot log-channel creation skipped: {er}")


async def keep_redis_alive() -> None:
    """Background task that pings Redis every 5 minutes to keep it warm."""
    from .. import udB
    if not udB or udB.name != "Redis":
        return
    while True:
        try:
            await asyncio.sleep(300)
            udB.ping()
        except asyncio.CancelledError:
            return
        except Exception as er:
            LOGS.info(f"Redis keep-alive ping failed: {er}")


def cleanup_cache() -> None:
    """Drop stale in-memory caches (called once at startup)."""
    from .. import udB
    if udB and hasattr(udB, "_cache"):
        # Keep the cache - it's only seeded from the DB on demand.
        pass
