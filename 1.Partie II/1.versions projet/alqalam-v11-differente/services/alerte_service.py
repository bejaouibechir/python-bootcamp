"""Service de surveillance des alertes en thread de fond."""

from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)


class AlerteService(threading.Thread):
    """Thread daemon qui sonde le stock et remonte les ruptures."""

    def __init__(self, stock_service, intervalle: int = 30):
        super().__init__(daemon=True, name="AlerteService")
        self.stock = stock_service
        self.intervalle = intervalle
        self._actif = threading.Event()
        self._actif.set()
        self._callback = None

    def on_alerte(self, callback):
        self._callback = callback
        return self

    def run(self):
        logger.info("Surveillance alertes démarrée")
        while self._actif.is_set():
            try:
                alertes = self.stock.produits_en_alerte()
                if alertes and self._callback:
                    self._callback(alertes)
            except Exception as exc:
                logger.error("Erreur thread alerte: %s", exc)
            time.sleep(self.intervalle)

    def arreter(self):
        self._actif.clear()
        logger.info("Surveillance alertes arrêtée")
