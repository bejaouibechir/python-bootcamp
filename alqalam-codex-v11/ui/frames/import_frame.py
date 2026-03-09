"""Frame import/export CSV."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog, messagebox

from alq_io.csv_handler import importer_catalogue


class ImportFrame(ctk.CTkFrame):
    """Interface d'import de catalogue CSV avec rapport détaillé."""

    def __init__(self, master, stock_service, on_refresh):
        super().__init__(master)
        self.stock_service = stock_service
        self.on_refresh = on_refresh

        ctk.CTkLabel(self, text="📁 Import / Export", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkButton(self, text="Importer un catalogue CSV", command=self._importer).pack(pady=10)

        self.resultat = ctk.CTkTextbox(self, height=350)
        self.resultat.pack(fill="both", expand=True, padx=12, pady=12)

    def _importer(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            rapport = importer_catalogue(path, self.stock_service)
            self.resultat.delete("1.0", "end")
            self.resultat.insert("end", str(rapport) + "\n\n")
            for err in rapport.erreurs:
                self.resultat.insert("end", f"- {err}\n")
            self.on_refresh()
        except Exception as exc:
            messagebox.showerror("Erreur import", str(exc))

