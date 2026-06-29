# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Generic typed key manager backed by the singleton ``udB`` instance.

This is a direct port of Ultroid's ``pyUltroid/dB/base.py`` - plugin code that
used ``KeyManager("FOO", cast=list)`` continues to work unchanged.
"""

from __future__ import annotations

from typing import Any, Optional, Type


class KeyManager:
    """Tiny helper around ``udB.get_key`` / ``udB.set_key`` with type casting.

    Parameters
    ----------
    key:
        Top-level DB key the manager reads and writes.
    cast:
        Optional Python type (``list``, ``dict``, ``int``, ...). When set,
        ``get()`` always returns an instance of that type, instantiating an
        empty one if the stored value is missing or has a different type.
    """

    def __init__(self, key: str, cast: Optional[Type[Any]] = None) -> None:
        self._key = key
        self._cast = cast

    # ------------------------------------------------------------------
    # reads
    # ------------------------------------------------------------------
    def get(self) -> Any:
        # Imported lazily to avoid a circular import at package load time.
        from . import udB
        data = udB.get_key(self._key) if udB else None
        if self._cast and not isinstance(data, self._cast):
            if data is None:
                return self._cast()
            return [data] if self._cast is list else self._cast(data)
        if data is not None:
            return data
        return self._cast() if callable(self._cast) else None

    def get_child(self, key: str) -> Any:
        return self.get()[key]

    def count(self) -> int:
        return len(self.get())

    def contains(self, item: Any) -> bool:
        return item in self.get()

    # ------------------------------------------------------------------
    # writes
    # ------------------------------------------------------------------
    def add(self, item: Any) -> None:
        from . import udB
        content = self.get()
        if content is None and isinstance(item, (list, dict)):
            content = type(item)()
        if isinstance(content, dict) and isinstance(item, dict):
            content.update(item)
        elif isinstance(content, list) and item not in content:
            content.append(item)
        else:
            return
        if udB:
            udB.set_key(self._key, content)

    def remove(self, item: Any) -> None:
        from . import udB
        content = self.get()
        if isinstance(content, list) and item in content:
            content.remove(item)
        elif isinstance(content, dict) and content.get(item) is not None:
            del content[item]
        else:
            return
        if udB:
            udB.set_key(self._key, content)
