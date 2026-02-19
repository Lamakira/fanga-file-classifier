import logging
import os
import re
from datetime import date

from src.utils import sanitize_description

logger = logging.getLogger("fanga")

FRENCH_MONTHS = {
    "janvier": "01", "fevrier": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "aout": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "decembre": "12",
}


class FileRenamer:
    """Generate normalized filenames."""

    def generate_name(self, metadata: dict, classification: dict) -> str:
        """Return a normalized filename: YYYY-MM-DD_{category}_{description}.{ext}"""
        date_str = self._extract_date(metadata["filename"], classification.get("description", ""))
        category = classification["category"]
        description = sanitize_description(classification.get("description", "unknown"))
        ext = metadata["extension"]

        return f"{date_str}_{category}_{description}{ext}"

    def resolve_collision(self, filepath: str) -> str:
        """Append a counter if file already exists at destination."""
        if not os.path.exists(filepath):
            return filepath

        base, ext = os.path.splitext(filepath)
        counter = 1
        while True:
            new_path = f"{base}_{counter:02d}{ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def _extract_date(self, filename: str, description: str) -> str:
        """Try to extract a date from filename or description."""
        combined = f"{filename} {description}".lower()

        # Remove accents for matching
        combined = combined.replace("e\u0301", "e").replace("u\u0302", "u")

        # Look for full year
        year_match = re.search(r"(20\d{2})", combined)
        year = year_match.group(1) if year_match else None

        # Look for French month name
        month = None
        for name, num in FRENCH_MONTHS.items():
            if name in combined:
                month = num
                break

        if year and month:
            return f"{year}-{month}-01"
        if year:
            return f"{year}-01-01"
        if month:
            return f"{date.today().year}-{month}-01"

        return date.today().strftime("%Y-%m-%d")
