# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""``pyZelretch._misc`` - decorators, sudo management, message wrappers."""

from __future__ import annotations

# Re-export the most commonly used names so that
# ``from pyZelretch._misc import zelretch_cmd, eor, eod, owner_and_sudos``
# works in plugins.
from ._decorators import compile_pattern, zelretch_cmd
from ._supporter import SUDO_M, owner_and_sudos
from ._wrappers import eod, eor

__all__ = [
    "compile_pattern",
    "zelretch_cmd",
    "SUDO_M",
    "owner_and_sudos",
    "eod",
    "eor",
]
