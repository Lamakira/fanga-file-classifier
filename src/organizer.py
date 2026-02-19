import logging
import os
import shutil
from datetime import datetime

from src.utils import CATEGORIES, AMBIGUOUS_FOLDER

logger = logging.getLogger("fanga")


class FileOrganizer:
    """Create directory structure and place files."""

    def setup_output_dirs(self, output_base: str) -> None:
        """Create all category subdirectories and A_verifier."""
        for category in CATEGORIES:
            os.makedirs(os.path.join(output_base, category), exist_ok=True)
        os.makedirs(os.path.join(output_base, AMBIGUOUS_FOLDER), exist_ok=True)
        logger.info(f"Output directories created under {output_base}")

    def place_file(
        self,
        source: str,
        output_base: str,
        category: str,
        new_name: str,
        move: bool = False,
    ) -> str:
        """Copy or move file to destination. Return final path."""
        dest_dir = os.path.join(output_base, category)
        dest_path = os.path.join(dest_dir, new_name)

        if move:
            shutil.move(source, dest_path)
            logger.info(f"Moved: {source} -> {dest_path}")
        else:
            shutil.copy2(source, dest_path)
            logger.info(f"Copied: {source} -> {dest_path}")

        return dest_path

    def write_ambiguity_note(
        self,
        dest_folder: str,
        filename: str,
        original_name: str,
        suggested_category: str,
        confidence: float,
        threshold: float,
        reasoning: str,
    ) -> None:
        """Write a companion note file for ambiguous classifications."""
        note_name = os.path.splitext(filename)[0] + "_NOTE.txt"
        note_path = os.path.join(dest_folder, note_name)

        content = (
            f"Fichier: {original_name}\n"
            f"Categorie suggeree: {suggested_category}\n"
            f"Confiance: {confidence}\n"
            f"Raison de verification: Confiance inferieure au seuil ({threshold})\n"
            f"Raisonnement du modele: {reasoning}\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Ambiguity note written: {note_path}")
