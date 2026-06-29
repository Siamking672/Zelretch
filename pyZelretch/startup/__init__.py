# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Startup subpackage - lazily-imported internals that wire the bot together."""

from __future__ import annotations

import logging

LOGS = logging.getLogger("Zelretch.startup")

# Re-export the most useful helpers so that `from pyZelretch.startup import *`
# works in the style of the original Ultroid.
from ..configs import Var  # noqa: F401,E402
