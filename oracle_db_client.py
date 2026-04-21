"""Oracle Database helper for thick mode connections via YAML settings."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import oracledb
import yaml


class OracleDBClient:
    """Simple Oracle DB client with thick mode initialization and basic queries."""

    def __init__(self, config_file: str = "config.yaml") -> None:
        self.config = self._load_config(config_file)

        self.user = self._require_config("ORACLE_USER")
        self.password = self._require_config("ORACLE_PASSWORD")
        self.dsn = self._build_dsn()
        self.lib_dir = self._require_config("ORACLE_CLIENT_LIB_DIR")
        self.config_dir = self._optional_config("ORACLE_CLIENT_CONFIG_DIR")
        self.connection: oracledb.Connection | None = None

        self._init_thick_mode()

    def __enter__(self) -> "OracleDBClient":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    @staticmethod
    def _load_config(config_file: str) -> dict[str, Any]:
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}

        if not isinstance(config, dict):
            raise ValueError("Config file must contain a YAML mapping at the top level.")

        return config

    def _require_config(self, name: str) -> str:
        value = self.config.get(name)
        if not value:
            raise ValueError(f"Required config value is missing: {name}")
        return str(value)

    def _optional_config(self, name: str) -> str | None:
        value = self.config.get(name)
        if value in (None, ""):
            return None
        return str(value)

    def _build_dsn(self) -> str:
        dsn = self._optional_config("ORACLE_DSN")
        if dsn:
            return dsn

        host = self._require_config("ORACLE_HOST")
        port = int(self.config.get("ORACLE_PORT", 1521))
        service_name = self._optional_config("ORACLE_SERVICE_NAME")
        sid = self._optional_config("ORACLE_SID")

        if service_name:
            return oracledb.makedsn(host=host, port=port, service_name=service_name)

        if sid:
            return oracledb.makedsn(host=host, port=port, sid=sid)

        raise ValueError(
            "Set ORACLE_DSN or provide ORACLE_HOST with ORACLE_SERVICE_NAME or ORACLE_SID."
        )

    def _init_thick_mode(self) -> None:
        try:
            if self.config_dir:
                oracledb.init_oracle_client(
                    lib_dir=self.lib_dir,
                    config_dir=self.config_dir,
                )
            else:
                oracledb.init_oracle_client(lib_dir=self.lib_dir)
        except oracledb.ProgrammingError as exc:
            # The Oracle client can only be initialized once per process.
            if "DPY-2017" not in str(exc):
                raise

    def connect(self) -> oracledb.Connection:
        if self.connection is None or not self.connection.is_healthy():
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn,
            )
        return self.connection

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    @staticmethod
    def _execute(
        cursor: oracledb.Cursor,
        query: str,
        params: dict[str, Any] | list[Any] | tuple[Any, ...] | None = None,
    ) -> None:
        if params is None:
            cursor.execute(query)
            return
        cursor.execute(query, params)

    @contextmanager
    def cursor(self) -> Iterator[oracledb.Cursor]:
        connection = self.connect()
        cursor = connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def select(
        self,
        query: str,
        params: dict[str, Any] | list[Any] | tuple[Any, ...] | None = None,
    ) -> list[dict[str, Any]]:
        with self.cursor() as cursor:
            self._execute(cursor, query, params)
            columns = [column[0] for column in cursor.description or []]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    def execute_dml(
        self,
        query: str,
        params: dict[str, Any] | list[Any] | tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> int:
        with self.cursor() as cursor:
            self._execute(cursor, query, params)
            affected_rows = cursor.rowcount
            if auto_commit:
                self.connect().commit()
            return affected_rows

    def test_connection(self) -> bool:
        with self.cursor() as cursor:
            cursor.execute("SELECT 1 FROM DUAL")
            return cursor.fetchone() is not None

    def insert(
        self,
        query: str,
        params: dict[str, Any] | list[Any] | tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> int:
        return self.execute_dml(query, params=params, auto_commit=auto_commit)

    def update(
        self,
        query: str,
        params: dict[str, Any] | list[Any] | tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> int:
        return self.execute_dml(query, params=params, auto_commit=auto_commit)

    def delete(
        self,
        query: str,
        params: dict[str, Any] | list[Any] | tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> int:
        return self.execute_dml(query, params=params, auto_commit=auto_commit)

    def commit(self) -> None:
        self.connect().commit()

    def rollback(self) -> None:
        self.connect().rollback()


if __name__ == "__main__":
    client = OracleDBClient()

    try:
        users = client.select("SELECT * FROM users WHERE ROWNUM <= :limit", {"limit": 5})
        print(users)
    finally:
        client.close()
