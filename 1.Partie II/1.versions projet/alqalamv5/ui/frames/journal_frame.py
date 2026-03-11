# [V5 - Décorateurs] Panneau "Journal" — 4ème onglet de l'application.
#
# Ce frame affiche en temps réel les opérations enregistrées par le décorateur
# @journaliser. Il rafraîchit la liste toutes les 2 secondes via after().

import customtkinter as ctk
from tkinter import ttk

from config import COULEUR_PRIMAIRE, COULEUR_ALERTE, COULEUR_OK, COULEUR_FOND


class JournalFrame(ctk.CTkFrame):
    """
    Panneau d'audit — historique de toutes les opérations décorées.

    Responsabilités :
    - Afficher la liste des opérations avec icône, heure, ref, résultat
    - Filtrer par type (toutes / erreurs seulement)
    - Permettre d'effacer le journal
    - Afficher les KPIs du journal (total, erreurs)
    """

    def __init__(self, parent, stock_service, **kwargs):
        super().__init__(parent, fg_color=COULEUR_FOND, **kwargs)
        self._stock    = stock_service
        self._id_poll  = None
        self._filtre   = "toutes"   # "toutes" ou "erreurs"

        self._construire_ui()
        self._demarrer_polling()

    # ── Construction ───────────────────────────────────────────────────────

    def _construire_ui(self) -> None:
        # En-tête
        entete = ctk.CTkFrame(self, fg_color=COULEUR_PRIMAIRE, corner_radius=8)
        entete.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(
            entete,
            text="📋  Journal d'audit — Opérations enregistrées par @journaliser",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=15, pady=10)

        # KPIs dans l'en-tête
        self._lbl_kpi = ctk.CTkLabel(
            entete, text="", font=ctk.CTkFont(size=11), text_color="#A9CCE3"
        )
        self._lbl_kpi.pack(side="right", padx=15)

        # Barre de contrôles
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=10, pady=4)

        ctk.CTkButton(
            barre, text="🔄 Rafraîchir", command=self.rafraichir,
            fg_color="#2196F3", hover_color="#1565C0", width=140,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            barre, text="🗑 Effacer journal",
            command=self._effacer,
            fg_color="#757575", hover_color="#424242", width=150,
        ).pack(side="left")

        # Filtre
        ctk.CTkLabel(barre, text="Afficher :", font=ctk.CTkFont(size=11)).pack(side="right", padx=(0, 4))
        self._var_filtre = ctk.StringVar(value="Toutes")
        ctk.CTkOptionMenu(
            barre,
            values=["Toutes", "Erreurs seulement"],
            variable=self._var_filtre,
            command=lambda _: self.rafraichir(),
            width=170,
        ).pack(side="right", padx=(0, 8))

        # Tableau
        frame_tree = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        frame_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        colonnes = ("icone", "heure", "operation", "ref", "details", "duree", "erreur")
        self._arbre = ttk.Treeview(
            frame_tree, columns=colonnes, show="headings", height=16
        )
        self._arbre.heading("icone",     text="")
        self._arbre.heading("heure",     text="Heure")
        self._arbre.heading("operation", text="Opération")
        self._arbre.heading("ref",       text="Réf produit")
        self._arbre.heading("details",   text="Détails")
        self._arbre.heading("duree",     text="Durée")
        self._arbre.heading("erreur",    text="Message erreur")

        self._arbre.column("icone",     width=30,  anchor="center")
        self._arbre.column("heure",     width=75,  anchor="center")
        self._arbre.column("operation", width=120, anchor="center")
        self._arbre.column("ref",       width=90,  anchor="center")
        self._arbre.column("details",   width=200)
        self._arbre.column("duree",     width=70,  anchor="center")
        self._arbre.column("erreur",    width=220)

        # Style des lignes d'erreur
        self._arbre.tag_configure("erreur", foreground="#C0392B", background="#FDF2F2")
        self._arbre.tag_configure("succes", foreground="#1A5E20")

        scroll = ttk.Scrollbar(frame_tree, orient="vertical", command=self._arbre.yview)
        self._arbre.configure(yscrollcommand=scroll.set)
        self._arbre.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scroll.pack(side="right", fill="y", pady=4)

    # ── Polling ────────────────────────────────────────────────────────────

    def _demarrer_polling(self) -> None:
        """Rafraîchit le journal toutes les 2 secondes."""
        self._id_poll = self.after(2000, self._poll)

    def _poll(self) -> None:
        self.rafraichir()
        self._id_poll = self.after(2000, self._poll)

    # ── Mise à jour ────────────────────────────────────────────────────────

    def rafraichir(self) -> None:
        """Reconstruit le tableau depuis le JournalService."""
        journal = self._stock.journal
        filtre  = self._var_filtre.get()

        entrees = journal.get_erreurs() if filtre == "Erreurs seulement" \
                  else journal.get_recentes(200)

        # KPIs
        self._lbl_kpi.configure(
            text=f"{journal.nb_total} opération(s)  |  {journal.nb_erreurs} erreur(s)"
        )

        # Reconstruire le tableau
        for item in self._arbre.get_children():
            self._arbre.delete(item)

        for e in entrees:
            tag = "erreur" if not e.succes else "succes"
            self._arbre.insert("", "end", tags=(tag,), values=(
                e.icone(),
                e.heure_formatee(),
                e.label_operation(),
                e.ref,
                e.details[:60] + ("…" if len(e.details) > 60 else ""),
                f"{e.duree_ms} ms",
                e.erreur[:80] if e.erreur else "—",
            ))

    # ── Actions ────────────────────────────────────────────────────────────

    def _effacer(self) -> None:
        self._stock.journal.vider()
        for item in self._arbre.get_children():
            self._arbre.delete(item)

    def arreter_polling(self) -> None:
        if self._id_poll:
            self.after_cancel(self._id_poll)
            self._id_poll = None
