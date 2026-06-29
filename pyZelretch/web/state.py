# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Setup wizard state machine.

The wizard tracks one of six states per session:

    NOT_CONFIGURED            -> initial state, no DB yet (or DB empty)
    CORE_VARS_SAVED           -> core variables + DB choice persisted
    DATABASE_RESTORED         -> operator provided existing DB and we
                                 successfully imported its config
    SESSION_CONFIGURED        -> Kurigram session string validated
    READY_TO_DEPLOY           -> all required values present and validated
    DEPLOYED                  -> bot launched (wizard stops)

State transitions are persisted in the DB (key ``SETUP_STATE``) so an
interrupted wizard can resume cleanly. The wizard never stores secrets in
plaintext files - everything lives in the DB the operator picked.
"""

from __future__ import annotations

import enum
from typing import Any, Dict, Optional


class SetupState(str, enum.Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CORE_VARS_SAVED = "CORE_VARS_SAVED"
    DATABASE_RESTORED = "DATABASE_RESTORED"
    SESSION_CONFIGURED = "SESSION_CONFIGURED"
    READY_TO_DEPLOY = "READY_TO_DEPLOY"
    DEPLOYED = "DEPLOYED"

    @classmethod
    def from_str(cls, value: Optional[str]) -> "SetupState":
        try:
            return cls(value or cls.NOT_CONFIGURED.value)
        except ValueError:
            return cls.NOT_CONFIGURED


# Linear progression. The wizard may also jump forward (e.g. restore flow).
ORDER = [
    SetupState.NOT_CONFIGURED,
    SetupState.CORE_VARS_SAVED,
    SetupState.DATABASE_RESTORED,
    SetupState.SESSION_CONFIGURED,
    SetupState.READY_TO_DEPLOY,
    SetupState.DEPLOYED,
]


def can_advance(current: SetupState, target: SetupState) -> bool:
    """Return True if *target* is at or ahead of *current* in the canonical order."""
    return ORDER.index(target) >= ORDER.index(current)


def next_state(current: SetupState) -> SetupState:
    idx = ORDER.index(current)
    if idx == len(ORDER) - 1:
        return current
    return ORDER[idx + 1]


# ---------------------------------------------------------------------------
# DB persistence
# ---------------------------------------------------------------------------

def get_state() -> SetupState:
    """Read the current wizard state from the DB."""
    from ..configs import get_var
    return SetupState.from_str(get_var("SETUP_STATE"))


def set_state(state: SetupState) -> None:
    """Persist *state* to the DB."""
    from ..configs import set_var
    set_var("SETUP_STATE", state.value)


def reset_state() -> None:
    """Forcibly rewind to the start - used by the "Reset" button."""
    from ..configs import set_var
    set_var("SETUP_STATE", SetupState.NOT_CONFIGURED.value)
    set_var("SETUP_COMPLETE", False)


# ---------------------------------------------------------------------------
# Step completion predicates
# ---------------------------------------------------------------------------

def core_vars_complete() -> bool:
    """True when every required ``core`` / ``database`` variable is set."""
    from ..configs import all_vars, schema_for
    snap = all_vars()
    for entry in schema_for("core") + schema_for("database"):
        if entry["required"] and not snap.get(entry["key"]):
            return False
    return True


def session_configured() -> bool:
    """True when a SESSION value has been persisted."""
    from ..configs import get_var
    return bool(get_var("SESSION"))


def ready_to_deploy() -> bool:
    """True when every required schema entry has a non-empty value."""
    from ..configs import all_vars, CONFIG_SCHEMA
    snap = all_vars()
    for entry in CONFIG_SCHEMA:
        if entry["required"] and not snap.get(entry["key"]):
            return False
    return True


def compute_state() -> SetupState:
    """Recompute the state from current config (used after each step)."""
    if not core_vars_complete():
        return SetupState.NOT_CONFIGURED
    if not session_configured():
        return SetupState.CORE_VARS_SAVED
    if not ready_to_deploy():
        return SetupState.SESSION_CONFIGURED
    return SetupState.READY_TO_DEPLOY
