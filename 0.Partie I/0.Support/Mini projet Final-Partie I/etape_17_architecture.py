"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 17  ·  Architecture Modulaire      ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Organiser le projet en modules Python spécialisés.               ║
║    Chaque fichier a une responsabilité unique.                      ║
║    Comprendre import, from ... import, if __name__ == "__main__"    ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    modules · import · from ... import · __name__ · __all__         ║
║    sys.path · dossiers comme packages                               ║
╚══════════════════════════════════════════════════════════════════════╝

Ce fichier est un GUIDE D'ARCHITECTURE.
Il explique comment découper le projet en modules et montre
la structure finale du projet.

Dans un vrai projet, chaque section ci-dessous serait un fichier séparé.
"""

# ════════════════════════════════════════════════════════════════════
#  STRUCTURE DU PROJET FINAL
# ════════════════════════════════════════════════════════════════════

"""
stock_manager/
│
├── main.py                ← Point d'entrée unique
│
├── modules/
│   ├── __init__.py        ← Fait du dossier un "package" Python
│   ├── produits.py        ← Modèle de données + CRUD
│   ├── mouvements.py      ← Entrées, sorties, historique
│   ├── persistance.py     ← JSON, CSV, backup
│   ├── rapports.py        ← Valorisation, marges, expirations
│   ├── alertes.py         ← Analyse + bulletin d'alertes
│   ├── statistiques.py    ← Graphes ASCII
│   ├── interface.py       ← Menus, navigation, formulaires
│   ├── parametres.py      ← Config chargement/sauvegarde
│   ├── erreurs.py         ← Logs, try/except, sécurisation
│   └── validation.py      ← Fonctions valider_*()
│
├── data/
│   ├── stock.json         ← Catalogue persisté
│   ├── stock_backup.json  ← Backup automatique
│   └── config.json        ← Configuration persistée
│
├── exports/
│   └── *.csv, *.txt       ← Fichiers exportés
│
└── logs/
    └── stock_manager.log  ← Journal d'activité
"""

# ════════════════════════════════════════════════════════════════════
#  RÈGLES D'ARCHITECTURE
# ════════════════════════════════════════════════════════════════════

"""
RÈGLE 1 — Responsabilité unique
    Chaque module fait UNE seule chose.
    produits.py ne fait PAS d'affichage Rich.
    interface.py ne fait PAS de calculs métier.

RÈGLE 2 — Sens des imports
    Autorisés (bas vers haut) :
        interface.py  → produits.py, mouvements.py, rapports.py
        rapports.py   → produits.py
        persistance.py → produits.py
    
    Interdits (circulaires) :
        produits.py   → interface.py   ← INTERDIT
        persistance.py → rapports.py   ← INTERDIT

RÈGLE 3 — if __name__ == "__main__"
    Chaque module peut être exécuté seul pour ses propres tests.
    Sans cette garde, l'exécution de main.py déclencherait aussi
    le code de test de chaque module importé.

RÈGLE 4 — __all__ (optionnel mais recommandé)
    Déclare l'API publique d'un module.
    from produits import * n'importera que ce qui est dans __all__.
"""

from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.columns import Columns

console = Console()


# ════════════════════════════════════════════════════════════════════
#  CONTENU DE __init__.py  (dossier modules/)
# ════════════════════════════════════════════════════════════════════

INIT_PY = '''
"""
Package stock_manager.modules
Centralise tous les imports pour que main.py reste minimal.
"""

from .produits     import (creer_produit, ajouter_produit, trouver_par_ref,
                            rechercher, trier, modifier_produit, supprimer_produit,
                            valeur_stock, marge_pct, etat_stock)

from .mouvements   import (enregistrer_mouvement, afficher_historique,
                            formulaire_entree, formulaire_sortie)

from .persistance  import (initialiser, charger_catalogue, sauvegarder_catalogue,
                            charger_config, sauvegarder_config,
                            exporter_catalogue_csv, exporter_rapport_txt)

from .rapports     import (rapport_dashboard, rapport_valorisation,
                            rapport_marges, rapport_expirations)

from .alertes      import (analyser_alertes, badge_alertes,
                            afficher_bulletin_alertes)

from .statistiques import (graphe_etat_global, graphe_stocks_categorie,
                            graphe_marges, graphe_top_valeur)

from .interface    import (splash_screen, lancer_application,
                            afficher_catalogue, afficher_fiche_complete)

from .parametres   import (charger_config, sauvegarder_config,
                            menu_parametres, CONFIG_DEFAUT)

from .erreurs      import (configurer_logs, log_info, log_erreur,
                            operation_securisee, afficher_derniers_logs)
'''


# ════════════════════════════════════════════════════════════════════
#  CONTENU DE main.py
# ════════════════════════════════════════════════════════════════════

MAIN_PY = '''
"""
Stock Manager — Point d\'entrée principal
Lancer : python main.py
"""

import sys
from pathlib import Path

# Ajouter le dossier racine au chemin Python
# Nécessaire si lancé depuis un autre dossier
sys.path.insert(0, str(Path(__file__).parent))

from modules import (
    # Initialisation
    configurer_logs, initialiser,
    charger_catalogue, sauvegarder_catalogue,
    charger_config,
    # Interface
    splash_screen, lancer_application,
    # Alertes
    analyser_alertes, compter_alertes, afficher_bulletin_alertes,
)
from rich.console import Console
from rich.prompt  import Confirm

console = Console()


def main():
    """Séquence de démarrage complète."""

    # 1. Configurer les logs (en premier)
    configurer_logs()

    # 2. Initialiser l\'environnement (crée data/ si absent)
    initialiser()

    # 3. Charger les données
    config    = charger_config()
    catalogue = charger_catalogue()
    historique = charger_historique()

    # 4. Splash screen animé
    splash_screen(config)

    # 5. Vérification des alertes au démarrage
    alertes     = analyser_alertes(catalogue, config)
    nb_alertes  = compter_alertes(alertes)

    if nb_alertes > 0:
        console.print(
            f"  [bold yellow]⚠  {nb_alertes} alerte(s) détectée(s).[/bold yellow]"
        )
        if Confirm.ask("  Afficher le bulletin d\'alertes ?",
                       default=True, console=console):
            afficher_bulletin_alertes(catalogue, config)
            input("  Entrée pour continuer…")

    # 6. Boucle principale
    lancer_application(catalogue, historique, config)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\\n[yellow]Interruption — fermeture propre.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Erreur critique : {e}[/bold red]")
        import traceback
        traceback.print_exc()
    finally:
        import logging
        logging.info("Application fermée")
        console.print("[dim]Au revoir ![/dim]")
'''


# ════════════════════════════════════════════════════════════════════
#  AFFICHAGE DE L'ARCHITECTURE
# ════════════════════════════════════════════════════════════════════

def afficher_architecture():
    """Affiche la structure du projet de façon visuelle."""

    MODULES = [
        ("main.py",          "Point d'entrée unique",     "blue",    ["modules.*"]),
        ("modules/produits.py",    "CRUD + calculs métier",    "green",   []),
        ("modules/mouvements.py",  "Entrées/sorties/historique","green",  ["produits"]),
        ("modules/persistance.py", "JSON + CSV + backup",      "green",   ["produits"]),
        ("modules/rapports.py",    "Valorisation + analyses",  "cyan",    ["produits"]),
        ("modules/alertes.py",     "Détection + bulletin",     "red",     ["produits"]),
        ("modules/statistiques.py","Graphes ASCII",            "magenta", ["produits"]),
        ("modules/interface.py",   "Menus + navigation",       "yellow",  ["produits","mouvements","rapports","alertes","statistiques","persistance"]),
        ("modules/parametres.py",  "Configuration",            "dim cyan",["persistance"]),
        ("modules/erreurs.py",     "Logs + sécurisation",      "dim red", []),
        ("modules/validation.py",  "Fonctions valider_*()",    "dim white",[]),
    ]

    t = Table(
        title="[bold white]ARCHITECTURE DU PROJET — STOCK MANAGER[/bold white]",
        border_style="blue",
        header_style="bold blue",
        show_lines=True,
    )
    t.add_column("Fichier",        style="bold white",  width=28)
    t.add_column("Responsabilité", style="white",       width=28)
    t.add_column("Importe",        style="dim cyan",    width=36)

    for fichier, responsabilite, couleur, imports in MODULES:
        imports_str = ", ".join(imports) if imports else "[dim]—[/dim]"
        t.add_row(
            f"[{couleur}]{fichier}[/{couleur}]",
            responsabilite,
            imports_str,
        )

    console.print(Panel(t, border_style="blue"))

    console.print()
    console.print(Panel(
        "[bold white]Commande de lancement :[/bold white]\n"
        "[bold green]  python main.py[/bold green]\n\n"
        "[bold white]Tester un module seul :[/bold white]\n"
        "[bold cyan]  python modules/produits.py[/bold cyan]\n"
        "[bold cyan]  python modules/rapports.py[/bold cyan]\n\n"
        "[bold white]Consulter les logs :[/bold white]\n"
        "[bold dim]  cat logs/stock_manager.log[/bold dim]",
        title="[bold white]🚀  COMMANDES UTILES[/bold white]",
        border_style="green",
        padding=(0, 2),
    ))


def afficher_regles():
    """Affiche les règles d'architecture."""

    regles = [
        ("Responsabilité unique",
         "Chaque module fait une seule chose. produits.py ne fait jamais d'affichage Rich."),
        ("Imports directionnels",
         "interface.py peut importer produits.py, mais JAMAIS l'inverse."),
        ("if __name__ == '__main__'",
         "Chaque module contient ses propres tests exécutables indépendamment."),
        ("Aucune variable globale partagée",
         "Le catalogue et l'historique sont passés en paramètre, jamais en global."),
        ("Séparation calcul / affichage",
         "Les fonctions de calcul retournent des valeurs. L'affichage est dans interface.py."),
    ]

    t = Table(show_header=False, box=None, padding=(0, 2))
    t.add_column(style="bold cyan",  width=28)
    t.add_column(style="white",      width=50)

    for regle, explication in regles:
        t.add_row(f"✓  {regle}", explication)

    console.print(Panel(
        t,
        title="[bold white]📐  RÈGLES D'ARCHITECTURE[/bold white]",
        border_style="cyan",
        padding=(1, 2),
    ))


# ════════════════════════════════════════════════════════════════════
#  TEST AUTONOME
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    console.rule("[bold cyan]ARCHITECTURE — STOCK MANAGER[/bold cyan]")
    console.print()

    afficher_architecture()

    console.print()
    afficher_regles()

    console.print()
    console.print(Panel(
        "[bold white]Contenu de main.py :[/bold white]\n\n"
        + MAIN_PY[:400] + "\n  [dim]…[/dim]",
        border_style="dim blue",
        padding=(0, 2),
    ))


# ════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — sys.path.insert(0, ...)
#     Ajouter le dossier du projet en tête du chemin de recherche
#     garantit que Python trouve les modules locaux même si
#     l'application est lancée depuis un autre répertoire.
#
#  💡 ASTUCE — from .produits import ...
#     Le point devant "produits" signifie "import relatif dans
#     le même package". Utilisé dans __init__.py d'un dossier/package.
#     from produits import ... (sans point) = import absolu.
#
#  💡 ASTUCE — __all__ dans un module
#     __all__ = ["creer_produit", "ajouter_produit"]
#     Contrôle ce que from module import * expose.
#     Bonne pratique : toujours définir __all__ dans les modules
#     qui seront utilisés par d'autres.
#
#  🏋️  EXERCICE
#     1. Créer le dossier modules/ avec __init__.py vide, puis
#        déplacer une fonction dans modules/produits.py et
#        l'importer depuis main.py.
#     2. Vérifier que python modules/produits.py fonctionne
#        seul grâce à if __name__ == "__main__".
#     3. Créer modules/utils.py avec effacer(), pause(), ok(),
#        err(), info() et l'importer depuis interface.py.
# ════════════════════════════════════════════════════════════════════