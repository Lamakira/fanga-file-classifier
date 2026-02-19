import logging
import os
from collections import defaultdict

from src.classifier import FileClassifier
from src.extractor import FileExtractor
from src.organizer import FileOrganizer
from src.renamer import FileRenamer
from src.reporter import ReportGenerator
from src.utils import AMBIGUOUS_FOLDER, setup_logging, compute_file_hash

logger = logging.getLogger("fanga")


class Pipeline:
    """Main orchestrator tying all modules together."""

    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        threshold: float = 0.70,
        move: bool = False,
        dry_run: bool = False,
        check_duplicates: bool = False,
        api_key: str = "",
        model: str = "gpt-4o",
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.threshold = threshold
        self.move = move
        self.dry_run = dry_run
        self.check_duplicates = check_duplicates

        self.extractor = FileExtractor()
        self.classifier = FileClassifier(api_key=api_key, model=model)
        self.renamer = FileRenamer()
        self.organizer = FileOrganizer()
        self.reporter = ReportGenerator()

    def run(self) -> dict:
        """Execute the full pipeline. Return the report dict."""
        setup_logging(os.path.join(os.path.dirname(self.output_dir), "logs"))

        # Validate input
        if not os.path.isdir(self.input_dir):
            logger.error(f"Input directory not found: {self.input_dir}")
            return self.reporter.generate([], [{"error": "Input directory not found"}])

        # Create output structure
        self.organizer.setup_output_dirs(self.output_dir)

        # Scan files
        files = self._scan_files()
        if not files:
            logger.warning("No files found in input directory")
            return self.reporter.generate([], [])

        logger.info(f"Found {len(files)} files to process")

        # Duplicate detection
        duplicates = set()
        if self.check_duplicates:
            duplicates = self._find_duplicates(files)

        results = []
        errors = []

        for i, filepath in enumerate(files, 1):
            filename = os.path.basename(filepath)
            logger.info(f"Processing file {i} of {len(files)}: {filename}")

            try:
                result = self._process_file(filepath, filename, duplicates)
                results.append(result)
                logger.info(
                    f"{filename} -> {result['categorie']}/{result['nom_final']} "
                    f"(confidence: {result['confiance']})"
                )
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                errors.append({
                    "nom_original": filename,
                    "erreur": str(e),
                })

        # Generate and save report
        report = self.reporter.generate(results, errors)
        report_path = os.path.join(os.path.dirname(self.output_dir), "rapport_traitement.json")
        self.reporter.save(report, report_path)

        logger.info(
            f"Pipeline complete. {len(results)} files processed, "
            f"{len(errors)} errors, "
            f"{sum(1 for r in results if r.get('statut') == 'ambigu')} ambiguous."
        )

        return report

    def _scan_files(self) -> list[str]:
        """List all non-hidden files in input directory."""
        files = []
        for name in sorted(os.listdir(self.input_dir)):
            if name.startswith("."):
                continue
            path = os.path.join(self.input_dir, name)
            if os.path.isfile(path):
                files.append(path)
        return files

    def _find_duplicates(self, files: list[str]) -> set[str]:
        """Return set of filepaths that are duplicates (keep first occurrence)."""
        hashes = defaultdict(list)
        for f in files:
            h = compute_file_hash(f)
            hashes[h].append(f)

        duplicates = set()
        for paths in hashes.values():
            if len(paths) > 1:
                for dup in paths[1:]:
                    logger.warning(f"Duplicate detected: {os.path.basename(dup)}")
                    duplicates.add(dup)
        return duplicates

    def _process_file(self, filepath: str, filename: str, duplicates: set[str]) -> dict:
        """Process a single file through the pipeline."""
        is_duplicate = filepath in duplicates

        # Extract
        metadata = self.extractor.extract_metadata(filepath)
        content = self.extractor.extract_content(filepath)

        if content.get("type") == "error":
            raise RuntimeError(f"Extraction error: {content.get('error', 'unknown')}")

        # Classify
        classification = self.classifier.classify(metadata, content)

        # Determine effective category
        confidence = classification["confidence"]
        if confidence < self.threshold:
            effective_category = AMBIGUOUS_FOLDER
            status = "ambigu"
        else:
            effective_category = classification["category"]
            status = "succes"

        # Rename
        new_name = self.renamer.generate_name(metadata, classification)
        if is_duplicate:
            base, ext = os.path.splitext(new_name)
            new_name = f"{base}_DOUBLON{ext}"

        # Place file
        if not self.dry_run:
            dest_dir = os.path.join(self.output_dir, effective_category)
            dest_path = os.path.join(dest_dir, new_name)
            dest_path = self.renamer.resolve_collision(dest_path)
            new_name = os.path.basename(dest_path)

            self.organizer.place_file(filepath, self.output_dir, effective_category, new_name, self.move)

            if effective_category == AMBIGUOUS_FOLDER:
                self.organizer.write_ambiguity_note(
                    dest_folder=dest_dir,
                    filename=new_name,
                    original_name=filename,
                    suggested_category=classification["category"],
                    confidence=confidence,
                    threshold=self.threshold,
                    reasoning=classification.get("reasoning", ""),
                )
        else:
            logger.info(f"[DRY-RUN] Would place {filename} -> {effective_category}/{new_name}")

        return {
            "nom_original": filename,
            "nom_final": new_name,
            "categorie": classification["category"],
            "confiance": confidence,
            "statut": status,
            "doublon": is_duplicate,
        }
