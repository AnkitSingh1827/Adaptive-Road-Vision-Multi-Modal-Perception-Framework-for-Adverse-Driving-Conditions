"""
Ultralytics YOLO Training Orchestrator for Object Detection.
Supports YOLO11n, YOLO11s and other YOLO variants on BDD100K road object classes.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import os
import shutil
import logging
import torch
import yaml

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
MODELS_DIR = PROJECT_ROOT / "models" / "detection"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
CONFIGS_DIR = PROJECT_ROOT / "configs"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)


def train_yolo_detector(
    model_name: str = "yolo11n.pt",
    data_yaml: Optional[Path] = None,
    run_name: str = "detector_training",
    epochs: int = 50,
    batch_size: int = 16,
    imgsz: int = 640,
    patience: int = 10,
    device: Optional[str] = None,
    workers: int = 0,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Trains a YOLO model using Ultralytics API.
    Saves best weights to models/detection/<run_name>_best.pt.
    """
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise ImportError("Ultralytics package is required: pip install ultralytics") from e

    device = device or ("0" if torch.cuda.is_available() else "cpu")
    data_yaml = data_yaml or (CONFIGS_DIR / "detection.yaml")
    if not data_yaml.exists():
        data_yaml = CONFIGS_DIR / "dataset.yaml"

    assert data_yaml.exists(), f"Detection dataset YAML not found at: {data_yaml}"

    # Check for weights location (weights/ or root)
    model_path = model_name
    if not Path(model_path).exists():
        candidate_weights = PROJECT_ROOT / "weights" / model_name
        if candidate_weights.exists():
            model_path = str(candidate_weights)

    logger.info("Initializing YOLO model: %s (device=%s)", model_path, device)
    model = YOLO(model_path)

    project_save_dir = EXPERIMENTS_DIR / run_name

    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        patience=patience,
        device=device,
        workers=workers,
        seed=seed,
        project=str(EXPERIMENTS_DIR),
        name=run_name,
        exist_ok=True,
        verbose=True,
    )

    # Export best model to models/detection
    train_save_dir = Path(model.trainer.save_dir) if hasattr(model, "trainer") else project_save_dir
    best_pt = train_save_dir / "weights" / "best.pt"
    last_pt = train_save_dir / "weights" / "last.pt"

    dest_best = MODELS_DIR / f"{run_name}_best.pt"
    dest_last = MODELS_DIR / f"{run_name}_last.pt"

    if best_pt.exists():
        shutil.copy2(best_pt, dest_best)
        logger.info("Saved best detector checkpoint to: %s", dest_best)
    if last_pt.exists():
        shutil.copy2(last_pt, dest_last)

    report = {
        "model_name": model_name,
        "run_name": run_name,
        "epochs": epochs,
        "device": device,
        "save_dir": str(train_save_dir),
        "best_checkpoint": str(dest_best if dest_best.exists() else best_pt),
        "last_checkpoint": str(dest_last if dest_last.exists() else last_pt),
    }

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train YOLO detector")
    parser.add_argument("--model", type=str, default="yolo11n.pt")
    parser.add_argument("--name", type=str, default="detector_1")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch", type=int, default=16)
    args = parser.parse_args()

    train_yolo_detector(
        model_name=args.model,
        run_name=args.name,
        epochs=args.epochs,
        batch_size=args.batch,
    )
