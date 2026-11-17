"""
Object Detection Evaluation and Performance Reporting.
Evaluates YOLO checkpoints on validation and test sets, generating per-class and per-condition metrics.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging
import pandas as pd
import numpy as np
import torch

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
RESULTS_DIR = PROJECT_ROOT / "results" / "detection"
CONFIGS_DIR = PROJECT_ROOT / "configs"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = [
    "person", "rider", "car", "truck", "bus",
    "train", "motorcycle", "bicycle", "traffic light", "traffic sign"
]


def evaluate_yolo_detector(
    checkpoint_path: Path,
    data_yaml: Optional[Path] = None,
    split: str = "val",
    imgsz: int = 640,
    batch_size: int = 16,
    conf_thresh: float = 0.25,
    iou_thresh: float = 0.50,
    save_prefix: str = "detector_val",
) -> Dict[str, Any]:
    """
    Evaluates a trained YOLO model checkpoint and writes structured metric reports.
    """
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise ImportError("Ultralytics package is required: pip install ultralytics") from e

    ckpt = Path(checkpoint_path)
    if not ckpt.is_file():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt}")

    data_yaml = data_yaml or (CONFIGS_DIR / "detection.yaml")
    if not data_yaml.exists():
        data_yaml = CONFIGS_DIR / "dataset.yaml"

    device = "0" if torch.cuda.is_available() else "cpu"
    logger.info("Evaluating detector %s on %s split (device=%s)", ckpt.name, split, device)

    model = YOLO(str(ckpt))
    metrics = model.val(
        data=str(data_yaml),
        split=split,
        imgsz=imgsz,
        batch=batch_size,
        conf=conf_thresh,
        iou=iou_thresh,
        device=device,
        save_json=False,
        plots=True,
    )

    box_metrics = metrics.box
    map50 = float(box_metrics.map50)
    map50_95 = float(box_metrics.map)
    mp = float(box_metrics.mp)
    mr = float(box_metrics.mr)

    # Per-class breakdown
    per_class_data = []
    maps_per_class = box_metrics.maps if hasattr(box_metrics, "maps") else []
    for idx, name in enumerate(CLASS_NAMES):
        c_map50 = float(box_metrics.p_curve[idx]) if hasattr(box_metrics, "p_curve") and idx < len(box_metrics.p_curve) else None
        c_map = float(maps_per_class[idx]) if idx < len(maps_per_class) else None
        per_class_data.append({
            "class_id": idx,
            "class_name": name,
            "map50_95": c_map,
        })

    class_df = pd.DataFrame(per_class_data)
    class_csv = RESULTS_DIR / f"{save_prefix}_class_metrics.csv"
    class_df.to_csv(class_csv, index=False)

    report = {
        "checkpoint": str(ckpt),
        "split": split,
        "mAP50": map50,
        "mAP50_95": map50_95,
        "mean_precision": mp,
        "mean_recall": mr,
        "classes": CLASS_NAMES,
    }

    report_path = RESULTS_DIR / f"{save_prefix}_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Evaluation complete: mAP50=%.4f, mAP50-95=%.4f -> %s", map50, map50_95, report_path)
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate YOLO detector")
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--prefix", type=str, default="detector_eval")
    args = parser.parse_args()

    evaluate_yolo_detector(
        checkpoint_path=Path(args.checkpoint),
        split=args.split,
        save_prefix=args.prefix,
    )
