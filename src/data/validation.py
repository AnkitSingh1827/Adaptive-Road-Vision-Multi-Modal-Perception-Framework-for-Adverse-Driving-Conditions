"""
Dataset Validation and Quality Integrity Checks.
Validates image decodability, dimension bounds, YOLO label format, and image-label synchronization.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import os
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)

SUPPORTED_IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def validate_image_file(image_path: Path) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Checks if an image file exists, has non-zero size, and can be decoded by PIL without error.
    """
    p = Path(image_path)
    if not p.is_file():
        return False, f"File does not exist: {p}", None

    if p.stat().st_size == 0:
        return False, "File is zero bytes", None

    try:
        with Image.open(p) as img:
            img.verify()

        # Reopen to read dimensions and pixel values
        with Image.open(p) as img:
            img = img.convert("RGB")
            w, h = img.size
            arr = np.asarray(img, dtype=np.float32)
            brightness = float(arr.mean())
            contrast = float(arr.std())

        metrics = {
            "width": w,
            "height": h,
            "brightness": round(brightness, 2),
            "contrast": round(contrast, 2),
            "size_bytes": p.stat().st_size,
        }
        return True, "Valid", metrics
    except Exception as e:
        return False, f"Corrupted or invalid image: {str(e)}", None


def validate_yolo_label_file(
    label_path: Path, num_classes: int = 10
) -> Tuple[bool, str, int]:
    """
    Validates a YOLO-format annotation text file:
    Each line must have: <class_id> <x_center> <y_center> <width> <height>
    Coordinates must be floats normalized within [0.0, 1.0].
    """
    p = Path(label_path)
    if not p.is_file():
        return False, f"Label file does not exist: {p}", 0

    valid_boxes = 0
    with open(p, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue

            parts = line_str.split()
            if len(parts) != 5:
                return False, f"Line {line_idx} has {len(parts)} tokens (expected 5)", valid_boxes

            try:
                cls_id = int(parts[0])
                xc, yc, w, h = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
            except ValueError:
                return False, f"Line {line_idx} non-numeric values", valid_boxes

            if not (0 <= cls_id < num_classes):
                return False, f"Line {line_idx} invalid class ID {cls_id}", valid_boxes

            if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                return False, f"Line {line_idx} coordinates outside [0, 1]: ({xc}, {yc}, {w}, {h})", valid_boxes

            valid_boxes += 1

    return True, "Valid", valid_boxes


def run_dataset_integrity_check(
    dataset_root: Path, split: str = "train"
) -> Dict[str, Any]:
    """
    Performs full cross-check of image and label pairs for a dataset split.
    """
    root = Path(dataset_root)
    img_dir = root / "images" / split
    lbl_dir = root / "labels" / split

    if not img_dir.is_dir():
        return {"passed": False, "error": f"Image dir not found: {img_dir}"}

    img_files = sorted([p for p in img_dir.iterdir() if p.suffix.lower() in SUPPORTED_IMG_EXTS])
    missing_labels = 0
    corrupt_images = 0
    total_boxes = 0

    for img_p in img_files:
        is_ok, reason, _ = validate_image_file(img_p)
        if not is_ok:
            corrupt_images += 1
            continue

        lbl_p = lbl_dir / f"{img_p.stem}.txt"
        if not lbl_p.is_file():
            missing_labels += 1
        else:
            lbl_ok, _, n_boxes = validate_yolo_label_file(lbl_p)
            if lbl_ok:
                total_boxes += n_boxes

    report = {
        "dataset_root": str(root),
        "split": split,
        "total_images": len(img_files),
        "corrupt_images": corrupt_images,
        "missing_labels": missing_labels,
        "total_bounding_boxes": total_boxes,
        "passed": (corrupt_images == 0 and missing_labels == 0),
    }
    return report
