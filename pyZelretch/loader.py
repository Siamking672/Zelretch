# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Generic filesystem plugin loader.

The loader is framework-agnostic - it walks a directory, imports every
``.py`` file as a module, and lets the modules themselves register handlers
via decorators. This means it works equally well for the bundled
``plugins/`` folder and for the external ``addons/`` repo.
"""

from __future__ import annotations

import contextlib
import glob
import importlib
import logging
import os
from importlib import import_module
from typing import Iterable, List, Optional


def get_all_files(path: str, extension: str = ".py") -> List[str]:
    """Recursively collect every file under *path* ending in *extension*."""
    matches: List[str] = []
    for root, _dirs, files in os.walk(path):
        for name in files:
            if name.endswith(extension):
                matches.append(os.path.join(root, name))
    return matches


class Loader:
    """Filesystem plugin loader.

    Parameters
    ----------
    path:
        Folder (or single file) to load from.
    key:
        Human label used in log lines ("Official", "Addons", ...).
    logger:
        Logger to emit progress to.
    """

    def __init__(
        self,
        path: str = "plugins",
        key: str = "Official",
        logger: logging.Logger = logging.getLogger("Zelretch.loader"),
    ) -> None:
        self.path = path
        self.key = key
        self._logger = logger

    def load(
        self,
        log: bool = True,
        func=import_module,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
        after_load=None,
        load_all: bool = False,
    ) -> List[str]:
        """Import every plugin file under ``self.path``.

        Returns the list of file-stems that were successfully loaded (useful
        for the plugin manager commands).
        """
        loaded: List[str] = []
        _single = os.path.isfile(self.path)
        if include:
            files = sorted(glob.glob(f"{self.path}/_*.py"))
            for file in include:
                p = f"{self.path}/{file}.py"
                if os.path.exists(p):
                    files.append(p)
        elif _single:
            files = [self.path]
        else:
            files = sorted(
                get_all_files(self.path, ".py") if load_all
                else glob.glob(f"{self.path}/*.py")
            )
            if exclude:
                for path in exclude:
                    if not path.startswith("_"):
                        with contextlib.suppress(ValueError):
                            files.remove(f"{self.path}/{path}.py")

        if log and not _single:
            self._logger.info(f"• Installing {self.key} plugins || Count: {len(files)} •")

        for plugin_path in sorted(files):
            stem = os.path.splitext(os.path.basename(plugin_path))[0]
            if stem == "__init__":
                continue
            module_name = plugin_path.replace(".py", "").replace("/", ".").replace("\\", ".")
            try:
                if func is import_module:
                    func(module_name)
                else:
                    func(plugin_path)
            except ModuleNotFoundError as er:
                self._logger.error(f"{module_name}: '{er.name}' not installed!")
                continue
            except Exception as exc:
                self._logger.error(f"pyZelretch - {self.key} - ERROR - {module_name}")
                self._logger.exception(exc)
                continue
            loaded.append(stem)
            if _single and log:
                self._logger.info(f"Successfully loaded {stem}!")
            if callable(after_load):
                after_load(self, module_name, plugin_name=stem)
        return loaded
