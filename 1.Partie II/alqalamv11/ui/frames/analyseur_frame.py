# [V7 - Regex] AnalyseurFrame — onglet d'analyse du journal par expressions régulières.
#
# FONCTIONNALITÉS :
#   1. Affichage du journal brut formaté (texte multiligne)
#   2. Statistiques extraites par regex (nb opérations par type, erreurs, refs actives)
#   3. Barre de recherche regex — filtre les lignes en temps réel (<KeyRelease>)
#   4. Filtre par type d'opération (boutons radio)
#   5. Filtre erreurs uniquement
#
# CONCEPTS REGEX ILLUSTRÉS :
#   - re.findall()    → compter succès/erreurs
#   - re.finditer()   → groupes nommés pour parser les opérations
#   - re.MULTILINE    → chercher dans les lignes du log
#   - re.compile()    → patterns pré-compilés réutilisés à chaque filtrage
#   - re.error        → gestion regex invalide (feedback utilisateur)

import re
import threading
import customtkinter as ctk
from tkinter import scrolledtext

from config import (
    COULEUR_PRIMAIRE, COULEUR_OK, COULEUR_ALERTE,
    COULEUR_ORANGE, COULEUR_FOND,
)
from services.log_parser import LogParser

COULEUR_VIOLET = "#8E44AD"
POLL_MS = 3000   # rafraîchissement toutes les 3 secondes


class AnalyseurFrame(ctk.CTkFrame):
    """
    [V7] Onglet d'analyse du journal par regex.

    Reçoit le StockService pour accéder à son JournalService.
    Instancie un LogParser qui fait tout le travail regex côté service.
    """

    def __init__(self, parent, stock_service):
        super().__init__(parent, fg_color=COULEUR_FOND, corner_radius=0)
        self._stock   = stock_service
        self._parser  = LogParser(stock_service.journal)
        self._polling = True
        self._construire()
        self._demarrer_polling()

    # ── Construction UI ────────────────────────────────────────────────────

    def _construire(self):
        """Construit l'interface en deux colonnes : stats (gauche) + log (droite)."""

        # ── En-tête ──────────────────────────────────────────────────────
        entete = ctk.CTkFrame(self, fg_color=COULEUR_VIOLET, height=40, corner_radius=0)
        entete.pack(fill="x")
        entete.pack_propagate(False)
        ctk.CTkLabel(
            entete,
            text="🔍  Analyseur de journal — Expressions régulières  [V7]",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="white",
        ).pack(side="left", padx=15)

        # ── Corps principal ───────────────────────────────────────────────
        corps = ctk.CTkFrame(self, fg_color="transparent")
        corps.pack(fill="both", expand=True, padx=10, pady=8)

        # Colonne gauche : stats + filtres
        self._colonne_gauche(corps)
        # Colonne droite : journal brut + recherche
        self._colonne_droite(corps)

    def _colonne_gauche(self, parent):
        col = ctk.CTkFrame(parent, width=280, fg_color="white", corner_radius=8)
        col.pack(side="left", fill="y", padx=(0, 8))
        col.pack_propagate(False)

        # -- Titre stats
        ctk.CTkLabel(col, text="📊 Statistiques regex",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COULEUR_PRIMAIRE).pack(pady=(12, 6), padx=12, anchor="w")

        # Bloc KPIs
        self.kpi_frame = ctk.CTkFrame(col, fg_color="#F0F4F8", corner_radius=6)
        self.kpi_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.lbl_total   = self._kpi(self.kpi_frame, "Total opérations", "—")
        self.lbl_succes  = self._kpi(self.kpi_frame, "Succès ✅",        "—", COULEUR_OK)
        self.lbl_erreurs = self._kpi(self.kpi_frame, "Erreurs ❌",       "—", COULEUR_ALERTE)

        # -- Répartition par type
        ctk.CTkLabel(col, text="Répartition par type",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#7F8C8D").pack(padx=12, anchor="w")
        self.lbl_repartition = ctk.CTkLabel(
            col, text="—", justify="left", anchor="w",
            font=ctk.CTkFont(size=11), text_color=COULEUR_PRIMAIRE,
        )
        self.lbl_repartition.pack(padx=16, pady=(2, 8), anchor="w")

        # -- Références actives
        ctk.CTkLabel(col, text="Références les plus actives",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#7F8C8D").pack(padx=12, anchor="w")
        self.lbl_refs = ctk.CTkLabel(
            col, text="—", justify="left", anchor="w",
            font=ctk.CTkFont(size=11), text_color=COULEUR_PRIMAIRE,
        )
        self.lbl_refs.pack(padx=16, pady=(2, 12), anchor="w")

        # ── Filtres rapides ───────────────────────────────────────────────
        ctk.CTkLabel(col, text="🎯 Filtres rapides",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COULEUR_PRIMAIRE).pack(pady=(6, 4), padx=12, anchor="w")

        filtres = [
            ("Tout afficher",   None,          COULEUR_PRIMAIRE),
            ("📥 Entrées",      "entree",       COULEUR_OK),
            ("📤 Sorties",      "sortie",       COULEUR_ALERTE),
            ("⚖️ Ajustements", "ajustement",   COULEUR_ORANGE),
            ("↩️ Retours",     "retour",       COULEUR_ORANGE),
            ("➕ Ajouts",       "ajout",        COULEUR_PRIMAIRE),
            ("❌ Erreurs seul.", "__erreurs__",  COULEUR_ALERTE),
        ]

        for label, filtre, couleur in filtres:
            ctk.CTkButton(
                col, text=label, fg_color=couleur, height=28,
                font=ctk.CTkFont(size=11),
                command=lambda f=filtre: self._appliquer_filtre(f),
            ).pack(fill="x", padx=12, pady=2)

        ctk.CTkButton(
            col, text="🔄 Rafraîchir", fg_color="#7F8C8D", height=28,
            font=ctk.CTkFont(size=11),
            command=self.rafraichir,
        ).pack(fill="x", padx=12, pady=(8, 4))

    def _colonne_droite(self, parent):
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.pack(side="left", fill="both", expand=True)

        # -- Barre de recherche regex [V7]
        barre = ctk.CTkFrame(col, fg_color="white", corner_radius=8, height=50)
        barre.pack(fill="x", pady=(0, 6))
        barre.pack_propagate(False)

        ctk.CTkLabel(barre, text="🔎 Recherche regex :",
                     font=ctk.CTkFont(size=12), text_color=COULEUR_PRIMAIRE).pack(
            side="left", padx=(12, 6), pady=10)

        self.e_recherche = ctk.CTkEntry(
            barre, placeholder_text="ex: CRAY|STYL  ou  entree  ou  ❌",
            height=32, width=300,
        )
        self.e_recherche.pack(side="left", padx=(0, 8), pady=9)
        self.e_recherche.bind("<KeyRelease>", self._recherche_live)

        # Indicateur de validité regex
        self.lbl_regex_statut = ctk.CTkLabel(
            barre, text="", font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        )
        self.lbl_regex_statut.pack(side="left", padx=4)

        self.chk_casse = ctk.CTkCheckBox(
            barre, text="Insensible casse",
            font=ctk.CTkFont(size=11),
            command=self._recherche_live,
        )
        self.chk_casse.pack(side="left", padx=8)
        self.chk_casse.select()   # coché par défaut

        # -- Zone de log
        log_frame = ctk.CTkFrame(col, fg_color="white", corner_radius=8)
        log_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(log_frame, text="📄 Journal formaté",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEUR_PRIMAIRE).pack(anchor="w", padx=12, pady=(8, 4))

        self.lbl_nb_lignes = ctk.CTkLabel(
            log_frame, text="", font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        )
        self.lbl_nb_lignes.pack(anchor="w", padx=12)

        # Zone texte scrollable (widget tkinter classique pour monospace)
        self.txt_log = scrolledtext.ScrolledText(
            log_frame, wrap="none", state="disabled",
            font=("Consolas", 9), bg="#F8F9FA", fg="#2C3E50",
            relief="flat", padx=8, pady=4,
        )
        self.txt_log.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # Tags de couleur pour les lignes ✅/❌
        self.txt_log.tag_config("succes", foreground="#1E8449")
        self.txt_log.tag_config("erreur", foreground="#C0392B")
        self.txt_log.tag_config("neutre", foreground="#2C3E50")

    # ── Helpers ────────────────────────────────────────────────────────────

    def _kpi(self, parent, label, valeur, couleur_val=None) -> ctk.CTkLabel:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=3)
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=11),
                     text_color="#7F8C8D", anchor="w").pack(side="left")
        lbl = ctk.CTkLabel(row, text=valeur,
                            font=ctk.CTkFont(size=13, weight="bold"),
                            text_color=couleur_val or COULEUR_PRIMAIRE)
        lbl.pack(side="right")
        return lbl

    # ── Mise à jour du log dans la zone texte ─────────────────────────────

    def _afficher_lignes(self, lignes: list[str]):
        """Affiche les lignes dans la zone scrollable avec coloration ✅/❌."""
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")

        for ligne in lignes:
            if "❌" in ligne:
                self.txt_log.insert("end", ligne + "\n", "erreur")
            elif "✅" in ligne:
                self.txt_log.insert("end", ligne + "\n", "succes")
            else:
                self.txt_log.insert("end", ligne + "\n", "neutre")

        self.txt_log.configure(state="disabled")
        nb = len(lignes)
        self.lbl_nb_lignes.configure(text=f"{nb} ligne(s) affichée(s)")

    # ── Actions ────────────────────────────────────────────────────────────

    def rafraichir(self):
        """Recrée le LogParser, analyse et affiche le journal complet."""
        self._parser = LogParser(self._stock.journal)
        statut = self._parser.analyser()

        # KPIs
        self.lbl_total.configure(text=str(statut.nb_total))
        self.lbl_succes.configure(text=str(statut.nb_succes))
        self.lbl_erreurs.configure(text=str(statut.nb_erreurs))

        # Répartition
        if statut.par_operation:
            repartition = "\n".join(
                f"  {op:<12} : {n}"
                for op, n in sorted(statut.par_operation.items(), key=lambda x: -x[1])
            )
        else:
            repartition = "  (aucune opération)"
        self.lbl_repartition.configure(text=repartition)

        # Refs actives
        self.lbl_refs.configure(
            text="\n".join(f"  {r}" for r in statut.refs_actives) or "  (aucune)"
        )

        # Log complet
        lignes = statut.texte_brut.splitlines() if statut.texte_brut else []
        self._afficher_lignes(lignes)

    def _recherche_live(self, _event=None):
        """
        [V7] Filtre le journal en temps réel à chaque frappe.

        Utilise LogParser.rechercher(motif) qui appelle re.findall()
        avec re.MULTILINE sur le texte du journal.
        """
        motif         = self.e_recherche.get().strip()
        ignorer_casse = bool(self.chk_casse.get())

        if not motif:
            # Pas de filtre : affiche tout
            self.lbl_regex_statut.configure(text="", text_color="#7F8C8D")
            self.rafraichir()
            return

        # Vérifier si la regex est syntaxiquement valide
        try:
            re.compile(motif)
            self.lbl_regex_statut.configure(text="✓ regex valide", text_color=COULEUR_OK)
        except re.error as exc:
            self.lbl_regex_statut.configure(
                text=f"⚠ regex invalide : {exc}", text_color=COULEUR_ALERTE,
            )
            return

        lignes = self._parser.rechercher(motif, ignorer_casse=ignorer_casse)
        self._afficher_lignes(lignes)

    def _appliquer_filtre(self, type_op):
        """
        Filtre le journal par type d'opération ou affiche les erreurs seulement.

        Utilise LogParser.extraire_par_operation() ou recherche ❌.
        """
        if type_op is None:
            self.rafraichir()
        elif type_op == "__erreurs__":
            lignes = self._parser.rechercher("❌", ignorer_casse=False)
            self._afficher_lignes(lignes)
        else:
            lignes = self._parser.extraire_par_operation(type_op)
            self._afficher_lignes(lignes)

    # ── Polling ────────────────────────────────────────────────────────────

    def _demarrer_polling(self):
        """Rafraîchit l'onglet toutes les POLL_MS ms (thread principal)."""
        if self._polling:
            self.rafraichir()
            self.after(POLL_MS, self._demarrer_polling)

    def arreter_polling(self):
        self._polling = False
