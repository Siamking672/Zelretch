# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Multi-client launcher (legacy Ultroid compatibility).

When the env var ``SESSION1`` (and optionally ``SESSION2`` ... ``SESSION5``)
is set, this script starts one Zelretch client per session string. Each
client runs in its own asyncio task and shares the same plugin loader.
"""

from __future__ import annotations

import asyncio
import os
import sys


def main() -> int:
    print("[zelretch] Multi-client mode detected - launching multi_client.py")
    sessions = []
    for i in range(1, 6):
        s = os.environ.get(f"SESSION{i}")
        if s:
            sessions.append(s)
    if not sessions:
        print("No SESSION1..SESSION5 found. Falling back to single-client mode.")
        from pyZelretch.__main__ import main as run
        run()
        return 0

    from pyZelretch.startup._database import ZelretchDB
    ZelretchDB()

    from pyZelretch.startup.BaseClient import ZelretchClient
    from pyZelretch.startup.loader import load_other_plugins

    async def run_all():
        clients = []
        for idx, sess in enumerate(sessions):
            try:
                c = ZelretchClient(sess, exit_on_error=False)
                clients.append(c)
                print(f"[zelretch] Started client #{idx + 1} as {c.full_name}")
            except Exception as er:
                print(f"[zelretch] Client #{idx + 1} failed: {er}")

        load_other_plugins(addons=True)

        await asyncio.gather(*[c.run_until_disconnected() for c in clients])

    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        print("[zelretch] Stopped by user.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
