# [V1 - UI] Le frame principal : tableau de stock + barre d'actions.
# Un "frame" est un panneau qui vit à l'intérieur de la fenêtre principale.

import customtkinter as ctk
from tkinter import ttk, messagebox

from config import (
    COULEUR_PRIMAIRE, COULEUR_ALERTE, COULEUR_OK,
    COULEUR_ORANGE, COULEUR_FOND, COULEUR_TEXTE
)


class StockFrame(ctk.CTkFrame):
    """
    Panneau principal affichant le tableau de stock.

    Contient :
    - Un tableau (Treeview) avec toutes les colonnes
    - Des boutons d'action (Nouveau, Entrée, Sortie)
    - Une barre de statut avec le compteur d'alertes
    """

    # Colonnes du tableau : (id_interne, label_affiché, largeur_px)
    COLONNES = [
        ("ref",        "Référence",    110),
        ("nom",        "Nom",          200),
        ("categorie",  "Catégorie",    110),
        ("prix_achat", "Prix Achat",    90),
        ("prix_vente", "Prix Vente",    90),
        ("qte",        "Quantité",      80),
        ("seuil_min",  "Seuil Min",     80),
        ("statut",     "Statut",        90),
    ]

    def __init__(self, parent, stock_service, callbacks: dict):
        """
        Args:
            parent       : widget parent (la fenêtre principale)
            stock_service: instance de StockService
            callbacks    : dict avec les fonctions { "nouveau": fn, "entree": fn, "sortie": fn }
        """
        super().__init__(parent, fg_color="transparent")
        self.stock    = stock_service
        self.callbacks = callbacks
        self._construire()
        self.rafraichir()

    # ── Construction de l'interface ───────────────────────────────────────

    def _construire(self):
        """Construit tous les widgets du frame."""
        # Titre du panneau
        titre = ctk.CTkLabel(
            self,
            text="📦 Stock des Produits",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COULEUR_PRIMAIRE
        )
        titre.pack(anchor="w", padx=15, pady=(10, 5))

        # Barre d'actions (boutons)
        self._construire_barre_actions()

        # Tableau des produits
        self._construire_tableau()

        # Barre de statut en bas
        self._construire_barre_statut()

    def _construire_barre_actions(self):
        """Crée la rangée de boutons d'action."""
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=15, pady=5)

        # Bouton : Nouveau produit
        ctk.CTkButton(
            barre,
            text="+ Nouveau produit",
            width=160,
            fg_color=COULEUR_PRIMAIRE,
            hover_color="#163D61",
            command=self.callbacks.get("nouveau")
        ).pack(side="left", padx=(0, 8))

        # Bouton : Entrée de stock
        ctk.CTkButton(
            barre,
            text="↑ Entrée stock",
            width=140,
            fg_color=COULEUR_OK,
            hover_color="#1E8449",
            command=self.callbacks.get("entree")
        ).pack(side="left", padx=(0, 8))

        # Bouton : Sortie de stock
        ctk.CTkButton(
            barre,
            text="↓ Sortie stock",
            width=140,
            fg_color=COULEUR_ALERTE,
            hover_color="#C0392B",
            command=self.callbacks.get("sortie")
        ).pack(side="left", padx=(0, 8))

        # Bouton : Rafraîchir
        ctk.CTkButton(
            barre,
            text="⟳ Rafraîchir",
            width=110,
            fg_color="#7F8C8D",
            hover_color="#616A6B",
            command=self.rafraichir
        ).pack(side="left")

    def _construire_tableau(self):
        """Crée le tableau Treeview avec défilement."""
        # Conteneur du tableau avec bordure
        cadre = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        cadre.pack(fill="both", expand=True, padx=15, pady=5)

        # Style du tableau
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "AlQalam.Treeview",
            background="white",
            foreground=COULEUR_TEXTE,
            rowheight=30,
            fieldbackground="white",
            font=("Segoe UI", 10),
        )
        style.configure(
            "AlQalam.Treeview.Heading",
            background=COULEUR_PRIMAIRE,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map(
            "AlQalam.Treeview",
            background=[("selected", COULEUR_PRIMAIRE)],
            foreground=[("selected", "white")],
        )
        # Styles des tags de ligne (couleurs selon statut)
        style.configure("Treeview", rowheight=30)

        # Création du Treeview
        ids_colonnes = [c[0] for c in self.COLONNES]
        self.tableau = ttk.Treeview(
            cadre,
            columns=ids_colonnes,
            show="headings",
            style="AlQalam.Treeview",
            selectmode="browse",
        )

        # Configuration des colonnes
        for col_id, label, largeur in self.COLONNES:
            self.tableau.heading(col_id, text=label)
            anchor = "center" if col_id in ("qte", "seuil_min", "statut",
                                             "prix_achat", "prix_vente") else "w"
            self.tableau.column(col_id, width=largeur, anchor=anchor, minwidth=60)

        # Tags de couleur par statut
        self.tableau.tag_configure("alerte", background="#FDEDEC", foreground="#922B21")
        self.tableau.tag_configure("ok",     background="#EAFAF1", foreground="#1E8449")
        self.tableau.tag_configure("pair",   background="#F8F9FA")
        self.tableau.tag_configure("impair", background="white")

        # Scrollbar verticale
        scrollbar = ttk.Scrollbar(cadre, orient="vertical", command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scrollbar.set)

        self.tableau.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.pack(side="right", fill="y")

    def _construire_barre_statut(self):
        """Crée la barre de statut en bas du frame."""
        self.barre_statut = ctk.CTkFrame(self, height=30, fg_color=COULEUR_PRIMAIRE,
                                          corner_radius=6)
        self.barre_statut.pack(fill="x", padx=15, pady=(2, 10))
        self.barre_statut.pack_propagate(False)

        self.lbl_statut = ctk.CTkLabel(
            self.barre_statut,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="white"
        )
        self.lbl_statut.pack(side="left", padx=10, pady=4)

        self.lbl_alertes = ctk.CTkLabel(
            self.barre_statut,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FFDDC1"
        )
        self.lbl_alertes.pack(side="right", padx=10, pady=4)

    # ── Données ───────────────────────────────────────────────────────────

    def rafraichir(self):
        """Recharge et réaffiche tous les produits depuis le service."""
        # Vider le tableau
        for item in self.tableau.get_children():
            self.tableau.delete(item)

        produits = self.stock.lister_tous()
        nb_alertes = 0

        for i, p in enumerate(produits):
            en_alerte = p.est_en_alerte()
            if en_alerte:
                nb_alertes += 1

            # Tag de ligne : alerte prioritaire sur pair/impair
            tags = ("alerte",) if en_alerte else (("pair",) if i % 2 == 0 else ("impair",))

            self.tableau.insert("", "end", iid=p.ref, tags=tags, values=(
                p.ref,
                p.nom,
                p.categorie,
                f"{p.prix_achat:.3f} TND",
                f"{p.prix_vente:.3f} TND",
                p.qte,
                p.seuil_min,
                p.statut_label(),
            ))

        # Mise à jour de la barre de statut
        self.lbl_statut.configure(
            text=f"📦 {len(produits)} produit(s) en stock  |  "
                 f"Valeur totale : {self.stock.valeur_totale_stock():.2f} TND"
        )
        if nb_alertes > 0:
            self.lbl_alertes.configure(
                text=f"⚠️  {nb_alertes} alerte(s) de rupture"
            )
        else:
            self.lbl_alertes.configure(text="✅ Aucune alerte")

    def get_ref_selectionnee(self) -> str | None:
        """Retourne la référence de la ligne sélectionnée, ou None."""
        selection = self.tableau.selection()
        return selection[0] if selection else None
