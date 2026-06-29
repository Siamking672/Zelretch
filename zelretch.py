#!/usr/bin/env python3
# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""One-command launcher.

Run with::

    python zelretch.py

This single command:
  1. Ensures every required Python dependency is installed (auto-pip).
  2. Initialises the LocalDB if no DB has been configured yet.
  3. Decides whether to launch the web setup wizard or the bot proper,
     based on the ``SETUP_COMPLETE`` flag in the DB.

Designed for Hugging Face Spaces, Docker, Heroku, Okteto, Termux and bare
Linux. The user never needs to manually create a ``.env`` file - everything
is collected through the web wizard and stored in the chosen database.
"""

from __future__ import annotations

import os
import subprocess
import sys


REQUIREMENTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
OPTIONAL_REQUIREMENTS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "optional-requirements.txt"
)


def _ensure_pip() -> None:
    try:
        import pip  # type: ignore  # noqa: F401
    except ImportError:
        print("Bootstrapping pip...")
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])


def _install_requirements() -> None:
    if not os.path.exists(REQUIREMENTS_FILE):
        return
    print("[zelretch] Installing core requirements...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q", "-r", REQUIREMENTS_FILE]
    )
    if os.path.exists(OPTIONAL_REQUIREMENTS_FILE):
        print("[zelretch] Installing optional requirements (best-effort)...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-q", "-r", OPTIONAL_REQUIREMENTS_FILE]
            )
        except subprocess.CalledProcessError:
            print("[zelretch] Some optional requirements failed to install - continuing.")


def _ensure_kurigram() -> None:
    try:
        import kurigram  # type: ignore  # noqa: F401
    except ImportError:
        print("[zelretch] Kurigram not installed - installing from requirements.txt")
        _install_requirements()


def _print_banner() -> None:
    print("""
            ┏┳┓╋┏┓╋╋╋╋┏┓┏┓
            ┃┃┣┓┃┗┳┳┳━╋╋┛┃
            ┃┃┃┗┫┏┫┏┫╋┃┃╋┃
            ┗━┻━┻━┻┛┗━┻┻━┛

      Zelretch - Kurigram UserBot
      Based on Ultroid (C) TeamUltroid
""")


def main() -> int:
    _print_banner()
    _ensure_pip()
    _ensure_kurigram()

    # Now that dependencies are present, import the package and run it.
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)

    from pyZelretch.__main__ import main as run_zelretch
    try:
        run_zelretch()
    except KeyboardInterrupt:
        print("\n[zelretch] Stopped by user.")
        return 0
    except Exception as er:
        print(f"[zelretch] Fatal error: {er}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
