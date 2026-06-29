# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Zelretch-specific exceptions, mirroring the Ultroid exception catalogue."""

class ZelretchError(Exception):
    """Base class for every Zelretch internal error."""


class DependencyMissingError(ZelretchError):
    """Raised when a plugin tries to use an optional dependency that is not installed."""

    def __init__(self, message="A required dependency is missing."):
        self.message = message
        super().__init__(self.message)


class SetupIncompleteError(ZelretchError):
    """Raised when the bot is asked to run before the setup wizard has finished."""


class SetupStateMismatchError(ZelretchError):
    """Raised when the setup wizard receives a request out of the expected state order."""


class DatabaseConnectionError(ZelretchError):
    """Raised when the configured database cannot be reached."""


class SessionInvalidError(ZelretchError):
    """Raised when a Kurigram session string fails to authenticate."""


class PluginLoadError(ZelretchError):
    """Raised when a plugin fails to import or register its handlers."""
