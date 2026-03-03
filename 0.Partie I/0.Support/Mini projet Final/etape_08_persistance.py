"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 08  ·  Persistance JSON            ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Sauvegarder et recharger les données entre deux sessions         ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    json · pathlib · try/except · shutil · open() · with             ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Affichage infos fichiers · messages de statut colorés            ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json
import shutil
import datetime
from pathlib import Path
from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table

console = Console()

# ─── Chemins des fichiers ─────────────────────────────────────────────
DATA_DIR     = Path("data")
STOCK_FILE   = DATA_DIR / "stock.json"
BACKUP_FILE  = DATA_DIR / "stock_backup.json"
CONFIG_FILE  = DATA_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "historique.json"

CONFIG_DEFAUT = {
    "entreprise" : "Mon Drug Store",
    "devise"     : "DT",
    "tva_pct"    : 19.0,
    "version"    : "1.0",
    "cree_le"    : datetime.date.today().strftime("%d/%m/%Y"),
}


# ════════════════════════════════════════════════════════════════════
#  INITIALISATION
# ════════════════════════════════════════════════════════════════════

def initialiser():
    """Crée le dossier data/ et les fichiers manquants."""
    DATA_DIR.mkdir(exist_ok=True)
    if not STOCK_FILE.exists():
        _ecrire_json(STOCK_FILE, {"meta": {}, "catalogue": []})
        console.print("[dim]  stock.json créé.[/dim]")
    if not CONFIG_FILE.exists():
        _ecrire_json(CONFIG_FILE, CONFIG_DEFAUT)
        console.print("[dim]  config.json créé.[/dim]")
    if not HISTORY_FILE.exists():
        _ecrire_json(HISTORY_FILE, [])
        console.print("[dim]  historique.json créé.[/dim]")


# ════════════════════════════════════════════════════════════════════
#  OUTILS BAS NIVEAU
# ════════════════════════════════════════════════════════════════════

def _ecrire_json(chemin, donnees):
    """Écrit des données Python dans un fichier JSON."""
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)

def _lire_json(chemin):
    """Lit et retourne le contenu d'un fichier JSON."""
    with open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)


# ════════════════════════════════════════════════════════════════════
#  CATALOGUE
# ════════════════════════════════════════════════════════════════════

def sauvegarder(catalogue):
    """
    Sauvegarde le catalogue.
    Crée un backup de l'ancienne version avant d'écraser.
    Retourne True si succès, False si erreur.
    """
    try:
        DATA_DIR.mkdir(exist_ok=True)

        # Rotation backup : stock.json → stock_backup.json
        if STOCK_FILE.exists():
            shutil.copy2(STOCK_FILE, BACKUP_FILE)

        payload = {
            "meta": {
                "sauvegarde_le"  : datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "nb_produits"    : len(catalogue),
                "version_schema" : "1.0",
            },
            "catalogue": catalogue,
        }
        _ecrire_json(STOCK_FILE, payload)
        return True

    except (OSError, IOError) as e:
        console.print(f"[bold red]✗  Erreur de sauvegarde : {e}[/bold red]")
        return False


def charger():
    """
    Charge le catalogue depuis stock.json.
    En cas de corruption, tente de restaurer le backup.
    Retourne toujours une liste (éventuellement vide).
    """
    if not STOCK_FILE.exists():
        return []

    try:
        donnees = _lire_json(STOCK_FILE)

        # Accepter les deux formats : liste brute ou dict avec "catalogue"
        if isinstance(donnees, list):
            catalogue = donnees
        else:
            catalogue = donnees.get("catalogue", [])
            meta      = donnees.get("meta", {})
            if meta:
                console.print(
                    f"  [dim]Chargé : [white]{meta.get('nb_produits','?')}[/white] produits  "
                    f"— dernier save : {meta.get('sauvegarde_le','?')}[/dim]"
                )
        return catalogue

    except json.JSONDecodeError as e:
        console.print(f"[bold red]✗  stock.json corrompu ({e}) — restauration backup…[/bold red]")
        return _restaurer_backup()

    except (OSError, IOError) as e:
        console.print(f"[bold red]✗  Lecture impossible : {e}[/bold red]")
        return []


def _restaurer_backup():
    """Restaure stock.json depuis stock_backup.json."""
    if not BACKUP_FILE.exists():
        console.print("[red]Aucun backup disponible.[/red]")
        return []
    try:
        shutil.copy2(BACKUP_FILE, STOCK_FILE)
        console.print("[green]Backup restauré.[/green]")
        return charger()
    except Exception:
        return []


# ════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ════════════════════════════════════════════════════════════════════

def charger_config():
    """Retourne la config (fusionnée avec les valeurs par défaut)."""
    if not CONFIG_FILE.exists():
        return CONFIG_DEFAUT.copy()
    try:
        cfg = _lire_json(CONFIG_FILE)
        # {**defaut, **lu} : les clés lues écrasent les défauts
        return {**CONFIG_DEFAUT, **cfg}
    except Exception:
        return CONFIG_DEFAUT.copy()


def sauvegarder_config(config):
    """Sauvegarde la configuration."""
    DATA_DIR.mkdir(exist_ok=True)
    try:
        _ecrire_json(CONFIG_FILE, config)
        return True
    except Exception as e:
        console.print(f"[red]✗  Erreur config : {e}[/red]")
        return False


# ════════════════════════════════════════════════════════════════════
#  HISTORIQUE DES MOUVEMENTS
# ════════════════════════════════════════════════════════════════════

def ajouter_historique(type_mvt, reference, nom, quantite,
                       motif="", utilisateur="Administrateur"):
    """
    Enregistre un mouvement dans l'historique JSON.
    type_mvt : "entree" | "sortie" | "ajustement"
    """
    historique = charger_historique()
    entree = {
        "date"        : datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "type"        : type_mvt,
        "reference"   : reference,
        "nom"         : nom,
        "quantite"    : quantite,
        "motif"       : motif,
        "utilisateur" : utilisateur,
    }
    historique.append(entree)
    # Garder les 500 derniers mouvements max
    if len(historique) > 500:
        historique = historique[-500:]
    try:
        _ecrire_json(HISTORY_FILE, historique)
    except Exception:
        pass   # historique non critique — ne pas bloquer l'appli


def charger_historique():
    """Retourne la liste des mouvements enregistrés."""
    if not HISTORY_FILE.exists():
        return []
    try:
        return _lire_json(HISTORY_FILE)
    except Exception:
        return []


# ════════════════════════════════════════════════════════════════════
#  INFORMATIONS SUR LES FICHIERS (affichage)
# ════════════════════════════════════════════════════════════════════

def afficher_infos_fichiers():
    """Tableau récapitulatif de l'état des fichiers de données."""
    t = Table(show_header=True, header_style="bold cyan", box=None,
              padding=(0, 3))
    t.add_column("Fichier",       style="white",      width=22)
    t.add_column("Taille",        justify="right",    width=12)
    t.add_column("Modifié le",    style="dim white",  width=20)
    t.add_column("État",          justify="center",   width=12)

    for f in [STOCK_FILE, BACKUP_FILE, CONFIG_FILE, HISTORY_FILE]:
        if f.exists():
            st     = f.stat()
            taille = f"{st.st_size:,} o"
            modif  = datetime.datetime.fromtimestamp(
                         st.st_mtime).strftime("%d/%m/%Y %H:%M")
            etat   = "[bold green]✓ OK[/bold green]"
        else:
            taille = "—"
            modif  = "—"
            etat   = "[dim]absent[/dim]"
        t.add_row(f.name, taille, modif, etat)

    console.print(Panel(t, title="[bold white]📁  FICHIERS DE DONNÉES[/bold white]",
                        border_style="dim blue"))


# ─── Test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    console.rule("[bold cyan]TEST — PERSISTANCE JSON[/bold cyan]")
    initialiser()

    catalogue_test = [
        {"reference":"MED-001","nom":"Paracétamol 500mg","categorie":"Analgésique",
         "unite":"boîte","prix_achat":3.5,"prix_vente":5.8,"quantite":250,
         "stock_min":50,"stock_max":500,"fournisseur":"SIPHAT",
         "date_expiration":"31/12/2025","date_creation":"01/01/2024",
         "date_modification":None},
    ]

    ok = sauvegarder(catalogue_test)
    console.print(f"Sauvegarde : [{'green]✓' if ok else 'red]✗'}[/]")

    cat = charger()
    console.print(f"Chargement : [green]{len(cat)}[/green] produit(s)")

    ajouter_historique("entree", "MED-001", "Paracétamol 500mg", 50, "Réception commande")
    console.print(f"Historique : [green]{len(charger_historique())}[/green] entrée(s)")

    console.print()
    afficher_infos_fichiers()


# ══════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — with open(...) as f
#     Le mot-clé with garantit la fermeture du fichier même si
#     une exception survient à l'intérieur du bloc. C'est la
#     façon correcte en Python (gestionnaire de contexte).
#
#  💡 ASTUCE — {**defaut, **config}
#     Fusion de deux dictionnaires. Les clés de config écrasent
#     celles de defaut. Disponible depuis Python 3.5+.
#     Utilité : si un futur champ est ajouté au schéma, les
#     anciens fichiers de config seront complétés automatiquement.
#
#  💡 ASTUCE — ensure_ascii=False dans json.dump()
#     Conserve les accents tels quels dans le fichier JSON.
#     Sans ça, "Médicament" serait écrit "M\u00e9dicament".
#
#  🏋️  EXERCICE
#     1. Écrire exporter_csv(catalogue, chemin) qui produit
#        un fichier CSV lisible par Excel (séparateur ;).
#     2. Modifier sauvegarder() pour conserver les 3 derniers
#        backups : backup_1.json, backup_2.json, backup_3.json
#        en rotation.
#     3. Ajouter une fonction statistiques_historique() qui
#        retourne : nb entrées, nb sorties, quantité totale
#        entrée/sortie sur les 30 derniers jours.
# ══════════════════════════════════════════════════════════════════════