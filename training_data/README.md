# BimaGyan — LLM Training Pipeline

This directory contains scripts, notebook, and generated data files for fine-tuning a domain-specific insurance AI model on all BimaGyan data.

---

## Overview

```
training_data/
├── bimagyan_qlora_training.ipynb   # Kaggle notebook (QLoRA fine-tuning)
├── README.md                       # This file
│
│ ── Generated (git-ignored, reproducible) ──
├── train.jsonl                     # ~1,030 training examples (Alpaca format)
├── val.jsonl                       # ~115 validation examples
└── dataset_stats.json              # Category breakdown & counts
```

> **Note:** `*.jsonl` and `dataset_stats.json` are `.gitignore`-d because they are large and fully reproducible. Regenerate them at any time with the build script below.

---

## Step 1 — Build the Training Dataset

Requires the backend's Python environment with database connectivity.

```bash
cd c:/Projects/Insurance_Project
pip install -r backend/requirements.txt   # if not already installed

# Run the dataset builder (connects to Neon PostgreSQL)
python backend/scripts/build_training_dataset.py
```

This pulls data from:
| Source | Examples |
|---|---|
| IRDAI regulatory facts & DB `PolicyFact` rows | ~119 |
| Policy benefits, exclusions, waiting periods (DB) | ~450 |
| DocumentChunk text (DB) | ~250 |
| Scraped policy comparison JSONs | ~95 |
| Educational module content (15 modules) | ~46 + 40 quiz + 48 advice |
| Glossary definitions (30 terms) | ~90 |
| Practical scenarios & common mistakes | ~45 + 15 |

Output is **Alpaca format** with ChatML wrapping for Qwen2.5-Instruct:
```json
{
  "system": "You are BimaGyan AI...",
  "instruction": "What does co-payment mean?",
  "input": "",
  "output": "Co-payment is...",
  "category": "glossary_definition"
}
```

---

## Step 2 — Upload to Kaggle

```bash
# Set credentials in backend/.env (or export as env vars):
# KAGGLE_USERNAME=your_username
# KAGGLE_KEY=your_api_key

pip install kaggle python-dotenv
python backend/scripts/upload_to_kaggle.py
```

Or upload manually:
1. Go to https://www.kaggle.com/datasets/new
2. Upload `train.jsonl` and `val.jsonl`
3. Name the dataset `bimagyan-training-data`

---

## Step 3 — Fine-tune on Kaggle (Free P100 GPU)

1. Create a new Kaggle notebook
2. Import `bimagyan_qlora_training.ipynb` (or copy-paste its cells)
3. Add the dataset `your-username/bimagyan-training-data` as input
4. Set **Kaggle Secrets**:
   - `HF_TOKEN` = your Hugging Face write token
   - `HF_REPO` = `your-hf-username/bimagyan`
5. Enable **GPU P100** accelerator (free tier)
6. **Run All** — training takes ~30–45 minutes for 3 epochs on 1,145 examples

The notebook will automatically push:
- LoRA adapters → `your-hf-username/bimagyan`
- Merged full model → `your-hf-username/bimagyan-merged`

---

## Step 4 — Deploy as Free Public Serverless API (Modal Labs)

Modal provides **$30/month of free compute credits** every month with zero upfront payment.

1. Sign up for free at **https://modal.com** (one-click with GitHub or Google).
2. Authenticate your terminal:
   ```bash
   modal setup
   ```
3. Deploy the model to Modal:
   ```bash
   python backend/scripts/deploy_modal.py
   ```
4. Modal outputs your live public HTTPS endpoint:
   ```text
   https://<username>--bimagyan-api-bimagyanmodel-generate.modal.run
   ```
5. Add it to `backend/.env`:
   ```env
   LLM_PROVIDER=bimagyan
   HF_INFERENCE_URL=https://<username>--bimagyan-api-bimagyanmodel-generate.modal.run
   ```

---

## Step 5 — Update Backend `.env`

```env
LLM_PROVIDER=bimagyan
HF_INFERENCE_URL=https://bimagyan-ai.<your-subdomain>.workers.dev/
```

Restart the backend. The RAG assistant will now call the BimaGyan edge model deployed on Cloudflare Workers AI.

---

## Retraining on Updated Data

### Manual retrain trigger (Admin API)
```bash
curl -X POST http://localhost:8000/api/v1/ingestion/trigger-retrain \
  -H "X-Admin-Key: your_admin_key"
```

This queues a background rebuild of `train.jsonl` / `val.jsonl` from the latest database state. After it completes (check server logs), re-run Steps 2–5.

### Automated periodic retraining

Use the `/schedule` slash command in this conversation to set up a recurring reminder, or schedule a cron job that:
1. `POST /api/v1/ingestion/trigger-retrain`
2. `python backend/scripts/upload_to_kaggle.py`
3. Trigger Kaggle notebook via Kaggle API (requires `kaggle kernels pull / push`)

---

## Model Details

| Property | Value |
|---|---|
| Base model | `Qwen2.5-1.5B-Instruct` |
| Quantization | 4-bit NF4 (bitsandbytes) |
| Training method | QLoRA via `unsloth` |
| LoRA rank | 16, alpha 32 |
| Epochs | 3 |
| Max seq length | 2,048 tokens |
| Training GPU | Kaggle free P100 (16 GB VRAM) |
| Inference | HF Serverless Inference API (free for public models ≤10 GB) |

---

## Free Tier Limits

| Service | Limit |
|---|---|
| Kaggle GPU | 30 hrs/week P100 |
| HF Serverless Inference | Rate-limited, shared queue — ~5–30s cold start |
| HF model storage | Free for public models |
| Neon PostgreSQL | 0.5 GB free |
