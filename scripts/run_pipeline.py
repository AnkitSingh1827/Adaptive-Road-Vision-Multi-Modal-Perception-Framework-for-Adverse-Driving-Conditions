"""
Command-Line Interface for Running the Adaptive Road Vision End-to-End Pipeline.
Runs condition classification, adaptive enhancement, object detection/tracking,
monocular depth estimation, and risk assessment on single images or full directories.
"""

import argparse
from pathlib import Path
import json
import logging
from tqdm import tqdm
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline.inference import AdaptiveRoadVisionPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "pipeline_inference"


def main():
    parser = argparse.ArgumentParser(description="Adaptive Road Vision - Pipeline Inference CLI")
    parser.add_argument("--input", type=str, required=True, help="Path to input image file or directory of images")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output directory for visual results")
    parser.add_argument("--device", type=str, default=None, help="Device to use ('cuda' or 'cpu')")
    parser.add_argument("--no-enhancement", action="store_true", help="Disable adaptive condition enhancement")
    parser.add_argument("--no-depth", action="store_true", help="Disable monocular depth estimation")
    parser.add_argument("--conf", type=float, default=0.25, help="Detection confidence threshold")
    parser.add_argument("--max-images", type=int, default=None, help="Maximum images to process")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline = AdaptiveRoadVisionPipeline(
        use_enhancement=not args.no_enhancement,
        use_depth=not args.no_depth,
        device=args.device,
    )

    if input_path.is_file():
        image_files = [input_path]
    elif input_path.is_dir():
        supported_exts = {".jpg", ".jpeg", ".png", ".bmp"}
        image_files = sorted([p for p in input_path.iterdir() if p.suffix.lower() in supported_exts])
        if args.max_images:
            image_files = image_files[:args.max_images]
    else:
        logger.error("Input path does not exist: %s", input_path)
        return

    logger.info("Processing %d images -> %s", len(image_files), output_dir)
    records = []

    for idx, img_p in enumerate(tqdm(image_files, desc="Running Pipeline")):
        try:
            result = pipeline.process_frame(
                img_p,
                frame_idx=idx + 1,
                conf_thresh=args.conf,
                return_visualization=True,
            )

            # Save visualization
            vis_img = result.pop("visualization", None)
            if vis_img:
                out_img_path = output_dir / f"annotated_{img_p.name}"
                vis_img.save(out_img_path, quality=92)
                result["visualization_saved"] = str(out_img_path)

            result["image_name"] = img_p.name
            records.append(result)
        except Exception as e:
            logger.error("Failed processing %s: %s", img_p.name, e)

    # Save summary report
    summary_path = output_dir / "inference_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    logger.info("Pipeline execution complete. Results saved to: %s", output_dir)


if __name__ == "__main__":
    main()
