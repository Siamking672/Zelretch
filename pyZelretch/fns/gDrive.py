# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Google Drive helpers (stub - real impl requires oauth2 setup)."""

from __future__ import annotations


async def gdrive_upload(file_path: str) -> str:
    raise NotImplementedError(
        "Google Drive upload requires oauth2 credentials - "
        "configure them via the setup wizard's 'advanced' tab."
    )
