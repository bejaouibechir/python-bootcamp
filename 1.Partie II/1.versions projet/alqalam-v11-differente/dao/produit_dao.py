"""DAO des produits."""

from __future__ import annotations

from dao.base_dao import BaseDAO
from models.produit import Produit


class ProduitDAO(BaseDAO):
    """CRUD SQL des produits."""

    def inserer(self, produit: Produit) -> None:
        sql = """
            INSERT INTO produit (ref, nom, categorie, prix_achat, prix_vente, qte, seuil_min)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        with self._session() as conn:
            conn.execute(
                sql,
                (
                    produit.ref,
                    produit.nom,
                    produit.categorie,
                    produit.prix_achat,
                    produit.prix_vente,
                    produit.qte,
                    produit.seuil_min,
                ),
            )

    def get_par_ref(self, ref: str) -> Produit | None:
        with self._session() as conn:
            row = conn.execute("SELECT * FROM produit WHERE ref = ?", (ref,)).fetchone()
        return Produit(**dict(row)) if row else None

    def lister_tous(self) -> list[Produit]:
        with self._session() as conn:
            rows = conn.execute("SELECT * FROM produit ORDER BY nom").fetchall()
        return [Produit(**dict(row)) for row in rows]

    def mettre_a_jour_qte(self, ref: str, nouvelle_qte: int) -> None:
        sql = """
            UPDATE produit
            SET qte = ?, date_modif = datetime('now')
            WHERE ref = ?
        """
        with self._session() as conn:
            conn.execute(sql, (nouvelle_qte, ref))

    def mettre_a_jour_complet(self, produit: Produit) -> None:
        sql = """
            UPDATE produit
            SET nom = ?, categorie = ?, prix_achat = ?, prix_vente = ?,
                qte = ?, seuil_min = ?, date_modif = datetime('now')
            WHERE ref = ?
        """
        with self._session() as conn:
            conn.execute(
                sql,
                (
                    produit.nom,
                    produit.categorie,
                    produit.prix_achat,
                    produit.prix_vente,
                    produit.qte,
                    produit.seuil_min,
                    produit.ref,
                ),
            )

    def supprimer(self, ref: str) -> None:
        with self._session() as conn:
            conn.execute("DELETE FROM produit WHERE ref = ?", (ref,))

    def en_alerte(self) -> list[Produit]:
        with self._session() as conn:
            rows = conn.execute("SELECT * FROM produit WHERE qte <= seuil_min ORDER BY qte").fetchall()
        return [Produit(**dict(row)) for row in rows]
