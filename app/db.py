"""Db2 for i connection helper (pyodbc)."""
import os
from contextlib import contextmanager

import pyodbc


def get_dsn() -> str:
    dsn = os.environ.get("DB_DSN")
    if not dsn:
        raise RuntimeError("DB_DSN environment variable is not set")
    return dsn


@contextmanager
def get_connection():
    """Open a connection, commit on success, roll back on error, always close.

    Note: a new ODBC connection starts a server job on IBM i, so this is
    intentionally simple. Add connection pooling before any real load.
    """
    conn = pyodbc.connect(get_dsn(), autocommit=False, timeout=10)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
