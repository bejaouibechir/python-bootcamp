# [V7 - Regex] Dialogues avec validation en temps réel par expressions régulières.
#
# NOUVEAUTÉ V7 :
#   Chaque champ de saisie affiche un indicateur visuel (✓ vert / ✗ rouge)
#   mis à jour à chaque frappe (<KeyRelease>) grâce aux regex du module validators.
#
#   Principe :
#     1. L'utilisateur tape dans un CTkEntry
#     2. L'événement <KeyRelease> appelle _valider_champs()
#     3. Les regex compilées (REGEX[...]) testent la valeur instantanément
#     4. Un CTkLabel affiche le résultat (✓ vert ou message d'erreur rouge)
#     5. Le bouton "Ajouter/Valider" est activé uniquement si tout est valide

import customtkinter as ctk
from tkinter import messagebox

from models.produit import Produit
from config import COULEUR_PRIMAIRE, COULEUR_OK, COULEUR_ALERTE, COULEUR_TEXTE, COULEUR_ORANGE
from validators.regex_validators import valider_ref, valider_nom, valider_prix, valider_qte, valider_note

# Couleurs de feedback regex
COULEUR_VALIDE   = COULEUR_OK
COULEUR_INVALIDE = COULEUR_ALERTE
COULEUR_NEUTRE   = "#95A5A6"


# ─────────────────────────────────────────────────────────────────────────────
# Dialogue : Nouveau produit — validation regex en temps réel
# ─────────────────────────────────────────────────────────────────────────────

class DialogueProduit(ctk.CTkToplevel):
    """
    Dialogue modal pour ajouter un nouveau produit.

    [V7] Chaque champ est validé en temps réel par regex.
    Un indicateur ✓/✗ s'affiche sous chaque entrée.
    Le bouton "Ajouter" reste désactivé jusqu'à ce que tous les champs soient valides.
    """

    CATEGORIES = ["Écriture", "Papier", "Effaçage", "Coupe", "Mesure", "Classement", "Autre"]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Nouveau produit")
        self.geometry("490x640")
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
                     text_color=COULEUR_PRIMAIRE).pack(pady=(18, 2))

        # Sous-titre V7
        ctk.CTkLabel(
            self,
            text="[V7] Validation regex en temps réel — format réf : XX…-NNN",
            font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        ).pack(pady=(0, 6))

        cadre = ctk.CTkFrame(self, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=30)

        def champ_avec_feedback(label_txt, placeholder, bind_cmd):
            ctk.CTkLabel(cadre, text=label_txt, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(fill="x", pady=(6, 0))
            entry = ctk.CTkEntry(cadre, placeholder_text=placeholder, height=35)
            entry.pack(fill="x")
            lbl = ctk.CTkLabel(cadre, text="", anchor="w",
                               font=ctk.CTkFont(size=10), text_color=COULEUR_NEUTRE)
            lbl.pack(fill="x")
            entry.bind("<KeyRelease>", bind_cmd)
            return entry, lbl

        self.e_ref,        self.lbl_ref        = champ_avec_feedback(
            "Référence *  (ex: CRAY-001, PAP-A4)", "ex: CRAY-001", self._valider_champs)
        self.e_nom,        self.lbl_nom        = champ_avec_feedback(
            "Nom *", "ex: Crayon HB", self._valider_champs)

        ctk.CTkLabel(cadre, text="Catégorie *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(6, 0))
        self.e_categorie = ctk.CTkOptionMenu(cadre, values=self.CATEGORIES, height=35)
        self.e_categorie.pack(fill="x")

        self.e_prix_achat, self.lbl_prix_achat = champ_avec_feedback(
            "Prix d'achat (TND) *", "ex: 0.300", self._valider_champs)
        self.e_prix_vente, self.lbl_prix_vente = champ_avec_feedback(
            "Prix de vente (TND) *", "ex: 0.900", self._valider_champs)
        self.e_qte,        self.lbl_qte        = champ_avec_feedback(
            "Quantité initiale", "ex: 100  (défaut: 0)", self._valider_champs)
        self.e_seuil,      self.lbl_seuil      = champ_avec_feedback(
            "Seuil d'alerte", "ex: 20  (défaut: 5)", self._valider_champs)

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=16)
        ctk.CTkButton(barre, text="Annuler", fg_color="#7F8C8D",
                      command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        self.btn_ajouter = ctk.CTkButton(
            barre, text="✓ Ajouter", fg_color="#7F8C8D",
            command=self._valider, state="disabled",
        )
        self.btn_ajouter.pack(side="right", expand=True, padx=(5, 0))

    def _valider_champs(self, _event=None):
        """[V7] Valide tous les champs par regex à chaque frappe."""
        ref_txt   = self.e_ref.get().strip().upper()
        nom_txt   = self.e_nom.get().strip()
        pa_txt    = self.e_prix_achat.get().strip()
        pv_txt    = self.e_prix_vente.get().strip()
        qte_txt   = self.e_qte.get().strip()
        seuil_txt = self.e_seuil.get().strip()

        resultats = [
            (valider_ref(ref_txt),                    self.lbl_ref),
            (valider_nom(nom_txt),                    self.lbl_nom),
            (valider_prix(pa_txt),                    self.lbl_prix_achat),
            (valider_prix(pv_txt),                    self.lbl_prix_vente),
            (valider_qte(qte_txt, obligatoire=False), self.lbl_qte),
            (valider_qte(seuil_txt, obligatoire=False), self.lbl_seuil),
        ]

        tous_valides = True
        for (valide, msg), lbl in resultats:
            lbl.configure(
                text=msg,
                text_color=COULEUR_VALIDE if valide else COULEUR_INVALIDE,
            )
            if not valide:
                tous_valides = False

        self.btn_ajouter.configure(
            state="normal" if tous_valides else "disabled",
            fg_color=COULEUR_OK if tous_valides else "#7F8C8D",
        )

    def _valider(self):
        ref       = self.e_ref.get().strip().upper()
        nom       = self.e_nom.get().strip()
        categorie = self.e_categorie.get()
        pa        = float(self.e_prix_achat.get().strip().replace(",", "."))
        pv        = float(self.e_prix_vente.get().strip().replace(",", "."))
        qte       = int(self.e_qte.get().strip() or "0")
        seuil     = int(self.e_seuil.get().strip() or "5")
        self.resultat = Produit(
            ref=ref, nom=nom, categorie=categorie,
            prix_achat=pa, prix_vente=pv, qte=qte, seuil_min=seuil,
        )
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Dialogue : Entrée / Sortie / Retour — validation regex quantité
# ─────────────────────────────────────────────────────────────────────────────

class DialogueMouvement(ctk.CTkToplevel):
    """
    Dialogue pour entrée, sortie ou retour fournisseur.
    [V7] La quantité est validée par regex en temps réel.
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
        self.geometry("400x420")
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
        self.lbl_qte = ctk.CTkLabel(cadre, text="", anchor="w",
                                     font=ctk.CTkFont(size=10), text_color=COULEUR_NEUTRE)
        self.lbl_qte.pack(fill="x")
        self.e_qte.bind("<KeyRelease>", self._valider_qte_live)
        self.e_qte.focus_set()

        ctk.CTkLabel(cadre, text="Note (optionnel)", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(10, 0))
        self.e_note = ctk.CTkEntry(cadre, placeholder_text="ex: Commande #42", height=35)
        self.e_note.pack(fill="x")
        self.lbl_note = ctk.CTkLabel(cadre, text="", anchor="w",
                                      font=ctk.CTkFont(size=10), text_color=COULEUR_NEUTRE)
        self.lbl_note.pack(fill="x")
        self.e_note.bind("<KeyRelease>", self._valider_note_live)

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=12)
        ctk.CTkButton(barre, text="Annuler", fg_color="#7F8C8D",
                      command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(barre, text="✓ Valider", fg_color=couleur,
                      command=self._valider).pack(side="right", expand=True, padx=(5, 0))

    def _valider_qte_live(self, _event=None):
        txt = self.e_qte.get().strip()
        valide, msg = valider_qte(txt, obligatoire=True)
        if valide and txt == "0":
            valide, msg = False, "La quantité doit être > 0."
        self.lbl_qte.configure(
            text=msg,
            text_color=COULEUR_VALIDE if valide else COULEUR_INVALIDE,
        )

    def _valider_note_live(self, _event=None):
        valide, msg = valider_note(self.e_note.get())
        self.lbl_note.configure(
            text=msg,
            text_color=COULEUR_VALIDE if valide else COULEUR_INVALIDE,
        )

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
# [V6+V7] Dialogue : Ajustement d'inventaire
# ─────────────────────────────────────────────────────────────────────────────

class DialogueAjustement(ctk.CTkToplevel):
    """[V6+V7] Ajustement d'inventaire avec validation regex sur la quantité cible."""

    def __init__(self, parent, produit: Produit):
        super().__init__(parent)
        self.produit  = produit
        self.resultat = None
        self.title(f"⚖️  Ajustement — {produit.nom}")
        self.geometry("420x420")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self._construire()
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _construire(self):
        header = ctk.CTkFrame(self, fg_color="#8E44AD", height=50, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="⚖️  Ajustement d'inventaire",
                     font=ctk.CTkFont(size=15, weight="bold"), text_color="white").pack(expand=True)

        cadre = ctk.CTkFrame(self, fg_color="transparent")
        cadre.pack(fill="both", expand=True, padx=30, pady=15)

        info = ctk.CTkFrame(cadre, fg_color="#F0F4F8", corner_radius=6)
        info.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(info,
                     text=f"[{self.produit.ref}]  {self.produit.nom}  —  {self.produit.categorie}",
                     font=ctk.CTkFont(size=11), text_color="#2C3E50").pack(padx=10, pady=6)

        ctk.CTkLabel(cadre, text="Quantité théorique (stock système) :",
                     anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x")
        ctk.CTkLabel(cadre, text=str(self.produit.qte),
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COULEUR_PRIMAIRE).pack(anchor="w", padx=4, pady=(2, 10))

        ctk.CTkLabel(cadre, text="Quantité réelle (résultat du comptage) *",
                     anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x")
        self.e_qte = ctk.CTkEntry(cadre, placeholder_text="ex: 45", height=38,
                                   font=ctk.CTkFont(size=14))
        self.e_qte.pack(fill="x", pady=(4, 0))
        self.e_qte.focus_set()
        self.e_qte.bind("<KeyRelease>", self._maj_live)
        self._lbl_delta = ctk.CTkLabel(cadre, text="Écart : —",
                                        font=ctk.CTkFont(size=11), text_color="#7F8C8D")
        self._lbl_delta.pack(anchor="w", pady=(4, 10))

        ctk.CTkLabel(cadre, text="Motif de l'ajustement (optionnel)", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x")
        self.e_note = ctk.CTkEntry(cadre, placeholder_text="ex: Casse, inventaire annuel…",
                                    height=35)
        self.e_note.pack(fill="x")

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=15)
        ctk.CTkButton(barre, text="Annuler", fg_color="#7F8C8D",
                      command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(barre, text="✓ Appliquer", fg_color="#8E44AD",
                      hover_color="#6C3483",
                      command=self._valider).pack(side="right", expand=True, padx=(5, 0))

    def _maj_live(self, _event=None):
        """[V7] Valide la quantité par regex ET calcule l'écart en temps réel."""
        txt = self.e_qte.get().strip()
        valide, _ = valider_qte(txt, obligatoire=True)
        if valide:
            try:
                qte_cible = int(txt)
                delta = qte_cible - self.produit.qte
                if delta > 0:
                    self._lbl_delta.configure(text=f"Écart : +{delta} (gain)", text_color=COULEUR_OK)
                elif delta < 0:
                    self._lbl_delta.configure(text=f"Écart : {delta} (perte)", text_color=COULEUR_ALERTE)
                else:
                    self._lbl_delta.configure(text="Écart : 0 (aucun changement)", text_color="#7F8C8D")
            except ValueError:
                self._lbl_delta.configure(text="Écart : —", text_color="#7F8C8D")
        else:
            self._lbl_delta.configure(text="⚠ Entier ≥ 0 attendu", text_color=COULEUR_INVALIDE)

    def _valider(self):
        try:
            qte_cible = int(self.e_qte.get().strip())
            if qte_cible < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "La quantité cible doit être un entier ≥ 0.", parent=self)
            return
        self.resultat = {
            "ref"      : self.produit.ref,
            "qte_cible": qte_cible,
            "note"     : self.e_note.get().strip(),
        }
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# [V2] Dialogue : Fiche détail (inchangé V7)
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
# [V2+V7] Dialogue : Modifier un produit — validation regex en temps réel
# ─────────────────────────────────────────────────────────────────────────────

class DialogueModification(ctk.CTkToplevel):
    """
    Formulaire pré-rempli pour modifier un produit existant.
    [V7] Les champs nom, prix, seuil sont validés par regex en temps réel.
    """

    CATEGORIES = ["Écriture", "Papier", "Effaçage", "Coupe", "Mesure", "Classement", "Autre"]

    def __init__(self, parent, produit):
        super().__init__(parent)
        self.title(f"Modifier — {produit.nom}")
        self.geometry("480x520")
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

        # Référence (non modifiable)
        ctk.CTkLabel(cadre, text="Référence (non modifiable)", anchor="w",
                     font=ctk.CTkFont(size=12), text_color="#95A5A6").pack(fill="x", pady=(6, 0))
        ref_entry = ctk.CTkEntry(cadre, height=34, fg_color="#ECF0F1", text_color="#7F8C8D")
        ref_entry.insert(0, p.ref)
        ref_entry.configure(state="disabled")
        ref_entry.pack(fill="x")
        self._ref_original = p.ref

        def champ_regex(label_txt, val, bind_cmd):
            ctk.CTkLabel(cadre, text=label_txt, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(fill="x", pady=(6, 0))
            e = ctk.CTkEntry(cadre, height=34)
            e.insert(0, str(val))
            e.pack(fill="x")
            lbl = ctk.CTkLabel(cadre, text="", anchor="w",
                               font=ctk.CTkFont(size=10), text_color=COULEUR_NEUTRE)
            lbl.pack(fill="x")
            e.bind("<KeyRelease>", bind_cmd)
            return e, lbl

        self.e_nom,        self.lbl_nom   = champ_regex("Nom *",               p.nom,        self._valider_champs)
        ctk.CTkLabel(cadre, text="Catégorie *", anchor="w",
                     font=ctk.CTkFont(size=12)).pack(fill="x", pady=(6, 0))
        self.e_categorie = ctk.CTkOptionMenu(cadre, values=self.CATEGORIES, height=34)
        if p.categorie in self.CATEGORIES:
            self.e_categorie.set(p.categorie)
        self.e_categorie.pack(fill="x")
        self.e_prix_achat, self.lbl_pa    = champ_regex("Prix d'achat (TND) *", p.prix_achat, self._valider_champs)
        self.e_prix_vente, self.lbl_pv    = champ_regex("Prix de vente (TND) *",p.prix_vente, self._valider_champs)
        self.e_seuil,      self.lbl_seuil = champ_regex("Seuil d'alerte",       p.seuil_min,  self._valider_champs)

        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=30, pady=14)
        ctk.CTkButton(barre, text="Annuler", fg_color="#7F8C8D",
                      command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(barre, text="✓ Enregistrer", fg_color="#8E44AD",
                      command=self._valider).pack(side="right", expand=True, padx=(5, 0))

    def _valider_champs(self, _event=None):
        """[V7] Valide chaque champ modifiable par regex en temps réel."""
        for (valide, msg), lbl in [
            (valider_nom(self.e_nom.get().strip()),               self.lbl_nom),
            (valider_prix(self.e_prix_achat.get().strip()),       self.lbl_pa),
            (valider_prix(self.e_prix_vente.get().strip()),       self.lbl_pv),
            (valider_qte(self.e_seuil.get().strip(), False),      self.lbl_seuil),
        ]:
            lbl.configure(text=msg, text_color=COULEUR_VALIDE if valide else COULEUR_INVALIDE)

    def _valider(self):
        nom    = self.e_nom.get().strip()
        pa_txt = self.e_prix_achat.get().strip().replace(",", ".")
        pv_txt = self.e_prix_vente.get().strip().replace(",", ".")
        s_txt  = self.e_seuil.get().strip() or "5"

        erreurs = []
        for ok, msg in [
            valider_nom(nom),
            valider_prix(pa_txt),
            valider_prix(pv_txt),
            valider_qte(s_txt, False),
        ]:
            if not ok:
                erreurs.append(msg)

        if erreurs:
            messagebox.showerror("Erreur de saisie", "\n".join(erreurs), parent=self)
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
