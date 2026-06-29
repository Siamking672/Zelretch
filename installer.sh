#!/usr/bin/env bash
# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# Installer: ensures every system + Python dependency is present.
# Used by the Docker build and by the one-command launcher.

set -e

PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY="python"

# Ensure pip is present.
"$PY" -m pip install --upgrade pip >/dev/null 2>&1 || "$PY" -m ensurepip --upgrade

# Core requirements.
"$PY" -m pip install -r requirements.txt

# Optional requirements (best-effort).
if [ -f optional-requirements.txt ] ; then
  "$PY" -m pip install -r optional-requirements.txt || \
    echo "[zelretch] Some optional requirements failed to install - continuing."
fi

# Localdb fallback (used when DATABASE_TYPE=local).
"$PY" -m pip install -q localdb.json 2>/dev/null || true

echo "[zelretch] Installer finished."
