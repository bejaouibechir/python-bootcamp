"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 05  ·  Saisie & Validation         ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Saisir des données utilisateur de façon robuste et élégante      ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    try / except · while · conditions · types · fonctions            ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    Prompt · Confirm · IntPrompt · FloatPrompt · Panel               ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import datetime
from rich.console import Console
from rich.panel   import Panel
from rich.prompt  import Prompt, Confirm, IntPrompt, FloatPrompt

console = Console()

# ── Constantes de référence ───────────────────────────────────────────
CATEGORIES   = ["Analgésique","Antibiotique","Gastro","Diabétologie",
                "Cardiologie","Dermatologie","Pédiatrie","Parapharmacie",
                "Matériel médical","Autre"]

FOURNISSEURS = ["SIPHAT","ADWYA","PHARMAGHREB","MEDIS","COSMEPHARM","Autre"]

UNITES       = ["boîte","flacon","sachet","tube","unité","litre","kg"]


# ══════════════════════════════════════════════════════════════════════
#  FONCTIONS DE VALIDATION (pures — elles ne font qu'évaluer)
#  Retournent toujours un tuple  (ok: bool, message: str)
# ══════════════════════════════════════════════════════════════════════

def valider_reference(ref, catalogue):
    """Référence non vide, format XXX-NNN, et unique dans le catalogue."""
    import re
    if not ref:
        return False, "La référence ne peut pas être vide."
    if not re.match(r"^[A-Z]{2,4}-\d{2,4}$", ref.upper()):
        return False, "Format requis : 2–4 lettres, tiret, 2–4 chiffres  (ex: MED-001)."
    refs = [p["reference"] for p in catalogue]
    if ref.upper() in refs:
        return False, f"La référence [bold yellow]{ref.upper()}[/bold yellow] existe déjà."
    return True, ""

def valider_date_future(date_str):
    """JJ/MM/AAAA, dans le futur (ou vide = sans expiration)."""
    if not date_str:
        return True, ""
    try:
        d = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
        if d <= datetime.date.today():
            return False, "La date doit être dans le futur."
        return True, ""
    except ValueError:
        return False, "Format invalide. Attendu : JJ/MM/AAAA  (ex: 31/12/2026)."

def valider_strictement_positif(valeur):
    return (True, "") if valeur > 0 else (False, "La valeur doit être > 0.")

def valider_positif_ou_nul(valeur):
    return (True, "") if valeur >= 0 else (False, "La valeur ne peut pas être négative.")


# ══════════════════════════════════════════════════════════════════════
#  FONCTIONS DE SAISIE (elles interagissent avec l'utilisateur)
# ══════════════════════════════════════════════════════════════════════

def saisir_choix_liste(label, options):
    """
    Affiche une liste numérotée et retourne l'option choisie.
    L'utilisateur tape le numéro, pas le texte.
    """
    console.print(f"\n  [cyan]{label} :[/cyan]")
    for i, opt in enumerate(options, 1):
        console.print(f"    [yellow]{i:>2}.[/yellow]  {opt}")

    while True:
        try:
            n = IntPrompt.ask(
                "  [cyan]Numéro[/cyan]", console=console
            )
            if 1 <= n <= len(options):
                return options[n - 1]
            console.print(f"  [red]Entrez un numéro entre 1 et {len(options)}.[/red]")
        except Exception:
            console.print("  [red]Entrez un numéro valide.[/red]")


def saisir_float(label, validateur=None):
    """Saisie d'un nombre décimal avec validation optionnelle."""
    while True:
        try:
            valeur = FloatPrompt.ask(f"  [cyan]{label}[/cyan]", console=console)
            if validateur:
                ok, msg = validateur(valeur)
                if not ok:
                    console.print(f"  [bold red]✗  {msg}[/bold red]")
                    continue
            return valeur
        except Exception:
            console.print("  [bold red]✗  Nombre décimal requis (ex: 12.500).[/bold red]")


def saisir_int(label, validateur=None, defaut=None):
    """Saisie d'un entier avec validation optionnelle."""
    while True:
        try:
            kwargs = {"console": console}
            if defaut is not None:
                kwargs["default"] = defaut
            valeur = IntPrompt.ask(f"  [cyan]{label}[/cyan]", **kwargs)
            if validateur:
                ok, msg = validateur(valeur)
                if not ok:
                    console.print(f"  [bold red]✗  {msg}[/bold red]")
                    continue
            return valeur
        except Exception:
            console.print("  [bold red]✗  Entier requis (ex: 100).[/bold red]")


def saisir_date_optionnelle(label):
    """Saisie d'une date optionnelle avec validation."""
    while True:
        val = Prompt.ask(
            f"  [cyan]{label}[/cyan] [dim](Entrée = sans date)[/dim]",
            default="", console=console,
        ).strip()
        ok, msg = valider_date_future(val)
        if not ok:
            console.print(f"  [bold red]✗  {msg}[/bold red]")
            continue
        return val or None


# ══════════════════════════════════════════════════════════════════════
#  FORMULAIRE COMPLET — NOUVEAU PRODUIT
# ══════════════════════════════════════════════════════════════════════

def formulaire_nouveau_produit(catalogue):
    """
    Dialogue interactif complet pour créer un nouveau produit.
    Retourne le dict produit, ou None si l'utilisateur annule.
    """
    console.print()
    console.print(Panel(
        "[bold white]Remplissez chaque champ et appuyez sur Entrée.\n[/bold white]"
        "[dim]Les champs optionnels peuvent être laissés vides.[/dim]",
        title="[bold cyan]➕  NOUVEAU PRODUIT[/bold cyan]",
        border_style="cyan", padding=(0, 2),
    ))
    console.print()

    # ── Référence ─────────────────────────────────────────────────────
    while True:
        ref = Prompt.ask(
            "  [cyan]Référence[/cyan] [dim](ex: MED-099)[/dim]",
            console=console,
        ).upper().strip()
        ok, msg = valider_reference(ref, catalogue)
        if not ok:
            console.print(f"  [bold red]✗  {msg}[/bold red]")
        else:
            break

    # ── Informations générales ─────────────────────────────────────────
    nom        = Prompt.ask("  [cyan]Nom du produit[/cyan]", console=console).strip()
    categorie  = saisir_choix_liste("Catégorie", CATEGORIES)
    unite      = saisir_choix_liste("Unité", UNITES)
    fournisseur= saisir_choix_liste("Fournisseur", FOURNISSEURS)
    if fournisseur == "Autre":
        fournisseur = Prompt.ask(
            "  [cyan]Nom du fournisseur[/cyan]", console=console
        ).strip()

    # ── Prix ──────────────────────────────────────────────────────────
    console.print("\n  [bold white]── Prix ──[/bold white]")
    prix_achat = saisir_float("Prix d'achat HT (DT)", valider_strictement_positif)

    while True:
        prix_vente = saisir_float("Prix de vente TTC (DT)", valider_strictement_positif)
        if prix_vente < prix_achat:
            console.print(
                f"  [bold yellow]⚠  Prix vente ({prix_vente:.3f}) "
                f"< prix achat ({prix_achat:.3f}) → marge négative ![/bold yellow]"
            )
            if not Confirm.ask("  Confirmer quand même ?", console=console):
                continue
        break

    # ── Stock ─────────────────────────────────────────────────────────
    console.print("\n  [bold white]── Stock ──[/bold white]")
    quantite  = saisir_int("Quantité actuelle",  valider_positif_ou_nul)
    stock_min = saisir_int("Stock minimum (alerte)",  valider_positif_ou_nul)
    stock_max = saisir_int("Stock maximum",        valider_positif_ou_nul, defaut=stock_min*5)

    # ── Expiration ─────────────────────────────────────────────────────
    console.print()
    date_exp = saisir_date_optionnelle("Date d'expiration JJ/MM/AAAA")

    # ── Récapitulatif & confirmation ───────────────────────────────────
    marge_c = ((prix_vente - prix_achat) / prix_achat * 100) if prix_achat else 0
    console.print()
    console.print(Panel(
        f"[bold cyan]{ref}[/bold cyan]  —  [white]{nom}[/white]\n"
        f"Catégorie : [cyan]{categorie}[/cyan]  |  Unité : [cyan]{unite}[/cyan]  |  "
        f"Fournisseur : [cyan]{fournisseur}[/cyan]\n"
        f"P.Achat : [white]{prix_achat:.3f} DT[/white]  "
        f"P.Vente : [green]{prix_vente:.3f} DT[/green]  "
        f"Marge : [{'red' if marge_c < 15 else 'yellow' if marge_c < 30 else 'green'}]"
        f"{marge_c:.1f} %[/]\n"
        f"Stock : [yellow]{quantite}[/yellow]  "
        f"Min : [yellow]{stock_min}[/yellow]  Max : [yellow]{stock_max}[/yellow]"
        + (f"\nExpiration : [yellow]{date_exp}[/yellow]" if date_exp else ""),
        title="[bold white]✅  RÉCAPITULATIF[/bold white]",
        border_style="green", padding=(0, 2),
    ))

    if not Confirm.ask("\n  [bold white]Confirmer l'ajout ?[/bold white]", console=console):
        console.print("  [yellow]Ajout annulé.[/yellow]")
        return None

    return {
        "reference": ref, "nom": nom, "categorie": categorie, "unite": unite,
        "prix_achat": prix_achat, "prix_vente": prix_vente,
        "quantite": quantite, "stock_min": stock_min, "stock_max": stock_max,
        "fournisseur": fournisseur, "date_expiration": date_exp,
        "date_creation": datetime.date.today().strftime("%d/%m/%Y"),
        "date_modification": None,
    }


# ─── Test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    console.rule("[bold cyan]TEST — FORMULAIRE DE SAISIE[/bold cyan]")
    cat = []
    produit = formulaire_nouveau_produit(cat)
    if produit:
        cat.append(produit)
        console.print(f"\n[bold green]✓  Produit ajouté ! Catalogue : "
                      f"[white]{len(cat)}[/white] article(s).[/bold green]")


# ══════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — Séparation Validation / Saisie
#     Les fonctions valider_*() ne font qu'évaluer — elles ne
#     lisent jamais de clavier. Cela permet de les tester
#     indépendamment et de les réutiliser dans d'autres contextes
#     (import de données, API…).
#
#  💡 ASTUCE — re.match() pour valider un format
#     r"^[A-Z]{2,4}-\d{2,4}$" signifie :
#       ^        début de la chaîne
#       [A-Z]{2,4}  2 à 4 lettres majuscules
#       -        tiret littéral
#       \d{2,4}  2 à 4 chiffres
#       $        fin de la chaîne
#
#  💡 ASTUCE — Confirm.ask() retourne True/False directement.
#     C'est le moyen le plus lisible pour les confirmations :
#     if not Confirm.ask("Supprimer ?"): return
#
#  🏋️  EXERCICE
#     1. Ajouter la saisie d'un "code barre" (13 chiffres)
#        avec une validation re.match(r"^\d{13}$", val).
#     2. Modifier saisir_choix_liste() pour afficher aussi
#        une option "0. Annuler" qui retourne None.
#     3. Ajouter une alerte si stock_max < stock_min × 2
#        ("Stock max semble très bas par rapport au minimum").
# ══════════════════════════════════════════════════════════════════════