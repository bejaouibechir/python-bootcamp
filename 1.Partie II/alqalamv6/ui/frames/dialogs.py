# [V6 - Métaclasses] Dialogues — ajout de DialogueAjustement.
#
# NOUVEAUTÉ V6 :
#   DialogueAjustement : permet de saisir une quantité cible (inventaire physique).
#   → Appelle stock.ajustement_stock() qui crée un AjustementMouvement via le registre.
#
# DialogueMouvement étendu pour "retour" (même logique que sortie côté UI).

import customtkinter as ctk
from tkinter import messagebox

from models.produit import Produit
from config import COULEUR_PRIMAIRE, COULEUR_OK, COULEUR_ALERTE, COULEUR_TEXTE, COULEUR_ORANGE


# ─────────────────────────────────────────────────────────────────────────────
# Dialogue : Nouveau produit
# ─────────────────────────────────────────────────────────────────────────────

class DialogueProduit(ctk.CTkToplevel):
    """Dialogue modal pour ajouter un nouveau produit."""

    CATEGORIES = ["Écriture", "Papier", "Effaçage", "Coupe", "Mesure", "Classement", "Autre"]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Nouveau produit")
        self.geometry("480x520")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.resultat: Produit | None = None
        self._construire()
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _construire(self):
        ctk.CTkLabel(self, text="+ Nouveau produit",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COULEUR_PRIMAIRE).pack(pady=(20, 10))

        cadre = ctk.CTkFrame(self, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=30)

        def champ(label, placeholder=""):
            ctk.CTkLabel(cadre, text=label, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 0))
            e = ctk.CTkEntry(cadre, placeholder_text=placeholder, height=35)
            e.pack(fill="x")
            return e

        self.e_ref        = champ("Référence *",           "ex: CRAY-001")
        self.e_nom        = champ("Nom *",                 "ex: Crayon HB")
        ctk.CTkLabel(cadre, text="Catégorie *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 0))
        self.e_categorie  = ctk.CTkOptionMenu(cadre, values=self.CATEGORIES, height=35)
        self.e_categorie.pack(fill="x")
        self.e_prix_achat = champ("Prix d'achat (TND) *",  "ex: 0.30")
        self.e_prix_vente = champ("Prix de vente (TND) *", "ex: 0.90")
        self.e_qte        = champ("Quantité initiale",     "ex: 100")
        self.e_seuil      = champ("Seuil d'alerte",        "ex: 20")

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=20)
        ctk.CTkButton(barre, text="Annuler", fg_color="#7F8C8D",
                      command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(barre, text="✓ Ajouter", fg_color=COULEUR_PRIMAIRE,
                      command=self._valider).pack(side="right", expand=True, padx=(5, 0))

    def _valider(self):
        ref       = self.e_ref.get().strip().upper()
        nom       = self.e_nom.get().strip()
        categorie = self.e_categorie.get()
        pa_txt    = self.e_prix_achat.get().strip().replace(",", ".")
        pv_txt    = self.e_prix_vente.get().strip().replace(",", ".")
        qte_txt   = self.e_qte.get().strip() or "0"
        seuil_txt = self.e_seuil.get().strip() or "5"

        erreurs = []
        if not ref: erreurs.append("La référence est obligatoire.")
        if not nom: erreurs.append("Le nom est obligatoire.")
        try:
            pa = float(pa_txt)
            if pa < 0: raise ValueError
        except ValueError:
            erreurs.append("Prix d'achat invalide.")
        try:
            pv = float(pv_txt)
            if pv < 0: raise ValueError
        except ValueError:
            erreurs.append("Prix de vente invalide.")
        try:
            qte = int(qte_txt)
            if qte < 0: raise ValueError
        except ValueError:
            erreurs.append("Quantité invalide.")
        try:
            seuil = int(seuil_txt)
            if seuil < 0: raise ValueError
        except ValueError:
            erreurs.append("Seuil invalide.")

        if erreurs:
            messagebox.showerror("Erreur de saisie", "\n".join(erreurs), parent=self)
            return

        self.resultat = Produit(
            ref=ref, nom=nom, categorie=categorie,
            prix_achat=float(pa_txt), prix_vente=float(pv_txt),
            qte=int(qte_txt or 0), seuil_min=int(seuil_txt or 5),
        )
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Dialogue : Entrée / Sortie / Retour de stock
# ─────────────────────────────────────────────────────────────────────────────

class DialogueMouvement(ctk.CTkToplevel):
    """
    Dialogue pour entrée, sortie ou retour fournisseur.

    [V6] Accepte type_mvt="retour" en plus de "entree"/"sortie".
    """

    TITRES   = {"entree": "↑ Entrée de stock",  "sortie": "↓ Sortie de stock",
                "retour": "↩️ Retour fournisseur"}
    COULEURS = {"entree": COULEUR_OK, "sortie": COULEUR_ALERTE, "retour": COULEUR_ORANGE}

    def __init__(self, parent, stock_service, type_mvt: str, produit=None):
        super().__init__(parent)
        self.stock    = stock_service
        self.type_mvt = type_mvt
        self.resultat = None

        titre   = self.TITRES.get(type_mvt, "Mouvement de stock")
        couleur = self.COULEURS.get(type_mvt, COULEUR_PRIMAIRE)

        self.title(titre)
        self.geometry("400x380")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self._construire(titre, couleur, produit)
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _construire(self, titre, couleur, produit_defaut):
        header = ctk.CTkFrame(self, fg_color=couleur, height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=titre, font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="white").pack(expand=True)

        cadre = ctk.CTkFrame(self, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=30, pady=10)

        ctk.CTkLabel(cadre, text="Produit *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 0))
        refs = [f"{p.ref} — {p.nom}" for p in self.stock]
        self.combo_produit = ctk.CTkOptionMenu(cadre, values=refs or ["(aucun)"], height=35)
        self.combo_produit.pack(fill="x")
        if produit_defaut:
            valeur = f"{produit_defaut.ref} — {produit_defaut.nom}"
            if valeur in refs:
                self.combo_produit.set(valeur)

        ctk.CTkLabel(cadre, text="Quantité *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(12, 0))
        self.e_qte = ctk.CTkEntry(cadre, placeholder_text="ex: 50", height=35)
        self.e_qte.pack(fill="x")
        self.e_qte.focus_set()

        ctk.CTkLabel(cadre, text="Note (optionnel)", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(12, 0))
        self.e_note = ctk.CTkEntry(cadre, placeholder_text="ex: Commande #42", height=35)
        self.e_note.pack(fill="x")

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=15)
        ctk.CTkButton(barre, text="Annuler", fg_color="#7F8C8D",
                      command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(barre, text="✓ Valider", fg_color=couleur,
                      command=self._valider).pack(side="right", expand=True, padx=(5, 0))

    def _valider(self):
        selection = self.combo_produit.get()
        if not selection or selection == "(aucun)":
            messagebox.showerror("Erreur", "Veuillez sélectionner un produit.", parent=self)
            return
        ref = selection.split(" — ")[0].strip()
        try:
            qte = int(self.e_qte.get().strip())
            if qte <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "La quantité doit être un entier positif.", parent=self)
            return
        self.resultat = {"ref": ref, "qte": qte, "note": self.e_note.get().strip()}
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# [V6] Dialogue : Ajustement d'inventaire
# ─────────────────────────────────────────────────────────────────────────────

class DialogueAjustement(ctk.CTkToplevel):
    """
    [V6] Dialogue d'inventaire physique — règle le stock à une valeur cible.

    Montre :
      - La quantité théorique actuelle
      - Un champ pour saisir la quantité réelle (résultat du comptage)
      - Le delta calculé automatiquement

    Appelle stock.ajustement_stock() qui crée un AjustementMouvement
    via Mouvement.fabriquer("ajustement", ...) → le registre RegistreMouvementMeta.
    """

    def __init__(self, parent, produit: Produit):
        super().__init__(parent)
        self.produit  = produit
        self.resultat = None

        self.title(f"⚖️  Ajustement — {produit.nom}")
        self.geometry("420x380")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self._construire()
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _construire(self):
        # En-tête
        header = ctk.CTkFrame(self, fg_color="#8E44AD", height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="⚖️  Ajustement d'inventaire",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="white",
        ).pack(expand=True)

        cadre = ctk.CTkFrame(self, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=30, pady=15)

        # Info produit
        info = ctk.CTkFrame(cadre, fg_color="#F0F4F8", corner_radius=6)
        info.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            info,
            text=f"[{self.produit.ref}]  {self.produit.nom}  —  Catégorie : {self.produit.categorie}",
            font=ctk.CTkFont(size=11), text_color="#2C3E50",
        ).pack(padx=10, pady=6)

        # Quantité actuelle (théorique)
        ctk.CTkLabel(
            cadre, text="Quantité théorique (stock système) :",
            anchor="w", font=ctk.CTkFont(size=12),
        ).pack(fill="x")
        lbl_actuelle = ctk.CTkLabel(
            cadre, text=str(self.produit.qte),
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        )
        lbl_actuelle.pack(anchor="w", padx=4, pady=(2, 12))

        # Quantité réelle (résultat du comptage)
        ctk.CTkLabel(
            cadre, text="Quantité réelle (résultat du comptage) *",
            anchor="w", font=ctk.CTkFont(size=12),
        ).pack(fill="x")
        self.e_qte = ctk.CTkEntry(cadre, placeholder_text="ex: 45", height=38,
                                   font=ctk.CTkFont(size=14))
        self.e_qte.pack(fill="x", pady=(4, 0))
        self.e_qte.focus_set()
        self.e_qte.bind("<KeyRelease>", self._maj_delta)

        # Delta calculé en temps réel
        self._lbl_delta = ctk.CTkLabel(
            cadre, text="Écart : —",
            font=ctk.CTkFont(size=11), text_color="#7F8C8D",
        )
        self._lbl_delta.pack(anchor="w", pady=(4, 12))

        # Note
        ctk.CTkLabel(cadre, text="Motif de l'ajustement (optionnel)", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x")
        self.e_note = ctk.CTkEntry(cadre, placeholder_text="ex: Casse, inventaire annuel…",
                                    height=35)
        self.e_note.pack(fill="x")

        # Boutons
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=15)
        ctk.CTkButton(barre, text="Annuler", fg_color="#7F8C8D",
                      command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(barre, text="✓ Appliquer l'ajustement", fg_color="#8E44AD",
                      hover_color="#6C3483",
                      command=self._valider).pack(side="right", expand=True, padx=(5, 0))

    def _maj_delta(self, _event=None):
        """Calcule et affiche l'écart en temps réel pendant la frappe."""
        try:
            qte_cible = int(self.e_qte.get().strip())
            delta = qte_cible - self.produit.qte
            if delta > 0:
                self._lbl_delta.configure(
                    text=f"Écart : +{delta} (gain)",
                    text_color=COULEUR_OK,
                )
            elif delta < 0:
                self._lbl_delta.configure(
                    text=f"Écart : {delta} (perte)",
                    text_color=COULEUR_ALERTE,
                )
            else:
                self._lbl_delta.configure(
                    text="Écart : 0 (aucun changement)",
                    text_color="#7F8C8D",
                )
        except ValueError:
            self._lbl_delta.configure(text="Écart : —", text_color="#7F8C8D")

    def _valider(self):
        try:
            qte_cible = int(self.e_qte.get().strip())
            if qte_cible < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "La quantité cible doit être un entier ≥ 0.",
                                 parent=self)
            return
        self.resultat = {
            "ref"      : self.produit.ref,
            "qte_cible": qte_cible,
            "note"     : self.e_note.get().strip(),
        }
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# [V2] Dialogue : Fiche détail
# ─────────────────────────────────────────────────────────────────────────────

class DialogueFicheDetail(ctk.CTkToplevel):
    """Affiche toutes les informations d'un produit en lecture seule."""

    def __init__(self, parent, produit):
        super().__init__(parent)
        self.title(f"Fiche — {produit.nom}")
        self.geometry("400x460")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        self._construire(produit)

    def _construire(self, p):
        couleur_header = COULEUR_ALERTE if p.est_en_alerte() else COULEUR_OK
        header = ctk.CTkFrame(self, fg_color=couleur_header, height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"📦 {p.nom}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="white").pack(expand=True)

        cadre = ctk.CTkFrame(self, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=30, pady=15)

        def ligne(label, valeur):
            row = ctk.CTkFrame(cadre, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=f"{label} :", width=130, anchor="w",
                         font=ctk.CTkFont(size=12), text_color="#7F8C8D").pack(side="left")
            ctk.CTkLabel(row, text=valeur, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COULEUR_TEXTE).pack(side="left")

        ligne("Référence",     p.ref)
        ligne("Nom",           p.nom)
        ligne("Catégorie",     p.categorie)
        ligne("Prix d'achat",  f"{p.prix_achat:.3f} TND")
        ligne("Prix de vente", f"{p.prix_vente:.3f} TND")
        ligne("Marge unitaire",f"{p.marge_unitaire():.3f} TND")
        ligne("Quantité",      str(p.qte))
        ligne("Seuil d'alerte",str(p.seuil_min))
        ligne("Valeur stock",  f"{p.valeur_stock():.2f} TND")

        couleur_statut = COULEUR_ALERTE if p.est_en_alerte() else COULEUR_OK
        sf = ctk.CTkFrame(cadre, fg_color=couleur_statut, corner_radius=6, height=36)
        sf.pack(fill="x", pady=(15, 0))
        sf.pack_propagate(False)
        ctk.CTkLabel(sf, text=str(p), font=ctk.CTkFont(size=11),
                     text_color="white").pack(expand=True)

        ctk.CTkButton(self, text="Fermer", fg_color=COULEUR_PRIMAIRE,
                      command=self.destroy).pack(pady=15, padx=30, fill="x")


# ─────────────────────────────────────────────────────────────────────────────
# [V2] Dialogue : Modifier un produit
# ─────────────────────────────────────────────────────────────────────────────

class DialogueModification(ctk.CTkToplevel):
    """Formulaire pré-rempli pour modifier un produit existant."""

    CATEGORIES = ["Écriture", "Papier", "Effaçage", "Coupe", "Mesure", "Classement", "Autre"]

    def __init__(self, parent, produit):
        super().__init__(parent)
        self.title(f"Modifier — {produit.nom}")
        self.geometry("480x480")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.resultat = None
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        self._construire(produit)

    def _construire(self, p):
        ctk.CTkLabel(self, text=f"✏️  Modifier — {p.ref}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COULEUR_PRIMAIRE).pack(pady=(18, 8))

        cadre = ctk.CTkFrame(self, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=30)

        def champ(label, val):
            ctk.CTkLabel(cadre, text=label, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(fill="x", pady=(6, 0))
            e = ctk.CTkEntry(cadre, height=34)
            e.insert(0, str(val))
            e.pack(fill="x")
            return e

        ctk.CTkLabel(cadre, text="Référence (non modifiable)", anchor="w",
                     font=ctk.CTkFont(size=12), text_color="#95A5A6").pack(fill="x", pady=(6, 0))
        ref_entry = ctk.CTkEntry(cadre, height=34, fg_color="#ECF0F1", text_color="#7F8C8D")
        ref_entry.insert(0, p.ref)
        ref_entry.configure(state="disabled")
        ref_entry.pack(fill="x")

        self.e_nom        = champ("Nom *",               p.nom)
        ctk.CTkLabel(cadre, text="Catégorie *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(6, 0))
        self.e_categorie  = ctk.CTkOptionMenu(cadre, values=self.CATEGORIES, height=34)
        if p.categorie in self.CATEGORIES:
            self.e_categorie.set(p.categorie)
        self.e_categorie.pack(fill="x")
        self.e_prix_achat = champ("Prix d'achat (TND) *", p.prix_achat)
        self.e_prix_vente = champ("Prix de vente (TND) *",p.prix_vente)
        self.e_seuil      = champ("Seuil d'alerte",       p.seuil_min)
        self._ref_original = p.ref

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=15)
        ctk.CTkButton(barre, text="Annuler", fg_color="#7F8C8D",
                      command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(barre, text="✓ Enregistrer", fg_color="#8E44AD",
                      command=self._valider).pack(side="right", expand=True, padx=(5, 0))

    def _valider(self):
        nom    = self.e_nom.get().strip()
        pa_txt = self.e_prix_achat.get().strip().replace(",", ".")
        pv_txt = self.e_prix_vente.get().strip().replace(",", ".")
        s_txt  = self.e_seuil.get().strip() or "5"

        erreurs = []
        if not nom: erreurs.append("Le nom est obligatoire.")
        try:
            if float(pa_txt) < 0: raise ValueError
        except ValueError:
            erreurs.append("Prix d'achat invalide.")
        try:
            if float(pv_txt) < 0: raise ValueError
        except ValueError:
            erreurs.append("Prix de vente invalide.")
        try:
            if int(s_txt) < 0: raise ValueError
        except ValueError:
            erreurs.append("Seuil invalide.")

        if erreurs:
            messagebox.showerror("Erreur", "\n".join(erreurs), parent=self)
            return

        self.resultat = {
            "ref"       : self._ref_original,
            "nom"       : nom,
            "categorie" : self.e_categorie.get(),
            "prix_achat": float(pa_txt),
            "prix_vente": float(pv_txt),
            "seuil_min" : int(s_txt),
        }
        self.destroy()
