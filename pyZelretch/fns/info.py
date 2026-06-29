# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Info helpers (chat / user / file metadata extraction)."""

from __future__ import annotations

from typing import Any, Optional


def display_name(entity: Any) -> str:
    if not entity:
        return "Unknown"
    first = getattr(entity, "first_name", "") or ""
    last = getattr(entity, "last_name", "") or ""
    title = getattr(entity, "title", "") or ""
    username = getattr(entity, "username", "") or ""
    if first or last:
        return f"{first} {last}".strip()
    if title:
        return title
    if username:
        return f"@{username}"
    return "Unknown"


def user_mention(user: Any) -> str:
    name = display_name(user)
    uid = getattr(user, "id", 0)
    return f"[{name}](tg://user?id={uid})"


def chat_link(chat: Any) -> str:
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}"
    return f"tg://chat?id={getattr(chat, 'id', 0)}"
