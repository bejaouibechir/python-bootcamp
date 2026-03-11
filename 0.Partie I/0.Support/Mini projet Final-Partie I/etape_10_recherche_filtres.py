"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 10  ·  Recherche & Filtres         ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Implémenter une recherche multi-critères cumulables avec tri     ║
║    dynamique et pagination des résultats                            ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    list comprehension · sorted() · lambda · conditions · datetime   ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Table paginée · Prompt.ask(choices=) · surlignage résultats      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import datetime
from rich.console import Console
from rich.table   import Table
from rich.panel   import Panel
from rich.prompt  import Prompt, Confirm, IntPrompt, FloatPrompt

console = Console()

# ─── Fonctions importées des étapes précédentes ────────────────────────
def etat_stock(p):
    q = p["quantite"]
    if q == 0:               return ("rupture", "⛔ RUPTURE",  "bold red")
    if q <= p["stock_min"]:  return ("alerte",  "⚠  ALERTE",   "bold yellow")
    if q >  p["stock_max"]:  return ("surplus", "↑  SURPLUS",  "bold magenta")
    return                          ("ok",      "✅ OK",        "bold green")

def valeur_stock(p): return p["prix_achat"] * p["quantite"]
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
#  1. MOTEUR DE RECHERCHE MULTI-CRITÈRES
# ════════════════════════════════════════════════════════════════════

def recherche_avancee(catalogue,
                      terme=None,
                      categorie=None,
                      fournisseur=None,
                      prix_max=None,
                      en_alerte=False,
                      expirant_dans=None):
    """
    Filtre le catalogue selon plusieurs critères cumulables.
    Tous les paramètres sont optionnels.

    Parameters
    ----------
    terme          str   recherche dans ref / nom / catégorie / fourn.
    categorie      str   filtre exact sur la catégorie
    fournisseur    str   filtre exact sur le fournisseur
    prix_max       float filtre les produits dont prix_vente <= prix_max
    en_alerte      bool  si True, n'affiche que les produits en alerte
    expirant_dans  int   nombre de jours : retourne les produits
                         expirant dans moins de X jours

    Returns
    -------
    list  liste filtrée (copie — le catalogue original est intact)
    """
    resultats = catalogue[:]    # copie — ne jamais modifier le catalogue original

    # ── Terme de recherche (multi-champs) ─────────────────────────
    if terme:
        t = terme.lower().strip()
        resultats = [
            p for p in resultats
            if any(
                t in p[champ].lower()
                for champ in ("reference", "nom", "categorie", "fournisseur")
            )
        ]

    # ── Filtre catégorie ──────────────────────────────────────────
    if categorie:
        resultats = [
            p for p in resultats
            if p["categorie"].lower() == categorie.lower()
        ]

    # ── Filtre fournisseur ────────────────────────────────────────
    if fournisseur:
        resultats = [
            p for p in resultats
            if p["fournisseur"].lower() == fournisseur.lower()
        ]

    # ── Filtre prix maximum ───────────────────────────────────────
    if prix_max is not None:
        resultats = [p for p in resultats if p["prix_vente"] <= prix_max]

    # ── Filtre alertes uniquement ─────────────────────────────────
    if en_alerte:
        resultats = [
            p for p in resultats
            if p["quantite"] <= p["stock_min"]
        ]

    # ── Filtre expirations proches ────────────────────────────────
    if expirant_dans is not None:
        limite = datetime.date.today() + datetime.timedelta(days=expirant_dans)
        def proche(p):
            j = jours_exp(p)
            if j is None: return False
            return 0 <= j <= expirant_dans
        resultats = [p for p in resultats if proche(p)]

    return resultats


# ════════════════════════════════════════════════════════════════════
#  2. TRI DYNAMIQUE
# ════════════════════════════════════════════════════════════════════

# Clés de tri disponibles → (champ_dict, calcul_special)
CLES_TRI = {
    "n": ("nom",          lambda p: p["nom"]),
    "r": ("référence",    lambda p: p["reference"]),
    "q": ("stock ↑",      lambda p: p["quantite"]),
    "Q": ("stock ↓",      lambda p: -p["quantite"]),
    "p": ("prix vente ↑", lambda p: p["prix_vente"]),
    "P": ("prix vente ↓", lambda p: -p["prix_vente"]),
    "m": ("marge ↑",      lambda p: marge_pct(p)),
    "v": ("valeur stock ↓",lambda p: -valeur_stock(p)),
    "c": ("catégorie",    lambda p: p["categorie"]),
    "e": ("expiration",   lambda p: jours_exp(p) if jours_exp(p) is not None else 99999),
}

def trier_resultats(resultats, cle="n"):
    """Trie une liste de produits selon la clé choisie."""
    if cle not in CLES_TRI:
        cle = "n"
    _, tri_fn = CLES_TRI[cle]
    return sorted(resultats, key=tri_fn)


# ════════════════════════════════════════════════════════════════════
#  3. AFFICHAGE PAGINÉ
# ════════════════════════════════════════════════════════════════════

def afficher_page(resultats, page=1, par_page=10):
    """
    Affiche une page de résultats dans un tableau coloré.

    Parameters
    ----------
    resultats : liste complète
    page      : numéro de page (commence à 1)
    par_page  : nombre de lignes par page

    Returns
    -------
    int  nombre total de pages
    """
    total_pages = max(1, (len(resultats) + par_page - 1) // par_page)
    page = max(1, min(page, total_pages))

    debut = (page - 1) * par_page
    fin   = debut + par_page
    tranche = resultats[debut:fin]

    if not tranche:
        console.print("[yellow]Aucun résultat à afficher.[/yellow]")
        return 0

    t = Table(
        border_style="cyan",
        header_style="bold cyan on dark_blue",
        row_styles=["on grey7", ""],
        show_lines=True,
    )
    t.add_column("#",          style="dim white",  width=4,  justify="right")
    t.add_column("Réf.",       style="bold yellow", width=10)
    t.add_column("Nom",        style="white",       width=24)
    t.add_column("Catégorie",  style="cyan",        width=14)
    t.add_column("P.Vente",    style="green",       width=10, justify="right")
    t.add_column("Marge",      style="magenta",     width=8,  justify="right")
    t.add_column("Stock",      width=7,             justify="right")
    t.add_column("Statut",     width=12,            justify="center")
    t.add_column("Expiration", width=12)

    for i, p in enumerate(tranche, debut + 1):
        code, libelle, couleur = etat_stock(p)
        j = jours_exp(p)
        if j is None:   exp = "[dim]—[/dim]"
        elif j < 0:     exp = "[bold red]EXPIRÉ[/bold red]"
        elif j < 30:    exp = f"[bold red]{p['date_expiration']}[/bold red]"
        elif j < 90:    exp = f"[yellow]{p['date_expiration']}[/yellow]"
        else:           exp = f"[dim white]{p['date_expiration']}[/dim white]"

        t.add_row(
            str(i),
            p["reference"],
            p["nom"][:22],
            p["categorie"][:12],
            f"{p['prix_vente']:.3f}",
            f"{marge_pct(p):.1f}%",
            f"[{couleur}]{p['quantite']}[/{couleur}]",
            f"[{couleur}]{libelle}[/{couleur}]",
            exp,
        )

    titre = (
        f"[bold white]{len(resultats)} résultat(s)  —  "
        f"Page {page}/{total_pages}[/bold white]"
    )
    console.print(Panel(t, title=titre, border_style="cyan"))
    return total_pages


# ════════════════════════════════════════════════════════════════════
#  4. INTERFACE INTERACTIVE DE RECHERCHE
# ════════════════════════════════════════════════════════════════════

def interface_recherche(catalogue):
    """
    Interface complète : saisie des critères → résultats paginés
    avec navigation et tri dynamiques.
    """
    console.print()
    console.print(Panel(
        "[bold white]Définissez vos critères de recherche.[/bold white]\n"
        "[dim]Laissez vide pour ignorer un critère.[/dim]",
        title="[bold cyan]🔍  RECHERCHE AVANCÉE[/bold cyan]",
        border_style="cyan", padding=(0, 2),
    ))
    console.print()

    # ── Saisie des critères ───────────────────────────────────────
    terme = Prompt.ask(
        "  [cyan]Terme[/cyan] [dim](réf / nom / catégorie / fourn.)[/dim]",
        default="", console=console,
    ).strip() or None

    categorie = Prompt.ask(
        "  [cyan]Catégorie exacte[/cyan] [dim](ex: Analgésique)[/dim]",
        default="", console=console,
    ).strip() or None

    fournisseur = Prompt.ask(
        "  [cyan]Fournisseur[/cyan] [dim](ex: SIPHAT)[/dim]",
        default="", console=console,
    ).strip() or None

    prix_max_s = Prompt.ask(
        "  [cyan]Prix vente max (DT)[/cyan] [dim](ex: 10)[/dim]",
        default="", console=console,
    ).strip()
    prix_max = float(prix_max_s.replace(",", ".")) if prix_max_s else None

    en_alerte = Confirm.ask(
        "  [cyan]Uniquement les articles en alerte ?[/cyan]",
        default=False, console=console,
    )

    exp_s = Prompt.ask(
        "  [cyan]Expirant dans moins de X jours[/cyan] [dim](ex: 90)[/dim]",
        default="", console=console,
    ).strip()
    expirant_dans = int(exp_s) if exp_s.isdigit() else None

    # ── Lancer la recherche ───────────────────────────────────────
    resultats = recherche_avancee(
        catalogue, terme, categorie, fournisseur,
        prix_max, en_alerte, expirant_dans,
    )

    if not resultats:
        console.print(Panel(
            "[yellow]Aucun produit ne correspond à ces critères.[/yellow]",
            border_style="yellow",
        ))
        return

    console.print(
        f"\n  [bold white]{len(resultats)}[/bold white] produit(s) trouvé(s) "
        f"sur [dim]{len(catalogue)}[/dim] au total.\n"
    )

    # ── Choisir le tri ────────────────────────────────────────────
    console.print("  Trier par : " + "  ".join(
        f"[yellow]({k})[/yellow] {label}"
        for k, (label, _) in CLES_TRI.items()
    ))
    console.print()
    cle_tri = Prompt.ask(
        "  [cyan]Touche de tri[/cyan]",
        default="n",
        choices=list(CLES_TRI.keys()),
        show_choices=False,
        console=console,
    )
    resultats = trier_resultats(resultats, cle_tri)

    # ── Navigation paginée ────────────────────────────────────────
    page_courante = 1
    par_page      = 10

    while True:
        import os
        os.system("cls" if os.name == "nt" else "clear")
        total_pages = afficher_page(resultats, page_courante, par_page)

        if total_pages <= 1:
            break

        # Navigation
        options = []
        if page_courante > 1:          options.append(("p", "Page précédente"))
        if page_courante < total_pages:options.append(("s", "Page suivante"))
        options.append(("q", "Quitter la recherche"))

        console.print("  " + "  ".join(
            f"[yellow]({k})[/yellow] {l}" for k, l in options
        ))
        touches = [k for k, _ in options]
        choix = Prompt.ask(
            "  [cyan]Navigation[/cyan]",
            choices=touches, show_choices=False, console=console,
        )

        if   choix == "s": page_courante += 1
        elif choix == "p": page_courante -= 1
        elif choix == "q": break


# ════════════════════════════════════════════════════════════════════
#  TEST AUTONOME
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    import datetime

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
        {"reference":"MAT-001","nom":"Seringues 5ml ×100","categorie":"Matériel","unite":"boîte",
         "prix_achat":12.0,"prix_vente":18.0,"quantite":45,"stock_min":10,"stock_max":100,
         "fournisseur":"MEDIS","date_expiration":None,
         "date_creation":"01/01/2024","date_modification":None},
        {"reference":"PAR-001","nom":"Vitamine C 1000mg","categorie":"Parapharmacie","unite":"boîte",
         "prix_achat":6.8,"prix_vente":11.5,"quantite":90,"stock_min":30,"stock_max":300,
         "fournisseur":"PHARMAGHREB","date_expiration":"30/11/2025",
         "date_creation":"01/01/2024","date_modification":None},
    ]

    console.rule("[bold cyan]TEST — RECHERCHE & FILTRES[/bold cyan]")
    console.print()

    # Test 1 : terme libre
    res = recherche_avancee(catalogue_test, terme="anal")
    console.print(f"Terme 'anal'         : [green]{len(res)}[/green] résultat(s)")

    # Test 2 : catégorie
    res = recherche_avancee(catalogue_test, categorie="Analgésique")
    console.print(f"Catégorie Analgésique: [green]{len(res)}[/green] résultat(s)")

    # Test 3 : en alerte
    res = recherche_avancee(catalogue_test, en_alerte=True)
    console.print(f"En alerte            : [yellow]{len(res)}[/yellow] résultat(s)")

    # Test 4 : prix max
    res = recherche_avancee(catalogue_test, prix_max=10.0)
    console.print(f"Prix vente ≤ 10 DT   : [green]{len(res)}[/green] résultat(s)")

    # Test 5 : tri par marge décroissante
    tries = trier_resultats(catalogue_test, "m")
    console.print(f"\nTrié par marge ↑ : "
                  + " → ".join(f"{p['reference']} ({marge_pct(p):.0f}%)" for p in tries))

    # Affichage paginé
    console.print()
    afficher_page(catalogue_test, page=1, par_page=3)


# ════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — resultats = catalogue[:]
#     Crée une COPIE de la liste avant de filtrer.
#     Sans ce [:], chaque filtre modifierait catalogue directement
#     et la liste originale serait détruite.
#
#  💡 ASTUCE — list comprehension à condition multiple
#     [p for p in liste if cond1 and cond2]
#     est plus lisible et plus rapide qu'une boucle for + if imbriqués.
#     Python optimise ces expressions nativement.
#
#  💡 ASTUCE — datetime.timedelta(days=X)
#     Ajoute exactement X jours à une date. Gère automatiquement
#     les mois de longueurs différentes, les années bissextiles, etc.
#     Ne jamais ajouter 86400 secondes manuellement.
#
#  🏋️  EXERCICE
#     1. Ajouter un filtre "valeur_min" qui ne retourne que
#        les produits dont valeur_stock() >= valeur_min.
#     2. Écrire surligner(texte, terme) qui retourne le texte
#        avec le terme en [bold yellow]terme[/bold yellow].
#     3. Ajouter une option de tri "par expiration la plus proche"
#        en ignorant les produits sans date d'expiration.
# ════════════════════════════════════════════════════════════════════