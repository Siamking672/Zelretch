# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Tag-all - mention every member of a group. Admins only."""

from __future__ import annotations

from pyZelretch import eod, eor, zelretch_bot, zelretch_cmd


@zelretch_cmd(pattern=r"tagall(?:\s+(.+))?$", admins_only=True, groups_only=True)
async def tag_all(event):
    if zelretch_bot is None:
        return await eod(event, "Bot client not ready.", time=5)
    args = event.matches[0].group(1) if event.matches else ""
    try:
        members = [m async for m in zelretch_bot.get_chat_members(event.chat.id)]
    except Exception as er:
        return await eod(event, f"Could not fetch members: `{er}`", time=10)
    if not members:
        return await eod(event, "No members found.", time=5)
    header = f"**{args or 'Tag all'}**\n\n"
    body = ""
    for m in members[:200]:
        user = m.user
        name = (user.first_name or user.username or "user") if user else "user"
        body += f"[{name}](tg://user?id={user.id if user else 0}) "
    # Split into chunks of 4096 - 200 (header) chars.
    chunk = header + body
    await event.reply(chunk)
    try:
        await event.delete()
    except Exception:
        pass
