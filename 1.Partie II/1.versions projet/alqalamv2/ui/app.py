# [V2 - Méthodes Magiques] Fenêtre principale enrichie avec :
# - Callbacks modifier, supprimer, detail
# - Utilisation de __len__, __contains__ du StockService

import customtkinter as ctk
from tkinter import messagebox

from config import (
    APP_NAME, APP_VERSION, APP_WIDTH, APP_HEIGHT,
    COULEUR_PRIMAIRE
)
from services.stock_service import StockService
from ui.frames.stock_frame  import StockFrame
from ui.frames.dialogs      import (
    DialogueProduit, DialogueMouvement,
    DialogueFicheDetail, DialogueModification
)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class AlQalamApp(ctk.CTk):
    """Fenêtre principale V2 — méthodes magiques intégrées."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  —  v{APP_VERSION}")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(900, 580)

        self.update_idletasks()
        x = (self.winfo_screenwidth()  - APP_WIDTH)  // 2
        y = (self.winfo_screenheight() - APP_HEIGHT) // 2
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}+{x}+{y}")

        self.stock = StockService()
        # [V2] Démo console : __str__, __len__, __contains__
        print(self.stock)                          # utilise __str__
        print(f"CRAY-001 in stock : {'CRAY-001' in self.stock}")  # utilise __contains__

        self._construire_entete()
        self._construire_contenu()
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

    def _construire_contenu(self):
        callbacks = {
            "nouveau"  : self._ouvrir_dialogue_nouveau,
            "entree"   : self._ouvrir_dialogue_entree,
            "sortie"   : self._ouvrir_dialogue_sortie,
            "modifier" : self._ouvrir_dialogue_modifier,   # [V2]
            "supprimer": self._supprimer_produit,          # [V2]
            "detail"   : self._ouvrir_fiche_detail,        # [V2]
        }
        self.stock_frame = StockFrame(self, self.stock, callbacks)
        self.stock_frame.pack(fill="both", expand=True)

    def _construire_pied(self):
        pied = ctk.CTkFrame(self, height=25, fg_color="#ECF0F1", corner_radius=0)
        pied.pack(fill="x", side="bottom")
        pied.pack_propagate(False)
        ctk.CTkLabel(pied,
                     text="Al Qalam Stock Manager  |  Formation Python — Partie II",
                     font=ctk.CTkFont(size=10),
                     text_color="#7F8C8D").pack(side="left", padx=15)

    # ── Dialogues hérités de V1 ────────────────────────────────────────────

    def _ouvrir_dialogue_nouveau(self):
        dlg = DialogueProduit(self)
        self.wait_window(dlg)
        if dlg.resultat is not None:
            try:
                self.stock.ajouter_produit(dlg.resultat)
                self.stock_frame.rafraichir()
                messagebox.showinfo("Produit ajouté",
                                    f"✅ '{dlg.resultat.nom}' ajouté avec succès.")
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
                self.stock_frame.rafraichir()
                messagebox.showinfo("Entrée enregistrée",
                                    f"✅ +{r['qte']} unités pour '{r['ref']}'.")
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
                self.stock_frame.rafraichir()
                messagebox.showinfo("Sortie enregistrée",
                                    f"✅ -{r['qte']} unités pour '{r['ref']}'.")
            except (ValueError, KeyError) as e:
                messagebox.showerror("Erreur", str(e))

    # ── Nouveaux callbacks V2 ──────────────────────────────────────────────

    def _ouvrir_fiche_detail(self, ref: str):
        """[V2] Ouvre la fiche détail (double-clic ou bouton)."""
        try:
            produit = self.stock.get_produit(ref)
            dlg = DialogueFicheDetail(self, produit)
            self.wait_window(dlg)
        except KeyError as e:
            messagebox.showerror("Erreur", str(e))

    def _ouvrir_dialogue_modifier(self):
        """[V2] Ouvre le formulaire de modification d'un produit sélectionné."""
        ref = self.stock_frame.get_ref_selectionnee()
        if not ref:
            messagebox.showwarning("Aucune sélection",
                                   "Sélectionnez d'abord un produit dans le tableau.")
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
            # On reconstruit le produit en conservant la quantité actuelle
            produit_maj = produit.__class__(
                ref        = r["ref"],
                nom        = r["nom"],
                categorie  = r["categorie"],
                prix_achat = r["prix_achat"],
                prix_vente = r["prix_vente"],
                qte        = produit.qte,      # quantité inchangée
                seuil_min  = r["seuil_min"],
            )
            # [V2] __eq__ : produit_maj == produit → True (même ref)
            self.stock.mettre_a_jour_produit(produit_maj)
            self.stock_frame.rafraichir()
            messagebox.showinfo("Modifié", f"✅ '{r['nom']}' mis à jour.")

    def _supprimer_produit(self):
        """[V2] Supprime le produit sélectionné après confirmation."""
        ref = self.stock_frame.get_ref_selectionnee()
        if not ref:
            messagebox.showwarning("Aucune sélection",
                                   "Sélectionnez d'abord un produit dans le tableau.")
            return
        try:
            produit = self.stock.get_produit(ref)
        except KeyError as e:
            messagebox.showerror("Erreur", str(e))
            return

        # [V2] str(produit) utilise __str__
        confirme = messagebox.askyesno(
            "Confirmer la suppression",
            f"Supprimer définitivement :\n{str(produit)} ?"
        )
        if confirme:
            self.stock.supprimer_produit(ref)
            self.stock_frame.rafraichir()
            messagebox.showinfo("Supprimé", f"✅ '{produit.nom}' supprimé.")

    # ── Fermeture ─────────────────────────────────────────────────────────

    def _quitter(self):
        if messagebox.askyesno("Quitter", "Voulez-vous quitter Al Qalam ?"):
            self.destroy()
