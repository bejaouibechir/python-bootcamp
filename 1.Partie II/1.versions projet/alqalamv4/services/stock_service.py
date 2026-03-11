# [V4 - Threading] StockService protégé par un threading.Lock.
# Le SurveillanceService lit _produits depuis un thread secondaire ;
# le thread principal (Tkinter) écrit dans _produits lors des opérations.
# → Le Lock empêche une lecture partielle pendant une écriture (race condition).
#
# Bonne pratique : on n'acquiert le Lock que le temps strictement nécessaire
# (pas pendant la sauvegarde JSON qui est plus longue).

import json
import threading
from pathlib import Path

from models.produit   import Produit
from models.mouvement import Mouvement
from config           import DATA_DIR


# ── Context Manager pour la sauvegarde sécurisée ─────────────────────────────
# [V2 - Context Manager] __enter__ et __exit__ garantissent que le fichier
# est toujours fermé proprement, même en cas d'erreur lors de l'écriture.

class FichierStock:
    """Gestionnaire de contexte pour la sauvegarde sécurisée du stock JSON."""

    def __init__(self, chemin: Path):
        self.chemin   = chemin
        self._fichier = None

    def __enter__(self):
        """Ouvre le fichier en écriture et le retourne."""
        self._fichier = open(self.chemin, "w", encoding="utf-8")
        return self._fichier

    def __exit__(self, type_erreur, valeur, traceback):
        """Ferme toujours le fichier, même si une exception s'est produite."""
        if self._fichier:
            self._fichier.close()
        return False   # False = ne pas étouffer l'exception si elle existe


class StockService:
    """
    Gère l'ensemble du stock : ajout, entrée, sortie, persistance.

    Responsabilités :
    - Maintenir le catalogue de produits en mémoire
    - Enregistrer les mouvements de stock
    - Persister les données dans data/stock.json
    - Fournir des vues filtrées (alertes, par catégorie, etc.)
    """

    def __init__(self):
        # [POO] L'état interne est privé (convention: préfixe _)
        # On ne modifie pas ces structures directement depuis l'extérieur
        self._produits   = {}   # dict { ref: Produit } — accès O(1) par ref
        self._mouvements = []   # liste chronologique des mouvements
        self._chemin     = DATA_DIR / "stock.json"

        # [V4] Lock partagé avec SurveillanceService pour protéger _produits.
        # Tout accès concurrent (lecture depuis le thread de surveillance,
        # écriture depuis le thread principal) doit acquérir ce verrou.
        self._lock = threading.Lock()

        # Chargement automatique au démarrage
        self.charger()

    # ── Gestion des produits ──────────────────────────────────────────────

    def ajouter_produit(self, produit: Produit) -> None:
        """Ajoute un nouveau produit au catalogue."""
        with self._lock:   # [V4] écriture protégée
            if produit.ref in self._produits:
                raise ValueError(f"La référence '{produit.ref}' existe déjà dans le stock.")
            self._produits[produit.ref] = produit
        self.sauvegarder()

    def mettre_a_jour_produit(self, produit: Produit) -> None:
        """Met à jour un produit existant (utilisé par l'import CSV V8)."""
        with self._lock:   # [V4] écriture protégée
            if produit.ref not in self._produits:
                raise KeyError(f"Produit '{produit.ref}' introuvable.")
            self._produits[produit.ref] = produit
        self.sauvegarder()

    def supprimer_produit(self, ref: str) -> None:
        """Supprime un produit du catalogue."""
        with self._lock:   # [V4] écriture protégée
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            del self._produits[ref]
        self.sauvegarder()

    def get_produit(self, ref: str) -> Produit:
        """Retourne un produit par sa référence."""
        with self._lock:   # [V4] lecture protégée
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            return self._produits[ref]

    def lister_tous(self) -> list[Produit]:
        """Retourne la liste complète des produits."""
        with self._lock:
            return list(self._produits.values())

    def produits_en_alerte(self) -> list[Produit]:
        """
        Retourne les produits dont la quantité est sous le seuil.
        [V4] Lecture protégée par Lock — appelée depuis le thread de surveillance.
        """
        with self._lock:
            return [p for p in self._produits.values() if p.est_en_alerte()]

    def nb_alertes(self) -> int:
        """Nombre de produits en alerte (pour la barre de statut)."""
        return len(self.produits_en_alerte())

    # ── Mouvements de stock ───────────────────────────────────────────────

    def entree_stock(self, ref: str, qte: int, note: str = "") -> None:
        """
        Enregistre une entrée de stock (réception marchandise).

        Args:
            ref  : référence du produit
            qte  : quantité reçue (doit être > 0)
            note : commentaire optionnel (ex: "Commande fournisseur #42")

        Raises:
            ValueError: si la quantité est invalide
            KeyError  : si le produit n'existe pas
        """
        if qte <= 0:
            raise ValueError(f"La quantité doit être positive, reçu : {qte}")
        # [V4] Accès direct à _produits pour éviter le deadlock :
        # get_produit() acquiert aussi _lock → threading.Lock n'est pas réentrant.
        with self._lock:
            if ref not in self._produits:
                raise KeyError(f"Produit '{ref}' introuvable.")
            produit = self._produits[ref]
            produit.qte += qte
            self._mouvements.append(Mouvement(ref, "entree", qte, note))
        self.sauvegarder()

    def sortie_stock(self, ref: str, qte: int, note: str = "") -> None:
        """
        Enregistre une sortie de stock (vente ou consommation).

        Args:
            ref  : référence du produit
            qte  : quantité retirée (doit être > 0)
            note : commentaire optionnel (ex: "Vente client")

        Raises:
            ValueError: si la quantité est invalide ou stock insuffisant
            KeyError  : si le produit n'existe pas
        """
        if qte <= 0:
            raise ValueError(f"La quantité doit être positive, reçu : {qte}")
        with self._lock:   # [V4] accès direct pour éviter le deadlock
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
        """Retourne l'historique complet des mouvements."""
        return list(self._mouvements)

    # ── Statistiques ──────────────────────────────────────────────────────

    def valeur_totale_stock(self) -> float:
        """Valeur totale du stock (somme des qte × prix_achat)."""
        return sum(p.valeur_stock() for p in self._produits.values())

    def nb_produits(self) -> int:
        """Nombre total de références en stock."""
        return len(self._produits)

    # ── Méthodes V3 — Compréhensions et Générateurs ───────────────────────
    # Chaque méthode remplace une boucle for+append par une expression concise.

    def par_categorie(self) -> dict:
        """
        Regroupe les produits par catégorie.
        [V3] Dict comprehension imbriqué dans une set comprehension.
        """
        # Set comprehension : toutes les catégories uniques
        categories = {p.categorie for p in self._produits.values()}
        # Dict comprehension : { catégorie → [liste de produits] }
        return {
            cat: [p for p in self._produits.values() if p.categorie == cat]
            for cat in sorted(categories)
        }

    def top_valeur(self, n: int = 5) -> list:
        """
        Top N produits par valeur de stock.
        [V3] sorted() + slicing en une ligne — pas de boucle.
        """
        return sorted(self._produits.values(),
                      key=lambda p: p.valeur_stock(),
                      reverse=True)[:n]

    def rechercher(self, texte: str) -> list:
        """
        Filtre multi-champs : ref, nom ou catégorie contiennent le texte.
        [V3] List comprehension avec condition composée.
        """
        t = texte.lower().strip()
        if not t:
            return list(self._produits.values())
        return [
            p for p in self._produits.values()
            if t in p.ref.lower() or t in p.nom.lower() or t in p.categorie.lower()
        ]

    def stats_categories(self) -> dict:
        """
        Statistiques agrégées par catégorie.
        [V3] Dict comprehension avec expression génératrice dans sum().
        Retourne : { cat → { nb_produits, valeur_totale, nb_alertes } }
        """
        return {
            cat: {
                "nb_produits"  : len(prods),
                "valeur_totale": sum(p.valeur_stock() for p in prods),   # générateur
                "nb_alertes"   : sum(1 for p in prods if p.est_en_alerte()),  # générateur
            }
            for cat, prods in self.par_categorie().items()
        }

    def flux_export(self):
        """
        Générateur de lignes CSV — produit les données une par une.
        [V3] yield : économe en mémoire (pas de liste intermédiaire).
        Utilisable : for ligne in stock.flux_export(): ...
        """
        yield ["ref", "nom", "categorie", "prix_achat", "prix_vente", "qte", "seuil_min"]
        for p in sorted(self._produits.values()):   # __lt__ de Produit
            yield [p.ref, p.nom, p.categorie,
                   p.prix_achat, p.prix_vente, p.qte, p.seuil_min]

    # ── Méthodes Magiques V2 ──────────────────────────────────────────────
    # Ces méthodes font de StockService un conteneur Python natif.

    def __len__(self) -> int:
        """len(stock) retourne le nombre de produits."""
        return len(self._produits)

    def __contains__(self, ref: str) -> bool:
        """'CRAY-001' in stock  → True/False directement."""
        return ref in self._produits

    def __iter__(self):
        """for produit in stock: ...  → itère sur tous les produits."""
        return iter(self._produits.values())

    def __str__(self) -> str:
        """print(stock) affiche un résumé propre."""
        alertes = len(self.produits_en_alerte())
        return f"Al Qalam Stock · {len(self)} produits · {alertes} alerte(s)"

    # ── Persistance ───────────────────────────────────────────────────────

    def sauvegarder(self) -> None:
        """
        Sauvegarde le stock dans data/stock.json via le context manager FichierStock.
        [V2] Utilise 'with FichierStock(...)' au lieu de write_text direct.
        """
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = [p.to_dict() for p in self._produits.values()]
        with FichierStock(self._chemin) as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False))

    def charger(self) -> None:
        """
        Charge le stock depuis data/stock.json.
        Si le fichier n'existe pas, insère les données de démonstration.
        """
        if not self._chemin.exists():
            self._seeder()
            return
        try:
            texte = self._chemin.read_text(encoding="utf-8")
            data  = json.loads(texte)
            self._produits = {d["ref"]: Produit.from_dict(d) for d in data}
        except (json.JSONDecodeError, KeyError) as e:
            # Fichier corrompu → on repart des données de démo
            print(f"[StockService] Fichier corrompu ({e}), réinitialisation.")
            self._seeder()

    def _seeder(self) -> None:
        """
        Insère 10 produits de démonstration au premier lancement.
        Certains sont volontairement en rupture pour illustrer les alertes.
        """
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
