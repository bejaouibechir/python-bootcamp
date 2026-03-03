"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 11  ·  Rapports & Statistiques     ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Générer des rapports visuels : valorisation, marges, expirations ║
║    Top articles, analyses par catégorie et par fournisseur          ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    sum() · max() · min() · sorted() · dict · datetime · lambda      ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Table.add_section() · Columns · Panel imbriqués · couleurs KPI   ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import datetime
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich.columns import Columns

console = Console()

# ─── Helpers (reprises des étapes précédentes) ────────────────────────
def etat_stock(p):
    q = p["quantite"]
    if q == 0:               return ("rupture", "⛔ RUPTURE",  "bold red")
    if q <= p["stock_min"]:  return ("alerte",  "⚠  ALERTE",   "bold yellow")
    if q >  p["stock_max"]:  return ("surplus", "↑  SURPLUS",  "bold magenta")
    return                          ("ok",      "✅ OK",        "bold green")

def valeur_stock(p):  return p["prix_achat"] * p["quantite"]
def marge_pct(p):
    return ((p["prix_vente"] - p["prix_achat"]) / p["prix_achat"] * 100) \
           if p["prix_achat"] else 0
def jours_exp(p):
    if not p.get("date_expiration"): return None
    try:
        return (datetime.datetime.strptime(p["date_expiration"], "%d/%m/%Y").date()
                - datetime.date.today()).days
    except ValueError: return None


# ════════════════════════════════════════════════════════════════════
#  1. TABLEAU DE BORD COMPLET
# ════════════════════════════════════════════════════════════════════

def rapport_dashboard(catalogue, config=None):
    """
    Tableau de bord complet : KPI, catégories, alertes critiques.
    Tous les panneaux affichés côte à côte avec Columns().
    """
    devise = (config or {}).get("devise", "DT")
    total  = len(catalogue)

    if total == 0:
        console.print("[yellow]Le catalogue est vide.[/yellow]")
        return

    # ── Calculs globaux ───────────────────────────────────────────
    ruptures  = [p for p in catalogue if etat_stock(p)[0] == "rupture"]
    alertes   = [p for p in catalogue if etat_stock(p)[0] == "alerte"]
    surplus   = [p for p in catalogue if etat_stock(p)[0] == "surplus"]
    ok_list   = [p for p in catalogue if etat_stock(p)[0] == "ok"]
    val_tot   = sum(valeur_stock(p) for p in catalogue)
    marge_moy = sum(marge_pct(p) for p in catalogue) / total

    # Produits expirant dans 90 jours
    exp_proches = [p for p in catalogue
                   if jours_exp(p) is not None and 0 <= jours_exp(p) <= 90]

    # ── Panneau KPI ───────────────────────────────────────────────
    kpi = Table(show_header=False, box=None, padding=(0, 2))
    kpi.add_column(style="dim cyan",  width=26)
    kpi.add_column(justify="right",   width=14)

    kpi.add_row("📦 Articles en catalogue",  f"[bold white]{total}[/bold white]")
    kpi.add_row("✅ Stock normal",            f"[bold green]{len(ok_list)}[/bold green]")
    kpi.add_row("⚠  En alerte réappro.",     f"[bold yellow]{len(alertes)}[/bold yellow]")
    kpi.add_row("⛔ En rupture",              f"[bold red]{len(ruptures)}[/bold red]")
    kpi.add_row("↑  En surplus",             f"[bold magenta]{len(surplus)}[/bold magenta]")
    kpi.add_row("📅 Expirant < 90 j",        f"[bold yellow]{len(exp_proches)}[/bold yellow]")
    kpi.add_row("",                           "")
    kpi.add_row("💵 Valeur totale",           f"[bold green]{val_tot:,.3f} {devise}[/bold green]")
    kpi.add_row("📈 Marge moyenne",           f"[bold cyan]{marge_moy:.1f} %[/bold cyan]")

    # ── Panneau catégories ────────────────────────────────────────
    cats = {}
    for p in catalogue:
        c = p["categorie"]
        if c not in cats:
            cats[c] = {"nb": 0, "val": 0.0}
        cats[c]["nb"]  += 1
        cats[c]["val"] += valeur_stock(p)

    cat_t = Table(show_header=False, box=None, padding=(0, 2))
    cat_t.add_column(style="cyan",    width=20)
    cat_t.add_column(justify="right", width=6)
    cat_t.add_column(style="green",   width=14, justify="right")

    for cat, d in sorted(cats.items(), key=lambda x: -x[1]["val"]):
        cat_t.add_row(
            cat[:18],
            f"[white]{d['nb']}[/white]",
            f"{d['val']:,.0f} {devise}",
        )

    # ── Panneau produits critiques ────────────────────────────────
    critiques = sorted(
        [p for p in catalogue if etat_stock(p)[0] in ("rupture", "alerte")],
        key=lambda p: p["quantite"],
    )[:6]

    crit_t = Table(show_header=False, box=None, padding=(0, 2))
    crit_t.add_column(style="bold yellow", width=10)
    crit_t.add_column(style="white",       width=18)
    crit_t.add_column(justify="right",     width=8)

    for p in critiques:
        code, _, couleur = etat_stock(p)
        deficit = p["stock_min"] - p["quantite"]
        crit_t.add_row(
            p["reference"],
            p["nom"][:16],
            f"[{couleur}]{p['quantite']} / {p['stock_min']}[/{couleur}]",
        )

    console.print(Columns([
        Panel(kpi,    title="[bold white]📊 INDICATEURS[/bold white]",
              border_style="blue",    width=48),
        Panel(cat_t,  title="[bold white]📂 CATÉGORIES[/bold white]",
              border_style="cyan",    width=46),
        Panel(crit_t, title="[bold white]🚨 CRITIQUES[/bold white]",
              border_style="red",     width=42),
    ]))


# ════════════════════════════════════════════════════════════════════
#  2. VALORISATION DU STOCK PAR CATÉGORIE
# ════════════════════════════════════════════════════════════════════

def rapport_valorisation(catalogue, config=None):
    """
    Valeur du stock par catégorie avec totaux, pourcentages, marges.
    """
    devise = (config or {}).get("devise", "DT")

    # Regrouper par catégorie
    cats = {}
    for p in catalogue:
        c = p["categorie"]
        if c not in cats:
            cats[c] = {"nb": 0, "val_achat": 0.0, "val_vente": 0.0, "produits": []}
        cats[c]["nb"]        += 1
        cats[c]["val_achat"] += p["prix_achat"] * p["quantite"]
        cats[c]["val_vente"] += p["prix_vente"] * p["quantite"]
        cats[c]["produits"].append(p)

    total_achat = sum(d["val_achat"] for d in cats.values())
    total_vente = sum(d["val_vente"] for d in cats.values())

    t = Table(
        title="[bold white]VALORISATION DU STOCK[/bold white]",
        border_style="green",
        header_style="bold green on dark_green",
        show_lines=True,
    )
    t.add_column("Catégorie",      style="cyan",         width=18)
    t.add_column("Nbr",            justify="right",      width=5)
    t.add_column("Val. achat",     style="dim white",    width=14, justify="right")
    t.add_column("Val. vente",     style="bold green",   width=14, justify="right")
    t.add_column("Marge potent.",  style="magenta",      width=14, justify="right")
    t.add_column("% du stock",     justify="right",      width=10)

    for cat, d in sorted(cats.items(), key=lambda x: -x[1]["val_achat"]):
        marge_cat = d["val_vente"] - d["val_achat"]
        pct       = (d["val_achat"] / total_achat * 100) if total_achat else 0
        t.add_row(
            cat,
            str(d["nb"]),
            f"{d['val_achat']:,.3f} {devise}",
            f"{d['val_vente']:,.3f} {devise}",
            f"[green]+{marge_cat:,.3f}[/green]" if marge_cat >= 0
            else f"[red]{marge_cat:,.3f}[/red]",
            f"{pct:.1f} %",
        )

    # Ligne de total
    t.add_section()
    marge_totale = total_vente - total_achat
    t.add_row(
        "[bold white]TOTAL",
        f"[bold white]{len(catalogue)}",
        f"[bold white]{total_achat:,.3f} {devise}",
        f"[bold green]{total_vente:,.3f} {devise}",
        f"[bold green]+{marge_totale:,.3f}[/bold green]",
        "[bold white]100.0 %",
    )

    console.print(Panel(t, border_style="green"))


# ════════════════════════════════════════════════════════════════════
#  3. RAPPORT DES EXPIRATIONS
# ════════════════════════════════════════════════════════════════════

def rapport_expirations(catalogue, jours=90):
    """
    Liste des produits expirant dans les prochains jours,
    avec le coût financier (valeur à risque de perte).
    """
    produits_exp = []
    for p in catalogue:
        j = jours_exp(p)
        if j is not None:
            produits_exp.append((j, p))

    produits_exp.sort(key=lambda x: x[0])

    t = Table(
        title=f"[bold white]PRODUITS EXPIRANT DANS {jours} JOURS[/bold white]",
        border_style="yellow",
        header_style="bold yellow",
        show_lines=True,
    )
    t.add_column("Jours",        justify="right",    width=8)
    t.add_column("Réf.",         style="bold yellow", width=10)
    t.add_column("Nom",          style="white",       width=24)
    t.add_column("Expiration",   width=13)
    t.add_column("Stock",        justify="right",     width=8)
    t.add_column("Valeur risque",style="bold red",    width=16, justify="right")

    total_risque = 0.0
    nb_affiches  = 0

    for j, p in produits_exp:
        if j > jours:
            continue

        val = valeur_stock(p)
        total_risque += val
        nb_affiches  += 1

        if j < 0:
            coul, badge = "bold red",    "⛔ EXPIRÉ"
        elif j < 30:
            coul, badge = "bold red",    "🔴 URGENT"
        else:
            coul, badge = "bold yellow", "🟡 BIENTÔT"

        t.add_row(
            f"[{coul}]{j}[/{coul}]",
            p["reference"],
            p["nom"][:22],
            f"[{coul}]{p['date_expiration']}[/{coul}]",
            str(p["quantite"]),
            f"[{coul}]{val:.3f} DT[/{coul}]",
        )

    if nb_affiches == 0:
        console.print(Panel(
            f"[green]✓  Aucun produit n'expire dans les {jours} prochains jours.[/green]",
            border_style="green",
        ))
        return

    t.add_section()
    t.add_row(
        "", "", "", f"[bold white]{nb_affiches} produit(s)", "",
        f"[bold red]{total_risque:.3f} DT[/bold red]",
    )
    console.print(Panel(t, border_style="yellow"))


# ════════════════════════════════════════════════════════════════════
#  4. ANALYSE DES MARGES
# ════════════════════════════════════════════════════════════════════

def rapport_marges(catalogue, top=5):
    """
    Top N et Flop N des marges, plus analyse par catégorie.
    """
    if not catalogue:
        console.print("[yellow]Catalogue vide.[/yellow]")
        return

    tries = sorted(catalogue, key=lambda p: marge_pct(p), reverse=True)

    # ── Tableau top + flop ────────────────────────────────────────
    t = Table(
        title=f"[bold white]ANALYSE DES MARGES — TOP / FLOP {top}[/bold white]",
        border_style="magenta",
        header_style="bold magenta",
        show_lines=True,
    )
    t.add_column("Rang",        justify="center",   width=6)
    t.add_column("Réf.",        style="bold yellow", width=10)
    t.add_column("Nom",         style="white",       width=24)
    t.add_column("P.Achat",     justify="right",     width=10)
    t.add_column("P.Vente",     justify="right",     width=10)
    t.add_column("Marge %",     justify="right",     width=10)
    t.add_column("Marge DT",    justify="right",     width=10)

    def ligne_marge(rang_str, p, couleur_rang):
        m_pct = marge_pct(p)
        m_dt  = p["prix_vente"] - p["prix_achat"]
        coul  = "green" if m_pct >= 30 else "yellow" if m_pct >= 15 else "red"
        t.add_row(
            f"[{couleur_rang}]{rang_str}[/{couleur_rang}]",
            p["reference"], p["nom"][:22],
            f"{p['prix_achat']:.3f}",
            f"{p['prix_vente']:.3f}",
            f"[{coul}]{m_pct:.1f} %[/{coul}]",
            f"[{coul}]{m_dt:.3f} DT[/{coul}]",
        )

    # Top
    for i, p in enumerate(tries[:top], 1):
        ligne_marge(f"🥇 {i}", p, "bold green")

    t.add_section()

    # Flop
    for i, p in enumerate(reversed(tries[-top:]), 1):
        ligne_marge(f"⚠ -{i}", p, "bold red")

    console.print(Panel(t, border_style="magenta"))

    # ── Moyennes par catégorie ────────────────────────────────────
    cats = {}
    for p in catalogue:
        c = p["categorie"]
        if c not in cats: cats[c] = []
        cats[c].append(marge_pct(p))

    cat_t = Table(show_header=False, box=None, padding=(0, 3))
    cat_t.add_column(style="cyan",  width=22)
    cat_t.add_column(justify="right", width=10)

    for cat, marges in sorted(cats.items(), key=lambda x: -sum(x[1])/len(x[1])):
        moy = sum(marges) / len(marges)
        coul = "green" if moy >= 30 else "yellow" if moy >= 15 else "red"
        cat_t.add_row(cat, f"[{coul}]{moy:.1f} %[/{coul}]")

    console.print(Panel(
        cat_t,
        title="[bold white]Marge moyenne par catégorie[/bold white]",
        border_style="dim magenta",
    ))


# ════════════════════════════════════════════════════════════════════
#  5. RAPPORT PAR FOURNISSEUR
# ════════════════════════════════════════════════════════════════════

def rapport_fournisseur(catalogue, fournisseur, config=None):
    """
    Résumé détaillé de tous les produits d'un fournisseur.
    """
    devise   = (config or {}).get("devise", "DT")
    produits = [p for p in catalogue
                if p["fournisseur"].lower() == fournisseur.lower()]

    if not produits:
        console.print(f"[yellow]Aucun produit du fournisseur '{fournisseur}'.[/yellow]")
        return

    val_tot  = sum(valeur_stock(p) for p in produits)
    marge_m  = sum(marge_pct(p) for p in produits) / len(produits)
    ruptures = sum(1 for p in produits if p["quantite"] == 0)
    alertes  = sum(1 for p in produits if 0 < p["quantite"] <= p["stock_min"])

    t = Table(
        title=f"[bold white]FOURNISSEUR : {fournisseur.upper()}[/bold white]",
        border_style="cyan",
        header_style="bold cyan",
        show_lines=True,
    )
    t.add_column("Réf.",      style="bold yellow", width=10)
    t.add_column("Nom",       style="white",       width=26)
    t.add_column("P.Achat",   justify="right",     width=10)
    t.add_column("P.Vente",   justify="right",     width=10)
    t.add_column("Marge",     justify="right",     width=8)
    t.add_column("Stock",     justify="right",     width=7)
    t.add_column("Valeur",    justify="right",     width=14)
    t.add_column("Statut",    justify="center",    width=12)

    for p in sorted(produits, key=lambda x: x["nom"]):
        code, libelle, couleur = etat_stock(p)
        t.add_row(
            p["reference"], p["nom"][:24],
            f"{p['prix_achat']:.3f}",
            f"{p['prix_vente']:.3f}",
            f"{marge_pct(p):.1f}%",
            f"[{couleur}]{p['quantite']}[/{couleur}]",
            f"[green]{valeur_stock(p):.3f} {devise}[/green]",
            f"[{couleur}]{libelle}[/{couleur}]",
        )

    t.add_section()
    t.add_row(
        "", f"[white]{len(produits)} articles", "", "",
        f"[cyan]{marge_m:.1f}%[/cyan]",
        f"[red]{ruptures} rupt.[/red]",
        f"[bold green]{val_tot:.3f} {devise}[/bold green]",
        f"[yellow]{alertes} alert.[/yellow]",
    )

    console.print(Panel(t, border_style="cyan"))


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
        {"reference":"MED-004","nom":"Oméprazole 20mg","categorie":"Gastro","unite":"boîte",
         "prix_achat":5.1,"prix_vente":8.9,"quantite":120,"stock_min":40,"stock_max":400,
         "fournisseur":"SIPHAT","date_expiration":"28/02/2026",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MED-005","nom":"Metformine 850mg","categorie":"Diabétologie","unite":"boîte",
         "prix_achat":3.8,"prix_vente":6.5,"quantite":0,"stock_min":30,"stock_max":200,
         "fournisseur":"PHARMAGHREB","date_expiration":"31/03/2026",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MAT-001","nom":"Seringues 5ml ×100","categorie":"Matériel","unite":"boîte",
         "prix_achat":12.0,"prix_vente":18.0,"quantite":45,"stock_min":10,"stock_max":100,
         "fournisseur":"MEDIS","date_expiration":None,
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"PAR-001","nom":"Vitamine C 1000mg","categorie":"Parapharmacie","unite":"boîte",
         "prix_achat":6.8,"prix_vente":11.5,"quantite":90,"stock_min":30,"stock_max":300,
         "fournisseur":"PHARMAGHREB","date_expiration":"30/11/2025",
         "date_creation":"01/01/2024","date_modification":None},
    ]

    config = {"devise": "DT"}

    console.rule("[bold cyan]TABLEAU DE BORD[/bold cyan]")
    rapport_dashboard(catalogue_test, config)

    console.print()
    console.rule("[bold cyan]VALORISATION[/bold cyan]")
    rapport_valorisation(catalogue_test, config)

    console.print()
    console.rule("[bold cyan]MARGES[/bold cyan]")
    rapport_marges(catalogue_test, top=3)

    console.print()
    console.rule("[bold cyan]EXPIRATIONS[/bold cyan]")
    rapport_expirations(catalogue_test, jours=365)

    console.print()
    console.rule("[bold cyan]FOURNISSEUR SIPHAT[/bold cyan]")
    rapport_fournisseur(catalogue_test, "SIPHAT", config)


# ════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — t.add_section()
#     Ajoute une ligne séparatrice dans un tableau Rich.
#     Parfait pour séparer les données d'un total en bas.
#     Sans elle, le total se mélange visuellement aux lignes.
#
#  💡 ASTUCE — sorted avec lambda complexe
#     sorted(cats.items(), key=lambda x: -sum(x[1])/len(x[1]))
#     x[0] = clé du dict (catégorie), x[1] = valeur (liste de marges)
#     Ce pattern permet de trier par une valeur calculée à la volée.
#
#  💡 ASTUCE — Columns() adaptatif
#     Si le terminal est trop étroit, Columns() empile les panneaux
#     verticalement automatiquement. Aucune gestion manuelle nécessaire.
#
#  🏋️  EXERCICE
#     1. Écrire rapport_rotation(catalogue, historique) qui calcule
#        le nombre de sorties par article sur les 30 derniers jours.
#     2. Ajouter dans rapport_valorisation() une colonne
#        "Nb jours de stock" = quantite / (ventes_moy_jour).
#     3. Écrire rapport_comparatif(cat_actuel, cat_precedent)
#        qui compare deux états du catalogue (hausse/baisse par article).
# ════════════════════════════════════════════════════════════════════