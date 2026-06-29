# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Chat-actions responder (typing / upload photo / ...)."""

from __future__ import annotations

from pyZelretch import zelretch_bot, zelretch_cmd


@zelretch_cmd(pattern="typing$")
async def typing_action(event):
    if zelretch_bot is None:
        return
    try:
        await zelretch_bot.send_chat_action(event.chat.id, "typing")
        await event.reply("...")
    except Exception:
        pass
