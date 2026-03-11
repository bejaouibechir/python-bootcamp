# [V9 - Excel] Onglet "📊 Excel" — export rapport coloré + import bon de commande.
#
# FONCTIONNALITÉS :
#   Section Export :
#     - Bouton "Rapport stock coloré" → ExcelService.exporter_rapport_stock()
#       Génère un classeur 3 feuilles : Catalogue, Ruptures, Statistiques
#     - Label de statut + log des exports
#
#   Section Import :
#     - Bouton "Parcourir" → filedialog pour choisir un .xlsx
#     - Prévisualisation : noms de feuilles + aperçu données
#     - Bouton "Importer bon de commande" → ExcelService.importer_bon_commande()
#     - Rapport : nb traités, total qte, erreurs

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from pathlib  import Path
from datetime import datetime
import subprocess
import sys

from config import (
    COULEUR_PRIMAIRE, COULEUR_OK, COULEUR_ALERTE,
    COULEUR_FOND, COULEUR_ORANGE, EXCEL_DIR,
)
from services.excel_service import ExcelService, ErreurExcel


class ExcelFrame(ctk.CTkFrame):
    """
    [V9] Onglet Excel — rapport de stock colorisé multi-feuilles + import bon de commande.

    Démontre openpyxl :
      - Workbook multi-feuilles avec styles professionnels
      - PatternFill pour colorisation conditionnelle
      - Font / Alignment / Border pour mise en forme
      - BarChart pour graphique de statistiques
      - load_workbook pour lecture d'un bon de commande
    """

    POLL_MS = 5_000

    def __init__(self, parent, stock_service):
        super().__init__(parent, fg_color=COULEUR_FOND)
        self._stock     = stock_service
        self._excel_svc = ExcelService(stock_service)
        self._chemin_import: Path | None = None
        self._dernier_export: Path | None = None
        self._polling_id = None

        self._construire()
        self._demarrer_polling()

    # ── Construction UI ────────────────────────────────────────────────────

    def _construire(self):
        ctk.CTkLabel(
            self, text="📊 Gestion Excel — Rapport & Bon de commande",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(pady=(10, 4))

        corps = ctk.CTkFrame(self, fg_color="transparent")
        corps.pack(fill="both", expand=True, padx=12, pady=6)
        corps.columnconfigure(0, weight=2)
        corps.columnconfigure(1, weight=3)
        corps.rowconfigure(0, weight=1)

        self._construire_section_export(corps)
        self._construire_section_import(corps)

    def _construire_section_export(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(
            frame, text="📤 Export rapport de stock",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(pady=(12, 4))

        # Légende colorisation
        legende = ctk.CTkFrame(frame, fg_color="#F8F9FA", corner_radius=6)
        legende.pack(fill="x", padx=16, pady=(4, 8))
        ctk.CTkLabel(
            legende, text="Colorisation du rapport Excel :",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#555",
        ).pack(anchor="w", padx=8, pady=(6, 2))
        for texte, couleur in [
            ("🟥  Rouge pâle  — Rupture totale (stock = 0)", "#E74C3C"),
            ("🟧  Orange pâle — Alerte (0 < stock ≤ seuil)", "#E67E22"),
            ("🟩  Vert pâle   — Normal (stock > seuil)", "#27AE60"),
        ]:
            ctk.CTkLabel(
                legende, text=texte,
                font=ctk.CTkFont(size=10), text_color=couleur,
            ).pack(anchor="w", padx=12)
        ctk.CTkFrame(legende, height=4, fg_color="transparent").pack()

        ctk.CTkLabel(
            frame, text="3 feuilles générées : Catalogue · Ruptures · Statistiques",
            font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        ).pack()

        ctk.CTkButton(
            frame, text="📊 Générer rapport Excel",
            fg_color=COULEUR_PRIMAIRE, font=ctk.CTkFont(size=13, weight="bold"),
            height=40, command=self._exporter_rapport,
        ).pack(pady=12, padx=20)

        self._btn_ouvrir = ctk.CTkButton(
            frame, text="📂 Ouvrir le dernier rapport",
            fg_color="#7F8C8D", state="disabled",
            command=self._ouvrir_dernier_rapport,
        )
        self._btn_ouvrir.pack(pady=(0, 8), padx=20)

        ctk.CTkFrame(frame, height=1, fg_color="#E0E0E0").pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(
            frame, text="Exports générés :",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=COULEUR_PRIMAIRE,
        ).pack(anchor="w", padx=16)

        self._txt_exports = ctk.CTkTextbox(
            frame, height=150, font=ctk.CTkFont(size=10),
            fg_color="#F0F4F8", state="disabled",
        )
        self._txt_exports.pack(fill="both", expand=True, padx=12, pady=(4, 8))

        self._lbl_stats = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        )
        self._lbl_stats.pack(pady=(0, 8))

    def _construire_section_import(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            frame, text="📂 Import bon de commande (.xlsx)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            frame,
            text="Format attendu : colonnes 'ref' et 'qte' (+ 'note' optionnelle) en ligne 1",
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

        # Infos feuilles
        self._lbl_feuilles = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        )
        self._lbl_feuilles.pack(anchor="w", padx=16)

        # Prévisualisation
        frame_tree = ctk.CTkFrame(frame, fg_color="#F8F9FA", corner_radius=6)
        frame_tree.pack(fill="both", expand=True, padx=12, pady=4)

        ctk.CTkLabel(
            frame_tree, text="Prévisualisation (5 premières lignes)",
            font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        ).pack(anchor="w", padx=6, pady=(4, 0))

        self._tree_prev = ttk.Treeview(
            frame_tree, show="headings", height=6, selectmode="none",
        )
        scroll_x = ttk.Scrollbar(frame_tree, orient="horizontal",
                                  command=self._tree_prev.xview)
        self._tree_prev.configure(xscrollcommand=scroll_x.set)
        self._tree_prev.pack(fill="both", expand=True, padx=4, pady=2)
        scroll_x.pack(fill="x", padx=4)

        # Zone rapport
        self._txt_rapport = ctk.CTkTextbox(
            frame, height=90, font=ctk.CTkFont(size=11),
            fg_color="#F0F4F8", state="disabled",
        )
        self._txt_rapport.pack(fill="x", padx=12, pady=4)

        self._btn_importer = ctk.CTkButton(
            frame, text="⬇️ Importer le bon de commande",
            fg_color=COULEUR_PRIMAIRE,
            command=self._importer_bon_commande,
            state="disabled",
        )
        self._btn_importer.pack(pady=(4, 12), padx=12)

    # ── Actions Export ─────────────────────────────────────────────────────

    def _exporter_rapport(self):
        chemin = filedialog.asksaveasfilename(
            title="Enregistrer le rapport Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialdir=str(EXCEL_DIR),
            initialfile=f"rapport_stock_{datetime.now().strftime('%Y%m%d')}.xlsx",
        )
        if not chemin:
            return
        try:
            chemin_cree = self._excel_svc.exporter_rapport_stock(chemin)
            self._dernier_export = chemin_cree
            self._btn_ouvrir.configure(state="normal", fg_color=COULEUR_OK)
            self._log_export(
                f"✅ Rapport : {Path(chemin).name}\n"
                f"   Feuilles : Catalogue · Ruptures · Statistiques"
            )
            messagebox.showinfo(
                "Rapport Excel généré",
                f"✅ Rapport généré avec succès !\n\n"
                f"Fichier : {Path(chemin).name}\n"
                f"3 feuilles : Catalogue, Ruptures, Statistiques"
            )
        except Exception as e:
            messagebox.showerror("Erreur export Excel", str(e))

    def _ouvrir_dernier_rapport(self):
        """Ouvre le dernier fichier Excel généré avec l'application par défaut du système."""
        if self._dernier_export and self._dernier_export.exists():
            if sys.platform == "win32":
                import os
                os.startfile(str(self._dernier_export))
            else:
                subprocess.run(["xdg-open", str(self._dernier_export)])
        else:
            messagebox.showwarning("Fichier introuvable", "Le fichier n'existe plus.")

    def _log_export(self, message: str):
        horodatage = datetime.now().strftime("%H:%M:%S")
        self._txt_exports.configure(state="normal")
        self._txt_exports.insert("end", f"[{horodatage}] {message}\n")
        self._txt_exports.see("end")
        self._txt_exports.configure(state="disabled")

    # ── Actions Import ─────────────────────────────────────────────────────

    def _parcourir_fichier(self):
        chemin = filedialog.askopenfilename(
            title="Choisir un bon de commande Excel",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Tous les fichiers", "*.*")],
            initialdir=str(EXCEL_DIR),
        )
        if not chemin:
            return

        self._chemin_import = Path(chemin)
        self._var_chemin.set(str(self._chemin_import))

        apercu = self._excel_svc.previsualiser_excel(self._chemin_import, nb_lignes=5)
        self._afficher_previsualisation(apercu)

        if apercu["feuilles"]:
            self._lbl_feuilles.configure(
                text=f"Feuilles détectées : {', '.join(apercu['feuilles'])} "
                     f"({apercu['nb_feuilles']} feuille(s))"
            )

        if apercu["valide"]:
            self._btn_importer.configure(state="normal", fg_color=COULEUR_OK)
            self._ecrire_rapport(
                "✅ Structure valide — colonnes 'ref' et 'qte' trouvées.\n"
                f"   Colonnes : {', '.join(apercu['colonnes'])}"
            )
        else:
            self._btn_importer.configure(state="disabled", fg_color=COULEUR_ALERTE)
            self._ecrire_rapport(
                "❌ Structure invalide — colonnes 'ref' et 'qte' requises.\n"
                f"   Colonnes détectées : {', '.join(apercu['colonnes']) or '(aucune)'}"
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
            self._tree_prev.insert("", "end", values=ligne)

    def _importer_bon_commande(self):
        if not self._chemin_import:
            return
        try:
            rapport = self._excel_svc.importer_bon_commande(self._chemin_import)
            texte = (
                f"✅ Import terminé !\n"
                f"   Lignes lues    : {rapport['total_lues']}\n"
                f"   Traités        : {rapport['traites']} réceptions enregistrées\n"
                f"   Total qté      : {rapport['total_qte']} unités réceptionnées\n"
                f"   Erreurs        : {len(rapport['erreurs'])}"
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
                "Import bon de commande",
                f"Import terminé !\n"
                f"{rapport['traites']} réceptions | {rapport['total_qte']} unités"
            )
        except FileNotFoundError as e:
            messagebox.showerror("Fichier introuvable", str(e))
        except ErreurExcel as e:
            messagebox.showerror("Erreur structure Excel", str(e))
            self._ecrire_rapport(f"❌ Erreur : {e}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur inattendue :\n{e}")

    def _ecrire_rapport(self, texte: str):
        self._txt_rapport.configure(state="normal")
        self._txt_rapport.delete("1.0", "end")
        self._txt_rapport.insert("end", texte)
        self._txt_rapport.configure(state="disabled")

    # ── Rafraîchissement ───────────────────────────────────────────────────

    def rafraichir(self):
        nb      = self._stock.nb_produits()
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
