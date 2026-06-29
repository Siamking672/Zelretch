# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Admin tools - kick / ban / mute / unmute / pin / promote / demote."""

from __future__ import annotations

from pyZelretch import eod, eor, zelretch_bot, zelretch_cmd


def _target_user(event):
    if event.reply_to_message and event.reply_to_message.from_user:
        return event.reply_to_message.from_user
    return None


@zelretch_cmd(pattern=r"kick(?:\s+(\d+))?$", admins_only=True, groups_only=True)
async def kick(event):
    if zelretch_bot is None:
        return
    target = _target_user(event)
    if not target:
        return await eod(event, "Reply to the user you want to kick.", time=5)
    try:
        await zelretch_bot.ban_chat_member(event.chat.id, target.id)
        await zelretch_bot.unban_chat_member(event.chat.id, target.id)
        await eor(event, f"👢 Kicked {target.first_name}.")
    except Exception as er:
        await eod(event, f"Could not kick: `{er}`", time=10)


@zelretch_cmd(pattern=r"ban(?:\s+(\d+))?$", admins_only=True, groups_only=True)
async def ban(event):
    if zelretch_bot is None:
        return
    target = _target_user(event)
    if not target:
        return await eod(event, "Reply to the user you want to ban.", time=5)
    try:
        await zelretch_bot.ban_chat_member(event.chat.id, target.id)
        await eor(event, f"🚫 Banned {target.first_name}.")
    except Exception as er:
        await eod(event, f"Could not ban: `{er}`", time=10)


@zelretch_cmd(pattern=r"unban(?:\s+(\d+))?$", admins_only=True, groups_only=True)
async def unban(event):
    if zelretch_bot is None:
        return
    target = _target_user(event)
    if not target:
        return await eod(event, "Reply to the user you want to unban.", time=5)
    try:
        await zelretch_bot.unban_chat_member(event.chat.id, target.id)
        await eor(event, f"✅ Unbanned {target.first_name}.")
    except Exception as er:
        await eod(event, f"Could not unban: `{er}`", time=10)


@zelretch_cmd(pattern=r"promote(?:\s+(\d+))?$", admins_only=True, groups_only=True)
async def promote(event):
    if zelretch_bot is None:
        return
    target = _target_user(event)
    if not target:
        return await eod(event, "Reply to the user you want to promote.", time=5)
    try:
        await zelretch_bot.promote_chat_member(event.chat.id, target.id)
        await eor(event, f"⬆️ Promoted {target.first_name}.")
    except Exception as er:
        await eod(event, f"Could not promote: `{er}`", time=10)


@zelretch_cmd(pattern=r"demote(?:\s+(\d+))?$", admins_only=True, groups_only=True)
async def demote(event):
    if zelretch_bot is None:
        return
    target = _target_user(event)
    if not target:
        return await eod(event, "Reply to the user you want to demote.", time=5)
    try:
        await zelretch_bot.promote_chat_member(event.chat.id, target.id,
                                               is_anonymous=False,
                                               can_change_info=False,
                                               can_delete_messages=False,
                                               can_edit_messages=False,
                                               can_invite_users=False,
                                               can_pin_messages=False,
                                               can_manage_topics=False,
                                               can_manage_chat=False,
                                               can_manage_video_chats=False,
                                               can_restrict_members=False,
                                               can_promote_members=False)
        await eor(event, f"⬇️ Demoted {target.first_name}.")
    except Exception as er:
        await eod(event, f"Could not demote: `{er}`", time=10)


@zelretch_cmd(pattern="pin$", admins_only=True, groups_only=True)
async def pin(event):
    if zelretch_bot is None or not event.reply_to_message:
        return await eod(event, "Reply to a message to pin it.", time=5)
    try:
        await zelretch_bot.pin_chat_message(event.chat.id, event.reply_to_message.id)
        await eor(event, "📌 Pinned.")
    except Exception as er:
        await eod(event, f"Could not pin: `{er}`", time=10)
