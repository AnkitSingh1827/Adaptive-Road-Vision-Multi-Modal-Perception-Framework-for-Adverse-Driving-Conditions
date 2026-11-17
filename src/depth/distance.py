"""
Depth to Distance Mapping and Object Proximity Extraction.
Calculates robust object depth and proximity from dense depth maps and 2D bounding boxes.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np


def extract_box_depth(
    depth_map: np.ndarray,
    bbox_xyxy: List[float],
    interior_ratio: float = 0.5,
) -> Dict[str, float]:
    """
    Extracts depth statistics from the robust interior region of a bounding box.
    bbox_xyxy: [x1, y1, x2, y2] in pixel coordinates.
    interior_ratio: ratio of central box sampled (e.g. 0.5 samples central 50% width and height).
    """
    h_img, w_img = depth_map.shape[:2]
    x1, y1, x2, y2 = bbox_xyxy

    # Clamp to image bounds
    x1 = max(0, min(w_img - 1, int(x1)))
    x2 = max(0, min(w_img, int(x2)))
    y1 = max(0, min(h_img - 1, int(y1)))
    y2 = max(0, min(h_img, int(y2)))

    bw = x2 - x1
    bh = y2 - y1

    if bw < 2 or bh < 2:
        return {"median_depth": 0.0, "mean_depth": 0.0, "proximity": 0.0}

    # Central interior box
    margin_w = int(bw * (1.0 - interior_ratio) / 2.0)
    margin_h = int(bh * (1.0 - interior_ratio) / 2.0)

    sub_x1 = x1 + margin_w
    sub_x2 = max(sub_x1 + 1, x2 - margin_w)
    sub_y1 = y1 + margin_h
    sub_y2 = max(sub_y1 + 1, y2 - margin_h)

    patch = depth_map[sub_y1:sub_y2, sub_x1:sub_x2]
    if patch.size == 0:
        patch = depth_map[y1:y2, x1:x2]

    median_val = float(np.median(patch))
    mean_val = float(np.mean(patch))
    p90_val = float(np.percentile(patch, 90))

    # Proximity: in Depth Anything V2 normalized map, higher values generally indicate closer proximity
    proximity = median_val

    return {
        "median_depth": round(median_val, 4),
        "mean_depth": round(mean_val, 4),
        "proximity": round(proximity, 4),
    }


def compute_metric_distance(
    proximity: float,
    scale_factor: Optional[float] = None,
    focal_length_px: float = 1000.0,
    camera_height_m: float = 1.6,
) -> Optional[float]:
    """
    Computes approximate metric distance in meters if a calibration scale factor is provided.
    If scale_factor is None, returns None to avoid claiming unverified metric distances.
    """
    if scale_factor is None:
        return None

    # Inverted relation: closer objects have higher proximity
    clamped_prox = max(0.01, min(1.0, proximity))
    distance_m = (scale_factor / clamped_prox)
    return round(distance_m, 2)
