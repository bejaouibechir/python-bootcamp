# [V2 - Méthodes Magiques] Dialogues enrichis avec :
# - DialogueFicheDetail  : affiche toutes les infos d'un produit (lecture seule)
# - DialogueModification : formulaire pré-rempli pour modifier un produit existant

import customtkinter as ctk
from tkinter import messagebox

from models.produit import Produit
from config import COULEUR_PRIMAIRE, COULEUR_OK, COULEUR_ALERTE, COULEUR_TEXTE


# ─────────────────────────────────────────────────────────────────────────────
# Dialogue : Nouveau produit
# ─────────────────────────────────────────────────────────────────────────────

class DialogueProduit(ctk.CTkToplevel):
    """
    Dialogue modal pour ajouter un nouveau produit.

    Retourne le produit créé via self.resultat (None si annulé).
    """

    CATEGORIES = ["Écriture", "Papier", "Effaçage", "Coupe", "Mesure", "Classement", "Autre"]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Nouveau produit")
        self.geometry("480x520")
        self.resizable(False, False)
        self.grab_set()          # rend la fenêtre modale
        self.focus_set()

        self.resultat: Produit | None = None
        self._construire()

        # Centrage par rapport à la fenêtre parente
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _construire(self):
        """Construit le formulaire."""
        # ── En-tête ────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="+ Nouveau produit",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COULEUR_PRIMAIRE
        ).pack(pady=(20, 10))

        # ── Champs du formulaire ────────────────────────────────────────
        cadre = ctk.CTkFrame(self, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=30)

        def champ(label: str, placeholder: str = "") -> ctk.CTkEntry:
            """Crée un label + champ de saisie et les ajoute au formulaire."""
            ctk.CTkLabel(cadre, text=label, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 0))
            entry = ctk.CTkEntry(cadre, placeholder_text=placeholder, height=35)
            entry.pack(fill="x")
            return entry

        self.e_ref        = champ("Référence *",   "ex: CRAY-001")
        self.e_nom        = champ("Nom *",          "ex: Crayon HB")

        # Catégorie : liste déroulante
        ctk.CTkLabel(cadre, text="Catégorie *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 0))
        self.e_categorie = ctk.CTkOptionMenu(
            cadre, values=self.CATEGORIES, height=35
        )
        self.e_categorie.pack(fill="x")

        self.e_prix_achat = champ("Prix d'achat (TND) *", "ex: 0.30")
        self.e_prix_vente = champ("Prix de vente (TND) *", "ex: 0.90")
        self.e_qte        = champ("Quantité initiale",     "ex: 100")
        self.e_seuil      = champ("Seuil d'alerte",        "ex: 20")

        # ── Boutons ────────────────────────────────────────────────────
        barre_boutons = ctk.CTkFrame(self, fg_color="transparent")
        barre_boutons.pack(fill="x", padx=30, pady=20)

        ctk.CTkButton(
            barre_boutons, text="Annuler",
            fg_color="#7F8C8D", hover_color="#616A6B",
            command=self.destroy
        ).pack(side="left", expand=True, padx=(0, 5))

        ctk.CTkButton(
            barre_boutons, text="✓ Ajouter",
            fg_color=COULEUR_PRIMAIRE, hover_color="#163D61",
            command=self._valider
        ).pack(side="right", expand=True, padx=(5, 0))

    def _valider(self):
        """Valide les champs et crée l'objet Produit si tout est correct."""
        ref        = self.e_ref.get().strip().upper()
        nom        = self.e_nom.get().strip()
        categorie  = self.e_categorie.get()
        prix_achat = self.e_prix_achat.get().strip().replace(",", ".")
        prix_vente = self.e_prix_vente.get().strip().replace(",", ".")
        qte_txt    = self.e_qte.get().strip() or "0"
        seuil_txt  = self.e_seuil.get().strip() or "5"

        # Validation des champs obligatoires
        erreurs = []
        if not ref:
            erreurs.append("La référence est obligatoire.")
        if not nom:
            erreurs.append("Le nom est obligatoire.")
        try:
            pa = float(prix_achat)
            if pa < 0:
                raise ValueError
        except ValueError:
            erreurs.append("Prix d'achat invalide (ex: 0.30).")
        try:
            pv = float(prix_vente)
            if pv < 0:
                raise ValueError
        except ValueError:
            erreurs.append("Prix de vente invalide (ex: 0.90).")
        try:
            qte = int(qte_txt)
            if qte < 0:
                raise ValueError
        except ValueError:
            erreurs.append("Quantité invalide (nombre entier ≥ 0).")
        try:
            seuil = int(seuil_txt)
            if seuil < 0:
                raise ValueError
        except ValueError:
            erreurs.append("Seuil d'alerte invalide (nombre entier ≥ 0).")

        if erreurs:
            messagebox.showerror("Erreur de saisie", "\n".join(erreurs), parent=self)
            return

        # Tout est valide → on crée le produit et on ferme
        self.resultat = Produit(
            ref=ref, nom=nom, categorie=categorie,
            prix_achat=float(prix_achat), prix_vente=float(prix_vente),
            qte=int(qte_txt or 0), seuil_min=int(seuil_txt or 5)
        )
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Dialogue : Entrée / Sortie de stock
# ─────────────────────────────────────────────────────────────────────────────

class DialogueMouvement(ctk.CTkToplevel):
    """
    Dialogue modal pour enregistrer une entrée ou une sortie de stock.

    Args:
        type_mvt : "entree" ou "sortie"
        produit  : Produit pré-sélectionné (ou None pour choisir dans la liste)
    """

    def __init__(self, parent, stock_service, type_mvt: str, produit=None):
        super().__init__(parent)
        self.stock    = stock_service
        self.type_mvt = type_mvt
        self.resultat = None   # sera un dict {"ref": ..., "qte": ..., "note": ...}

        est_entree = type_mvt == "entree"
        titre = "↑ Entrée de stock" if est_entree else "↓ Sortie de stock"
        couleur = COULEUR_OK if est_entree else COULEUR_ALERTE

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

    def _construire(self, titre: str, couleur: str, produit_defaut):
        # En-tête coloré selon le type
        header = ctk.CTkFrame(self, fg_color=couleur, height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text=titre,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="white"
        ).pack(expand=True)

        cadre = ctk.CTkFrame(self, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=30, pady=10)

        # Sélection du produit (liste déroulante)
        ctk.CTkLabel(cadre, text="Produit *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(8, 0))
        refs = [f"{p.ref} — {p.nom}" for p in self.stock]   # utilise __iter__
        self.combo_produit = ctk.CTkOptionMenu(cadre, values=refs or ["(aucun)"], height=35)
        self.combo_produit.pack(fill="x")

        # Pré-sélectionner le produit si fourni
        if produit_defaut:
            valeur = f"{produit_defaut.ref} — {produit_defaut.nom}"
            if valeur in refs:
                self.combo_produit.set(valeur)

        # Quantité
        ctk.CTkLabel(cadre, text="Quantité *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(12, 0))
        self.e_qte = ctk.CTkEntry(cadre, placeholder_text="ex: 50", height=35)
        self.e_qte.pack(fill="x")
        self.e_qte.focus_set()

        # Note optionnelle
        ctk.CTkLabel(cadre, text="Note (optionnel)", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(12, 0))
        self.e_note = ctk.CTkEntry(cadre, placeholder_text="ex: Commande fournisseur #42",
                                    height=35)
        self.e_note.pack(fill="x")

        # Boutons
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=15)

        ctk.CTkButton(
            barre, text="Annuler",
            fg_color="#7F8C8D", hover_color="#616A6B",
            command=self.destroy
        ).pack(side="left", expand=True, padx=(0, 5))

        ctk.CTkButton(
            barre, text="✓ Valider",
            fg_color=couleur,
            command=self._valider
        ).pack(side="right", expand=True, padx=(5, 0))

    def _valider(self):
        """Valide et retourne le mouvement sous forme de dict."""
        selection = self.combo_produit.get()
        if not selection or selection == "(aucun)":
            messagebox.showerror("Erreur", "Veuillez sélectionner un produit.", parent=self)
            return

        # Extraire la ref (avant " — ")
        ref = selection.split(" — ")[0].strip()

        qte_txt = self.e_qte.get().strip()
        try:
            qte = int(qte_txt)
            if qte <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "La quantité doit être un entier positif.", parent=self)
            return

        self.resultat = {
            "ref" : ref,
            "qte" : qte,
            "note": self.e_note.get().strip()
        }
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# [V2] Dialogue : Fiche détail d'un produit (lecture seule)
# ─────────────────────────────────────────────────────────────────────────────

class DialogueFicheDetail(ctk.CTkToplevel):
    """
    Affiche toutes les informations d'un produit en lecture seule.
    Ouvert par double-clic sur une ligne du tableau.
    [V2] Utilise str(produit) qui appelle __str__.
    """

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
        # En-tête coloré selon le statut
        couleur_header = COULEUR_ALERTE if p.est_en_alerte() else COULEUR_OK
        header = ctk.CTkFrame(self, fg_color=couleur_header, height=60, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"📦 {p.nom}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="white").pack(expand=True)

        cadre = ctk.CTkFrame(self, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=30, pady=15)

        def ligne(label: str, valeur: str):
            """Affiche une ligne label : valeur."""
            row = ctk.CTkFrame(cadre, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=f"{label} :", width=130, anchor="w",
                         font=ctk.CTkFont(size=12),
                         text_color="#7F8C8D").pack(side="left")
            ctk.CTkLabel(row, text=valeur, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COULEUR_TEXTE).pack(side="left")

        ligne("Référence",    p.ref)
        ligne("Nom",          p.nom)
        ligne("Catégorie",    p.categorie)
        ligne("Prix d'achat", f"{p.prix_achat:.3f} TND")
        ligne("Prix de vente",f"{p.prix_vente:.3f} TND")
        ligne("Marge unitaire", f"{p.marge_unitaire():.3f} TND")
        ligne("Quantité",     str(p.qte))
        ligne("Seuil d'alerte", str(p.seuil_min))
        ligne("Valeur stock", f"{p.valeur_stock():.2f} TND")

        # Statut mis en valeur
        couleur_statut = COULEUR_ALERTE if p.est_en_alerte() else COULEUR_OK
        statut_frame = ctk.CTkFrame(cadre, fg_color=couleur_statut,
                                     corner_radius=6, height=36)
        statut_frame.pack(fill="x", pady=(15, 0))
        statut_frame.pack_propagate(False)
        # [V2] str(p) appelle __str__ de Produit
        ctk.CTkLabel(statut_frame, text=str(p),
                     font=ctk.CTkFont(size=11),
                     text_color="white").pack(expand=True)

        ctk.CTkButton(self, text="Fermer", fg_color=COULEUR_PRIMAIRE,
                      command=self.destroy).pack(pady=15, padx=30, fill="x")


# ─────────────────────────────────────────────────────────────────────────────
# [V2] Dialogue : Modifier un produit existant
# ─────────────────────────────────────────────────────────────────────────────

class DialogueModification(ctk.CTkToplevel):
    """
    Formulaire pré-rempli pour modifier un produit existant.
    Retourne le produit modifié via self.resultat.
    """

    CATEGORIES = ["Écriture", "Papier", "Effaçage", "Coupe", "Mesure", "Classement", "Autre"]

    def __init__(self, parent, produit):
        super().__init__(parent)
        self.title(f"Modifier — {produit.nom}")
        self.geometry("480x480")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.resultat: Produit | None = None

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

        def champ(label, valeur_defaut):
            ctk.CTkLabel(cadre, text=label, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(fill="x", pady=(6, 0))
            e = ctk.CTkEntry(cadre, height=34)
            e.insert(0, str(valeur_defaut))
            e.pack(fill="x")
            return e

        # La référence est non modifiable (clé primaire)
        ctk.CTkLabel(cadre, text="Référence (non modifiable)", anchor="w",
                     font=ctk.CTkFont(size=12), text_color="#95A5A6").pack(fill="x", pady=(6, 0))
        ref_lbl = ctk.CTkEntry(cadre, height=34, state="disabled",
                                fg_color="#ECF0F1", text_color="#7F8C8D")
        ref_lbl.configure(state="normal")
        ref_lbl.insert(0, p.ref)
        ref_lbl.configure(state="disabled")
        ref_lbl.pack(fill="x")

        self.e_nom        = champ("Nom *",               p.nom)
        ctk.CTkLabel(cadre, text="Catégorie *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(6, 0))
        self.e_categorie = ctk.CTkOptionMenu(cadre, values=self.CATEGORIES, height=34)
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
        nom        = self.e_nom.get().strip()
        prix_achat = self.e_prix_achat.get().strip().replace(",", ".")
        prix_vente = self.e_prix_vente.get().strip().replace(",", ".")
        seuil_txt  = self.e_seuil.get().strip() or "5"

        erreurs = []
        if not nom:
            erreurs.append("Le nom est obligatoire.")
        try:
            pa = float(prix_achat)
            if pa < 0: raise ValueError
        except ValueError:
            erreurs.append("Prix d'achat invalide.")
        try:
            pv = float(prix_vente)
            if pv < 0: raise ValueError
        except ValueError:
            erreurs.append("Prix de vente invalide.")
        try:
            seuil = int(seuil_txt)
            if seuil < 0: raise ValueError
        except ValueError:
            erreurs.append("Seuil invalide.")

        if erreurs:
            messagebox.showerror("Erreur", "\n".join(erreurs), parent=self)
            return

        # On récupère la qte actuelle depuis le produit original (non modifiable ici)
        self.resultat = {
            "ref"       : self._ref_original,
            "nom"       : nom,
            "categorie" : self.e_categorie.get(),
            "prix_achat": float(prix_achat),
            "prix_vente": float(prix_vente),
            "seuil_min" : int(seuil_txt),
        }
        self.destroy()
