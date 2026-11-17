"""
Detector Comparison and Model Selection Engine.
Compares candidate detectors (e.g. YOLO11n vs YOLO11s) on accuracy, latency, and parameter footprint
to automatically produce final detector selection recommendation.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import time
import json
import logging
import pandas as pd
import numpy as np
import torch

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
RESULTS_DIR = PROJECT_ROOT / "results" / "detection"
MODELS_DIR = PROJECT_ROOT / "models" / "detection"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def measure_model_latency(
    model, dummy_input_shape=(1, 3, 640, 640), warmup=10, iterations=50, device="cpu"
) -> Dict[str, float]:
    """
    Measures inference latency and throughput (FPS).
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        pass

    dummy_tensor = torch.zeros(dummy_input_shape).to(device)

    # Warmup
    for _ in range(warmup):
        _ = model(dummy_tensor)

    if device == "cuda":
        torch.cuda.synchronize()

    start_t = time.perf_counter()
    for _ in range(iterations):
        _ = model(dummy_tensor)

    if device == "cuda":
        torch.cuda.synchronize()

    elapsed = time.perf_counter() - start_t
    avg_latency_ms = (elapsed / iterations) * 1000.0
    fps = 1000.0 / avg_latency_ms if avg_latency_ms > 0 else 0.0

    return {
        "avg_latency_ms": round(avg_latency_ms, 2),
        "fps": round(fps, 1),
    }


def compare_detectors(
    candidate_checkpoints: List[Dict[str, Any]],
    output_filename: str = "detector_comparison_summary.csv"
) -> Dict[str, Any]:
    """
    Evaluates and compares detector candidates.
    candidate_checkpoints: list of dicts with keys: 'name', 'model_id', 'checkpoint_path', 'val_map50', 'test_map50_95'
    """
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise ImportError("Ultralytics package is required") from e

    device = "cuda" if torch.cuda.is_available() else "cpu"
    rows = []

    best_detector = None
    highest_score = -1.0

    for cand in candidate_checkpoints:
        name = cand["name"]
        ckpt_p = Path(cand["checkpoint_path"])
        if not ckpt_p.is_file():
            logger.warning("Checkpoint for %s missing: %s", name, ckpt_p)
            continue

        file_size_mb = ckpt_p.stat().st_size / (1024 * 1024)
        model = YOLO(str(ckpt_p))

        # Count parameters
        param_count = sum(p.numel() for p in model.model.parameters())

        latency_metrics = measure_model_latency(model, device=device)

        map50 = cand.get("val_map50", 0.0)
        map50_95 = cand.get("test_map50_95", 0.0)

        # Efficiency composite score: balances accuracy and speed for embedded ADAS deployment
        # Score = mAP50_95 * 0.6 + normalized_fps * 0.4
        norm_fps = min(1.0, latency_metrics["fps"] / 60.0)
        score = (map50_95 * 0.6) + (norm_fps * 0.4)

        row = {
            "candidate": name,
            "model_id": cand.get("model_id", name),
            "checkpoint": str(ckpt_p),
            "size_mb": round(file_size_mb, 2),
            "params_million": round(param_count / 1e6, 2),
            "latency_ms": latency_metrics["avg_latency_ms"],
            "fps": latency_metrics["fps"],
            "mAP50": map50,
            "mAP50_95": map50_95,
            "efficiency_score": round(score, 4),
        }
        rows.append(row)

        if score > highest_score:
            highest_score = score
            best_detector = cand

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / output_filename, index=False)

    selection_report = {
        "selected_detector": best_detector["name"] if best_detector else "None",
        "selected_model": best_detector.get("model_id", "") if best_detector else "None",
        "stable_downstream_checkpoint": str(best_detector["checkpoint_path"]) if best_detector else "None",
        "selection_rationale": "Optimized trade-off between edge ADAS inference latency and multi-condition mAP.",
        "candidates": rows,
    }

    selection_json = RESULTS_DIR / "final_detector_selection.json"
    with open(selection_json, "w", encoding="utf-8") as f:
        json.dump(selection_report, f, indent=2)

    logger.info("Detector comparison complete. Selected: %s", selection_report["selected_detector"])
    return selection_report
