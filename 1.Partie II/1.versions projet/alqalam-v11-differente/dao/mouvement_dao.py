"""DAO des mouvements."""

from __future__ import annotations

from dao.base_dao import BaseDAO


class MouvementDAO(BaseDAO):
    """CRUD SQL de l'historique des mouvements."""

    def inserer(
        self,
        ref_produit: str,
        type_mvt: str,
        qte: int,
        qte_avant: int,
        qte_apres: int,
        note: str = "",
    ) -> None:
        sql = """
            INSERT INTO mouvement (ref_produit, type_mvt, qte, qte_avant, qte_apres, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        with self._session() as conn:
            conn.execute(sql, (ref_produit, type_mvt, qte, qte_avant, qte_apres, note))

    def lister(self, ref: str | None = None, type_mvt: str | None = None) -> list[dict]:
        conditions = []
        params = []
        if ref:
            conditions.append("ref_produit = ?")
            params.append(ref)
        if type_mvt:
            conditions.append("type_mvt = ?")
            params.append(type_mvt)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM mouvement {where} ORDER BY date_mvt DESC, id DESC"

        with self._session() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def dernieres(self, limite: int = 20) -> list[dict]:
        with self._session() as conn:
            rows = conn.execute(
                "SELECT * FROM mouvement ORDER BY date_mvt DESC, id DESC LIMIT ?", (limite,)
            ).fetchall()
        return [dict(row) for row in rows]
