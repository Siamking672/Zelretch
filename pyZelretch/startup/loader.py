# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""High-level plugin loader that knows about core plugins, addons and extras."""

from __future__ import annotations

import logging
import os
import sys
from typing import Iterable, Optional

from .. import HOSTED_ON, LOGS, udB
from ..dB._core import ADDONS, LIST, LOADED, PLUGINS
from ..loader import Loader

LOGS = logging.getLogger("Zelretch.plugin_loader")


def load_other_plugins(
    addons: bool = True,
    pmbot: bool = False,
    manager: bool = False,
    vcbot: bool = False,
    exclude: Optional[Iterable[str]] = None,
) -> None:
    """Load every official plugin, plus addons and optional extra modules.

    Parameters
    ----------
    addons:
        When True, also import every ``.py`` under ``addons/`` (if that
        folder exists next to the main project).
    pmbot:
        Load the PM-permit assistant module.
    manager:
        Load the group-manager assistant module.
    vcbot:
        Load the voice-chat assistant module (no-op if pyTgCalls missing).
    exclude:
        Iterable of plugin stems to skip.
    """
    exclude_set = set(exclude or [])
    # Lite-deploy default exclusions (preserved from Ultroid).
    if (HOSTED_ON == "termux" or (udB and udB.get_key("LITE_DEPLOY"))) and \
            (udB and udB.get_key("EXCLUDE_OFFICIAL") is None):
        udB.set_key(
            "EXCLUDE_OFFICIAL",
            "autocorrect audiotools compressor forcesubscribe gdrive glitch "
            "nsfwfilter nightmode pdftools profanityfilter writer youtube",
        )

    if udB and udB.get_key("EXCLUDE_OFFICIAL"):
        exclude_set.update(udB.get_key("EXCLUDE_OFFICIAL").split())

    loader = Loader(path="plugins", key="Official", logger=LOGS)
    loaded = loader.load(exclude=exclude_set or None)
    PLUGINS.extend(loaded)

    # Optional assistant modules.
    assistant_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assistant")
    if os.path.isdir(assistant_dir):
        Loader(path=assistant_dir, key="Assistant", logger=LOGS).load(
            include=["_on_adds", "stickermanager", "admins", "misc", "afk", "_help"]
            if os.path.isdir(os.path.join(assistant_dir, "manager")) else None,
            load_all=True,
        )

    # Addons - look in the standard sibling location first, then in the
    # current working directory (so users can `git clone` the Addons repo
    # next to the main repo).
    addon_paths = []
    for candidate in (
        os.path.join(os.getcwd(), "addons"),
        os.path.join(os.getcwd(), "Zelretch-Addons"),
        os.path.join(os.path.dirname(os.getcwd()), "Zelretch-Addons"),
    ):
        if os.path.isdir(candidate):
            addon_paths.append(candidate)
            break

    if addons and addon_paths:
        addon_loaded = Loader(path=addon_paths[0], key="Addons", logger=LOGS).load()
        ADDONS.extend(addon_loaded)
        LOGS.info(f"Loaded {len(addon_loaded)} addons from {addon_paths[0]}")
    elif addons:
        LOGS.info("Addons enabled but no addons/ folder found - skipping.")

    if vcbot:
        LOGS.info("VCBOT requested but pyTgCalls support is not bundled in this build.")
