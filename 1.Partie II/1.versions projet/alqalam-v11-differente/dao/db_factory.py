"""Fabrique de connexion base de données."""

import sqlite3
from pathlib import Path

from config import DB_ENGINE, DB_PATH


def get_connection(db_path: str | Path | None = None):
    """Retourne une connexion DB selon l'engine configuré."""
    if DB_ENGINE != "sqlite":
        raise NotImplementedError("Cette version V11 est livrée avec SQLite")
    path = str(db_path or DB_PATH)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
