"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 04  ·  Catalogue & Dashboard       ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Afficher un catalogue complet et des indicateurs clés (KPI)      ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    liste de dicts · boucles for · sum() · sorted() · lambda        ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Table avec en-tête · row_styles · Columns · Panel               ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import datetime
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich.columns import Columns

console = Console()

# ─── Import des fonctions de l'étape précédente ───────────────────────
# En production, on ferait :  from etape_03 import creer_produit, …
# Ici on recopie pour que chaque étape soit autonome.

def creer_produit(ref, nom, cat, unite, pa, pv, qte, smi, sma, fourn, exp=None):
    return {
        "reference": ref.upper(), "nom": nom, "categorie": cat, "unite": unite,
        "prix_achat": float(pa), "prix_vente": float(pv),
        "quantite": int(qte), "stock_min": int(smi), "stock_max": int(sma),
        "fournisseur": fourn, "date_expiration": exp,
        "date_creation": datetime.date.today().strftime("%d/%m/%Y"),
        "date_modification": None,
    }

def etat_stock(p):
    q = p["quantite"]
    if q == 0:              return ("rupture", "⛔ RUPTURE",  "bold red")
    if q <= p["stock_min"]: return ("alerte",  "⚠  ALERTE",   "bold yellow")
    if q >  p["stock_max"]: return ("surplus", "↑  SURPLUS",  "bold magenta")
    return                         ("ok",      "✅ OK",        "bold green")

def valeur_stock(p):  return p["prix_achat"] * p["quantite"]
def marge_pct(p):
    return ((p["prix_vente"] - p["prix_achat"]) / p["prix_achat"] * 100) \
           if p["prix_achat"] else 0

def jours_exp(p):
    if not p["date_expiration"]: return None
    try:
        return (datetime.datetime.strptime(p["date_expiration"], "%d/%m/%Y").date()
                - datetime.date.today()).days
    except ValueError: return None


# ─── Données de démonstration ─────────────────────────────────────────

def catalogue_demo():
    return [
        creer_produit("MED-001","Paracétamol 500mg",    "Analgésique",   "boîte",  3.500, 5.800, 250, 50, 500, "SIPHAT",     "31/12/2025"),
        creer_produit("MED-002","Ibuprofène 400mg",     "Analgésique",   "boîte",  4.200, 7.200,  18, 30, 300, "ADWYA",      "30/09/2025"),
        creer_produit("MED-003","Amoxicilline 1g",      "Antibiotique",  "boîte",  8.200,12.500,   5, 20, 200, "ADWYA",      "30/06/2025"),
        creer_produit("MED-004","Oméprazole 20mg",      "Gastro",        "boîte",  5.100, 8.900, 120, 40, 400, "SIPHAT",     "28/02/2026"),
        creer_produit("MED-005","Metformine 850mg",     "Diabétologie",  "boîte",  3.800, 6.500,   0, 30, 200, "PHARMAGHREB","31/03/2026"),
        creer_produit("MED-006","Amlodipine 5mg",       "Cardiologie",   "boîte",  6.200, 9.800, 600, 50, 400, "SIPHAT",     "31/01/2027"),
        creer_produit("MAT-001","Seringues 5ml ×100",   "Matériel",      "boîte", 12.000,18.000,  45, 10, 100, "MEDIS"),
        creer_produit("MAT-002","Gants latex M ×100",   "Matériel",      "boîte",  8.500,14.000,   8, 15, 120, "MEDIS"),
        creer_produit("MAT-003","Compresses 10×10 ×50", "Matériel",      "sachet", 4.200, 7.500, 200, 50, 500, "SIPHAT",     "31/12/2026"),
        creer_produit("PAR-001","Vitamine C 1000mg",    "Parapharmacie", "boîte",  6.800,11.500,  90, 30, 300, "PHARMAGHREB","30/11/2025"),
        creer_produit("PAR-002","Crème hydratante 200ml","Dermatologie", "tube",  14.000,22.000,  32, 15, 150, "COSMEPHARM"),
        creer_produit("PAR-003","Baume pédiatrique",    "Pédiatrie",     "tube",   9.500,15.000,   3, 10, 100, "COSMEPHARM", "30/09/2025"),
    ]


# ─── 1. Tableau catalogue complet ─────────────────────────────────────

def afficher_catalogue(catalogue, titre="CATALOGUE DES PRODUITS"):
    """Affiche tous les produits dans un tableau coloré professionnel."""

    t = Table(
        title=f"[bold white]{titre}[/bold white]",
        border_style="cyan",
        header_style="bold cyan on dark_blue",
        row_styles=["on grey7", ""],          # alternance de fond
        show_lines=True,
        min_width=110,
    )

    t.add_column("Réf.",       style="bold yellow",  width=10)
    t.add_column("Nom",        style="white",         width=26)
    t.add_column("Catégorie",  style="cyan",          width=15)
    t.add_column("Unité",      style="dim white",     width=8)
    t.add_column("P.Achat",    justify="right",       width=10)
    t.add_column("P.Vente",    style="green",justify="right", width=10)
    t.add_column("Marge",      style="magenta",justify="right",width=8)
    t.add_column("Stock",      justify="right",       width=7)
    t.add_column("Statut",     justify="center",      width=12)
    t.add_column("Expiration", width=13)

    for p in catalogue:
        code, libelle, couleur = etat_stock(p)
        qte_txt    = f"[{couleur}]{p['quantite']}[/{couleur}]"
        statut_txt = f"[{couleur}]{libelle}[/{couleur}]"

        # Expiration colorée
        j = jours_exp(p)
        if j is None:
            exp_txt = "[dim]—[/dim]"
        elif j < 0:
            exp_txt = "[bold red]EXPIRÉ[/bold red]"
        elif j < 30:
            exp_txt = f"[bold red]{p['date_expiration']}[/bold red]"
        elif j < 90:
            exp_txt = f"[yellow]{p['date_expiration']}[/yellow]"
        else:
            exp_txt = f"[dim white]{p['date_expiration']}[/dim white]"

        t.add_row(
            p["reference"], p["nom"], p["categorie"], p["unite"],
            f"{p['prix_achat']:.3f}",
            f"{p['prix_vente']:.3f}",
            f"{marge_pct(p):.1f}%",
            qte_txt, statut_txt, exp_txt,
        )

    console.print(t)


# ─── 2. Tableau de bord KPI ───────────────────────────────────────────

def afficher_dashboard(catalogue):
    """Affiche les indicateurs clés du stock (KPI)."""

    total      = len(catalogue)
    ruptures   = [p for p in catalogue if etat_stock(p)[0] == "rupture"]
    alertes    = [p for p in catalogue if etat_stock(p)[0] == "alerte"]
    surplus    = [p for p in catalogue if etat_stock(p)[0] == "surplus"]
    ok_list    = [p for p in catalogue if etat_stock(p)[0] == "ok"]
    val_tot    = sum(valeur_stock(p) for p in catalogue)
    marge_moy  = sum(marge_pct(p) for p in catalogue) / total if total else 0

    # Compter par catégorie
    categories = {}
    for p in catalogue:
        categories[p["categorie"]] = categories.get(p["categorie"], 0) + 1

    # ── Panneau KPI ──────────────────────────────────────────────────
    kpi = Table(show_header=False, box=None, padding=(0, 2))
    kpi.add_column(style="dim cyan",   width=26)
    kpi.add_column(justify="right",    width=14)

    kpi.add_row("📦 Articles en catalogue",  f"[bold white]{total}[/bold white]")
    kpi.add_row("✅ Stock normal",            f"[bold green]{len(ok_list)}[/bold green]")
    kpi.add_row("⚠  En alerte réappro.",     f"[bold yellow]{len(alertes)}[/bold yellow]")
    kpi.add_row("⛔ En rupture",              f"[bold red]{len(ruptures)}[/bold red]")
    kpi.add_row("↑  En surplus",             f"[bold magenta]{len(surplus)}[/bold magenta]")
    kpi.add_row("",                           "")
    kpi.add_row("💵 Valeur totale du stock",  f"[bold green]{val_tot:,.3f} DT[/bold green]")
    kpi.add_row("📈 Marge moyenne",           f"[bold cyan]{marge_moy:.1f} %[/bold cyan]")

    # ── Panneau catégories ───────────────────────────────────────────
    cat_t = Table(show_header=False, box=None, padding=(0, 2))
    cat_t.add_column(style="cyan",   width=20)
    cat_t.add_column(justify="right",width=8)

    for cat, nb in sorted(categories.items(), key=lambda x: -x[1]):
        cat_t.add_row(cat, f"[white]{nb}[/white]")

    # ── Produits critiques ───────────────────────────────────────────
    critiques = sorted(
        [p for p in catalogue if etat_stock(p)[0] in ("rupture", "alerte")],
        key=lambda p: p["quantite"]
    )[:5]

    crit_t = Table(show_header=False, box=None, padding=(0, 2))
    crit_t.add_column(style="yellow", width=10)
    crit_t.add_column(style="white",  width=22)
    crit_t.add_column(justify="right",width=8)

    for p in critiques:
        code, _, couleur = etat_stock(p)
        crit_t.add_row(
            p["reference"], p["nom"][:20],
            f"[{couleur}]{p['quantite']}[/{couleur}]"
        )

    # ── Mise en page côte à côte ─────────────────────────────────────
    console.print(Columns([
        Panel(kpi,    title="[bold white]📊 INDICATEURS[/bold white]",  border_style="blue",   width=46),
        Panel(cat_t,  title="[bold white]📂 CATÉGORIES[/bold white]",   border_style="cyan",   width=34),
        Panel(crit_t, title="[bold white]🚨 CRITIQUES[/bold white]",    border_style="red",    width=46),
    ]))


# ─── Point d'entrée ───────────────────────────────────────────────────
if __name__ == "__main__":
    cat = catalogue_demo()

    console.rule("[bold cyan]TABLEAU DE BORD[/bold cyan]")
    console.print()
    afficher_dashboard(cat)

    console.print()
    console.rule("[bold cyan]CATALOGUE COMPLET[/bold cyan]")
    console.print()
    afficher_catalogue(cat)
    console.print()


# ══════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — row_styles=["on grey7", ""]
#     Alternance de fond sur les lignes paires/impaires.
#     "grey7" est une teinte très sombre qui reste lisible.
#     Sur fond blanc : préférer ["on grey85", ""].
#
#  💡 ASTUCE — Columns() pour le layout horizontal
#     Columns([panel1, panel2, panel3]) place les panneaux
#     côte à côte, ajuste automatiquement si le terminal est
#     trop étroit. width= fixe la largeur de chaque panel.
#
#  💡 ASTUCE — sorted() avec lambda + clé négative
#     sorted(liste, key=lambda x: -x[1]) trie par ordre
#     décroissant sans passer reverse=True. Utile quand on
#     trie selon une valeur calculée.
#
#  🏋️  EXERCICE
#     1. Ajouter dans le dashboard le "Top 3 articles les plus
#        rentables" (triés par marge_pct décroissante).
#     2. Calculer et afficher le nombre de produits dont la date
#        d'expiration est dans moins de 90 jours.
#     3. Écrire afficher_catalogue_filtre(catalogue, categorie)
#        qui n'affiche que les produits d'une catégorie donnée.
# ══════════════════════════════════════════════════════════════════════