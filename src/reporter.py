import json
import logging
from datetime import datetime

from src.utils import CATEGORIES

logger = logging.getLogger("fanga")


class ReportGenerator:
    """Generate the final JSON treatment report."""

    def generate(self, results: list[dict], errors: list[dict]) -> dict:
        """Build the report dict from results and errors."""
        # Count files per category
        classes = {cat: 0 for cat in CATEGORIES}
        for r in results:
            cat = r.get("categorie", "Autre")
            if cat in classes:
                classes[cat] += 1

        confidences = [r["confiance"] for r in results if r.get("confiance") is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        ambiguous = sum(1 for r in results if r.get("statut") == "ambigu")
        duplicates = sum(1 for r in results if r.get("doublon", False))

        return {
            "date_execution": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "total_fichiers": len(results) + len(errors),
            "classes": classes,
            "fichiers": results,
            "erreurs": errors,
            "statistiques": {
                "confiance_moyenne": round(avg_confidence, 2),
                "fichiers_ambigus": ambiguous,
                "fichiers_en_erreur": len(errors),
                "doublons_detectes": duplicates,
            },
        }

    def save(self, report: dict, output_path: str) -> None:
        """Write report to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"Report saved to {output_path}")
