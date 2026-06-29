# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Snippets - regex-triggered auto-replies. Ported from ``plugins/snips.py``.

Provides:
  .snip <pattern> :: <reply>   - save a snip
  .snips                      - list snips
  .delsnip <pattern>          - delete a snip
"""

from __future__ import annotations

import re

from pyZelretch import LOGS, eod, eor, zelretch_bot, zelretch_cmd
from pyZelretch.dB import snips_db


@zelretch_cmd(pattern=r"snip\s+(\S+)\s*::\s*(.+)$", owner_only=True)
async def save_snip(event):
    pattern = event.matches[0].group(1)
    reply = event.matches[0].group(2)
    snips_db.add_item(pattern, reply)
    await eor(event, f"💾 Saved snip for `{pattern}`.")


@zelretch_cmd(pattern="snips$")
async def list_snips(event):
    items = snips_db.list_items()
    if not items:
        return await eor(event, "No snips saved.")
    text = "**Snips:**\n\n" + ", ".join(f"`{p}`" for p in items)
    await eor(event, text)


@zelretch_cmd(pattern=r"delsnip\s+(\S+)$", owner_only=True)
async def del_snip(event):
    pattern = event.matches[0].group(1)
    if snips_db.del_item(pattern):
        await eor(event, f"🗑 Deleted snip `{pattern}`.")
    else:
        await eod(event, f"No snip matching `{pattern}`.", time=5)


# Responder for incoming messages.
async def snip_responder(client, message):
    if not message or not message.text:
        return
    data = snips_db.get_data()
    for pattern, reply in data.items():
        try:
            if re.search(pattern, message.text):
                await message.reply(reply)
                break
        except re.error:
            continue
        except Exception as er:
            LOGS.info(f"Snip match error: {er}")


if zelretch_bot is not None:
    try:
        from kurigram import filters  # type: ignore
        zelretch_bot.add_message_handler(snip_responder, filters.incoming & ~filters.bot)
    except Exception:
        pass
