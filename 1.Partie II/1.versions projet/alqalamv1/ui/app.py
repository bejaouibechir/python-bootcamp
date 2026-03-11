# [V1 - UI] Fenêtre principale de l'application Al Qalam.
# Elle orchestre tous les panneaux (frames) et connecte l'UI au service.

import customtkinter as ctk
from tkinter import messagebox

from config import (
    APP_NAME, APP_VERSION, APP_WIDTH, APP_HEIGHT,
    COULEUR_PRIMAIRE, COULEUR_FOND
)
from services.stock_service    import StockService
from ui.frames.stock_frame     import StockFrame
from ui.frames.dialogs         import DialogueProduit, DialogueMouvement


# ── Configuration globale de CustomTkinter ─────────────────────────────────
# "system" : suit le thème Windows (clair/sombre automatiquement)
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class AlQalamApp(ctk.CTk):
    """
    Fenêtre principale de l'application.

    Hérite de CTk (CustomTkinter) qui hérite lui-même de Tk (tkinter).
    La boucle graphique est lancée par mainloop() dans main.py.
    """

    def __init__(self):
        super().__init__()

        # ── Configuration de la fenêtre ────────────────────────────────
        self.title(f"{APP_NAME}  —  v{APP_VERSION}")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.minsize(900, 580)

        # Centrage de la fenêtre sur l'écran
        self.update_idletasks()
        larg_ecran = self.winfo_screenwidth()
        haut_ecran = self.winfo_screenheight()
        x = (larg_ecran - APP_WIDTH)  // 2
        y = (haut_ecran - APP_HEIGHT) // 2
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}+{x}+{y}")

        # ── Initialisation du service métier ───────────────────────────
        self.stock = StockService()

        # ── Construction de l'interface ────────────────────────────────
        self._construire_entete()
        self._construire_contenu()
        self._construire_pied()

        # Fermeture propre
        self.protocol("WM_DELETE_WINDOW", self._quitter)

    # ── Construction ───────────────────────────────────────────────────────

    def _construire_entete(self):
        """Barre de titre colorée en haut de la fenêtre."""
        entete = ctk.CTkFrame(self, fg_color=COULEUR_PRIMAIRE, height=55, corner_radius=0)
        entete.pack(fill="x")
        entete.pack_propagate(False)

        # Logo + nom de l'application
        ctk.CTkLabel(
            entete,
            text="📚  Al Qalam — Gestion de Stock",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=10)

        # Numéro de version à droite
        ctk.CTkLabel(
            entete,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color="#A9CCE3"
        ).pack(side="right", padx=20)

    def _construire_contenu(self):
        """Zone centrale avec le frame de stock."""
        # Callbacks : fonctions à appeler depuis les boutons de StockFrame
        callbacks = {
            "nouveau": self._ouvrir_dialogue_nouveau,
            "entree" : self._ouvrir_dialogue_entree,
            "sortie" : self._ouvrir_dialogue_sortie,
        }

        self.stock_frame = StockFrame(self, self.stock, callbacks)
        self.stock_frame.pack(fill="both", expand=True)

    def _construire_pied(self):
        """Pied de page discret avec le copyright."""
        pied = ctk.CTkFrame(self, height=25, fg_color="#ECF0F1", corner_radius=0)
        pied.pack(fill="x", side="bottom")
        pied.pack_propagate(False)

        ctk.CTkLabel(
            pied,
            text="Al Qalam Stock Manager  |  Formation Python — Partie II",
            font=ctk.CTkFont(size=10),
            text_color="#7F8C8D"
        ).pack(side="left", padx=15)

    # ── Dialogues ─────────────────────────────────────────────────────────

    def _ouvrir_dialogue_nouveau(self):
        """Ouvre le dialogue d'ajout d'un nouveau produit."""
        dlg = DialogueProduit(self)
        self.wait_window(dlg)          # attendre la fermeture du dialogue

        if dlg.resultat is not None:
            try:
                self.stock.ajouter_produit(dlg.resultat)
                self.stock_frame.rafraichir()
                messagebox.showinfo(
                    "Produit ajouté",
                    f"✅ '{dlg.resultat.nom}' ajouté avec succès."
                )
            except ValueError as e:
                messagebox.showerror("Erreur", str(e))

    def _ouvrir_dialogue_entree(self):
        """Ouvre le dialogue d'entrée de stock (réception)."""
        ref_sel = self.stock_frame.get_ref_selectionnee()
        produit = self.stock.get_produit(ref_sel) if ref_sel else None

        dlg = DialogueMouvement(self, self.stock, "entree", produit)
        self.wait_window(dlg)

        if dlg.resultat is not None:
            try:
                r = dlg.resultat
                self.stock.entree_stock(r["ref"], r["qte"], r["note"])
                self.stock_frame.rafraichir()
                messagebox.showinfo(
                    "Entrée enregistrée",
                    f"✅ +{r['qte']} unités ajoutées pour '{r['ref']}'."
                )
            except (ValueError, KeyError) as e:
                messagebox.showerror("Erreur", str(e))

    def _ouvrir_dialogue_sortie(self):
        """Ouvre le dialogue de sortie de stock (vente)."""
        ref_sel = self.stock_frame.get_ref_selectionnee()
        produit = self.stock.get_produit(ref_sel) if ref_sel else None

        dlg = DialogueMouvement(self, self.stock, "sortie", produit)
        self.wait_window(dlg)

        if dlg.resultat is not None:
            try:
                r = dlg.resultat
                self.stock.sortie_stock(r["ref"], r["qte"], r["note"])
                self.stock_frame.rafraichir()
                messagebox.showinfo(
                    "Sortie enregistrée",
                    f"✅ -{r['qte']} unités retirées pour '{r['ref']}'."
                )
            except (ValueError, KeyError) as e:
                messagebox.showerror("Erreur", str(e))

    # ── Fermeture ─────────────────────────────────────────────────────────

    def _quitter(self):
        """Fermeture propre de l'application."""
        if messagebox.askyesno("Quitter", "Voulez-vous quitter Al Qalam ?"):
            self.destroy()
