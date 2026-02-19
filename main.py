import argparse
import os
import sys

from dotenv import load_dotenv

from src.pipeline import Pipeline


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Fanga Intelligent File Classifier"
    )
    parser.add_argument(
        "--input", type=str, default="./fanga_inbox",
        help="Path to source folder (default: ./fanga_inbox)",
    )
    parser.add_argument(
        "--output", type=str, default="./fanga_organised",
        help="Path to output folder (default: ./fanga_organised)",
    )
    parser.add_argument(
        "--move", action="store_true", default=False,
        help="Move files instead of copying (destructive)",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.70,
        help="Confidence threshold for ambiguous classification (default: 0.70)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=False,
        help="Preview mode, no file operations",
    )
    parser.add_argument(
        "--check-duplicates", action="store_true", default=False,
        help="Enable duplicate detection via MD5 hash",
    )

    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found. Set it in .env or environment.")
        sys.exit(1)

    model = os.getenv("OPENAI_MODEL", "gpt-4o")

    pipeline = Pipeline(
        input_dir=args.input,
        output_dir=args.output,
        threshold=args.threshold,
        move=args.move,
        dry_run=args.dry_run,
        check_duplicates=args.check_duplicates,
        api_key=api_key,
        model=model,
    )

    report = pipeline.run()
    print(f"\nDone. {report['total_fichiers']} files processed.")
    print(f"Report saved to rapport_traitement.json")


if __name__ == "__main__":
    main()
