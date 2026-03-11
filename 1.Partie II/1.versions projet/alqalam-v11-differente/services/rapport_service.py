"""Service de rapports métier."""

from __future__ import annotations

from datetime import datetime

from alq_io.csv_handler import exporter_stock
from alq_io.excel_handler import exporter_rapport_complet


class RapportService:
    """Centralise la génération des exports métier."""

    def __init__(self, stock_service):
        self.stock_service = stock_service

    def exporter_csv(self, chemin: str) -> int:
        return exporter_stock(chemin, self.stock_service)

    def exporter_excel(self, chemin: str) -> None:
        exporter_rapport_complet(chemin, self.stock_service)

    def nom_fichier_rapport(self, prefixe: str = "rapport_stock") -> str:
        horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefixe}_{horodatage}.xlsx"

