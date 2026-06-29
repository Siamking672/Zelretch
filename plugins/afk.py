# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""AFK (Away From Keyboard) plugin - ported from Ultroid ``plugins/afk.py``."""

from __future__ import annotations

import time
from datetime import datetime

from pyZelretch import eod, eor, udB, zelretch_bot, zelretch_cmd
from pyZelretch.dB import afk_db
from pyZelretch.fns.info import display_name


@zelretch_cmd(pattern=r"afk(?:\s+(.+))?$")
async def set_afk(event):
    reason = (event.matches[0].group(1) if event.matches else "").strip() or "No reason."
    afk_db.add_item("state", {"reason": reason, "since": time.time()})
    await eor(event, f"🛌 **I'm now AFK.**\nReason: `{reason}`")


@zelretch_cmd(pattern="unafk$")
async def unset_afk(event):
    state = afk_db.get_data()
    if not state:
        return await eod(event, "I'm not AFK.", time=5)
    since = state.get("since", time.time())
    elapsed = time_formatter(int((time.time() - since) * 1000))
    afk_db.clear()
    await eor(event, f"👋 **Back.** Was away for `{elapsed}`.")


def time_formatter(ms: int) -> str:
    if not ms or ms < 0:
        return "0s"
    s, _ = divmod(int(ms), 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    if s: parts.append(f"{s}s")
    return " ".join(parts)


# Responder for incoming mentions while AFK.
async def afk_responder(client, message):
    if not afk_db.get_data():
        return
    if not message.from_user or message.from_user.is_bot:
        return
    state = afk_db.get_data()
    elapsed = time_formatter(int((time.time() - state.get("since", time.time())) * 1000))
    try:
        await message.reply(
            f"🛌 **{display_name(zelretch_bot.me) if zelretch_bot else 'User'} is AFK.**\n"
            f"• Reason: `{state.get('reason', 'No reason.')}`\n"
            f"• Away for: `{elapsed}`"
        )
    except Exception:
        pass


if zelretch_bot is not None:
    try:
        from kurigram import filters  # type: ignore
        zelretch_bot.add_message_handler(afk_responder, filters.mentioned & filters.incoming)
    except Exception:
        pass
