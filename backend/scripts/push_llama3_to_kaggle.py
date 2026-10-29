"""
push_llama3_to_kaggle.py
────────────────────────
Pushes training_data/bimagyan_llama3_lora_training.ipynb to Kaggle
under the slug `bimagyan-llama3-lora` with the BimaGyan dataset and GPU enabled.
"""

import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
TRAINING_DIR = PROJECT_ROOT / "training_data"
NOTEBOOK_PATH = TRAINING_DIR / "bimagyan_llama3_lora_training.ipynb"

KERNEL_SLUG = "bimagyan-llama-3-lora-training"
KERNEL_TITLE = "BimaGyan Llama-3 LoRA Training"
DATASET_SLUG = "siddharthkumarmishra/bimagyan-training-data"


def _configure_credentials():
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env")
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")
    if not username or not key:
        print("Error: KAGGLE_USERNAME and KAGGLE_KEY must be set in backend/.env")
        sys.exit(1)
    os.environ["KAGGLE_USERNAME"] = username
    if key.startswith("KGAT_"):
        os.environ["KAGGLE_API_TOKEN"] = key
    else:
        os.environ["KAGGLE_KEY"] = key
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_dir.mkdir(parents=True, exist_ok=True)
    if key.startswith("KGAT_"):
        (kaggle_dir / "access_token").write_text(key.strip(), encoding="utf-8")
    else:
        (kaggle_dir / "kaggle.json").write_text(json.dumps({"username": username, "key": key}), encoding="utf-8")
    return username


def main():
    username = _configure_credentials()
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()

    kernel_dir = PROJECT_ROOT / ".kaggle_staging_llama3"
    kernel_dir.mkdir(parents=True, exist_ok=True)

    # Copy notebook
    import shutil
    shutil.copy(NOTEBOOK_PATH, kernel_dir / "bimagyan_llama3_lora_training.ipynb")

    meta = {
        "id": f"{username}/{KERNEL_SLUG}",
        "title": KERNEL_TITLE,
        "code_file": "bimagyan_llama3_lora_training.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "false",
        "enable_gpu": "true",
        "enable_internet": "true",
        "dataset_sources": [DATASET_SLUG],
        "kernel_sources": [],
        "competition_sources": [],
    }

    meta_path = kernel_dir / "kernel-metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Pushing {username}/{KERNEL_SLUG} to Kaggle with GPU...")
    api.kernels_push(str(kernel_dir))

    url = f"https://www.kaggle.com/code/{username}/{KERNEL_SLUG}"
    print(f"Successfully pushed!\nNotebook URL: {url}")


if __name__ == "__main__":
    main()
