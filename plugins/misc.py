# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Misc small commands ported from Ultroid ``plugins/misc.py``.

Provides:
  .whois   - show user info (alias for .info)
  .chatinfo - show chat info
  .stats   - show bot statistics
  .purge   - delete messages in a range (admins only)
"""

from __future__ import annotations

from pyZelretch import eod, eor, zelretch_bot, zelretch_cmd
from pyZelretch.dB._core import ADDONS, LIST, PLUGINS
from pyZelretch.fns.info import display_name


@zelretch_cmd(pattern="whois$")
async def whois(event):
    target = event.reply_to_message.from_user if event.reply_to_message else event.from_user
    if not target:
        return await eod(event, "Reply to a user.", time=5)
    text = (
        f"**Whois**\n\n"
        f"• Name: {display_name(target)}\n"
        f"• ID: `{target.id}`\n"
        f"• Username: @{getattr(target, 'username', 'None')}\n"
        f"• Bot: `{getattr(target, 'is_bot', False)}`\n"
    )
    await eor(event, text)


@zelretch_cmd(pattern="chatinfo$")
async def chatinfo(event):
    chat = event.chat
    if not chat:
        return await eod(event, "No chat context.", time=5)
    text = (
        f"**Chat info**\n\n"
        f"• Title: {getattr(chat, 'title', 'Private')}\n"
        f"• ID: `{chat.id}`\n"
        f"• Type: `{getattr(chat, 'type', 'unknown')}`\n"
        f"• Members: `{getattr(chat, 'members_count', 'unknown')}`\n"
    )
    await eor(event, text)


@zelretch_cmd(pattern="stats$")
async def stats(event):
    text = (
        "**Zelretch stats**\n\n"
        f"• Core plugins: `{len(PLUGINS)}`\n"
        f"• Addons: `{len(ADDONS)}`\n"
        f"• Total commands: `{sum(len(v) for v in LIST.values())}`\n"
    )
    await eor(event, text)


@zelretch_cmd(pattern="purge$", admins_only=True, groups_only=True)
async def purge(event):
    """Delete every message from the replied message up to now."""
    if not event.reply_to_message:
        return await eod(event, "Reply to a message to start purging from.", time=5)
    if zelretch_bot is None:
        return await eod(event, "Bot client not ready.", time=5)
    start_id = event.reply_to_message.id + 1
    end_id = event.id
    deleted = 0
    for msg_id in range(start_id, end_id):
        try:
            await zelretch_bot.delete_messages(event.chat.id, msg_id)
            deleted += 1
        except Exception:
            pass
    await eor(event, f"🗑 Purged `{deleted}` messages.", time=5)
