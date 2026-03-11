# [V4 - Threading] Service de surveillance en arrière-plan.
#
# Concepts threading illustrés dans ce fichier :
#
#  threading.Thread  → exécution parallèle sans bloquer l'UI
#  threading.Event   → signal d'arrêt propre (remplace un flag booléen brut)
#  threading.Lock    → verrou pour protéger les données partagées
#  queue.Queue       → canal thread-safe Thread → UI (pas de .get() bloquant côté UI)
#  thread daemon     → s'arrête automatiquement quand le programme principal se termine
#
# Flux général :
#   main thread (Tkinter)  ←──queue──  SurveillanceService._thread  (daemon)
#   App._poll_alertes() lit la queue via after() toutes les 500 ms (non bloquant).

import threading
import queue
import time
from datetime import datetime


class SurveillanceService:
    """
    Surveille en continu les ruptures de stock dans un thread dédié.

    Usage typique :
        svc = SurveillanceService(stock_service, intervalle=30)
        svc.demarrer()          # lance le thread daemon
        ...
        alertes = svc.lire_alertes()   # polling non-bloquant depuis l'UI
        ...
        svc.arreter()           # arrêt propre à la fermeture de l'app
    """

    def __init__(self, stock_service, intervalle: int = 30):
        self._stock        = stock_service
        self._intervalle   = max(5, int(intervalle))   # minimum 5 s

        # ── Primitives de synchronisation ─────────────────────────────────
        # threading.Event : objet partagé entre threads.
        #   .set()   → lève le drapeau (signal)
        #   .is_set()→ vérifie
        #   .wait(t) → bloque jusqu'à ce que le drapeau soit levé OU timeout
        self._stop_event = threading.Event()

        # threading.Lock : verrou d'exclusion mutuelle.
        #   with self._lock:  → acquiert le verrou, le relâche en sortie de bloc
        self._lock = threading.Lock()

        # queue.Queue : file thread-safe ; put() côté thread, get_nowait() côté UI
        self._file_alertes: queue.Queue = queue.Queue()

        # Historique (protégé par _lock car écrit depuis le thread de surveillance)
        self._historique: list[dict] = []

        # Référence au thread (None avant démarrage)
        self._thread: threading.Thread | None = None

    # ── Démarrage / Arrêt ─────────────────────────────────────────────────

    def demarrer(self) -> None:
        """
        Lance le thread de surveillance en arrière-plan.

        daemon=True : le thread s'arrête automatiquement si l'application
        principale se ferme — on n'a pas à le gérer si l'utilisateur force
        la fermeture (Alt+F4, kill, etc.).
        """
        if self.est_actif:
            return   # déjà en cours

        self._stop_event.clear()   # remet le drapeau à zéro

        self._thread = threading.Thread(
            target=self._boucle_surveillance,
            name="SurveillanceStock",   # nom visible dans les outils de debug
            daemon=True,                # [V4] thread daemon
        )
        self._thread.start()

    def arreter(self) -> None:
        """
        Arrête proprement le thread de surveillance.

        .set() réveille immédiatement le .wait() dans la boucle ;
        .join() attend que le thread ait fini avant de continuer.
        """
        self._stop_event.set()         # [V4] signal d'arrêt via Event
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)   # attente max 5 s

    def forcer_verification(self) -> None:
        """
        Lance une vérification immédiate dans un thread éphémère.
        Utile quand l'utilisateur clique sur "Vérifier maintenant".
        """
        t = threading.Thread(
            target=self._verifier_alertes,
            name="VerifImmediate",
            daemon=True,
        )
        t.start()

    # ── Boucle principale du thread ───────────────────────────────────────

    def _boucle_surveillance(self) -> None:
        """
        Corps du thread de surveillance.

        Cycle :
          1. Vérifier les alertes
          2. Attendre self._intervalle secondes  ← .wait() libère le CPU
          3. Répéter jusqu'au signal d'arrêt
        """
        while not self._stop_event.is_set():
            self._verifier_alertes()
            # [V4] Event.wait(timeout) : bloque le thread sans consommer de CPU.
            # Retourne immédiatement si _stop_event est levé (arrêt propre).
            self._stop_event.wait(timeout=self._intervalle)

    def _verifier_alertes(self) -> None:
        """
        Lit la liste des produits en alerte et publie un rapport dans la queue.

        Le Lock protège l'accès à _stock._produits qui peut être modifié
        par le thread principal (ajout, sortie stock…) en même temps.
        """
        # [V4] Lock : un seul thread peut lire _stock à la fois
        with self._lock:
            produits_alerte = self._stock.produits_en_alerte()

        if not produits_alerte:
            return   # rien à signaler

        alerte = {
            "timestamp": datetime.now().isoformat(),
            "produits" : produits_alerte,
            "count"    : len(produits_alerte),
        }

        # [V4] Queue.put() : thread-safe, ne bloque pas l'émetteur
        self._file_alertes.put(alerte)

        # Historique protégé par Lock (écrit depuis le thread secondaire)
        with self._lock:
            self._historique.append(alerte)

    # ── API côté UI (appelée depuis le thread principal Tkinter) ──────────

    def lire_alertes(self) -> list[dict]:
        """
        Vide la queue et retourne toutes les alertes disponibles.

        get_nowait() est non-bloquant — parfait pour un polling via after().
        Lève queue.Empty quand la file est vide → on s'arrête.
        """
        resultats = []
        try:
            while True:
                resultats.append(self._file_alertes.get_nowait())
        except queue.Empty:
            pass
        return resultats

    def get_historique(self) -> list[dict]:
        """Retourne une copie thread-safe de l'historique complet."""
        with self._lock:
            return list(self._historique)

    def vider_historique(self) -> None:
        """Efface l'historique (protégé par Lock)."""
        with self._lock:
            self._historique.clear()
        # Vide aussi la queue
        try:
            while True:
                self._file_alertes.get_nowait()
        except queue.Empty:
            pass

    # ── Propriétés ────────────────────────────────────────────────────────

    @property
    def est_actif(self) -> bool:
        """True si le thread tourne réellement."""
        return self._thread is not None and self._thread.is_alive()

    @property
    def intervalle(self) -> int:
        return self._intervalle

    @intervalle.setter
    def intervalle(self, valeur: int) -> None:
        """Modifie l'intervalle — thread-safe grâce au Lock."""
        with self._lock:
            self._intervalle = max(5, int(valeur))

    @property
    def nb_alertes_totales(self) -> int:
        """Nombre total de rapports d'alerte dans l'historique."""
        with self._lock:
            return len(self._historique)
