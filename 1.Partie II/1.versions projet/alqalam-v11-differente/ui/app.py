"""Application CustomTkinter principale."""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from config import ALERTE_INTERVALLE, APP_NAME, RACCOURCIS, THEME_DEFAULT, VERSION
from services.alerte_service import AlerteService
from services.rapport_service import RapportService
from services.stock_service import StockService
from ui.frames.about_frame import AboutFrame
from ui.frames.entree_frame import EntreeFrame
from ui.frames.historique_frame import HistoriqueFrame
from ui.frames.import_frame import ImportFrame
from ui.frames.log_frame import LogFrame
from ui.frames.rapport_frame import RapportFrame
from ui.frames.sortie_frame import SortieFrame
from ui.frames.stock_frame import StockFrame
from ui.widgets.notif_banner import NotifBanner
from ui.widgets.sidebar import Sidebar

ctk.set_appearance_mode(THEME_DEFAULT)
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """Fenêtre principale du logiciel."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1300x800")
        self.minsize(1100, 700)

        self.stock_service = StockService()
        self.rapport_service = RapportService(self.stock_service)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(
            self,
            sections=[
                ("stock", "📦 Stock"),
                ("entree", "📥 Entrée"),
                ("sortie", "📤 Sortie"),
                ("rapport", "📊 Tableau de bord"),
                ("import", "📁 Import / Export"),
                ("historique", "🕐 Historique"),
                ("journal", "📜 Journal"),
                ("about", "⚙️ À propos"),
            ],
            callback=self.afficher_frame,
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.zone = ctk.CTkFrame(self)
        self.zone.grid(row=0, column=1, sticky="nsew")
        self.zone.grid_rowconfigure(1, weight=1)
        self.zone.grid_columnconfigure(0, weight=1)

        topbar = ctk.CTkFrame(self.zone)
        topbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
        ctk.CTkLabel(topbar, text=f"{APP_NAME}", font=ctk.CTkFont(size=20, weight="bold")).pack(
            side="left", padx=10
        )
        ctk.CTkButton(topbar, text="☀️/🌙", width=72, command=self.toggle_theme).pack(side="right", padx=8)

        self.notif = NotifBanner(self.zone)
        self.notif.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 0))

        self.container = ctk.CTkFrame(self.zone)
        self.container.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.status = ctk.CTkLabel(self, text="", anchor="w")
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=6)

        self.frames = {
            "stock": StockFrame(self.container, self.stock_service, self._action_stock),
            "entree": EntreeFrame(self.container, self.stock_service, self._retour_stock),
            "sortie": SortieFrame(self.container, self.stock_service, self._retour_stock),
            "rapport": RapportFrame(self.container, self.stock_service, self.rapport_service, self.refresh_all),
            "import": ImportFrame(self.container, self.stock_service, self.refresh_all),
            "historique": HistoriqueFrame(self.container, self.stock_service),
            "journal": LogFrame(self.container),
            "about": AboutFrame(self.container),
        }

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

        self.bind_all("<Control-n>", lambda _e: self._action_stock("nouveau"))
        self.bind_all("<Control-e>", lambda _e: self.afficher_frame("rapport"))
        self.bind_all("<F5>", lambda _e: self.refresh_all())

        self.alerte_service = None
        self._demarrer_surveillance()

        self.protocol("WM_DELETE_WINDOW", self._fermer)
        self.afficher_frame("stock")
        self._maj_status_horloge()

    def _demarrer_surveillance(self):
        self.alerte_service = AlerteService(self.stock_service, intervalle=ALERTE_INTERVALLE)
        self.alerte_service.on_alerte(self._on_rupture_detectee).start()

    def _on_rupture_detectee(self, ruptures):
        self.after(0, lambda: self._afficher_notification(ruptures))

    def _afficher_notification(self, ruptures):
        refs = ", ".join(p.ref for p in ruptures[:3])
        self.notif.afficher(f"⚠️ {len(ruptures)} produit(s) en rupture: {refs}")

    def afficher_frame(self, cle: str):
        self.frames[cle].tkraise()
        self.refresh_all()

    def toggle_theme(self):
        mode = ctk.get_appearance_mode().lower()
        ctk.set_appearance_mode("dark" if mode == "light" else "light")

    def refresh_all(self):
        for f in self.frames.values():
            if hasattr(f, "rafraichir"):
                f.rafraichir()
        self._maj_status()

    def _maj_status(self):
        k = self.stock_service.kpis()
        now = datetime.now().strftime("%H:%M:%S")
        self.status.configure(
            text=(
                f"🟢 Surveillance active | {k['nb_produits']} produits | "
                f"Valeur stock : {k['valeur_stock']:.2f} TND | ⚠️ {k['nb_alertes']} alertes | {now}"
            )
        )

    def _maj_status_horloge(self):
        self._maj_status()
        self.after(1000, self._maj_status_horloge)

    def _action_stock(self, action: str):
        if action == "entree":
            self.afficher_frame("entree")
            return
        if action == "sortie":
            self.afficher_frame("sortie")
            return
        if action == "nouveau":
            self._popup_nouveau()

    def _popup_nouveau(self):
        win = ctk.CTkToplevel(self)
        win.title("Nouveau produit")
        win.geometry("420x360")

        champs = {}
        specs = [
            ("ref", "Référence"),
            ("nom", "Nom"),
            ("categorie", "Catégorie"),
            ("prix_achat", "Prix achat"),
            ("prix_vente", "Prix vente"),
            ("qte", "Quantité"),
            ("seuil_min", "Seuil mini"),
        ]
        for key, label in specs:
            row = ctk.CTkFrame(win)
            row.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(row, text=label, width=120, anchor="w").pack(side="left")
            var = ctk.StringVar()
            ctk.CTkEntry(row, textvariable=var).pack(side="left", fill="x", expand=True)
            champs[key] = var

        def enregistrer():
            from models.produit import Produit

            try:
                produit = Produit(
                    ref=champs["ref"].get(),
                    nom=champs["nom"].get(),
                    categorie=champs["categorie"].get(),
                    prix_achat=float(champs["prix_achat"].get()),
                    prix_vente=float(champs["prix_vente"].get()),
                    qte=int(champs["qte"].get() or "0"),
                    seuil_min=int(champs["seuil_min"].get() or "5"),
                )
                self.stock_service.ajouter_produit(produit)
                win.destroy()
                self.refresh_all()
            except Exception as exc:
                messagebox.showerror("Erreur", str(exc))

        ctk.CTkButton(win, text="Créer", command=enregistrer).pack(pady=12)

    def _retour_stock(self):
        self.afficher_frame("stock")

    def _fermer(self):
        if self.alerte_service:
            self.alerte_service.arreter()
        self.destroy()


def splash_screen():
    splash = ctk.CTk()
    splash.title("Démarrage")
    splash.geometry("420x180")
    ctk.CTkLabel(splash, text="📚 Al Qalam Stock Manager", font=ctk.CTkFont(size=24, weight="bold")).pack(
        pady=(30, 12)
    )
    bar = ctk.CTkProgressBar(splash, width=300)
    bar.pack(pady=6)
    bar.set(0)

    def avancer(step=0):
        bar.set(step / 20)
        if step < 20:
            splash.after(35, lambda: avancer(step + 1))
        else:
            splash.destroy()

    avancer()
    splash.mainloop()


def lancer_application():
    splash_screen()
    app = App()
    app.mainloop()
