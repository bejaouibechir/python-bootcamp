# [V5 - Décorateurs] StockService décoré avec @journaliser et @valider_qte.
#
# Les décorateurs s'appliquent comme des "couches" autour des méthodes :
#   entree_stock() → valider_qte() vérifie d'abord la quantité
#                  → journaliser() enregistre le résultat (succès ou échec)
#                  → le corps de la méthode s'exécute si les validations passent
#
# Ordre des décorateurs (bas → haut = premier exécuté en dernier) :
#   @journaliser("entree")        ← exécuté EN PREMIER (enveloppe externe)
#   @valider_qte(min_val=1)       ← exécuté EN SECOND  (enveloppe interne)
#   def entree_stock(self, ...):  ← corps original

import json
import threading
from pathlib import Path

from models.produit    import Produit
from models.mouvement  import Mouvement
from config            import DATA_DIR
from decorateurs.journalisation import journaliser
from decorateurs.validation     import valider_qte, valider_ref
from services.journal_service   import JournalService


# ── Context Manager (V2) ───────────────────────────────────────────────────────

class FichierStock:
    """Gestionnaire de contexte pour la sauvegarde sécurisée du stock JSON."""

    def __init__(self, chemin: Path):
        self.chemin   = chemin
        self._fichier = None

    def __enter__(self):
        self._fichier = open(self.chemin, "w", encoding="utf-8")
        return self._fichier

    def __exit__(self, type_erreur, valeur, traceback):
        if self._fichier:
            self._fichier.close()
        return False


# ── StockService ──────────────────────────────────────────────────────────────

class StockService:
    """
    Gère l'ensemble du stock : ajout, entrée, sortie, persistance.

    [V5] Les méthodes critiques sont décorées avec :
      @journaliser(op)   → logging automatique dans self._journal
      @valider_qte(...)  → validation de quantité avant exécution
      @valider_ref       → normalisation et validation de la référence
    """

    def __init__(self):
        self._produits   = {}   # dict { ref: Produit }
        self._mouvements = []   # liste chronologique
        self._chemin     = DATA_DIR / "stock.json"
        self._lock       = threading.Lock()    # [V4] protection thread
        self._journal    = JournalService()    # [V5] journal des opérations
        self.charger()

    # ── Propriété publique vers le journal (pour l'UI) ────────────────────

    @property
    def journal(self) -> JournalService:
        """Expose le journal en lecture seule pour l'UI."""
        return self._journal

    # ── Gestion des produits ──────────────────────────────────────────────

    @journaliser("ajout")
    def ajouter_produit(self, produit: Produit) -> None:
        """Ajoute un nouveau produit au catalogue."""
        with self._lock:
            if produit.ref in self._produits:
                raise ValueError(f"La référence '{produit.ref}' existe déjà dans le stock.")
            self._produits[produit.ref] = produit
        self.sauvegarder()

    @journaliser("modification")
    def mettre_a_jour_produit(self, produit: Produit) -> None:
        """Met à jour un produit existant."""
        with self._lock:
            if produit.ref not in self._produits:
                raise KeyError(f"Produit '{produit.ref}' introuvable.")
            self._produits[produit.ref] = produit
        self.sauvegarder()

    @journaliser("suppression")
    def supprimer_produit(self, ref: str) -> None:
        """Supprime un produit du catalogue."""
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            del self._produits[ref]
        self.sauvegarder()

    def get_produit(self, ref: str) -> Produit:
        """Retourne un produit par sa référence."""
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            return self._produits[ref]

    def lister_tous(self) -> list[Produit]:
        with self._lock:
            return list(self._produits.values())

    def produits_en_alerte(self) -> list[Produit]:
        with self._lock:
            return [p for p in self._produits.values() if p.est_en_alerte()]

    def nb_alertes(self) -> int:
        return len(self.produits_en_alerte())

    # ── Mouvements de stock ───────────────────────────────────────────────
    # [V5] Double décoration : @journaliser (externe) puis @valider_qte (interne).
    # L'ordre est important : le journal capture aussi les erreurs de validation.

    @journaliser("entree")
    @valider_qte(min_val=1, max_val=100_000)
    def entree_stock(self, ref: str, qte: int, note: str = "") -> None:
        """
        Enregistre une entrée de stock (réception marchandise).

        [V5] @valider_qte vérifie que qte est un entier dans [1, 100_000]
             AVANT d'entrer dans le corps de la méthode.
             @journaliser enregistre l'opération dans le journal, y compris
             si @valider_qte a levé une exception.
        """
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            produit = self._produits[ref]
            produit.qte += qte
            self._mouvements.append(Mouvement(ref, "entree", qte, note))
        self.sauvegarder()

    @journaliser("sortie")
    @valider_qte(min_val=1, max_val=100_000)
    def sortie_stock(self, ref: str, qte: int, note: str = "") -> None:
        """
        Enregistre une sortie de stock (vente ou consommation).

        [V5] Double décoration identique à entree_stock.
        """
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
            self._mouvements.append(Mouvement(ref, "sortie", qte, note))
        self.sauvegarder()

    def get_mouvements(self) -> list[Mouvement]:
        return list(self._mouvements)

    # ── Statistiques ──────────────────────────────────────────────────────

    def valeur_totale_stock(self) -> float:
        return sum(p.valeur_stock() for p in self._produits.values())

    def nb_produits(self) -> int:
        return len(self._produits)

    # ── Méthodes V3 ── Compréhensions et Générateurs ──────────────────────

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

    # ── Méthodes Magiques V2 ──────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._produits)

    def __contains__(self, ref: str) -> bool:
        return ref in self._produits

    def __iter__(self):
        return iter(self._produits.values())

    def __str__(self) -> str:
        alertes = len(self.produits_en_alerte())
        return f"Al Qalam Stock · {len(self)} produits · {alertes} alerte(s)"

    # ── Persistance ───────────────────────────────────────────────────────

    def sauvegarder(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = [p.to_dict() for p in self._produits.values()]
        with FichierStock(self._chemin) as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False))

    def charger(self) -> None:
        if not self._chemin.exists():
            self._seeder()
            return
        try:
            texte = self._chemin.read_text(encoding="utf-8")
            data  = json.loads(texte)
            self._produits = {d["ref"]: Produit.from_dict(d) for d in data}
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[StockService] Fichier corrompu ({e}), réinitialisation.")
            self._seeder()

    def _seeder(self) -> None:
        demo = [
            Produit("CRAY-001", "Crayon HB",       "Écriture", 0.15, 0.50, 150, 20),
            Produit("CRAY-002", "Crayon 2B",        "Écriture", 0.20, 0.60,   8, 20),
            Produit("STYL-001", "Stylo Bleu",       "Écriture", 0.30, 0.90, 200, 30),
            Produit("STYL-002", "Stylo Rouge",      "Écriture", 0.30, 0.90,   4, 30),
            Produit("GOM-001",  "Gomme Blanche",    "Effaçage", 0.20, 0.70,  60, 10),
            Produit("PAP-A4",   "Rame Papier A4",   "Papier",   2.50, 5.00, 300, 50),
            Produit("PAP-A3",   "Rame Papier A3",   "Papier",   4.00, 8.00,   6, 10),
            Produit("CIS-001",  "Ciseaux 17cm",     "Coupe",    1.50, 4.00,  25,  5),
            Produit("REG-001",  "Règle 30cm",       "Mesure",   0.80, 2.00,  40, 10),
            Produit("CAR-001",  "Carnet A5",        "Papier",   1.20, 3.50,   3, 10),
        ]
        for p in demo:
            self._produits[p.ref] = p
        self.sauvegarder()
