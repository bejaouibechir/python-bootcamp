"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 02  ·  Splash screen & Logo        ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Créer un écran de démarrage professionnel avec animation         ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    import · time.sleep() · os · fonctions · f-strings · datetime    ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Panel · Text · Align · Progress (barre de chargement)            ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import time
import datetime
from rich.console  import Console
from rich.panel    import Panel
from rich.text     import Text
from rich.align    import Align
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

console = Console()


# ─── Constantes de l'application ──────────────────────────────────────
APP_NOM      = "STOCK MANAGER"
APP_SLOGAN   = "Gestion de stock professionnelle"
APP_VERSION  = "v 1.0"
APP_CIBLE    = "Drug Store · Industrie · Commerce"


# ─── 1. Logo ASCII art ────────────────────────────────────────────────

LOGO = r"""
  ██████╗████████╗ ██████╗  ██████╗██╗  ██╗
 ██╔════╝╚══██╔══╝██╔═══██╗██╔════╝██║ ██╔╝
 ╚█████╗    ██║   ██║   ██║██║     █████╔╝
  ╚═══██╗   ██║   ██║   ██║██║     ██╔═██╗
 ██████╔╝   ██║   ╚██████╔╝╚██████╗██║  ██╗
 ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝
  ███╗   ███╗ █████╗ ███╗  ██╗ █████╗  ██████╗ ███████╗██████╗
  ████╗ ████║██╔══██╗████╗ ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗
  ██╔████╔██║███████║██╔██╗██║███████║██║  ███╗█████╗  ██████╔╝
  ██║╚██╔╝██║██╔══██║██║╚████║██╔══██║██║   ██║██╔══╝  ██╔══██╗
  ██║ ╚═╝ ██║██║  ██║██║ ╚███║██║  ██║╚██████╔╝███████╗██║  ██║
  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
"""


def afficher_logo():
    """Construit et affiche le bloc logo dans un Panel centré."""

    # Text() permet d'assembler du texte avec des styles différents
    contenu = Text(justify="center")
    contenu.append(LOGO,                    style="bold cyan")
    contenu.append(f"\n  {APP_SLOGAN}\n",   style="italic yellow")
    contenu.append(f"  {APP_CIBLE}\n",      style="dim white")
    contenu.append(f"\n  {APP_VERSION}",    style="bold white")
    contenu.append("  ·  2024 – 2025\n",   style="dim white")

    console.print(Panel(
        Align.center(contenu),
        border_style="bold cyan",
        padding=(1, 6),
    ))


# ─── 2. Barre de chargement animée ────────────────────────────────────

def afficher_chargement():
    """Simule l'initialisation du système avec une barre de progression."""

    etapes = [
        ("Initialisation du système…",    30, 0.025),
        ("Chargement de la base…",         25, 0.020),
        ("Vérification des stocks…",       25, 0.020),
        ("Prêt !",                         20, 0.015),
    ]

    console.print()

    with Progress(
        SpinnerColumn(style="bold cyan"),
        TextColumn("[bold cyan]{task.description:<35}"),
        BarColumn(bar_width=38, style="dim cyan", complete_style="bold green"),
        TextColumn("[bold white]{task.percentage:>3.0f}%"),
        console=console,
        transient=True,          # disparaît proprement à la fin
    ) as progress:

        tache = progress.add_task("Démarrage…", total=100)

        for description, pourcentage, delai in etapes:
            for _ in range(pourcentage):
                progress.update(tache, advance=1, description=description)
                time.sleep(delai)

    console.print(Align.center(
        "[bold green]✓  Système prêt ![/bold green]"
    ))
    console.print()


# ─── 3. Bandeau de session ─────────────────────────────────────────────

def afficher_bandeau_session(utilisateur="Administrateur"):
    """Affiche les informations de la session ouverte."""

    now = datetime.datetime.now()
    texte = Text()
    texte.append("  Session : ", style="dim white")
    texte.append(now.strftime("%A %d %B %Y  %H:%M:%S"), style="bold white")
    texte.append("   |   Utilisateur : ",               style="dim white")
    texte.append(utilisateur,                            style="bold green")
    texte.append("   |   " + APP_NOM,                   style="dim cyan")

    console.print(Panel(texte, border_style="dim blue", padding=(0, 1)))
    console.print()


# ─── 4. Séquence complète ─────────────────────────────────────────────

def splash_screen(utilisateur="Administrateur"):
    """Lance la séquence complète de démarrage."""
    os.system("cls" if os.name == "nt" else "clear")
    afficher_logo()
    afficher_chargement()
    afficher_bandeau_session(utilisateur)


# ─── Point d'entrée ────────────────────────────────────────────────────
if __name__ == "__main__":
    splash_screen()
    console.print("[dim]Appuyez sur Entrée pour continuer…[/dim]", end="")
    input()


# ══════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — transient=True dans Progress
#     La barre de progression s'efface après completion pour ne
#     pas encombrer l'écran. Sans transient, elle reste affichée.
#
#  💡 ASTUCE — os.system("cls" if os.name == "nt" else "clear")
#     os.name vaut "nt" sur Windows et "posix" sur Linux/Mac.
#     Ce one-liner cross-platform évite les imports conditionnels.
#
#  💡 ASTUCE — Panel + Align.center()
#     Panel encadre n'importe quel contenu Rich.
#     Align.center() centre horizontalement dans le terminal.
#     Combinés, ils donnent un aspect "carte" très professionnel.
#
#  🏋️  EXERCICE
#     1. Modifier les constantes APP_NOM / APP_SLOGAN / APP_CIBLE
#        pour personnaliser l'application au nom de votre entreprise.
#     2. Ajouter une ligne "Connexion à la base : OK" dans
#        afficher_chargement() avec un délai plus court.
#     3. Modifier afficher_bandeau_session() pour accepter aussi
#        un paramètre role ("Admin", "Vendeur", "Lecture seule")
#        et l'afficher avec une couleur différente selon le rôle.
# ══════════════════════════════════════════════════════════════════════