# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Zelretch i18n shim.

We keep the original Ultroid YAML layout so community translations can be
reused, but ``get_string`` returns the key itself when no translation is
found - this is safer than crashing at startup.
"""

from __future__ import annotations

import os
from typing import Optional

_STRINGS: dict = {}
_DEFAULT_LANG = "en"


def _load(lang: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "strings", f"{lang}.yml")
    if not os.path.exists(path):
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_string(key: str, *args: object, **kwargs: object) -> str:
    """Return the localised string for *key*.

    Falls back to the English bundle, then to *key* itself. Positional /
    keyword arguments are passed to ``str.format``.
    """
    global _STRINGS
    if not _STRINGS:
        _STRINGS = _load(_DEFAULT_LANG)
    value = _STRINGS.get(key)
    if value is None:
        return key
    try:
        return value.format(*args, **kwargs)  # type: ignore[union-attr]
    except Exception:
        return value


def set_language(lang: str) -> None:
    global _STRINGS, _DEFAULT_LANG
    _DEFAULT_LANG = lang
    _STRINGS = _load(lang) or _load("en")
