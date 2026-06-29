# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Misc utility commands ported from Ultroid ``plugins/tools.py``.

Provides:
  .echo <text>           - echo back the text
  .tr <lang> <text>      - translate text (uses ``googletrans`` if installed)
  .upper / .lower <text> - case conversion
  .reverse <text>        - reverse the text
  .repeat <n> <text>     - repeat text n times
"""

from __future__ import annotations

from pyZelretch import eod, eor, zelretch_cmd


@zelretch_cmd(pattern=r"echo(?:\s+(.+))?$")
async def echo(event):
    text = event.matches[0].group(1) if event.matches else None
    if not text:
        return await eod(event, "Usage: `.echo hello`", time=5)
    await eor(event, text)


@zelretch_cmd(pattern=r"upper(?:\s+(.+))?$")
async def upper(event):
    text = event.matches[0].group(1) if event.matches else None
    if not text:
        return await eod(event, "Usage: `.upper hello`", time=5)
    await eor(event, text.upper())


@zelretch_cmd(pattern=r"lower(?:\s+(.+))?$")
async def lower(event):
    text = event.matches[0].group(1) if event.matches else None
    if not text:
        return await eod(event, "Usage: `.lower HELLO`", time=5)
    await eor(event, text.lower())


@zelretch_cmd(pattern=r"reverse(?:\s+(.+))?$")
async def reverse(event):
    text = event.matches[0].group(1) if event.matches else None
    if not text:
        return await eod(event, "Usage: `.reverse hello`", time=5)
    await eor(event, text[::-1])


@zelretch_cmd(pattern=r"repeat\s+(\d+)\s+(.+)$")
async def repeat(event):
    n = int(event.matches[0].group(1))
    text = event.matches[0].group(2)
    if n > 50:
        return await eod(event, "Maximum repeat is 50.", time=5)
    await eor(event, (text + "\n") * n)


@zelretch_cmd(pattern=r"tr(?:\s+(\S+)\s+(.+))?$")
async def translate(event):
    """Translate text using ``googletrans`` if installed."""
    lang = event.matches[0].group(1) if event.matches else None
    text = event.matches[0].group(2) if event.matches else None
    if not (lang and text):
        return await eod(event, "Usage: `.tr hi Hello world`", time=5)
    try:
        from googletrans import Translator  # type: ignore
        t = Translator()
        result = t.translate(text, dest=lang)
        await eor(event, f"**{result.text}**")
    except ImportError:
        await eod(event, "Install `googletrans` to use this command.", time=10)
