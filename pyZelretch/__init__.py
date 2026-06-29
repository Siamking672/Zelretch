# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Zelretch - a Kurigram-based pluggable Telegram userbot.

This package mirrors the original ``pyUltroid`` namespace so that existing
plugins can be ported with minimal churn. The most important differences are:

* The Telegram client is :class:`kurigram.Client` instead of
  ``telethon.TelegramClient``.
* Configuration lives in the database, not the environment (see
  :mod:`pyZelretch.configs`).
* A FastAPI web setup wizard (see :mod:`pyZelretch.web`) is started before the
  bot on first launch and after every "factory reset".
"""

from __future__ import annotations

import logging
import os
import sys

from .version import __version__, zelretch_version, ZR_CREDIT

# A standard library logger is used at import time so that callers can attach
# handlers before any heavy work happens.
LOGS = logging.getLogger("Zelretch")
if not LOGS.handlers:
    _h = logging.StreamHandler(sys.stdout)
    _h.setFormatter(logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s"))
    LOGS.addHandler(_h)
LOGS.setLevel(logging.INFO)

# True when this package is being executed as ``python -m pyZelretch``.
run_as_module = __package__ in sys.argv or (sys.argv and sys.argv[0] == "-m")

# Initialise these now so that `from pyZelretch import udB, zelretch_bot, ...`
# never raises NameError even when imported as a library.
zelretch_bot = None
asst = None
udB = None
vcClient = None
HOSTED_ON = os.environ.get("HOSTED_ON", "local")

# Command handlers - populated by __main__ after the DB is wired.
HNDLR = "."
DUAL_HNDLR = "/"
SUDO_HNDLR = "."

# Shared runtime caches used by decorators and the loader.
start_time = 0.0
_ult_cache: dict = {}
_ignore_eval: list = []


def _bootstrap_runtime() -> None:
    """Heavy initialisation that only runs when executed as a module.

    Imported lazily so that simply importing :mod:`pyZelretch` (e.g. for the
    setup wizard) does not pull in Kurigram or the database backends.
    """
    global zelretch_bot, asst, udB, vcClient, HOSTED_ON, HNDLR, DUAL_HNDLR, SUDO_HNDLR, start_time

    import time
    start_time = time.time()

    from .configs import Var, is_setup_complete
    from .startup._database import ZelretchDB
    from .startup.BaseClient import ZelretchClient
    from .startup.connections import validate_session, vc_connection
    from .startup.funcs import autobot, enable_inline, update_envs

    udB = ZelretchDB()
    update_envs()

    LOGS.info(f"Connecting to {udB.name}...")
    if udB.ping():
        LOGS.info(f"Connected to {udB.name} successfully!")
    else:
        LOGS.warning(f"Could not ping {udB.name} - continuing anyway (cached reads only).")

    HOSTED_ON = Var.HOSTED_ON
    BOT_MODE = udB.get_key("BOTMODE")
    DUAL_MODE = udB.get_key("DUAL_MODE")
    USER_MODE = udB.get_key("USER_MODE")
    if USER_MODE:
        DUAL_MODE = False
        udB.set_key("DUAL_MODE", False)

    if BOT_MODE:
        if DUAL_MODE:
            udB.del_key("DUAL_MODE")
            DUAL_MODE = False
        zelretch_bot = None
        if not udB.get_key("BOT_TOKEN"):
            LOGS.critical('"BOT_TOKEN" not found - cannot use BOTMODE without it.')
            sys.exit()
    else:
        zelretch_bot = ZelretchClient(
            validate_session(Var.SESSION, LOGS),
            udB=udB,
            app_version=zelretch_version,
            device_model="Zelretch",
        )
        zelretch_bot.loop.run_until_complete(autobot())

    if USER_MODE:
        asst = zelretch_bot
    else:
        asst = ZelretchClient("asst", bot_token=udB.get_key("BOT_TOKEN"), udB=udB)

    if BOT_MODE:
        zelretch_bot = asst
        if udB.get_key("OWNER_ID"):
            try:
                zelretch_bot.me = zelretch_bot.loop.run_until_complete(
                    zelretch_bot.get_users(udB.get_key("OWNER_ID"))
                )
            except Exception as er:
                LOGS.exception(er)
    elif getattr(asst.me, "is_bot", True):
        try:
            zelretch_bot.loop.run_until_complete(enable_inline(zelretch_bot, asst.me.username))
        except Exception as er:
            LOGS.info(f"Inline enablement skipped: {er}")

    vcClient = vc_connection(udB, zelretch_bot)

    HNDLR = udB.get_key("HNDLR") or "."
    DUAL_HNDLR = udB.get_key("DUAL_HNDLR") or "/"
    SUDO_HNDLR = udB.get_key("SUDO_HNDLR") or HNDLR


# Lazy-imported decorator. We attach it at package level so plugins can do
# ``from pyZelretch import zelretch_cmd`` regardless of whether the package
# has been bootstrapped. The decorator itself reads HNDLR / SUDO_HNDLR at
# call-time (i.e. when the plugin is imported), so they are always current.
def __getattr__(name):  # PEP 562 module-level __getattr__
    if name == "zelretch_cmd":
        from ._misc._decorators import zelretch_cmd as _zc
        globals()[name] = _zc
        return _zc
    if name == "ultroid_cmd":  # backwards-compat alias
        from ._misc._decorators import zelretch_cmd as _zc
        globals()[name] = _zc
        return _zc
    if name == "Button":
        try:
            from kurigram.types import InlineKeyboardButton as _B  # type: ignore
            globals()[name] = _B
            return _B
        except Exception:
            class _B:  # minimal stand-in
                def __init__(self, *a, **k):
                    pass
            globals()[name] = _B
            return _B
    if name == "get_string":
        try:
            from strings import get_string as _gs  # type: ignore
            globals()[name] = _gs
            return _gs
        except Exception:
            def _gs(key, *a, **k):
                return key
            globals()[name] = _gs
            return _gs
    if name == "eor":
        from ._misc._wrappers import eor as _eor
        globals()[name] = _eor
        return _eor
    if name == "eod":
        from ._misc._wrappers import eod as _eod
        globals()[name] = _eod
        return _eod
    raise AttributeError(f"module 'pyZelretch' has no attribute {name!r}")


if run_as_module:
    # NOTE: We deliberately do NOT auto-bootstrap here. The wizard needs to
    # run *before* the bot starts, and the decision of which path to take
    # lives in ``pyZelretch.__main__.main``. Importing this package as a
    # module should never crash even if Kurigram or the database is not
    # installed yet.
    LOGS.info(f"Zelretch {zelretch_version} (C) 2021-2026 - {ZR_CREDIT}")
    LOGS.info("Run with: python -m pyZelretch")
else:
    LOGS.info(f"Zelretch {zelretch_version} (C) 2021-2026 - {ZR_CREDIT}")
