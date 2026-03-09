# [V3 - Compréhensions] Tableau de bord avec statistiques en temps réel.
# Toutes les données affichées proviennent des méthodes en compréhensions
# ajoutées dans StockService.

import customtkinter as ctk
from config import COULEUR_PRIMAIRE, COULEUR_ALERTE, COULEUR_OK, COULEUR_ORANGE, COULEUR_TEXTE


class RapportFrame(ctk.CTkFrame):
    """
    Onglet "Tableau de bord" — KPIs + statistiques par catégorie + top 5.

    Se met à jour automatiquement via rafraichir() appelé depuis app.py
    après chaque opération de stock.
    """

    def __init__(self, parent, stock_service):
        super().__init__(parent, fg_color="transparent")
        self.stock = stock_service
        self._construire()
        self.rafraichir()

    # ── Construction ──────────────────────────────────────────────────────

    def _construire(self):
        ctk.CTkLabel(self, text="📊 Tableau de Bord",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COULEUR_PRIMAIRE).pack(anchor="w", padx=15, pady=(10, 5))

        # Zone des KPIs (3 cartes côte à côte)
        self._construire_kpis()

        # Zone inférieure : catégories à gauche, top 5 à droite
        zone_bas = ctk.CTkFrame(self, fg_color="transparent")
        zone_bas.pack(fill="both", expand=True, padx=15, pady=5)
        zone_bas.columnconfigure(0, weight=3)
        zone_bas.columnconfigure(1, weight=2)

        self._construire_categories(zone_bas)
        self._construire_top5(zone_bas)

    def _construire_kpis(self):
        """Trois cartes de KPI : nb produits, valeur totale, nb alertes."""
        zone = ctk.CTkFrame(self, fg_color="transparent")
        zone.pack(fill="x", padx=15, pady=8)

        # On stocke les labels pour les mettre à jour dans rafraichir()
        self._kpi_labels = {}

        infos = [
            ("produits",  "📦 Produits",      COULEUR_PRIMAIRE),
            ("valeur",    "💰 Valeur Stock",   "#8E44AD"),
            ("alertes",   "⚠️  Alertes",       COULEUR_ALERTE),
        ]
        for i, (key, titre, couleur) in enumerate(infos):
            carte = ctk.CTkFrame(zone, fg_color=couleur, corner_radius=10)
            carte.grid(row=0, column=i, padx=8, sticky="ew")
            zone.columnconfigure(i, weight=1)

            ctk.CTkLabel(carte, text=titre,
                         font=ctk.CTkFont(size=12),
                         text_color="white").pack(pady=(12, 2))

            lbl_val = ctk.CTkLabel(carte, text="—",
                                    font=ctk.CTkFont(size=26, weight="bold"),
                                    text_color="white")
            lbl_val.pack(pady=(0, 12))
            self._kpi_labels[key] = lbl_val

    def _construire_categories(self, parent):
        """Tableau des statistiques par catégorie."""
        cadre = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
        cadre.grid(row=0, column=0, padx=(0, 6), sticky="nsew", pady=4)

        ctk.CTkLabel(cadre, text="📂 Par catégorie",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COULEUR_PRIMAIRE).pack(anchor="w", padx=12, pady=(10, 4))

        # Frame scrollable pour les lignes de catégories
        self._frame_cats = ctk.CTkScrollableFrame(cadre, fg_color="transparent")
        self._frame_cats.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _construire_top5(self, parent):
        """Top 5 des produits par valeur de stock."""
        cadre = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
        cadre.grid(row=0, column=1, padx=(6, 0), sticky="nsew", pady=4)

        ctk.CTkLabel(cadre, text="🏆 Top 5 — Valeur stock",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COULEUR_PRIMAIRE).pack(anchor="w", padx=12, pady=(10, 4))

        self._frame_top5 = ctk.CTkScrollableFrame(cadre, fg_color="transparent")
        self._frame_top5.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ── Données ───────────────────────────────────────────────────────────

    def rafraichir(self):
        """
        Recharge toutes les statistiques depuis le service.
        [V3] Utilise stats_categories(), valeur_totale_stock(), top_valeur()
        — toutes basées sur des compréhensions.
        """
        # ── KPIs ─────────────────────────────────────────────────────────
        nb       = len(self.stock)                          # __len__
        valeur   = self.stock.valeur_totale_stock()
        alertes  = self.stock.nb_alertes()

        self._kpi_labels["produits"].configure(text=str(nb))
        self._kpi_labels["valeur"].configure(text=f"{valeur:.0f} TND")
        self._kpi_labels["alertes"].configure(
            text=str(alertes) if alertes > 0 else "✅ 0"
        )

        # ── Catégories ────────────────────────────────────────────────────
        # Vider le contenu précédent
        for w in self._frame_cats.winfo_children():
            w.destroy()

        # [V3] stats_categories() renvoie un dict comprehension
        stats = self.stock.stats_categories()
        for cat, s in stats.items():
            self._ligne_categorie(cat, s)

        # ── Top 5 ─────────────────────────────────────────────────────────
        for w in self._frame_top5.winfo_children():
            w.destroy()

        # [V3] top_valeur() utilise sorted() + slicing
        for rang, p in enumerate(self.stock.top_valeur(5), start=1):
            self._ligne_top5(rang, p)

    def _ligne_categorie(self, cat: str, stats: dict):
        """Affiche une ligne de statistique pour une catégorie."""
        row = ctk.CTkFrame(self._frame_cats, fg_color="#F8F9FA", corner_radius=6)
        row.pack(fill="x", pady=3)

        icone = "⚠️" if stats["nb_alertes"] > 0 else "✅"
        ctk.CTkLabel(row, text=f"{icone}  {cat}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COULEUR_TEXTE,
                     width=140, anchor="w").pack(side="left", padx=10, pady=8)

        ctk.CTkLabel(row, text=f"{stats['nb_produits']} produits",
                     font=ctk.CTkFont(size=11),
                     text_color="#7F8C8D").pack(side="left", padx=6)

        ctk.CTkLabel(row, text=f"{stats['valeur_totale']:.2f} TND",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#8E44AD").pack(side="right", padx=10)

        if stats["nb_alertes"] > 0:
            ctk.CTkLabel(row, text=f"⚠️ {stats['nb_alertes']} alerte(s)",
                         font=ctk.CTkFont(size=10),
                         text_color=COULEUR_ALERTE).pack(side="right", padx=4)

    def _ligne_top5(self, rang: int, produit):
        """Affiche une ligne du top 5."""
        medailles = {1: "🥇", 2: "🥈", 3: "🥉"}
        medaille  = medailles.get(rang, f"  {rang}.")

        row = ctk.CTkFrame(self._frame_top5, fg_color="#F8F9FA", corner_radius=6)
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(row, text=medaille, font=ctk.CTkFont(size=14),
                     width=30).pack(side="left", padx=8, pady=8)

        ctk.CTkLabel(row, text=produit.nom,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COULEUR_TEXTE,
                     anchor="w").pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(row, text=f"{produit.valeur_stock():.2f} TND",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COULEUR_PRIMAIRE).pack(side="right", padx=10)
