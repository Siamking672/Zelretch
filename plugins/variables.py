# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Variables viewer - inspect / modify runtime config from the bot.

Provides:
  .getvar <key>     - show a config value
  .setvar <k> <v>   - update a config value
  .delvar <key>     - remove a config value
  .allvars          - dump every config key (secrets masked)
"""

from __future__ import annotations

from pyZelretch import eod, eor, zelretch_cmd
from pyZelretch.configs import CONFIG_SCHEMA, all_vars, del_var, get_var, set_var


@zelretch_cmd(pattern=r"getvar\s+(\S+)$", owner_only=True)
async def getvar(event):
    key = event.matches[0].group(1)
    value = get_var(key)
    # Mask secrets.
    schema = next((e for e in CONFIG_SCHEMA if e["key"] == key), None)
    if schema and schema.get("secret") and value:
        value = "********"
    await eor(event, f"`{key}` = `{value!r}`")


@zelretch_cmd(pattern=r"setvar\s+(\S+)\s+(.+)$", owner_only=True)
async def setvar_cmd(event):
    key = event.matches[0].group(1)
    value = event.matches[0].group(2)
    set_var(key, value)
    await eor(event, f"✅ Set `{key}`.")


@zelretch_cmd(pattern=r"delvar\s+(\S+)$", owner_only=True)
async def delvar_cmd(event):
    key = event.matches[0].group(1)
    del_var(key)
    await eor(event, f"🗑 Deleted `{key}` (if it existed).")


@zelretch_cmd(pattern="allvars$", owner_only=True)
async def allvars(event):
    snap = all_vars()
    schema_by_key = {e["key"]: e for e in CONFIG_SCHEMA}
    lines = []
    for k, v in snap.items():
        if schema_by_key.get(k, {}).get("secret") and v:
            v = "********"
        lines.append(f"• `{k}`: `{v!r}`")
    await eor(event, "**All vars:**\n\n" + "\n".join(lines))
