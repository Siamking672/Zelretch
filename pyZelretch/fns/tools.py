# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Small utility helpers (file walking, safe parsing, ...)."""

from __future__ import annotations

import os
import re
from typing import List


def get_all_files(path: str, extension: str = ".py") -> List[str]:
    matches: List[str] = []
    for root, _dirs, files in os.walk(path):
        for name in files:
            if name.endswith(extension):
                matches.append(os.path.join(root, name))
    return matches


def safe_filename(name: str, max_len: int = 64) -> str:
    name = re.sub(r"[^\w.\- ]", "_", name).strip()
    return name[:max_len] or "file"
