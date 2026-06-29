# Zelretch - UserBot
# Resources - fonts, session generator and startup helpers.

This folder holds static resources used by Zelretch plugins.

## fonts/

TTF / OTF font files used by image-generating plugins (logo, glitch,
profile card, etc.). All fonts are redistributed under their respective
open-source licenses.

## session/

Contains `ssgen.py` (a Python session-string generator) and `session.sh`
(a bash wrapper). Both are preserved from Ultroid for parity; the
recommended path in Zelretch is to use the top-level `sessiongen` script
which produces a Kurigram-format session string.

## startup/

Holds platform-specific startup helpers (e.g. the Termux bootstrap).
Preserved from Ultroid for parity.

## extras/

Logos, thumbnails and tutorial markdown files. Used by image plugins and
by the README.
