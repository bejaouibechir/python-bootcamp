"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 18  ·  VERSION FINALE              ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Assembler toutes les étapes en une application cohérente         ║
║    prête à l'emploi — point d'entrée unique, navigation complète    ║
║                                                                      ║
║  Ce fichier intègre :                                               ║
║    Étapes 01–17 · Splash · CRUD · JSON · Mouvements · Rapports     ║
║    Recherche · Alertes · Stats · Export · Config · Logs             ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import csv
import shutil
import logging
import datetime
import traceback
from pathlib import Path

from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.text    import Text
from rich.align   import Align
from rich.columns import Columns
from rich.prompt  import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

console = Console()

# ════════════════════════════════════════════════════════════════════
#  CONFIGURATION GLOBALE
# ════════════════════════════════════════════════════════════════════

APP_NOM     = "STOCK MANAGER"
APP_VERSION = "1.0"

DOSSIER_DATA    = Path("data")
DOSSIER_EXPORTS = Path("exports")
DOSSIER_LOGS    = Path("logs")

STOCK_FILE  = DOSSIER_DATA / "stock.json"
BACKUP_FILE = DOSSIER_DATA / "stock_backup.json"
CONFIG_FILE = DOSSIER_DATA / "config.json"
HISTO_FILE  = DOSSIER_DATA / "historique.json"
LOG_FILE    = DOSSIER_LOGS / "stock_manager.log"

CONFIG_DEFAUT = {
    "entreprise"        : "Mon Drug Store",
    "adresse"           : "",
    "telephone"         : "",
    "devise"            : "DT",
    "tva"               : 19.0,
    "seuil_exp_urgent"  : 30,
    "seuil_exp_proche"  : 90,
    "nb_resultats_page" : 15,
    "version"           : APP_VERSION,
}

CATEGORIES   = ["Analgésique","Antibiotique","Gastro","Diabétologie",
                "Cardiologie","Dermatologie","Pédiatrie",
                "Parapharmacie","Matériel médical","Autre"]
FOURNISSEURS = ["SIPHAT","ADWYA","PHARMAGHREB","MEDIS","COSMEPHARM","Autre"]
UNITES       = ["boîte","flacon","sachet","tube","unité","litre","kg"]


# ════════════════════════════════════════════════════════════════════
#  UTILITAIRES INTERFACE
# ════════════════════════════════════════════════════════════════════

def effacer():
    os.system("cls" if os.name == "nt" else "clear")

def pause(msg="  Entrée pour continuer…"):
    input(msg)

def ok(msg):   console.print(f"  [bold green]✓  {msg}[/bold green]")
def err(msg):  console.print(f"  [bold red]✗  {msg}[/bold red]")
def info(msg): console.print(f"  [cyan]ℹ  {msg}[/cyan]")


def entete(titre="", fil_ariane="", config=None):
    """Bandeau persistant en haut de chaque page."""
    nom_app  = (config or {}).get("entreprise", APP_NOM)
    now      = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M")
    t = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    t.add_column(ratio=1)
    t.add_column(ratio=2, justify="center")
    t.add_column(ratio=1, justify="right")
    t.add_row(
        f"[bold cyan]{APP_NOM}[/bold cyan]",
        f"[bold white]{titre}[/bold white]",
        f"[dim white]{now}[/dim white]",
    )
    console.print(Panel(t, border_style="dim cyan", padding=(0, 0)))
    if fil_ariane:
        console.print(f"  [dim]📍  {fil_ariane}[/dim]")
    console.print()


def afficher_menu(items, titre="MENU"):
    """
    Affiche un menu générique et retourne l'action du choix.
    items = [(touche, libelle, action), …]
    """
    t = Table(show_header=False, box=None, padding=(0, 3), min_width=48)
    t.add_column(style="bold yellow", width=5)
    t.add_column(style="white")
    for touche, libelle, _ in items:
        if touche == "0":
            t.add_row("", "")
        t.add_row(f"[{touche}]", libelle)
    console.print(Panel(t, title=f"[bold white]{titre}[/bold white]",
                        border_style="cyan", padding=(1, 4)))
    touches = [i[0] for i in items]
    actions = {i[0]: i[2] for i in items}
    choix   = Prompt.ask("  [bold cyan]Votre choix[/bold cyan]",
                         choices=touches, show_choices=False, console=console)
    return actions[choix]


# ════════════════════════════════════════════════════════════════════
#  FONCTIONS MÉTIER (produits)
# ════════════════════════════════════════════════════════════════════

def valeur_stock(p):  return p["prix_achat"] * p["quantite"]
def marge_pct(p):
    return ((p["prix_vente"] - p["prix_achat"]) / p["prix_achat"] * 100) \
           if p["prix_achat"] else 0

def etat_stock(p):
    q = p["quantite"]
    if q == 0:               return ("rupture", "⛔ RUPTURE",  "bold red")
    if q <= p["stock_min"]:  return ("alerte",  "⚠  ALERTE",   "bold yellow")
    if q >  p["stock_max"]:  return ("surplus", "↑  SURPLUS",  "bold magenta")
    return                          ("ok",      "✅ OK",        "bold green")

def jours_exp(p):
    if not p.get("date_expiration"): return None
    try:
        return (datetime.datetime.strptime(p["date_expiration"], "%d/%m/%Y").date()
                - datetime.date.today()).days
    except ValueError: return None

def trouver_par_ref(catalogue, ref):
    ref = ref.upper().strip()
    for p in catalogue:
        if p["reference"] == ref: return p
    return None

def recherche_rapide(catalogue, terme):
    terme = terme.lower().strip()
    return [p for p in catalogue if any(
        terme in p[c].lower()
        for c in ("reference", "nom", "categorie", "fournisseur")
    )] if terme else catalogue[:]


# ════════════════════════════════════════════════════════════════════
#  PERSISTANCE
# ════════════════════════════════════════════════════════════════════

def initialiser():
    """Crée l'arborescence de dossiers si elle n'existe pas."""
    for d in (DOSSIER_DATA, DOSSIER_EXPORTS, DOSSIER_LOGS):
        d.mkdir(exist_ok=True)
    if not STOCK_FILE.exists():  sauvegarder_catalogue([])
    if not CONFIG_FILE.exists(): sauvegarder_config(CONFIG_DEFAUT.copy())
    if not HISTO_FILE.exists():  sauvegarder_historique([])


def charger_catalogue():
    if not STOCK_FILE.exists(): return []
    try:
        with open(STOCK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list): return data
        cat = data.get("catalogue", [])
        meta = data.get("meta", {})
        if meta:
            info(f"Stock chargé : {meta.get('nb_produits','?')} produits "
                 f"— {meta.get('sauvegarde','?')}")
        return cat
    except json.JSONDecodeError:
        err("stock.json corrompu — tentative de restauration backup…")
        if BACKUP_FILE.exists():
            shutil.copy2(BACKUP_FILE, STOCK_FILE)
            return charger_catalogue()
        return []
    except OSError as e:
        err(f"Lecture impossible : {e}"); return []


def sauvegarder_catalogue(catalogue):
    try:
        if STOCK_FILE.exists(): shutil.copy2(STOCK_FILE, BACKUP_FILE)
        with open(STOCK_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "meta": {
                    "sauvegarde": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "nb_produits": len(catalogue),
                },
                "catalogue": catalogue,
            }, f, ensure_ascii=False, indent=2)
        return True
    except OSError as e:
        err(f"Sauvegarde impossible : {e}"); return False


def charger_config():
    if not CONFIG_FILE.exists(): return CONFIG_DEFAUT.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return {**CONFIG_DEFAUT, **json.load(f)}
    except Exception: return CONFIG_DEFAUT.copy()


def sauvegarder_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except OSError: return False


def charger_historique():
    if not HISTO_FILE.exists(): return []
    try:
        with open(HISTO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception: return []


def sauvegarder_historique(historique):
    try:
        with open(HISTO_FILE, "w", encoding="utf-8") as f:
            json.dump(historique[:500], f, ensure_ascii=False, indent=2)
        return True
    except OSError: return False


# ════════════════════════════════════════════════════════════════════
#  SPLASH SCREEN
# ════════════════════════════════════════════════════════════════════

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


def splash_screen(config=None):
    """Écran de démarrage animé."""
    import time
    effacer()

    entreprise = (config or {}).get("entreprise", "Drug Store · Industrie · Commerce")

    contenu = Text(justify="center")
    contenu.append(LOGO, style="bold cyan")
    contenu.append(f"\n  {entreprise}\n", style="bold yellow")
    contenu.append(f"  Gestion de stock professionnelle  v{APP_VERSION}\n",
                   style="dim white")
    console.print(Panel(Align.center(contenu),
                        border_style="bold cyan", padding=(1, 6)))

    # Barre de chargement
    etapes = [
        ("Initialisation du système…",  30, 0.018),
        ("Chargement des données…",     25, 0.015),
        ("Vérification des stocks…",    25, 0.015),
        ("Prêt !",                      20, 0.010),
    ]
    with Progress(
        SpinnerColumn(style="bold cyan"),
        TextColumn("[bold cyan]{task.description:<36}"),
        BarColumn(bar_width=38, style="dim cyan", complete_style="bold green"),
        TextColumn("[bold white]{task.percentage:>3.0f}%"),
        console=console, transient=True,
    ) as progress:
        tache = progress.add_task("Démarrage…", total=100)
        for description, pct, delai in etapes:
            for _ in range(pct):
                progress.update(tache, advance=1, description=description)
                time.sleep(delai)

    now = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    console.print(Align.center(
        Panel(f"[bold green]✓  Système prêt ![/bold green]  "
              f"[dim white]{now}[/dim white]",
              border_style="green", padding=(0, 4))
    ))
    console.print()


# ════════════════════════════════════════════════════════════════════
#  AFFICHAGE CATALOGUE
# ════════════════════════════════════════════════════════════════════

def afficher_catalogue(catalogue, titre="CATALOGUE"):
    """Tableau complet avec couleurs et alternance."""
    if not catalogue:
        console.print(Panel("[yellow]Le catalogue est vide.[/yellow]",
                            border_style="yellow"))
        return
    t = Table(
        title=f"[bold white]{titre}[/bold white]",
        border_style="cyan",
        header_style="bold cyan on dark_blue",
        row_styles=["on grey7", ""],
        show_lines=True,
    )
    t.add_column("Réf.",      style="bold yellow", width=10)
    t.add_column("Nom",       style="white",       width=26)
    t.add_column("Catégorie", style="cyan",        width=14)
    t.add_column("P.Achat",   justify="right",     width=9)
    t.add_column("P.Vente",   style="green",       justify="right", width=9)
    t.add_column("Marge",     style="magenta",     justify="right", width=7)
    t.add_column("Stock",     justify="right",     width=7)
    t.add_column("Statut",    justify="center",    width=12)
    t.add_column("Expiration",width=13)

    for p in catalogue:
        code, libelle, couleur = etat_stock(p)
        j = jours_exp(p)
        if j is None:   exp = "[dim]—[/dim]"
        elif j < 0:     exp = "[bold red]EXPIRÉ[/bold red]"
        elif j < 30:    exp = f"[bold red]{p['date_expiration']}[/bold red]"
        elif j < 90:    exp = f"[yellow]{p['date_expiration']}[/yellow]"
        else:           exp = f"[dim white]{p['date_expiration']}[/dim white]"
        t.add_row(
            p["reference"], p["nom"][:24], p["categorie"][:12],
            f"{p['prix_achat']:.3f}", f"{p['prix_vente']:.3f}",
            f"{marge_pct(p):.1f}%",
            f"[{couleur}]{p['quantite']}[/{couleur}]",
            f"[{couleur}]{libelle}[/{couleur}]",
            exp,
        )
    console.print(t)


def afficher_fiche(p):
    """Fiche détaillée d'un produit."""
    code, libelle, couleur = etat_stock(p)
    j = jours_exp(p)
    if j is None:   exp = "[dim]—[/dim]"
    elif j < 0:     exp = "[bold red]EXPIRÉ[/bold red]"
    elif j < 30:    exp = f"[bold red]{p['date_expiration']} ({j} j)[/bold red]"
    elif j < 90:    exp = f"[yellow]{p['date_expiration']} ({j} j)[/yellow]"
    else:           exp = f"[dim white]{p['date_expiration']}[/dim white]"

    t = Table(show_header=False, box=None, padding=(0, 2), min_width=54)
    t.add_column(style="dim cyan", width=22)
    t.add_column(style="bold white")
    t.add_row("📦 Référence",    p["reference"])
    t.add_row("🏷  Nom",          p["nom"])
    t.add_row("📂 Catégorie",    p["categorie"])
    t.add_row("📐 Unité",         p.get("unite", "—"))
    t.add_row("🏭 Fournisseur",  p["fournisseur"])
    t.add_row("", "")
    t.add_row("💰 Prix achat",   f"{p['prix_achat']:.3f} DT")
    t.add_row("🛒 Prix vente",   f"{p['prix_vente']:.3f} DT")
    t.add_row("📈 Marge",        f"{marge_pct(p):.1f} %")
    t.add_row("", "")
    t.add_row(f"[{couleur}]Stock",
              f"[{couleur}]{p['quantite']} {p.get('unite','')}[/{couleur}]")
    t.add_row("⬇  Seuil alerte", str(p["stock_min"]))
    t.add_row("⬆  Stock max",    str(p["stock_max"]))
    t.add_row("💵 Valeur stock", f"[green]{valeur_stock(p):.3f} DT[/green]")
    t.add_row("", "")
    t.add_row("📅 Expiration",   exp)
    t.add_row("🗓  Créé le",      p.get("date_creation", "—"))
    if p.get("date_modification"):
        t.add_row("✏  Modifié le", p["date_modification"])

    panel_couleur = {"rupture":"red","alerte":"yellow",
                     "surplus":"magenta","ok":"green"}[code]
    console.print(Panel(t,
        title=f"[bold white]FICHE — {p['reference']}  [{couleur}]{libelle}[/{couleur}][/bold white]",
        border_style=panel_couleur, padding=(1, 2)))


# ════════════════════════════════════════════════════════════════════
#  MOUVEMENTS DE STOCK
# ════════════════════════════════════════════════════════════════════

def enregistrer_mouvement(catalogue, historique, ref, type_mvt, quantite, motif=""):
    p = trouver_par_ref(catalogue, ref)
    if not p: return False, f"Produit '{ref}' introuvable"
    if type_mvt == "sortie" and quantite > p["quantite"]:
        return False, f"Stock insuffisant : {p['quantite']} disponibles, {quantite} demandés"
    qte_avant = p["quantite"]
    if   type_mvt == "entree":     p["quantite"] += quantite
    elif type_mvt == "sortie":     p["quantite"] -= quantite
    elif type_mvt == "ajustement": p["quantite"]  = quantite
    historique.insert(0, {
        "date"     : datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "reference": p["reference"],
        "nom"      : p["nom"],
        "type"     : type_mvt,
        "quantite" : quantite,
        "qte_avant": qte_avant,
        "qte_apres": p["quantite"],
        "motif"    : motif,
    })
    p["date_modification"] = datetime.date.today().strftime("%d/%m/%Y")
    return True, p


def afficher_historique(historique, nb=20):
    """Tableau des derniers mouvements."""
    if not historique:
        console.print("[yellow]Aucun mouvement enregistré.[/yellow]"); return
    STYLES = {
        "entree"    : ("[bold green]📥 ENTRÉE[/bold green]",   "green"),
        "sortie"    : ("[bold red]📤 SORTIE[/bold red]",       "red"),
        "ajustement": ("[bold cyan]🔃 AJUST.[/bold cyan]",     "cyan"),
    }
    t = Table(border_style="cyan", header_style="bold cyan",
              row_styles=["on grey7", ""], show_lines=True)
    t.add_column("Date/Heure",  style="dim white", width=20)
    t.add_column("Réf.",        style="bold yellow", width=10)
    t.add_column("Nom",         style="white", width=22)
    t.add_column("Type",        width=12, justify="center")
    t.add_column("Qté",         justify="right", width=6)
    t.add_column("Avant→Après", justify="center", width=14)
    t.add_column("Motif",       style="dim white", width=16)
    for m in historique[:nb]:
        type_txt, coul = STYLES.get(m["type"], (m["type"], "white"))
        t.add_row(
            m["date"], m["reference"], m["nom"][:20], type_txt,
            f"[{coul}]{m['quantite']}[/{coul}]",
            f"{m['qte_avant']} → [{coul}]{m['qte_apres']}[/{coul}]",
            m.get("motif","")[:14],
        )
    console.print(Panel(t, title=f"[white]{len(historique)} mouvement(s)",
                        border_style="cyan"))


# ════════════════════════════════════════════════════════════════════
#  ALERTES
# ════════════════════════════════════════════════════════════════════

def analyser_alertes(catalogue, config=None):
    s_urgent = (config or {}).get("seuil_exp_urgent", 30)
    s_proche = (config or {}).get("seuil_exp_proche", 90)
    res = {"ruptures":[],"alertes_stock":[],"expirations_urgentes":[],"surplus":[]}
    for p in catalogue:
        code = etat_stock(p)[0]
        if code == "rupture":   res["ruptures"].append(p)
        elif code == "alerte":  res["alertes_stock"].append(p)
        elif code == "surplus": res["surplus"].append(p)
        j = jours_exp(p)
        if j is not None and j <= s_urgent:
            res["expirations_urgentes"].append((j, p))
    res["expirations_urgentes"].sort(key=lambda x: x[0])
    return res


def badge_alertes(catalogue, config=None):
    a = analyser_alertes(catalogue, config)
    parties = []
    if a["ruptures"]:
        parties.append(f"[bold red]⛔ {len(a['ruptures'])} rupture(s)[/bold red]")
    if a["alertes_stock"]:
        parties.append(f"[bold yellow]⚠  {len(a['alertes_stock'])} alerte(s)[/bold yellow]")
    if a["expirations_urgentes"]:
        parties.append(f"[bold red]📅 {len(a['expirations_urgentes'])} exp. urgente(s)[/bold red]")
    return "  |  ".join(parties) if parties else "[bold green]✓  Stock en bon état[/bold green]"


def afficher_bulletin_alertes(catalogue, config=None):
    a = analyser_alertes(catalogue, config)
    devise = (config or {}).get("devise", "DT")
    total = len(a["ruptures"]) + len(a["alertes_stock"]) + len(a["expirations_urgentes"])
    if total == 0:
        console.print(Panel("[bold green]✓  Aucune alerte — Stock en bon état.[/bold green]",
                            border_style="green")); return
    # Produits critiques
    critiques = a["ruptures"] + a["alertes_stock"]
    if critiques:
        t = Table(border_style="red", header_style="bold red", show_lines=True)
        t.add_column("Réf.",    style="bold yellow", width=10)
        t.add_column("Nom",     style="white", width=24)
        t.add_column("Stock",   justify="right", width=8)
        t.add_column("Min",     justify="right", width=6)
        t.add_column("Déficit", style="bold red", width=10, justify="right")
        t.add_column("Réappro.",style="yellow", width=14, justify="right")
        for p in sorted(critiques, key=lambda x: x["quantite"]):
            deficit = p["stock_min"] - p["quantite"]
            _, _, coul = etat_stock(p)
            t.add_row(p["reference"], p["nom"][:22],
                      f"[{coul}]{p['quantite']}[/{coul}]",
                      str(p["stock_min"]),
                      f"[bold red]-{deficit}[/bold red]",
                      f"{deficit * p['prix_achat']:.3f} {devise}")
        console.print(Panel(t,
            title=f"[bold red]⛔ RUPTURES ({len(a['ruptures'])})  ⚠  ALERTES ({len(a['alertes_stock'])})[/bold red]",
            border_style="red"))
    # Expirations urgentes
    if a["expirations_urgentes"]:
        t2 = Table(border_style="red", header_style="bold red", show_lines=True)
        t2.add_column("Jours",    justify="right", width=8)
        t2.add_column("Réf.",     style="bold yellow", width=10)
        t2.add_column("Nom",      style="white", width=24)
        t2.add_column("Expiration",width=13)
        t2.add_column("Stock",    justify="right", width=8)
        for j, p in a["expirations_urgentes"]:
            coul = "bold red" if j <= 0 else "red"
            t2.add_row(f"[{coul}]{j}[/{coul}]", p["reference"],
                       p["nom"][:22],
                       f"[{coul}]{p['date_expiration']}[/{coul}]",
                       str(p["quantite"]))
        console.print(Panel(t2,
            title=f"[bold red]📅 EXPIRATIONS URGENTES ({len(a['expirations_urgentes'])})[/bold red]",
            border_style="red"))


# ════════════════════════════════════════════════════════════════════
#  GRAPHE ASCII SIMPLIFIÉ
# ════════════════════════════════════════════════════════════════════

def barre(valeur, maximum, largeur=28, couleur="green"):
    if maximum <= 0: return "[dim]—[/dim]"
    nb  = round(min(1.0, valeur / maximum) * largeur)
    return f"[{couleur}]{'█' * nb}{'░' * (largeur - nb)}[/{couleur}] [dim]{valeur/maximum*100:.0f}%[/dim]"


def graphe_rapide(catalogue):
    """Dashboard visuel compact : stocks et marges par catégorie."""
    cats = {}
    for p in catalogue:
        c = p["categorie"]
        if c not in cats: cats[c] = {"qte": 0, "nb": 0, "marges": []}
        cats[c]["qte"]    += p["quantite"]
        cats[c]["nb"]     += 1
        cats[c]["marges"].append(marge_pct(p))
    if not cats: return
    max_qte = max(d["qte"] for d in cats.values()) or 1
    t = Table(title="[bold white]VUE GRAPHIQUE[/bold white]",
              border_style="blue", header_style="bold blue", show_lines=False)
    t.add_column("Catégorie",   style="cyan", width=16)
    t.add_column("Nb",  justify="right", width=4)
    t.add_column("Stock total", width=36)
    t.add_column("Marge moy.",  justify="right", width=10)
    for cat, d in sorted(cats.items(), key=lambda x: -x[1]["qte"]):
        moy_m = sum(d["marges"]) / len(d["marges"])
        coul_m = "green" if moy_m >= 30 else "yellow" if moy_m >= 15 else "red"
        coul_s = "green" if d["qte"] >= max_qte * 0.5 else "yellow" if d["qte"] >= max_qte * 0.2 else "red"
        t.add_row(cat[:14], str(d["nb"]),
                  barre(d["qte"], max_qte, 30, coul_s),
                  f"[{coul_m}]{moy_m:.1f}%[/{coul_m}]")
    console.print(Panel(t, border_style="blue"))


# ════════════════════════════════════════════════════════════════════
#  FORMULAIRES
# ════════════════════════════════════════════════════════════════════

def _choix(label, options):
    console.print(f"\n  [cyan]{label} :[/cyan]")
    for i, o in enumerate(options, 1):
        console.print(f"    [yellow]{i:>2}.[/yellow]  {o}")
    while True:
        try:
            n = IntPrompt.ask("  [cyan]Numéro[/cyan]", console=console)
            if 1 <= n <= len(options): return options[n - 1]
            console.print(f"  [red]Entre 1 et {len(options)}.[/red]")
        except Exception: console.print("  [red]Numéro invalide.[/red]")


def formulaire_ajouter(catalogue):
    """Formulaire complet d'ajout d'un produit."""
    import re
    console.print(Panel("[bold white]Nouveau produit[/bold white]\n[dim]Entrée = optionnel[/dim]",
                        title="[bold cyan]➕  AJOUTER[/bold cyan]", border_style="cyan"))
    # Référence
    while True:
        ref = Prompt.ask("  [cyan]Référence (ex: MED-099)[/cyan]",
                         console=console).upper().strip()
        if not re.match(r"^[A-Z]{2,4}-\d{2,4}$", ref):
            err("Format : 2–4 lettres, tiret, 2–4 chiffres"); continue
        if ref in [p["reference"] for p in catalogue]:
            err(f"'{ref}' déjà existante"); continue
        break
    nom         = Prompt.ask("  [cyan]Nom du produit[/cyan]", console=console).strip()
    categorie   = _choix("Catégorie", CATEGORIES)
    unite       = _choix("Unité", UNITES)
    fournisseur = _choix("Fournisseur", FOURNISSEURS)
    if fournisseur == "Autre":
        fournisseur = Prompt.ask("  [cyan]Fournisseur[/cyan]", console=console).strip()
    # Prix
    while True:
        try:
            prix_achat = float(Prompt.ask("  [cyan]Prix achat HT (DT)[/cyan]",
                                          console=console).replace(",","."))
            if prix_achat > 0: break
            err("Doit être > 0")
        except ValueError: err("Nombre requis (ex: 3.500)")
    while True:
        try:
            prix_vente = float(Prompt.ask("  [cyan]Prix vente TTC (DT)[/cyan]",
                                          console=console).replace(",","."))
            if prix_vente <= 0: err("Doit être > 0"); continue
            if prix_vente < prix_achat:
                console.print(f"  [yellow]⚠  Marge négative.[/yellow]")
                if not Confirm.ask("  Confirmer ?", console=console): continue
            break
        except ValueError: err("Nombre requis")
    quantite  = IntPrompt.ask("  [cyan]Quantité actuelle[/cyan]", console=console)
    stock_min = IntPrompt.ask("  [cyan]Stock minimum[/cyan]", console=console)
    stock_max = IntPrompt.ask("  [cyan]Stock maximum[/cyan]",
                               default=stock_min * 5, console=console)
    # Expiration
    date_exp = None
    while True:
        s = Prompt.ask("  [cyan]Date expiration JJ/MM/AAAA[/cyan] [dim](Entrée=aucune)[/dim]",
                       default="", console=console).strip()
        if not s: break
        try:
            d = datetime.datetime.strptime(s, "%d/%m/%Y").date()
            if d <= datetime.date.today(): err("Doit être dans le futur"); continue
            date_exp = s; break
        except ValueError: err("Format JJ/MM/AAAA requis")
    # Récapitulatif
    mc = ((prix_vente - prix_achat) / prix_achat * 100) if prix_achat else 0
    console.print(Panel(
        f"[bold cyan]{ref}[/bold cyan]  —  {nom}\n"
        f"{categorie} | {unite} | {fournisseur}\n"
        f"Achat: {prix_achat:.3f}  Vente: [green]{prix_vente:.3f}[/green]  "
        f"Marge: [cyan]{mc:.1f}%[/cyan]\n"
        f"Stock: [yellow]{quantite}[/yellow]  Min: {stock_min}  Max: {stock_max}"
        + (f"\nExp: [yellow]{date_exp}[/yellow]" if date_exp else ""),
        title="[bold white]✅  RÉCAPITULATIF[/bold white]", border_style="green"))
    if not Confirm.ask("\n  [bold white]Confirmer l'ajout ?[/bold white]", console=console):
        info("Ajout annulé."); return None
    return {"reference":ref,"nom":nom,"categorie":categorie,"unite":unite,
            "prix_achat":prix_achat,"prix_vente":prix_vente,"quantite":quantite,
            "stock_min":stock_min,"stock_max":stock_max,"fournisseur":fournisseur,
            "date_expiration":date_exp,
            "date_creation":datetime.date.today().strftime("%d/%m/%Y"),
            "date_modification":None}


def formulaire_entree(catalogue, historique):
    console.print(Panel("[bold white]Réception de marchandises[/bold white]",
                        title="[bold green]📥  ENTRÉE EN STOCK[/bold green]",
                        border_style="green"))
    ref = Prompt.ask("  [cyan]Référence[/cyan]", console=console).upper().strip()
    p   = trouver_par_ref(catalogue, ref)
    if not p: err(f"{ref} introuvable"); return
    console.print(f"  [white]{p['nom']}[/white]  —  Stock : [yellow]{p['quantite']}[/yellow]")
    qte   = IntPrompt.ask("  [cyan]Quantité reçue[/cyan]", console=console)
    motif = Prompt.ask("  [cyan]Motif / BL n°[/cyan] [dim](optionnel)[/dim]",
                       default="", console=console).strip()
    ok_op, res = enregistrer_mouvement(catalogue, historique, ref, "entree", qte, motif)
    if ok_op:
        ok(f"Stock mis à jour : [yellow]{res['quantite']}[/yellow] {res.get('unite','')}")
    else:
        err(res)


def formulaire_sortie(catalogue, historique):
    console.print(Panel("[bold white]Sortie de stock[/bold white]",
                        title="[bold red]📤  SORTIE DE STOCK[/bold red]",
                        border_style="red"))
    ref = Prompt.ask("  [cyan]Référence[/cyan]", console=console).upper().strip()
    p   = trouver_par_ref(catalogue, ref)
    if not p: err(f"{ref} introuvable"); return
    console.print(f"  [white]{p['nom']}[/white]  —  Stock : [yellow]{p['quantite']}[/yellow]")
    qte   = IntPrompt.ask("  [cyan]Quantité sortie[/cyan]", console=console)
    motif = Prompt.ask("  [cyan]Motif[/cyan] [dim](optionnel)[/dim]",
                       default="", console=console).strip()
    ok_op, res = enregistrer_mouvement(catalogue, historique, ref, "sortie", qte, motif)
    if ok_op:
        ok(f"Stock mis à jour : [yellow]{res['quantite']}[/yellow] {res.get('unite','')}")
    else:
        err(res)


# ════════════════════════════════════════════════════════════════════
#  EXPORT RAPIDE
# ════════════════════════════════════════════════════════════════════

def exporter_csv_rapide(catalogue, config=None):
    DOSSIER_EXPORTS.mkdir(exist_ok=True)
    devise = (config or {}).get("devise", "DT")
    tstamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = DOSSIER_EXPORTS / f"catalogue_{tstamp}.csv"
    try:
        with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Réf.","Nom","Catégorie","Unité","P.Achat","P.Vente",
                        "Marge%","Qté","Min","Max","Valeur","Fournisseur",
                        "Expiration","Statut"])
            for p in catalogue:
                _, lib, _ = etat_stock(p)
                w.writerow([p["reference"],p["nom"],p["categorie"],
                             p.get("unite",""),
                             f"{p['prix_achat']:.3f}",f"{p['prix_vente']:.3f}",
                             f"{marge_pct(p):.1f}",p["quantite"],
                             p["stock_min"],p["stock_max"],
                             f"{valeur_stock(p):.3f}",p["fournisseur"],
                             p.get("date_expiration",""),lib])
        ok(f"CSV exporté : [white]{chemin}[/white]  ({len(catalogue)} articles)")
        return chemin
    except OSError as e:
        err(f"Erreur export : {e}"); return None


# ════════════════════════════════════════════════════════════════════
#  NAVIGATION — SOUS-MENUS
# ════════════════════════════════════════════════════════════════════

def nav_produits(catalogue, historique, config):
    MENU = [
        ("1", "➕  Ajouter un produit",    "ajouter"),
        ("2", "📋  Afficher le catalogue", "catalogue"),
        ("3", "🔍  Voir la fiche",          "fiche"),
        ("4", "✏️   Modifier",              "modifier"),
        ("5", "🗑️   Supprimer",             "supprimer"),
        ("6", "🔎  Recherche rapide",       "recherche"),
        ("0", "↩️   Retour",               "retour"),
    ]
    while True:
        effacer()
        entete("Produits", "Menu > Produits", config)
        action = afficher_menu(MENU, "📦  PRODUITS")

        if action == "retour": break

        elif action == "ajouter":
            effacer()
            entete("Ajouter", "Menu > Produits > Ajouter", config)
            nouveau = formulaire_ajouter(catalogue)
            if nouveau:
                if nouveau["reference"] not in [p["reference"] for p in catalogue]:
                    catalogue.append(nouveau)
                    sauvegarder_catalogue(catalogue)
                    ok(f"[cyan]{nouveau['reference']}[/cyan] — {nouveau['nom']} ajouté.")
                else:
                    err("Référence déjà existante.")
            pause()

        elif action == "catalogue":
            effacer()
            entete("Catalogue", "Menu > Produits > Catalogue", config)
            console.print(f"  [dim]{len(catalogue)} produit(s) en catalogue[/dim]\n")
            afficher_catalogue(catalogue)
            pause()

        elif action == "fiche":
            effacer()
            entete("Fiche produit", "Menu > Produits > Fiche", config)
            ref = Prompt.ask("  [cyan]Référence[/cyan]",
                             console=console).upper().strip()
            p   = trouver_par_ref(catalogue, ref)
            if p: afficher_fiche(p)
            else: err(f"'{ref}' introuvable.")
            pause()

        elif action == "modifier":
            effacer()
            entete("Modifier", "Menu > Produits > Modifier", config)
            ref = Prompt.ask("  [cyan]Référence à modifier[/cyan]",
                             console=console).upper().strip()
            p   = trouver_par_ref(catalogue, ref)
            if not p: err(f"'{ref}' introuvable."); pause(); continue
            afficher_fiche(p)
            console.print("[dim]Entrée = conserver la valeur actuelle[/dim]\n")
            CHAMPS = [("nom","Nom","str"),("categorie","Catégorie","str"),
                      ("fournisseur","Fournisseur","str"),
                      ("prix_achat","Prix achat","float"),
                      ("prix_vente","Prix vente","float"),
                      ("quantite","Quantité","int"),
                      ("stock_min","Stock min","int"),("stock_max","Stock max","int"),
                      ("date_expiration","Date expiration","str")]
            changed = False
            for champ, libelle, typ in CHAMPS:
                actuel = str(p.get(champ,""))
                nouv   = Prompt.ask(f"  [cyan]{libelle}[/cyan] [dim](actuel: {actuel})[/dim]",
                                    default=actuel, console=console).strip()
                if nouv != actuel:
                    try:
                        if   typ == "float": p[champ] = float(nouv.replace(",","."))
                        elif typ == "int":   p[champ] = int(nouv)
                        else:                p[champ] = nouv
                        changed = True
                    except ValueError: console.print(f"  [yellow]Valeur ignorée.[/yellow]")
            if changed:
                p["date_modification"] = datetime.date.today().strftime("%d/%m/%Y")
                sauvegarder_catalogue(catalogue)
                ok(f"{ref} modifié.")
            else:
                info("Aucune modification.")
            pause()

        elif action == "supprimer":
            effacer()
            entete("Supprimer", "Menu > Produits > Supprimer", config)
            ref = Prompt.ask("  [cyan]Référence à supprimer[/cyan]",
                             console=console).upper().strip()
            p   = trouver_par_ref(catalogue, ref)
            if not p: err(f"'{ref}' introuvable."); pause(); continue
            afficher_fiche(p)
            console.print("[bold red]  Cette action est irréversible.[/bold red]")
            if Confirm.ask(f"  Supprimer '{ref}' ?", console=console):
                for i, prod in enumerate(catalogue):
                    if prod["reference"] == ref:
                        catalogue.pop(i); break
                sauvegarder_catalogue(catalogue)
                ok(f"{ref} supprimé.")
            else:
                info("Annulé.")
            pause()

        elif action == "recherche":
            effacer()
            entete("Recherche", "Menu > Produits > Recherche", config)
            terme = Prompt.ask("  [cyan]Terme de recherche[/cyan]",
                               console=console).strip()
            res   = recherche_rapide(catalogue, terme)
            if res:
                afficher_catalogue(res, f"Résultats pour '{terme}'")
            else:
                info(f"Aucun résultat pour '{terme}'.")
            pause()


def nav_mouvements(catalogue, historique, config):
    MENU = [
        ("1", "📥  Entrée en stock",    "entree"),
        ("2", "📤  Sortie de stock",    "sortie"),
        ("3", "📋  Voir l'historique",  "historique"),
        ("0", "↩️   Retour",           "retour"),
    ]
    while True:
        effacer()
        entete("Mouvements", "Menu > Mouvements", config)
        action = afficher_menu(MENU, "🔄  MOUVEMENTS")

        if action == "retour": break
        elif action == "entree":
            effacer()
            entete("Entrée", "Menu > Mouvements > Entrée", config)
            formulaire_entree(catalogue, historique)
            sauvegarder_catalogue(catalogue)
            sauvegarder_historique(historique)
            pause()
        elif action == "sortie":
            effacer()
            entete("Sortie", "Menu > Mouvements > Sortie", config)
            formulaire_sortie(catalogue, historique)
            sauvegarder_catalogue(catalogue)
            sauvegarder_historique(historique)
            pause()
        elif action == "historique":
            effacer()
            entete("Historique", "Menu > Mouvements > Historique", config)
            nb = config.get("nb_historique", 20)
            afficher_historique(historique, nb)
            pause()


def nav_rapports(catalogue, historique, config):
    MENU = [
        ("1", "📊  Tableau de bord",     "dashboard"),
        ("2", "📈  Graphe visuel",        "graphe"),
        ("3", "🚨  Bulletin d'alertes",   "alertes"),
        ("4", "📤  Exporter CSV",         "csv"),
        ("0", "↩️   Retour",             "retour"),
    ]
    while True:
        effacer()
        entete("Rapports", "Menu > Rapports", config)
        action = afficher_menu(MENU, "📊  RAPPORTS")

        if action == "retour": break

        elif action == "dashboard":
            effacer()
            entete("Tableau de bord", "Menu > Rapports > Dashboard", config)
            if not catalogue:
                info("Catalogue vide."); pause(); continue
            devise   = config.get("devise", "DT")
            total    = len(catalogue)
            val_tot  = sum(valeur_stock(p) for p in catalogue)
            marge_m  = sum(marge_pct(p) for p in catalogue) / total
            ruptures = sum(1 for p in catalogue if etat_stock(p)[0] == "rupture")
            alertes  = sum(1 for p in catalogue if etat_stock(p)[0] == "alerte")

            kpi = Table(show_header=False, box=None, padding=(0, 2))
            kpi.add_column(style="dim cyan", width=28)
            kpi.add_column(justify="right")
            kpi.add_row("📦 Articles total",      f"[bold white]{total}[/bold white]")
            kpi.add_row("⛔ Ruptures",             f"[bold red]{ruptures}[/bold red]")
            kpi.add_row("⚠  Alertes réappro.",    f"[bold yellow]{alertes}[/bold yellow]")
            kpi.add_row("💵 Valeur totale",        f"[bold green]{val_tot:,.3f} {devise}[/bold green]")
            kpi.add_row("📈 Marge moyenne",        f"[bold cyan]{marge_m:.1f} %[/bold cyan]")

            # Catégories
            cats = {}
            for p in catalogue:
                c = p["categorie"]
                if c not in cats: cats[c] = 0
                cats[c] += valeur_stock(p)
            cat_t = Table(show_header=False, box=None, padding=(0, 2))
            cat_t.add_column(style="cyan", width=18)
            cat_t.add_column(style="green", justify="right")
            for cat, val in sorted(cats.items(), key=lambda x: -x[1])[:6]:
                cat_t.add_row(cat[:16], f"{val:,.0f} {devise}")

            console.print(Columns([
                Panel(kpi,   title="[bold white]📊 INDICATEURS[/bold white]",
                      border_style="blue", width=46),
                Panel(cat_t, title="[bold white]📂 CATÉGORIES[/bold white]",
                      border_style="cyan", width=40),
            ]))
            pause()

        elif action == "graphe":
            effacer()
            entete("Graphe", "Menu > Rapports > Graphe", config)
            graphe_rapide(catalogue)
            pause()

        elif action == "alertes":
            effacer()
            entete("Alertes", "Menu > Rapports > Alertes", config)
            afficher_bulletin_alertes(catalogue, config)
            pause()

        elif action == "csv":
            effacer()
            entete("Export CSV", "Menu > Rapports > Export", config)
            exporter_csv_rapide(catalogue, config)
            pause()


# ════════════════════════════════════════════════════════════════════
#  BOUCLE PRINCIPALE
# ════════════════════════════════════════════════════════════════════

def lancer_application(catalogue, historique, config):
    """Boucle principale de l'application."""

    MENU_PRINCIPAL = [
        ("1", "📦  Gestion des produits",    "produits"),
        ("2", "🔄  Mouvements de stock",     "mouvements"),
        ("3", "📊  Rapports & statistiques", "rapports"),
        ("4", "⚙️   Paramètres",              "parametres"),
        ("0", "🚪  Quitter",                  "quitter"),
    ]

    while True:
        effacer()
        entete(config=config)

        # Badge d'alertes
        badge = badge_alertes(catalogue, config)
        console.print(Align.center(badge))
        console.print()

        action = afficher_menu(MENU_PRINCIPAL, "🏥  MENU PRINCIPAL")

        if action == "quitter":
            effacer()
            console.print(Align.center(Panel(
                "[bold cyan]Merci d'avoir utilisé Stock Manager ![/bold cyan]\n"
                "[dim white]Données sauvegardées automatiquement.[/dim white]",
                border_style="cyan", padding=(1, 8),
            )))
            sauvegarder_catalogue(catalogue)
            sauvegarder_historique(historique)
            break

        elif action == "produits":
            nav_produits(catalogue, historique, config)

        elif action == "mouvements":
            nav_mouvements(catalogue, historique, config)

        elif action == "rapports":
            nav_rapports(catalogue, historique, config)

        elif action == "parametres":
            effacer()
            entete("Paramètres", "Menu > Paramètres", config)
            # Modification rapide nom/devise
            console.print(Panel("[bold white]Paramètres rapides[/bold white]",
                                border_style="cyan"))
            config["entreprise"] = Prompt.ask(
                "  [cyan]Nom de l'entreprise[/cyan]",
                default=config["entreprise"], console=console).strip()
            config["devise"] = Prompt.ask(
                "  [cyan]Devise[/cyan]",
                default=config["devise"], console=console).strip()
            try:
                config["tva"] = float(Prompt.ask(
                    "  [cyan]TVA (%)[/cyan]",
                    default=str(config["tva"]), console=console).replace(",","."))
            except ValueError: pass
            sauvegarder_config(config)
            ok("Paramètres sauvegardés.")
            pause()


# ════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════════════

def main():
    """Séquence complète de démarrage."""

    # Configurer les logs
    DOSSIER_LOGS.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_FILE), level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S", encoding="utf-8",
    )
    logging.info("Application démarrée")

    # Initialiser les dossiers et fichiers
    initialiser()

    # Charger les données
    config     = charger_config()
    catalogue  = charger_catalogue()
    historique = charger_historique()

    # Splash screen
    splash_screen(config)

    # Alertes au démarrage
    alertes  = analyser_alertes(catalogue, config)
    nb_alertes = (len(alertes["ruptures"]) + len(alertes["alertes_stock"])
                  + len(alertes["expirations_urgentes"]))

    if nb_alertes > 0:
        console.print(f"\n  [bold yellow]⚠  {nb_alertes} alerte(s) détectée(s).[/bold yellow]")
        if Confirm.ask("  Afficher le bulletin d'alertes ?",
                       default=True, console=console):
            afficher_bulletin_alertes(catalogue, config)
            pause()

    # Lancer la boucle principale
    lancer_application(catalogue, historique, config)

    logging.info("Application fermée normalement")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Interruption — fermeture propre.[/bold yellow]")
        logging.info("Interruption clavier")
    except Exception as e:
        console.print(f"\n[bold red]Erreur critique : {e}[/bold red]")
        traceback.print_exc()
        logging.critical(f"Erreur critique : {e}")
    finally:
        console.print("[dim]Au revoir ![/dim]")


# ════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — Point d'entrée unique
#     Tout passe par main() → splash → alertes → boucle.
#     Le bloc try/except/finally dans __main__ garantit qu'une
#     fermeture propre s'effectue même en cas d'erreur critique.
#
#  💡 ASTUCE — Sauvegardes systématiques
#     Sauvegarder après CHAQUE opération qui modifie les données
#     (ajouter, modifier, supprimer, entree, sortie) garantit
#     qu'aucune donnée n'est perdue si l'application plante.
#
#  💡 ASTUCE — config passé en paramètre partout
#     config est un dict mutable passé à chaque fonction.
#     Quand une fonction modifie config["devise"], le changement
#     est immédiatement visible dans toute l'application
#     car les dicts sont passés par référence en Python.
#
#  🏋️  EXERCICE FINAL
#     1. Ajouter 5 produits de test au démarrage si le catalogue
#        est vide (données de démonstration).
#     2. Ajouter un raccourci clavier : taper 'a' dans le menu
#        principal pour aller directement à "Ajouter un produit".
#     3. Ajouter une page "À propos" dans le menu paramètres
#        affichant : version, nb produits, valeur totale, nb logs.
# ════════════════════════════════════════════════════════════════════