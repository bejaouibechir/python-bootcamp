# [V8 - CSV] Onglet "📥 CSV" — import/export de fichiers CSV.
#
# FONCTIONNALITÉS :
#   Section Import :
#     - Bouton "Parcourir" → ouvre tkinter.filedialog pour choisir un CSV
#     - Zone de prévisualisation → affiche les 5 premières lignes en Treeview
#     - Bouton "Importer" → lance CsvService.importer_catalogue()
#     - Rapport : nb importés, mis à jour, erreurs
#
#   Section Export :
#     - Bouton "Exporter catalogue"  → CsvService.exporter_catalogue()
#     - Bouton "Exporter mouvements" → CsvService.exporter_mouvements()
#     - Bouton "Rapport comptable"   → CsvService.exporter_comptabilite()

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from pathlib  import Path
from datetime import datetime

from config import (
    COULEUR_PRIMAIRE, COULEUR_OK, COULEUR_ALERTE,
    COULEUR_FOND, COULEUR_ORANGE, CSV_DIR
)
from services.csv_service import CsvService, ErreurCsv


class CsvFrame(ctk.CTkFrame):
    """
    [V8] Onglet CSV — import catalogue fournisseur + exports comptabilité.

    Démontre :
      - csv.DictReader  pour import avec validation de colonnes
      - csv.DictWriter  pour exports formatés
      - encoding="utf-8-sig" pour compatibilité Excel
      - newline="" obligatoire à l'écriture sous Windows
      - Prévisualisation avant import (bonne pratique UX)
    """

    POLL_MS = 5_000

    def __init__(self, parent, stock_service):
        super().__init__(parent, fg_color=COULEUR_FOND)
        self._stock   = stock_service
        self._csv_svc = CsvService(stock_service)
        self._chemin_import: Path | None = None
        self._polling_id = None

        self._construire()
        self._demarrer_polling()

    # ── Construction UI ────────────────────────────────────────────────────

    def _construire(self):
        ctk.CTkLabel(
            self, text="📥 Gestion CSV — Import / Export",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(pady=(10, 4))

        corps = ctk.CTkFrame(self, fg_color="transparent")
        corps.pack(fill="both", expand=True, padx=12, pady=6)
        corps.columnconfigure(0, weight=3)
        corps.columnconfigure(1, weight=2)
        corps.rowconfigure(0, weight=1)

        self._construire_section_import(corps)
        self._construire_section_export(corps)

    def _construire_section_import(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(
            frame, text="📂 Import catalogue fournisseur",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            frame,
            text="Format attendu : ref, nom, categorie, prix_achat, prix_vente, seuil_min",
            font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        ).pack()

        barre = ctk.CTkFrame(frame, fg_color="transparent")
        barre.pack(fill="x", padx=12, pady=(8, 4))

        self._var_chemin = ctk.StringVar(value="Aucun fichier sélectionné")
        ctk.CTkEntry(
            barre, textvariable=self._var_chemin,
            state="readonly", font=ctk.CTkFont(size=11),
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            barre, text="📁 Parcourir", width=100,
            command=self._parcourir_fichier,
        ).pack(side="right")

        frame_tree = ctk.CTkFrame(frame, fg_color="#F8F9FA", corner_radius=6)
        frame_tree.pack(fill="both", expand=True, padx=12, pady=4)

        ctk.CTkLabel(
            frame_tree, text="Prévisualisation (5 premières lignes)",
            font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        ).pack(anchor="w", padx=6, pady=(4, 0))

        self._tree_prev = ttk.Treeview(
            frame_tree, show="headings", height=5,
            selectmode="none",
        )
        scroll_x = ttk.Scrollbar(frame_tree, orient="horizontal",
                                  command=self._tree_prev.xview)
        self._tree_prev.configure(xscrollcommand=scroll_x.set)
        self._tree_prev.pack(fill="both", expand=True, padx=4, pady=2)
        scroll_x.pack(fill="x", padx=4)

        self._txt_rapport = ctk.CTkTextbox(
            frame, height=80, font=ctk.CTkFont(size=11),
            fg_color="#F0F4F8", state="disabled",
        )
        self._txt_rapport.pack(fill="x", padx=12, pady=4)

        self._btn_importer = ctk.CTkButton(
            frame, text="⬇️ Importer dans le stock",
            fg_color=COULEUR_PRIMAIRE,
            command=self._importer,
            state="disabled",
        )
        self._btn_importer.pack(pady=(4, 12), padx=12)

    def _construire_section_export(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            frame, text="📤 Exports CSV",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(pady=(12, 8))

        exports = [
            ("📦 Catalogue produits",    self._exporter_catalogue,    COULEUR_PRIMAIRE),
            ("🔄 Historique mouvements", self._exporter_mouvements,   COULEUR_ORANGE),
            ("💰 Rapport comptable",     self._exporter_comptabilite, COULEUR_OK),
        ]
        for label, cmd, couleur in exports:
            ctk.CTkButton(
                frame, text=label, fg_color=couleur,
                command=cmd, width=220,
            ).pack(pady=6, padx=20)

        # Séparateur manuel (CTkSeparator n'existe pas dans customtkinter)
        ctk.CTkFrame(frame, height=1, fg_color="#E0E0E0").pack(
            fill="x", padx=16, pady=8
        )

        ctk.CTkLabel(
            frame, text="Fichiers exportés :",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(anchor="w", padx=16)

        self._txt_exports = ctk.CTkTextbox(
            frame, height=180, font=ctk.CTkFont(size=10),
            fg_color="#F0F4F8", state="disabled",
        )
        self._txt_exports.pack(fill="both", expand=True, padx=12, pady=(4, 8))

        self._lbl_stats = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=10),
            text_color="#7F8C8D",
        )
        self._lbl_stats.pack(pady=(0, 8))

    # ── Actions Import ─────────────────────────────────────────────────────

    def _parcourir_fichier(self):
        chemin = filedialog.askopenfilename(
            title="Choisir un catalogue CSV fournisseur",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            initialdir=str(CSV_DIR),
        )
        if not chemin:
            return

        self._chemin_import = Path(chemin)
        self._var_chemin.set(str(self._chemin_import))

        apercu = self._csv_svc.previsualiser_csv(self._chemin_import, nb_lignes=5)
        self._afficher_previsualisation(apercu)

        if apercu["valide"]:
            self._btn_importer.configure(state="normal", fg_color=COULEUR_OK)
            self._ecrire_rapport(
                "✅ Structure valide — colonnes requises présentes.\n"
                f"   Colonnes : {', '.join(apercu['colonnes'])}"
            )
        else:
            self._btn_importer.configure(state="disabled", fg_color=COULEUR_ALERTE)
            self._ecrire_rapport(
                "❌ Structure invalide.\n"
                f"   Colonnes présentes : {', '.join(apercu['colonnes'])}\n"
                "   Colonnes requises  : ref, nom, categorie, prix_achat, prix_vente, seuil_min"
            )

    def _afficher_previsualisation(self, apercu: dict):
        self._tree_prev.delete(*self._tree_prev.get_children())
        colonnes = apercu["colonnes"]
        if not colonnes:
            return

        self._tree_prev["columns"] = colonnes
        for col in colonnes:
            self._tree_prev.heading(col, text=col)
            self._tree_prev.column(col, width=100, minwidth=60, anchor="center")

        for ligne in apercu["lignes"]:
            valeurs = [ligne.get(col, "") for col in colonnes]
            self._tree_prev.insert("", "end", values=valeurs)

    def _importer(self):
        if not self._chemin_import:
            return
        try:
            rapport = self._csv_svc.importer_catalogue(self._chemin_import)
            texte = (
                f"✅ Import terminé !\n"
                f"   Lignes lues   : {rapport['total_lues']}\n"
                f"   Importés      : {rapport['importes']} nouveaux produits\n"
                f"   Mis à jour    : {rapport['mis_a_jour']} produits existants\n"
                f"   Erreurs       : {len(rapport['erreurs'])}"
            )
            if rapport["erreurs"]:
                texte += "\n\nDétail des erreurs :"
                for err in rapport["erreurs"][:5]:
                    texte += f"\n  • {err}"
                if len(rapport["erreurs"]) > 5:
                    texte += f"\n  ... et {len(rapport['erreurs'])-5} autre(s)"

            self._ecrire_rapport(texte)
            self.rafraichir()
            messagebox.showinfo(
                "Import CSV",
                f"Import terminé !\n{rapport['importes']} importés | {rapport['mis_a_jour']} mis à jour"
            )

        except FileNotFoundError as e:
            messagebox.showerror("Fichier introuvable", str(e))
        except ErreurCsv as e:
            messagebox.showerror("Erreur structure CSV", str(e))
            self._ecrire_rapport(f"❌ Erreur : {e}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur inattendue :\n{e}")

    def _ecrire_rapport(self, texte: str):
        self._txt_rapport.configure(state="normal")
        self._txt_rapport.delete("1.0", "end")
        self._txt_rapport.insert("end", texte)
        self._txt_rapport.configure(state="disabled")

    # ── Actions Export ─────────────────────────────────────────────────────

    def _exporter_catalogue(self):
        chemin = filedialog.asksaveasfilename(
            title="Exporter catalogue",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialdir=str(CSV_DIR),
            initialfile="catalogue.csv",
        )
        if not chemin:
            return
        try:
            nb = self._csv_svc.exporter_catalogue(chemin)
            self._log_export(f"✅ Catalogue : {Path(chemin).name} ({nb} produits)")
            messagebox.showinfo("Export catalogue", f"✅ {nb} produits exportés.")
        except Exception as e:
            messagebox.showerror("Erreur export", str(e))

    def _exporter_mouvements(self):
        chemin = filedialog.asksaveasfilename(
            title="Exporter mouvements",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialdir=str(CSV_DIR),
            initialfile="mouvements.csv",
        )
        if not chemin:
            return
        try:
            nb = self._csv_svc.exporter_mouvements(chemin)
            self._log_export(f"✅ Mouvements : {Path(chemin).name} ({nb} lignes)")
            messagebox.showinfo("Export mouvements", f"✅ {nb} mouvements exportés.")
        except Exception as e:
            messagebox.showerror("Erreur export", str(e))

    def _exporter_comptabilite(self):
        chemin = filedialog.asksaveasfilename(
            title="Rapport comptable",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialdir=str(CSV_DIR),
            initialfile="comptabilite.csv",
        )
        if not chemin:
            return
        try:
            nb = self._csv_svc.exporter_comptabilite(chemin)
            self._log_export(f"✅ Comptabilité : {Path(chemin).name} ({nb} lignes)")
            messagebox.showinfo("Rapport comptable", f"✅ Rapport de {nb} produits exporté.")
        except Exception as e:
            messagebox.showerror("Erreur export", str(e))

    def _log_export(self, message: str):
        horodatage = datetime.now().strftime("%H:%M:%S")
        self._txt_exports.configure(state="normal")
        self._txt_exports.insert("end", f"[{horodatage}] {message}\n")
        self._txt_exports.see("end")
        self._txt_exports.configure(state="disabled")

    # ── Rafraîchissement ───────────────────────────────────────────────────

    def rafraichir(self):
        nb = self._stock.nb_produits()
        alertes = self._stock.nb_alertes()
        self._lbl_stats.configure(
            text=f"Stock courant : {nb} produits | {alertes} alerte(s)"
        )

    def _demarrer_polling(self):
        self.rafraichir()
        self._polling_id = self.after(self.POLL_MS, self._demarrer_polling)

    def arreter_polling(self):
        if self._polling_id:
            self.after_cancel(self._polling_id)
            self._polling_id = None
