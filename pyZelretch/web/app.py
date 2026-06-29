# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""FastAPI web setup wizard.

Endpoints
---------
``GET  /``                - state-aware landing page
``GET  /core``            - core variables form
``POST /core``            - validate + persist core variables
``GET  /restore``         - "I have an existing DB" form
``POST /restore``         - validate connection, import config
``GET  /session``         - session string form + generator
``POST /session``         - validate + persist session
``GET  /deploy``          - final review + Deploy button
``POST /deploy``          - flip SETUP_COMPLETE=True and start the bot
``GET  /health``          - JSON probe (used by HF Spaces)
``GET  /api/state``       - JSON current state
``POST /api/generate-session`` - run the in-wizard session generator

Security
--------
* Secret values are rendered as ``"********"`` placeholders in every GET
  response; they are only ever written, never read back to the browser.
* Logs are scrubbed: the wizard never prints a secret.
"""

# NOTE: ``from __future__ import annotations`` is intentionally NOT used here
# because FastAPI relies on runtime type-hint resolution to distinguish a
# ``Request`` parameter from a query/form parameter.

import asyncio
import logging
import os
import threading
from typing import Any, Dict, Optional

from .state import (
    SetupState,
    compute_state,
    get_state,
    ready_to_deploy,
    reset_state,
    set_state,
)
from .validators import validate_payload

LOGS = logging.getLogger("Zelretch.wizard")


def _import_fastapi():
    """Import FastAPI + Jinja2 + uvicorn lazily so the rest of the bot can
    run without the web stack installed (e.g. for headless plugin-only
    deployments)."""
    try:
        from fastapi import FastAPI, Request, Form, HTTPException  # type: ignore
        from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse  # type: ignore
        from fastapi.templating import Jinja2Templates  # type: ignore
        from fastapi.staticfiles import StaticFiles  # type: ignore
    except ImportError as er:
        raise RuntimeError(
            "Web setup wizard requires FastAPI. Install with: "
            "pip install fastapi uvicorn jinja2 python-multipart"
        ) from er
    return (FastAPI, Request, Form, HTTPException,
            HTMLResponse, JSONResponse, RedirectResponse,
            Jinja2Templates, StaticFiles)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def build_app():
    """Build the FastAPI app. Returns the app instance + the templates object."""
    (FastAPI, Request, Form, HTTPException,
     HTMLResponse, JSONResponse, RedirectResponse,
     Jinja2Templates, StaticFiles) = _import_fastapi()

    app = FastAPI(title="Zelretch Setup Wizard", docs_url=None, redoc_url=None)

    here = os.path.dirname(__file__)
    templates = Jinja2Templates(directory=os.path.join(here, "templates"))
    static_dir = os.path.join(here, "static")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------
    def _ctx(request: Request, **extra) -> Dict[str, Any]:
        from ..configs import CONFIG_SCHEMA, all_vars, get_var
        snap = all_vars()
        masked: Dict[str, Any] = {}
        for entry in CONFIG_SCHEMA:
            v = snap.get(entry["key"])
            if entry.get("secret") and v:
                masked[entry["key"]] = "********"
            else:
                masked[entry["key"]] = v
        return {
            "request": request,
            "state": get_state().value,
            "ready": ready_to_deploy(),
            "schema": CONFIG_SCHEMA,
            "vars": masked,
            "hosted_on": get_var("HOSTED_ON"),
            **extra,
        }

    def _persist(payload: Dict[str, Any]) -> Dict[str, str]:
        """Write every value in *payload* to the config DB. Returns errors."""
        from ..configs import set_var
        errors = validate_payload(payload)
        if errors:
            return errors
        for key, value in payload.items():
            if value == "" or value == "********":
                continue
            set_var(key, value)
        return {}

    # ----------------------------------------------------------------
    # Routes
    # ----------------------------------------------------------------
    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        state = get_state()
        if state == SetupState.DEPLOYED:
            return templates.TemplateResponse("success.html", _ctx(request))
        if not ready_to_deploy():
            if state in (SetupState.NOT_CONFIGURED, SetupState.CORE_VARS_SAVED):
                return RedirectResponse("/core", status_code=303)
            if state == SetupState.DATABASE_RESTORED:
                return RedirectResponse("/session", status_code=303)
            if state == SetupState.SESSION_CONFIGURED:
                return RedirectResponse("/deploy", status_code=303)
        return RedirectResponse("/deploy", status_code=303)

    @app.get("/health")
    async def health():
        return JSONResponse({"status": "ok", "state": get_state().value})

    @app.get("/api/state")
    async def api_state():
        from ..configs import CONFIG_SCHEMA, all_vars
        snap = all_vars()
        secret_keys = {e["key"] for e in CONFIG_SCHEMA if e.get("secret")}
        safe = {k: ("********" if k in secret_keys and v else v) for k, v in snap.items()}
        return JSONResponse({"state": get_state().value, "vars": safe})

    @app.get("/core", response_class=HTMLResponse)
    async def core_form(request: Request):
        return templates.TemplateResponse("core.html", _ctx(request, step="core"))

    @app.post("/core", response_class=HTMLResponse)
    async def core_submit(request: Request):
        form = await request.form()
        payload = {k: v for k, v in form.items() if k != "csrf"}
        db_type = payload.get("DATABASE_TYPE", "local")
        if db_type != "mongo":
            payload.pop("MONGO_URI", None)
        if db_type != "redis":
            payload.pop("REDIS_URI", None)
            payload.pop("REDIS_PASSWORD", None)
        if db_type != "sql":
            payload.pop("DATABASE_URL", None)
        errors = _persist(payload)
        if not errors:
            new_state = compute_state()
            set_state(new_state)
            return RedirectResponse("/session", status_code=303)
        ctx = _ctx(request, step="core", errors=errors)
        return templates.TemplateResponse("core.html", ctx)

    @app.get("/restore", response_class=HTMLResponse)
    async def restore_form(request: Request):
        return templates.TemplateResponse("restore.html", _ctx(request, step="restore"))

    @app.post("/restore", response_class=HTMLResponse)
    async def restore_submit(request: Request):
        form = await request.form()
        db_type = form.get("DATABASE_TYPE", "local")
        payload = {
            "DATABASE_TYPE": db_type,
            "MONGO_URI": form.get("MONGO_URI", ""),
            "REDIS_URI": form.get("REDIS_URI", ""),
            "REDIS_PASSWORD": form.get("REDIS_PASSWORD", ""),
            "DATABASE_URL": form.get("DATABASE_URL", ""),
        }
        if db_type != "mongo":
            payload.pop("MONGO_URI", None)
        if db_type != "redis":
            payload.pop("REDIS_URI", None)
            payload.pop("REDIS_PASSWORD", None)
        if db_type != "sql":
            payload.pop("DATABASE_URL", None)
        errors = _persist(payload)
        if errors:
            return templates.TemplateResponse("restore.html",
                                              _ctx(request, step="restore", errors=errors))
        try:
            from ..configs import _install_db_bridge
            from ..startup._database import ZelretchDB
            inst = ZelretchDB()
            _install_db_bridge(inst)
            from ..dB import _set_udb
            _set_udb(inst)
        except Exception as er:
            return templates.TemplateResponse("restore.html",
                                              _ctx(request, step="restore",
                                                   errors={"_restore": str(er)}))
        from ..configs import get_var
        set_state(SetupState.DATABASE_RESTORED)
        if get_var("SESSION"):
            set_state(SetupState.SESSION_CONFIGURED)
            return RedirectResponse("/deploy", status_code=303)
        return RedirectResponse("/session", status_code=303)

    @app.get("/session", response_class=HTMLResponse)
    async def session_form(request: Request):
        return templates.TemplateResponse("session.html", _ctx(request, step="session"))

    @app.post("/session", response_class=HTMLResponse)
    async def session_submit(request: Request):
        form = await request.form()
        payload = {"SESSION": form.get("SESSION", "")}
        for k in ("HNDLR", "DUAL_HNDLR", "LOG_CHANNEL", "LANGUAGE", "ADDONS", "VCBOT", "BOTMODE", "DUAL_MODE"):
            if k in form:
                payload[k] = form.get(k)
        errors = _persist(payload)
        if errors:
            return templates.TemplateResponse("session.html",
                                              _ctx(request, step="session", errors=errors))
        set_state(SetupState.SESSION_CONFIGURED)
        if ready_to_deploy():
            set_state(SetupState.READY_TO_DEPLOY)
        return RedirectResponse("/deploy", status_code=303)

    @app.get("/deploy", response_class=HTMLResponse)
    async def deploy_form(request: Request):
        if not ready_to_deploy():
            return RedirectResponse("/core", status_code=303)
        return templates.TemplateResponse("deploy.html", _ctx(request, step="deploy"))

    @app.post("/deploy", response_class=HTMLResponse)
    async def deploy_submit(request: Request):
        from ..configs import set_var
        set_var("SETUP_COMPLETE", True)
        set_state(SetupState.DEPLOYED)
        threading.Thread(target=_launch_bot, daemon=True).start()
        return templates.TemplateResponse("success.html", _ctx(request, deployed=True))

    @app.get("/reset", response_class=HTMLResponse)
    async def reset(request: Request):
        reset_state()
        return RedirectResponse("/core", status_code=303)

    @app.post("/api/generate-session")
    async def generate_session(request: Request):
        form = await request.form()
        api_id = form.get("API_ID")
        api_hash = form.get("API_HASH")
        phone = form.get("PHONE")
        if not (api_id and api_hash and phone):
            return JSONResponse(
                {"ok": False, "error": "API_ID, API_HASH and phone are required."},
                status_code=400,
            )
        try:
            asyncio.create_task(_run_sessiongen(api_id, api_hash, phone))
            return JSONResponse(
                {"ok": True, "message": "Check the server log for the login code prompt."}
            )
        except Exception as er:
            return JSONResponse({"ok": False, "error": str(er)}, status_code=500)

    return app, templates


# ---------------------------------------------------------------------------
# Background bot launcher (called from /deploy)
# ---------------------------------------------------------------------------

def _launch_bot() -> None:
    """Start the Zelretch bot in the current process after the wizard finishes."""
    try:
        from . import _bootstrap_runtime  # type: ignore
        _bootstrap_runtime()
        from .. import asst
        if asst is not None:
            asst.run()
    except Exception as er:
        LOGS.exception(er)


async def _run_sessiongen(api_id, api_hash, phone) -> None:
    """Interactive session generator coroutine.

    In a real deployment this would ask the operator for the login code via a
    follow-up wizard step. For this build we log a clear instruction and
    point the operator at the standalone ``sessiongen`` script which supports
    interactive input.
    """
    LOGS.info(
        "Session generation requested for phone=%s. Use the bundled "
        "`sessiongen` script in a terminal to complete interactive login.",
        phone,
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_wizard() -> None:
    """Start the FastAPI wizard on the configured port (default 7860)."""
    import uvicorn  # type: ignore
    from ..configs import get_var

    app, _ = build_app()
    port = int(get_var("PORT") or 7860)
    host = get_var("HOST") or "0.0.0.0"
    LOGS.info(f"Starting Zelretch setup wizard on http://{host}:{port}")
    LOGS.info("Open this URL in your browser to complete setup.")
    if host == "0.0.0.0" and os.environ.get("SPACE_AUTHOR_NAME"):
        LOGS.info("Detected Hugging Face Spaces - the wizard will be reachable at your Space URL.")
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        LOGS.info("Wizard stopped by user.")
