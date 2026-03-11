"""Frame principal de gestion des produits."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox, ttk

from config import COLONNES_STOCK
from ui.widgets.table import TableStock


class StockFrame(ctk.CTkFrame):
    """Liste, recherche, filtre catégorie et actions produit."""

    def __init__(self, master, service, on_action):
        super().__init__(master)
        self.service = service
        self.on_action = on_action

        self.search_var = ctk.StringVar(value="")
        self.cat_var = ctk.StringVar(value="Toutes")

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top, text="🔍 Rechercher").pack(side="left", padx=(8, 4))
        ent = ctk.CTkEntry(top, textvariable=self.search_var, width=220)
        ent.pack(side="left", padx=4)
        ent.bind("<KeyRelease>", lambda _e: self.rafraichir())

        self.combo = ttk.Combobox(top, textvariable=self.cat_var, state="readonly", width=18)
        self.combo.pack(side="left", padx=8)
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self.rafraichir())

        ctk.CTkButton(top, text="+ Nouveau", command=self._nouveau).pack(side="right", padx=4)
        ctk.CTkButton(top, text="↑ Entrée", command=lambda: on_action("entree")).pack(side="right", padx=4)
        ctk.CTkButton(top, text="↓ Sortie", command=lambda: on_action("sortie")).pack(side="right", padx=4)

        self.table = TableStock(self, COLONNES_STOCK, height=16)
        self.table.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.table.tag_configure("alerte", background="#FFE5CC")
        self.table.bind("<Double-1>", self._detail)

        self.rafraichir()

    def _categories(self):
        cats = sorted({p.categorie for p in self.service.lister_tous()})
        return ["Toutes"] + cats

    def rafraichir(self):
        self.combo["values"] = self._categories()
        if self.cat_var.get() not in self.combo["values"]:
            self.cat_var.set("Toutes")

        texte = self.search_var.get()
        produits = self.service.rechercher(texte)
        if self.cat_var.get() != "Toutes":
            produits = [p for p in produits if p.categorie == self.cat_var.get()]

        self.table.delete(*self.table.get_children())
        for p in produits:
            statut = "⚠️" if p.est_en_alerte() else "✅"
            tag = ("alerte",) if p.est_en_alerte() else ()
            self.table.insert(
                "",
                "end",
                values=(p.ref, p.nom, p.categorie, p.qte, f"{p.prix_vente:.2f}", statut),
                tags=tag,
            )

    def _nouveau(self):
        self.on_action("nouveau")

    def _detail(self, _event):
        selected = self.table.selection()
        if not selected:
            return
        ref = self.table.item(selected[0], "values")[0]
        p = self.service.get_produit(ref)
        messagebox.showinfo(
            "Détail produit",
            (
                f"Réf: {p.ref}\nNom: {p.nom}\nCatégorie: {p.categorie}\n"
                f"Prix achat: {p.prix_achat:.2f}\nPrix vente: {p.prix_vente:.2f}\n"
                f"Qté: {p.qte}\nSeuil mini: {p.seuil_min}"
            ),
        )
