# [V3 - Compréhensions] Fenêtre principale avec deux onglets :
# - "Stock"          : tableau produits + filtres + recherche
# - "Tableau de bord": KPIs + stats catégories + top 5

import customtkinter as ctk
from tkinter import messagebox

from config import APP_NAME, APP_VERSION, APP_WIDTH, APP_HEIGHT, COULEUR_PRIMAIRE
from services.stock_service  import StockService
from ui.frames.stock_frame   import StockFrame
from ui.frames.rapport_frame import RapportFrame
from ui.frames.dialogs       import (
    DialogueProduit, DialogueMouvement,
    DialogueFicheDetail, DialogueModification
)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class AlQalamApp(ctk.CTk):
    """Fenêtre principale V3 — onglets Stock + Tableau de bord."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  —  v{APP_VERSION}")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(900, 600)

        x = (self.winfo_screenwidth()  - APP_WIDTH)  // 2
        y = (self.winfo_screenheight() - APP_HEIGHT) // 2
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}+{x}+{y}")

        self.stock = StockService()
        self._construire_entete()
        self._construire_onglets()
        self._construire_pied()
        self.protocol("WM_DELETE_WINDOW", self._quitter)

    # ── Construction ───────────────────────────────────────────────────────

    def _construire_entete(self):
        entete = ctk.CTkFrame(self, fg_color=COULEUR_PRIMAIRE, height=55, corner_radius=0)
        entete.pack(fill="x")
        entete.pack_propagate(False)
        ctk.CTkLabel(entete, text="📚  Al Qalam — Gestion de Stock",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="white").pack(side="left", padx=20)
        ctk.CTkLabel(entete, text=f"v{APP_VERSION}",
                     font=ctk.CTkFont(size=12),
                     text_color="#A9CCE3").pack(side="right", padx=20)

    def _construire_onglets(self):
        """
        [V3] CTkTabview crée deux onglets.
        Chaque onglet contient un frame dédié.
        """
        self.tabs = ctk.CTkTabview(self, anchor="nw",
                                    segmented_button_selected_color=COULEUR_PRIMAIRE,
                                    segmented_button_selected_hover_color="#163D61")
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(6, 0))

        self.tabs.add("📦 Stock")
        self.tabs.add("📊 Tableau de bord")

        # Onglet Stock
        callbacks = {
            "nouveau"  : self._ouvrir_dialogue_nouveau,
            "entree"   : self._ouvrir_dialogue_entree,
            "sortie"   : self._ouvrir_dialogue_sortie,
            "modifier" : self._ouvrir_dialogue_modifier,
            "supprimer": self._supprimer_produit,
            "detail"   : self._ouvrir_fiche_detail,
        }
        self.stock_frame = StockFrame(self.tabs.tab("📦 Stock"), self.stock, callbacks)
        self.stock_frame.pack(fill="both", expand=True)

        # Onglet Tableau de bord
        self.rapport_frame = RapportFrame(self.tabs.tab("📊 Tableau de bord"), self.stock)
        self.rapport_frame.pack(fill="both", expand=True)

    def _construire_pied(self):
        pied = ctk.CTkFrame(self, height=25, fg_color="#ECF0F1", corner_radius=0)
        pied.pack(fill="x", side="bottom")
        pied.pack_propagate(False)
        ctk.CTkLabel(pied,
                     text="Al Qalam Stock Manager  |  Formation Python — Partie II",
                     font=ctk.CTkFont(size=10),
                     text_color="#7F8C8D").pack(side="left", padx=15)

    # ── Helper ─────────────────────────────────────────────────────────────

    def _post_operation(self):
        """Rafraîchit les deux onglets après toute modification du stock."""
        self.stock_frame.rafraichir()
        self.rapport_frame.rafraichir()   # [V3] dashboard synchronisé

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
        ref = self.stock_frame.get_ref_selectionnee()
        produit = self.stock.get_produit(ref) if ref else None
        dlg = DialogueMouvement(self, self.stock, "entree", produit)
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
        ref = self.stock_frame.get_ref_selectionnee()
        produit = self.stock.get_produit(ref) if ref else None
        dlg = DialogueMouvement(self, self.stock, "sortie", produit)
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

    def _quitter(self):
        if messagebox.askyesno("Quitter", "Voulez-vous quitter Al Qalam ?"):
            self.destroy()
