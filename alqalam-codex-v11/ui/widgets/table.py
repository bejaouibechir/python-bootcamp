"""Widget de tableau basé sur ttk.Treeview."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class TableStock(ttk.Treeview):
    """Table triable pour afficher les produits."""

    def __init__(self, master, colonnes: list[str], **kwargs):
        super().__init__(master, columns=colonnes, show="headings", **kwargs)
        self._reverse = {c: False for c in colonnes}
        for col in colonnes:
            self.heading(col, text=col.capitalize(), command=lambda c=col: self.trier(c))
            self.column(col, width=120, anchor=tk.CENTER)

    def trier(self, colonne: str):
        lignes = [(self.set(item, colonne), item) for item in self.get_children("")]

        def _key(pair):
            val = pair[0]
            try:
                return float(str(val).replace("TND", "").strip())
            except ValueError:
                return str(val).lower()

        lignes.sort(key=_key, reverse=self._reverse[colonne])
        for idx, (_, item) in enumerate(lignes):
            self.move(item, "", idx)
        self._reverse[colonne] = not self._reverse[colonne]
