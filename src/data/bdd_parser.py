"""
BDD100K Annotation and Metadata Parser.
Parses raw BDD100K JSON/JSONL labels into structured detection and scene condition metadata.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import logging

logger = logging.getLogger(__name__)

# BDD100K to YOLO 10-class standard taxonomy
BDD_CLASS_TO_ID = {
    "person": 0,
    "rider": 1,
    "car": 2,
    "truck": 3,
    "bus": 4,
    "train": 5,
    "motorcycle": 6,
    "bicycle": 7,
    "traffic light": 8,
    "traffic sign": 9,
}

ID_TO_BDD_CLASS = {v: k for k, v in BDD_CLASS_TO_ID.items()}

# Condition mapping to unified project vocabulary: Day, Night, Rain, Fog, Unknown
WEATHER_MAPPING = {
    "clear": "Clear",
    "partly cloudy": "Clear",
    "overcast": "Clear",
    "rainy": "Rain",
    "foggy": "Fog",
    "snowy": "Unknown",
    "undefined": "Unknown",
}

TIME_MAPPING = {
    "daytime": "Day",
    "night": "Night",
    "dawn/dusk": "Day",
    "undefined": "Unknown",
}


def normalize_bbox(
    box2d: Dict[str, float], img_w: int, img_h: int
) -> Optional[Tuple[float, float, float, float]]:
    """
    Converts BDD100K box2d {'x1', 'y1', 'x2', 'y2'} to normalized YOLO format:
    (x_center, y_center, width, height).
    Returns None if dimensions are invalid or non-positive.
    """
    x1, y1 = float(box2d.get("x1", 0)), float(box2d.get("y1", 0))
    x2, y2 = float(box2d.get("x2", 0)), float(box2d.get("y2", 0))

    # Clamp coordinates to image boundaries
    x1 = max(0.0, min(float(img_w), x1))
    x2 = max(0.0, min(float(img_w), x2))
    y1 = max(0.0, min(float(img_h), y1))
    y2 = max(0.0, min(float(img_h), y2))

    w = x2 - x1
    h = y2 - y1

    if w <= 1.0 or h <= 1.0:
        return None

    x_center = (x1 + w / 2.0) / img_w
    y_center = (y1 + h / 2.0) / img_h
    norm_w = w / img_w
    norm_h = h / img_h

    # Ensure strictly within [0, 1]
    x_center = max(0.0, min(1.0, x_center))
    y_center = max(0.0, min(1.0, y_center))
    norm_w = max(0.0, min(1.0, norm_w))
    norm_h = max(0.0, min(1.0, norm_h))

    return x_center, y_center, norm_w, norm_h


def parse_bdd_annotation_dict(
    data: Dict[str, Any], img_w: int = 1280, img_h: int = 720
) -> Dict[str, Any]:
    """
    Parses a single BDD100K frame record into structured labels and metadata.
    """
    name = data.get("name", "")
    attributes = data.get("attributes", {})
    raw_weather = attributes.get("weather", "undefined").lower()
    raw_time = attributes.get("timeofday", "undefined").lower()
    scene = attributes.get("scene", "undefined")

    weather_label = WEATHER_MAPPING.get(raw_weather, "Unknown")
    time_label = TIME_MAPPING.get(raw_time, "Unknown")

    # Primary condition resolution
    if weather_label == "Fog":
        primary_condition = "Fog"
    elif weather_label == "Rain":
        primary_condition = "Rain"
    elif time_label == "Night":
        primary_condition = "Night"
    elif time_label == "Day" and weather_label == "Clear":
        primary_condition = "Day"
    else:
        primary_condition = "Unknown"

    objects = []
    labels = data.get("labels", [])
    if isinstance(labels, list):
        for lbl in labels:
            category = lbl.get("category", "")
            if category not in BDD_CLASS_TO_ID:
                continue

            box2d = lbl.get("box2d")
            if not box2d:
                continue

            norm_box = normalize_bbox(box2d, img_w, img_h)
            if norm_box is None:
                continue

            class_id = BDD_CLASS_TO_ID[category]
            objects.append({
                "category": category,
                "class_id": class_id,
                "bbox_raw": [box2d["x1"], box2d["y1"], box2d["x2"], box2d["y2"]],
                "bbox_yolo": list(norm_box),
            })

    return {
        "image_name": name,
        "raw_weather": raw_weather,
        "raw_time": raw_time,
        "scene": scene,
        "weather_label": weather_label,
        "time_label": time_label,
        "condition": primary_condition,
        "num_objects": len(objects),
        "objects": objects,
    }


def parse_bdd_file(json_path: Path, img_w: int = 1280, img_h: int = 720) -> List[Dict[str, Any]]:
    """
    Reads a BDD100K annotation JSON file (single object or list of frame objects).
    """
    path = Path(json_path)
    if not path.is_file():
        raise FileNotFoundError(f"Annotation file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return [parse_bdd_annotation_dict(item, img_w, img_h) for item in data]
    elif isinstance(data, dict):
        return [parse_bdd_annotation_dict(data, img_w, img_h)]
    return []
