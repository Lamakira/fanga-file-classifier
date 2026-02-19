import hashlib
import logging
import os
import re
import unicodedata


CATEGORIES = [
    "Contrats",
    "Factures",
    "Photos",
    "Rapports",
    "Exports_donnees",
    "Documents_identite",
    "Maintenance",
    "Autre",
]

AMBIGUOUS_FOLDER = "A_verifier"

TEXT_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".txt"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def setup_logging(log_dir: str) -> logging.Logger:
    """Configure structured logging to file and console."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "pipeline.log")

    logger = logging.getLogger("fanga")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def compute_file_hash(filepath: str) -> str:
    """Return MD5 hash of file content."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def sanitize_description(text: str) -> str:
    """Clean and normalize a description string for use in filenames."""
    # Remove accents
    nfkd = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in nfkd if not unicodedata.combining(c))

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")

    return text[:50]
