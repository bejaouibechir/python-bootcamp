"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 12  ·  Export CSV & TXT            ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Exporter les données vers des fichiers partageables              ║
║    CSV = importable dans Excel · TXT = rapport imprimable           ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    csv · open() · with · write() · pathlib · datetime · f-strings   ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Messages de confirmation · affichage chemin fichier créé         ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import csv
import datetime
from pathlib import Path
from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table

console  = Console()
EXPORTS  = Path("exports")     # dossier de sortie


# ─── Helpers ─────────────────────────────────────────────────────────
def valeur_stock(p):  return p["prix_achat"] * p["quantite"]
def marge_pct(p):
    return ((p["prix_vente"] - p["prix_achat"]) / p["prix_achat"] * 100) \
           if p["prix_achat"] else 0
def etat_stock(p):
    q = p["quantite"]
    if q == 0:              return ("rupture", "⛔ RUPTURE",  "bold red")
    if q <= p["stock_min"]: return ("alerte",  "⚠  ALERTE",   "bold yellow")
    if q >  p["stock_max"]: return ("surplus", "↑  SURPLUS",  "bold magenta")
    return                         ("ok",      "✅ OK",        "bold green")


# ════════════════════════════════════════════════════════════════════
#  1. EXPORT CSV  (importable dans Excel / LibreOffice Calc)
# ════════════════════════════════════════════════════════════════════

def exporter_catalogue_csv(catalogue, config=None):
    """
    Exporte le catalogue complet au format CSV.

    Notes techniques
    ----------------
    - Encodage UTF-8 avec BOM (utf-8-sig) pour Excel Windows
    - Séparateur point-virgule (standard FR)
    - Virgule décimale dans les montants
    - Les nombres restent des nombres (pas de quotes autour)
    """
    EXPORTS.mkdir(exist_ok=True)
    devise   = (config or {}).get("devise", "DT")
    horodatage = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin   = EXPORTS / f"catalogue_{horodatage}.csv"

    en_tetes = [
        "Référence", "Nom", "Catégorie", "Unité",
        "Prix achat", "Prix vente", "Marge %",
        "Quantité", "Stock min", "Stock max",
        "Valeur stock", "Fournisseur",
        "Date expiration", "Date création", "Statut",
    ]

    try:
        with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
            # utf-8-sig ajoute le BOM — indispensable pour Excel FR/Windows
            ecrivain = csv.writer(
                f,
                delimiter=";",           # séparateur FR standard
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
            )

            # Ligne d'en-tête
            ecrivain.writerow(en_tetes)

            # Une ligne par produit
            for p in catalogue:
                _, libelle, _ = etat_stock(p)
                ecrivain.writerow([
                    p["reference"],
                    p["nom"],
                    p["categorie"],
                    p.get("unite", ""),
                    str(p["prix_achat"]).replace(".", ","),   # virgule FR
                    str(p["prix_vente"]).replace(".", ","),
                    str(round(marge_pct(p), 2)).replace(".", ","),
                    p["quantite"],
                    p["stock_min"],
                    p["stock_max"],
                    str(round(valeur_stock(p), 3)).replace(".", ","),
                    p["fournisseur"],
                    p.get("date_expiration") or "",
                    p.get("date_creation") or "",
                    libelle,
                ])

        console.print(
            f"  [bold green]✓  Catalogue exporté :[/bold green] "
            f"[white]{chemin}[/white]  "
            f"[dim]({len(catalogue)} articles)[/dim]"
        )
        return chemin

    except (OSError, IOError) as e:
        console.print(f"  [bold red]✗  Erreur export CSV : {e}[/bold red]")
        return None


def exporter_historique_csv(historique, config=None):
    """
    Exporte l'historique des mouvements au format CSV.
    """
    EXPORTS.mkdir(exist_ok=True)
    horodatage = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin     = EXPORTS / f"mouvements_{horodatage}.csv"

    en_tetes = [
        "Date", "Référence", "Nom", "Type",
        "Quantité", "Stock avant", "Stock après", "Motif",
    ]

    TYPES_FR = {
        "entree":     "Entrée",
        "sortie":     "Sortie",
        "ajustement": "Ajustement",
    }

    try:
        with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
            ecrivain = csv.writer(f, delimiter=";", quotechar='"',
                                  quoting=csv.QUOTE_MINIMAL)
            ecrivain.writerow(en_tetes)

            for m in historique:
                ecrivain.writerow([
                    m.get("date", ""),
                    m.get("reference", ""),
                    m.get("nom", ""),
                    TYPES_FR.get(m.get("type", ""), m.get("type", "")),
                    m.get("quantite", ""),
                    m.get("qte_avant", ""),
                    m.get("qte_apres", ""),
                    m.get("motif", ""),
                ])

        console.print(
            f"  [bold green]✓  Mouvements exportés :[/bold green] "
            f"[white]{chemin}[/white]  "
            f"[dim]({len(historique)} mouvements)[/dim]"
        )
        return chemin

    except (OSError, IOError) as e:
        console.print(f"  [bold red]✗  Erreur export historique : {e}[/bold red]")
        return None


# ════════════════════════════════════════════════════════════════════
#  2. RAPPORT TEXTE (imprimable)
# ════════════════════════════════════════════════════════════════════

def exporter_rapport_txt(catalogue, config=None):
    """
    Génère un rapport textuel complet et formaté.

    Le fichier est encodé UTF-8 et contient :
    - En-tête entreprise
    - Indicateurs clés
    - Liste complète par catégorie
    - Produits en alerte
    - Pied de page
    """
    EXPORTS.mkdir(exist_ok=True)
    devise     = (config or {}).get("devise", "DT")
    entreprise = (config or {}).get("entreprise", "STOCK MANAGER")
    horodatage = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin     = EXPORTS / f"rapport_{horodatage}.txt"
    now_str    = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M:%S")

    LARGEUR = 74
    SEP     = "═" * LARGEUR
    sep2    = "─" * LARGEUR

    try:
        with open(chemin, "w", encoding="utf-8") as f:

            def L(texte=""):
                f.write(texte + "\n")

            # ── En-tête ───────────────────────────────────────────
            L(SEP)
            L(f"  {entreprise.upper()}")
            L(f"  RAPPORT DE STOCK  —  Édité le {now_str}")
            L(SEP)
            L()

            # ── Indicateurs clés ──────────────────────────────────
            total     = len(catalogue)
            ruptures  = sum(1 for p in catalogue if p["quantite"] == 0)
            alertes   = sum(1 for p in catalogue
                            if 0 < p["quantite"] <= p["stock_min"])
            val_tot   = sum(valeur_stock(p) for p in catalogue)
            marge_moy = (sum(marge_pct(p) for p in catalogue) / total) if total else 0

            L("  INDICATEURS CLÉS")
            L(sep2)
            L(f"  Produits en catalogue  : {total}")
            L(f"  En rupture de stock    : {ruptures}")
            L(f"  En alerte réappro.     : {alertes}")
            L(f"  Valeur totale du stock : {val_tot:,.3f} {devise}")
            L(f"  Marge moyenne          : {marge_moy:.1f} %")
            L()

            # ── Catalogue par catégorie ───────────────────────────
            L("  CATALOGUE COMPLET (par catégorie)")
            L(SEP)

            # Regrouper par catégorie
            cats = {}
            for p in catalogue:
                c = p["categorie"]
                if c not in cats:
                    cats[c] = []
                cats[c].append(p)

            col_ref  = 12
            col_nom  = 26
            col_cat  = 1   # déjà dans la section
            col_qte  = 8
            col_val  = 14

            for cat, produits_cat in sorted(cats.items()):
                L()
                L(f"  [ {cat.upper()} ]")
                L(sep2)
                L(
                    f"  {'Référence':<{col_ref}}"
                    f"{'Nom':<{col_nom}}"
                    f"{'Qté':>{col_qte}}"
                    f"{'P.Vente':>10}"
                    f"{'Valeur':>{col_val}}"
                    f"  Statut"
                )
                L(sep2)

                for p in sorted(produits_cat, key=lambda x: x["nom"]):
                    _, libelle_txt, _ = etat_stock(p)
                    # Supprimer les emojis pour le fichier texte
                    statut_propre = libelle_txt.replace("⛔", "[!]").replace("⚠", "[!]").replace("✅", "[OK]").replace("↑", "[^]")
                    L(
                        f"  {p['reference']:<{col_ref}}"
                        f"{p['nom'][:col_nom-2]:<{col_nom}}"
                        f"{p['quantite']:>{col_qte}}"
                        f"{p['prix_vente']:>10.3f}"
                        f"{valeur_stock(p):>{col_val}.3f}"
                        f"  {statut_propre}"
                    )

                sous_total = sum(valeur_stock(p) for p in produits_cat)
                L(sep2)
                L(
                    f"  {'Sous-total ' + cat:<{col_ref + col_nom + col_qte + 2}}"
                    f"{sous_total:>{col_val + 10}.3f} {devise}"
                )

            # ── Total ─────────────────────────────────────────────
            L()
            L(SEP)
            L(
                f"  {'TOTAL GÉNÉRAL':<{col_ref + col_nom + col_qte + 2}}"
                f"{val_tot:>{col_val + 10}.3f} {devise}"
            )
            L(SEP)

            # ── Produits en alerte ────────────────────────────────
            alertes_list = [p for p in catalogue if p["quantite"] <= p["stock_min"]]
            if alertes_list:
                L()
                L("  PRODUITS EN ALERTE / RUPTURE")
                L(sep2)
                L(f"  {'Référence':<12}{'Nom':<28}{'Stock':>8}{'Min':>6}{'Déficit':>10}")
                L(sep2)
                for p in sorted(alertes_list, key=lambda x: x["quantite"]):
                    deficit = p["stock_min"] - p["quantite"]
                    L(f"  {p['reference']:<12}{p['nom'][:26]:<28}"
                      f"{p['quantite']:>8}{p['stock_min']:>6}{deficit:>10}")
                L(sep2)

            # ── Pied de page ──────────────────────────────────────
            L()
            L(SEP)
            L(f"  Généré par Stock Manager  —  {now_str}")
            L(f"  {len(catalogue)} articles  |  Valeur : {val_tot:,.3f} {devise}")
            L(SEP)

        console.print(
            f"  [bold green]✓  Rapport TXT :[/bold green] "
            f"[white]{chemin}[/white]"
        )
        return chemin

    except (OSError, IOError) as e:
        console.print(f"  [bold red]✗  Erreur rapport TXT : {e}[/bold red]")
        return None


# ════════════════════════════════════════════════════════════════════
#  3. MENU D'EXPORT INTERACTIF
# ════════════════════════════════════════════════════════════════════

def menu_export(catalogue, historique, config=None):
    """
    Sous-menu interactif pour choisir le type d'export.
    """
    from rich.prompt import Prompt

    console.print(Panel(
        "[bold white]Choisissez le format d'export.[/bold white]",
        title="[bold cyan]📤  EXPORT DES DONNÉES[/bold cyan]",
        border_style="cyan",
    ))

    EXPORTS.mkdir(exist_ok=True)

    items = [
        ("1", "📊  Catalogue complet en CSV  (Excel)"),
        ("2", "📋  Rapport complet en TXT    (imprimable)"),
        ("3", "🔄  Historique mouvements CSV"),
        ("0", "↩️   Retour"),
    ]

    t = Table(show_header=False, box=None, padding=(0, 3))
    t.add_column(style="bold yellow", width=5)
    t.add_column(style="white")
    for touche, libelle in items:
        if touche == "0":
            t.add_row("", "")
        t.add_row(f"[{touche}]", libelle)

    console.print(Panel(t, title="[bold white]FORMAT[/bold white]",
                        border_style="cyan", padding=(1, 4)))

    choix = Prompt.ask(
        "  [bold cyan]Votre choix[/bold cyan]",
        choices=["0", "1", "2", "3"],
        show_choices=False,
        console=console,
    )

    if   choix == "1": exporter_catalogue_csv(catalogue, config)
    elif choix == "2": exporter_rapport_txt(catalogue, config)
    elif choix == "3": exporter_historique_csv(historique, config)
    elif choix == "0": return

    if choix != "0":
        console.print(f"\n  [dim]Les fichiers sont dans le dossier : [white]{EXPORTS}[/white][/dim]")


# ════════════════════════════════════════════════════════════════════
#  TEST AUTONOME
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    catalogue_test = [
        {"reference":"MED-001","nom":"Paracétamol 500mg","categorie":"Analgésique","unite":"boîte",
         "prix_achat":3.5,"prix_vente":5.8,"quantite":250,"stock_min":50,"stock_max":500,
         "fournisseur":"SIPHAT","date_expiration":"31/12/2025",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MED-002","nom":"Ibuprofène 400mg","categorie":"Analgésique","unite":"boîte",
         "prix_achat":4.2,"prix_vente":7.2,"quantite":15,"stock_min":30,"stock_max":300,
         "fournisseur":"ADWYA","date_expiration":"30/09/2025",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MED-003","nom":"Amoxicilline 1g","categorie":"Antibiotique","unite":"boîte",
         "prix_achat":8.2,"prix_vente":12.5,"quantite":5,"stock_min":20,"stock_max":200,
         "fournisseur":"ADWYA","date_expiration":"30/06/2025",
         "date_creation":"01/01/2024","date_modification":None},
    ]

    historique_test = [
        {"date":"18/02/2025 10:30","reference":"MED-001","nom":"Paracétamol 500mg",
         "type":"entree","quantite":100,"qte_avant":150,"qte_apres":250,"motif":"BL-1234"},
        {"date":"17/02/2025 15:00","reference":"MED-002","nom":"Ibuprofène 400mg",
         "type":"sortie","quantite":5,"qte_avant":20,"qte_apres":15,"motif":"Vente"},
    ]

    config = {"devise": "DT", "entreprise": "Pharmacie El Amal"}

    console.rule("[bold cyan]TEST — EXPORT CSV & TXT[/bold cyan]")
    console.print()

    c1 = exporter_catalogue_csv(catalogue_test, config)
    c2 = exporter_rapport_txt(catalogue_test, config)
    c3 = exporter_historique_csv(historique_test, config)

    # Afficher la taille des fichiers créés
    console.print()
    for chemin in [c1, c2, c3]:
        if chemin and Path(chemin).exists():
            taille = Path(chemin).stat().st_size
            console.print(f"  [dim]{chemin.name}[/dim]  →  [green]{taille:,} octets[/green]")


# ════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — encoding='utf-8-sig'
#     Le BOM (Byte Order Mark) dans utf-8-sig dit à Excel
#     "ce fichier est du UTF-8". Sans lui, Excel affiche des
#     caractères corrompus (ï¿½ au lieu des accents).
#
#  💡 ASTUCE — delimiter=';'
#     Standard en France. Avec ',' comme séparateur, les montants
#     "3,500" (virgule décimale FR) seraient mal interprétés par Excel.
#     Utiliser ';' évite complètement ce problème.
#
#  💡 ASTUCE — f-string avec :<N et :>N
#     f"{'texte':<12}" aligne à gauche sur 12 caractères.
#     f"{nombre:>10.3f}" aligne à droite sur 10 caractères, 3 décimales.
#     Ces opérateurs de formatage créent des colonnes alignées
#     dans les fichiers texte sans aucune bibliothèque externe.
#
#  🏋️  EXERCICE
#     1. Ajouter l'export des produits en alerte uniquement
#        dans un fichier alertes_AAAAMMJJ.csv.
#     2. Ajouter une ligne de métadonnées en haut du CSV :
#        "# Entreprise;Mon Drug Store;Date;01/01/2025".
#     3. Écrire importer_catalogue_csv(chemin) qui lit un fichier
#        CSV exporté et recharge le catalogue.
# ════════════════════════════════════════════════════════════════════