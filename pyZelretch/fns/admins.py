# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Admin-checking helper, ported from ``pyUltroid.fns.admins``."""

from __future__ import annotations

from typing import Any, Optional


async def admin_check(event, require: Optional[str] = None) -> bool:
    """Return True if the message sender is an admin in the current chat.

    The *require* argument (one of ``"ban"``, ``"delete"``, ``"pin"``...) is
    accepted for parity with the original Ultroid signature but not enforced
    in this minimal build.
    """
    if not event or not hasattr(event, "chat") or not hasattr(event, "from_user"):
        return False
    chat = event.chat
    if not chat:
        return False
    # Private chats: everyone is "admin" of their own chat.
    if getattr(chat, "type", None) == "private":
        return True
    try:
        member = await event.chat.get_member(event.from_user.id)
        return member.status in ("administrator", "owner", "creator")
    except Exception:
        return False
