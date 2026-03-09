"""Frame historique des mouvements."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk


class HistoriqueFrame(ctk.CTkFrame):
    """Affiche les mouvements filtrables par référence et type."""

    def __init__(self, master, service):
        super().__init__(master)
        self.service = service
        self.ref = ctk.StringVar()
        self.type_mvt = ctk.StringVar(value="Tous")

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=10)
        ctk.CTkEntry(top, textvariable=self.ref, width=180, placeholder_text="Référence").pack(side="left", padx=6)
        ttk.Combobox(top, textvariable=self.type_mvt, values=["Tous", "entree", "sortie", "retour", "inventaire"], state="readonly", width=14).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Filtrer", command=self.rafraichir).pack(side="left", padx=6)

        self.table = ttk.Treeview(
            self,
            columns=["date", "ref", "type", "qte", "avant", "apres", "note"],
            show="headings",
            height=18,
        )
        for c in ["date", "ref", "type", "qte", "avant", "apres", "note"]:
            self.table.heading(c, text=c.capitalize())
            self.table.column(c, width=120, anchor="center")
        self.table.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.rafraichir()

    def rafraichir(self):
        type_filtre = None if self.type_mvt.get() == "Tous" else self.type_mvt.get()
        ref_filtre = self.ref.get().strip().upper() or None
        lignes = self.service.get_historique(ref=ref_filtre, type_mvt=type_filtre)

        self.table.delete(*self.table.get_children())
        for row in lignes:
            self.table.insert(
                "",
                "end",
                values=(
                    row["date_mvt"],
                    row["ref_produit"],
                    row["type_mvt"],
                    row["qte"],
                    row["qte_avant"],
                    row["qte_apres"],
                    row["note"],
                ),
            )
