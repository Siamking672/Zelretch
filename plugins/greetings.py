# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Greetings - welcome / goodbye messages for new chat members."""

from __future__ import annotations

from pyZelretch import LOGS, eor, udB, zelretch_bot, zelretch_cmd
from pyZelretch.dB import greetings_db
from pyZelretch.fns.info import display_name


@zelretch_cmd(pattern=r"welcome(?:\s+(.+))?$", admins_only=True, groups_only=True)
async def set_welcome(event):
    text = event.matches[0].group(1) if event.matches else None
    if not text:
        return greetings_db.del_item("welcome") or await eor(event, "Welcome message cleared.")
    greetings_db.add_item("welcome", text)
    await eor(event, f"👋 Welcome message set to:\n\n{text}")


@zelretch_cmd(pattern=r"goodbye(?:\s+(.+))?$", admins_only=True, groups_only=True)
async def set_goodbye(event):
    text = event.matches[0].group(1) if event.matches else None
    if not text:
        greetings_db.del_item("goodbye")
        return await eor(event, "Goodbye message cleared.")
    greetings_db.add_item("goodbye", text)
    await eor(event, f"👋 Goodbye message set to:\n\n{text}")


async def greetings_responder(client, message):
    new_members = getattr(message, "new_chat_members", None)
    left_member = getattr(message, "left_chat_member", None)
    data = greetings_db.get_data() or {}
    if new_members:
        tmpl = data.get("welcome")
        if not tmpl:
            return
        names = ", ".join(display_name(u) for u in new_members)
        await message.reply(tmpl.replace("{name}", names).replace("{chat}", message.chat.title or "the group"))
    elif left_member:
        tmpl = data.get("goodbye")
        if not tmpl:
            return
        await message.reply(tmpl.replace("{name}", display_name(left_member)))


if zelretch_bot is not None:
    try:
        from kurigram import filters  # type: ignore
        zelretch_bot.add_message_handler(greetings_responder,
                                         filters.new_chat_members | filters.left_chat_member)
    except Exception as er:
        LOGS.info(f"Greetings handler not attached: {er}")
