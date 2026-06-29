# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Utility helpers used by the startup code."""

from __future__ import annotations

import logging
import os
from typing import Optional

LOGS = logging.getLogger("Zelretch.utils")


def time_formatter(ms: int) -> str:
    """Convert milliseconds to a human-readable duration string."""
    if not ms or ms < 0:
        return "0s"
    s, ms = divmod(int(ms), 1000)
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


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def host_platform() -> str:
    """Detect the hosting platform (Heroku / HF / Okteto / local / ...)."""
    if os.environ.get("DYNO"):
        return "heroku"
    if os.environ.get("SPACE_AUTHOR_NAME") or os.environ.get("SPACE_ID"):
        return "huggingface"
    if os.environ.get("OKTETO_NAMESPACE"):
        return "okteto"
    if os.environ.get("TERMUX_VERSION"):
        return "termux"
    if os.path.exists("/.dockerenv"):
        return "docker"
    return "local"
