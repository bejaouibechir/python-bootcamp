"""
╔══════════════════════════════════════════════════════════════════════╗
║         STOCK MANAGER  ·  ÉTAPE 01  ·  Découverte de Rich          ║
╠══════════════════════════════════════════════════════════════════════╣
║  Objectif pédagogique                                               ║
║    Remplacer print() par console.print() et découvrir les styles    ║
║                                                                      ║
║  Concepts Python mobilisés                                           ║
║    variables · types str / int / float · f-strings · print()        ║
║                                                                      ║
║  Bibliothèque                                                        ║
║    rich  →  pip install rich                                         ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# ─── Import ────────────────────────────────────────────────────────────
from rich.console import Console

# La Console Rich est l'objet central : elle remplace print()
# et gère tout l'affichage coloré de l'application.
console = Console()


# ─── 1. Texte coloré basique ───────────────────────────────────────────
# Les balises [style] fonctionnent comme des balises HTML.
# Elles se ferment avec [/style] ou sont auto-fermantes en fin de ligne.

console.print("[bold cyan]Bienvenue dans Stock Manager ![/bold cyan]")
console.print("[green]Tout va bien.[/green]")
console.print("[bold red]ERREUR : opération impossible.[/bold red]")
console.print("[bold yellow]ATTENTION : stock faible.[/bold yellow]")


# ─── 2. Styles combinés ────────────────────────────────────────────────
# On peut combiner plusieurs styles dans une même balise.

console.print("[bold underline white]Nom du produit[/bold underline white]")
console.print("[italic dim]Information secondaire[/italic dim]")


# ─── 3. Afficher des variables avec f-strings ─────────────────────────
# Rich comprend parfaitement les f-strings Python.

nom_produit   = "Paracétamol 500mg"
quantite      = 150
prix_unitaire = 5.800

console.print(f"\n[underline cyan]Fiche rapide :[/underline cyan]")
console.print(f"  Produit  : [bold white]{nom_produit}[/bold white]")
console.print(f"  Quantité : [yellow]{quantite}[/yellow] unités")
console.print(f"  Prix     : [green]{prix_unitaire:.3f} DT[/green]")
console.print(f"  Valeur   : [bold green]{quantite * prix_unitaire:.3f} DT[/bold green]")


# ─── 4. Séparateur visuel ─────────────────────────────────────────────
# console.rule() trace une ligne horizontale avec titre centré.
# Indispensable pour structurer les sorties dans le terminal.

console.rule("[bold blue]── Fin de la démonstration ──[/bold blue]")


# ─── 5. Couleurs disponibles (aperçu) ────────────────────────────────
console.print("\n[bold white]Palette de couleurs Rich :[/bold white]")
couleurs = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]
for c in couleurs:
    console.print(f"  [{c}]■[/{c}] {c}")


# ══════════════════════════════════════════════════════════════════════
#  💡 ASTUCE — console.rule()
#     Contrairement à print("─" * 60), console.rule() calcule
#     automatiquement la largeur du terminal et centre le titre.
#     Toujours préférer rule() pour les séparations visuelles.
#
#  💡 ASTUCE — Styles courants à mémoriser
#     [bold]       texte en gras
#     [italic]     texte en italique
#     [underline]  texte souligné
#     [dim]        texte atténué (gris clair)
#     [reverse]    fond/texte inversés
#     [bold red on white]  gras rouge sur fond blanc
#
#  🏋️  EXERCICE
#     1. Ajouter les variables fournisseur (str) et
#        date_creation (str "JJ/MM/AAAA") et les afficher
#        avec des couleurs distinctes.
#     2. Calculer et afficher la TVA (19 %) du prix unitaire.
#     3. Afficher un message d'alerte si quantite < 20.
# ══════════════════════════════════════════════════════════════════════