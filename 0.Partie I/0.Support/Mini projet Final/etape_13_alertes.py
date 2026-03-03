"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 13  ·  Alertes & Notifications     ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Créer un système d'alertes automatiques : stock critique,        ║
║    expirations proches, marges négatives, surplus                   ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    conditions · boucles · datetime · list comprehension · dict      ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Panel imbriqués · couleurs d'urgence · Columns · Table alertes   ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import datetime
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich.columns import Columns
from rich.text    import Text

console = Console()

# ─── Helpers ─────────────────────────────────────────────────────────
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
#  1. MOTEUR D'ANALYSE DES ALERTES
# ════════════════════════════════════════════════════════════════════

def analyser_alertes(catalogue, config=None):
    """
    Parcourt le catalogue et collecte toutes les alertes.

    Retourne un dictionnaire structuré :
    {
        'ruptures'            : [produit, …],
        'alertes_stock'       : [produit, …],
        'surplus'             : [produit, …],
        'expirations_urgentes': [(jours, produit), …],   # < 30 jours
        'expirations_proches' : [(jours, produit), …],   # 30–90 jours
        'marges_negatives'    : [produit, …],
    }

    Cette fonction ne fait PAS d'affichage.
    Elle est appelée par toutes les fonctions d'affichage.
    """
    seuil_urgent = (config or {}).get("seuil_exp_urgent", 30)
    seuil_proche = (config or {}).get("seuil_exp_proche", 90)

    resultats = {
        "ruptures"            : [],
        "alertes_stock"       : [],
        "surplus"             : [],
        "expirations_urgentes": [],
        "expirations_proches" : [],
        "marges_negatives"    : [],
    }

    for p in catalogue:
        code = etat_stock(p)[0]

        # ── Stock ─────────────────────────────────────────────────
        if code == "rupture":
            resultats["ruptures"].append(p)
        elif code == "alerte":
            resultats["alertes_stock"].append(p)
        elif code == "surplus":
            resultats["surplus"].append(p)

        # ── Expirations ───────────────────────────────────────────
        j = jours_exp(p)
        if j is not None:
            if j <= seuil_urgent:
                resultats["expirations_urgentes"].append((j, p))
            elif j <= seuil_proche:
                resultats["expirations_proches"].append((j, p))

        # ── Marge négative ────────────────────────────────────────
        if marge_pct(p) < 0:
            resultats["marges_negatives"].append(p)

    # Trier les expirations par urgence croissante (plus urgent en premier)
    resultats["expirations_urgentes"].sort(key=lambda x: x[0])
    resultats["expirations_proches"].sort(key=lambda x: x[0])

    return resultats


def compter_alertes(alertes):
    """Retourne le nombre total d'alertes critiques."""
    return (
        len(alertes["ruptures"])
        + len(alertes["alertes_stock"])
        + len(alertes["expirations_urgentes"])
        + len(alertes["marges_negatives"])
    )


# ════════════════════════════════════════════════════════════════════
#  2. BADGE D'ALERTE COMPACT (pour l'entête du menu)
# ════════════════════════════════════════════════════════════════════

def badge_alertes(catalogue, config=None):
    """
    Retourne un texte Rich court pour afficher dans l'en-tête.
    Ex : "[bold red]⛔ 2 ruptures[/bold red]  [yellow]⚠ 3 alertes[/yellow]"
    ou  "[green]✓ Stock en bon état[/green]"
    """
    alertes = analyser_alertes(catalogue, config)
    parties = []

    if alertes["ruptures"]:
        n = len(alertes["ruptures"])
        parties.append(f"[bold red]⛔ {n} rupture{'s' if n > 1 else ''}[/bold red]")

    if alertes["alertes_stock"]:
        n = len(alertes["alertes_stock"])
        parties.append(f"[bold yellow]⚠  {n} alerte{'s' if n > 1 else ''} stock[/bold yellow]")

    if alertes["expirations_urgentes"]:
        n = len(alertes["expirations_urgentes"])
        parties.append(f"[bold red]📅 {n} expiration{'s' if n > 1 else ''} urgente{'s' if n > 1 else ''}[/bold red]")

    if alertes["marges_negatives"]:
        n = len(alertes["marges_negatives"])
        parties.append(f"[bold magenta]📉 {n} marge{'s' if n > 1 else ''} négative{'s' if n > 1 else ''}[/bold magenta]")

    if not parties:
        return "[bold green]✓  Stock en bon état[/bold green]"

    return "  |  ".join(parties)


# ════════════════════════════════════════════════════════════════════
#  3. BULLETIN D'ALERTES COMPLET
# ════════════════════════════════════════════════════════════════════

def afficher_bulletin_alertes(catalogue, config=None):
    """
    Bulletin d'alerte complet affiché à l'ouverture ou sur demande.
    Structure : résumé → ruptures → alertes → expirations → marges
    """
    alertes = analyser_alertes(catalogue, config)
    devise  = (config or {}).get("devise", "DT")
    total   = compter_alertes(alertes)

    # ── Aucune alerte ─────────────────────────────────────────────
    if total == 0:
        console.print(Panel(
            "[bold green]✓  Aucune alerte détectée.\n"
            "[dim white]Tous les stocks sont dans les seuils normaux.[/dim white][/bold green]",
            title="[bold green]📋  BULLETIN D'ALERTES[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))
        return

    # ── Résumé haut de page ───────────────────────────────────────
    resume = Text()
    resume.append(f"  {total} alerte(s) requièrent votre attention\n\n",
                  style="bold white")
    if alertes["ruptures"]:
        resume.append(f"  ⛔  {len(alertes['ruptures'])} rupture(s) de stock\n",
                      style="bold red")
    if alertes["alertes_stock"]:
        resume.append(f"  ⚠   {len(alertes['alertes_stock'])} alerte(s) de réapprovisionnement\n",
                      style="bold yellow")
    if alertes["expirations_urgentes"]:
        resume.append(f"  📅  {len(alertes['expirations_urgentes'])} expiration(s) urgente(s)\n",
                      style="bold red")
    if alertes["marges_negatives"]:
        resume.append(f"  📉  {len(alertes['marges_negatives'])} produit(s) à marge négative\n",
                      style="bold magenta")

    console.print(Panel(
        resume,
        title="[bold red]🚨  BULLETIN D'ALERTES[/bold red]",
        border_style="red",
        padding=(0, 1),
    ))
    console.print()

    # ── Tableau ruptures + alertes stock ──────────────────────────
    produits_critiques = alertes["ruptures"] + alertes["alertes_stock"]
    if produits_critiques:
        t = Table(
            border_style="red",
            header_style="bold red",
            show_lines=True,
            row_styles=["on grey7", ""],
        )
        t.add_column("Réf.",         style="bold yellow",  width=10)
        t.add_column("Nom",          style="white",        width=24)
        t.add_column("Catégorie",    style="cyan",         width=14)
        t.add_column("Stock actuel", justify="right",      width=12)
        t.add_column("Seuil min",    justify="right",      width=10)
        t.add_column("Déficit",      style="bold red",     width=10, justify="right")
        t.add_column("Coût réappro.",style="bold yellow",  width=14, justify="right")

        for p in sorted(produits_critiques, key=lambda x: x["quantite"]):
            deficit    = p["stock_min"] - p["quantite"]
            cout_reappro = deficit * p["prix_achat"]
            code, _, couleur = etat_stock(p)
            t.add_row(
                p["reference"],
                p["nom"][:22],
                p["categorie"][:12],
                f"[{couleur}]{p['quantite']}[/{couleur}]",
                str(p["stock_min"]),
                f"[bold red]-{deficit}[/bold red]",
                f"[yellow]{cout_reappro:.3f} {devise}[/yellow]",
            )

        titre = (
            f"[bold red]⛔ RUPTURES ({len(alertes['ruptures'])})  "
            f"⚠  ALERTES STOCK ({len(alertes['alertes_stock'])})[/bold red]"
        )
        console.print(Panel(t, title=titre, border_style="red"))
        console.print()

    # ── Expirations urgentes ───────────────────────────────────────
    if alertes["expirations_urgentes"]:
        t2 = Table(
            border_style="red",
            header_style="bold red",
            show_lines=True,
        )
        t2.add_column("Jours",       justify="right",     width=8)
        t2.add_column("Réf.",        style="bold yellow",  width=10)
        t2.add_column("Nom",         style="white",        width=24)
        t2.add_column("Expiration",  width=13)
        t2.add_column("Stock",       justify="right",      width=8)
        t2.add_column("Valeur risque",style="bold red",    width=14, justify="right")

        val_risque_tot = 0.0
        for j, p in alertes["expirations_urgentes"]:
            val = valeur_stock(p)
            val_risque_tot += val
            coul = "bold red" if j <= 0 else "red"
            badge = "⛔ EXPIRÉ" if j <= 0 else "🔴 URGENT"
            t2.add_row(
                f"[{coul}]{j}[/{coul}]",
                p["reference"],
                p["nom"][:22],
                f"[{coul}]{p['date_expiration']}[/{coul}]",
                str(p["quantite"]),
                f"[{coul}]{val:.3f} {devise}[/{coul}]",
            )

        t2.add_section()
        t2.add_row("", "", "", "",
                   f"[white]{len(alertes['expirations_urgentes'])}",
                   f"[bold red]{val_risque_tot:.3f} {devise}[/bold red]")

        console.print(Panel(
            t2,
            title=f"[bold red]📅 EXPIRATIONS URGENTES ({len(alertes['expirations_urgentes'])})[/bold red]",
            border_style="red",
        ))
        console.print()

    # ── Marges négatives ──────────────────────────────────────────
    if alertes["marges_negatives"]:
        t3 = Table(
            border_style="magenta",
            header_style="bold magenta",
            show_lines=False,
        )
        t3.add_column("Réf.",      style="bold yellow", width=10)
        t3.add_column("Nom",       style="white",       width=24)
        t3.add_column("P.Achat",   justify="right",     width=10)
        t3.add_column("P.Vente",   justify="right",     width=10)
        t3.add_column("Marge",     style="bold red",    width=10, justify="right")

        for p in alertes["marges_negatives"]:
            t3.add_row(
                p["reference"],
                p["nom"][:22],
                f"{p['prix_achat']:.3f}",
                f"{p['prix_vente']:.3f}",
                f"[bold red]{marge_pct(p):.1f} %[/bold red]",
            )

        console.print(Panel(
            t3,
            title=f"[bold magenta]📉 MARGES NÉGATIVES ({len(alertes['marges_negatives'])})[/bold magenta]",
            border_style="magenta",
        ))


# ════════════════════════════════════════════════════════════════════
#  4. ALERTES EXPIRATIONS PROCHES (moins urgentes)
# ════════════════════════════════════════════════════════════════════

def afficher_expirations_proches(catalogue, config=None):
    """
    Affiche les produits dont l'expiration approche (30–90 jours).
    Séparé du bulletin principal pour éviter de le surcharger.
    """
    alertes = analyser_alertes(catalogue, config)
    proches = alertes["expirations_proches"]
    devise  = (config or {}).get("devise", "DT")

    if not proches:
        console.print("[green]✓  Aucun produit n'expire dans les 90 prochains jours.[/green]")
        return

    t = Table(
        title="[bold white]EXPIRATIONS DANS 30–90 JOURS[/bold white]",
        border_style="yellow",
        header_style="bold yellow",
        show_lines=True,
        row_styles=["on grey7", ""],
    )
    t.add_column("Jours",       justify="right",     width=8)
    t.add_column("Réf.",        style="bold yellow",  width=10)
    t.add_column("Nom",         style="white",        width=24)
    t.add_column("Expiration",  width=13)
    t.add_column("Catégorie",   style="cyan",         width=14)
    t.add_column("Stock",       justify="right",      width=8)

    for j, p in proches:
        t.add_row(
            f"[yellow]{j}[/yellow]",
            p["reference"],
            p["nom"][:22],
            f"[yellow]{p['date_expiration']}[/yellow]",
            p["categorie"][:12],
            str(p["quantite"]),
        )

    console.print(Panel(t, border_style="yellow"))


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
         "prix_achat":8.2,"prix_vente":12.5,"quantite":0,"stock_min":20,"stock_max":200,
         "fournisseur":"ADWYA","date_expiration":"30/06/2025",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MED-004","nom":"Asprine 500mg","categorie":"Analgésique","unite":"boîte",
         "prix_achat":6.0,"prix_vente":5.5,"quantite":40,"stock_min":10,"stock_max":100,
         "fournisseur":"SIPHAT","date_expiration":"28/02/2026",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MAT-001","nom":"Seringues 5ml","categorie":"Matériel","unite":"boîte",
         "prix_achat":12.0,"prix_vente":18.0,"quantite":600,"stock_min":10,"stock_max":100,
         "fournisseur":"MEDIS","date_expiration":None,
         "date_creation":"01/01/2024","date_modification":None},
    ]

    config = {"devise": "DT", "seuil_exp_urgent": 30, "seuil_exp_proche": 90}

    console.rule("[bold cyan]TEST — BADGE D'ALERTES[/bold cyan]")
    console.print(badge_alertes(catalogue_test, config))

    console.print()
    console.rule("[bold cyan]BULLETIN COMPLET[/bold cyan]")
    afficher_bulletin_alertes(catalogue_test, config)

    console.print()
    console.rule("[bold cyan]EXPIRATIONS PROCHES[/bold cyan]")
    afficher_expirations_proches(catalogue_test, config)


# ════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — Séparer analyse et affichage
#     analyser_alertes() collecte les données sans les afficher.
#     Cela permet de l'appeler depuis l'en-tête (badge court)
#     ET depuis le bulletin complet, sans dupliquer la logique.
#
#  💡 ASTUCE — .sort() vs sorted()
#     resultats["expirations_urgentes"].sort(key=lambda x: x[0])
#     trie EN PLACE (modifie la liste directement).
#     C'est acceptable ici car resultats est un dict local,
#     pas le catalogue original.
#
#  💡 ASTUCE — Text() pour les textes composites
#     Text() de Rich permet d'assembler du texte avec des styles
#     différents sur chaque portion, puis de le passer à Panel()
#     ou console.print() en un seul bloc.
#
#  🏋️  EXERCICE
#     1. Ajouter une alerte "prix de vente non mis à jour"
#        pour les produits dont le prix n'a pas changé depuis > 6 mois.
#     2. Calculer le "coût total de réapprovisionnement" de toutes
#        les ruptures + alertes et l'afficher dans le résumé.
#     3. Ajouter un son de notification (print('\a')) quand le
#        nombre de ruptures > 0 au démarrage de l'application.
# ════════════════════════════════════════════════════════════════════