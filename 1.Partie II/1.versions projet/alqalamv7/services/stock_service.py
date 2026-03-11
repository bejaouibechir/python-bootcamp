# [V6 - Métaclasses] StockService utilise SingletonMeta pour garantir une
# instance unique, et Mouvement.fabriquer() pour créer le bon type via le registre.
#
# CHANGEMENTS V6 :
#   1. class StockService(metaclass=SingletonMeta)
#      → StockService() retourne TOUJOURS la même instance
#      → id(StockService()) == id(StockService())  →  True
#
#   2. import models.types_mouvement  (force l'enregistrement des 4 sous-classes)
#      → après cet import, RegistreMouvementMeta._registre contient :
#        {"entree": EntreeMouvement, "sortie": SortieMouvement,
#         "ajustement": AjustementMouvement, "retour": RetourMouvement}
#
#   3. entree_stock / sortie_stock utilisent Mouvement.fabriquer(type, ...)
#      → au lieu de Mouvement(ref, type, qte, note) directement
#
#   4. Nouvelle méthode : ajustement_stock(ref, qte_cible, note)
#      → inventaire physique : règle la quantité à une valeur absolue cible

import json
import threading
from pathlib import Path

from models.produit    import Produit
from models.mouvement  import Mouvement
import models.types_mouvement          # [V6] force l'enregistrement des 4 types
from config            import DATA_DIR
from metaclasses.singleton             import SingletonMeta
from decorateurs.journalisation        import journaliser
from decorateurs.validation            import valider_qte
from services.journal_service          import JournalService


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

class StockService(metaclass=SingletonMeta):
    """
    Gère l'ensemble du stock : ajout, entrée, sortie, ajustement, persistance.

    [V6] Singleton garanti par SingletonMeta :
      - Premier appel  : StockService() → crée l'instance, charge le stock
      - Appels suivants: StockService() → retourne la même instance (sans __init__)
      - Preuve : assert StockService() is StockService()  →  True

    [V6] Types de mouvements étendus via le registre RegistreMouvementMeta :
      - entree     → EntreeMouvement
      - sortie     → SortieMouvement
      - ajustement → AjustementMouvement  (nouveau V6)
      - retour     → RetourMouvement      (nouveau V6)
    """

    def __init__(self):
        self._produits   = {}   # dict { ref: Produit }
        self._mouvements = []   # liste chronologique de Mouvement (sous-classes)
        self._chemin     = DATA_DIR / "stock.json"
        self._lock       = threading.Lock()
        self._journal    = JournalService()
        self.charger()

    # ── Propriété publique vers le journal (pour l'UI) ────────────────────

    @property
    def journal(self) -> JournalService:
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
        Enregistre une entrée de stock (réception marchandise).

        [V6] Utilise Mouvement.fabriquer("entree", ...) qui retourne
             une instance de EntreeMouvement (pas de Mouvement de base).
        """
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            produit = self._produits[ref]
            produit.qte += qte
            # [V6] fabriquer() consulte le registre → crée EntreeMouvement
            self._mouvements.append(Mouvement.fabriquer("entree", ref, qte, note))
        self.sauvegarder()

    @journaliser("sortie")
    @valider_qte(min_val=1, max_val=100_000)
    def sortie_stock(self, ref: str, qte: int, note: str = "") -> None:
        """
        Enregistre une sortie de stock (vente ou consommation).

        [V6] Crée SortieMouvement via le registre.
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
            self._mouvements.append(Mouvement.fabriquer("sortie", ref, qte, note))
        self.sauvegarder()

    @journaliser("ajustement")
    def ajustement_stock(self, ref: str, qte_cible: int, note: str = "") -> None:
        """
        [V6] Ajuste le stock à une quantité cible (inventaire physique).

        Cas d'usage : comptage physique révèle que le stock réel diffère
        du stock théorique. L'ajustement corrige l'écart.

        Args:
            ref       : référence du produit
            qte_cible : nouvelle quantité absolue (résultat du comptage)
            note      : raison de l'ajustement (casse, vol, erreur saisie…)
        """
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            produit  = self._produits[ref]
            qte_avant = produit.qte
            delta    = qte_cible - qte_avant

            # La quantité cible doit être positive ou nulle
            if qte_cible < 0:
                raise ValueError(f"La quantité cible ne peut pas être négative : {qte_cible}")

            produit.qte = qte_cible
            # AjustementMouvement avec delta (peut être 0 si pas de changement)
            note_auto = note or f"Inventaire : {qte_avant}→{qte_cible} (Δ{delta:+d})"
            self._mouvements.append(
                Mouvement.fabriquer("ajustement", ref, abs(delta) or 1, note_auto)
            )
        self.sauvegarder()

    @journaliser("retour")
    @valider_qte(min_val=1, max_val=100_000)
    def retour_stock(self, ref: str, qte: int, note: str = "") -> None:
        """
        [V6] Enregistre un retour fournisseur (marchandise renvoyée).

        Le stock diminue (retour = sortie comptable) mais est catégorisé
        séparément pour les rapports fournisseurs.
        """
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
            self._mouvements.append(Mouvement.fabriquer("retour", ref, qte, note))
        self.sauvegarder()

    def get_mouvements(self) -> list:
        return list(self._mouvements)

    def stats_par_type(self) -> dict:
        """
        [V6] Statistiques des mouvements groupées par type.

        Retourne :
            { "entree": {"nb": 5, "qte_totale": 230, "classe": EntreeMouvement},
              "sortie": {"nb": 3, "qte_totale": 80,  "classe": SortieMouvement},
              ... }
        """
        from metaclasses.registre import RegistreMouvementMeta
        registre = RegistreMouvementMeta.get_registre()

        stats = {}
        for type_mvt, classe in registre.items():
            mvts = [m for m in self._mouvements if m.type_mvt == type_mvt]
            stats[type_mvt] = {
                "nb"         : len(mvts),
                "qte_totale" : sum(m.qte for m in mvts),
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
