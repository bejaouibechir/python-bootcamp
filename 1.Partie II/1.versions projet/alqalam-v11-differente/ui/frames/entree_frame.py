"""Frame d'entrée de stock."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox


class EntreeFrame(ctk.CTkFrame):
    """Formulaire d'entrée de stock."""

    def __init__(self, master, service, on_done):
        super().__init__(master)
        self.service = service
        self.on_done = on_done

        ctk.CTkLabel(self, text="📥 Entrée de stock", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=12)

        self.ref = ctk.StringVar()
        self.qte = ctk.StringVar()
        self.note = ctk.StringVar()

        for label, var in (("Référence", self.ref), ("Quantité", self.qte), ("Note", self.note)):
            row = ctk.CTkFrame(self)
            row.pack(fill="x", padx=20, pady=6)
            ctk.CTkLabel(row, text=label, width=120, anchor="w").pack(side="left")
            ctk.CTkEntry(row, textvariable=var).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(self, text="Valider entrée", command=self._valider).pack(pady=16)

    def _valider(self):
        try:
            self.service.entree_stock(self.ref.get().strip().upper(), int(self.qte.get()), self.note.get().strip())
            messagebox.showinfo("Entrée", "Entrée de stock enregistrée")
            self.on_done()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))
