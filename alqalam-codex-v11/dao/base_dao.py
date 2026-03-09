"""Classe de base DAO avec gestion transactionnelle."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from dao.db_factory import get_connection

logger = logging.getLogger(__name__)


class BaseDAO:
    """Offre une session SQL transactionnelle simple."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = db_path

    @contextmanager
    def _session(self):
        conn = get_connection(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.error("Rollback SQL: %s", exc)
            raise
        finally:
            conn.close()
