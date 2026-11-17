"""
Multi-Factor Collision Risk Assessment Engine for Autonomous Road Vision.
Combines object proximity, velocity, class vulnerability weight, and scene condition multipliers
to compute transparent per-object and per-frame situational risk scores.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
DEFAULT_RISK_CONFIG = PROJECT_ROOT / "configs" / "risk.yaml"

DEFAULT_CONDITION_FACTORS = {
    "Day": 1.0,
    "Night": 1.20,
    "Rain": 1.15,
    "Fog": 1.25,
    "Unknown": 1.05,
}

DEFAULT_CLASS_WEIGHTS = {
    0: 1.30,  # person (vulnerable road user)
    1: 1.25,  # rider
    2: 1.00,  # car
    3: 1.05,  # truck
    4: 1.05,  # bus
    5: 1.00,  # train
    6: 1.20,  # motorcycle
    7: 1.20,  # bicycle
    8: 0.80,  # traffic light
    9: 0.80,  # traffic sign
}


class RiskEngine:
    """
    Transparent Rule-Based Road Situational Risk Engine.
    Computes per-object risk and aggregate frame risk level.
    """
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_RISK_CONFIG
        self.condition_factors = dict(DEFAULT_CONDITION_FACTORS)
        self.class_weights = dict(DEFAULT_CLASS_WEIGHTS)
        self.near_threshold = 0.25
        self.critical_threshold = 0.60
        self.confidence_floor = 0.25
        self.persistence_reference = 10
        self.level_thresholds = {"LOW": 0.25, "MEDIUM": 0.50, "HIGH": 0.75}

        self._load_config()

    def _load_config(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}

                if "condition_factor" in cfg:
                    self.condition_factors.update(cfg["condition_factor"])
                if "class_weight" in cfg:
                    for k, v in cfg["class_weight"].items():
                        self.class_weights[int(k)] = float(v)
                if "near_distance_threshold" in cfg:
                    self.near_threshold = float(cfg["near_distance_threshold"])
                if "critical_distance_threshold" in cfg:
                    self.critical_threshold = float(cfg["critical_distance_threshold"])
                if "level_thresholds" in cfg:
                    self.level_thresholds = cfg["level_thresholds"]

                logger.info("Loaded risk configuration from %s", self.config_path.name)
            except Exception as e:
                logger.warning("Failed to load %s, using defaults: %s", self.config_path, e)

    def compute_object_risk(
        self,
        proximity: float,
        confidence: float,
        class_id: int,
        condition: str = "Day",
        track_age: int = 1,
    ) -> float:
        """
        Computes single object risk score in range [0.0, 1.0].
        """
        conf_weight = max(self.confidence_floor, min(1.0, confidence))
        cls_factor = self.class_weights.get(class_id, 1.0)
        cond_factor = self.condition_factors.get(condition, 1.0)

        # Proximity contribution (non-linear ramp)
        prox_contrib = proximity ** 1.3

        # Track persistence factor (stabilizes detections)
        pers_factor = min(1.0, 0.7 + 0.3 * (track_age / self.persistence_reference))

        # Composite raw score
        raw_score = prox_contrib * cls_factor * cond_factor * conf_weight * pers_factor
        risk_score = max(0.0, min(1.0, raw_score))

        return round(float(risk_score), 4)

    def evaluate_frame(
        self,
        objects: List[Dict[str, Any]],
        condition: str = "Day",
    ) -> Dict[str, Any]:
        """
        Evaluates risk for all objects in a frame and assigns global frame risk.
        objects: list of dicts with keys: 'proximity', 'confidence', 'class_id', 'track_age' (optional)
        """
        scored_objects = []
        max_risk = 0.0

        for obj in objects:
            prox = float(obj.get("proximity", 0.0))
            conf = float(obj.get("confidence", 0.5))
            cid = int(obj.get("class_id", 0))
            age = int(obj.get("track_age", 1))

            risk = self.compute_object_risk(prox, conf, cid, condition, age)
            scored = dict(obj)
            scored["risk_score"] = risk
            scored["is_critical"] = (risk >= self.level_thresholds.get("HIGH", 0.75))
            scored_objects.append(scored)

            if risk > max_risk:
                max_risk = risk

        # Frame level assignment
        if max_risk >= self.level_thresholds.get("HIGH", 0.75):
            level = "CRITICAL" if max_risk >= 0.88 else "HIGH"
        elif max_risk >= self.level_thresholds.get("MEDIUM", 0.50):
            level = "MEDIUM"
        elif max_risk >= self.level_thresholds.get("LOW", 0.25):
            level = "LOW"
        else:
            level = "SAFE"

        return {
            "condition": condition,
            "condition_multiplier": self.condition_factors.get(condition, 1.0),
            "frame_risk_score": round(max_risk, 4),
            "risk_level": level,
            "num_objects": len(scored_objects),
            "critical_objects_count": sum(1 for o in scored_objects if o.get("is_critical", False)),
            "objects": scored_objects,
        }
