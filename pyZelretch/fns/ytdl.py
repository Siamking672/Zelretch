# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""yt-dlp wrapper used by media plugins (kept minimal)."""

from __future__ import annotations

from typing import Optional


async def ytdl_download(url: str, audio_only: bool = False) -> Optional[str]:
    """Download *url* via yt-dlp. Returns the local file path or None."""
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        return None
    opts = {
        "format": "bestaudio/best" if audio_only else "best",
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info) if info else None
