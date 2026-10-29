"""
upload_to_kaggle.py
───────────────────
Uploads (or updates) the BimaGyan training dataset to Kaggle so the
bimagyan_qlora_training Kaggle notebook can pull the latest JSONL files.

Supports both Kaggle SDK v1 (legacy apikey) and v2 (access token KGAT_...).
"""

import argparse
import json
import os
import pathlib
import sys
import tempfile
import shutil
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Resolve project root ──────────────────────────────────────────────────────
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TRAINING_DIR = PROJECT_ROOT / "training_data"

DATASET_FILES = [
    TRAINING_DIR / "train.jsonl",
    TRAINING_DIR / "val.jsonl",
    TRAINING_DIR / "dataset_stats.json",
]


def _load_env():
    """Load .env from backend/ if present."""
    env_path = PROJECT_ROOT / "backend" / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)


def _get_credentials():
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    if not username or not key:
        # Try reading from ~/.kaggle/kaggle.json
        kaggle_json = pathlib.Path.home() / ".kaggle" / "kaggle.json"
        if kaggle_json.exists():
            creds = json.loads(kaggle_json.read_text())
            username = username or creds.get("username")
            key = key or creds.get("key")
    if not username or not key:
        logger.error(
            "Kaggle credentials not found. Set KAGGLE_USERNAME and KAGGLE_KEY "
            "environment variables, or create ~/.kaggle/kaggle.json."
        )
        sys.exit(1)
    return username, key


def _configure_credentials(username: str, key: str):
    """Configures environment and files for both legacy API keys and new Access Tokens."""
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = key

    # If it's a Kaggle Access Token (starts with KGAT_ or token format), set KAGGLE_API_TOKEN
    os.environ["KAGGLE_API_TOKEN"] = key

    kaggle_dir = pathlib.Path.home() / ".kaggle"
    kaggle_dir.mkdir(exist_ok=True)

    # 1. Legacy kaggle.json
    creds_path = kaggle_dir / "kaggle.json"
    creds_path.write_text(json.dumps({"username": username, "key": key}))

    # 2. Modern access_token file
    access_token_path = kaggle_dir / "access_token"
    access_token_path.write_text(key.strip())


def _build_dataset_metadata(username: str, title: str, dataset_slug: str) -> dict:
    return {
        "title": title,
        "id": f"{username}/{dataset_slug}",
        "licenses": [{"name": "other"}],
        "resources": [
            {"path": f.name, "description": f.stem.replace("_", " ").title()}
            for f in DATASET_FILES
            if f.exists()
        ],
    }


def upload(title: str = "BimaGyan Insurance Training Dataset", dataset_slug: str = "bimagyan-training-data"):
    _load_env()

    username, key = _get_credentials()
    _configure_credentials(username, key)

    # Validate files exist
    missing = [str(f) for f in DATASET_FILES if not f.exists()]
    if missing:
        logger.warning(
            "Some training files not found — run build_training_dataset.py first:\n  %s",
            "\n  ".join(missing)
        )
        existing = [f for f in DATASET_FILES if f.exists()]
        if not existing:
            logger.error("No training files to upload. Aborting.")
            sys.exit(1)
    else:
        existing = DATASET_FILES

    # Import Kaggle API client (compatible with kaggle 1.x and 2.x)
    try:
        from kaggle import KaggleApi
    except ImportError:
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
        except ImportError:
            try:
                from kaggle.api.kaggle_api_extended import KaggleApiExtended as KaggleApi
            except ImportError:
                logger.error("Kaggle SDK is not installed. Please run: pip install kaggle")
                sys.exit(1)

    api = KaggleApi()
    api.authenticate()

    # Build metadata in a temp staging directory
    staging = pathlib.Path(tempfile.mkdtemp(prefix="bimagyan_kaggle_"))
    try:
        meta = _build_dataset_metadata(username, title, dataset_slug)
        (staging / "dataset-metadata.json").write_text(json.dumps(meta, indent=2))

        for f in existing:
            shutil.copy(f, staging / f.name)
            logger.info("Staged: %s (%s bytes)", f.name, f.stat().st_size)

        dataset_id = f"{username}/{dataset_slug}"

        # Check if dataset already exists
        dataset_exists = False
        try:
            status = api.dataset_status(dataset_id)
            if status:
                dataset_exists = True
        except Exception:
            # 404 or 401 when not found
            dataset_exists = False

        if dataset_exists:
            logger.info("Updating existing dataset: %s", dataset_id)
            result = api.dataset_create_version(
                str(staging),
                version_notes="Automated update from BimaGyan build_training_dataset.py",
                quiet=False,
                convert_to_csv=False,
                delete_old_versions=False,
                dir_mode="skip",
            )
            if hasattr(result, "error") and result.error:
                logger.error("Failed to update dataset: %s", result.error)
                sys.exit(1)
        else:
            logger.info("Creating new dataset: %s", dataset_id)
            result = api.dataset_create_new(
                str(staging),
                public=True,
                quiet=False,
                convert_to_csv=False,
                dir_mode="skip",
            )
            if hasattr(result, "error") and result.error:
                logger.error("Failed to create dataset: %s", result.error)
                sys.exit(1)

        logger.info(
            "\n=======================================================\n"
            " SUCCESS: Dataset uploaded to Kaggle!\n"
            " URL: https://www.kaggle.com/datasets/%s\n"
            "=======================================================\n\n"
            "Next steps:\n"
            "  1. Open Kaggle notebook (bimagyan_qlora_training.ipynb)\n"
            "  2. Add dataset input: %s\n"
            "  3. Set Kaggle Secrets: HF_TOKEN and HF_REPO\n"
            "  4. Run on free P100 GPU\n",
            dataset_id, dataset_id,
        )

    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload BimaGyan training data to Kaggle")
    parser.add_argument(
        "--title",
        default="BimaGyan Insurance Training Dataset",
        help="Dataset title on Kaggle (default: 'BimaGyan Insurance Training Dataset')"
    )
    parser.add_argument(
        "--slug",
        default="bimagyan-training-data",
        help="Dataset slug / identifier (default: bimagyan-training-data)"
    )
    args = parser.parse_args()
    upload(title=args.title, dataset_slug=args.slug)
