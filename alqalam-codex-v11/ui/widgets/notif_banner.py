"""Bandeau de notification des alertes."""

from __future__ import annotations

import customtkinter as ctk


class NotifBanner(ctk.CTkFrame):
    """Affiche un message d'alerte en haut de l'interface."""

    def __init__(self, master):
        super().__init__(master, fg_color="#F4B183", corner_radius=8)
        self.label = ctk.CTkLabel(self, text="", text_color="#3D2B1F")
        self.label.pack(fill="x", padx=8, pady=4)
        self.pack_forget()

    def afficher(self, message: str):
        self.label.configure(text=message)
        self.pack(fill="x", padx=10, pady=6)

    def masquer(self):
        self.pack_forget()
