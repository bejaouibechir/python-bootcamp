"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 03  ·  Modèle de données           ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Représenter un produit sous forme de dictionnaire Python         ║
║    Calculer des indicateurs : valeur, marge, état du stock          ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    dict · types numériques · f-strings · fonctions · conditions     ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Table (sans en-tête) · Panel · couleurs conditionnelles          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import datetime
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel

console = Console()


# ══════════════════════════════════════════════════════════════════════
#  MODÈLE DE DONNÉES
#  Un produit = un dictionnaire Python avec des clés fixes.
#  C'est notre "contrat de données" : toute l'application
#  s'appuiera sur cette structure.
# ══════════════════════════════════════════════════════════════════════

def creer_produit(reference, nom, categorie, unite,
                  prix_achat, prix_vente,
                  quantite, stock_min, stock_max,
                  fournisseur, date_expiration=None):
    """
    Crée et retourne un dictionnaire représentant un produit en stock.

    Paramètres
    ----------
    reference       str    Code unique  (ex: "MED-001")
    nom             str    Nom commercial
    categorie       str    Famille produit
    unite           str    "boîte" | "flacon" | "sachet" | "unité"
    prix_achat      float  Prix d'achat HT
    prix_vente      float  Prix de vente TTC
    quantite        int    Quantité actuelle en stock
    stock_min       int    Seuil déclenchant l'alerte de réappro.
    stock_max       int    Quantité maximale à stocker
    fournisseur     str    Nom du fournisseur principal
    date_expiration str    "JJ/MM/AAAA"  ou  None

    Retourne
    --------
    dict  produit complet avec date_creation auto
    """
    return {
        "reference"        : str(reference).upper().strip(),
        "nom"              : str(nom).strip(),
        "categorie"        : str(categorie).strip(),
        "unite"            : str(unite).strip(),
        "prix_achat"       : float(prix_achat),
        "prix_vente"       : float(prix_vente),
        "quantite"         : int(quantite),
        "stock_min"        : int(stock_min),
        "stock_max"        : int(stock_max),
        "fournisseur"      : str(fournisseur).strip(),
        "date_expiration"  : date_expiration,
        "date_creation"    : datetime.date.today().strftime("%d/%m/%Y"),
        "date_modification": None,
    }


# ── Fonctions de calcul ────────────────────────────────────────────────

def valeur_stock(produit):
    """Valeur totale = prix d'achat × quantité."""
    return produit["prix_achat"] * produit["quantite"]

def marge_brute(produit):
    """Marge en valeur absolue par unité."""
    return produit["prix_vente"] - produit["prix_achat"]

def marge_pct(produit):
    """Marge en pourcentage du prix d'achat."""
    if produit["prix_achat"] == 0:
        return 0.0
    return (marge_brute(produit) / produit["prix_achat"]) * 100

def etat_stock(produit):
    """
    Retourne l'état du stock sous forme de tuple (code, libellé, couleur).
    code : "rupture" | "alerte" | "ok" | "surplus"
    """
    q   = produit["quantite"]
    smi = produit["stock_min"]
    sma = produit["stock_max"]

    if q == 0:
        return ("rupture", "⛔ RUPTURE",  "bold red")
    if q <= smi:
        return ("alerte",  "⚠  ALERTE",   "bold yellow")
    if q > sma:
        return ("surplus", "↑  SURPLUS",  "bold magenta")
    return ("ok",      "✅ OK",       "bold green")

def jours_avant_expiration(produit):
    """
    Retourne le nombre de jours avant la date d'expiration,
    ou None si pas de date.
    Valeur négative = produit déjà expiré.
    """
    if not produit["date_expiration"]:
        return None
    try:
        d_exp = datetime.datetime.strptime(
            produit["date_expiration"], "%d/%m/%Y"
        ).date()
        return (d_exp - datetime.date.today()).days
    except ValueError:
        return None


# ── Affichage d'une fiche détaillée ───────────────────────────────────

def afficher_fiche(produit):
    """Affiche la fiche complète d'un produit dans un Panel coloré."""

    code, libelle, couleur = etat_stock(produit)
    jours                  = jours_avant_expiration(produit)

    # ── Couleur de la date d'expiration ──────────────────────────────
    if jours is None:
        exp_txt = "[dim]—[/dim]"
    elif jours < 0:
        exp_txt = f"[bold red]EXPIRÉ ({abs(jours)} j)[/bold red]"
    elif jours < 30:
        exp_txt = f"[bold red]{produit['date_expiration']} ({jours} j)[/bold red]"
    elif jours < 90:
        exp_txt = f"[yellow]{produit['date_expiration']} ({jours} j)[/yellow]"
    else:
        exp_txt = f"[dim white]{produit['date_expiration']}[/dim white]"

    # ── Tableau fiche ────────────────────────────────────────────────
    t = Table(show_header=False, box=None, padding=(0, 2), min_width=52)
    t.add_column(style="dim cyan",   width=22)
    t.add_column(style="bold white", width=30)

    t.add_row("📦 Référence",        produit["reference"])
    t.add_row("🏷️  Nom",              produit["nom"])
    t.add_row("📂 Catégorie",         produit["categorie"])
    t.add_row("📐 Unité",             produit["unite"])
    t.add_row("🏭 Fournisseur",        produit["fournisseur"])
    t.add_row("",                     "")
    t.add_row("💰 Prix achat HT",     f"{produit['prix_achat']:.3f} DT")
    t.add_row("🛒 Prix vente TTC",    f"{produit['prix_vente']:.3f} DT")
    t.add_row("📈 Marge unitaire",    f"{marge_brute(produit):.3f} DT  ({marge_pct(produit):.1f} %)")
    t.add_row("",                     "")
    t.add_row("🔢 Quantité actuelle", f"[{couleur}]{produit['quantite']} {produit['unite']}[/{couleur}]")
    t.add_row("⬇  Stock minimum",     f"{produit['stock_min']}")
    t.add_row("⬆  Stock maximum",     f"{produit['stock_max']}")
    t.add_row("💵 Valeur du stock",   f"[green]{valeur_stock(produit):.3f} DT[/green]")
    t.add_row("",                     "")
    t.add_row("📅 Expiration",        exp_txt)
    t.add_row("🗓️  Créé le",           produit["date_creation"])

    if produit.get("date_modification"):
        t.add_row("✏️  Modifié le",     produit["date_modification"])

    # Couleur du Panel selon l'état
    couleur_panel = {
        "rupture": "red",
        "alerte" : "yellow",
        "surplus": "magenta",
        "ok"     : "green",
    }[code]

    console.print(Panel(
        t,
        title=f"[bold white] FICHE PRODUIT — {produit['reference']} "
              f"[{couleur}]{libelle}[/{couleur}] [/bold white]",
        border_style=couleur_panel,
        padding=(1, 2),
    ))


# ── Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    console.rule("[bold cyan]TEST — MODÈLE PRODUIT[/bold cyan]")
    console.print()

    produits_test = [
        creer_produit("MED-001", "Paracétamol 500mg",     "Analgésique",    "boîte",
                      3.500,  5.800, 250, 50, 500,  "SIPHAT",    "31/12/2025"),
        creer_produit("MED-002", "Amoxicilline 1g",       "Antibiotique",   "boîte",
                      8.200, 12.500,  15, 30, 200,  "ADWYA",     "30/06/2025"),
        creer_produit("MED-003", "Metformine 850mg",      "Diabétologie",   "boîte",
                      3.800,  6.500,   0, 30, 200,  "PHARMAGHREB","31/03/2026"),
        creer_produit("MAT-001", "Seringues 5ml ×100",   "Matériel",       "boîte",
                     12.000, 18.000,  45, 10, 100,  "MEDIS"),
    ]

    for p in produits_test:
        afficher_fiche(p)
        console.print()


# ══════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — Tuple de retour dans etat_stock()
#     Retourner (code, libellé, couleur) en une seule valeur
#     est élégant : l'appelant peut ignorer ce dont il n'a pas
#     besoin avec _  :  code, _, couleur = etat_stock(p)
#
#  💡 ASTUCE — .strftime() / .strptime()
#     strftime = datetime → chaîne  ("format to string")
#     strptime = chaîne  → datetime ("parse from string")
#     Format "%d/%m/%Y" = JJ/MM/AAAA, standard en français.
#
#  💡 ASTUCE — float() et int() dans creer_produit()
#     Forcer la conversion garantit qu'un prix passé en str
#     ("3.5") sera bien stocké comme float. Défense proactive
#     contre les erreurs de type en aval.
#
#  🏋️  EXERCICE
#     1. Ajouter un champ "code_barre" (str, optionnel) dans
#        creer_produit() et l'afficher dans la fiche.
#     2. Écrire une fonction taux_rotation(produit, sorties_mois)
#        qui retourne quantite / sorties_mois (vitesse d'écoulement).
#     3. Colorier la marge en rouge si < 15 %, en jaune si < 30 %,
#        en vert sinon.
# ══════════════════════════════════════════════════════════════════════