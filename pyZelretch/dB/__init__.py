# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Re-export the singleton database handle.

Plugins should ``from pyZelretch.dB import udB`` - the actual instance is set
by :mod:`pyZelretch.startup._database` after the backend has been chosen.
"""

from __future__ import annotations

# Placeholder; replaced by ``_database.py`` once a backend is live.
udB = None  # type: ignore[assignment]


def _set_udb(instance) -> None:
    """Internal hook used by the startup code."""
    global udB
    udB = instance


from . import _core  # noqa: E402,F401  (re-export for ``from pyZelretch.dB import PLUGINS``)
from . import (  # noqa: E402,F401
    afk_db,
    antiflood_db,
    asstcmd_db,
    blacklist_chat_db,
    blacklist_db,
    botchat_db,
    echo_db,
    filestore_db,
    filter_db,
    forcesub_db,
    gban_mute_db,
    greetings_db,
    mute_db,
    notes_db,
    nsfw_db,
    snips_db,
    vc_sudos,
    warn_db,
)

__all__ = ["udB", "_core"]
