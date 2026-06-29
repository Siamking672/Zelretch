# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Registry of plugin metadata, populated at import time by the loader."""

# Names of every core plugin currently loaded.
PLUGINS: list = []

# Names of every addon currently loaded.
ADDONS: list = []

# Plugin name -> list of command patterns it registered.
HELP: dict = {}

# Plugin file stem -> list of wrapped handler functions (for unload).
LOADED: dict = {}

# Plugin file stem -> list of command patterns (for `.help <plugin>`).
LIST: dict = {}

# Voice-chat help (kept for parity with Ultroid).
VC_HELP: dict = {}

# Developers / sudo users allowed to bypass owner checks.
DEVLIST: list = []
