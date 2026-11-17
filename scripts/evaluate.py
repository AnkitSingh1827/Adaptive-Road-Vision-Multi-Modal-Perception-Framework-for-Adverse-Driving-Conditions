"""
Unified Evaluation CLI for Adaptive Road Vision.
Runs quantitative benchmarking across Condition Analysis, Object Detection, and Full Pipeline.
"""

import argparse
from pathlib import Path
import logging

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")


def main():
    parser = argparse.ArgumentParser(description="Adaptive Road Vision - Evaluation CLI")
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=["condition", "detector", "pipeline"],
        help="Component stage to evaluate",
    )
    parser.add_argument("--checkpoint", type=str, default=None, help="Model checkpoint path (for detector)")
    parser.add_argument("--split", type=str, default="test", help="Dataset split ('val' or 'test')")
    args = parser.parse_args()

    if args.stage == "condition":
        from src.condition.evaluate import evaluate_condition_model
        logger.info("Evaluating Condition Model on held-out test split...")
        evaluate_condition_model()

    elif args.stage == "detector":
        from src.detection.evaluate import evaluate_yolo_detector
        ckpt = args.checkpoint or (PROJECT_ROOT / "models" / "detection" / "final_selected_detector.pt")
        if not Path(ckpt).exists():
            ckpt = PROJECT_ROOT / "models" / "detection" / "detector_1_best.pt"
        logger.info("Evaluating Detector on %s split using %s...", args.split, ckpt)
        evaluate_yolo_detector(checkpoint_path=Path(ckpt), split=args.split)

    elif args.stage == "pipeline":
        from src.pipeline.inference import AdaptiveRoadVisionPipeline
        logger.info("Running Pipeline evaluation...")
        pipeline = AdaptiveRoadVisionPipeline()
        logger.info("Pipeline initialized and validated successfully.")


if __name__ == "__main__":
    main()
