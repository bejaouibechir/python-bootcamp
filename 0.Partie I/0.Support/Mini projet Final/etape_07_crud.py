"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 07  ·  CRUD — Gestion produits     ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Implémenter les 4 opérations fondamentales sur les données       ║
║    Create · Read · Update · Delete                                  ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    list · dict · boucles · conditions · fonctions · enumerate()     ║
║                                                                      ║
║  Nouveaux outils Rich                                                ║
║    affichage résultats de recherche · tableau de modification        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import datetime
from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.prompt  import Prompt, Confirm, IntPrompt, FloatPrompt

console = Console()


# ════════════════════════════════════════════════════════════════════
#  FONCTIONS CRUD PURES  (pas d'affichage — logique seule)
# ════════════════════════════════════════════════════════════════════

# ── CREATE ────────────────────────────────────────────────────────────

def ajouter_produit(catalogue, produit):
    """
    Ajoute un produit si sa référence est unique.
    Retourne True si ajouté, False si référence déjà présente.
    """
    if any(p["reference"] == produit["reference"] for p in catalogue):
        return False
    catalogue.append(produit)
    return True


# ── READ ──────────────────────────────────────────────────────────────

def trouver_par_reference(catalogue, reference):
    """Retourne le produit correspondant à la référence, ou None."""
    ref = reference.upper().strip()
    for p in catalogue:
        if p["reference"] == ref:
            return p
    return None


def rechercher(catalogue, terme):
    """
    Recherche dans référence, nom, catégorie, fournisseur.
    Retourne la liste des correspondances (insensible à la casse).
    """
    if not terme.strip():
        return catalogue[:]
    t = terme.lower()
    return [
        p for p in catalogue
        if any(t in str(p.get(champ, "")).lower()
               for champ in ("reference","nom","categorie","fournisseur"))
    ]


def filtrer(catalogue, categorie=None, fournisseur=None, en_alerte=False):
    """Filtre multi-critères. Critères None = ignorés."""
    res = catalogue[:]
    if categorie:
        res = [p for p in res if p["categorie"] == categorie]
    if fournisseur:
        res = [p for p in res if p["fournisseur"] == fournisseur]
    if en_alerte:
        res = [p for p in res if p["quantite"] <= p["stock_min"]]
    return res


def trier(catalogue, cle="nom", inverse=False):
    """
    Retourne une copie triée du catalogue.
    Clés valides : nom · reference · quantite · prix_vente ·
                   prix_achat · categorie · fournisseur
    """
    cles_valides = {"nom","reference","quantite","prix_vente",
                    "prix_achat","categorie","fournisseur"}
    k = cle if cle in cles_valides else "nom"
    return sorted(catalogue, key=lambda p: p[k], reverse=inverse)


# ── UPDATE ────────────────────────────────────────────────────────────

CHAMPS_PROTEGES = {"reference", "date_creation"}

def modifier_produit(catalogue, reference, modifications):
    """
    Applique les modifications à un produit existant.
    Les champs protégés (reference, date_creation) sont ignorés.
    Retourne True si modifié, False si produit introuvable.
    """
    p = trouver_par_reference(catalogue, reference)
    if p is None:
        return False
    for champ, val in modifications.items():
        if champ in CHAMPS_PROTEGES:
            continue
        if champ in ("prix_achat", "prix_vente"):
            p[champ] = float(val)
        elif champ in ("quantite", "stock_min", "stock_max"):
            p[champ] = int(val)
        else:
            p[champ] = val
    p["date_modification"] = datetime.date.today().strftime("%d/%m/%Y")
    return True


# ── DELETE ────────────────────────────────────────────────────────────

def supprimer_produit(catalogue, reference):
    """
    Retire le produit du catalogue.
    Retourne le produit supprimé, ou None si introuvable.
    """
    for i, p in enumerate(catalogue):
        if p["reference"] == reference.upper():
            return catalogue.pop(i)   # pop() retire ET retourne
    return None


# ════════════════════════════════════════════════════════════════════
#  AFFICHAGE RÉSULTATS
# ════════════════════════════════════════════════════════════════════

def _etat(p):
    q = p["quantite"]
    if q == 0:              return "bold red",     "⛔ RUPTURE"
    if q <= p["stock_min"]: return "bold yellow",  "⚠  ALERTE"
    if q >  p["stock_max"]: return "bold magenta", "↑  SURPLUS"
    return                         "bold green",   "✅ OK"

def _exp_txt(p):
    if not p.get("date_expiration"): return "[dim]—[/dim]"
    try:
        j = (datetime.datetime.strptime(p["date_expiration"],"%d/%m/%Y").date()
             - datetime.date.today()).days
        if j < 0:   return "[bold red]EXPIRÉ[/bold red]"
        if j < 30:  return f"[bold red]{p['date_expiration']}[/bold red]"
        if j < 90:  return f"[yellow]{p['date_expiration']}[/yellow]"
        return f"[dim white]{p['date_expiration']}[/dim white]"
    except ValueError: return p["date_expiration"]


def afficher_liste(produits, titre="Résultats"):
    """Affiche une liste de produits en tableau compact."""
    if not produits:
        console.print(Panel("[yellow]Aucun produit trouvé.[/yellow]",
                            border_style="yellow"))
        return

    t = Table(border_style="cyan", header_style="bold cyan on dark_blue",
              show_lines=False, row_styles=["on grey7",""])
    t.add_column("Réf.",      style="bold yellow", width=10)
    t.add_column("Nom",       style="white",        width=28)
    t.add_column("Catégorie", style="cyan",          width=15)
    t.add_column("P.Vente",   style="green", justify="right", width=10)
    t.add_column("Stock",     justify="right",       width=7)
    t.add_column("Statut",    justify="center",      width=12)
    t.add_column("Expiration",                       width=13)

    for p in produits:
        coul, label = _etat(p)
        t.add_row(
            p["reference"], p["nom"], p["categorie"],
            f"{p['prix_vente']:.3f} DT",
            f"[{coul}]{p['quantite']}[/{coul}]",
            f"[{coul}]{label}[/{coul}]",
            _exp_txt(p),
        )

    console.print(Panel(t,
        title=f"[bold white]{titre}  ({len(produits)} article(s))[/bold white]",
        border_style="cyan"))


# ════════════════════════════════════════════════════════════════════
#  INTERFACES INTERACTIVES (menus → actions)
# ════════════════════════════════════════════════════════════════════

def ui_afficher_fiche(catalogue):
    """Demande une référence et affiche la fiche complète."""
    from etape_03_modele_produit import afficher_fiche  # réutilisation
    ref = Prompt.ask("  [cyan]Référence[/cyan]", console=console).upper().strip()
    p   = trouver_par_reference(catalogue, ref)
    if p:
        console.print(); afficher_fiche(p)
    else:
        console.print(f"  [bold red]✗  Produit '{ref}' introuvable.[/bold red]")


def ui_recherche(catalogue):
    """Saisie d'un terme et affichage des résultats."""
    terme = Prompt.ask("  [cyan]Terme de recherche[/cyan]", console=console).strip()
    res   = rechercher(catalogue, terme)
    afficher_liste(res, f"Recherche : '{terme}'")


def ui_modifier(catalogue):
    """Formulaire de modification d'un produit existant."""
    ref = Prompt.ask("  [cyan]Référence à modifier[/cyan]", console=console).upper().strip()
    p   = trouver_par_reference(catalogue, ref)
    if not p:
        console.print(f"  [bold red]✗  Produit '{ref}' introuvable.[/bold red]")
        return

    CHAMPS = [
        ("nom",             "Nom",             "str"),
        ("categorie",       "Catégorie",        "str"),
        ("fournisseur",     "Fournisseur",      "str"),
        ("unite",           "Unité",            "str"),
        ("prix_achat",      "Prix achat HT",    "float"),
        ("prix_vente",      "Prix vente TTC",   "float"),
        ("quantite",        "Quantité",         "int"),
        ("stock_min",       "Stock minimum",    "int"),
        ("stock_max",       "Stock maximum",    "int"),
        ("date_expiration", "Expiration (JJ/MM/AAAA)", "str"),
    ]

    console.print(Panel(
        f"[bold white]Modification de [cyan]{ref}[/cyan] — {p['nom']}[/bold white]\n"
        "[dim]Appuyez sur Entrée pour conserver la valeur actuelle.[/dim]",
        border_style="cyan"))
    console.print()

    modifs = {}
    for champ, libelle, typ in CHAMPS:
        actuel = str(p.get(champ) or "")
        nouv   = Prompt.ask(
            f"  [cyan]{libelle}[/cyan] [dim](actuel: {actuel})[/dim]",
            default=actuel, console=console,
        ).strip()
        if nouv != actuel:
            try:
                modifs[champ] = float(nouv) if typ == "float" \
                           else int(nouv)   if typ == "int"   \
                           else nouv
            except ValueError:
                console.print(f"  [yellow]⚠  Valeur ignorée pour '{libelle}'[/yellow]")

    if not modifs:
        console.print("  [dim]Aucune modification.[/dim]")
        return

    modifier_produit(catalogue, ref, modifs)
    console.print(f"  [bold green]✓  {len(modifs)} champ(s) modifié(s).[/bold green]")


def ui_supprimer(catalogue):
    """Confirmation puis suppression d'un produit."""
    ref = Prompt.ask("  [cyan]Référence à supprimer[/cyan]", console=console).upper().strip()
    p   = trouver_par_reference(catalogue, ref)
    if not p:
        console.print(f"  [bold red]✗  Produit '{ref}' introuvable.[/bold red]")
        return

    console.print(f"\n  Produit : [bold white]{p['nom']}[/bold white]  "
                  f"— stock actuel : [yellow]{p['quantite']}[/yellow]")
    if not Confirm.ask("  [bold red]Confirmer la suppression ?[/bold red]",
                       default=False, console=console):
        console.print("  [dim]Suppression annulée.[/dim]")
        return

    supprimer_produit(catalogue, ref)
    console.print(f"  [bold green]✓  Produit {ref} supprimé.[/bold green]")


# ─── Test autonome ────────────────────────────────────────────────────
if __name__ == "__main__":
    cat = [
        {"reference":"MED-001","nom":"Paracétamol 500mg","categorie":"Analgésique",
         "unite":"boîte","prix_achat":3.5,"prix_vente":5.8,"quantite":250,
         "stock_min":50,"stock_max":500,"fournisseur":"SIPHAT",
         "date_expiration":"31/12/2025","date_creation":"01/01/2024",
         "date_modification":None},
        {"reference":"MED-002","nom":"Ibuprofène 400mg","categorie":"Analgésique",
         "unite":"boîte","prix_achat":4.2,"prix_vente":7.2,"quantite":18,
         "stock_min":30,"stock_max":300,"fournisseur":"ADWYA",
         "date_expiration":"30/09/2025","date_creation":"01/01/2024",
         "date_modification":None},
    ]
    console.rule("[bold cyan]TEST CRUD[/bold cyan]")
    afficher_liste(cat, "Catalogue initial")
    console.print()
    res = rechercher(cat, "ib")
    afficher_liste(res, "Recherche 'ib'")


# ══════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — any() avec expression génératrice
#     any(condition for item in liste) parcourt la liste et
#     s'arrête au premier True — plus efficace qu'une boucle
#     for + break manuelle. Parfait pour les tests d'existence.
#
#  💡 ASTUCE — catalogue.pop(i) dans supprimer_produit()
#     pop(index) retire ET retourne l'élément en une seule op.
#     C'est plus propre que del catalogue[i] + return p séparés.
#
#  💡 ASTUCE — Copie vs référence dans trier()
#     sorted() retourne TOUJOURS une nouvelle liste.
#     catalogue.sort() trie EN PLACE (modifie l'original).
#     Pour l'affichage, on veut une copie → sorted().
#
#  🏋️  EXERCICE
#     1. Écrire dupliquer_produit(catalogue, ref, nouvelle_ref)
#        qui copie un produit avec une nouvelle référence.
#        Indice : utilisez dict.copy() puis modifiez les champs.
#     2. Écrire rechercher_avance(catalogue, prix_max, en_alerte)
#        qui combine plusieurs filtres.
#     3. Modifier trier() pour accepter cle="valeur_stock"
#        (prix_achat × quantite) — calculé dynamiquement.
# ══════════════════════════════════════════════════════════════════════