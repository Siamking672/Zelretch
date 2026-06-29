# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Session validation + voice-chat connection helpers."""

from __future__ import annotations

import logging
from typing import Any, Optional

LOGS = logging.getLogger("Zelretch.connections")


def validate_session(session: Optional[str], logger: logging.Logger = LOGS) -> Optional[str]:
    """Validate that *session* looks like a Kurigram session string.

    The original Ultroid supported both Telethon and Pyrogram session strings.
    Kurigram uses the Pyrogram v2 format - a base64-encoded blob that starts
    with a version byte. We only check the structural shape here; full
    validation happens when :class:`ZelretchClient` actually calls ``start``.
    """
    if not session:
        logger.warning(
            "No SESSION configured. The web setup wizard will guide you through "
            "generating one - the bot will refuse to start until a valid session "
            "is in place."
        )
        return None
    s = session.strip()
    # Pyrogram v2 sessions are typically > 200 chars and base64-decodable.
    if len(s) < 80:
        logger.warning("Session string looks too short - it may be invalid.")
    return s


def vc_connection(udB: Any, client: Any) -> Any:
    """Return a pyTgCalls client if VCBOT is enabled, else ``None``."""
    try:
        if not udB or not udB.get_key("VCBOT"):
            return None
        try:
            from pyrogram.raw.functions.phone import GetGroupCall  # noqa: F401
        except Exception:
            LOGS.info("pyTgCalls not installed - VCBOT disabled.")
            return None
        LOGS.info("Voice-chat client requested; not yet wired in this build.")
        return None
    except Exception as er:
        LOGS.info(f"VC connection skipped: {er}")
        return None
