"""
retrain.py
──────────
API endpoints for managing the BimaGyan AI retraining schedule,
monitoring live pipeline progress, and triggering retraining runs.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.retrain_service import retrain_service

router = APIRouter(prefix="/retrain", tags=["retrain"])


class RetrainConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    cadence_days: Optional[int] = None


@router.get("/status")
def get_retrain_status() -> Dict[str, Any]:
    """Returns the current retraining pipeline status, schedule, and execution history."""
    return retrain_service.get_status()


@router.post("/trigger")
def trigger_retrain() -> Dict[str, Any]:
    """Manually triggers the end-to-end retraining pipeline (DB rebuild → Kaggle upload → GPU training → Cloudflare sync)."""
    return retrain_service.trigger_pipeline(trigger_type="MANUAL_ADMIN")


@router.post("/config")
def update_retrain_config(cfg: RetrainConfigUpdate) -> Dict[str, Any]:
    """Updates the automatic retraining schedule (enable/disable, cadence in days)."""
    return retrain_service.update_config(enabled=cfg.enabled, cadence_days=cfg.cadence_days)
