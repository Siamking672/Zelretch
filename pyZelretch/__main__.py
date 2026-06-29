# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""``python -m pyZelretch`` entry point.

This module decides what to start based on the setup state:

* If ``SETUP_COMPLETE`` is False (or unset), it launches the web setup wizard
  on the configured port (default 7860, the Hugging Face Spaces default).
  The wizard collects every required variable, validates them, persists them
  to the database, then signals the bot to start.
* If ``SETUP_COMPLETE`` is True, it skips the wizard and goes straight to the
  bot bootstrap.
"""

from __future__ import annotations

import logging
import os
import sys
import time

LOGS = logging.getLogger("Zelretch")


def main() -> None:
    from . import _bootstrap_runtime, run_as_module
    from .configs import is_setup_complete, get_var, set_var
    from .startup.utils import host_platform

    # Make sure HOSTED_ON is reflected in the config DB on first launch.
    if not get_var("HOSTED_ON") or get_var("HOSTED_ON") == "local":
        set_var("HOSTED_ON", host_platform())

    if not is_setup_complete():
        # The wizard itself needs a working DB to persist state across
        # restarts, so we initialise the database layer first - it falls back
        # to LocalDB if the user hasn't picked one yet.
        from .startup._database import ZelretchDB
        ZelretchDB()  # wires udB + the configs bridge

        LOGS.info("SETUP_COMPLETE is False - starting the web setup wizard.")
        from .web.app import run_wizard
        run_wizard()
        # When the wizard finishes (user clicks Deploy), it flips
        # SETUP_COMPLETE=True and calls back into this module to launch the
        # bot. We fall through here only if the wizard exits cleanly.
        if not is_setup_complete():
            LOGS.info("Wizard exited without completing setup - stopping.")
            return

        # Wizard completed - the bot is being launched in a background thread
        # by the /deploy endpoint. Block forever to keep the process alive.
        LOGS.info("Setup complete - bot is launching in background. Keeping process alive.")
        import time
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            LOGS.info("Stopping Zelretch (Ctrl-C).")
            return

    # Bootstrap the full runtime (DB + clients + plugin loader).
    _bootstrap_runtime()

    from . import udB, zelretch_bot, asst
    from .startup.funcs import (
        WasItRestart,
        autopilot,
        customize,
        keep_redis_alive,
        ready,
        startup_stuff,
    )
    from .startup.loader import load_other_plugins
    from .fns.helper import time_formatter

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler  # noqa: F401
    except ImportError:
        pass

    if not zelretch_bot:
        LOGS.critical("Bot client was not initialised. Re-run the setup wizard.")
        return

    zelretch_bot.loop.run_until_complete(startup_stuff())
    if zelretch_bot.me and not getattr(zelretch_bot.me, "is_bot", False):
        udB.set_key("OWNER_ID", zelretch_bot.uid)

    LOGS.info("Initialising...")

    zelretch_bot.loop.run_until_complete(autopilot())
    zelretch_bot.loop.create_task(keep_redis_alive())

    pmbot = udB.get_key("PMBOT")
    manager = udB.get_key("MANAGER")
    addons = udB.get_key("ADDONS")
    if addons is None:
        addons = True
    vcbot = udB.get_key("VCBOT")
    if get_var("HOSTED_ON") == "huggingface":
        vcbot = False  # voice calls are not supported on HF Spaces

    load_other_plugins(addons=addons, pmbot=pmbot, manager=manager, vcbot=vcbot)

    plugin_channels = udB.get_key("PLUGIN_CHANNEL")

    zelretch_bot.loop.run_until_complete(customize())

    if plugin_channels:
        # Remote addon loading via a Telegram channel - kept as a hook for
        # plugins/<channel_loader>.py.
        pass

    if not udB.get_key("LOG_OFF"):
        zelretch_bot.loop.run_until_complete(ready())

    zelretch_bot.loop.run_until_complete(WasItRestart(udB))

    elapsed = time_formatter(int((time.time() - __import__("pyZelretch").start_time) * 1000))
    LOGS.info(f"Took {elapsed} to start Zelretch.")
    LOGS.info(
        "----------------------------------------------------------------------\n"
        "    Zelretch has been deployed! Type `.help` to see commands.\n"
        "----------------------------------------------------------------------"
    )

    try:
        asst.run()
    except KeyboardInterrupt:
        LOGS.info("Stopping Zelretch (Ctrl-C)...")
    except Exception as er:
        LOGS.exception(er)


if __name__ == "__main__":
    main()
