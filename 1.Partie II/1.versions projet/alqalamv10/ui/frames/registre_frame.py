# [V6 - Métaclasses] Panneau "Registre" — 5ème onglet de l'application.
#
# Ce panneau démontre visuellement deux concepts de métaclasses :
#
#  1. REGISTRE (RegistreMouvementMeta)
#     → Tableau des types de mouvements auto-enregistrés
#     → Statistiques par type (nb mouvements, quantités)
#     → Inspecter le registre en temps réel
#
#  2. SINGLETON (SingletonMeta)
#     → Démonstrateur interactif : appelle StockService() N fois
#       et prouve que l'id() est toujours identique
#     → Affiche les classes Singleton connues
#
# Pédagogie :
#   L'utilisateur peut cliquer "Créer une instance" plusieurs fois
#   et observer que l'id mémoire ne change jamais → Singleton confirmé.

import customtkinter as ctk
from tkinter import ttk

from config import COULEUR_PRIMAIRE, COULEUR_ALERTE, COULEUR_OK, COULEUR_FOND
from metaclasses.registre import RegistreMouvementMeta
from metaclasses.singleton import SingletonMeta


class RegistreFrame(ctk.CTkFrame):
    """
    Panneau pédagogique — visualise le registre des métaclasses V6.

    Sections :
    ┌────────────────────────────────────────────────────┐
    │  [KPIs]  Types enregistrés | Mouvements totaux     │
    ├──────────────────────┬─────────────────────────────┤
    │  Registre des types  │  Démo Singleton             │
    │  (tableau + stats)   │  (appels + id mémoire)      │
    └──────────────────────┴─────────────────────────────┘
    """

    def __init__(self, parent, stock_service, **kwargs):
        super().__init__(parent, fg_color=COULEUR_FOND, **kwargs)
        self._stock   = stock_service
        self._id_poll = None
        self._nb_appels_singleton = 0   # compteur démo Singleton

        self._construire_ui()
        self._demarrer_polling()

    # ── Construction ───────────────────────────────────────────────────────

    def _construire_ui(self) -> None:
        # En-tête
        entete = ctk.CTkFrame(self, fg_color=COULEUR_PRIMAIRE, corner_radius=8)
        entete.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            entete,
            text="🗂  Registre des Métaclasses — RegistreMouvementMeta & SingletonMeta",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=15, pady=10)

        self._lbl_kpi = ctk.CTkLabel(
            entete, text="", font=ctk.CTkFont(size=11), text_color="#A9CCE3"
        )
        self._lbl_kpi.pack(side="right", padx=15)

        # Bouton rafraîchir
        barre = ctk.CTkFrame(self, fg_color="transparent")
        barre.pack(fill="x", padx=10, pady=4)
        ctk.CTkButton(
            barre, text="🔄 Rafraîchir", command=self.rafraichir,
            fg_color="#2196F3", hover_color="#1565C0", width=140,
        ).pack(side="left")

        # Zone principale : 2 colonnes
        zone = ctk.CTkFrame(self, fg_color="transparent")
        zone.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        zone.columnconfigure(0, weight=3)
        zone.columnconfigure(1, weight=2)

        self._construire_registre(zone)
        self._construire_singleton(zone)

    def _construire_registre(self, parent) -> None:
        """Colonne gauche : tableau du registre des types de mouvements."""
        cadre = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
        cadre.grid(row=0, column=0, padx=(0, 6), sticky="nsew", pady=4)

        ctk.CTkLabel(
            cadre,
            text="📋  RegistreMouvementMeta._registre",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(anchor="w", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            cadre,
            text="Chaque ligne = une sous-classe auto-enregistrée lors de sa définition par Python.",
            font=ctk.CTkFont(size=10),
            text_color="#7F8C8D",
        ).pack(anchor="w", padx=12, pady=(0, 6))

        # Tableau Treeview du registre
        frame_tree = ctk.CTkFrame(cadre, fg_color="#F8F9FA", corner_radius=6)
        frame_tree.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        cols = ("icone", "type_mvt", "classe", "label", "nb_mvts", "qte_totale")
        self._arbre_registre = ttk.Treeview(
            frame_tree, columns=cols, show="headings", height=6
        )
        self._arbre_registre.heading("icone",     text="")
        self._arbre_registre.heading("type_mvt",  text="TYPE_MVT")
        self._arbre_registre.heading("classe",    text="Classe Python")
        self._arbre_registre.heading("label",     text="Label")
        self._arbre_registre.heading("nb_mvts",   text="Nb mvts")
        self._arbre_registre.heading("qte_totale",text="Qté totale")

        self._arbre_registre.column("icone",      width=35,  anchor="center")
        self._arbre_registre.column("type_mvt",   width=100, anchor="center")
        self._arbre_registre.column("classe",     width=160)
        self._arbre_registre.column("label",      width=130)
        self._arbre_registre.column("nb_mvts",    width=70,  anchor="center")
        self._arbre_registre.column("qte_totale", width=80,  anchor="center")

        self._arbre_registre.tag_configure("pair",   background="#F0F4F8")
        self._arbre_registre.tag_configure("impair", background="white")

        self._arbre_registre.pack(fill="both", expand=True, padx=4, pady=4)

        # Explication textuelle sous le tableau
        expl = ctk.CTkFrame(cadre, fg_color="#EBF5FB", corner_radius=6)
        expl.pack(fill="x", padx=8, pady=(4, 8))

        code_txt = (
            "# Fonctionnement de l'auto-enregistrement :\n"
            "class EntreeMouvement(Mouvement):\n"
            "    TYPE_MVT = \"entree\"  # ← RegistreMouvementMeta.__init__() lit ceci\n"
            "    ...                   # et exécute : _registre[\"entree\"] = EntreeMouvement"
        )
        ctk.CTkLabel(
            expl, text=code_txt,
            font=ctk.CTkFont(family="Courier New", size=9),
            text_color="#2C3E50", justify="left",
        ).pack(anchor="w", padx=10, pady=6)

    def _construire_singleton(self, parent) -> None:
        """Colonne droite : démonstrateur du pattern Singleton."""
        cadre = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
        cadre.grid(row=0, column=1, padx=(6, 0), sticky="nsew", pady=4)

        ctk.CTkLabel(
            cadre,
            text="🔒  SingletonMeta — Démo",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(anchor="w", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            cadre,
            text="Cliquez autant de fois que vous voulez :\nStockService() retourne TOUJOURS la même instance.",
            font=ctk.CTkFont(size=10),
            text_color="#7F8C8D",
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Bouton de démo
        ctk.CTkButton(
            cadre,
            text="📞  Appeler StockService()",
            command=self._demo_singleton,
            fg_color="#8E44AD", hover_color="#6C3483",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(padx=12, pady=4, fill="x")

        # Compteur d'appels
        self._lbl_appels = ctk.CTkLabel(
            cadre, text="0 appel(s)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        )
        self._lbl_appels.pack(pady=(8, 0))

        ctk.CTkLabel(
            cadre, text="à StockService()",
            font=ctk.CTkFont(size=10), text_color="#7F8C8D",
        ).pack()

        # Séparateur
        ctk.CTkFrame(cadre, height=1, fg_color="#ECF0F1").pack(fill="x", padx=12, pady=10)

        # Résultat de la comparaison
        ctk.CTkLabel(
            cadre, text="Résultat de la vérification :",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(anchor="w", padx=12)

        self._lbl_id_a = ctk.CTkLabel(
            cadre, text="id(instance_1) = —",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color="#2C3E50",
        )
        self._lbl_id_a.pack(anchor="w", padx=16, pady=2)

        self._lbl_id_b = ctk.CTkLabel(
            cadre, text="id(instance_2) = —",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color="#2C3E50",
        )
        self._lbl_id_b.pack(anchor="w", padx=16, pady=2)

        self._lbl_egal = ctk.CTkLabel(
            cadre, text="",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._lbl_egal.pack(pady=6)

        # Séparateur
        ctk.CTkFrame(cadre, height=1, fg_color="#ECF0F1").pack(fill="x", padx=12, pady=8)

        # Instances Singleton connues
        ctk.CTkLabel(
            cadre, text="Classes sous SingletonMeta :",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COULEUR_PRIMAIRE,
        ).pack(anchor="w", padx=12)

        self._frame_singletons = ctk.CTkScrollableFrame(
            cadre, fg_color="transparent", height=80
        )
        self._frame_singletons.pack(fill="x", padx=8, pady=(4, 10))

        # Explication code
        expl2 = ctk.CTkFrame(cadre, fg_color="#EBF5FB", corner_radius=6)
        expl2.pack(fill="x", padx=8, pady=(0, 10))
        code2 = (
            "class StockService(metaclass=SingletonMeta):\n"
            "    ...\n\n"
            "a = StockService()  # crée l'instance\n"
            "b = StockService()  # retourne la MÊME instance\n"
            "assert a is b       # True ✅"
        )
        ctk.CTkLabel(
            expl2, text=code2,
            font=ctk.CTkFont(family="Courier New", size=9),
            text_color="#2C3E50", justify="left",
        ).pack(anchor="w", padx=10, pady=6)

    # ── Polling ────────────────────────────────────────────────────────────

    def _demarrer_polling(self) -> None:
        self._id_poll = self.after(3000, self._poll)

    def _poll(self) -> None:
        self.rafraichir()
        self._id_poll = self.after(3000, self._poll)

    # ── Mise à jour ────────────────────────────────────────────────────────

    def rafraichir(self) -> None:
        """Recharge le registre et les stats depuis les métaclasses."""
        registre = RegistreMouvementMeta.get_registre()
        stats    = self._stock.stats_par_type()

        # KPIs
        total_mvts = sum(s["nb"] for s in stats.values())
        self._lbl_kpi.configure(
            text=f"{len(registre)} type(s) enregistré(s)  |  {total_mvts} mouvement(s) total"
        )

        # Tableau du registre
        for item in self._arbre_registre.get_children():
            self._arbre_registre.delete(item)

        for i, (type_mvt, classe) in enumerate(sorted(registre.items())):
            s   = stats.get(type_mvt, {"nb": 0, "qte_totale": 0})
            tag = "pair" if i % 2 == 0 else "impair"
            self._arbre_registre.insert("", "end", tags=(tag,), values=(
                classe.ICONE,
                type_mvt,
                classe.__name__,
                classe.LABEL,
                s["nb"],
                s["qte_totale"],
            ))

        # Instances Singleton
        for w in self._frame_singletons.winfo_children():
            w.destroy()

        instances = SingletonMeta.get_instances()
        if instances:
            for cls, inst in instances.items():
                row = ctk.CTkFrame(self._frame_singletons, fg_color="#F0F4F8", corner_radius=4)
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(
                    row,
                    text=f"🔒  {cls.__name__}   →   id = {id(inst)}",
                    font=ctk.CTkFont(family="Courier New", size=9),
                    text_color="#2C3E50",
                ).pack(anchor="w", padx=8, pady=4)
        else:
            ctk.CTkLabel(
                self._frame_singletons,
                text="(aucune instance Singleton encore créée)",
                font=ctk.CTkFont(size=10), text_color="#95A5A6",
            ).pack(anchor="w", padx=8)

    # ── Démo Singleton ────────────────────────────────────────────────────

    def _demo_singleton(self) -> None:
        """
        Appelle StockService() deux fois et compare les id().

        [V6] Démontre que SingletonMeta.__call__() retourne toujours
        la même instance, peu importe le nombre d'appels.
        """
        from services.stock_service import StockService

        self._nb_appels_singleton += 1
        self._lbl_appels.configure(text=f"{self._nb_appels_singleton} appel(s)")

        # Deux appels → doivent retourner la même instance
        instance_a = StockService()
        instance_b = StockService()

        id_a = id(instance_a)
        id_b = id(instance_b)
        meme = instance_a is instance_b

        self._lbl_id_a.configure(text=f"id(instance_1) = {id_a}")
        self._lbl_id_b.configure(text=f"id(instance_2) = {id_b}")

        if meme:
            self._lbl_egal.configure(
                text="✅  instance_1 is instance_2  →  True",
                text_color=COULEUR_OK,
            )
        else:
            self._lbl_egal.configure(
                text="❌  instances différentes !",
                text_color=COULEUR_ALERTE,
            )

        self.rafraichir()

    # ── Arrêt propre ──────────────────────────────────────────────────────

    def arreter_polling(self) -> None:
        if self._id_poll:
            self.after_cancel(self._id_poll)
            self._id_poll = None
