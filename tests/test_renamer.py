import os
import re
import tempfile
import unittest

from src.renamer import FileRenamer
from src.utils import sanitize_description


class TestSanitizeDescription(unittest.TestCase):

    def test_removes_accents(self):
        assert sanitize_description("controle qualite") == "controle-qualite"

    def test_removes_special_chars(self):
        assert sanitize_description("hello@world!#2024") == "helloworld2024"

    def test_replaces_spaces_with_hyphens(self):
        assert sanitize_description("contrat location moto") == "contrat-location-moto"

    def test_max_50_chars(self):
        long = "a" * 100
        assert len(sanitize_description(long)) == 50

    def test_lowercase(self):
        assert sanitize_description("FACTURE MARS") == "facture-mars"


class TestFileRenamer(unittest.TestCase):

    def setUp(self):
        self.renamer = FileRenamer()

    def test_format_matches_pattern(self):
        metadata = {"filename": "test.pdf", "extension": ".pdf"}
        classification = {"category": "Contrats", "description": "contrat-test"}
        name = self.renamer.generate_name(metadata, classification)
        assert re.match(r"\d{4}-\d{2}-\d{2}_\w+_.+\.pdf", name)

    def test_extracts_year_from_filename(self):
        metadata = {"filename": "contrat_2024.pdf", "extension": ".pdf"}
        classification = {"category": "Contrats", "description": "contrat-test"}
        name = self.renamer.generate_name(metadata, classification)
        assert name.startswith("2024-01-01")

    def test_extracts_month_only_uses_current_year(self):
        from datetime import date
        metadata = {"filename": "facture_mars.pdf", "extension": ".pdf"}
        classification = {"category": "Factures", "description": "facture-mars"}
        name = self.renamer.generate_name(metadata, classification)
        assert name.startswith(f"{date.today().year}-03-01")

    def test_extracts_year_and_month(self):
        metadata = {"filename": "facture_station_cocody_mars_2024.pdf", "extension": ".pdf"}
        classification = {"category": "Factures", "description": "facture-station-cocody"}
        name = self.renamer.generate_name(metadata, classification)
        assert name.startswith("2024-03-01")

    def test_collision_handling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file to cause collision
            existing = os.path.join(tmpdir, "test.pdf")
            with open(existing, "w") as f:
                f.write("x")

            resolved = self.renamer.resolve_collision(existing)
            assert resolved.endswith("test_01.pdf")

    def test_no_collision(self):
        path = "/tmp/nonexistent_file_abc123.pdf"
        assert self.renamer.resolve_collision(path) == path

    def test_multiple_collisions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "test.pdf")
            first = os.path.join(tmpdir, "test_01.pdf")
            for path in (base, first):
                with open(path, "w") as f:
                    f.write("x")

            resolved = self.renamer.resolve_collision(base)
            assert resolved.endswith("test_02.pdf")

    def test_no_date_info_falls_to_today(self):
        from datetime import date
        metadata = {"filename": "random_file.pdf", "extension": ".pdf"}
        classification = {"category": "Autre", "description": "some-file"}
        name = self.renamer.generate_name(metadata, classification)
        assert name.startswith(date.today().strftime("%Y-%m-%d"))

    def test_empty_description(self):
        metadata = {"filename": "test_2024.pdf", "extension": ".pdf"}
        classification = {"category": "Contrats", "description": ""}
        name = self.renamer.generate_name(metadata, classification)
        assert name.startswith("2024-01-01_Contrats_")
        assert name.endswith(".pdf")


class TestSanitizeEdgeCases(unittest.TestCase):

    def test_empty_string(self):
        assert sanitize_description("") == ""

    def test_only_special_chars(self):
        assert sanitize_description("@#$%^&*!") == ""

    def test_french_accented_chars(self):
        assert sanitize_description("resume general") == "resume-general"

    def test_mixed_accents(self):
        result = sanitize_description("controle qualite superieure")
        assert "controle" in result
        assert "qualite" in result


if __name__ == "__main__":
    unittest.main()
