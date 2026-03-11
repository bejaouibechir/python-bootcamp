"""Fenêtre à propos."""

from __future__ import annotations

import customtkinter as ctk

from config import APP_NAME, VERSION


class AboutFrame(ctk.CTkFrame):
    """Affiche les informations produit."""

    def __init__(self, master):
        super().__init__(master)
        texte = (
            f"{APP_NAME}\n"
            f"Version: {VERSION}\n\n"
            "Auteur: Bechir Bejaoui\n"
            "UI: CustomTkinter\n"
            "DB: SQLite\n"
            "Tests: pytest"
        )
        ctk.CTkLabel(self, text="ℹ️ À propos", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=14)
        ctk.CTkLabel(self, text=texte, justify="left").pack(pady=10, padx=20)
