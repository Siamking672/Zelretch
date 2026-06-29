# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Async code-executor sandbox (kept minimal - not a security boundary)."""

from __future__ import annotations

import asyncio
from typing import Any


async def execute(code: str, env: dict = None) -> dict:
    """Execute *code* with ``exec`` in a fresh namespace.

    Use this only for trusted, operator-supplied snippets. The original
    Ultroid exposed a similar helper for the ``.eval`` command - keep that
    command restricted to the owner.
    """
    env = env or {}
    out = {"result": None, "error": None}
    try:
        exec(code, env, env)
        out["result"] = env.get("result")
    except Exception as er:
        out["error"] = str(er)
    return out
