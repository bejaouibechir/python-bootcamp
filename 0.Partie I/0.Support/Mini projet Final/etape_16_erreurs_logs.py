"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 15  ·  Paramètres Dynamiques       ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Permettre à l'utilisateur de configurer l'application en temps   ║
║    réel : nom, devise, TVA, seuils. Sauvegarder et recharger.       ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    dict · json · open() · with · fusion de dicts · input()          ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Prompt avec default= · Table de config · Panel dynamique         ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json
import datetime
from pathlib import Path
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich.prompt  import Prompt, Confirm, IntPrompt, FloatPrompt

console = Console()

# ════════════════════════════════════════════════════════════════════
#  CONFIGURATION PAR DÉFAUT
#  Toutes les clés avec leurs valeurs initiales.
#  Fusionnée avec la config chargée du fichier JSON.
# ════════════════════════════════════════════════════════════════════

CONFIG_DEFAUT = {
    # Identité
    "entreprise"        : "Mon Drug Store",
    "adresse"           : "",
    "telephone"         : "",
    # Finance
    "devise"            : "DT",
    "tva"               : 19.0,
    # Seuils d'alerte
    "seuil_exp_urgent"  : 30,    # jours avant expiration → alerte rouge
    "seuil_exp_proche"  : 90,    # jours avant expiration → alerte jaune
    # Interface
    "nb_resultats_page" : 15,    # articles par page dans les listes
    "nb_historique"     : 50,    # mouvements visibles dans l'historique
    # Métadonnées
    "version"           : "1.0",
    "date_creation"     : datetime.date.today().strftime("%d/%m/%Y"),
}

CONFIG_FILE = Path("data") / "config.json"


# ════════════════════════════════════════════════════════════════════
#  CHARGEMENT ET SAUVEGARDE
# ════════════════════════════════════════════════════════════════════

def charger_config():
    """
    Charge la configuration depuis data/config.json.
    Fusionne avec CONFIG_DEFAUT pour garantir toutes les clés.

    Le pattern {**defaut, **charge} :
      - prend CONFIG_DEFAUT comme base
      - écrase les clés présentes dans le fichier
      - garantit que les nouvelles clés (ajoutées au defaut) sont présentes
    """
    if not CONFIG_FILE.exists():
        return CONFIG_DEFAUT.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            chargee = json.load(f)
        return {**CONFIG_DEFAUT, **chargee}   # fusion
    except (json.JSONDecodeError, OSError):
        console.print("[yellow]Config illisible → valeurs par défaut.[/yellow]")
        return CONFIG_DEFAUT.copy()


def sauvegarder_config(config):
    """
    Sauvegarde la configuration dans data/config.json.
    Crée le dossier data/ si absent.
    """
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except OSError as e:
        console.print(f"[bold red]✗  Impossible de sauvegarder la config : {e}[/bold red]")
        return False


# ════════════════════════════════════════════════════════════════════
#  AFFICHAGE DE LA CONFIGURATION
# ════════════════════════════════════════════════════════════════════

def afficher_config(config):
    """
    Affiche toutes les options de configuration dans un tableau.
    Les clés techniques (version, date_creation) sont masquées.
    """
    LABELS = {
        "entreprise"        : ("🏢", "Nom de l'entreprise"),
        "adresse"           : ("📍", "Adresse"),
        "telephone"         : ("📞", "Téléphone"),
        "devise"            : ("💱", "Devise"),
        "tva"               : ("📊", "Taux TVA (%)"),
        "seuil_exp_urgent"  : ("🔴", "Alerte expiration urgente (jours)"),
        "seuil_exp_proche"  : ("🟡", "Alerte expiration proche (jours)"),
        "nb_resultats_page" : ("📄", "Résultats par page"),
        "nb_historique"     : ("🔄", "Mouvements dans l'historique"),
    }

    t = Table(show_header=False, box=None, padding=(0, 2), min_width=52)
    t.add_column(style="dim cyan",   width=4)
    t.add_column(style="dim white",  width=34)
    t.add_column(style="bold white")

    for cle, (icone, label) in LABELS.items():
        valeur = config.get(cle, "")
        if cle == "tva":
            valeur_str = f"{valeur} %"
        elif cle in ("seuil_exp_urgent", "seuil_exp_proche"):
            valeur_str = f"{valeur} jours"
        else:
            valeur_str = str(valeur) if valeur else "[dim]—[/dim]"
        t.add_row(icone, label, valeur_str)

    console.print(Panel(
        t,
        title="[bold white]⚙️  PARAMÈTRES ACTUELS[/bold white]",
        border_style="dim cyan",
        padding=(1, 2),
    ))


# ════════════════════════════════════════════════════════════════════
#  MENU DE CONFIGURATION INTERACTIF
# ════════════════════════════════════════════════════════════════════

def menu_parametres(config):
    """
    Sous-menu de configuration interactif.
    Modifie config EN PLACE (dict mutable).
    Sauvegarde automatiquement à la sortie.

    Returns : config (modifiée ou inchangée)
    """
    import os

    SECTIONS = [
        ("1", "🏢  Identité de l'entreprise"),
        ("2", "💱  Devise et fiscalité"),
        ("3", "⚠️   Seuils d'alerte"),
        ("4", "📄  Affichage"),
        ("0", "↩️   Retour (sauvegarde automatique)"),
    ]

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        afficher_config(config)
        console.print()

        # Menu des sections
        from rich.table import Table as T
        t = T(show_header=False, box=None, padding=(0, 3), min_width=44)
        t.add_column(style="bold yellow", width=5)
        t.add_column(style="white")
        for touche, libelle in SECTIONS:
            if touche == "0":
                t.add_row("", "")
            t.add_row(f"[{touche}]", libelle)
        console.print(Panel(t, title="[bold white]SECTIONS[/bold white]",
                            border_style="cyan", padding=(1, 4)))

        choix = Prompt.ask(
            "  [bold cyan]Section[/bold cyan]",
            choices=["0", "1", "2", "3", "4"],
            show_choices=False,
            console=console,
        )

        if choix == "0":
            break

        elif choix == "1":
            _section_identite(config)

        elif choix == "2":
            _section_finance(config)

        elif choix == "3":
            _section_seuils(config)

        elif choix == "4":
            _section_affichage(config)

    # Sauvegarde automatique à la sortie
    if sauvegarder_config(config):
        console.print("  [bold green]✓  Paramètres sauvegardés.[/bold green]")
    return config


def _section_identite(config):
    """Saisie des informations d'identité de l'entreprise."""
    console.print(Panel(
        "[bold white]Identité de l'entreprise[/bold white]\n"
        "[dim]Entrée = conserver la valeur actuelle[/dim]",
        border_style="cyan",
    ))
    config["entreprise"] = Prompt.ask(
        "  [cyan]Nom de l'entreprise[/cyan]",
        default=config["entreprise"],
        console=console,
    ).strip()

    config["adresse"] = Prompt.ask(
        "  [cyan]Adresse[/cyan]",
        default=config.get("adresse", ""),
        console=console,
    ).strip()

    config["telephone"] = Prompt.ask(
        "  [cyan]Téléphone[/cyan]",
        default=config.get("telephone", ""),
        console=console,
    ).strip()

    console.print("  [green]✓  Identité mise à jour.[/green]")


def _section_finance(config):
    """Saisie des paramètres financiers."""
    console.print(Panel(
        "[bold white]Devise et fiscalité[/bold white]",
        border_style="cyan",
    ))

    devises_courantes = ["DT", "EUR", "USD", "MAD", "Autre"]
    console.print("  Devises courantes : "
                  + "  ".join(f"[yellow]({i})[/yellow] {d}"
                              for i, d in enumerate(devises_courantes, 1)))
    choix_dev = Prompt.ask(
        "  [cyan]Numéro ou saisie libre[/cyan]",
        default="1", console=console,
    ).strip()

    if choix_dev.isdigit() and 1 <= int(choix_dev) <= len(devises_courantes) - 1:
        config["devise"] = devises_courantes[int(choix_dev) - 1]
    elif choix_dev.isdigit() and int(choix_dev) == len(devises_courantes):
        config["devise"] = Prompt.ask(
            "  [cyan]Devise personnalisée[/cyan]", console=console
        ).strip()
    elif not choix_dev.isdigit():
        config["devise"] = choix_dev.upper()

    try:
        config["tva"] = FloatPrompt.ask(
            f"  [cyan]Taux TVA (%)[/cyan]",
            default=config["tva"],
            console=console,
        )
    except Exception:
        pass

    console.print(f"  [green]✓  Devise : [white]{config['devise']}[/white]  "
                  f"TVA : [white]{config['tva']} %[/white][/green]")


def _section_seuils(config):
    """Saisie des seuils d'alerte."""
    console.print(Panel(
        "[bold white]Seuils d'alerte[/bold white]\n"
        "[dim]Définissent quand un produit passe en alerte[/dim]",
        border_style="yellow",
    ))

    config["seuil_exp_urgent"] = IntPrompt.ask(
        f"  [cyan]🔴  Expiration urgente (jours)[/cyan]",
        default=config["seuil_exp_urgent"],
        console=console,
    )
    config["seuil_exp_proche"] = IntPrompt.ask(
        f"  [cyan]🟡  Expiration proche (jours)[/cyan]",
        default=config["seuil_exp_proche"],
        console=console,
    )

    if config["seuil_exp_urgent"] >= config["seuil_exp_proche"]:
        console.print(
            "  [yellow]⚠  Le seuil urgent devrait être < seuil proche.[/yellow]"
        )

    console.print(
        f"  [green]✓  Urgent : [white]{config['seuil_exp_urgent']} j[/white]  "
        f"Proche : [white]{config['seuil_exp_proche']} j[/white][/green]"
    )


def _section_affichage(config):
    """Saisie des préférences d'affichage."""
    console.print(Panel(
        "[bold white]Préférences d'affichage[/bold white]",
        border_style="cyan",
    ))

    config["nb_resultats_page"] = IntPrompt.ask(
        "  [cyan]Résultats par page (5–50)[/cyan]",
        default=config["nb_resultats_page"],
        console=console,
    )
    config["nb_resultats_page"] = max(5, min(50, config["nb_resultats_page"]))

    config["nb_historique"] = IntPrompt.ask(
        "  [cyan]Mouvements visibles dans l'historique[/cyan]",
        default=config["nb_historique"],
        console=console,
    )
    config["nb_historique"] = max(10, min(500, config["nb_historique"]))

    console.print("  [green]✓  Affichage mis à jour.[/green]")


# ════════════════════════════════════════════════════════════════════
#  TEST AUTONOME
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    console.rule("[bold cyan]TEST — PARAMÈTRES[/bold cyan]")
    console.print()

    # Charger (ou créer) la configuration
    config = charger_config()

    # Afficher la configuration actuelle
    afficher_config(config)

    # Modifier quelques valeurs directement (sans menu interactif pour le test)
    config["entreprise"] = "Pharmacie Al Amal"
    config["devise"]     = "DT"
    config["tva"]        = 19.0

    # Sauvegarder
    ok = sauvegarder_config(config)
    console.print(f"\nSauvegarde : [{'green]✓ OK' if ok else 'red]✗ Échec'}[/]")

    # Recharger pour vérifier
    config2 = charger_config()
    console.print(
        f"Rechargé   : [green]{config2['entreprise']}[/green]  "
        f"[cyan]{config2['devise']}[/cyan]  "
        f"TVA : [white]{config2['tva']} %[/white]"
    )

    # Test fusion — clé manquante dans le fichier
    config3 = {**CONFIG_DEFAUT, "entreprise": "Test SAS"}
    console.print(
        f"\nFusion     : entreprise=[green]{config3['entreprise']}[/green]  "
        f"tva=[white]{config3['tva']}[/white]  "
        f"(défaut préservé)"
    )


# ════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — {**defaut, **charge}
#     Fusionne deux dicts. Les clés de 'charge' écrasent 'defaut'.
#     Les clés présentes dans 'defaut' mais absentes de 'charge'
#     sont conservées → garantit que toutes les clés existent.
#     C'est la pattern la plus propre pour gérer les configurations.
#
#  💡 ASTUCE — modifier config EN PLACE
#     config["cle"] = valeur modifie le dict original car les
#     dicts Python sont passés par référence. Pas besoin de
#     return config si la fonction ne recrée pas de nouveau dict.
#
#  💡 ASTUCE — Prompt.ask(default=valeur_actuelle)
#     Pré-remplit le champ avec la valeur courante. L'utilisateur
#     appuie sur Entrée pour conserver, ou tape pour modifier.
#     C'est l'UX standard des formulaires de modification.
#
#  🏋️  EXERCICE
#     1. Ajouter une option "Réinitialiser aux valeurs par défaut"
#        avec confirmation Confirm.ask().
#     2. Ajouter un export de la config en fichier texte lisible.
#     3. Ajouter un champ "logo_ascii" (multi-lignes) qui permet
#        de personnaliser le logo du splash screen.
# ════════════════════════════════════════════════════════════════════