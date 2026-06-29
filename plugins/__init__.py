# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Top-level ``plugins`` package.

Plugins in this folder are loaded by :class:`pyZelretch.loader.Loader` at
startup. They share the ``pyZelretch`` namespace via ``from pyZelretch import *``.
"""

from __future__ import annotations

# Re-export the most common names so plugins can do ``from plugins import *``.
from pyZelretch import (  # noqa: F401
    HNDLR,
    LOGS,
    SUDO_HNDLR,
    asst,
    eod,
    eor,
    get_string,
    udB,
    zelretch_bot,
    zelretch_cmd,
    ultroid_cmd,
)

try:
    from kurigram.types import InlineKeyboardButton as Button  # type: ignore  # noqa: F401
except ImportError:  # pragma: no cover - kurigram installed at runtime
    class Button:  # type: ignore[no-redef]
        def __init__(self, *a, **k):
            pass
