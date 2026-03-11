# [V6 - Métaclasses] Tableau de stock — ajout des boutons Ajuster et Retour.
# Les boutons utilisent les nouveaux types AjustementMouvement / RetourMouvement
# via les callbacks enregistrés dans app.py.

import customtkinter as ctk
from tkinter import ttk, messagebox

from config import (
    COULEUR_PRIMAIRE, COULEUR_ALERTE, COULEUR_OK,
    COULEUR_ORANGE, COULEUR_FOND, COULEUR_TEXTE
)


class StockFrame(ctk.CTkFrame):
    """
    Panneau principal affichant le tableau de stock.
    [V6] Nouveaux boutons : ⚖️ Ajuster (inventaire) et ↩️ Retour (fournisseur).
    """

    COLONNES = [
        ("ref",        "Référence ↕",   110),
        ("nom",        "Nom ↕",         200),
        ("categorie",  "Catégorie ↕",   110),
        ("prix_achat", "Prix Achat ↕",   90),
        ("prix_vente", "Prix Vente ↕",   90),
        ("qte",        "Quantité ↕",     80),
        ("seuil_min",  "Seuil Min",      80),
        ("statut",     "Statut",         90),
    ]

    def __init__(self, parent, stock_service, callbacks: dict):
        super().__init__(parent, fg_color="transparent")
        self.stock     = stock_service
        self.callbacks = callbacks
        self._tri_colonne = None
        self._tri_asc     = True
        self._filtre_texte = ""
        self._filtre_cat   = "Toutes"
        self._construire()
        self.rafraichir()

    def _construire(self):
        ctk.CTkLabel(
            self, text="📦 Stock des Produits",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self._construire_barre_actions()
        self._construire_barre_actions_v6()   # [V6]
        self._construire_barre_filtres()
        self._construire_tableau()
        self._construire_barre_statut()

    def _construire_barre_actions(self):
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=15, pady=5)

        ctk.CTkButton(barre, text="+ Nouveau",   width=130,
                      fg_color=COULEUR_PRIMAIRE, hover_color="#163D61",
                      command=self.callbacks.get("nouveau")).pack(side="left", padx=(0, 6))
        ctk.CTkButton(barre, text="↑ Entrée",    width=120,
                      fg_color=COULEUR_OK, hover_color="#1E8449",
                      command=self.callbacks.get("entree")).pack(side="left", padx=(0, 6))
        ctk.CTkButton(barre, text="↓ Sortie",    width=120,
                      fg_color=COULEUR_ALERTE, hover_color="#C0392B",
                      command=self.callbacks.get("sortie")).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(barre, text="|", text_color="#BDC3C7",
                     font=ctk.CTkFont(size=16)).pack(side="left", padx=6)
        ctk.CTkButton(barre, text="✏️ Modifier",  width=120,
                      fg_color="#8E44AD", hover_color="#6C3483",
                      command=self.callbacks.get("modifier")).pack(side="left", padx=(0, 6))
        ctk.CTkButton(barre, text="🗑 Supprimer", width=120,
                      fg_color="#E67E22", hover_color="#CA6F1E",
                      command=self.callbacks.get("supprimer")).pack(side="left", padx=(0, 6))
        ctk.CTkButton(barre, text="⟳", width=50,
                      fg_color="#7F8C8D", hover_color="#616A6B",
                      command=self.rafraichir).pack(side="left")

    def _construire_barre_actions_v6(self):
        """[V6] Deuxième barre : boutons Ajustement et Retour fournisseur."""
        barre = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=6)
        barre.pack(fill="x", padx=15, pady=(0, 4))

        ctk.CTkLabel(
            barre, text="V6 →",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#8E44AD",
        ).pack(side="left", padx=(10, 6), pady=6)

        ctk.CTkButton(
            barre, text="⚖️ Ajuster stock",
            width=150, height=30,
            fg_color="#8E44AD", hover_color="#6C3483",
            font=ctk.CTkFont(size=11),
            command=self.callbacks.get("ajuster"),
        ).pack(side="left", padx=(0, 6), pady=6)

        ctk.CTkButton(
            barre, text="↩️ Retour fourn.",
            width=150, height=30,
            fg_color="#16A085", hover_color="#0E6655",
            font=ctk.CTkFont(size=11),
            command=self.callbacks.get("retour"),
        ).pack(side="left", padx=(0, 6), pady=6)

        ctk.CTkLabel(
            barre,
            text="Ajuster = inventaire physique  |  Retour = marchandise renvoyée fournisseur",
            font=ctk.CTkFont(size=9), text_color="#95A5A6",
        ).pack(side="left", padx=4)

    def _construire_barre_filtres(self):
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=15, pady=(0, 4))
        ctk.CTkLabel(barre, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 4))
        self.e_recherche = ctk.CTkEntry(barre, placeholder_text="Rechercher...",
                                         width=220, height=32)
        self.e_recherche.pack(side="left", padx=(0, 12))
        self.e_recherche.bind("<KeyRelease>", self._on_recherche)
        ctk.CTkLabel(barre, text="Catégorie :", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        cats = ["Toutes"] + sorted({p.categorie for p in self.stock})
        self.combo_cat = ctk.CTkOptionMenu(barre, values=cats, width=150, height=32,
                                            command=self._on_filtre_cat)
        self.combo_cat.pack(side="left")
        self.lbl_resultats = ctk.CTkLabel(barre, text="", font=ctk.CTkFont(size=11),
                                           text_color="#7F8C8D")
        self.lbl_resultats.pack(side="right", padx=5)

    def _construire_tableau(self):
        cadre = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        cadre.pack(fill="both", expand=True, padx=15, pady=5)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("AlQalam.Treeview",
                         background="white", foreground=COULEUR_TEXTE,
                         rowheight=30, fieldbackground="white",
                         font=("Segoe UI", 10))
        style.configure("AlQalam.Treeview.Heading",
                         background=COULEUR_PRIMAIRE, foreground="white",
                         font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("AlQalam.Treeview",
                  background=[("selected", COULEUR_PRIMAIRE)],
                  foreground=[("selected", "white")])

        ids = [c[0] for c in self.COLONNES]
        self.tableau = ttk.Treeview(cadre, columns=ids, show="headings",
                                     style="AlQalam.Treeview", selectmode="browse")
        for col_id, label, largeur in self.COLONNES:
            self.tableau.heading(col_id, text=label,
                                  command=lambda c=col_id: self._trier_par(c))
            anchor = "center" if col_id in ("qte", "seuil_min", "statut",
                                             "prix_achat", "prix_vente") else "w"
            self.tableau.column(col_id, width=largeur, anchor=anchor, minwidth=60)

        self.tableau.tag_configure("alerte", background="#FDEDEC", foreground="#922B21")
        self.tableau.tag_configure("ok",     background="#EAFAF1", foreground="#1E8449")
        self.tableau.tag_configure("pair",   background="#F8F9FA")
        self.tableau.tag_configure("impair", background="white")

        scrollbar = ttk.Scrollbar(cadre, orient="vertical", command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=scrollbar.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.pack(side="right", fill="y")
        self.tableau.bind("<Double-1>", self._on_double_clic)

    def _construire_barre_statut(self):
        self.barre_statut = ctk.CTkFrame(self, height=30, fg_color=COULEUR_PRIMAIRE, corner_radius=6)
        self.barre_statut.pack(fill="x", padx=15, pady=(2, 10))
        self.barre_statut.pack_propagate(False)
        self.lbl_statut  = ctk.CTkLabel(self.barre_statut, text="",
                                         font=ctk.CTkFont(size=11), text_color="white")
        self.lbl_statut.pack(side="left", padx=10, pady=4)
        self.lbl_alertes = ctk.CTkLabel(self.barre_statut, text="",
                                         font=ctk.CTkFont(size=11, weight="bold"),
                                         text_color="#FFDDC1")
        self.lbl_alertes.pack(side="right", padx=10, pady=4)

    def rafraichir(self):
        for item in self.tableau.get_children():
            self.tableau.delete(item)
        produits = self.stock.rechercher(self._filtre_texte)
        if self._filtre_cat != "Toutes":
            produits = [p for p in produits if p.categorie == self._filtre_cat]
        produits   = self._appliquer_tri(produits)
        nb_alertes = 0
        for i, p in enumerate(produits):
            en_alerte = p.est_en_alerte()
            if en_alerte: nb_alertes += 1
            tags = ("alerte",) if en_alerte else (("pair",) if i % 2 == 0 else ("impair",))
            self.tableau.insert("", "end", iid=p.ref, tags=tags, values=(
                p.ref, p.nom, p.categorie,
                f"{p.prix_achat:.3f} TND", f"{p.prix_vente:.3f} TND",
                p.qte, p.seuil_min, p.statut_label(),
            ))
        total  = len(self.stock)
        affich = len(produits)
        self.lbl_resultats.configure(
            text="" if affich == total else f"{affich} / {total} résultats"
        )
        self.lbl_statut.configure(
            text=f"📦 {total} produit(s)  |  Valeur : {self.stock.valeur_totale_stock():.2f} TND"
        )
        self.lbl_alertes.configure(
            text=f"⚠️  {nb_alertes} alerte(s)" if nb_alertes > 0 else "✅ Aucune alerte"
        )
        cats = ["Toutes"] + sorted({p.categorie for p in self.stock})
        self.combo_cat.configure(values=cats)

    def _on_recherche(self, _event=None):
        self._filtre_texte = self.e_recherche.get()
        self.rafraichir()

    def _on_filtre_cat(self, valeur: str):
        self._filtre_cat = valeur
        self.rafraichir()

    def _appliquer_tri(self, produits: list) -> list:
        if self._tri_colonne is None or self._tri_colonne == "nom":
            return sorted(produits, reverse=not self._tri_asc)
        cles = {
            "ref"       : lambda p: p.ref,
            "categorie" : lambda p: p.categorie.lower(),
            "prix_achat": lambda p: p.prix_achat,
            "prix_vente": lambda p: p.prix_vente,
            "qte"       : lambda p: p.qte,
            "seuil_min" : lambda p: p.seuil_min,
            "statut"    : lambda p: p.est_en_alerte(),
        }
        key = cles.get(self._tri_colonne, lambda p: p.nom.lower())
        return sorted(produits, key=key, reverse=not self._tri_asc)

    def _trier_par(self, colonne: str):
        if self._tri_colonne == colonne:
            self._tri_asc = not self._tri_asc
        else:
            self._tri_colonne = colonne
            self._tri_asc     = True
        self.rafraichir()

    def _on_double_clic(self, _event):
        ref = self.get_ref_selectionnee()
        if ref and self.callbacks.get("detail"):
            self.callbacks["detail"](ref)

    def get_ref_selectionnee(self) -> str | None:
        sel = self.tableau.selection()
        return sel[0] if sel else None
