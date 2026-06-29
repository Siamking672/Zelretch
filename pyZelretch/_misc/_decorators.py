# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""``zelretch_cmd`` decorator - the Kurigram successor to ``ultroid_cmd``.

Plugins register commands with::

    from pyZelretch import zelretch_cmd

    @zelretch_cmd(pattern="ping$")
    async def ping_handler(event):
        await event.reply("Pong!")

The decorator transparently:
* Builds a Kurigram ``filters.command`` filter from the pattern + handler.
* Wraps the callback in a try/except that captures FloodWait, AuthKey errors
  and unexpected crashes - posting the traceback to the configured log
  channel.
* Skips chats listed in ``BLACKLIST_CHATS``.
* Honours owner/sudo restrictions.
* Records the pattern in ``LIST`` for the ``.help`` system.

The pattern syntax matches Ultroid: a leading ``^`` or ``.`` is stripped,
then a single-character handler (``HNDLR``, default ``.``) is prepended.
"""

from __future__ import annotations

import inspect
import logging
import re
import sys
import traceback
from io import BytesIO
from pathlib import Path
from time import gmtime, strftime
from typing import Any, Callable, Optional

try:
    from kurigram import filters  # type: ignore
    from kurigram.errors import (  # type: ignore
        AuthKeyDuplicated,
        BotInlineDisabled,
        ChatSendInlineForbidden,
        ChatSendMediaForbidden,
        ChatSendStickersForbidden,
        FloodWait,
        MessageDeleteForbidden,
        MessageIdInvalid,
        MessageNotModified,
        UserIsBot,
    )
    _K = True
except ImportError:  # pragma: no cover - bootstrap only
    filters = None  # type: ignore[assignment]
    _K = False

from .. import HNDLR, LOGS, SUDO_HNDLR, _ignore_eval, udB, zelretch_bot, asst
from ..dB._core import LIST, LOADED
from ..version import __version__, zelretch_version
from ._supporter import SUDO_M, owner_and_sudos
from ._wrappers import eod

LOGS = logging.getLogger("Zelretch.decorators")


def compile_pattern(data: str, hndlr: str) -> re.Pattern:
    """Compile *data* into a regex anchored at the start by *hndlr*."""
    if not data:
        return re.compile("^$")
    if data.startswith("^"):
        data = data[1:]
    if data.startswith("."):
        data = data[1:]
    if hndlr in (" ", "NO_HNDLR"):
        return re.compile("^" + data)
    return re.compile("\\" + hndlr + data)


def _build_kurigram_filter(pattern: str, hndlr: str):
    """Translate an Ultroid-style pattern into a Kurigram ``filters`` object."""
    if not _K:
        return None
    # Kurigram's filters.command expects a command name (no prefix); the
    # prefix is supplied via ``prefixes=``. We support the original Ultroid
    # regex-style patterns by using ``filters.regex`` instead.
    regex = compile_pattern(pattern or "", hndlr)
    return filters.regex(regex)


def zelretch_cmd(
    pattern: Optional[str] = None,
    manager: bool = False,
    zelretch_bot: Any = zelretch_bot,
    asst: Any = asst,
    **kwargs: Any,
) -> Callable[[Callable], Callable]:
    """Register a Kurigram message handler.

    Parameters
    ----------
    pattern:
        Ultroid-style command pattern (e.g. ``"ping$"``). May include a
        capture group (e.g. ``"wiki (.*)"``).
    manager:
        When True, also register the handler against the assistant bot so
        group admins can invoke it via ``/cmd``.
    owner_only, groups_only, admins_only, fullsudo, only_devs:
        Standard Ultroid access-control flags.
    """
    owner_only = kwargs.get("owner_only", False)
    groups_only = kwargs.get("groups_only", False)
    admins_only = kwargs.get("admins_only", False)
    fullsudo = kwargs.get("fullsudo", False)
    only_devs = kwargs.get("only_devs", False)

    def decor(callback: Callable) -> Callable:
        async def wrapper(event: Any) -> None:
            # Command logging (preserved from Ultroid).
            if udB and udB.get_key("COMMAND_LOGGER"):
                user_id = getattr(event.from_user, "id", None) if event else None
                chat_id = getattr(event.chat, "id", None) if event else None
                cmd_text = getattr(event, "text", "") or ""
                LOGS.info(f"Command '{cmd_text[:40]}' by {user_id} in chat {chat_id}")
                log_channel = udB.get_key("LOG_CHANNEL")
                if log_channel and asst:
                    try:
                        await asst.send_message(
                            log_channel,
                            f"Command `{cmd_text[:40]}` executed by `{user_id}` in `{chat_id}`",
                        )
                    except Exception as e:
                        LOGS.warning(f"Could not post command log: {e}")

            # Owner / sudo enforcement (only meaningful for incoming events).
            is_outgoing = (
                event
                and event.from_user
                and zelretch_bot
                and event.from_user.id == getattr(zelretch_bot, "uid", 0)
            )
            if not is_outgoing:
                if owner_only:
                    return
                sender_id = getattr(event.from_user, "id", 0) if event.from_user else 0
                if sender_id and sender_id not in owner_and_sudos():
                    return
                if sender_id and sender_id in _ignore_eval:
                    return await eod(event, "You are blocked from using Zelretch.")
                if fullsudo and sender_id and sender_id not in SUDO_M.fullsudos:
                    return await eod(event, "Full-sudo only.", time=15)

            # Chat-type enforcement.
            chat = getattr(event, "chat", None)
            if chat and hasattr(chat, "title"):
                title = (chat.title or "").lower()
                if "#noub" in title and not getattr(chat, "is_admin", False):
                    if event.from_user and event.from_user.id not in owner_and_sudos():
                        return
            if chat and getattr(chat, "type", None) == "private" and (groups_only or admins_only):
                return await eod(event, "This command works only in groups.")
            if admins_only:
                from ..fns.admins import admin_check
                if not await admin_check(event):
                    return await eod(event, "Admins only.")
            if only_devs and not (udB and udB.get_key("I_DEV")):
                return await eod(event, f"Developer-only command. Use `{HNDLR}help`.", time=10)

            # Run the callback, catching every Ultroid-known error.
            try:
                await callback(event)
            except FloodWait as fwerr:
                if asst and udB and udB.get_key("LOG_CHANNEL"):
                    try:
                        await asst.send_message(
                            udB.get_key("LOG_CHANNEL"),
                            f"FloodWait: sleeping {fwerr.value + 10}s",
                        )
                    except Exception:
                        pass
                if zelretch_bot:
                    try:
                        await zelretch_bot.disconnect()
                    except Exception:
                        pass
                import asyncio
                await asyncio.sleep(fwerr.value + 10)
                if zelretch_bot:
                    try:
                        await zelretch_bot.connect()
                    except Exception:
                        pass
                return
            except ChatSendInlineForbidden:
                return await eod(event, "Inline locked in this chat.")
            except (ChatSendMediaForbidden, ChatSendStickersForbidden):
                return await eod(event, "Media locked in this chat.")
            except (BotInlineDisabled, UserIsBot):
                return await eod(event, "Inline mode is disabled for the assistant bot.")
            except (MessageIdInvalid, MessageNotModified, MessageDeleteForbidden) as er:
                LOGS.info(f"Benign message error: {er}")
            except AuthKeyDuplicated:
                LOGS.critical("Session expired - please re-generate via the setup wizard.")
                if asst and udB and udB.get_key("LOG_CHANNEL"):
                    try:
                        await asst.send_message(
                            udB.get_key("LOG_CHANNEL"),
                            "Session string expired. Re-run the setup wizard.",
                        )
                    except Exception:
                        pass
                sys.exit(1)
            except Exception as e:
                LOGS.exception(e)
                _report_crash(event, e)

        # ----------------------------------------------------------------
        # Register the wrapped callback on the appropriate clients.
        # ----------------------------------------------------------------
        flt = _build_kurigram_filter(pattern or "", HNDLR)
        if flt is not None and zelretch_bot is not None:
            try:
                zelretch_bot.add_message_handler(wrapper, flt)
            except Exception as er:
                LOGS.warning(f"Could not attach handler to userbot: {er}")

        # Sudo handler with SUDO_HNDLR (if different from HNDLR).
        if SUDO_M.should_allow_sudo and SUDO_HNDLR != HNDLR and pattern:
            sudo_flt = _build_kurigram_filter(pattern, SUDO_HNDLR)
            if sudo_flt is not None and zelretch_bot is not None:
                try:
                    zelretch_bot.add_message_handler(wrapper, sudo_flt)
                except Exception:
                    pass

        # Manager mode (assistant bot, / prefix).
        if manager and asst is not None and pattern:
            mgr_flt = _build_kurigram_filter(pattern, "/")
            if mgr_flt is not None:
                try:
                    asst.add_message_handler(wrapper, mgr_flt)
                except Exception:
                    pass

        # Record the pattern in LIST for the help system.
        file = Path(inspect.stack()[1].filename)
        stem = file.stem
        if "addons/" in str(file) or "Zelretch-Addons" in str(file):
            if LOADED.get(stem):
                LOADED[stem].append(wrapper)
            else:
                LOADED[stem] = [wrapper]
        if pattern:
            if LIST.get(stem):
                LIST[stem].append(pattern)
            else:
                LIST[stem] = [pattern]
        return wrapper

    return decor


def _report_crash(event: Any, exc: Exception) -> None:
    """Build a crash-log message and try to post it to the log channel."""
    if not (udB and asst and udB.get_key("LOG_CHANNEL")):
        return
    try:
        date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        text = (
            "**Zelretch Client Error**\n\n"
            f"**Version:** `{zelretch_version}` / `{__version__}`\n"
            f"**Date:** `{date}`\n"
            f"**Chat:** `{getattr(event.chat, 'id', '?')}`\n"
            f"**Sender:** `{getattr(event.from_user, 'id', '?')}`\n\n"
            f"**Trigger:**\n```\n{(event.text or '')[:1000]}\n```\n\n"
            f"**Traceback:**\n```\n{traceback.format_exc()[-1500:]}\n```"
        )
        if len(text) > 4096:
            with BytesIO(text.encode()) as f:
                f.name = "zelretch-crash.log"
                asst.send_document(udB.get_key("LOG_CHANNEL"), f)
        else:
            asst.send_message(udB.get_key("LOG_CHANNEL"), text)
    except Exception as er:
        LOGS.info(f"Crash report could not be sent: {er}")
