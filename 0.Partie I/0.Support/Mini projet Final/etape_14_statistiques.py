"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 14  ·  Statistiques Visuelles      ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Créer des graphiques ASCII dans le terminal : barres             ║
║    horizontales, histogrammes, sparklines de tendances              ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    math · max() · min() · round() · boucles · f-strings · dict      ║
║                                                                      ║
║  Aucune bibliothèque graphique — uniquement Rich + caractères Unicode║
╚══════════════════════════════════════════════════════════════════════╝
"""

import math
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich.columns import Columns

console = Console()

# ─── Helpers ─────────────────────────────────────────────────────────
def valeur_stock(p):  return p["prix_achat"] * p["quantite"]
def marge_pct(p):
    return ((p["prix_vente"] - p["prix_achat"]) / p["prix_achat"] * 100) \
           if p["prix_achat"] else 0
def etat_stock(p):
    q = p["quantite"]
    if q == 0:               return ("rupture", "⛔",  "bold red")
    if q <= p["stock_min"]:  return ("alerte",  "⚠",   "bold yellow")
    if q >  p["stock_max"]:  return ("surplus", "↑",   "bold magenta")
    return                          ("ok",      "✅",   "bold green")


# ════════════════════════════════════════════════════════════════════
#  1. BRIQUE DE BASE : BARRE HORIZONTALE
# ════════════════════════════════════════════════════════════════════

def barre(valeur, maximum, largeur=30, couleur="green"):
    """
    Génère une barre ASCII Rich proportionnelle à valeur/maximum.

    Caractères utilisés :
      █  (U+2588)  bloc plein
      ░  (U+2591)  bloc vide (fond)

    Returns : str Rich formaté  ex: '[green]████████░░░░░░[/green] 57.3%'
    """
    if maximum <= 0:
        return "[dim]—[/dim]"
    ratio     = min(1.0, valeur / maximum)       # entre 0 et 1
    nb_pleins = round(ratio * largeur)
    nb_vides  = largeur - nb_pleins
    barre_str = "█" * nb_pleins + "░" * nb_vides
    pct       = ratio * 100
    return f"[{couleur}]{barre_str}[/{couleur}] [dim]{pct:.1f}%[/dim]"


def barre_bicolore(valeur, seuil, maximum, largeur=30):
    """
    Barre avec couleur adaptative :
    vert si valeur >= seuil, jaune si valeur >= seuil/2, rouge sinon.
    Utile pour visualiser les niveaux de stock.
    """
    if maximum <= 0:
        return "[dim]—[/dim]"
    if valeur >= seuil:
        couleur = "green"
    elif valeur >= seuil // 2:
        couleur = "yellow"
    else:
        couleur = "red"
    return barre(valeur, maximum, largeur, couleur)


# ════════════════════════════════════════════════════════════════════
#  2. GRAPHE DES STOCKS PAR CATÉGORIE
# ════════════════════════════════════════════════════════════════════

def graphe_stocks_categorie(catalogue):
    """
    Barres horizontales du stock moyen par catégorie.
    Couleur verte si au-dessus de la moyenne globale, rouge sinon.
    """
    # Calculer le stock moyen par catégorie
    cats = {}
    for p in catalogue:
        c = p["categorie"]
        if c not in cats:
            cats[c] = {"total": 0, "nb": 0, "val": 0.0}
        cats[c]["total"] += p["quantite"]
        cats[c]["nb"]    += 1
        cats[c]["val"]   += valeur_stock(p)

    if not cats:
        console.print("[yellow]Catalogue vide.[/yellow]")
        return

    moyennes  = {c: d["total"] / d["nb"] for c, d in cats.items()}
    max_moy   = max(moyennes.values()) if moyennes else 1
    moy_glob  = sum(moyennes.values()) / len(moyennes)

    t = Table(
        title="[bold white]STOCK MOYEN PAR CATÉGORIE[/bold white]",
        border_style="blue",
        header_style="bold blue",
        show_lines=False,
    )
    t.add_column("Catégorie",   style="cyan",  width=18)
    t.add_column("Moy.",        justify="right", width=8)
    t.add_column("Articles",    justify="right", width=8)
    t.add_column("Visualisation", width=42)

    for cat, moy in sorted(moyennes.items(), key=lambda x: -x[1]):
        nb  = cats[cat]["nb"]
        coul = "green" if moy >= moy_glob else "yellow" if moy >= moy_glob * 0.5 else "red"
        t.add_row(
            cat[:16],
            f"{moy:.1f}",
            str(nb),
            barre(moy, max_moy, 36, coul),
        )

    console.print(Panel(t, border_style="blue"))


# ════════════════════════════════════════════════════════════════════
#  3. GRAPHE DES MARGES
# ════════════════════════════════════════════════════════════════════

def graphe_marges(catalogue):
    """
    Barres de marge par catégorie avec seuils de couleur.
    Vert ≥ 30 %, Jaune ≥ 15 %, Rouge < 15 %.
    """
    cats = {}
    for p in catalogue:
        c = p["categorie"]
        if c not in cats:
            cats[c] = []
        cats[c].append(marge_pct(p))

    if not cats:
        return

    moyennes = {c: sum(v) / len(v) for c, v in cats.items()}
    max_marge = max(moyennes.values()) if moyennes else 100

    t = Table(
        title="[bold white]MARGES MOYENNES PAR CATÉGORIE[/bold white]",
        border_style="magenta",
        header_style="bold magenta",
        show_lines=False,
    )
    t.add_column("Catégorie",   style="cyan",     width=18)
    t.add_column("Marge",       justify="right",  width=8)
    t.add_column("Min/Max",     justify="center", width=12)
    t.add_column("Visualisation", width=42)

    for cat, moy in sorted(moyennes.items(), key=lambda x: -x[1]):
        marges_cat = cats[cat]
        coul = "green" if moy >= 30 else "yellow" if moy >= 15 else "red"
        t.add_row(
            cat[:16],
            f"[{coul}]{moy:.1f}%[/{coul}]",
            f"[dim]{min(marges_cat):.0f}% – {max(marges_cat):.0f}%[/dim]",
            barre(moy, max(max_marge, 100), 36, coul),
        )

    console.print(Panel(t, border_style="magenta"))


# ════════════════════════════════════════════════════════════════════
#  4. TOP N ARTICLES PAR VALEUR DE STOCK
# ════════════════════════════════════════════════════════════════════

def graphe_top_valeur(catalogue, top=8, config=None):
    """
    Barres horizontales des N articles dont la valeur de stock
    est la plus élevée.
    """
    devise  = (config or {}).get("devise", "DT")
    tries   = sorted(catalogue, key=lambda p: -valeur_stock(p))[:top]

    if not tries:
        return

    max_val = valeur_stock(tries[0])

    t = Table(
        title=f"[bold white]TOP {top} ARTICLES PAR VALEUR DE STOCK[/bold white]",
        border_style="green",
        header_style="bold green",
        show_lines=False,
    )
    t.add_column("Réf.",     style="bold yellow", width=10)
    t.add_column("Nom",      style="white",       width=22)
    t.add_column("Valeur",   style="green",       width=14, justify="right")
    t.add_column("Part du stock", width=38)

    for p in tries:
        val = valeur_stock(p)
        t.add_row(
            p["reference"],
            p["nom"][:20],
            f"{val:.3f} {devise}",
            barre(val, max_val, 32, "green"),
        )

    console.print(Panel(t, border_style="green"))


# ════════════════════════════════════════════════════════════════════
#  5. GRAPHE D'ÉTAT DES STOCKS (camembert ASCII)
# ════════════════════════════════════════════════════════════════════

def graphe_etat_global(catalogue):
    """
    Représentation visuelle de la répartition des états de stock.
    Barres proportionnelles + compteurs.
    """
    if not catalogue:
        return

    total    = len(catalogue)
    compteurs = {"ok": 0, "alerte": 0, "rupture": 0, "surplus": 0}
    for p in catalogue:
        compteurs[etat_stock(p)[0]] += 1

    STYLES = {
        "ok"     : ("✅ Stock normal",  "green"),
        "alerte" : ("⚠  En alerte",    "yellow"),
        "rupture": ("⛔ En rupture",    "red"),
        "surplus": ("↑  En surplus",   "magenta"),
    }

    t = Table(
        title="[bold white]RÉPARTITION DES ÉTATS DE STOCK[/bold white]",
        border_style="cyan",
        header_style="bold cyan",
        show_lines=False,
    )
    t.add_column("État",   width=18)
    t.add_column("Nb",     justify="right", width=6)
    t.add_column("Visualisation", width=46)

    for code in ("ok", "alerte", "rupture", "surplus"):
        nb      = compteurs[code]
        label, coul = STYLES[code]
        t.add_row(
            f"[{coul}]{label}[/{coul}]",
            f"[{coul}]{nb}[/{coul}]",
            barre(nb, total, 40, coul),
        )

    console.print(Panel(t, border_style="cyan"))


# ════════════════════════════════════════════════════════════════════
#  6. SPARKLINE — TENDANCE D'UN INDICATEUR SUR N VALEURS
# ════════════════════════════════════════════════════════════════════

def sparkline(valeurs, largeur=20, couleur="cyan"):
    """
    Crée une mini-ligne de tendance avec des caractères de blocs.
    Utile pour afficher l'évolution d'un stock sur plusieurs jours.

    valeurs : liste de nombres  ex: [100, 90, 85, 80, 75, 80, 95]

    Caractères de hauteur (du plus bas au plus haut) :
    ▁ ▂ ▃ ▄ ▅ ▆ ▇ █
    """
    BLOCS = "▁▂▃▄▅▆▇█"

    if not valeurs or len(valeurs) < 2:
        return "[dim]—[/dim]"

    vmin = min(valeurs)
    vmax = max(valeurs)
    plage = vmax - vmin

    if plage == 0:
        return f"[{couleur}]" + BLOCS[3] * min(len(valeurs), largeur) + f"[/{couleur}]"

    chars = []
    for v in valeurs[-largeur:]:
        idx = round((v - vmin) / plage * (len(BLOCS) - 1))
        chars.append(BLOCS[idx])

    ligne = "".join(chars)

    # Ajouter flèche de tendance
    if valeurs[-1] > valeurs[0]:
        tendance = "[green] ↑[/green]"
    elif valeurs[-1] < valeurs[0]:
        tendance = "[red] ↓[/red]"
    else:
        tendance = "[dim] →[/dim]"

    return f"[{couleur}]{ligne}[/{couleur}]{tendance}"


def graphe_evolution_historique(historique, nb_jours=7):
    """
    Affiche l'évolution des entrées/sorties sur les derniers jours.
    """
    import datetime

    if not historique:
        console.print("[yellow]Aucun historique disponible.[/yellow]")
        return

    # Regrouper par jour
    jours = {}
    for m in historique:
        try:
            date_str = m["date"][:10]   # "JJ/MM/AAAA"
            if date_str not in jours:
                jours[date_str] = {"entrees": 0, "sorties": 0}
            if m["type"] == "entree":
                jours[date_str]["entrees"] += m["quantite"]
            elif m["type"] == "sortie":
                jours[date_str]["sorties"] += m["quantite"]
        except (KeyError, IndexError):
            pass

    if not jours:
        return

    jours_tries = sorted(jours.items())[-nb_jours:]

    t = Table(
        title=f"[bold white]ÉVOLUTION SUR {nb_jours} JOURS[/bold white]",
        border_style="cyan",
        header_style="bold cyan",
        show_lines=False,
    )
    t.add_column("Date",     style="dim white", width=12)
    t.add_column("Entrées",  justify="right",   width=8)
    t.add_column("Vis. entrées", width=22)
    t.add_column("Sorties",  justify="right",   width=8)
    t.add_column("Vis. sorties", width=22)

    max_qte = max(
        max((v["entrees"] for _, v in jours_tries), default=1),
        max((v["sorties"] for _, v in jours_tries), default=1),
        1,
    )

    for date_str, vals in jours_tries:
        t.add_row(
            date_str,
            f"[green]{vals['entrees']}[/green]",
            barre(vals["entrees"], max_qte, 18, "green"),
            f"[red]{vals['sorties']}[/red]",
            barre(vals["sorties"], max_qte, 18, "red"),
        )

    # Sparklines de synthèse
    serie_entrees = [v["entrees"] for _, v in jours_tries]
    serie_sorties = [v["sorties"] for _, v in jours_tries]
    t.add_section()
    t.add_row(
        "[dim]Tendance[/dim]",
        "", sparkline(serie_entrees, 18, "green"),
        "", sparkline(serie_sorties, 18, "red"),
    )

    console.print(Panel(t, border_style="cyan"))


# ════════════════════════════════════════════════════════════════════
#  TEST AUTONOME
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    catalogue_test = [
        {"reference":"MED-001","nom":"Paracétamol 500mg","categorie":"Analgésique",
         "prix_achat":3.5,"prix_vente":5.8,"quantite":250,"stock_min":50,"stock_max":500,
         "fournisseur":"SIPHAT","date_expiration":"31/12/2025",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MED-002","nom":"Ibuprofène 400mg","categorie":"Analgésique",
         "prix_achat":4.2,"prix_vente":7.2,"quantite":15,"stock_min":30,"stock_max":300,
         "fournisseur":"ADWYA","date_expiration":"30/09/2025",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MED-003","nom":"Amoxicilline 1g","categorie":"Antibiotique",
         "prix_achat":8.2,"prix_vente":12.5,"quantite":5,"stock_min":20,"stock_max":200,
         "fournisseur":"ADWYA","date_expiration":"30/06/2025",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MED-004","nom":"Oméprazole 20mg","categorie":"Gastro",
         "prix_achat":5.1,"prix_vente":8.9,"quantite":120,"stock_min":40,"stock_max":400,
         "fournisseur":"SIPHAT","date_expiration":"28/02/2026",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MED-005","nom":"Metformine 850mg","categorie":"Diabétologie",
         "prix_achat":3.8,"prix_vente":6.5,"quantite":0,"stock_min":30,"stock_max":200,
         "fournisseur":"PHARMAGHREB","date_expiration":"31/03/2026",
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"MAT-001","nom":"Seringues 5ml ×100","categorie":"Matériel",
         "prix_achat":12.0,"prix_vente":18.0,"quantite":45,"stock_min":10,"stock_max":100,
         "fournisseur":"MEDIS","date_expiration":None,
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"PAR-001","nom":"Vitamine C 1000mg","categorie":"Parapharmacie",
         "prix_achat":6.8,"prix_vente":11.5,"quantite":90,"stock_min":30,"stock_max":300,
         "fournisseur":"PHARMAGHREB","date_expiration":"30/11/2025",
         "date_creation":"01/01/2024","date_modification":None},
    ]

    historique_test = [
        {"date":"10/02/2025 10:00","reference":"MED-001","nom":"Paracétamol","type":"entree","quantite":100,"qte_avant":150,"qte_apres":250,"motif":""},
        {"date":"11/02/2025 11:00","reference":"MED-002","nom":"Ibuprofène","type":"sortie","quantite":5,"qte_avant":20,"qte_apres":15,"motif":""},
        {"date":"12/02/2025 09:00","reference":"MED-001","nom":"Paracétamol","type":"sortie","quantite":30,"qte_avant":250,"qte_apres":220,"motif":""},
        {"date":"13/02/2025 14:00","reference":"MAT-001","nom":"Seringues","type":"entree","quantite":20,"qte_avant":25,"qte_apres":45,"motif":""},
        {"date":"14/02/2025 10:00","reference":"MED-003","nom":"Amoxicilline","type":"sortie","quantite":2,"qte_avant":7,"qte_apres":5,"motif":""},
        {"date":"15/02/2025 16:00","reference":"PAR-001","nom":"Vitamine C","type":"entree","quantite":50,"qte_avant":40,"qte_apres":90,"motif":""},
        {"date":"16/02/2025 11:00","reference":"MED-001","nom":"Paracétamol","type":"sortie","quantite":10,"qte_avant":220,"qte_apres":210,"motif":""},
        {"date":"17/02/2025 09:00","reference":"MED-004","nom":"Oméprazole","type":"entree","quantite":60,"qte_avant":60,"qte_apres":120,"motif":""},
        {"date":"18/02/2025 10:00","reference":"MED-002","nom":"Ibuprofène","type":"entree","quantite":50,"qte_avant":15,"qte_apres":65,"motif":""},
    ]

    console.rule("[bold cyan]ÉTATS DE STOCK[/bold cyan]")
    graphe_etat_global(catalogue_test)

    console.print()
    console.rule("[bold cyan]STOCKS PAR CATÉGORIE[/bold cyan]")
    graphe_stocks_categorie(catalogue_test)

    console.print()
    console.rule("[bold cyan]MARGES PAR CATÉGORIE[/bold cyan]")
    graphe_marges(catalogue_test)

    console.print()
    console.rule("[bold cyan]TOP 5 VALEURS[/bold cyan]")
    graphe_top_valeur(catalogue_test, top=5)

    console.print()
    console.rule("[bold cyan]ÉVOLUTION HISTORIQUE[/bold cyan]")
    graphe_evolution_historique(historique_test)

    # Démonstration sparkline
    console.print()
    console.rule("[bold cyan]SPARKLINES[/bold cyan]")
    series = [
        ("Tendance haussière",  [20, 25, 30, 28, 35, 40, 45, 50]),
        ("Tendance baissière",  [80, 70, 65, 60, 50, 45, 40, 30]),
        ("Stable",              [50, 52, 48, 51, 49, 50, 51, 50]),
        ("Volatile",            [20, 80, 10, 90, 30, 70, 40, 60]),
    ]
    for nom, vals in series:
        console.print(f"  {nom:<25} {sparkline(vals, 12)}")


# ════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — Caractères Unicode de blocs
#     █ ▇ ▆ ▅ ▄ ▃ ▂ ▁ (U+2588 à U+2581) forment une échelle
#     de 8 niveaux de remplissage vertical.
#     ░ (U+2591) est le bloc de fond (vide) de la barre horizontale.
#     Ces caractères sont supportés par tous les terminaux modernes.
#
#  💡 ASTUCE — round(ratio * 7)  pour les sparklines
#     Convertir une valeur normalisée [0–1] en index [0–7]
#     pour sélectionner le bon caractère de bloc.
#     round() plutôt que int() évite le biais vers le bas.
#
#  💡 ASTUCE — min(1.0, valeur / maximum) dans barre()
#     Clamp la valeur entre 0 et 1, même si valeur > maximum.
#     Sans ce min(), une barre pourrait dépasser 100 % et
#     produire nb_pleins > largeur → IndexError.
#
#  🏋️  EXERCICE
#     1. Créer barre_double(valeur, min_val, max_val, largeur=30)
#        qui affiche en rouge la partie sous min_val,
#        en vert la partie au-dessus, et en jaune entre les deux.
#     2. Créer un graphe de comparaison mois en cours vs mois
#        précédent en utilisant deux barres côte à côte.
#     3. Ajouter un graphe de répartition des fournisseurs
#        (similaire à graphe_stocks_categorie mais par fournisseur).
# ════════════════════════════════════════════════════════════════════