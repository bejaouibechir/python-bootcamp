# [V4 - Threading] Panneau "Alertes" — inchangé en V6.

import customtkinter as ctk
from tkinter import ttk
from datetime import datetime

from config import (
    COULEUR_PRIMAIRE, COULEUR_ALERTE, COULEUR_OK,
    COULEUR_ORANGE, COULEUR_FOND
)


class AlertesFrame(ctk.CTkFrame):
    """Panneau de surveillance temps réel — thread daemon + Queue."""

    def __init__(self, parent, surveillance_service, **kwargs):
        super().__init__(parent, fg_color=COULEUR_FOND, **kwargs)
        self._surveillance = surveillance_service
        self._id_polling   = None
        self._construire_ui()
        self._demarrer_polling()

    def _construire_ui(self) -> None:
        entete = ctk.CTkFrame(self, fg_color=COULEUR_PRIMAIRE, corner_radius=8)
        entete.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(entete, text="🔍  Surveillance des ruptures — Thread en arrière-plan",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="white").pack(side="left", padx=15, pady=10)
        self._lbl_statut = ctk.CTkLabel(entete, text="⏳ Démarrage...",
                                         font=ctk.CTkFont(size=11), text_color="#A9CCE3")
        self._lbl_statut.pack(side="right", padx=15)

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=10, pady=4)
        ctk.CTkButton(barre, text="▶  Vérifier maintenant",
                      command=self._verifier_maintenant,
                      fg_color="#2196F3", hover_color="#1565C0", width=190).pack(side="left", padx=(0, 6))
        ctk.CTkButton(barre, text="🗑  Effacer historique",
                      command=self._effacer_historique,
                      fg_color="#757575", hover_color="#424242", width=170).pack(side="left")
        self._lbl_info = ctk.CTkLabel(barre, text=f"Intervalle : {self._surveillance.intervalle} s",
                                       font=ctk.CTkFont(size=11), text_color="#666")
        self._lbl_info.pack(side="right", padx=10)

        ctk.CTkLabel(self, text="Produits en alerte (état actuel)",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#333").pack(anchor="w", padx=15, pady=(8, 2))
        self._zone_alertes = ctk.CTkScrollableFrame(self, height=130, fg_color="white")
        self._zone_alertes.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkLabel(self, text="Historique des vérifications",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#333").pack(anchor="w", padx=15, pady=(4, 2))
        frame_tree = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        frame_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        colonnes = ("heure", "nb", "produits")
        self._arbre = ttk.Treeview(frame_tree, columns=colonnes, show="headings", height=8)
        self._arbre.heading("heure",    text="Heure de détection")
        self._arbre.heading("nb",       text="Nb alertes")
        self._arbre.heading("produits", text="Références concernées")
        self._arbre.column("heure",    width=160, anchor="center")
        self._arbre.column("nb",       width=80,  anchor="center")
        self._arbre.column("produits", width=400)

        scroll = ttk.Scrollbar(frame_tree, orient="vertical", command=self._arbre.yview)
        self._arbre.configure(yscrollcommand=scroll.set)
        self._arbre.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scroll.pack(side="right", fill="y", pady=4)

    def _demarrer_polling(self) -> None:
        self._id_polling = self.after(500, self._poll_alertes)

    def _poll_alertes(self) -> None:
        nouvelles = self._surveillance.lire_alertes()
        for alerte in nouvelles:
            self._inserer_historique(alerte)
        self._maj_statut()
        self._maj_alertes_actives()
        self._id_polling = self.after(500, self._poll_alertes)

    def _maj_statut(self) -> None:
        if self._surveillance.est_actif:
            self._lbl_statut.configure(
                text=f"🟢 Thread actif  |  intervalle : {self._surveillance.intervalle} s"
                     f"  |  {self._surveillance.nb_alertes_totales} rapport(s)",
                text_color="#A9D6E5",
            )
        else:
            self._lbl_statut.configure(text="🔴 Thread arrêté", text_color="#F1948A")

    def _maj_alertes_actives(self) -> None:
        for w in self._zone_alertes.winfo_children():
            w.destroy()
        produits = self._surveillance._stock.produits_en_alerte()
        if not produits:
            ctk.CTkLabel(self._zone_alertes,
                         text="✅  Tous les produits sont au-dessus de leur seuil minimum.",
                         text_color=COULEUR_OK, font=ctk.CTkFont(size=12)).pack(padx=10, pady=12)
            return
        for p in produits:
            rang = p.qte / p.seuil_min
            couleur_fond = "#3a0d0d" if rang < 0.5 else "#3a2000"
            couleur_txt  = COULEUR_ALERTE if rang < 0.5 else COULEUR_ORANGE
            ligne = ctk.CTkFrame(self._zone_alertes, fg_color=couleur_fond, corner_radius=6)
            ligne.pack(fill="x", padx=6, pady=2)
            ctk.CTkLabel(ligne, text=f"⚠️  [{p.ref}]  {p.nom}",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=couleur_txt).pack(side="left", padx=12, pady=6)
            ctk.CTkLabel(ligne, text=f"Qté : {p.qte}  /  Seuil : {p.seuil_min}",
                         font=ctk.CTkFont(size=11), text_color="#ccc").pack(side="right", padx=12)

    def _inserer_historique(self, alerte: dict) -> None:
        ts    = datetime.fromisoformat(alerte["timestamp"])
        heure = ts.strftime("%d/%m/%Y  %H:%M:%S")
        refs  = ", ".join(p.ref for p in alerte["produits"])
        self._arbre.insert("", 0, values=(heure, alerte["count"], refs))

    def _verifier_maintenant(self) -> None:
        self._surveillance.forcer_verification()

    def _effacer_historique(self) -> None:
        for item in self._arbre.get_children():
            self._arbre.delete(item)
        self._surveillance.vider_historique()

    def rafraichir(self) -> None:
        self._maj_alertes_actives()

    def arreter_polling(self) -> None:
        if self._id_polling:
            self.after_cancel(self._id_polling)
            self._id_polling = None
