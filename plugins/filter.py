# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Filters - keyword-triggered replies (similar to snips but case-insensitive)."""

from __future__ import annotations

from pyZelretch import eod, eor, zelretch_cmd
from pyZelretch.dB import filter_db


@zelretch_cmd(pattern=r"filter\s+(\S+)\s*::\s*(.+)$", owner_only=True)
async def save_filter(event):
    keyword = event.matches[0].group(1)
    reply = event.matches[0].group(2)
    filter_db.add_item(keyword.lower(), reply)
    await eor(event, f"💾 Saved filter for `{keyword}`.")


@zelretch_cmd(pattern="filters$")
async def list_filters(event):
    items = filter_db.list_items()
    if not items:
        return await eor(event, "No filters saved.")
    await eor(event, "**Filters:** " + ", ".join(f"`{k}`" for k in items))


@zelretch_cmd(pattern=r"delfilter\s+(\S+)$", owner_only=True)
async def del_filter(event):
    keyword = event.matches[0].group(1).lower()
    if filter_db.del_item(keyword):
        await eor(event, f"🗑 Deleted filter `{keyword}`.")
    else:
        await eod(event, f"No filter named `{keyword}`.", time=5)
