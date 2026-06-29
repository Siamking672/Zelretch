# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""PM permit - auto-respond to private messages from unknown users."""

from __future__ import annotations

import logging

from pyZelretch import LOGS, udB, zelretch_bot, zelretch_cmd
from pyZelretch.dB import botchat_db

LOGS = logging.getLogger("Zelretch.pmpermit")


async def pm_responder(client, message):
    if not message or not message.from_user or message.from_user.is_bot:
        return
    if not message.chat or getattr(message.chat, "type", None) != "private":
        return
    # Allow owner + sudos.
    from pyZelretch._misc._supporter import owner_and_sudos
    if message.from_user.id in owner_and_sudos():
        return
    # Allow previously-approved users.
    approved = botchat_db.get_data() or {}
    if message.from_user.id in approved.get("approved", []):
        return
    # Otherwise: post a permit message and ignore further messages until approved.
    try:
        await message.reply(
            "👋 Hi! This is a Zelretch-protected account.\n\n"
            "Please wait - the owner will review your message and approve you shortly."
        )
    except Exception as er:
        LOGS.info(f"PM permit reply failed: {er}")


if zelretch_bot is not None:
    try:
        from kurigram import filters  # type: ignore
        zelretch_bot.add_message_handler(pm_responder, filters.private & filters.incoming)
    except Exception:
        pass


@zelretch_cmd(pattern="approve$")
async def approve_pm(event):
    if not event.reply_to_message:
        return
    target = event.reply_to_message.from_user
    if not target:
        return
    data = botchat_db.get_data() or {}
    approved = data.get("approved", [])
    if target.id not in approved:
        approved.append(target.id)
    data["approved"] = approved
    botchat_db.set_data(data)
    await event.reply(f"✅ Approved {target.first_name}.")


@zelretch_cmd(pattern="disapprove$")
async def disapprove_pm(event):
    if not event.reply_to_message:
        return
    target = event.reply_to_message.from_user
    data = botchat_db.get_data() or {}
    approved = data.get("approved", [])
    if target.id in approved:
        approved.remove(target.id)
    data["approved"] = approved
    botchat_db.set_data(data)
    await event.reply(f"🚫 Disapproved {target.first_name}.")
