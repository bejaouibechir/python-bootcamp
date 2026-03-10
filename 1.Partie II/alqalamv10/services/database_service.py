# [V10 - SQLite] DatabaseService — couche d'accès SQLite pour Al Qalam.
#
# Utilise le module sqlite3 de la bibliothèque standard Python (aucun pip requis).
#
# SCHÉMA :
#   Table produits   : catalogue complet (ref, nom, categorie, prix, qte, seuil)
#   Table mouvements : historique complet (id, date, type_mvt, ref, produit, qte, note)
#
# CONCEPTS SQLITE3 DÉMONTRÉS :
#   - sqlite3.connect()           : ouverture connexion (fichier .db)
#   - conn.row_factory            : accès résultats par nom de colonne (dict-like)
#   - PRAGMA foreign_keys         : intégrité référentielle activée
#   - PRAGMA journal_mode = WAL   : Write-Ahead Logging → meilleure concurrence
#   - context manager (with conn) : commit auto ou rollback sur exception
#   - Paramètres ? (positionnels) : protection contre les injections SQL
#   - executescript()             : exécution multi-instructions DDL
#   - CREATE TABLE IF NOT EXISTS  : idempotence du schéma
#   - CREATE INDEX IF NOT EXISTS  : index de performance
#   - SELECT avec filtres WHERE   : requêtes dynamiques paramétrées

import sqlite3
from pathlib import Path
from datetime import datetime


class DatabaseService:
    """
    Couche d'accès à la base de données SQLite pour Al Qalam.

    [V10] Remplace la persistance JSON par SQLite :
      - Table produits   : catalogue complet avec toutes les informations produit
      - Table mouvements : historique complet de tous les mouvements de stock

    Usage :
        db = DatabaseService(DB_PATH)
        db.inserer_produit({"ref": "CRAY-001", "nom": "Crayon HB", ...})
        mouvements = db.charger_mouvements(type_mvt="entree", limite=50)
    """

    # Types autorisés dans la contrainte CHECK SQLite
    TYPES_MVT = ("entree", "sortie", "ajustement", "retour")

    def __init__(self, chemin: Path):
        """
        Initialise la connexion et crée le schéma si nécessaire.

        Args:
            chemin : chemin vers le fichier .db (créé automatiquement)
        """
        self._chemin = Path(chemin)
        self._chemin.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ── Connexion ─────────────────────────────────────────────────────────

    def _connexion(self) -> sqlite3.Connection:
        """
        Ouvre une connexion SQLite configurée.

        row_factory = sqlite3.Row → les lignes sont accessibles par nom de colonne
        PRAGMA foreign_keys = ON  → intégrité référentielle activée
        PRAGMA journal_mode = WAL → performances en lecture/écriture simultanées
        """
        conn = sqlite3.connect(str(self._chemin))
        conn.row_factory = sqlite3.Row          # accès résultat["ref"] au lieu de résultat[0]
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    # ── Schéma ────────────────────────────────────────────────────────────

    def _init_schema(self) -> None:
        """
        Crée les tables et index si elles n'existent pas (idempotent).

        executescript() permet d'exécuter plusieurs instructions SQL d'un coup.
        CREATE TABLE IF NOT EXISTS garantit qu'on ne recrée pas une table existante.
        Les index accélèrent les filtres par date, ref et type_mvt.
        """
        with self._connexion() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS produits (
                    ref        TEXT PRIMARY KEY,
                    nom        TEXT NOT NULL,
                    categorie  TEXT NOT NULL,
                    prix_achat REAL NOT NULL CHECK(prix_achat >= 0),
                    prix_vente REAL NOT NULL CHECK(prix_vente >= 0),
                    qte        INTEGER NOT NULL DEFAULT 0 CHECK(qte >= 0),
                    seuil_min  INTEGER NOT NULL DEFAULT 5 CHECK(seuil_min >= 0)
                );

                CREATE TABLE IF NOT EXISTS mouvements (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    date      TEXT NOT NULL,
                    type_mvt  TEXT NOT NULL,
                    ref       TEXT NOT NULL,
                    produit   TEXT NOT NULL,
                    qte       INTEGER NOT NULL CHECK(qte > 0),
                    note      TEXT DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS idx_mvt_date    ON mouvements(date);
                CREATE INDEX IF NOT EXISTS idx_mvt_ref     ON mouvements(ref);
                CREATE INDEX IF NOT EXISTS idx_mvt_type    ON mouvements(type_mvt);
            """)

    # ══════════════════════════════════════════════════════════════════════
    # PRODUITS
    # ══════════════════════════════════════════════════════════════════════

    def charger_produits(self) -> list[dict]:
        """
        Charge tous les produits depuis la base, triés par référence.

        Returns:
            Liste de dicts avec les clés : ref, nom, categorie,
            prix_achat, prix_vente, qte, seuil_min
        """
        with self._connexion() as conn:
            rows = conn.execute(
                "SELECT * FROM produits ORDER BY ref"
            ).fetchall()
            return [dict(row) for row in rows]

    def inserer_produit(self, p: dict) -> None:
        """
        Insère un nouveau produit dans la base.

        Args:
            p : dict avec les clés ref, nom, categorie, prix_achat, prix_vente, qte, seuil_min

        Raises:
            sqlite3.IntegrityError si la ref existe déjà (PRIMARY KEY violation)
        """
        with self._connexion() as conn:
            conn.execute(
                """INSERT INTO produits
                   (ref, nom, categorie, prix_achat, prix_vente, qte, seuil_min)
                   VALUES (:ref, :nom, :categorie, :prix_achat, :prix_vente, :qte, :seuil_min)""",
                p
            )

    def mettre_a_jour_produit(self, p: dict) -> None:
        """
        Met à jour toutes les colonnes d'un produit existant.

        Args:
            p : dict avec les mêmes clés que inserer_produit()
        """
        with self._connexion() as conn:
            conn.execute(
                """UPDATE produits
                   SET nom=:nom, categorie=:categorie,
                       prix_achat=:prix_achat, prix_vente=:prix_vente,
                       qte=:qte, seuil_min=:seuil_min
                   WHERE ref=:ref""",
                p
            )

    def mettre_a_jour_qte(self, ref: str, qte: int) -> None:
        """
        Met à jour uniquement la quantité d'un produit (après mouvement).

        Requête ciblée, plus efficace qu'un UPDATE complet.
        """
        with self._connexion() as conn:
            conn.execute(
                "UPDATE produits SET qte=? WHERE ref=?",
                (qte, ref)
            )

    def supprimer_produit(self, ref: str) -> None:
        """Supprime un produit par sa référence."""
        with self._connexion() as conn:
            conn.execute("DELETE FROM produits WHERE ref=?", (ref,))

    def ref_existe(self, ref: str) -> bool:
        """Vérifie si une référence produit existe dans la base."""
        with self._connexion() as conn:
            row = conn.execute(
                "SELECT 1 FROM produits WHERE ref=?", (ref,)
            ).fetchone()
            return row is not None

    # ══════════════════════════════════════════════════════════════════════
    # MOUVEMENTS
    # ══════════════════════════════════════════════════════════════════════

    def inserer_mouvement(self, m: dict) -> None:
        """
        Insère un mouvement dans l'historique.

        Args:
            m : dict avec les clés date, type_mvt, ref, produit, qte, note
        """
        with self._connexion() as conn:
            conn.execute(
                """INSERT INTO mouvements (date, type_mvt, ref, produit, qte, note)
                   VALUES (:date, :type_mvt, :ref, :produit, :qte, :note)""",
                m
            )

    def charger_mouvements(
        self,
        type_mvt:   str | None = None,
        ref:        str | None = None,
        date_debut: str | None = None,
        date_fin:   str | None = None,
        limite:     int | None = None,
    ) -> list[dict]:
        """
        Charge les mouvements avec filtres optionnels.

        Construire la requête WHERE dynamiquement selon les filtres fournis :
          - type_mvt  : filtrer par type ("entree", "sortie", ...)
          - ref       : filtrer par référence produit
          - date_debut: mouvements >= cette date (format ISO "YYYY-MM-DD")
          - date_fin  : mouvements <= cette date (format ISO "YYYY-MM-DD")
          - limite    : nombre maximum de résultats retournés

        Returns:
            Liste de dicts avec les clés : id, date, type_mvt, ref, produit, qte, note
        """
        conditions: list[str] = []
        params:     list      = []

        if type_mvt:
            conditions.append("type_mvt = ?")
            params.append(type_mvt)
        if ref:
            conditions.append("ref = ?")
            params.append(ref)
        if date_debut:
            conditions.append("date >= ?")
            params.append(date_debut)
        if date_fin:
            # date_fin au format YYYY-MM-DD → on ajoute T23:59:59 pour couvrir la journée
            params.append(date_fin + "T23:59:59")
            conditions.append("date <= ?")

        clause_where  = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        clause_limit  = f"LIMIT {limite}" if limite else ""

        sql = f"SELECT * FROM mouvements {clause_where} ORDER BY date DESC {clause_limit}"

        with self._connexion() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def nb_mouvements(self) -> int:
        """Retourne le nombre total de mouvements enregistrés."""
        with self._connexion() as conn:
            return conn.execute("SELECT COUNT(*) FROM mouvements").fetchone()[0]

    def stats_mouvements(self) -> dict:
        """
        Agrège les mouvements par type.

        Utilise GROUP BY pour compter et sommer en une seule requête.

        Returns:
            dict { "entree": {"nb": 12, "qte_totale": 450}, ... }
        """
        with self._connexion() as conn:
            rows = conn.execute(
                """SELECT type_mvt, COUNT(*) as nb, SUM(qte) as qte_totale
                   FROM mouvements
                   GROUP BY type_mvt"""
            ).fetchall()
        result = {t: {"nb": 0, "qte_totale": 0} for t in self.TYPES_MVT}
        for row in rows:
            result[row["type_mvt"]] = {
                "nb": row["nb"],
                "qte_totale": row["qte_totale"] or 0,
            }
        return result

    def refs_distinctes(self) -> list[str]:
        """Retourne la liste triée des références ayant au moins un mouvement."""
        with self._connexion() as conn:
            rows = conn.execute(
                "SELECT DISTINCT ref FROM mouvements ORDER BY ref"
            ).fetchall()
            return [row["ref"] for row in rows]

    # ── Migration depuis JSON ──────────────────────────────────────────────

    def migrer_depuis_json(self, chemin_json: Path) -> int:
        """
        Migre les données d'un stock.json existant vers SQLite.

        Si le fichier JSON existe et que la table produits est vide,
        importe les produits et renomme le JSON en .json.bak.

        Args:
            chemin_json : chemin du fichier stock.json à migrer

        Returns:
            Nombre de produits migrés (0 si aucune migration effectuée)
        """
        import json

        if not chemin_json.exists():
            return 0

        # Ne migrer que si la table est vide (première utilisation)
        with self._connexion() as conn:
            nb = conn.execute("SELECT COUNT(*) FROM produits").fetchone()[0]
        if nb > 0:
            return 0

        try:
            data = json.loads(chemin_json.read_text(encoding="utf-8"))
            nb_migres = 0
            for d in data:
                try:
                    self.inserer_produit(d)
                    nb_migres += 1
                except sqlite3.IntegrityError:
                    pass  # ref déjà présente → ignorer
            # Renommer le JSON pour éviter une double migration au prochain lancement
            chemin_json.rename(chemin_json.with_suffix(".json.bak"))
            return nb_migres
        except Exception as e:
            print(f"[DatabaseService] Erreur migration JSON : {e}", flush=True)
            return 0
