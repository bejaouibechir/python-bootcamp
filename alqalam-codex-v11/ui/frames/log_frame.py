"""Frame journal de logs."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from config import LOG_PATH
from alq_io.validator import rechercher_dans_logs


class LogFrame(ctk.CTkFrame):
    """Affiche les logs applicatifs avec recherche regex."""

    def __init__(self, master):
        super().__init__(master)
        self.pattern = ctk.StringVar()

        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(top, text="Pattern regex").pack(side="left", padx=6)
        ctk.CTkEntry(top, textvariable=self.pattern, width=260).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Filtrer", command=self.rafraichir).pack(side="left", padx=6)

        self.zone = ctk.CTkTextbox(self)
        self.zone.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.rafraichir()

    def rafraichir(self):
        self.zone.delete("1.0", "end")
        path = Path(LOG_PATH)
        if not path.exists():
            self.zone.insert("end", "Aucun log disponible")
            return
        lignes = path.read_text(encoding="utf-8").splitlines()[-500:]
        pattern = self.pattern.get().strip()
        if pattern:
            try:
                lignes = rechercher_dans_logs(pattern, lignes)
            except ValueError as exc:
                self.zone.insert("end", str(exc))
                return
        self.zone.insert("end", "\n".join(lignes) if lignes else "Aucun résultat")

