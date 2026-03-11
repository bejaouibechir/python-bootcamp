"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 09  ·  Mouvements de stock         ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Entrées, sorties et ajustements de stock avec traçabilité        ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    fonctions · conditions · exceptions · dates · listes de dicts    ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Tableaux d'historique · couleurs conditionnelles · Prompt        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import datetime
from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.prompt  import Prompt, Confirm, IntPrompt

console = Console()

# ── Imports locaux ────────────────────────────────────────────────────
from etape_07_crud        import trouver_par_reference
from etape_08_persistance import ajouter_historique, charger_historique


# ════════════════════════════════════════════════════════════════════
#  LOGIQUE MÉTIER
# ════════════════════════════════════════════════════════════════════

def entree_stock(catalogue, reference, quantite, motif="Réception commande"):
    """
    Augmente le stock d'un produit.

    Retourne un dict résultat :
        ok      bool    succès ?
        message str     description
        avant   int     quantité avant
        apres   int     quantité après
    """
    if quantite <= 0:
        return {"ok": False, "message": "La quantité doit être > 0.", "avant": 0, "apres": 0}

    p = trouver_par_reference(catalogue, reference)
    if p is None:
        return {"ok": False, "message": f"Produit '{reference}' introuvable.",
                "avant": 0, "apres": 0}

    avant       = p["quantite"]
    p["quantite"] += quantite
    p["date_modification"] = datetime.date.today().strftime("%d/%m/%Y")

    ajouter_historique("entree", p["reference"], p["nom"], quantite, motif)

    return {
        "ok"     : True,
        "message": f"Entrée de {quantite} {p['unite']} enregistrée.",
        "avant"  : avant,
        "apres"  : p["quantite"],
    }


def sortie_stock(catalogue, reference, quantite, motif="Vente"):
    """
    Diminue le stock d'un produit.
    Refuse si stock insuffisant.
    """
    if quantite <= 0:
        return {"ok": False, "message": "La quantité doit être > 0.", "avant": 0, "apres": 0}

    p = trouver_par_reference(catalogue, reference)
    if p is None:
        return {"ok": False, "message": f"Produit '{reference}' introuvable.",
                "avant": 0, "apres": 0}

    avant = p["quantite"]

    if quantite > avant:
        return {
            "ok"     : False,
            "message": f"Stock insuffisant ({avant} disponible, {quantite} demandé).",
            "avant"  : avant,
            "apres"  : avant,
        }

    p["quantite"] -= quantite
    p["date_modification"] = datetime.date.today().strftime("%d/%m/%Y")

    ajouter_historique("sortie", p["reference"], p["nom"], quantite, motif)

    return {
        "ok"     : True,
        "message": f"Sortie de {quantite} {p['unite']} enregistrée.",
        "avant"  : avant,
        "apres"  : p["quantite"],
    }


def ajuster_stock(catalogue, reference, nouvelle_quantite, motif="Inventaire"):
    """
    Fixe la quantité exacte (résultat d'un inventaire physique).
    Enregistre la différence comme mouvement.
    """
    if nouvelle_quantite < 0:
        return {"ok": False, "message": "Quantité négative impossible.",
                "avant": 0, "apres": 0}

    p = trouver_par_reference(catalogue, reference)
    if p is None:
        return {"ok": False, "message": f"Produit '{reference}' introuvable.",
                "avant": 0, "apres": 0}

    avant       = p["quantite"]
    diff        = nouvelle_quantite - avant
    p["quantite"] = nouvelle_quantite
    p["date_modification"] = datetime.date.today().strftime("%d/%m/%Y")

    # On enregistre la différence (positive = gain, négative = perte)
    type_mvt = "entree" if diff > 0 else "sortie"
    ajouter_historique(type_mvt, p["reference"], p["nom"],
                       abs(diff), f"Ajustement inventaire — {motif}")

    return {
        "ok"     : True,
        "message": f"Stock ajusté : {avant} → {nouvelle_quantite} (diff: {diff:+d}).",
        "avant"  : avant,
        "apres"  : nouvelle_quantite,
    }


# ════════════════════════════════════════════════════════════════════
#  AFFICHAGE
# ════════════════════════════════════════════════════════════════════

def afficher_resultat_mouvement(produit, resultat):
    """Affiche le résultat d'un mouvement avec jauge visuelle."""
    if not resultat["ok"]:
        console.print(f"\n  [bold red]✗  {resultat['message']}[/bold red]")
        return

    avant   = resultat["avant"]
    apres   = resultat["apres"]
    diff    = apres - avant
    signe   = "+" if diff >= 0 else ""
    couleur = "green" if diff >= 0 else "red"

    # Jauge de stock
    smax    = produit.get("stock_max", max(apres, 1))
    pct     = min(apres / smax, 1.0) if smax > 0 else 0
    barres  = int(pct * 30)
    jauge   = f"[{'green' if pct > 0.3 else 'red'}]{'█' * barres}[/]{'░' * (30 - barres)}"

    console.print(Panel(
        f"  [dim]Avant : [white]{avant}[/white]   →   "
        f"Après : [{couleur}][bold]{apres}[/bold][/{couleur}]   "
        f"([{couleur}]{signe}{diff}[/{couleur}])\n\n"
        f"  {jauge}  {int(pct*100)}%  du max ({smax})",
        title=f"[bold green]✓  {resultat['message']}[/bold green]",
        border_style="green",
    ))


def afficher_historique(n=20):
    """Affiche les n derniers mouvements."""
    hist = charger_historique()
    if not hist:
        console.print(Panel("[yellow]Aucun mouvement enregistré.[/yellow]",
                            border_style="yellow"))
        return

    recents = hist[-n:][::-1]   # les plus récents en premier

    t = Table(border_style="cyan", header_style="bold cyan on dark_blue",
              row_styles=["on grey7", ""])
    t.add_column("Date",       style="dim white",  width=20)
    t.add_column("Type",       justify="center",   width=11)
    t.add_column("Référence",  style="yellow",     width=10)
    t.add_column("Produit",    style="white",       width=26)
    t.add_column("Qté",        justify="right",    width=6)
    t.add_column("Motif",      style="dim white",  width=24)

    for m in recents:
        typ     = m.get("type", "?")
        coul    = "bold green" if typ == "entree" else \
                  "bold red"   if typ == "sortie" else "bold cyan"
        icone   = "📥" if typ == "entree" else \
                  "📤" if typ == "sortie" else "🔃"
        t.add_row(
            m.get("date", ""),
            f"[{coul}]{icone} {typ.upper()}[/{coul}]",
            m.get("reference", ""),
            m.get("nom", "")[:25],
            str(m.get("quantite", 0)),
            m.get("motif", "")[:23],
        )

    console.print(Panel(t,
        title=f"[bold white]📋  HISTORIQUE ({len(recents)} derniers mouvements)[/bold white]",
        border_style="cyan"))


# ════════════════════════════════════════════════════════════════════
#  INTERFACES INTERACTIVES
# ════════════════════════════════════════════════════════════════════

MOTIFS_ENTREE = ["Réception commande", "Retour client", "Régularisation",
                 "Don / Donation", "Autre"]
MOTIFS_SORTIE = ["Vente", "Périmé / Cassé", "Utilisation interne",
                 "Retour fournisseur", "Autre"]

def _saisir_mouvement(catalogue, titre, motifs):
    """Formulaire commun pour entrée et sortie."""
    from etape_07_crud import afficher_liste
    console.print(Panel(f"[bold white]{titre}[/bold white]",
                        border_style="cyan"))

    ref = Prompt.ask("  [cyan]Référence produit[/cyan]", console=console).upper().strip()
    p   = trouver_par_reference(catalogue, ref)
    if not p:
        console.print(f"  [bold red]✗  Produit '{ref}' introuvable.[/bold red]")
        return None, None, None

    console.print(f"  Produit : [bold white]{p['nom']}[/bold white]  "
                  f"— stock actuel : [yellow]{p['quantite']} {p['unite']}[/yellow]")

    qte = IntPrompt.ask("  [cyan]Quantité[/cyan]", console=console)

    console.print(f"\n  [cyan]Motif :[/cyan]")
    for i, m in enumerate(motifs, 1):
        console.print(f"    [yellow]{i}.[/yellow]  {m}")
    n     = IntPrompt.ask("  [cyan]Numéro[/cyan]", console=console)
    motif = motifs[n-1] if 1 <= n <= len(motifs) else "Autre"
    if motif == "Autre":
        motif = Prompt.ask("  [cyan]Préciser[/cyan]", console=console)

    return p, qte, motif


def ui_entree(catalogue):
    p, qte, motif = _saisir_mouvement(catalogue, "📥  ENTRÉE EN STOCK", MOTIFS_ENTREE)
    if p is None: return
    res = entree_stock(catalogue, p["reference"], qte, motif)
    afficher_resultat_mouvement(p, res)


def ui_sortie(catalogue):
    p, qte, motif = _saisir_mouvement(catalogue, "📤  SORTIE DE STOCK", MOTIFS_SORTIE)
    if p is None: return
    res = sortie_stock(catalogue, p["reference"], qte, motif)
    afficher_resultat_mouvement(p, res)


def ui_ajustement(catalogue):
    console.print(Panel("[bold white]🔃  AJUSTEMENT / INVENTAIRE[/bold white]",
                        border_style="cyan"))
    ref  = Prompt.ask("  [cyan]Référence produit[/cyan]", console=console).upper().strip()
    p    = trouver_par_reference(catalogue, ref)
    if not p:
        console.print(f"  [bold red]✗  Produit '{ref}' introuvable.[/bold red]")
        return
    console.print(f"  Stock actuel : [yellow]{p['quantite']} {p['unite']}[/yellow]")
    nqte = IntPrompt.ask("  [cyan]Quantité réelle comptée[/cyan]", console=console)
    if not Confirm.ask(f"  Ajuster à [bold white]{nqte}[/bold white] ?", console=console):
        console.print("  [dim]Annulé.[/dim]"); return
    res = ajuster_stock(catalogue, ref, nqte)
    afficher_resultat_mouvement(p, res)


# ─── Test autonome ────────────────────────────────────────────────────
if __name__ == "__main__":
    cat = [
        {"reference":"MED-001","nom":"Paracétamol 500mg","categorie":"Analgésique",
         "unite":"boîte","prix_achat":3.5,"prix_vente":5.8,"quantite":100,
         "stock_min":50,"stock_max":500,"fournisseur":"SIPHAT",
         "date_expiration":"31/12/2025","date_creation":"01/01/2024",
         "date_modification":None},
    ]
    console.rule("[bold cyan]TEST MOUVEMENTS[/bold cyan]")
    r = entree_stock(cat, "MED-001", 50, "Réception commande")
    afficher_resultat_mouvement(cat[0], r)
    console.print()
    r2 = sortie_stock(cat, "MED-001", 30, "Vente")
    afficher_resultat_mouvement(cat[0], r2)
    console.print()
    afficher_historique()


# ══════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — Retourner un dict résultat
#     Retourner {"ok":..., "message":..., "avant":..., "apres":...}
#     au lieu de True/False permet d'afficher des informations
#     détaillées sans mélanger logique et présentation.
#
#  💡 ASTUCE — La jauge visuelle avec ░ et █
#     Ces caractères Unicode créent une barre de progression
#     sans bibliothèque spéciale. barres = int(pct * 30) donne
#     le nombre de █ à afficher.
#
#  💡 ASTUCE — hist[-n:][::-1]
#     hist[-n:]  → les n derniers éléments
#     [::-1]     → inverser l'ordre (plus récent en premier)
#     Deux slices enchaînées, très idiomatique en Python.
#
#  🏋️  EXERCICE
#     1. Modifier sortie_stock() pour accepter un paramètre
#        "autoriser_negatif=False" qui, si True, permet le stock
#        négatif (commandes en attente de livraison).
#     2. Écrire inventaire_rapide(catalogue) qui parcourt tous
#        les produits et demande la quantité comptée pour chacun.
#     3. Ajouter un champ "prix_unitaire" dans l'historique
#        pour calculer la valeur totale des sorties.
# ══════════════════════════════════════════════════════════════════════