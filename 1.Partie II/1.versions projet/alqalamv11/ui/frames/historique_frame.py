# [V10 - SQLite] Onglet "🗄️ Historique" — consultation de l'historique complet des mouvements.
#
# FONCTIONNALITÉS :
#   - Filtres : type de mouvement, référence produit, plage de dates
#   - Treeview paginé (limite 200 lignes) avec coloration par type
#   - Tableau de bord : stats par type (nb mouvements, qté totale)
#   - Bouton export CSV de l'historique filtré
#   - Rafraîchissement automatique toutes les 10 s

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date, timedelta
import csv
from pathlib import Path

from config import COULEUR_PRIMAIRE, COULEUR_OK, COULEUR_ALERTE, COULEUR_FOND, COULEUR_ORANGE, EXPORTS_DIR


# Couleurs par type de mouvement (Treeview tags)
COULEURS_TYPE = {
    "entree"     : "#EAFAF1",   # vert pâle
    "sortie"     : "#FDECEA",   # rouge pâle
    "ajustement" : "#EBF5FB",   # bleu pâle
    "retour"     : "#FEF9E7",   # orange pâle
}
ICONES_TYPE = {
    "entree"     : "📦 Entrée",
    "sortie"     : "🛒 Sortie",
    "ajustement" : "🔧 Ajustement",
    "retour"     : "↩️ Retour",
}


class HistoriqueFrame(ctk.CTkFrame):
    """
    [V10] Onglet Historique — consultation SQLite de tous les mouvements.

    Démontre sqlite3 :
      - Requêtes SELECT avec filtres WHERE dynamiques
      - GROUP BY pour les statistiques par type
      - Paramètres ? (protection injection SQL)
      - row_factory = sqlite3.Row (accès par nom de colonne)
    """

    POLL_MS  = 10_000   # rafraîchissement auto toutes les 10 secondes
    LIMITE   = 200      # nombre maximum de lignes affichées

    COLONNES = [
        ("ID",       "id",       50,  "center"),
        ("Date",     "date",    145,  "center"),
        ("Type",     "type",    110,  "center"),
        ("Référence","ref",      90,  "center"),
        ("Produit",  "produit", 160,  "w"),
        ("Qté",      "qte",      55,  "center"),
        ("Note",     "note",    260,  "w"),
    ]

    def __init__(self, parent, stock_service):
        super().__init__(parent, fg_color=COULEUR_FOND)
        self._stock      = stock_service
        self._db         = stock_service.db
        self._polling_id = None

        self._construire()
        self._demarrer_polling()

    # ── Construction UI ────────────────────────────────────────────────────

    def _construire(self):
        ctk.CTkLabel(
            self, text="🗄️ Historique des mouvements — Base SQLite",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(pady=(10, 4))

        # Zone filtres
        self._construire_filtres()

        # Stats KPIs
        self._construire_stats()

        # Tableau
        self._construire_tableau()

        # Barre de statut
        self._lbl_statut = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        )
        self._lbl_statut.pack(pady=(2, 4))

    def _construire_filtres(self):
        frame = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        frame.pack(fill="x", padx=12, pady=(0, 6))

        # Ligne 1 : filtres
        ligne = ctk.CTkFrame(frame, fg_color="transparent")
        ligne.pack(fill="x", padx=12, pady=8)

        # Type
        ctk.CTkLabel(ligne, text="Type :", font=ctk.CTkFont(size=11)).pack(side="left")
        self._var_type = ctk.StringVar(value="Tous")
        ctk.CTkComboBox(
            ligne,
            values=["Tous", "📦 Entrée", "🛒 Sortie", "🔧 Ajustement", "↩️ Retour"],
            variable=self._var_type, width=130,
            command=lambda _: self.rafraichir(),
        ).pack(side="left", padx=(4, 16))

        # Référence
        ctk.CTkLabel(ligne, text="Référence :", font=ctk.CTkFont(size=11)).pack(side="left")
        self._var_ref = ctk.StringVar()
        refs_entry = ctk.CTkComboBox(
            ligne,
            values=[""],
            variable=self._var_ref, width=120,
            command=lambda _: self.rafraichir(),
        )
        refs_entry.pack(side="left", padx=(4, 16))
        self._combo_ref = refs_entry

        # Date début
        ctk.CTkLabel(ligne, text="Du :", font=ctk.CTkFont(size=11)).pack(side="left")
        self._var_date_debut = ctk.StringVar(
            value=(date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        )
        ctk.CTkEntry(
            ligne, textvariable=self._var_date_debut, width=100,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(4, 8))

        # Date fin
        ctk.CTkLabel(ligne, text="Au :", font=ctk.CTkFont(size=11)).pack(side="left")
        self._var_date_fin = ctk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ctk.CTkEntry(
            ligne, textvariable=self._var_date_fin, width=100,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(4, 16))

        # Boutons
        ctk.CTkButton(
            ligne, text="🔍 Filtrer", width=90,
            fg_color=COULEUR_PRIMAIRE,
            command=self.rafraichir,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            ligne, text="↺ Tout", width=80,
            fg_color="#7F8C8D",
            command=self._reinitialiser_filtres,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            ligne, text="💾 Export CSV", width=110,
            fg_color=COULEUR_OK,
            command=self._exporter_csv,
        ).pack(side="right", padx=4)

    def _construire_stats(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=(0, 4))

        self._cards: dict[str, ctk.CTkLabel] = {}
        configs = [
            ("entree",      "📦 Entrées",     COULEUR_OK),
            ("sortie",      "🛒 Sorties",     COULEUR_ALERTE),
            ("ajustement",  "🔧 Ajustements", "#2E86C1"),
            ("retour",      "↩️ Retours",     COULEUR_ORANGE),
            ("total",       "🗄️ Total",       COULEUR_PRIMAIRE),
        ]
        for cle, label, couleur in configs:
            card = ctk.CTkFrame(frame, fg_color="white", corner_radius=8)
            card.pack(side="left", expand=True, fill="x", padx=4)
            ctk.CTkLabel(
                card, text=label,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=couleur,
            ).pack(pady=(6, 0))
            lbl_val = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=couleur,
            )
            lbl_val.pack(pady=(0, 6))
            self._cards[cle] = lbl_val

    def _construire_tableau(self):
        frame = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        # Style Treeview
        style = ttk.Style()
        style.configure("Historique.Treeview",
                         rowheight=22, font=("Calibri", 10))
        style.configure("Historique.Treeview.Heading",
                         font=("Calibri", 10, "bold"))

        self._tree = ttk.Treeview(
            frame,
            columns=[c[0] for c in self.COLONNES],
            show="headings", height=20,
            style="Historique.Treeview",
        )
        # En-têtes et largeurs
        for label, _cle, width, anchor in self.COLONNES:
            self._tree.heading(label, text=label)
            self._tree.column(label, width=width, minwidth=40, anchor=anchor)

        # Tags de couleur par type
        for type_mvt, couleur in COULEURS_TYPE.items():
            self._tree.tag_configure(type_mvt, background=couleur)

        # Scrollbars
        sb_v = ttk.Scrollbar(frame, orient="vertical",   command=self._tree.yview)
        sb_h = ttk.Scrollbar(frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=sb_v.set, xscrollcommand=sb_h.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        sb_v.grid(row=0, column=1, sticky="ns")
        sb_h.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    # ── Données ────────────────────────────────────────────────────────────

    def rafraichir(self):
        """Recharge les mouvements depuis SQLite selon les filtres actifs."""
        # Lire les filtres
        type_choisi = self._var_type.get()
        type_mvt    = None
        if type_choisi != "Tous":
            # Extraire le code depuis le label "📦 Entrée" → "entree"
            mapping = {v: k for k, v in ICONES_TYPE.items()}
            type_mvt = mapping.get(type_choisi)

        ref        = self._var_ref.get().strip() or None
        date_debut = self._var_date_debut.get().strip() or None
        date_fin   = self._var_date_fin.get().strip() or None

        # Requête SQLite via DatabaseService
        mouvements = self._db.charger_mouvements(
            type_mvt=type_mvt,
            ref=ref,
            date_debut=date_debut,
            date_fin=date_fin,
            limite=self.LIMITE,
        )

        # Mettre à jour le Treeview
        self._tree.delete(*self._tree.get_children())
        for m in mouvements:
            date_affichage = m["date"][:16].replace("T", " ")
            type_label     = ICONES_TYPE.get(m["type_mvt"], m["type_mvt"])
            valeurs = (
                m["id"], date_affichage, type_label,
                m["ref"], m["produit"], m["qte"], m["note"] or "—",
            )
            self._tree.insert(
                "", "end", values=valeurs,
                tags=(m["type_mvt"],),
            )

        # Mettre à jour les stats (depuis DB, indépendant des filtres)
        self._mettre_a_jour_stats()

        # Mettre à jour la liste des refs dans le combobox
        refs = [""] + self._db.refs_distinctes()
        self._combo_ref.configure(values=refs)

        # Statut
        nb    = len(mouvements)
        total = self._db.nb_mouvements()
        self._lbl_statut.configure(
            text=f"{nb} mouvement(s) affiché(s) sur {total} en base"
            + (" (limite atteinte)" if nb >= self.LIMITE else "")
        )

    def _mettre_a_jour_stats(self):
        """Met à jour les cartes KPI avec les stats globales de la base."""
        stats = self._db.stats_mouvements()
        total_nb = 0
        for type_mvt in ("entree", "sortie", "ajustement", "retour"):
            s  = stats.get(type_mvt, {"nb": 0, "qte_totale": 0})
            nb = s["nb"]
            qt = s["qte_totale"]
            total_nb += nb
            self._cards[type_mvt].configure(text=f"{nb} mvt · {qt} u.")
        self._cards["total"].configure(text=f"{total_nb} mouvements")

    def _reinitialiser_filtres(self):
        """Remet les filtres à leur valeur par défaut et rafraîchit."""
        self._var_type.set("Tous")
        self._var_ref.set("")
        self._var_date_debut.set((date.today() - timedelta(days=30)).strftime("%Y-%m-%d"))
        self._var_date_fin.set(date.today().strftime("%Y-%m-%d"))
        self.rafraichir()

    # ── Export CSV ─────────────────────────────────────────────────────────

    def _exporter_csv(self):
        """Exporte les mouvements actuellement affichés en CSV."""
        chemin = filedialog.asksaveasfilename(
            title="Exporter l'historique en CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialdir=str(EXPORTS_DIR),
            initialfile=f"historique_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not chemin:
            return

        # Re-lire les données filtrées pour l'export
        type_choisi = self._var_type.get()
        mapping     = {v: k for k, v in ICONES_TYPE.items()}
        type_mvt    = None if type_choisi == "Tous" else mapping.get(type_choisi)
        ref         = self._var_ref.get().strip() or None
        date_debut  = self._var_date_debut.get().strip() or None
        date_fin    = self._var_date_fin.get().strip() or None

        mouvements = self._db.charger_mouvements(
            type_mvt=type_mvt, ref=ref,
            date_debut=date_debut, date_fin=date_fin,
        )
        Path(chemin).parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["id", "date", "type_mvt", "ref", "produit", "qte", "note"],
                )
                writer.writeheader()
                writer.writerows(mouvements)

            messagebox.showinfo(
                "Export réussi",
                f"✅ {len(mouvements)} mouvements exportés\n{Path(chemin).name}"
            )
        except Exception as e:
            messagebox.showerror("Erreur export", str(e))

    # ── Polling ────────────────────────────────────────────────────────────

    def _demarrer_polling(self):
        self.rafraichir()
        self._polling_id = self.after(self.POLL_MS, self._demarrer_polling)

    def arreter_polling(self):
        if self._polling_id:
            self.after_cancel(self._polling_id)
            self._polling_id = None
