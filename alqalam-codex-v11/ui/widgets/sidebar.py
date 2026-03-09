"""Sidebar de navigation."""

from __future__ import annotations

import customtkinter as ctk


class Sidebar(ctk.CTkFrame):
    """Barre latérale avec boutons de navigation."""

    def __init__(self, master, sections: list[tuple[str, str]], callback):
        super().__init__(master, width=220, corner_radius=0)
        self.grid_propagate(False)
        self.callback = callback
        ctk.CTkLabel(self, text="📚 Al Qalam", font=ctk.CTkFont(size=20, weight="bold")).pack(
            pady=(18, 14), padx=10
        )
        for cle, label in sections:
            btn = ctk.CTkButton(self, text=label, command=lambda c=cle: self.callback(c), anchor="w")
            btn.pack(fill="x", padx=10, pady=4)
