# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Plugin manager - list / load / unload / reload / update plugins.

Commands
--------
``.plugins``         - list currently-loaded plugins and addons.
``.load <name>``     - load (or reload) a plugin by file stem.
``.unload <name>``   - remove a plugin's handlers from the active clients.
``.reload <name>``   - shorthand for unload + load.
``.update``          - git pull the main repo + addons, then restart.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

from pyZelretch import LOGS, eod, eor, zelretch_bot, zelretch_cmd
from pyZelretch.dB._core import ADDONS, LIST, LOADED, PLUGINS
from pyZelretch.fns.helper import bash


def _plugin_path(name: str) -> str:
    """Resolve *name* to a path under plugins/ or addons/."""
    for base in ("plugins", "addons", "Zelretch-Addons"):
        candidate = os.path.join(base, f"{name}.py")
        if os.path.exists(candidate):
            return candidate
    return ""


def _unload_plugin(name: str) -> int:
    """Remove a plugin's handlers from zelretch_bot. Returns count removed."""
    handlers = LOADED.pop(name, [])
    removed = 0
    if zelretch_bot is None:
        return 0
    try:
        current = zelretch_bot.list_handlers() if hasattr(zelretch_bot, "list_handlers") else []
    except Exception:
        current = []
    for handler in handlers:
        try:
            zelretch_bot.remove_handler(handler, None)
            removed += 1
        except Exception:
            pass
    LIST.pop(name, None)
    if name in PLUGINS:
        PLUGINS.remove(name)
    if name in ADDONS:
        ADDONS.remove(name)
    return removed


def _load_plugin(name: str) -> str:
    """Import (or reload) a plugin by file stem. Returns the module path."""
    path = _plugin_path(name)
    if not path:
        raise FileNotFoundError(f"Plugin {name!r} not found under plugins/ or addons/.")
    module_name = path.replace(".py", "").replace("/", ".").replace("\\", ".")
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    else:
        importlib.import_module(module_name)
    base = os.path.basename(os.path.dirname(path))
    if base in ("plugins",) and name not in PLUGINS:
        PLUGINS.append(name)
    elif base in ("addons", "Zelretch-Addons") and name not in ADDONS:
        ADDONS.append(name)
    return module_name


@zelretch_cmd(pattern="plugins$")
async def list_plugins(event):
    text = (
        f"**Zelretch - Loaded Plugins**\n\n"
        f"• **Core** ({len(PLUGINS)}): {', '.join(f'`{p}`' for p in PLUGINS) or 'none'}\n"
        f"• **Addons** ({len(ADDONS)}): {', '.join(f'`{p}`' for p in ADDONS) or 'none'}\n"
    )
    await eor(event, text)


@zelretch_cmd(pattern=r"load\s+(\S+)$", owner_only=True)
async def load_plugin(event):
    name = event.matches[0].group(1)
    try:
        module_name = _load_plugin(name)
        await eor(event, f"✅ Loaded `{name}` (`{module_name}`).")
    except Exception as er:
        LOGS.exception(er)
        await eod(event, f"❌ Could not load `{name}`: `{er}`", time=10)


@zelretch_cmd(pattern=r"unload\s+(\S+)$", owner_only=True)
async def unload_plugin(event):
    name = event.matches[0].group(1)
    removed = _unload_plugin(name)
    if removed == 0 and name not in PLUGINS and name not in ADDONS:
        return await eod(event, f"Plugin `{name}` was not loaded.", time=5)
    await eor(event, f"🗑 Unloaded `{name}` (removed {removed} handler(s)).")


@zelretch_cmd(pattern=r"reload\s+(\S+)$", owner_only=True)
async def reload_plugin(event):
    name = event.matches[0].group(1)
    _unload_plugin(name)
    try:
        _load_plugin(name)
        await eor(event, f"🔄 Reloaded `{name}`.")
    except Exception as er:
        LOGS.exception(er)
        await eod(event, f"❌ Reload failed for `{name}`: `{er}`", time=10)


@zelretch_cmd(pattern="update$", owner_only=True)
async def update_bot(event):
    """git pull + restart the bot."""
    msg = await event.reply("🔄 Updating Zelretch...")
    if not os.path.exists(".git"):
        return await msg.edit("Not a git repository - cannot update.")
    stdout, stderr = await bash("git pull --ff-only")
    text = (stdout or "") + (stderr or "")
    if "Already up to date" in text:
        return await msg.edit("✅ Already up to date.")
    await msg.edit(f"```{text[:1500]}```\n\nRestarting...")
    # Schedule a restart.
    os.execv(sys.executable, [sys.executable] + sys.argv)
