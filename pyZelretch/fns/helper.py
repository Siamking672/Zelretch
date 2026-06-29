# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Async-friendly shell + time helpers used throughout the bot."""

from __future__ import annotations

import asyncio
import os
import shlex
import time
from typing import Optional, Tuple


async def bash(cmd: str, timeout: int = 120) -> Tuple[str, Optional[str]]:
    """Run *cmd* in a subprocess, returning ``(stdout, stderr)``."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *shlex.split(cmd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except Exception as er:
        return "", str(er)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return "", f"Command timed out after {timeout}s"
    return (stdout or b"").decode(errors="replace"), (stderr or b"").decode(errors="replace") or None


def time_formatter(ms: int) -> str:
    """Convert milliseconds to a short human string (e.g. ``1d 2h 3m``)."""
    if not ms or ms < 0:
        return "0s"
    s, _ = divmod(int(ms), 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    if s:
        parts.append(f"{s}s")
    return " ".join(parts)


async def progress(current: int, total: int, event, start: float, message: str = "Working...") -> None:
    """Edit *event* with a progress bar every few seconds.

    Kept for parity with Ultroid's ``pyUltroid.fns.helper.progress`` - plugins
    pass it as the ``progress=`` argument to ``client.send_document(...)``.
    """
    if not event:
        return
    now = time.time()
    diff = now - start
    if current < total and int(diff) % 3 != 0:
        return  # throttle edits
    try:
        percent = int(current * 100 / total) if total else 0
        speed = int(current / diff) if diff else 0
        eta = int((total - current) / speed) if speed else 0
        bar = "█" * (percent // 5) + "░" * (20 - percent // 5)
        text = (
            f"{message}\n\n"
            f"`{bar}`  `{percent}%`\n\n"
            f"• `{humanbytes(current)}` of `{humanbytes(total)}`\n"
            f"• Speed: `{humanbytes(speed)}/s`\n"
            f"• ETA: `{time_formatter(eta * 1000)}`"
        )
        await event.edit(text)
    except Exception:
        pass


def humanbytes(size: int) -> str:
    """Format *size* bytes as a human-readable string."""
    if not size:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.2f} {units[i]}"


async def updater() -> bool:
    """Return True if a git pull would bring in new commits (best-effort)."""
    if not os.path.exists(".git"):
        return False
    stdout, _ = await bash("git fetch && git log HEAD..origin --oneline")
    return bool(stdout.strip())
