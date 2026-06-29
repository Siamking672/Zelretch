# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Sudo / owner management helpers (ported from ``pyUltroid._misc._supporter``)."""

from __future__ import annotations

from typing import List


class _SudoManager:
    """Tiny wrapper around the ``SUDOS`` config key."""

    def __init__(self) -> None:
        self._cached: List[int] = []

    @property
    def should_allow_sudo(self) -> bool:
        from .. import udB
        if not udB:
            return False
        return bool(udB.get_key("SUDOS"))

    @property
    def sudos(self) -> List[int]:
        from .. import udB
        if not udB:
            return []
        raw = udB.get_key("SUDOS") or ""
        return [int(x) for x in str(raw).split() if x.isdigit()]

    @property
    def fullsudos(self) -> List[int]:
        from .. import udB
        if not udB:
            return []
        raw = udB.get_key("FULLSUDOS") or ""
        return [int(x) for x in str(raw).split() if x.isdigit()]

    def add_sudo(self, user_id: int) -> None:
        from .. import udB
        if not udB:
            return
        current = set(self.sudos)
        current.add(int(user_id))
        udB.set_key("SUDOS", " ".join(map(str, current)))

    def del_sudo(self, user_id: int) -> None:
        from .. import udB
        if not udB:
            return
        current = set(self.sudos)
        current.discard(int(user_id))
        udB.set_key("SUDOS", " ".join(map(str, current)))


SUDO_M = _SudoManager()


def owner_and_sudos() -> List[int]:
    """Return the list of owner + sudo user IDs."""
    from .. import udB
    out: List[int] = []
    if udB:
        owner = udB.get_key("OWNER_ID")
        if owner:
            try:
                out.append(int(owner))
            except (TypeError, ValueError):
                pass
    out.extend(SUDO_M.sudos)
    return list(set(out))
