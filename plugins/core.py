# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Core commands: .ping, .alive, .help, .uptime, .info, .id."""

from __future__ import annotations

import time
from datetime import datetime

from pyZelretch import LOGS, eod, eor, get_string, udB, zelretch_bot, zelretch_cmd
from pyZelretch.dB._core import LIST, PLUGINS, ADDONS
from pyZelretch.fns.helper import time_formatter
from pyZelretch.fns.info import display_name, user_mention
from pyZelretch.version import __version__, zelretch_version


@zelretch_cmd(pattern="ping$")
async def ping(event):
    """Measure round-trip latency."""
    start = time.time()
    msg = await event.reply("Pinging...")
    elapsed_ms = int((time.time() - start) * 1000)
    await msg.edit(f"🏓 **Pong!**\n\n• Latency: `{elapsed_ms}` ms")


@zelretch_cmd(pattern="alive$")
async def alive(event):
    """Show the bot's current state."""
    from pyZelretch import HOSTED_ON
    text = (
        "🟢 **Zelretch is alive**\n\n"
        f"• Version: `{zelretch_version}` (build `{__version__}`)\n"
        f"• Uptime: `{_uptime()}`\n"
        f"• Hosted on: `{HOSTED_ON}`\n"
        f"• Database: `{udB.name if udB else 'unavailable'}`\n"
        f"• Plugins loaded: `{len(PLUGINS)}` core, `{len(ADDONS)}` addons\n"
    )
    await eor(event, text)


@zelretch_cmd(pattern="uptime$")
async def uptime(event):
    await eor(event, f"⏱ Uptime: `{_uptime()}`")


def _uptime() -> str:
    from pyZelretch import start_time
    if not start_time:
        return "0s"
    return time_formatter(int((time.time() - start_time) * 1000))


@zelretch_cmd(pattern=r"help(?:\s+(\S+))?$")
async def help_cmd(event):
    """List commands. Use ``.help <plugin>`` for a specific plugin's commands."""
    args = event.matches[0].group(1) if event.matches else None
    if args:
        cmds = LIST.get(args)
        if not cmds:
            return await eod(event, f"No plugin `{args}` was found.", time=5)
        text = f"**{args}** - commands:\n\n" + "\n".join(f"• `{c}`" for c in cmds)
        return await eor(event, text)
    # Otherwise list every plugin.
    chunks = ["**Zelretch - available plugins**\n"]
    chunks.append("**Core:** " + ", ".join(f"`{p}`" for p in PLUGINS))
    if ADDONS:
        chunks.append("**Addons:** " + ", ".join(f"`{p}`" for p in ADDONS))
    chunks.append("\nUse `.help <plugin>` to see a plugin's commands.")
    await eor(event, "\n\n".join(chunks))


@zelretch_cmd(pattern="id$")
async def get_id(event):
    """Reply with chat / user / reply IDs."""
    chat_id = event.chat.id if event.chat else "?"
    user_id = event.from_user.id if event.from_user else "?"
    text = f"• Chat ID: `{chat_id}`\n• Your ID: `{user_id}`"
    if event.reply_to_message:
        replied = event.reply_to_message.from_user
        if replied:
            text += f"\n• Replied user: `{replied.id}` ({display_name(replied)})"
    await eor(event, text)


@zelretch_cmd(pattern="info$")
async def info(event):
    """Show information about the replied user or yourself."""
    target = event.reply_to_message.from_user if event.reply_to_message else event.from_user
    if not target:
        return await eod(event, "Reply to a user or use this in a private chat.", time=5)
    text = (
        f"**User Information**\n\n"
        f"• Name: {display_name(target)}\n"
        f"• ID: `{target.id}`\n"
        f"• Username: @{getattr(target, 'username', 'None')}\n"
        f"• Bot: `{getattr(target, 'is_bot', False)}`\n"
        f"• Mention: {user_mention(target)}"
    )
    await eor(event, text)
