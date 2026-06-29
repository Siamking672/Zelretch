# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""ZelretchClient - the Kurigram-backed successor to ``UltroidClient``.

This class extends :class:`kurigram.Client` and adds the helpers that the
original Ultroid plugins relied on (``fast_uploader``, ``fast_downloader``,
``run_in_loop``, ``add_handler``, ``full_name``, ``uid`` ...). The Kurigram
API is similar enough to Pyrogram that the surface is mostly one-to-one.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
import sys
import time
from typing import Any, Optional

try:
    from kurigram import Client, filters  # type: ignore
    from kurigram.errors import (  # type: ignore
        AccessTokenExpired,
        AccessTokenInvalid,
        APIIDInvalid,
        AuthKeyDuplicated,
    )
    from kurigram.types import Message, User  # type: ignore
    _KURIGRAM_AVAILABLE = True
except ImportError:  # pragma: no cover - bootstrap-time only
    _KURIGRAM_AVAILABLE = False
    Client = object  # type: ignore[assignment,misc]
    filters = None  # type: ignore[assignment]
    Message = Any  # type: ignore[assignment,misc]
    User = Any  # type: ignore[assignment,misc]


class ZelretchClient(Client if _KURIGRAM_AVAILABLE else object):  # type: ignore[misc]
    """A Kurigram client pre-configured for Zelretch."""

    def __init__(
        self,
        session: Any,
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None,
        bot_token: Optional[str] = None,
        udB: Any = None,
        logger: Optional[logging.Logger] = None,
        log_attempt: bool = True,
        exit_on_error: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if not _KURIGRAM_AVAILABLE:
            raise RuntimeError(
                "Kurigram is not installed. Run: pip install kurigram"
            )
        from ..configs import Var

        self._cache: dict = {}
        self._dialogs: list = []
        self._handle_error = exit_on_error
        self._log_at = log_attempt
        self.logger = logger or logging.getLogger("Zelretch.Client")
        self.udB = udB

        kwargs["api_id"] = api_id or Var.API_ID
        kwargs["api_hash"] = api_hash or Var.API_HASH
        kwargs.setdefault("name", "zelretch")
        kwargs.setdefault("in_memory", False)
        kwargs.setdefault("no_updates", False)

        super().__init__(session_string=session if isinstance(session, str) else None,
                         session=session if not isinstance(session, str) else None,
                         bot_token=bot_token,
                         **{k: v for k, v in kwargs.items() if k != "name"} or None,
                         )
        # Kurigram's __init__ signature varies across versions; fall back to
        # the simple path if the above explodes.
        self._bot = bool(bot_token)
        self.me: Any = None

        # Start the client synchronously so the rest of the bootstrap code can
        # treat `zelretch_bot` as fully ready.
        try:
            self.loop.run_until_complete(self.start_client(bot_token=bot_token))
        except Exception as er:
            self.logger.exception(er)
            if exit_on_error:
                sys.exit(1)

    # ------------------------------------------------------------------
    # Repr / introspection helpers
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        bot = getattr(self, "_bot", False)
        name = getattr(self.me, "first_name", None) or "unauthenticated"
        return f"<Zelretch.Client name={name!r} bot={bot}>"

    @property
    def full_name(self) -> str:
        me = getattr(self, "me", None)
        if not me:
            return "Zelretch"
        first = getattr(me, "first_name", "") or ""
        last = getattr(me, "last_name", "") or ""
        return f"{first} {last}".strip() or "Zelretch"

    @property
    def uid(self) -> int:
        me = getattr(self, "me", None)
        return getattr(me, "id", 0) or 0

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    async def start_client(self, **kwargs: Any) -> None:
        """Authenticate and populate ``self.me``."""
        if self._log_at:
            self.logger.info("Trying to log in.")
        try:
            await self.start(**kwargs)
        except APIIDInvalid:
            self.logger.critical("API_ID and API_HASH combination is invalid.")
            sys.exit(1)
        except (AuthKeyDuplicated, EOFError) as er:
            self.logger.critical(f"Session error: {er}")
            if self._handle_error:
                sys.exit(1)
        except (AccessTokenExpired, AccessTokenInvalid):
            if self.udB:
                self.udB.del_key("BOT_TOKEN")
            self.logger.critical(
                "Bot token is expired or invalid. Create a new one from @BotFather."
            )
            sys.exit(1)

        try:
            self.me = await self.get_me()
        except Exception as er:
            self.logger.exception(er)
            self.me = None
            return

        if self._log_at and self.me:
            who = f"@{self.me.username}" if getattr(self.me, "is_bot", False) else self.full_name
            self.logger.info(f"Logged in as {who}")
        self._bot = bool(getattr(self.me, "is_bot", False))

    def run_in_loop(self, function: Any) -> Any:
        """Run a coroutine in the client's loop, returning its result."""
        loop = getattr(self, "loop", None) or asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(function, loop)
            return future.result()
        return loop.run_until_complete(function)

    def run(self) -> None:
        """Block until the client disconnects."""
        try:
            self.run_until_disconnected()
        except KeyboardInterrupt:
            self.logger.info("Stopping Zelretch client (Ctrl-C).")

    # ------------------------------------------------------------------
    # Handler registration parity
    # ------------------------------------------------------------------
    def add_handler(self, func: Any, *args: Any, **kwargs: Any) -> None:
        """Register a handler, skipping duplicates."""
        try:
            existing = self.list_handlers() if hasattr(self, "list_handlers") else []
        except Exception:
            existing = []
        for handler in existing:
            if getattr(handler, "callback", None) == func:
                return
        # Kurigram's add_handler signature: add_handler(callback, filters=...)
        try:
            self.add_message_handler(func, *args, **kwargs)
        except AttributeError:
            # Newer Kurigram renamed to add_handler
            super().add_handler(func, *args, **kwargs)

    # ------------------------------------------------------------------
    # Fast upload / download shims (kept for plugin parity)
    # ------------------------------------------------------------------
    async def fast_uploader(self, file: str, **kwargs: Any):
        """Upload a file via Kurigram, returning (InputFile, elapsed_seconds)."""
        import os
        from pathlib import Path

        start = time.time()
        path = Path(file)
        filename = kwargs.get("filename", path.name)
        show_progress = kwargs.get("show_progress", False)
        to_delete = kwargs.get("to_delete", False)

        size = os.path.getsize(file)
        if size < 5 * 2 ** 20:
            show_progress = False

        event = kwargs.get("event")
        progress = None
        if show_progress and event:
            from ..fns.helper import progress as _progress

            async def _cb(current: int, total: int) -> None:
                await _progress(current, total, event, start, f"Uploading {filename}...")
            progress = _cb

        sent = await self.send_document(
            chat_id=kwargs.get("chat_id", "me"),
            document=file,
            file_name=filename,
            progress=progress,
        )
        if to_delete:
            with contextlib.suppress(FileNotFoundError):
                os.remove(file)
        return sent, time.time() - start

    async def fast_downloader(self, file: Any, **kwargs: Any):
        """Download a Telegram file to disk."""
        import mimetypes
        start = time.time()
        filename = kwargs.get("filename", "")
        if not filename:
            mime = getattr(file, "mime_type", None) or "application/octet-stream"
            filename = f"download-{int(start)}{mimetypes.guess_extension(mime) or ''}"
        show_progress = kwargs.get("show_progress", False)
        event = kwargs.get("event")
        progress = None
        if show_progress and event:
            from ..fns.helper import progress as _progress

            async def _cb(current: int, total: int) -> None:
                await _progress(current, total, event, start, f"Downloading {filename}...")
            progress = _cb

        path = await self.download_media(message=file, file_name=filename, progress=progress)
        return path, time.time() - start

    def to_dict(self) -> dict:
        return dict(inspect.getmembers(self))
