# [V8 - CSV] CsvService — import/export CSV pour Al Qalam.
#
# Utilise le module standard `csv` (pas pandas) :
#   - csv.DictReader  : lecture par nom de colonne — robuste aux réordonnements
#   - csv.DictWriter  : écriture par nom de colonne — header auto
#   - encoding="utf-8-sig" : compatible Excel (BOM UTF-8) pour les accents
#   - newline="" à l'écriture : obligatoire sous Windows (évite \r\r\n)
#
# NOUVEAUTÉS V8 :
#   1. importer_catalogue(chemin) → dict {"importes": n, "mis_a_jour": n, "erreurs": [...]}
#      → valide les colonnes requises avant de traiter
#      → crée Produit si ref absente, met à jour si existante (seuil/prix)
#
#   2. exporter_catalogue(chemin) → int (nb lignes)
#      → exporte tous les produits du stock courant
#
#   3. exporter_mouvements(chemin) → int (nb lignes)
#      → exporte l'historique complet des mouvements
#
#   4. exporter_comptabilite(chemin) → int (nb lignes)
#      → rapport comptable : valeur stock + marges

import csv
from datetime import datetime
from pathlib  import Path

from config         import (
    COLONNES_CATALOGUE_IMPORT, COLONNES_CATALOGUE_EXPORT,
    COLONNES_MOUVEMENTS, COLONNES_COMPTABILITE, CSV_DIR
)
from models.produit import Produit
from decorateurs.journalisation import journaliser


class ErreurCsv(Exception):
    """Levée quand un fichier CSV ne respecte pas la structure attendue."""


class CsvService:
    """
    Service d'import/export CSV pour Al Qalam.

    [V8] Utilise uniquement le module standard `csv` :
      - Aucune dépendance externe (pas de pandas)
      - Traitement ligne par ligne → consommation mémoire constante
      - Compatible Excel grâce à encoding="utf-8-sig" (BOM)

    Usage :
        service = CsvService(stock_service)
        rapport = service.importer_catalogue("fournisseur.csv")
        service.exporter_comptabilite("rapport_mars.csv")
    """

    def __init__(self, stock_service):
        # CsvService dépend de StockService mais n'en est pas un Singleton lui-même
        self._stock = stock_service
        CSV_DIR.mkdir(parents=True, exist_ok=True)

    # ── Import ─────────────────────────────────────────────────────────────

    @journaliser("import_csv")
    def importer_catalogue(self, chemin: str | Path) -> dict:
        """
        Importe un catalogue fournisseur CSV dans le stock.

        Format attendu du CSV (colonnes dans n'importe quel ordre) :
            ref, nom, categorie, prix_achat, prix_vente, seuil_min

        Comportement :
          - ref absente du stock  → ajouter_produit() avec qte=0
          - ref déjà présente    → mettre_a_jour_produit() (prix + seuil)
          - ligne invalide        → ajoutée à erreurs[], traitement continue

        Args:
            chemin : chemin du fichier CSV fournisseur (str ou Path)

        Returns:
            dict {
                "importes"  : nb de nouveaux produits créés,
                "mis_a_jour": nb de produits mis à jour,
                "erreurs"   : liste de str décrivant les lignes rejetées,
                "total_lues": nb total de lignes traitées
            }
        """
        chemin = Path(chemin)

        if not chemin.exists():
            raise FileNotFoundError(f"Fichier introuvable : {chemin}")

        rapport = {"importes": 0, "mis_a_jour": 0, "erreurs": [], "total_lues": 0}

        with open(chemin, "r", encoding="utf-8-sig") as f:
            lecteur = csv.DictReader(f)

            # ── Validation de structure ──────────────────────────────────
            colonnes_presentes = set(lecteur.fieldnames or [])
            manquantes = set(COLONNES_CATALOGUE_IMPORT) - colonnes_presentes
            if manquantes:
                raise ErreurCsv(
                    f"Colonnes manquantes dans {chemin.name} : "
                    f"{', '.join(sorted(manquantes))}\n"
                    f"Colonnes requises : {', '.join(COLONNES_CATALOGUE_IMPORT)}"
                )

            # ── Traitement ligne par ligne ───────────────────────────────
            for numero_ligne, ligne in enumerate(lecteur, start=2):
                rapport["total_lues"] += 1
                try:
                    ref        = ligne["ref"].strip()
                    nom        = ligne["nom"].strip()
                    categorie  = ligne["categorie"].strip()
                    prix_achat = float(ligne["prix_achat"].replace(",", "."))
                    prix_vente = float(ligne["prix_vente"].replace(",", "."))
                    seuil_min  = int(ligne["seuil_min"])

                    if not ref or not nom or not categorie:
                        raise ValueError("ref, nom et categorie ne peuvent pas être vides")

                    if prix_achat < 0 or prix_vente < 0 or seuil_min < 0:
                        raise ValueError("Les valeurs numériques doivent être positives")

                    if ref in self._stock:
                        # Mise à jour prix et seuil du produit existant
                        produit_existant = self._stock.get_produit(ref)
                        produit_maj = Produit(
                            ref=produit_existant.ref,
                            nom=nom,
                            categorie=categorie,
                            prix_achat=prix_achat,
                            prix_vente=prix_vente,
                            qte=produit_existant.qte,
                            seuil_min=seuil_min,
                        )
                        self._stock.mettre_a_jour_produit(produit_maj)
                        rapport["mis_a_jour"] += 1
                    else:
                        # Nouveau produit — qte = 0 (à réceptionner via entrée stock)
                        nouveau = Produit(
                            ref=ref, nom=nom, categorie=categorie,
                            prix_achat=prix_achat, prix_vente=prix_vente,
                            qte=0, seuil_min=seuil_min,
                        )
                        self._stock.ajouter_produit(nouveau)
                        rapport["importes"] += 1

                except (ValueError, KeyError) as e:
                    rapport["erreurs"].append(f"Ligne {numero_ligne} rejetée : {e}")
                    continue

        return rapport

    # ── Exports ────────────────────────────────────────────────────────────

    @journaliser("export_catalogue_csv")
    def exporter_catalogue(self, chemin: str | Path | None = None) -> int:
        """
        Exporte le catalogue complet des produits vers un CSV.

        [V8] Utilise csv.DictWriter avec fieldnames=COLONNES_CATALOGUE_EXPORT.
             encoding="utf-8-sig" → s'ouvre directement dans Excel sans config.

        Args:
            chemin : chemin de destination (défaut : data/csv/catalogue_YYYYMMDD.csv)

        Returns:
            Nombre de lignes exportées (sans l'en-tête)
        """
        if chemin is None:
            horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
            chemin = CSV_DIR / f"catalogue_{horodatage}.csv"

        chemin = Path(chemin)
        chemin.parent.mkdir(parents=True, exist_ok=True)

        produits = self._stock.lister_tous()

        with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
            # newline="" : obligatoire sous Windows pour éviter les lignes vides
            writer = csv.DictWriter(f, fieldnames=COLONNES_CATALOGUE_EXPORT)
            writer.writeheader()

            for p in sorted(produits):
                writer.writerow({
                    "ref"        : p.ref,
                    "nom"        : p.nom,
                    "categorie"  : p.categorie,
                    "prix_achat" : p.prix_achat,
                    "prix_vente" : p.prix_vente,
                    "qte"        : p.qte,
                    "seuil_min"  : p.seuil_min,
                })

        return len(produits)

    @journaliser("export_mouvements_csv")
    def exporter_mouvements(self, chemin: str | Path | None = None) -> int:
        """
        Exporte l'historique des mouvements de stock vers un CSV.

        Colonnes : date, type, ref, produit, qte, note

        Args:
            chemin : chemin de destination (défaut : data/csv/mouvements_YYYYMMDD.csv)

        Returns:
            Nombre de mouvements exportés
        """
        if chemin is None:
            horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
            chemin = CSV_DIR / f"mouvements_{horodatage}.csv"

        chemin = Path(chemin)
        chemin.parent.mkdir(parents=True, exist_ok=True)

        mouvements = self._stock.get_mouvements()

        with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=COLONNES_MOUVEMENTS)
            writer.writeheader()

            for m in mouvements:
                # Récupérer le nom du produit si disponible
                try:
                    nom_produit = self._stock.get_produit(m.ref).nom
                except KeyError:
                    nom_produit = m.ref

                writer.writerow({
                    "date"   : m.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "type"   : m.type_mvt,
                    "ref"    : m.ref,
                    "produit": nom_produit,
                    "qte"    : m.qte,
                    "note"   : m.note,
                })

        return len(mouvements)

    @journaliser("export_comptabilite_csv")
    def exporter_comptabilite(self, chemin: str | Path | None = None) -> int:
        """
        Exporte un rapport comptable complet : valeur stock + marges.

        [V8] Colonnes calculées :
          - valeur_stock    = qte × prix_achat
          - marge_unitaire  = prix_vente − prix_achat
          - marge_totale    = qte × marge_unitaire

        Args:
            chemin : chemin de destination (défaut : data/csv/comptabilite_YYYYMMDD.csv)

        Returns:
            Nombre de lignes exportées
        """
        if chemin is None:
            horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
            chemin = CSV_DIR / f"comptabilite_{horodatage}.csv"

        chemin = Path(chemin)
        chemin.parent.mkdir(parents=True, exist_ok=True)

        produits = self._stock.lister_tous()

        with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=COLONNES_COMPTABILITE)
            writer.writeheader()

            for p in sorted(produits):
                writer.writerow({
                    "ref"           : p.ref,
                    "nom"           : p.nom,
                    "categorie"     : p.categorie,
                    "qte"           : p.qte,
                    "prix_achat"    : f"{p.prix_achat:.3f}",
                    "prix_vente"    : f"{p.prix_vente:.3f}",
                    "valeur_stock"  : f"{p.valeur_stock():.3f}",
                    "marge_unitaire": f"{p.marge_unitaire():.3f}",
                    "marge_totale"  : f"{p.qte * p.marge_unitaire():.3f}",
                })

        return len(produits)

    # ── Prévisualisation ───────────────────────────────────────────────────

    def previsualiser_csv(self, chemin: str | Path, nb_lignes: int = 5) -> dict:
        """
        Lit les premières lignes d'un CSV pour prévisualiser avant import.

        Args:
            chemin    : chemin du fichier CSV
            nb_lignes : nombre de lignes de données à lire (sans l'en-tête)

        Returns:
            dict {
                "colonnes" : liste des noms de colonnes,
                "lignes"   : liste de dicts (données),
                "total_col": nombre de colonnes,
                "valide"   : bool (colonnes requises présentes ?)
            }
        """
        chemin = Path(chemin)
        resultat = {"colonnes": [], "lignes": [], "total_col": 0, "valide": False}

        if not chemin.exists():
            return resultat

        with open(chemin, "r", encoding="utf-8-sig") as f:
            lecteur = csv.DictReader(f)
            colonnes = list(lecteur.fieldnames or [])
            resultat["colonnes"]  = colonnes
            resultat["total_col"] = len(colonnes)

            requises = set(COLONNES_CATALOGUE_IMPORT)
            resultat["valide"] = requises.issubset(set(colonnes))

            for i, ligne in enumerate(lecteur):
                if i >= nb_lignes:
                    break
                resultat["lignes"].append(dict(ligne))

        return resultat
