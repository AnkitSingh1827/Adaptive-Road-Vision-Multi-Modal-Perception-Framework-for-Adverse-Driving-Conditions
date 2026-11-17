"""
Unified Training CLI for Adaptive Road Vision.
Allows training condition classification, CycleGAN domain adaptation, and YOLO detectors.
"""

import argparse
from pathlib import Path
import logging

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Adaptive Road Vision - Training CLI")
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=["condition", "cyclegan", "detector"],
        help="Pipeline stage to train",
    )
    parser.add_argument("--epochs", type=int, default=None, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size")
    parser.add_argument("--lr", type=float, default=None, help="Learning rate")
    parser.add_argument("--model", type=str, default=None, help="Base model name or weights")
    args = parser.parse_args()

    if args.stage == "condition":
        from src.condition.train import train_condition_model
        epochs = args.epochs or 6
        batch = args.batch_size or 32
        lr = args.lr or 1e-4
        logger.info("Starting Condition Model training: epochs=%d, batch=%d, lr=%e", epochs, batch, lr)
        train_condition_model(epochs=epochs, batch_size=batch, lr=lr)

    elif args.stage == "cyclegan":
        from src.cyclegan.train import main as train_cyclegan
        logger.info("Starting CycleGAN domain adaptation training...")
        train_cyclegan()

    elif args.stage == "detector":
        from src.detection.train import train_yolo_detector
        model_name = args.model or "yolo11n.pt"
        epochs = args.epochs or 50
        batch = args.batch_size or 16
        logger.info("Starting Detector training: model=%s, epochs=%d, batch=%d", model_name, epochs, batch)
        train_yolo_detector(model_name=model_name, epochs=epochs, batch_size=batch)


if __name__ == "__main__":
    main()
