# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""filestore_db - ported from the original Ultroid module.

This file keeps the public surface (``KeyManager``-backed helpers) so plugins
that import these helpers continue to work. The implementation is a thin
wrapper around the shared KeyManager; the heavy lifting lives in the
underlying database backend.
"""

from __future__ import annotations

from typing import Any, List, Optional

from .base import KeyManager


_MANAGER = KeyManager("FILESTORE_DB", cast=dict)


def get_data() -> Any:
    return _MANAGER.get() or {}


def set_data(data: Any) -> None:
    from . import udB
    if udB:
        udB.set_key("FILESTORE_DB", data)


def add_item(key: str, value: Any) -> None:
    data = get_data()
    data[key] = value
    set_data(data)


def del_item(key: str) -> bool:
    data = get_data()
    if key in data:
        del data[key]
        set_data(data)
        return True
    return False


def get_item(key: str) -> Optional[Any]:
    return get_data().get(key)


def list_items() -> List[str]:
    return list(get_data().keys())


def clear() -> None:
    set_data({})
