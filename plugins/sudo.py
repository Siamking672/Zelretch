# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Sudo management - ported from ``plugins/sudo.py``.

Provides:
  .sudo <user_id>     - add a sudo user
  .delsudo <user_id>  - remove a sudo user
  .listsudo           - list all sudo users
"""

from __future__ import annotations

from pyZelretch import eod, eor, udB, zelretch_cmd
from pyZelretch._misc._supporter import SUDO_M


@zelretch_cmd(pattern=r"sudo(?:\s+(\d+))?$", owner_only=True)
async def add_sudo(event):
    """Add a user to the sudo list."""
    user_id = event.matches[0].group(1) if event.matches else None
    if not user_id and event.reply_to_message:
        user_id = str(event.reply_to_message.from_user.id)
    if not user_id:
        return await eod(event, "Reply to a user or pass their ID: `.sudo 123456`", time=5)
    SUDO_M.add_sudo(int(user_id))
    await eor(event, f"✅ Added `{user_id}` to sudo users.")


@zelretch_cmd(pattern=r"delsudo(?:\s+(\d+))?$", owner_only=True)
async def del_sudo(event):
    user_id = event.matches[0].group(1) if event.matches else None
    if not user_id and event.reply_to_message:
        user_id = str(event.reply_to_message.from_user.id)
    if not user_id:
        return await eod(event, "Usage: `.delsudo 123456`", time=5)
    SUDO_M.del_sudo(int(user_id))
    await eor(event, f"🗑 Removed `{user_id}` from sudo users.")


@zelretch_cmd(pattern="listsudo$", owner_only=True)
async def list_sudo(event):
    sudos = SUDO_M.sudos
    if not sudos:
        return await eor(event, "No sudo users configured.")
    text = "**Sudo users:**\n\n" + "\n".join(f"• `{u}`" for u in sudos)
    await eor(event, text)
