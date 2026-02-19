import unittest
from unittest.mock import MagicMock, patch

from src.classifier import FileClassifier
from src.utils import CATEGORIES


class TestFileClassifier(unittest.TestCase):

    def setUp(self):
        self.classifier = FileClassifier(api_key="test-key")

    @patch.object(FileClassifier, "_call_llm")
    def test_returns_valid_category(self, mock_llm):
        mock_llm.return_value = {
            "category": "Contrats",
            "confidence": 0.95,
            "description": "contrat-test",
            "reasoning": "Test reasoning",
        }
        metadata = {"filename": "test.pdf", "extension": ".pdf", "size_human": "1.0 KB"}
        content = {"type": "text", "content": "contrat de location"}

        result = self.classifier.classify(metadata, content)
        assert result["category"] in CATEGORIES

    @patch.object(FileClassifier, "_call_llm")
    def test_confidence_is_float_between_0_and_1(self, mock_llm):
        mock_llm.return_value = {
            "category": "Factures",
            "confidence": 0.85,
            "description": "facture-test",
            "reasoning": "Test",
        }
        metadata = {"filename": "test.pdf", "extension": ".pdf", "size_human": "1.0 KB"}
        content = {"type": "text", "content": "facture"}

        result = self.classifier.classify(metadata, content)
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0

    @patch.object(FileClassifier, "_call_llm")
    def test_invalid_category_maps_to_autre(self, mock_llm):
        mock_llm.return_value = {
            "category": "InvalidCategory",
            "confidence": 0.5,
            "description": "test",
            "reasoning": "Test",
        }
        metadata = {"filename": "test.pdf", "extension": ".pdf", "size_human": "1.0 KB"}
        content = {"type": "text", "content": "some content"}

        result = self.classifier.classify(metadata, content)
        assert result["category"] == "Autre"

    @patch.object(FileClassifier, "_call_llm")
    def test_empty_content_fallback(self, mock_llm):
        mock_llm.side_effect = Exception("API error")
        metadata = {"filename": "empty.txt", "extension": ".txt", "size_human": "0 B"}
        content = {"type": "text", "content": ""}

        result = self.classifier.classify(metadata, content)
        assert result["category"] == "Autre"
        assert result["confidence"] == 0.0

    @patch.object(FileClassifier, "_call_llm")
    def test_confidence_clamped_above_1(self, mock_llm):
        mock_llm.return_value = {
            "category": "Photos",
            "confidence": 1.5,
            "description": "photo",
            "reasoning": "Test",
        }
        metadata = {"filename": "test.jpg", "extension": ".jpg", "size_human": "1.0 KB"}
        content = {"type": "image", "content": "base64data"}

        result = self.classifier.classify(metadata, content)
        assert result["confidence"] == 1.0

    @patch.object(FileClassifier, "_call_llm")
    def test_confidence_clamped_below_0(self, mock_llm):
        mock_llm.return_value = {
            "category": "Contrats",
            "confidence": -0.5,
            "description": "test",
            "reasoning": "Test",
        }
        metadata = {"filename": "test.pdf", "extension": ".pdf", "size_human": "1.0 KB"}
        content = {"type": "text", "content": "contrat"}

        result = self.classifier.classify(metadata, content)
        assert result["confidence"] == 0.0

    @patch.object(FileClassifier, "_call_llm")
    def test_confidence_as_string(self, mock_llm):
        mock_llm.return_value = {
            "category": "Factures",
            "confidence": "0.85",
            "description": "facture",
            "reasoning": "Test",
        }
        metadata = {"filename": "test.pdf", "extension": ".pdf", "size_human": "1.0 KB"}
        content = {"type": "text", "content": "facture"}

        result = self.classifier.classify(metadata, content)
        assert isinstance(result["confidence"], float)
        assert result["confidence"] == 0.85

    @patch.object(FileClassifier, "_call_llm")
    def test_confidence_non_numeric_falls_to_zero(self, mock_llm):
        mock_llm.return_value = {
            "category": "Factures",
            "confidence": "high",
            "description": "facture",
            "reasoning": "Test",
        }
        metadata = {"filename": "test.pdf", "extension": ".pdf", "size_human": "1.0 KB"}
        content = {"type": "text", "content": "facture"}

        result = self.classifier.classify(metadata, content)
        assert result["confidence"] == 0.0

    @patch.object(FileClassifier, "_call_llm")
    def test_missing_category_falls_to_autre(self, mock_llm):
        mock_llm.return_value = {
            "confidence": 0.5,
            "description": "unknown",
            "reasoning": "Test",
        }
        metadata = {"filename": "test.pdf", "extension": ".pdf", "size_human": "1.0 KB"}
        content = {"type": "text", "content": "something"}

        result = self.classifier.classify(metadata, content)
        assert result["category"] == "Autre"

    @patch.object(FileClassifier, "_call_llm")
    def test_missing_confidence_falls_to_zero(self, mock_llm):
        mock_llm.return_value = {
            "category": "Contrats",
            "description": "contrat",
            "reasoning": "Test",
        }
        metadata = {"filename": "test.pdf", "extension": ".pdf", "size_human": "1.0 KB"}
        content = {"type": "text", "content": "contrat"}

        result = self.classifier.classify(metadata, content)
        assert result["confidence"] == 0.0


if __name__ == "__main__":
    unittest.main()
