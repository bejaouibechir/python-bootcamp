# [V4 - Threading] Service de surveillance en arrière-plan — inchangé en V6.

import threading
import queue
import time
from datetime import datetime


class SurveillanceService:
    """
    Surveille en continu les ruptures de stock dans un thread dédié.

    Concepts threading : Thread daemon, Event, Lock, Queue.
    """

    def __init__(self, stock_service, intervalle: int = 30):
        self._stock        = stock_service
        self._intervalle   = max(5, int(intervalle))
        self._stop_event   = threading.Event()
        self._lock         = threading.Lock()
        self._file_alertes : queue.Queue = queue.Queue()
        self._historique   : list[dict]  = []
        self._thread       : threading.Thread | None = None

    def demarrer(self) -> None:
        if self.est_actif:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._boucle_surveillance,
            name="SurveillanceStock",
            daemon=True,
        )
        self._thread.start()

    def arreter(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def forcer_verification(self) -> None:
        t = threading.Thread(target=self._verifier_alertes, name="VerifImmediate", daemon=True)
        t.start()

    def _boucle_surveillance(self) -> None:
        while not self._stop_event.is_set():
            self._verifier_alertes()
            self._stop_event.wait(timeout=self._intervalle)

    def _verifier_alertes(self) -> None:
        with self._lock:
            produits_alerte = self._stock.produits_en_alerte()
        if not produits_alerte:
            return
        alerte = {
            "timestamp": datetime.now().isoformat(),
            "produits" : produits_alerte,
            "count"    : len(produits_alerte),
        }
        self._file_alertes.put(alerte)
        with self._lock:
            self._historique.append(alerte)

    def lire_alertes(self) -> list[dict]:
        resultats = []
        try:
            while True:
                resultats.append(self._file_alertes.get_nowait())
        except queue.Empty:
            pass
        return resultats

    def get_historique(self) -> list[dict]:
        with self._lock:
            return list(self._historique)

    def vider_historique(self) -> None:
        with self._lock:
            self._historique.clear()
        try:
            while True:
                self._file_alertes.get_nowait()
        except queue.Empty:
            pass

    @property
    def est_actif(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def intervalle(self) -> int:
        return self._intervalle

    @intervalle.setter
    def intervalle(self, valeur: int) -> None:
        with self._lock:
            self._intervalle = max(5, int(valeur))

    @property
    def nb_alertes_totales(self) -> int:
        with self._lock:
            return len(self._historique)
