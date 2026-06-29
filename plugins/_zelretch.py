# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Zelretch identity plugin (ported from ``plugins/_ultroid.py``).

Provides the ``.repo`` and ``.zelretch`` commands - the public face of the
bot. The branding has been updated from ULTROID to Zelretch while preserving
credit to TeamUltroid for the original work.
"""

from __future__ import annotations

from pyZelretch import LOGS, asst, eor, get_string, zelretch_cmd
from pyZelretch.version import __version__, zelretch_version

REPOMSG = """
• **ZELRETCH USERBOT** •\n
• Repo - [Click Here](https://github.com/TeamUltroid/Ultroid)
• Addons - [Click Here](https://github.com/TeamUltroid/UltroidAddons)
• Support - @UltroidSupportChat

_Based on Ultroid (C) TeamUltroid - rewritten for Kurigram as Zelretch._
"""

ULTSTRING = (
    "🎇 **Thanks for deploying Zelretch Userbot!**\n\n"
    "• Here are the basic commands to get you started.\n"
    f"• Version: `{zelretch_version}` (build `{__version__}`)\n"
    "• Type `.help` to see every available command."
)


@zelretch_cmd(pattern="repo$")
async def repify(event):
    """Reply with the repository link."""
    try:
        await event.reply(REPOMSG, link=False)
    except Exception as er:
        LOGS.info(f"Error while repo command: {er}")
        await eor(event, REPOMSG)


@zelretch_cmd(pattern="zelretch$")
async def use_zelretch(event):
    """Post the welcome banner to the log channel (or current chat)."""
    from pyZelretch import udB
    log_channel = udB.get_key("LOG_CHANNEL") if udB else None
    if log_channel and asst:
        try:
            await asst.send_message(log_channel, ULTSTRING)
        except Exception:
            pass
    await eor(event, ULTSTRING)


# Backwards-compat alias for legacy `.ultroid` command.
@zelretch_cmd(pattern="ultroid$")
async def legacy_ultroid(event):
    await use_zelretch(event)
