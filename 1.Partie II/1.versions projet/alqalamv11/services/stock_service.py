# [V10 - SQLite] StockService utilise DatabaseService pour la persistance.
#
# CHANGEMENTS V10 :
#   - Remplacement de la persistance JSON par SQLite (module sqlite3 stdlib)
#   - DatabaseService gère toutes les opérations CRUD sur la DB
#   - Mouvements persistés en base (historique complet, filtrable)
#   - Migration automatique depuis stock.json au 1er lancement
#   - Suppression de FichierStock (context manager JSON, plus nécessaire)
#   - charger() lit depuis SQLite au lieu du JSON
#   - sauvegarder() → sauvegarder_produit(ref) : mise à jour ciblée (plus efficace)
#
# API PUBLIQUE INCHANGÉE (compatibilité UI) :
#   ajouter_produit, mettre_a_jour_produit, supprimer_produit,
#   entree_stock, sortie_stock, ajustement_stock, retour_stock,
#   get_produit, lister_tous, nb_produits, nb_alertes, ...

import threading
from pathlib import Path

from models.produit    import Produit
from models.mouvement  import Mouvement
import models.types_mouvement          # [V6] force l'enregistrement des 4 types
from config            import DATA_DIR, DB_PATH
from metaclasses.singleton             import SingletonMeta
from decorateurs.journalisation        import journaliser
from decorateurs.validation            import valider_qte
from services.journal_service          import JournalService
from services.database_service         import DatabaseService   # [V10]


class StockService(metaclass=SingletonMeta):
    """
    Gère l'ensemble du stock : ajout, entrée, sortie, ajustement, persistance.

    [V10] Persistance SQLite via DatabaseService :
      - Deux tables : produits + mouvements (historique complet)
      - Chargement initial depuis la base au démarrage
      - Chaque modification met à jour la base immédiatement
      - Migration automatique depuis stock.json si présent

    [V6] Singleton garanti par SingletonMeta.
    [V6] Types de mouvements via registre RegistreMouvementMeta.
    """

    def __init__(self):
        self._produits   = {}   # cache en mémoire { ref: Produit }
        self._mouvements = []   # cache en mémoire (pour compatibilité UI)
        self._lock       = threading.Lock()
        self._journal    = JournalService()
        self._db         = DatabaseService(DB_PATH)   # [V10]
        self.charger()

    # ── Propriété publique vers le journal ────────────────────────────────

    @property
    def journal(self) -> JournalService:
        return self._journal

    # ── Propriété publique vers la base (pour l'onglet Historique) ────────

    @property
    def db(self) -> DatabaseService:
        """Expose la DatabaseService pour les requêtes de l'onglet Historique."""
        return self._db

    # ── Gestion des produits ──────────────────────────────────────────────

    @journaliser("ajout")
    def ajouter_produit(self, produit: Produit) -> None:
        """Ajoute un nouveau produit au catalogue et en base."""
        with self._lock:
            if produit.ref in self._produits:
                raise ValueError(f"La référence '{produit.ref}' existe déjà dans le stock.")
            self._produits[produit.ref] = produit
        # [V10] Persistance SQLite au lieu de JSON
        self._db.inserer_produit(produit.to_dict())

    @journaliser("modification")
    def mettre_a_jour_produit(self, produit: Produit) -> None:
        """Met à jour un produit existant en mémoire et en base."""
        with self._lock:
            if produit.ref not in self._produits:
                raise KeyError(f"Produit '{produit.ref}' introuvable.")
            self._produits[produit.ref] = produit
        self._db.mettre_a_jour_produit(produit.to_dict())

    @journaliser("suppression")
    def supprimer_produit(self, ref: str) -> None:
        """Supprime un produit du catalogue et de la base."""
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            del self._produits[ref]
        self._db.supprimer_produit(ref)

    def get_produit(self, ref: str) -> Produit:
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            return self._produits[ref]

    def lister_tous(self) -> list:
        with self._lock:
            return list(self._produits.values())

    def produits_en_alerte(self) -> list:
        with self._lock:
            return [p for p in self._produits.values() if p.est_en_alerte()]

    def nb_alertes(self) -> int:
        return len(self.produits_en_alerte())

    # ── Mouvements de stock ───────────────────────────────────────────────

    @journaliser("entree")
    @valider_qte(min_val=1, max_val=100_000)
    def entree_stock(self, ref: str, qte: int, note: str = "") -> None:
        """
        Enregistre une entrée de stock.

        [V10] Le mouvement est persisté en SQLite (table mouvements).
        """
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            produit = self._produits[ref]
            produit.qte += qte
            mvt = Mouvement.fabriquer("entree", ref, qte, note)
            self._mouvements.append(mvt)
        # [V10] Double persistance : qte dans produits, mouvement dans mouvements
        self._db.mettre_a_jour_qte(ref, produit.qte)
        self._db.inserer_mouvement(self._mouvement_to_db(mvt, produit.nom))

    @journaliser("sortie")
    @valider_qte(min_val=1, max_val=100_000)
    def sortie_stock(self, ref: str, qte: int, note: str = "") -> None:
        """Enregistre une sortie de stock."""
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            produit = self._produits[ref]
            if produit.qte < qte:
                raise ValueError(
                    f"Stock insuffisant pour '{produit.nom}' : "
                    f"{produit.qte} disponible, {qte} demandé."
                )
            produit.qte -= qte
            mvt = Mouvement.fabriquer("sortie", ref, qte, note)
            self._mouvements.append(mvt)
        self._db.mettre_a_jour_qte(ref, produit.qte)
        self._db.inserer_mouvement(self._mouvement_to_db(mvt, produit.nom))

    @journaliser("ajustement")
    def ajustement_stock(self, ref: str, qte_cible: int, note: str = "") -> None:
        """Ajuste le stock à une quantité cible (inventaire physique)."""
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            produit   = self._produits[ref]
            qte_avant = produit.qte
            delta     = qte_cible - qte_avant
            if qte_cible < 0:
                raise ValueError(f"La quantité cible ne peut pas être négative : {qte_cible}")
            produit.qte = qte_cible
            note_auto = note or f"Inventaire : {qte_avant}→{qte_cible} (Δ{delta:+d})"
            mvt = Mouvement.fabriquer("ajustement", ref, abs(delta) or 1, note_auto)
            self._mouvements.append(mvt)
        self._db.mettre_a_jour_qte(ref, produit.qte)
        self._db.inserer_mouvement(self._mouvement_to_db(mvt, produit.nom))

    @journaliser("retour")
    @valider_qte(min_val=1, max_val=100_000)
    def retour_stock(self, ref: str, qte: int, note: str = "") -> None:
        """Enregistre un retour fournisseur."""
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            produit = self._produits[ref]
            if produit.qte < qte:
                raise ValueError(
                    f"Stock insuffisant pour un retour de '{produit.nom}' : "
                    f"{produit.qte} disponible, {qte} à retourner."
                )
            produit.qte -= qte
            mvt = Mouvement.fabriquer("retour", ref, qte, note)
            self._mouvements.append(mvt)
        self._db.mettre_a_jour_qte(ref, produit.qte)
        self._db.inserer_mouvement(self._mouvement_to_db(mvt, produit.nom))

    def get_mouvements(self) -> list:
        """Retourne le cache mémoire des mouvements (session courante)."""
        return list(self._mouvements)

    def stats_par_type(self) -> dict:
        """
        Statistiques des mouvements groupées par type.

        [V10] Délègue la requête d'agrégation à DatabaseService.
        """
        from metaclasses.registre import RegistreMouvementMeta
        registre = RegistreMouvementMeta.get_registre()
        stats_db = self._db.stats_mouvements()

        stats = {}
        for type_mvt, classe in registre.items():
            s = stats_db.get(type_mvt, {"nb": 0, "qte_totale": 0})
            stats[type_mvt] = {
                "nb"         : s["nb"],
                "qte_totale" : s["qte_totale"],
                "classe"     : classe,
                "icone"      : classe.ICONE,
                "label"      : classe.LABEL,
            }
        return stats

    # ── Statistiques ──────────────────────────────────────────────────────

    def valeur_totale_stock(self) -> float:
        return sum(p.valeur_stock() for p in self._produits.values())

    def nb_produits(self) -> int:
        return len(self._produits)

    def par_categorie(self) -> dict:
        categories = {p.categorie for p in self._produits.values()}
        return {
            cat: [p for p in self._produits.values() if p.categorie == cat]
            for cat in sorted(categories)
        }

    def top_valeur(self, n: int = 5) -> list:
        return sorted(self._produits.values(),
                      key=lambda p: p.valeur_stock(), reverse=True)[:n]

    def rechercher(self, texte: str) -> list:
        t = texte.lower().strip()
        if not t:
            return list(self._produits.values())
        return [
            p for p in self._produits.values()
            if t in p.ref.lower() or t in p.nom.lower() or t in p.categorie.lower()
        ]

    def stats_categories(self) -> dict:
        return {
            cat: {
                "nb_produits"  : len(prods),
                "valeur_totale": sum(p.valeur_stock() for p in prods),
                "nb_alertes"   : sum(1 for p in prods if p.est_en_alerte()),
            }
            for cat, prods in self.par_categorie().items()
        }

    def flux_export(self):
        yield ["ref", "nom", "categorie", "prix_achat", "prix_vente", "qte", "seuil_min"]
        for p in sorted(self._produits.values()):
            yield [p.ref, p.nom, p.categorie,
                   p.prix_achat, p.prix_vente, p.qte, p.seuil_min]

    # ── Méthodes Magiques ─────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._produits)

    def __contains__(self, ref: str) -> bool:
        return ref in self._produits

    def __iter__(self):
        return iter(self._produits.values())

    def __str__(self) -> str:
        alertes = len(self.produits_en_alerte())
        return f"Al Qalam Stock · {len(self)} produits · {alertes} alerte(s)"

    # ── Persistance SQLite [V10] ──────────────────────────────────────────

    def charger(self) -> None:
        """
        [V10] Charge le stock depuis SQLite.

        Séquence au premier lancement :
          1. Tente la migration depuis stock.json (si présent)
          2. Si la table est vide après migration → seeder
          3. Charge tous les produits en mémoire depuis SQLite
        """
        # Migration JSON → SQLite (au premier lancement seulement)
        chemin_json = DATA_DIR / "stock.json"
        nb_migres   = self._db.migrer_depuis_json(chemin_json)
        if nb_migres:
            print(f"[StockService] Migration JSON -> SQLite : {nb_migres} produits importes.")

        # Charger les produits depuis SQLite
        rows = self._db.charger_produits()

        if not rows:
            self._seeder()
            return

        self._produits = {r["ref"]: Produit.from_dict(r) for r in rows}

    def _mouvement_to_db(self, mvt: Mouvement, nom_produit: str) -> dict:
        """Convertit un objet Mouvement en dict compatible avec inserer_mouvement()."""
        return {
            "date"    : mvt.date,
            "type_mvt": mvt.type_mvt,
            "ref"     : mvt.ref_produit,
            "produit" : nom_produit,
            "qte"     : mvt.qte,
            "note"    : mvt.note,
        }

    def _seeder(self) -> None:
        """Initialise la base avec les 10 produits de démo."""
        demo = [
            Produit("CRAY-001", "Crayon HB",     "Écriture", 0.15, 0.50, 150, 20),
            Produit("CRAY-002", "Crayon 2B",      "Écriture", 0.20, 0.60,   8, 20),
            Produit("STYL-001", "Stylo Bleu",     "Écriture", 0.30, 0.90, 200, 30),
            Produit("STYL-002", "Stylo Rouge",    "Écriture", 0.30, 0.90,   4, 30),
            Produit("GOM-001",  "Gomme Blanche",  "Effaçage", 0.20, 0.70,  60, 10),
            Produit("PAP-A4",   "Rame Papier A4", "Papier",   2.50, 5.00, 300, 50),
            Produit("PAP-A3",   "Rame Papier A3", "Papier",   4.00, 8.00,   6, 10),
            Produit("CIS-001",  "Ciseaux 17cm",   "Coupe",    1.50, 4.00,  25,  5),
            Produit("REG-001",  "Règle 30cm",     "Mesure",   0.80, 2.00,  40, 10),
            Produit("CAR-001",  "Carnet A5",      "Papier",   1.20, 3.50,   3, 10),
        ]
        for p in demo:
            self._produits[p.ref] = p
            self._db.inserer_produit(p.to_dict())
