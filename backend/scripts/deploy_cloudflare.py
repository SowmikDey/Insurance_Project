"""
deploy_cloudflare.py
────────────────────
Deploys the BimaGyan AI inference endpoint to Cloudflare Workers AI.

Usage:
    cd c:\\Projects\\Insurance_Project
    python backend/scripts/deploy_cloudflare.py
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLOUDFLARE_DIR = ROOT_DIR / "cloudflare"
BACKEND_DIR = ROOT_DIR / "backend"
ENV_PATH = BACKEND_DIR / ".env"


def run_cmd(cmd, cwd=None):
    print(f"\n→ Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=cwd or CLOUDFLARE_DIR, shell=True)
    if res.returncode != 0:
        print(f"Command failed with code {res.returncode}")
        return False
    return True


def main():
    print("=" * 65)
    print("  BimaGyan AI — Cloudflare Workers AI Deployment")
    print("=" * 65)

    # 1. Check wrangler installation
    print("\n1. Verifying Wrangler CLI...")
    run_cmd(["npx", "wrangler", "--version"])

    # 2. Check if logged in / prompt login
    print("\n2. Checking Cloudflare authentication...")
    print("If your browser opens, authorize Cloudflare to link your free account.")
    run_cmd(["npx", "wrangler", "whoami"])

    # 3. Check for trained LoRA adapter
    lora_dir = ROOT_DIR / "training_data" / "bimagyan_lora_cloudflare"
    if lora_dir.exists() and (lora_dir / "adapter_model.safetensors").exists():
        print(f"\n3. Found local LoRA adapter in {lora_dir}")
        print("Uploading LoRA adapter to Cloudflare Workers AI...")
        run_cmd([
            "npx", "wrangler", "ai", "finetune", "create",
            "@cf/meta/llama-3.1-8b-instruct",
            "bimagyan-lora",
            str(lora_dir)
        ])
    else:
        print("\n3. Local LoRA adapter files not found yet.")
        print("   Deploying worker with base model first (@cf/meta/llama-3.1-8b-instruct).")
        print("   Once Kaggle finishes training, download the adapter and re-run this script.")

    # 4. Deploy Cloudflare Worker
    print("\n4. Deploying Cloudflare Worker...")
    run_cmd(["npx", "wrangler", "deploy"])

    print("\n" + "=" * 65)
    print("  Cloudflare Worker Deployed Successfully!")
    print("=" * 65)
    print("\nCopy your worker URL (e.g. https://bimagyan-ai.<subdomain>.workers.dev)")
    print("and set it in backend/.env:")
    print("  HF_INFERENCE_URL=https://bimagyan-ai.<subdomain>.workers.dev")


if __name__ == "__main__":
    main()
