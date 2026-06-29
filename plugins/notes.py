# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Notes / saved replies - ported from ``plugins/notes.py``.

Provides:
  .note <name> <text>   - save a note
  .get <name>           - retrieve a note
  .notes                - list saved notes
  .delnote <name>       - delete a note
"""

from __future__ import annotations

from pyZelretch import eod, eor, udB, zelretch_cmd
from pyZelretch.dB import notes_db


@zelretch_cmd(pattern=r"note\s+(\S+)\s+(.+)$")
async def save_note(event):
    name = event.matches[0].group(1)
    text = event.matches[0].group(2)
    notes_db.add_item(name, text)
    await eor(event, f"💾 Saved note `{name}`.")


@zelretch_cmd(pattern=r"get\s+(\S+)$")
async def get_note(event):
    name = event.matches[0].group(1)
    note = notes_db.get_item(name)
    if not note:
        return await eod(event, f"No note named `{name}`.", time=5)
    await eor(event, f"**{name}**\n\n{note}")


@zelretch_cmd(pattern="notes$")
async def list_notes(event):
    items = notes_db.list_items()
    if not items:
        return await eor(event, "No saved notes.")
    text = "**Saved notes:**\n\n" + ", ".join(f"`{n}`" for n in items)
    await eor(event, text)


@zelretch_cmd(pattern=r"delnote\s+(\S+)$")
async def del_note(event):
    name = event.matches[0].group(1)
    if notes_db.del_item(name):
        await eor(event, f"🗑 Deleted note `{name}`.")
    else:
        await eod(event, f"No note named `{name}`.", time=5)
