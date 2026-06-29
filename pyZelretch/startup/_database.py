# Zelretch - UserBot
# Copyright (C) 2021-2026 TeamUltroid (original) / Zelretch Maintainers (rewrite)
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ > (original)
# Rewritten for Kurigram by the Zelretch project.
# Licensed under the GNU Affero General Public License v3 or later.

"""Database backend selection + base class.

The original Ultroid supported four backends (Redis, MongoDB, PostgreSQL and
a JSON-file local DB). Zelretch preserves all four so existing operators do
not need to migrate their data. The selection logic now lives entirely in
the configuration DB - see :mod:`pyZelretch.configs` for the schema.
"""

from __future__ import annotations

import ast
import logging
import os
import sys
from typing import Any, Iterable, List, Optional

LOGS = logging.getLogger("Zelretch.DB")


# ---------------------------------------------------------------------------
# Base class (shared by every backend)
# ---------------------------------------------------------------------------


class _BaseDatabase:
    """Common interface implemented by every backend.

    Subclasses must provide ``set``, ``get``, ``delete`` and ``keys``. The
    base class adds an in-process cache so repeated reads of the same key do
    not hit the network.
    """

    name: str = "Base"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._cache: dict = {}

    # ----------------------------- cache --------------------------------
    def get_key(self, key: str) -> Any:
        if key in self._cache:
            return self._cache[key]
        value = self._get_data(key)
        self._cache[key] = value
        return value

    def re_cache(self) -> None:
        self._cache.clear()
        for key in self.keys():
            self._cache[key] = self.get_key(key)

    def ping(self) -> bool:
        return True

    @property
    def usage(self) -> int:
        return 0

    def keys(self) -> List[str]:  # pragma: no cover - overridden
        return []

    # ----------------------------- writes -------------------------------
    def del_key(self, key: str) -> bool:
        self._cache.pop(key, None)
        self.delete(key)
        return True

    def _get_data(self, key: Optional[str] = None, data: Any = None) -> Any:
        if key:
            data = self.get(str(key))
        if data and isinstance(data, str):
            try:
                data = ast.literal_eval(data)
            except (ValueError, SyntaxError):
                pass
        return data

    def set_key(self, key: str, value: Any, cache_only: bool = False) -> Optional[bool]:
        value = self._get_data(data=value)
        self._cache[key] = value
        if cache_only:
            return None
        return self.set(str(key), str(value))

    def rename(self, key1: str, key2: str) -> int:
        data = self.get_key(key1)
        if data is None:
            return 1
        self.del_key(key1)
        self.set_key(key2, data)
        return 0

    # subclasses override these -----------------------------------------
    def set(self, key: str, value: str) -> bool:  # pragma: no cover
        raise NotImplementedError

    def get(self, key: str) -> Optional[str]:  # pragma: no cover
        raise NotImplementedError

    def delete(self, key: str) -> bool:  # pragma: no cover
        raise NotImplementedError

    def flushall(self) -> bool:  # pragma: no cover
        self._cache.clear()
        return True


# ---------------------------------------------------------------------------
# MongoDB
# ---------------------------------------------------------------------------


class MongoDB(_BaseDatabase):
    """PyMongo-backed store. Uses a single database with one collection per key."""

    name = "Mongo"

    def __init__(self, uri: str, dbname: str = "ZelretchDB") -> None:
        from pymongo import MongoClient
        self.dB = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.dB[dbname]
        super().__init__()

    def __repr__(self) -> str:
        return f"<Zelretch.MongoDB total_keys={len(self.keys())}>"

    @property
    def usage(self) -> int:
        try:
            return int(self.db.command("dbstats")["dataSize"])
        except Exception:
            return 0

    def ping(self) -> bool:
        try:
            return bool(self.dB.server_info())
        except Exception as er:
            LOGS.warning(f"Mongo ping failed: {er}")
            return False

    def keys(self) -> List[str]:
        try:
            return list(self.db.list_collection_names())
        except Exception:
            return []

    def set(self, key: str, value: str) -> bool:
        if key in self.keys():
            self.db[key].replace_one({"_id": key}, {"value": str(value)})
        else:
            self.db[key].insert_one({"_id": key, "value": str(value)})
        return True

    def delete(self, key: str) -> bool:
        self.db.drop_collection(key)
        return True

    def get(self, key: str) -> Optional[str]:
        doc = self.db[key].find_one({"_id": key})
        return doc["value"] if doc else None

    def flushall(self) -> bool:
        self.dB.drop_database("ZelretchDB")
        self._cache.clear()
        return True


# ---------------------------------------------------------------------------
# PostgreSQL (via psycopg2)
# ---------------------------------------------------------------------------

# Thanks to "Akash Pattnaik" / @BLUE-DEVIL1134 for the original Ultroid SQL
# implementation. Zelretch keeps the same schema ("Ultroid" table, one column
# per key) so existing deployments can be migrated as-is.


class SqlDB(_BaseDatabase):
    name = "SQL"

    def __init__(self, url: str) -> None:
        import psycopg2  # type: ignore
        self._url = url
        self._connection = None
        self._cursor = None
        try:
            self._connection = psycopg2.connect(dsn=url)
            self._connection.autocommit = True
            self._cursor = self._connection.cursor()
            self._cursor.execute(
                "CREATE TABLE IF NOT EXISTS Zelretch (zelretchCli varchar(70))"
            )
        except Exception as error:
            LOGS.exception(error)
            LOGS.error("Invalid SQL database URL.")
            if self._connection:
                self._connection.close()
            raise
        super().__init__()

    @property
    def usage(self) -> int:
        self._cursor.execute(
            "SELECT pg_size_pretty(pg_relation_size('Zelretch')) AS size"
        )
        return int(self._cursor.fetchall()[0][0].split()[0])

    def ping(self) -> bool:
        try:
            self._cursor.execute("SELECT 1")
            return True
        except Exception:
            return False

    def keys(self) -> List[str]:
        self._cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'zelretch'"
        )
        return [row[0] for row in self._cursor.fetchall()]

    def get(self, variable: str) -> Optional[str]:
        try:
            self._cursor.execute(f'SELECT "{variable}" FROM Zelretch')
        except Exception:
            return None
        data = self._cursor.fetchall()
        if not data:
            return None
        for row in data:
            if row and row[0]:
                return row[0]
        return None

    def set(self, key: str, value: str) -> bool:
        import psycopg2  # type: ignore
        try:
            self._cursor.execute(f'ALTER TABLE Zelretch DROP COLUMN IF EXISTS "{key}"')
        except (psycopg2.errors.UndefinedColumn, psycopg2.errors.SyntaxError):
            pass
        except Exception as er:
            LOGS.exception(er)
        self._cache[key] = value
        self._cursor.execute(f'ALTER TABLE Zelretch ADD COLUMN "{key}" TEXT')
        self._cursor.execute(
            f'INSERT INTO Zelretch ("{key}") VALUES (%s)', (str(value),)
        )
        return True

    def delete(self, key: str) -> bool:
        import psycopg2  # type: ignore
        try:
            self._cursor.execute(f'ALTER TABLE Zelretch DROP COLUMN "{key}"')
        except psycopg2.errors.UndefinedColumn:
            return False
        return True

    def flushall(self) -> bool:
        self._cache.clear()
        self._cursor.execute("DROP TABLE Zelretch")
        self._cursor.execute(
            "CREATE TABLE IF NOT EXISTS Zelretch (zelretchCli varchar(70))"
        )
        return True


# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------


class RedisDB(_BaseDatabase):
    name = "Redis"

    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        password: Optional[str] = None,
        platform: str = "",
        logger: logging.Logger = LOGS,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if host and ":" in host:
            spli_ = host.split(":")
            host = spli_[0]
            port = int(spli_[-1])
            if host.startswith("http"):
                logger.error("REDIS_URI must not start with http.")
                sys.exit()
        elif not host or not port:
            logger.error("Redis host/port not found.")
            sys.exit()
        from redis import Redis  # type: ignore
        kwargs["host"] = host
        kwargs["password"] = password
        kwargs["port"] = port
        # Qovery-specific discovery (kept for parity with Ultroid).
        if platform.lower() == "qovery" and not host:
            var = ""
            for v in os.environ:
                if v.startswith("QOVERY_REDIS_") and v.endswith("_HOST"):
                    var = v
            if var:
                hash_ = var.split("_", maxsplit=2)[1].split("_")[0]
                kwargs["host"] = os.environ.get(f"QOVERY_REDIS_{hash_}_HOST")
                kwargs["port"] = os.environ.get(f"QOVERY_REDIS_{hash_}_PORT")
                kwargs["password"] = os.environ.get(f"QOVERY_REDIS_{hash_}_PASSWORD")
        kwargs.setdefault("decode_responses", True)
        kwargs.setdefault("socket_timeout", 5)
        kwargs.setdefault("retry_on_timeout", True)
        self.db = Redis(**kwargs)
        self.set = self.db.set  # type: ignore[assignment]
        self.get = self.db.get  # type: ignore[assignment]
        self.keys = self.db.keys  # type: ignore[assignment]
        self.delete = self.db.delete  # type: ignore[assignment]
        super().__init__()

    def ping(self) -> bool:
        try:
            return bool(self.db.ping())
        except Exception as er:
            LOGS.warning(f"Redis ping failed: {er}")
            return False

    @property
    def usage(self) -> int:
        try:
            return sum(self.db.memory_usage(k) or 0 for k in self.keys())
        except Exception:
            return 0


# ---------------------------------------------------------------------------
# Local JSON file
# ---------------------------------------------------------------------------


class LocalDB(_BaseDatabase):
    name = "LocalDB"

    def __init__(self) -> None:
        try:
            from localdb import Database  # type: ignore
        except ImportError:
            LOGS.info("Installing 'localdb.json' for local JSON database.")
            os.system(f"{sys.executable} -m pip install -q localdb.json")
            from localdb import Database  # type: ignore
        self.db = Database("zelretch")
        self.get = self.db.get  # type: ignore[assignment]
        self.set = self.db.set  # type: ignore[assignment]
        self.delete = self.db.delete  # type: ignore[assignment]
        super().__init__()

    def keys(self) -> List[str]:
        return list(self._cache.keys())

    def __repr__(self) -> str:
        return f"<Zelretch.LocalDB total_keys={len(self.keys())}>"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def ZelretchDB():
    """Build the backend declared under ``DATABASE_TYPE`` in the config DB.

    Falls back to :class:`LocalDB` when nothing has been configured yet (so
    the setup wizard itself can use ``udB`` to persist its own state).
    """
    from ..configs import get_var, _install_db_bridge

    db_type = (get_var("DATABASE_TYPE") or "local").lower()
    try:
        if db_type == "mongo":
            uri = get_var("MONGO_URI")
            if not uri:
                raise RuntimeError("MONGO_URI is required when DATABASE_TYPE=mongo")
            inst = MongoDB(uri)
        elif db_type == "redis":
            host = get_var("REDIS_URI")
            password = get_var("REDIS_PASSWORD")
            if not host:
                raise RuntimeError("REDIS_URI is required when DATABASE_TYPE=redis")
            inst = RedisDB(host=host, password=password)
        elif db_type == "sql":
            url = get_var("DATABASE_URL")
            if not url:
                raise RuntimeError("DATABASE_URL is required when DATABASE_TYPE=sql")
            inst = SqlDB(url)
        else:
            inst = LocalDB()
    except Exception as err:
        LOGS.exception(err)
        LOGS.warning("Falling back to LocalDB - configuration will NOT survive a "
                     "container rebuild. Re-run the setup wizard with a real DB.")
        inst = LocalDB()

    # Wire the DB into the configs module so Var reads actually hit the DB.
    _install_db_bridge(inst)
    # Make the singleton importable via ``from pyZelretch.dB import udB``.
    from ..dB import _set_udb
    _set_udb(inst)
    return inst
