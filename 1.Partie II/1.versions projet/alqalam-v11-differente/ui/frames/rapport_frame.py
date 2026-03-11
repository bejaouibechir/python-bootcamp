"""Frame tableau de bord et exports."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog, messagebox


class RapportFrame(ctk.CTkFrame):
    """Affiche les KPIs et propose les exports CSV/Excel."""

    def __init__(self, master, service, rapport_service, on_refresh):
        super().__init__(master)
        self.service = service
        self.rapport_service = rapport_service
        self.on_refresh = on_refresh

        self.kpi_produits = ctk.CTkLabel(self, text="0 produits", font=ctk.CTkFont(size=24, weight="bold"))
        self.kpi_valeur = ctk.CTkLabel(self, text="0.00 TND", font=ctk.CTkFont(size=24, weight="bold"))
        self.kpi_alertes = ctk.CTkLabel(self, text="0 alertes", font=ctk.CTkFont(size=24, weight="bold"))

        box = ctk.CTkFrame(self)
        box.pack(fill="x", padx=12, pady=12)
        self.kpi_produits.pack(in_=box, side="left", padx=12, pady=12)
        self.kpi_valeur.pack(in_=box, side="left", padx=12, pady=12)
        self.kpi_alertes.pack(in_=box, side="left", padx=12, pady=12)

        actions = ctk.CTkFrame(self)
        actions.pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(actions, text="Exporter CSV", command=self._export_csv).pack(side="left", padx=8, pady=8)
        ctk.CTkButton(actions, text="Exporter Rapport Excel", command=self._export_excel).pack(
            side="left", padx=8, pady=8
        )

        self.stats = ctk.CTkTextbox(self, height=320)
        self.stats.pack(fill="both", expand=True, padx=12, pady=12)

        self.rafraichir()

    def rafraichir(self):
        kpis = self.service.kpis()
        self.kpi_produits.configure(text=f"{kpis['nb_produits']} produits")
        self.kpi_valeur.configure(text=f"{kpis['valeur_stock']:.2f} TND")
        self.kpi_alertes.configure(text=f"⚠️ {kpis['nb_alertes']} alertes")

        self.stats.delete("1.0", "end")
        self.stats.insert("end", "Par catégorie\n\n")
        for cat, vals in self.service.stats_categories().items():
            self.stats.insert(
                "end",
                f"- {cat}: {vals['nb_produits']} produits | {vals['valeur_totale']:.2f} TND | alertes={vals['nb_alertes']}\n",
            )

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            nb = self.rapport_service.exporter_csv(path)
            messagebox.showinfo("Export CSV", f"{nb} lignes exportées")
            self.on_refresh()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    def _export_excel(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        try:
            self.rapport_service.exporter_excel(path)
            messagebox.showinfo("Export Excel", "Rapport Excel généré")
            self.on_refresh()
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))
