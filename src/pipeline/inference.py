"""
End-to-End Unified Adaptive Road Vision Pipeline.
Connects Condition Classification -> Adaptive Image Enhancement -> Object Detection & Tracking ->
Monocular Depth Estimation -> Situational Risk Assessment.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import time
import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
import logging

from src.condition.model import MultiTaskConditionClassifier, ConditionClassifier5Class
from src.enhancement.adaptive import AdaptiveEnhancer
from src.depth.depth_model import DepthEstimator
from src.depth.distance import extract_box_depth, compute_metric_distance
from src.tracking.bytetrack import RoadTracker
from src.risk.risk_engine import RiskEngine

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
MODELS_DIR = PROJECT_ROOT / "models"


class AdaptiveRoadVisionPipeline:
    """
    Unified Production Pipeline for Adaptive Road Vision.
    Performs full frame analysis from raw pixels to safety risk telemetry.
    """
    def __init__(
        self,
        condition_ckpt: Optional[Path] = None,
        detector_ckpt: Optional[Path] = None,
        use_enhancement: bool = True,
        use_depth: bool = True,
        device: Optional[str] = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_enhancement = use_enhancement
        self.use_depth = use_depth

        logger.info("Initializing Adaptive Road Vision Pipeline on %s...", self.device)

        # 1. Condition Classifier
        self.condition_model = None
        self._init_condition_model(condition_ckpt)

        # 2. Adaptive Enhancer
        self.enhancer = None
        if self.use_enhancement:
            self.enhancer = AdaptiveEnhancer(device=torch.device(self.device))

        # 3. Object Detector
        self.detector = None
        self._init_detector(detector_ckpt)

        # 4. Multi-Object Tracker
        self.tracker = RoadTracker()

        # 5. Depth Estimator
        self.depth_estimator = None
        if self.use_depth:
            try:
                self.depth_estimator = DepthEstimator(device=self.device)
            except Exception as e:
                logger.warning("Depth estimation unavailable: %s", e)
                self.use_depth = False

        # 6. Risk Engine
        self.risk_engine = RiskEngine()

        logger.info("Adaptive Road Vision Pipeline initialized successfully.")

    def _init_condition_model(self, ckpt_path: Optional[Path]):
        candidates = [
            ckpt_path,
            MODELS_DIR / "condition" / "condition_multitask_best.pth",
            MODELS_DIR / "condition" / "condition_resnet18_best.pth",
        ]
        resolved = next((p for p in candidates if p and Path(p).is_file()), None)

        if resolved:
            try:
                payload = torch.load(resolved, map_location=self.device)
                if isinstance(payload, dict) and "time_classes" in payload:
                    model = MultiTaskConditionClassifier(pretrained=False)
                    model.load_state_dict(payload["model_state_dict"])
                    self.is_multitask = True
                else:
                    model = ConditionClassifier5Class(num_classes=5, pretrained=False)
                    state = payload if not isinstance(payload, dict) or "model_state_dict" not in payload else payload["model_state_dict"]
                    if not any(k.startswith("model.") for k in state.keys()):
                        state = {f"model.{k}": v for k, v in state.items()}
                    model.load_state_dict(state)
                    self.is_multitask = False

                model.to(self.device).eval()
                self.condition_model = model
                logger.info("Loaded condition classifier: %s", resolved.name)
            except Exception as e:
                logger.warning("Failed to load condition classifier (%s): %s", resolved, e)
                self.condition_model = None
        else:
            logger.warning("No condition classifier checkpoint found.")

    def _init_detector(self, ckpt_path: Optional[Path]):
        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError("Ultralytics required: pip install ultralytics")

        candidates = [
            ckpt_path,
            MODELS_DIR / "detection" / "final_selected_detector.pt",
            MODELS_DIR / "detection" / "detector_2_best.pt",
            MODELS_DIR / "detection" / "detector_1_best.pt",
            PROJECT_ROOT / "weights" / "yolo11s.pt",
            PROJECT_ROOT / "weights" / "yolo11n.pt",
            PROJECT_ROOT / "yolo11s.pt",
            PROJECT_ROOT / "yolo11n.pt",
        ]
        resolved = next((p for p in candidates if p and Path(p).is_file()), None)
        assert resolved is not None, f"No detector checkpoint found! Checked: {[str(p) for p in candidates if p]}"

        logger.info("Loading YOLO detector from: %s", resolved.name)
        self.detector = YOLO(str(resolved))

    def predict_condition(self, pil_image: Image.Image) -> Dict[str, Any]:
        """Classifies scene time and weather conditions."""
        if self.condition_model is None:
            return {"primary_condition": "Day", "time": "Day", "weather": "Clear", "confidence": 1.0}

        import torchvision.transforms as _T
        _to_tensor = _T.ToTensor()
        resized = pil_image.resize((224, 224), Image.Resampling.BILINEAR)
        tensor = _to_tensor(resized).unsqueeze(0).to(self.device)

        with torch.no_grad():
            if getattr(self, "is_multitask", False):
                res = self.condition_model.predict(tensor)
                return res
            else:
                out = self.condition_model(tensor)
                probs = torch.softmax(out, dim=-1)[0]
                idx = int(torch.argmax(probs).item())
                classes = ["Day", "Night", "Rain", "Fog", "Unknown"]
                cond = classes[idx] if idx < len(classes) else "Day"
                class_probs = {c: round(float(probs[i].item()), 4) for i, c in enumerate(classes) if i < len(probs)}
                return {
                    "primary_condition": cond,
                    "time": "Night" if cond == "Night" else "Day",
                    "weather": cond if cond in ["Rain", "Fog"] else "Clear",
                    "confidence": float(probs[idx].item()),
                    "class_probabilities": class_probs,
                }

    def process_frame(
        self,
        image: Union[Image.Image, np.ndarray, str, Path],
        frame_idx: Optional[int] = None,
        conf_thresh: float = 0.25,
        iou_thresh: float = 0.50,
        return_visualization: bool = True,
    ) -> Dict[str, Any]:
        """
        Runs the full perception pipeline on a single frame.
        """
        start_time = time.perf_counter()

        # Load image
        if isinstance(image, (str, Path)):
            pil_orig = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            pil_orig = Image.fromarray(image.astype(np.uint8)).convert("RGB")
        else:
            pil_orig = image.convert("RGB")

        orig_w, orig_h = pil_orig.size

        # 1. Condition Analysis
        cond_info = self.predict_condition(pil_orig)
        condition = cond_info.get("primary_condition", "Day")

        # 2. Adaptive Enhancement
        was_enhanced = False
        if self.enhancer and condition in ["Night", "Rain", "Fog"]:
            pil_processed = self.enhancer.enhance_pil(pil_orig, condition)
            was_enhanced = True
        else:
            pil_processed = pil_orig

        # 3. Object Detection & Tracking
        yolo_results = self.detector.track(
            source=pil_processed,
            conf=conf_thresh,
            iou=iou_thresh,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
        )

        detections = []
        if yolo_results and len(yolo_results) > 0:
            res = yolo_results[0]
            boxes = res.boxes
            if boxes is not None and len(boxes) > 0:
                for b in boxes:
                    xyxy = b.xyxy[0].cpu().numpy().tolist()
                    conf = float(b.conf[0].item())
                    cid = int(b.cls[0].item())
                    tid = int(b.id[0].item()) if b.id is not None else None
                    cname = self.detector.names.get(cid, str(cid))

                    detections.append({
                        "bbox": xyxy,
                        "confidence": round(conf, 4),
                        "class_id": cid,
                        "class_name": cname,
                        "track_id": tid,
                    })

        # Update tracking telemetry
        tracked_detections = self.tracker.update_tracks(detections, frame_idx=frame_idx)

        # 4. Monocular Depth Estimation
        depth_map = None
        if self.depth_estimator:
            depth_map = self.depth_estimator.predict_depth_map(pil_orig)
            for det in tracked_detections:
                depth_stats = extract_box_depth(depth_map, det["bbox"])
                det.update(depth_stats)
        else:
            for det in tracked_detections:
                det["proximity"] = 0.5

        # 5. Risk Assessment
        risk_evaluation = self.risk_engine.evaluate_frame(tracked_detections, condition=condition)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        telemetry = {
            "frame_idx": frame_idx,
            "condition": condition,
            "condition_info": cond_info,
            "was_enhanced": was_enhanced,
            "enhanced_image": pil_processed if was_enhanced else None,
            "confidence_condition": cond_info.get("confidence", cond_info.get("overall_confidence", 1.0)),
            "detected_objects_count": len(tracked_detections),
            "frame_risk_score": risk_evaluation["frame_risk_score"],
            "risk_level": risk_evaluation["risk_level"],
            "critical_objects_count": risk_evaluation["critical_objects_count"],
            "condition_multiplier": risk_evaluation.get("condition_multiplier", 1.0),
            "latency_ms": round(elapsed_ms, 2),
            "fps": round(1000.0 / elapsed_ms, 1) if elapsed_ms > 0 else 0.0,
            "objects": risk_evaluation["objects"],
            "depth_map": depth_map,
        }

        # 6. Visualization
        if return_visualization:
            base_img = pil_processed if was_enhanced else pil_orig
            vis_img = self.render_overlay(base_img, telemetry, depth_map)
            telemetry["visualization"] = vis_img

        return telemetry

    def render_overlay(
        self,
        pil_img: Image.Image,
        telemetry: Dict[str, Any],
        depth_map: Optional[np.ndarray] = None,
    ) -> Image.Image:
        """
        Draws professional bounding boxes, tracking labels, distance indicators,
        and ADAS HUD dashboard banner.
        """
        canvas = pil_img.copy()
        draw = ImageDraw.Draw(canvas)
        w, h = canvas.size

        # Colors
        COLOR_SAFE = (0, 200, 100)
        COLOR_MED = (255, 180, 0)
        COLOR_CRIT = (255, 50, 50)

        for obj in telemetry.get("objects", []):
            x1, y1, x2, y2 = obj["bbox"]
            risk = obj.get("risk_score", 0.0)
            prox = obj.get("proximity", 0.0)
            tid = obj.get("track_id", "N/A")
            cname = obj.get("class_name", "")

            color = COLOR_CRIT if risk >= 0.70 else (COLOR_MED if risk >= 0.40 else COLOR_SAFE)

            # Box
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

            # Label banner
            label_text = f"#{tid} {cname} | Prox:{prox:.2f} | Risk:{risk:.2f}"
            draw.rectangle([x1, max(0, y1 - 20), x1 + len(label_text) * 7 + 10, y1], fill=color)
            draw.text((x1 + 4, max(0, y1 - 18)), label_text, fill=(255, 255, 255))

        # HUD Top Banner
        hud_bg = (20, 25, 35)
        draw.rectangle([0, 0, w, 40], fill=hud_bg)

        cond_str = telemetry.get("condition", "Unknown")
        enhanced_str = "[ENHANCED]" if telemetry.get("was_enhanced") else "[DIRECT]"
        risk_lvl = telemetry.get("risk_level", "SAFE")
        risk_score = telemetry.get("frame_risk_score", 0.0)
        fps = telemetry.get("fps", 0.0)

        hud_color = COLOR_CRIT if risk_lvl in ["CRITICAL", "HIGH"] else (COLOR_MED if risk_lvl == "MEDIUM" else COLOR_SAFE)

        hud_text = (
            f"ADAPTIVE ROAD VISION  |  Condition: {cond_str} {enhanced_str}  |  "
            f"Objects: {telemetry.get('detected_objects_count', 0)}  |  "
            f"Risk: {risk_lvl} ({risk_score:.2f})  |  FPS: {fps:.1f}"
        )
        draw.text((15, 12), hud_text, fill=hud_color)

        return canvas
