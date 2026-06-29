# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""FastTelethon shim - kept as a stub since Kurigram has fast transfer built in."""

from __future__ import annotations


async def upload_file(*args, **kwargs):
    """Use the client's native ``send_document`` instead."""
    raise NotImplementedError(
        "FastTelethon is no longer needed - Kurigram's send_document() is fast "
        "enough. Call client.send_document() directly."
    )


async def download_file(*args, **kwargs):
    raise NotImplementedError(
        "FastTelethon is no longer needed - Kurigram's download_media() is fast "
        "enough. Call client.download_media() directly."
    )
