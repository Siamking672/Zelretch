<p align="center">
  <h1 align="center"><b>Zelretch - UserBot</b></h1>
</p>

<b>A stable, pluggable Telegram userbot based on Kurigram, with a built-in web setup wizard and one-command deployment. Rewritten from Ultroid.</b>

[![Zelretch](https://img.shields.io/badge/Zelretch-v1.0.0-7c5cff)](#)
[![Python](https://img.shields.io/badge/Python-v3.10+-blue)](https://www.python.org/)
[![Kurigram](https://img.shields.io/badge/Kurigram-latest-4ec3ff)](https://github.com/KurimuzonAkiba/kurigram)
[![License](https://img.shields.io/badge/License-AGPLv3-blue)](LICENSE)
[![Based on Ultroid](https://img.shields.io/badge/Based%20on-Ultroid-critical)](https://github.com/TeamUltroid/Ultroid)

---

# What is Zelretch?

Zelretch is a complete rewrite of [Ultroid](https://github.com/TeamUltroid/Ultroid)
that swaps the original Telethon client for [Kurigram](https://github.com/KurimuzonAkiba/kurigram)
(a maintained Pyrogram v2 fork) and replaces the brittle `.env`-driven
configuration model with a **database-backed, web-wizard-guided setup flow**.

The project ships as two separate deliverables:

| Repo | Purpose |
|------|---------|
| **Zelretch-Main** (this repo) | Core bot runtime, setup wizard, deployment engine, database integration, session handling, plugin loader. |
| **Zelretch-Addons** | Separate plugin/addon repository compatible with the Zelretch plugin loader. |

The two repos intentionally stay separate so the addon ecosystem can evolve
independently of the core.

---

# Key features

- **One-command deployment** - `python zelretch.py` auto-installs dependencies, then either starts the web wizard or boots the bot.
- **Web setup wizard** - FastAPI app on port 7860 (the HF Spaces default) that collects every required variable through a guided browser interface.
- **Database-based configuration** - every setting lives in your chosen DB (MongoDB / Redis / PostgreSQL / local JSON), not in `.env`. Re-deployments restore automatically when the same DB is supplied.
- **Hugging Face Spaces support** - dedicated `README HF.md`, port 7860 binding, Dockerfile that works on HF Spaces without modification.
- **Resumable setup state** - the wizard tracks six states (`NOT_CONFIGURED`, `CORE_VARS_SAVED`, `DATABASE_RESTORED`, `SESSION_CONFIGURED`, `READY_TO_DEPLOY`, `DEPLOYED`) and resumes cleanly after an interrupt.
- **Input validation** - every form field is validated server-side; the **Deploy** button is locked until every required value passes.
- **Secure secret handling** - API hashes, bot tokens, session strings and DB URLs are never echoed in logs, never sent back to the browser as plain text, never written to disk in plaintext.
- **Kurigram-compatible plugin loader** - drop a plugin in `plugins/` (or `addons/`) and it auto-loads; `.load`, `.unload`, `.reload`, `.update` commands for live management.
- **Preserved feature parity** - AFK, sudo, notes, snips, filters, PM-permit, greetings, admintools, plugin manager, ping, alive, help, info, ... all ported.
- **Multilingual strings** - YAML-based i18n (English bundled; community translations welcome).

---

# Quick start

## Option 1 - One command (recommended)

```bash
git clone https://github.com/TeamUltroid/Ultroid.git Zelretch
cd Zelretch
python zelretch.py
```

That's it. The launcher:

1. Ensures `pip` is available.
2. Installs everything in `requirements.txt` (and best-effort `optional-requirements.txt`).
3. Detects whether you have already completed setup (by reading `SETUP_COMPLETE` from the DB).
4. If not, launches the **web setup wizard** on `http://0.0.0.0:7860` - open it in your browser, fill in the three steps, click **Deploy**.
5. If yes, skips the wizard and boots the bot directly.

You **never** need to create a `.env` file. If one exists from a legacy Ultroid deployment, its values are imported into the DB on first run, then ignored.

## Option 2 - Docker

```bash
docker compose up -d
```

Then open `http://localhost:7860` to complete the setup wizard.

## Option 3 - Hugging Face Spaces

1. Create a new Space at <https://huggingface.co/new-space>, choose **Docker** as the SDK.
2. **Important:** the HF Spaces platform reads its metadata from a file called `README.md` at the repo root. To avoid clobbering the project README, the bundled `README_HF.md` contains the HF metadata. When pushing to a Space, **rename `README_HF.md` to `README.md`** (overwriting the project README) — or push every other file and use `README_HF.md` as the README content directly.
3. Upload every file from `Zelretch-Main.zip` to the Space repo (or push them via `git`).
4. The Space builds automatically and the wizard becomes reachable at your Space URL.
5. Complete the wizard in the browser; HF Spaces secrets are auto-imported if you set `ZELRETCH_API_ID`, `ZELRETCH_API_HASH`, etc. as Space secrets.

Voice-chat features (VCBOT) are auto-disabled on Hugging Face Spaces because the platform does not support outbound UDP.

## Option 4 - Termux (Android)

```bash
pkg update && pkg install python git ffmpeg
git clone https://github.com/TeamUltroid/Ultroid.git Zelretch
cd Zelretch
bash install-termux
```

---

# The setup wizard

The wizard has three steps plus an optional "restore" flow:

## Step 1 - Core variables (`/core`)

Collects:

- `API_ID` and `API_HASH` (from <https://my.telegram.org>)
- `BOT_TOKEN` (optional - enables dual-mode)
- `OWNER_ID` (auto-filled on first login if left blank)
- `DATABASE_TYPE` (one of `local`, `mongo`, `redis`, `sql`)
- The corresponding connection string for the chosen DB
- Deployment platform (`HOSTED_ON`) and optional Heroku credentials

Secret fields are masked in the UI as soon as they are saved.

## Step 1b - Restore existing deployment (`/restore`)

If you have previously deployed Zelretch and want to reuse the configuration,
enter your existing DB connection here. Zelretch connects, imports every
saved variable, and skips the rest of the wizard. If the restored DB already
contains a `SESSION`, you are taken straight to the Deploy step.

## Step 2 - Userbot session (`/session`)

Two ways to provide the Kurigram session string:

1. **Paste an existing session string** - generate one with the bundled `sessiongen` script (see below).
2. **Use the in-wizard generator** - enter your API credentials + phone number, then follow the prompts in the server log.

This step also collects runtime preferences: command handler, log channel ID,
language, addon loading flag, voice-chat flag, bot-mode flag, dual-mode flag.

## Step 3 - Deploy (`/deploy`)

Reviews every variable, highlights any missing required fields, and shows a
**Deploy Zelretch** button. The button is disabled until every required
value passes validation. Clicking it flips `SETUP_COMPLETE=True` and starts
the bot in a background thread.

---

# Generating a session string

The bundled `sessiongen` script is interactive. Run it in a terminal:

```bash
python sessiongen
```

You will be asked for:

1. API ID
2. API Hash
3. Phone number (international format)
4. Login code (sent to your Telegram)
5. 2FA password (if enabled)

The script then prints a long string - paste that into the wizard's **Session** step.

> The session string is the most sensitive credential in the deployment.
> Anyone with it can act as you on Telegram. Treat it like a password.

---

# Configuration storage

Zelretch reads every runtime value from the DB at call time via the
`Var` proxy (`from pyZelretch.configs import Var`). The schema is declared
in `pyZelretch/configs.py::CONFIG_SCHEMA` - the wizard iterates over this
list to build its forms.

| Category   | Keys                                                                |
|------------|---------------------------------------------------------------------|
| core       | `API_ID`, `API_HASH`, `BOT_TOKEN`, `OWNER_ID`                       |
| database   | `DATABASE_TYPE`, `MONGO_URI`, `REDIS_URI`, `REDIS_PASSWORD`, `DATABASE_URL` |
| session    | `SESSION`, `VC_SESSION`                                             |
| runtime    | `HNDLR`, `DUAL_HNDLR`, `LOG_CHANNEL`, `LANGUAGE`, `ADDONS`, `VCBOT`, `BOTMODE`, `DUAL_MODE` |
| deployment | `HOSTED_ON`, `HEROKU_APP_NAME`, `HEROKU_API`                        |
| advanced   | `PORT`, `HOST`, `SETUP_COMPLETE`                                    |

Use the `.getvar`, `.setvar`, `.delvar`, `.allvars` bot commands (owner
only) to inspect / mutate config at runtime.

---

# Plugin architecture

## Loading

The `pyZelretch.loader.Loader` class walks a folder, imports every `.py`
file, and lets the modules register handlers via `@zelretch_cmd(...)`. The
high-level `pyZelretch.startup.loader.load_other_plugins()` function loads:

1. `plugins/` - bundled core plugins.
2. `addons/` (if present, or `Zelretch-Addons/` if you cloned the addon repo next to the main one).
3. `assistant/manager/` (legacy Ultroid assistant modules - kept as no-ops in this build).

## Writing a plugin

A plugin is just a Python file with one or more `@zelretch_cmd`-decorated
coroutines:

```python
# plugins/hello.py
from pyZelretch import zelretch_cmd, eor

@zelretch_cmd(pattern="hello$")
async def hello(event):
    """• `.hello` - greet the chat."""
    await eor(event, "👋 Hello from Zelretch!")
```

Drop the file under `plugins/` (for core plugins) or `addons/` (for the
addon repo) and restart - or use `.load hello` to load it live.

## Plugin management commands

| Command             | Description                                       |
|---------------------|---------------------------------------------------|
| `.plugins`          | List currently-loaded core plugins and addons.    |
| `.load <name>`      | Load (or reload) a plugin by file stem.           |
| `.unload <name>`    | Remove a plugin's handlers from the active clients. |
| `.reload <name>`    | Unload + load.                                    |
| `.update`           | `git pull` + restart.                             |

---

# Project structure

```
Zelretch-Main/
├── README.md                      # this file
├── LICENSE                        # AGPLv3 (preserved from Ultroid)
├── CODE_OF_CONDUCT.md             # preserved
├── CONTRIBUTING.md                # preserved
├── README HF.md                   # Hugging Face Spaces metadata
├── README_HF.md                   # same file without a space in the name
├── requirements.txt               # core Python deps
├── optional-requirements.txt      # best-effort extras
├── Dockerfile                     # container build
├── docker-compose.yml             # local container runner
├── app.json                       # Heroku button config
├── heroku.yml                     # Heroku container manifest
├── okteto-pipeline.yml            # Okteto manifest
├── startup                        # bash one-command entry point
├── installer.sh                   # dependency installer
├── install-termux                 # Termux installer
├── sessiongen                     # interactive Kurigram session generator
├── zelretch.py                    # one-command launcher (auto-pip + run)
├── pyZelretch/                    # the framework
│   ├── __init__.py
│   ├── __main__.py                # `python -m pyZelretch`
│   ├── configs.py                 # DB-backed config manager + schema
│   ├── exceptions.py
│   ├── loader.py                  # generic filesystem plugin loader
│   ├── version.py
│   ├── _misc/
│   │   ├── _decorators.py         # @zelretch_cmd (Kurigram filters-based)
│   │   ├── _supporter.py          # sudo manager
│   │   ├── _wrappers.py           # eor / eod
│   │   └── _assistant.py
│   ├── dB/                        # database backends + per-feature helpers
│   │   ├── __init__.py
│   │   ├── _core.py
│   │   ├── base.py                # KeyManager
│   │   └── *.py                   # one file per feature (afk_db, notes_db, ...)
│   ├── fns/                       # async helpers
│   │   ├── helper.py              # bash(), time_formatter(), progress()
│   │   ├── admins.py
│   │   ├── info.py
│   │   ├── tools.py
│   │   ├── misc.py
│   │   ├── executor.py
│   │   ├── ytdl.py
│   │   └── gDrive.py
│   ├── startup/
│   │   ├── __init__.py
│   │   ├── BaseClient.py          # ZelretchClient(Kurigram.Client)
│   │   ├── _database.py           # MongoDB / Redis / SqlDB / LocalDB backends
│   │   ├── connections.py         # session validation + VC hook
│   │   ├── funcs.py               # autobot, customize, ready, WasItRestart
│   │   ├── loader.py              # load_other_plugins()
│   │   ├── utils.py
│   │   └── _extra.py
│   └── web/                       # FastAPI setup wizard
│       ├── __init__.py
│       ├── app.py                 # endpoints + runner
│       ├── state.py               # 6-state machine
│       ├── validators.py          # per-field + per-payload validation
│       ├── templates/             # Jinja2 HTML
│       └── static/style.css
├── plugins/                       # core plugins (each one is a Zelretch command set)
│   ├── __init__.py
│   ├── _zelretch.py               # .repo, .zelretch
│   ├── _help.py
│   ├── _pluginmgr.py              # .plugins, .load, .unload, .reload, .update
│   ├── _userlogs.py
│   ├── _chatactions.py
│   ├── core.py                    # .ping, .alive, .help, .id, .info, .uptime
│   ├── sudo.py                    # .sudo, .delsudo, .listsudo
│   ├── afk.py                     # .afk, .unafk + auto-responder
│   ├── tools.py                   # .echo, .upper, .lower, .reverse, .repeat, .tr
│   ├── misc.py                    # .whois, .chatinfo, .stats, .purge
│   ├── tag.py                     # .tagall
│   ├── admintools.py              # .kick, .ban, .unban, .promote, .demote, .pin
│   ├── notes.py                   # .note, .get, .notes, .delnote
│   ├── snips.py                   # .snip, .snips, .delsnip + auto-responder
│   ├── filter.py                  # .filter, .filters, .delfilter
│   ├── pmpermit.py                # .approve, .disapprove + auto-responder
│   ├── greetings.py               # .welcome, .goodbye + auto-responder
│   └── variables.py               # .getvar, .setvar, .delvar, .allvars
├── strings/                       # i18n
│   ├── __init__.py
│   └── strings/en.yml
├── resources/                     # fonts + assets
│   └── fonts/                     # TTF / OTF fonts used by image plugins
└── assistant/                     # legacy Ultroid assistant namespace (minimal)
```

---

# Migration from Ultroid

If you have an existing Ultroid deployment:

1. Keep your `MONGO_URI` / `REDIS_URI` / `DATABASE_URL` handy.
2. Drop `Zelretch-Main.zip` next to your old install (or clone fresh).
3. Run `python zelretch.py`.
4. The wizard launches - choose **Step 1b - Restore**.
5. Paste your existing DB connection.
6. Zelretch imports every saved key (including `SESSION`, `BOT_TOKEN`, `LOG_CHANNEL`, etc.) and skips to the Deploy step.
7. Click **Deploy Zelretch**.

Your existing Ultroid DB schema is unchanged - Zelretch uses the same table
/ collection names. The only breaking change is the client framework: if
your custom addons import `from telethon import ...` directly, they need to
be ported to Kurigram (`from kurigram import ...`). The `zelretch_cmd`
decorator abstracts 95% of the difference away.

---

# Credits

Zelretch is a rewrite of [Ultroid](https://github.com/TeamUltroid/Ultroid) by
[TeamUltroid](https://t.me/TeamUltroid). The original authors retain all
credit for the project's design, plugin catalogue and community:

- [@xditya](https://github.com/xditya)
- [@1danish-00](https://github.com/1danish-00)
- [@buddhhu](https://github.com/buddhhu)
- [@TechiError](https://github.com/TechiError)
- [@New-dev0](https://github.com/New-dev0)
- [@ArnabXD](https://github.com/ArnabXD)
- [@sppidy](https://github.com/sppidy)
- [@Atul-Kumar-Jena](https://github.com/Atul-Kumar-Jena)
- [@iAkashPattnaik](https://github.com/iAkashPattnaik) (SQL backend)

Additional credits:

- [Lonami](https://github.com/LonamiWebs) for [Telethon](https://github.com/LonamiWebs/Telethon) - the original framework Ultroid was built on.
- [KurimuzonAkiba](https://github.com/KurimuzonAkiba) for [Kurigram](https://github.com/KurimuzonAkiba/kurigram) - the maintained Pyrogram v2 fork Zelretch uses.
- [MarshalX](https://github.com/MarshalX) for [pyTgCalls](https://github.com/MarshalX/tgcalls).

---

# License

Zelretch is licensed under the [GNU Affero General Public License v3 or later](LICENSE),
inherited from the original Ultroid project. By using, modifying or
redistributing Zelretch you agree to the terms of that license - including
the requirement to publish the source code of any modified version that you
operate as a network service.

---

# Troubleshooting

| Symptom | Fix |
|---------|-----|
| Wizard does not start | Check `python zelretch.py` output - the wizard needs `fastapi`, `uvicorn`, `jinja2`, `python-multipart`. The launcher auto-installs them; if it can't, run `pip install -r requirements.txt` manually. |
| Wizard starts but `Deploy` button is locked | Every required field must pass validation. Open `/deploy` to see which fields are flagged `missing`. |
| Bot does not respond after Deploy | Check the server log for tracebacks - they are also posted to your `LOG_CHANNEL` if one was configured. |
| Session rejected | Re-generate with `python sessiongen`. Sessions are framework-specific - a Telethon session string will not work with Kurigram. |
| Want to switch databases | Hit `/reset` in the wizard, then run the Restore flow with the new DB. |
| Want to start over | Delete the DB or run the wizard at `/reset`. |

> Made with 💕 by the Zelretch maintainers, on top of Ultroid by [@TeamUltroid](https://t.me/TeamUltroid).
