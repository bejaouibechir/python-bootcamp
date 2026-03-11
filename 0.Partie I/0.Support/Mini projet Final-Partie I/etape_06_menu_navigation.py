"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 06  ·  Menu & Navigation           ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Construire la boucle principale et le système de menus           ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    while True · if/elif · fonctions · import · os · datetime        ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Prompt.ask(choices=) · Panel · Table layout · Align              ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import datetime
from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.align   import Align
from rich.prompt  import Prompt

console = Console()

# ─── Constante globale ───────────────────────────────────────────────
APP_NOM = "STOCK MANAGER"


# ════════════════════════════════════════════════════════════════════════
#  UTILITAIRES D'INTERFACE
# ════════════════════════════════════════════════════════════════════════

def effacer():
    """Vide le terminal (cross-platform)."""
    os.system("cls" if os.name == "nt" else "clear")


def entete(titre_page="", fil_ariane=""):
    """
    Affiche la barre de navigation persistante en haut de chaque écran.
    fil_ariane : ex "Menu principal > Produits"
    """
    now = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M")

    t = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    t.add_column(ratio=1)
    t.add_column(ratio=2, justify="center")
    t.add_column(ratio=1, justify="right")

    t.add_row(
        f"[bold cyan]{APP_NOM}[/bold cyan]",
        f"[bold white]{titre_page}[/bold white]",
        f"[dim white]{now}[/dim white]",
    )

    console.print(Panel(t, border_style="dim cyan", padding=(0, 0)))

    if fil_ariane:
        console.print(f"  [dim]📍  {fil_ariane}[/dim]")
    console.print()


def pause(msg="Appuyez sur Entrée pour continuer…"):
    """Attend une confirmation de l'utilisateur."""
    console.print(f"\n[dim]{msg}[/dim]", end="")
    input()


def ok(msg):    console.print(f"\n[bold green]✓  {msg}[/bold green]")
def err(msg):   console.print(f"\n[bold red]✗  {msg}[/bold red]")
def info(msg):  console.print(f"\n[bold yellow]ℹ  {msg}[/bold yellow]")


# ════════════════════════════════════════════════════════════════════════
#  MOTEUR DE MENU GÉNÉRIQUE
# ════════════════════════════════════════════════════════════════════════

def afficher_menu(items, titre="MENU"):
    """
    Affiche un menu et retourne l'action choisie.

    items : liste de tuples  (touche, icône + libellé, action_str)
    titre : titre du Panel
    """
    t = Table(show_header=False, box=None, padding=(0, 3), min_width=48)
    t.add_column(style="bold yellow",  width=5)
    t.add_column(style="white")

    for touche, libelle, _ in items:
        if touche == "0":
            t.add_row("", "")
        t.add_row(f"[{touche}]", libelle)

    console.print(Panel(t, title=f"[bold white]{titre}[/bold white]",
                        border_style="cyan", padding=(1, 4)))

    touches = [item[0] for item in items]
    actions = {item[0]: item[2] for item in items}

    choix = Prompt.ask(
        "  [bold cyan]Votre choix[/bold cyan]",
        choices=touches, show_choices=False, console=console,
    )
    return actions[choix]


# ════════════════════════════════════════════════════════════════════════
#  DÉFINITION DES MENUS
# ════════════════════════════════════════════════════════════════════════

MENU_PRINCIPAL = [
    ("1", "📦  Gestion des produits",         "produits"),
    ("2", "🔄  Mouvements de stock",           "mouvements"),
    ("3", "📊  Rapports & statistiques",       "rapports"),
    ("4", "🔍  Recherche rapide",               "recherche"),
    ("5", "⚠️   Alertes & expirations",          "alertes"),
    ("6", "⚙️   Paramètres",                     "parametres"),
    ("0", "🚪  Quitter",                        "quitter"),
]

MENU_PRODUITS = [
    ("1", "➕  Ajouter un produit",            "ajouter"),
    ("2", "📋  Afficher le catalogue",          "catalogue"),
    ("3", "🔍  Fiche d'un produit",             "fiche"),
    ("4", "✏️   Modifier un produit",            "modifier"),
    ("5", "🗑️   Supprimer un produit",           "supprimer"),
    ("0", "↩️   Retour",                         "retour"),
]

MENU_MOUVEMENTS = [
    ("1", "📥  Entrée en stock (réception)",   "entree"),
    ("2", "📤  Sortie de stock (vente/casse)",  "sortie"),
    ("3", "🔃  Ajustement / Inventaire",        "ajustement"),
    ("4", "📋  Historique des mouvements",      "historique"),
    ("0", "↩️   Retour",                         "retour"),
]

MENU_RAPPORTS = [
    ("1", "📊  Tableau de bord",               "dashboard"),
    ("2", "💰  Valorisation du stock",          "valorisation"),
    ("3", "📈  Analyse des marges",             "marges"),
    ("4", "📅  Produits proches expiration",    "expirations"),
    ("5", "🏆  Top articles (rotation)",        "top_rotation"),
    ("0", "↩️   Retour",                         "retour"),
]

MENU_PARAMETRES = [
    ("1", "🏢  Nom de l'entreprise",            "nom_entreprise"),
    ("2", "💱  Devise",                          "devise"),
    ("3", "📄  Exporter catalogue CSV",          "export_csv"),
    ("0", "↩️   Retour",                         "retour"),
]


# ════════════════════════════════════════════════════════════════════════
#  STUB : action non encore implémentée
# ════════════════════════════════════════════════════════════════════════

def stub(nom):
    """Placeholder affiché pour les actions à implémenter plus tard."""
    info(f"Action [bold]'{nom}'[/bold] — sera implémentée prochainement.")
    pause()


# ════════════════════════════════════════════════════════════════════════
#  BOUCLES DE NAVIGATION
# ════════════════════════════════════════════════════════════════════════

def nav_produits(cat):
    while True:
        effacer(); entete("Gestion des produits", "Menu principal > Produits")
        a = afficher_menu(MENU_PRODUITS, "📦  PRODUITS")
        if   a == "retour":   break
        elif a == "ajouter":  stub("Ajouter")        # ← étape 07
        elif a == "catalogue":stub("Catalogue")       # ← étape 07
        elif a == "fiche":    stub("Fiche produit")   # ← étape 07
        elif a == "modifier": stub("Modifier")        # ← étape 07
        elif a == "supprimer":stub("Supprimer")       # ← étape 07


def nav_mouvements(cat):
    while True:
        effacer(); entete("Mouvements de stock", "Menu principal > Mouvements")
        a = afficher_menu(MENU_MOUVEMENTS, "🔄  MOUVEMENTS")
        if   a == "retour":     break
        elif a == "entree":     stub("Entrée stock")   # ← étape 09
        elif a == "sortie":     stub("Sortie stock")   # ← étape 09
        elif a == "ajustement": stub("Ajustement")     # ← étape 09
        elif a == "historique": stub("Historique")     # ← étape 10


def nav_rapports(cat):
    while True:
        effacer(); entete("Rapports & statistiques", "Menu principal > Rapports")
        a = afficher_menu(MENU_RAPPORTS, "📊  RAPPORTS")
        if   a == "retour":       break
        elif a == "dashboard":    stub("Dashboard")      # ← étape 11
        elif a == "valorisation": stub("Valorisation")   # ← étape 11
        elif a == "marges":       stub("Marges")         # ← étape 11
        elif a == "expirations":  stub("Expirations")    # ← étape 11
        elif a == "top_rotation": stub("Top rotation")   # ← étape 11


def nav_parametres(config):
    while True:
        effacer(); entete("Paramètres", "Menu principal > Paramètres")
        a = afficher_menu(MENU_PARAMETRES, "⚙️  PARAMÈTRES")
        if   a == "retour":         break
        elif a == "nom_entreprise": stub("Nom entreprise")
        elif a == "devise":         stub("Devise")
        elif a == "export_csv":     stub("Export CSV")    # ← étape 12


# ════════════════════════════════════════════════════════════════════════
#  BOUCLE PRINCIPALE
# ════════════════════════════════════════════════════════════════════════

def lancer_application():
    """Point d'entrée unique — boucle événementielle principale."""

    catalogue = []   # sera remplacé par le chargement JSON (étape 08)
    config    = {"entreprise": "Mon Drug Store", "devise": "DT"}

    while True:
        effacer()
        entete()

        # Résumé rapide des alertes dans le menu principal
        nb_alertes = sum(
            1 for p in catalogue
            if p.get("quantite", 0) <= p.get("stock_min", 0)
        )
        if nb_alertes:
            console.print(Align.center(
                f"[bold yellow]⚠   {nb_alertes} produit(s) en alerte de stock[/bold yellow]"
            ))
            console.print()

        action = afficher_menu(MENU_PRINCIPAL, f"🏥  {config['entreprise'].upper()}")

        if   action == "quitter":
            effacer()
            console.print(Align.center(Panel(
                "[bold cyan]Merci d'avoir utilisé Stock Manager.[/bold cyan]\n"
                "[dim]À bientôt ![/dim]",
                border_style="cyan", padding=(1, 8),
            )))
            break
        elif action == "produits":    nav_produits(catalogue)
        elif action == "mouvements":  nav_mouvements(catalogue)
        elif action == "rapports":    nav_rapports(catalogue)
        elif action == "recherche":   stub("Recherche")       # ← étape 07
        elif action == "alertes":     stub("Alertes")         # ← étape 11
        elif action == "parametres":  nav_parametres(config)


# ─── Point d'entrée ───────────────────────────────────────────────────
if __name__ == "__main__":
    lancer_application()


# ══════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — Pattern "skeleton first"
#     On construit d'abord toute la navigation avec des stubs,
#     puis on remplace chaque stub par du vrai code étape par étape.
#     Avantage : l'application est toujours exécutable et testable,
#     même avec des fonctionnalités incomplètes.
#
#  💡 ASTUCE — Prompt.ask(choices=[...], show_choices=False)
#     Rich valide automatiquement la saisie contre la liste choices.
#     show_choices=False évite d'afficher "(1/2/3/…)" à côté du prompt,
#     car le menu est déjà visible au-dessus.
#
#  💡 ASTUCE — Le fil d'Ariane dans entete()
#     "Menu principal > Produits > Ajouter" oriente l'utilisateur
#     sans interface graphique. Indispensable dans les TUI profondes.
#
#  🏋️  EXERCICE
#     1. Ajouter une option "7 — 📊  Mini-stats" dans le menu
#        principal qui affiche : nb produits, valeur totale, nb alertes
#        directement dans le menu (sans sous-menu).
#     2. Modifier entete() pour afficher en rouge le nombre
#        d'alertes si > 0, en vert sinon.
#     3. Ajouter un fil d'Ariane dynamique passé en paramètre
#        à chaque fonction de navigation.
# ══════════════════════════════════════════════════════════════════════