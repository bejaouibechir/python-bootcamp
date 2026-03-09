"""Service principal de gestion de stock."""

from __future__ import annotations

import logging
from pathlib import Path

from config import DB_PATH, LOG_PATH
from dao.mouvement_dao import MouvementDAO
from dao.produit_dao import ProduitDAO
from models.mouvement import Mouvement
from models.produit import Produit
from services.decorateurs import logger_operation, valider_quantite

logger = logging.getLogger(__name__)


class SingletonMeta(type):
    """Singleton par classe pour garantir une source de vérité unique."""

    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def reset_instance(mcs, cls):
        mcs._instances.pop(cls, None)


class StockService(metaclass=SingletonMeta):
    """Orchestre produits, mouvements, persistance et statistiques."""

    def __init__(self, db_path: str | Path | None = None, seed_demo: bool = True):
        self.db_path = str(db_path or DB_PATH)
        self._produit_dao = ProduitDAO(self.db_path)
        self._mouvement_dao = MouvementDAO(self.db_path)
        self._configurer_logging()
        self.initialiser_schema()
        if seed_demo:
            self._seeder_si_vide()

    @classmethod
    def reset_singleton(cls):
        """Utilitaire de test pour réinitialiser l'instance unique."""
        SingletonMeta.reset_instance(cls)

    def _configurer_logging(self):
        if logging.getLogger().handlers:
            return
        Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            handlers=[
                logging.FileHandler(LOG_PATH, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )

    def initialiser_schema(self) -> None:
        """Crée les tables SQL nécessaires."""
        with self._produit_dao._session() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS produit (
                    ref         TEXT    PRIMARY KEY,
                    nom         TEXT    NOT NULL,
                    categorie   TEXT    NOT NULL,
                    prix_achat  REAL    NOT NULL CHECK(prix_achat >= 0),
                    prix_vente  REAL    NOT NULL CHECK(prix_vente >= 0),
                    qte         INTEGER NOT NULL DEFAULT 0 CHECK(qte >= 0),
                    seuil_min   INTEGER NOT NULL DEFAULT 5 CHECK(seuil_min >= 0),
                    date_ajout  TEXT    NOT NULL DEFAULT (datetime('now')),
                    date_modif  TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS mouvement (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ref_produit TEXT    NOT NULL,
                    type_mvt    TEXT    NOT NULL CHECK(type_mvt IN ('entree','sortie','retour','inventaire')),
                    qte         INTEGER NOT NULL CHECK(qte > 0),
                    qte_avant   INTEGER NOT NULL,
                    qte_apres   INTEGER NOT NULL,
                    note        TEXT    DEFAULT '',
                    date_mvt    TEXT    NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (ref_produit) REFERENCES produit(ref) ON DELETE RESTRICT
                );

                CREATE INDEX IF NOT EXISTS idx_mouvement_ref ON mouvement(ref_produit);
                CREATE INDEX IF NOT EXISTS idx_mouvement_date ON mouvement(date_mvt);
                """
            )

    def _seeder_si_vide(self) -> None:
        if len(self) > 0:
            return
        demo = [
            Produit("CRAY-001", "Crayon HB", "Écriture", 0.15, 0.50, 150, 20),
            Produit("CRAY-002", "Crayon 2B", "Écriture", 0.20, 0.60, 8, 20),
            Produit("STYL-001", "Stylo Bleu", "Écriture", 0.30, 0.90, 200, 30),
            Produit("STYL-002", "Stylo Rouge", "Écriture", 0.30, 0.90, 4, 30),
            Produit("GOM-001", "Gomme Blanche", "Effaçage", 0.20, 0.70, 60, 10),
            Produit("PAP-A4", "Rame Papier A4", "Papier", 2.50, 5.00, 300, 50),
            Produit("PAP-A3", "Rame Papier A3", "Papier", 4.00, 8.00, 6, 10),
            Produit("CIS-001", "Ciseaux 17cm", "Coupe", 1.50, 4.00, 25, 5),
            Produit("REG-001", "Règle 30cm", "Mesure", 0.80, 2.00, 40, 10),
            Produit("CAR-001", "Carnet A5", "Papier", 1.20, 3.50, 3, 10),
        ]
        for produit in demo:
            self.ajouter_produit(produit)

    def __len__(self):
        return len(self._produit_dao.lister_tous())

    def __contains__(self, ref):
        return self._produit_dao.get_par_ref(ref) is not None

    def __iter__(self):
        return iter(self._produit_dao.lister_tous())

    def __str__(self):
        return f"Al Qalam Stock · {len(self)} produits · {len(self.produits_en_alerte())} alerte(s)"

    @logger_operation
    def ajouter_produit(self, produit: Produit) -> None:
        if produit.ref in self:
            raise ValueError(f"La référence {produit.ref} existe déjà")
        self._produit_dao.inserer(produit)

    @logger_operation
    def mettre_a_jour_produit(self, produit: Produit) -> None:
        if produit.ref not in self:
            self._produit_dao.inserer(produit)
            return
        self._produit_dao.mettre_a_jour_complet(produit)

    def supprimer_produit(self, ref: str) -> None:
        if ref not in self:
            raise KeyError(f"Produit {ref!r} introuvable")
        self._produit_dao.supprimer(ref)

    def get_produit(self, ref: str) -> Produit:
        produit = self._produit_dao.get_par_ref(ref)
        if not produit:
            raise KeyError(f"Produit {ref!r} introuvable")
        return produit

    def lister_tous(self) -> list[Produit]:
        return self._produit_dao.lister_tous()

    def produits_en_alerte(self) -> list[Produit]:
        return self._produit_dao.en_alerte()

    @valider_quantite
    @logger_operation
    def entree_stock(self, ref: str, qte: int, note: str = "") -> None:
        self._mouvement_stock(ref, "entree", qte, note)

    @valider_quantite
    @logger_operation
    def sortie_stock(self, ref: str, qte: int, note: str = "") -> None:
        produit = self.get_produit(ref)
        if produit.qte < qte:
            raise ValueError(f"Stock insuffisant : {produit.qte} disponible")
        self._mouvement_stock(ref, "sortie", qte, note)

    @valider_quantite
    @logger_operation
    def retour_stock(self, ref: str, qte: int, note: str = "") -> None:
        self._mouvement_stock(ref, "retour", qte, note)

    @valider_quantite
    @logger_operation
    def inventaire_stock(self, ref: str, qte: int, note: str = "") -> None:
        produit = self.get_produit(ref)
        delta = abs(produit.qte - qte)
        if delta == 0:
            return
        self._mouvement_stock(ref, "inventaire", delta, note, qte_force=qte)

    def _mouvement_stock(self, ref: str, type_mvt: str, qte: int, note: str, qte_force: int | None = None) -> None:
        if type_mvt not in Mouvement.types_disponibles():
            raise ValueError(f"Type de mouvement inconnu: {type_mvt}")
        produit = self.get_produit(ref)
        qte_avant = produit.qte

        if qte_force is not None:
            qte_apres = qte_force
        elif type_mvt in {"entree", "retour"}:
            qte_apres = qte_avant + qte
        else:
            qte_apres = qte_avant - qte

        with self._produit_dao._session() as conn:
            conn.execute(
                "UPDATE produit SET qte = ?, date_modif = datetime('now') WHERE ref = ?",
                (qte_apres, ref),
            )
            conn.execute(
                """
                INSERT INTO mouvement (ref_produit, type_mvt, qte, qte_avant, qte_apres, note)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (ref, type_mvt, qte, qte_avant, qte_apres, note),
            )

    def get_historique(self, ref: str | None = None, type_mvt: str | None = None) -> list[dict]:
        return self._mouvement_dao.lister(ref=ref, type_mvt=type_mvt)

    def dernieres_operations(self, limite: int = 20) -> list[dict]:
        return self._mouvement_dao.dernieres(limite)

    def par_categorie(self) -> dict[str, list[Produit]]:
        produits = self.lister_tous()
        categories = {p.categorie for p in produits}
        return {cat: [p for p in produits if p.categorie == cat] for cat in sorted(categories)}

    def valeur_totale_stock(self) -> float:
        return sum(p.valeur_stock() for p in self.lister_tous())

    def top_valeur(self, n: int = 5) -> list[Produit]:
        return sorted(self.lister_tous(), key=lambda p: p.valeur_stock(), reverse=True)[:n]

    def rechercher(self, texte: str) -> list[Produit]:
        t = texte.lower().strip()
        if not t:
            return self.lister_tous()
        return [
            p
            for p in self.lister_tous()
            if t in p.ref.lower() or t in p.nom.lower() or t in p.categorie.lower()
        ]

    def stats_categories(self) -> dict[str, dict[str, float | int]]:
        return {
            cat: {
                "nb_produits": len(prods),
                "valeur_totale": sum(p.valeur_stock() for p in prods),
                "nb_alertes": sum(1 for p in prods if p.est_en_alerte()),
            }
            for cat, prods in self.par_categorie().items()
        }

    def kpis(self) -> dict[str, float | int]:
        return {
            "nb_produits": len(self),
            "nb_alertes": len(self.produits_en_alerte()),
            "valeur_stock": round(self.valeur_totale_stock(), 2),
        }

    def flux_export(self):
        yield ["ref", "nom", "categorie", "prix_achat", "prix_vente", "qte", "seuil_min"]
        for p in sorted(self.lister_tous()):
            yield [p.ref, p.nom, p.categorie, p.prix_achat, p.prix_vente, p.qte, p.seuil_min]
