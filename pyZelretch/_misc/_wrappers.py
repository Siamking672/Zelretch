# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Message editing/deletion wrappers used by every plugin.

These mirror Ultroid's ``event.eor()`` and ``event.eod()`` helpers so that
plugins can be ported with minimal churn. They work on Kurigram ``Message``
objects (which is what ``@Client.on_message`` callbacks receive).
"""

from __future__ import annotations

import asyncio
from typing import Optional


async def eor(event, text: str, time: Optional[int] = None, **kwargs):
    """Edit-or-Reply: edit the message if possible, otherwise reply.

    Mirrors ``pyUltroid._misc.eor``. Returns the resulting message so callers
    can further edit/delete it.
    """
    if not event:
        return None
    try:
        if hasattr(event, "edit_text"):
            msg = await event.edit_text(text, **kwargs)
        elif hasattr(event, "edit"):
            msg = await event.edit(text, **kwargs)
        else:
            msg = await event.reply(text, **kwargs)
    except Exception:
        try:
            msg = await event.reply(text, **kwargs)
        except Exception:
            return None
    if time:
        await asyncio.sleep(time)
        try:
            await msg.delete()
        except Exception:
            pass
        return None
    return msg


async def eod(event, text: str, time: int = 5, **kwargs):
    """Edit-or-delete: like :func:`eor` but always auto-deletes after *time* seconds."""
    return await eor(event, text, time=time, **kwargs)
