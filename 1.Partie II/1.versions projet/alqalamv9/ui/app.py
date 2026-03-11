# [V9 - Excel] Fenêtre principale avec huit onglets :
# - "📦 Stock"             : tableau produits + filtres + recherche
# - "📊 Tableau de bord"   : KPIs + stats catégories + top 5
# - "🔔 Alertes"           : surveillance temps réel (thread daemon) [V4]
# - "📋 Journal"           : historique d'audit des opérations décorées [V5]
# - "🗂 Registre"          : registre métaclasses + démo Singleton      [V6]
# - "🔍 Analyseur"         : parsing du journal par regex               [V7]
# - "📥 CSV"               : import catalogue fournisseur + exports CSV  [V8] NEW
# - "📊 Excel"             : rapport coloré multi-feuilles + import bon de commande [V9] NEW
#
# NOUVEAUTÉS V8 dans app.py :
#   - 7ème onglet CsvFrame (import/export CSV)
#   - CsvService : csv.DictReader/DictWriter, encoding utf-8-sig, newline=""

import customtkinter as ctk
from tkinter import messagebox

from config import (
    APP_NAME, APP_VERSION, APP_WIDTH, APP_HEIGHT,
    COULEUR_PRIMAIRE, INTERVALLE_SURVEILLANCE
)
from services.stock_service        import StockService
from services.surveillance_service import SurveillanceService
from ui.frames.stock_frame         import StockFrame
from ui.frames.rapport_frame       import RapportFrame
from ui.frames.alertes_frame       import AlertesFrame
from ui.frames.journal_frame       import JournalFrame
from ui.frames.registre_frame      import RegistreFrame
from ui.frames.analyseur_frame     import AnalyseurFrame      # [V7]
from ui.frames.csv_frame           import CsvFrame            # [V8]
from ui.frames.excel_frame         import ExcelFrame           # [V9]
from ui.frames.dialogs             import (
    DialogueProduit, DialogueMouvement, DialogueAjustement,
    DialogueFicheDetail, DialogueModification
)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class AlQalamApp(ctk.CTk):
    """Fenêtre principale V9 — 8 onglets, Excel Export/Import actif."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  —  v{APP_VERSION}")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(1000, 680)

        x = (self.winfo_screenwidth()  - APP_WIDTH)  // 2
        y = (self.winfo_screenheight() - APP_HEIGHT) // 2
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}+{x}+{y}")

        self.stock        = StockService()
        self.surveillance = SurveillanceService(
            self.stock, intervalle=INTERVALLE_SURVEILLANCE
        )

        self._construire_entete()
        self._construire_onglets()
        self._construire_pied()
        self.protocol("WM_DELETE_WINDOW", self._quitter)
        self.after(100, self._demarrer_surveillance)

    # ── Construction ───────────────────────────────────────────────────────

    def _construire_entete(self):
        entete = ctk.CTkFrame(self, fg_color=COULEUR_PRIMAIRE, height=55, corner_radius=0)
        entete.pack(fill="x")
        entete.pack_propagate(False)
        ctk.CTkLabel(
            entete, text="📚  Al Qalam — Gestion de Stock",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=20)
        ctk.CTkLabel(
            entete, text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color="#A9CCE3",
        ).pack(side="right", padx=20)

    def _construire_onglets(self):
        """[V9] Huit onglets : Stock, Tableau de bord, Alertes, Journal, Registre, Analyseur, CSV, Excel."""
        self.tabs = ctk.CTkTabview(
            self, anchor="nw",
            segmented_button_selected_color=COULEUR_PRIMAIRE,
            segmented_button_selected_hover_color="#163D61",
        )
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(6, 0))

        self.tabs.add("📦 Stock")
        self.tabs.add("📊 Tableau de bord")
        self.tabs.add("🔔 Alertes")
        self.tabs.add("📋 Journal")
        self.tabs.add("🗂 Registre")
        self.tabs.add("🔍 Analyseur")    # [V7]
        self.tabs.add("📥 CSV")          # [V8]
        self.tabs.add("📊 Excel")        # [V9]

        callbacks = {
            "nouveau"   : self._ouvrir_dialogue_nouveau,
            "entree"    : self._ouvrir_dialogue_entree,
            "sortie"    : self._ouvrir_dialogue_sortie,
            "modifier"  : self._ouvrir_dialogue_modifier,
            "supprimer" : self._supprimer_produit,
            "detail"    : self._ouvrir_fiche_detail,
            "ajuster"   : self._ouvrir_dialogue_ajustement,
            "retour"    : self._ouvrir_dialogue_retour,
        }
        self.stock_frame = StockFrame(self.tabs.tab("📦 Stock"), self.stock, callbacks)
        self.stock_frame.pack(fill="both", expand=True)

        self.rapport_frame = RapportFrame(self.tabs.tab("📊 Tableau de bord"), self.stock)
        self.rapport_frame.pack(fill="both", expand=True)

        self.alertes_frame = AlertesFrame(self.tabs.tab("🔔 Alertes"), self.surveillance)
        self.alertes_frame.pack(fill="both", expand=True)

        self.journal_frame = JournalFrame(self.tabs.tab("📋 Journal"), self.stock)
        self.journal_frame.pack(fill="both", expand=True)

        self.registre_frame = RegistreFrame(self.tabs.tab("🗂 Registre"), self.stock)
        self.registre_frame.pack(fill="both", expand=True)

        # [V7] Onglet Analyseur — log parser + regex
        self.analyseur_frame = AnalyseurFrame(self.tabs.tab("🔍 Analyseur"), self.stock)
        self.analyseur_frame.pack(fill="both", expand=True)

        # [V8] Onglet CSV — import catalogue fournisseur + exports comptabilité
        self.csv_frame = CsvFrame(self.tabs.tab("📥 CSV"), self.stock)
        self.csv_frame.pack(fill="both", expand=True)

        # [V9] Onglet Excel — rapport coloré multi-feuilles + import bon de commande
        self.excel_frame = ExcelFrame(self.tabs.tab("📊 Excel"), self.stock)
        self.excel_frame.pack(fill="both", expand=True)

    def _construire_pied(self):
        pied = ctk.CTkFrame(self, height=25, fg_color="#ECF0F1", corner_radius=0)
        pied.pack(fill="x", side="bottom")
        pied.pack_propagate(False)
        ctk.CTkLabel(
            pied,
            text="Al Qalam Stock Manager  |  Formation Python — Partie II  |  V9 Excel Rapport & Bon de commande",
            font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        ).pack(side="left", padx=15)

    # ── Threading (V4) ────────────────────────────────────────────────────

    def _demarrer_surveillance(self) -> None:
        self.surveillance.demarrer()

    # ── Helper post-opération ─────────────────────────────────────────────

    def _post_operation(self):
        """Rafraîchit les huit onglets après toute modification du stock."""
        self.stock_frame.rafraichir()
        self.rapport_frame.rafraichir()
        self.alertes_frame.rafraichir()
        self.journal_frame.rafraichir()
        self.registre_frame.rafraichir()
        self.analyseur_frame.rafraichir()   # [V7]
        self.csv_frame.rafraichir()         # [V8]
        self.excel_frame.rafraichir()       # [V9]

    # ── Dialogues ─────────────────────────────────────────────────────────

    def _ouvrir_dialogue_nouveau(self):
        dlg = DialogueProduit(self)
        self.wait_window(dlg)
        if dlg.resultat is not None:
            try:
                self.stock.ajouter_produit(dlg.resultat)
                self._post_operation()
                messagebox.showinfo("Produit ajouté", f"✅ '{dlg.resultat.nom}' ajouté.")
            except ValueError as e:
                messagebox.showerror("Erreur", str(e))

    def _ouvrir_dialogue_entree(self):
        ref     = self.stock_frame.get_ref_selectionnee()
        produit = self.stock.get_produit(ref) if ref else None
        dlg     = DialogueMouvement(self, self.stock, "entree", produit)
        self.wait_window(dlg)
        if dlg.resultat is not None:
            try:
                r = dlg.resultat
                self.stock.entree_stock(r["ref"], r["qte"], r["note"])
                self._post_operation()
                messagebox.showinfo("Entrée enregistrée", f"✅ +{r['qte']} pour '{r['ref']}'.")
            except (ValueError, KeyError) as e:
                messagebox.showerror("Erreur", str(e))

    def _ouvrir_dialogue_sortie(self):
        ref     = self.stock_frame.get_ref_selectionnee()
        produit = self.stock.get_produit(ref) if ref else None
        dlg     = DialogueMouvement(self, self.stock, "sortie", produit)
        self.wait_window(dlg)
        if dlg.resultat is not None:
            try:
                r = dlg.resultat
                self.stock.sortie_stock(r["ref"], r["qte"], r["note"])
                self._post_operation()
                messagebox.showinfo("Sortie enregistrée", f"✅ -{r['qte']} pour '{r['ref']}'.")
            except (ValueError, KeyError) as e:
                messagebox.showerror("Erreur", str(e))

    def _ouvrir_fiche_detail(self, ref: str):
        try:
            dlg = DialogueFicheDetail(self, self.stock.get_produit(ref))
            self.wait_window(dlg)
        except KeyError as e:
            messagebox.showerror("Erreur", str(e))

    def _ouvrir_dialogue_modifier(self):
        ref = self.stock_frame.get_ref_selectionnee()
        if not ref:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un produit d'abord.")
            return
        try:
            produit = self.stock.get_produit(ref)
        except KeyError as e:
            messagebox.showerror("Erreur", str(e))
            return
        dlg = DialogueModification(self, produit)
        self.wait_window(dlg)
        if dlg.resultat is not None:
            r = dlg.resultat
            produit_maj = produit.__class__(
                ref=r["ref"], nom=r["nom"], categorie=r["categorie"],
                prix_achat=r["prix_achat"], prix_vente=r["prix_vente"],
                qte=produit.qte, seuil_min=r["seuil_min"],
            )
            self.stock.mettre_a_jour_produit(produit_maj)
            self._post_operation()
            messagebox.showinfo("Modifié", f"✅ '{r['nom']}' mis à jour.")

    def _supprimer_produit(self):
        ref = self.stock_frame.get_ref_selectionnee()
        if not ref:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un produit d'abord.")
            return
        try:
            produit = self.stock.get_produit(ref)
        except KeyError as e:
            messagebox.showerror("Erreur", str(e))
            return
        if messagebox.askyesno("Confirmer", f"Supprimer '{produit.nom}' ?"):
            self.stock.supprimer_produit(ref)
            self._post_operation()
            messagebox.showinfo("Supprimé", f"✅ '{produit.nom}' supprimé.")

    def _ouvrir_dialogue_ajustement(self):
        ref = self.stock_frame.get_ref_selectionnee()
        if not ref:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un produit d'abord.")
            return
        try:
            produit = self.stock.get_produit(ref)
        except KeyError as e:
            messagebox.showerror("Erreur", str(e))
            return
        dlg = DialogueAjustement(self, produit)
        self.wait_window(dlg)
        if dlg.resultat is not None:
            r = dlg.resultat
            try:
                self.stock.ajustement_stock(r["ref"], r["qte_cible"], r["note"])
                self._post_operation()
                messagebox.showinfo(
                    "Ajustement effectué",
                    f"✅ Stock de '{produit.nom}' ajusté à {r['qte_cible']} unités."
                )
            except (ValueError, KeyError) as e:
                messagebox.showerror("Erreur", str(e))

    def _ouvrir_dialogue_retour(self):
        ref     = self.stock_frame.get_ref_selectionnee()
        produit = self.stock.get_produit(ref) if ref else None
        dlg     = DialogueMouvement(self, self.stock, "retour", produit)
        self.wait_window(dlg)
        if dlg.resultat is not None:
            try:
                r = dlg.resultat
                self.stock.retour_stock(r["ref"], r["qte"], r["note"])
                self._post_operation()
                messagebox.showinfo("Retour enregistré", f"✅ Retour de {r['qte']} '{r['ref']}'.")
            except (ValueError, KeyError) as e:
                messagebox.showerror("Erreur", str(e))

    # ── Quitter ───────────────────────────────────────────────────────────

    def _quitter(self):
        if messagebox.askyesno("Quitter", "Voulez-vous quitter Al Qalam ?"):
            self.alertes_frame.arreter_polling()
            self.journal_frame.arreter_polling()
            self.registre_frame.arreter_polling()
            self.analyseur_frame.arreter_polling()   # [V7]
            self.csv_frame.arreter_polling()         # [V8]
            self.excel_frame.arreter_polling()       # [V9]
            self.surveillance.arreter()
            self.destroy()
