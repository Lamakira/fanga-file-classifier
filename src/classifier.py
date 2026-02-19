import json
import logging
import time

from openai import OpenAI

from src.utils import CATEGORIES

logger = logging.getLogger("fanga")

SYSTEM_PROMPT = """You are a document classification assistant for FANGA, an electric motorcycle platform in Cote d'Ivoire.

Classify the given file into exactly one of these categories:
- Contrats: Contracts, lease agreements, partnership agreements
- Factures: Invoices, receipts, payment documents
- Photos: Photographs of stations, equipment, installations
- Rapports: Monthly reports, activity reports, analysis documents
- Exports_donnees: CSV exports, data dumps, transaction logs
- Documents_identite: ID cards, driver's licenses, personal identity documents
- Maintenance: Battery maintenance reports, technical intervention logs, equipment status
- Autre: Anything that doesn't fit the above categories (screenshots, planning, purchase orders, internal docs)

Respond with valid JSON only, with exactly these fields:
- "category": one of the categories listed above
- "confidence": float between 0.0 and 1.0 reflecting genuine certainty
- "description": short kebab-case label suitable for a filename (max 5 words, no accents, lowercase)
- "reasoning": brief explanation of your classification choice"""


class FileClassifier:
    """Classify files using GPT-4o."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def classify(self, metadata: dict, content: dict) -> dict:
        """Send file content to LLM and return structured classification."""
        try:
            result = self._call_llm(metadata, content)
        except Exception as e:
            logger.error(f"Classification failed for {metadata['filename']}: {e}")
            result = self._fallback(str(e))

        # Validate category
        category = result.get("category")
        if category not in CATEGORIES:
            logger.warning(f"Invalid category '{category}', mapping to Autre")
            result["category"] = "Autre"

        # Validate confidence
        try:
            result["confidence"] = float(result.get("confidence", 0.0))
            result["confidence"] = max(0.0, min(1.0, result["confidence"]))
        except (ValueError, TypeError):
            result["confidence"] = 0.0

        return result

    def _call_llm(self, metadata: dict, content: dict, retry: bool = True) -> dict:
        """Make the API call and parse JSON response."""
        user_content = self._build_user_message(metadata, content)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        usage = response.usage
        logger.info(
            f"Tokens used for {metadata['filename']}: "
            f"prompt={usage.prompt_tokens}, completion={usage.completion_tokens}"
        )

        text = response.choices[0].message.content
        time.sleep(0.5)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if retry:
                logger.warning(f"JSON parse failed for {metadata['filename']}, retrying")
                return self._call_llm(metadata, content, retry=False)
            raise

    def _build_user_message(self, metadata: dict, content: dict) -> list:
        """Build the user message content for the API call."""
        file_info = (
            f"Filename: {metadata['filename']}\n"
            f"Extension: {metadata['extension']}\n"
            f"Size: {metadata['size_human']}"
        )

        if content.get("type") == "image":
            ext = metadata["extension"].lstrip(".")
            mime = "jpeg" if ext == "jpg" else ext
            return [
                {"type": "text", "text": f"{file_info}\n\nClassify this file."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{mime};base64,{content['content']}",
                        "detail": "low",
                    },
                },
            ]

        return [
            {
                "type": "text",
                "text": f"{file_info}\n\nFile content:\n{content.get('content', '')}\n\nClassify this file.",
            }
        ]

    @staticmethod
    def _fallback(error: str) -> dict:
        return {
            "category": "Autre",
            "confidence": 0.0,
            "description": "classification-error",
            "reasoning": f"Classification failed: {error}",
        }
