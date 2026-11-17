"""
PyTorch Dataset Implementations for Adaptive Road Vision.
Includes multi-task condition classification, enhancement training datasets,
and YOLO format export utilities.
"""

from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import numpy as np
import torch
from torch.utils.data import Dataset
from PIL import Image
import torchvision.transforms as transforms
import shutil
import logging

logger = logging.getLogger(__name__)

TIME_TO_ID = {"Day": 0, "Night": 1}
WEATHER_TO_ID = {"Clear": 0, "Rain": 1, "Fog": 2}
FIVE_CLASS_TO_ID = {"Day": 0, "Night": 1, "Rain": 2, "Fog": 3, "Unknown": 4}


class ConditionClassificationDataset(Dataset):
    """
    Dataset for training condition classification models.
    Returns: image tensor, time_label (Day/Night), weather_label (Clear/Rain/Fog), five_class_label.
    """
    def __init__(
        self,
        records: List[Dict[str, Any]],
        image_dir: Path,
        transform: Optional[Callable] = None,
        img_size: int = 224,
    ):
        self.records = records
        self.image_dir = Path(image_dir)
        self.transform = transform or transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        item = self.records[idx]
        img_name = str(item.get("image_name", ""))
        if not img_name.endswith(".jpg"):
            img_name += ".jpg"

        img_path = self.image_dir / img_name
        if not img_path.exists():
            # Fallback search if split subdirectory exists
            split = item.get("split", "train")
            alt_path = self.image_dir / str(split) / img_name
            if alt_path.exists():
                img_path = alt_path

        image = Image.open(img_path).convert("RGB")
        tensor = self.transform(image)

        t_lbl = TIME_TO_ID.get(item.get("time_label", "Day"), 0)
        w_lbl = WEATHER_TO_ID.get(item.get("weather_label", "Clear"), 0)
        five_lbl = FIVE_CLASS_TO_ID.get(item.get("condition", "Day"), 4)

        return {
            "image": tensor,
            "time_label": torch.tensor(t_lbl, dtype=torch.long),
            "weather_label": torch.tensor(w_lbl, dtype=torch.long),
            "five_label": torch.tensor(five_lbl, dtype=torch.long),
            "image_name": img_name,
            "path": str(img_path),
        }


class PairedEnhancementDataset(Dataset):
    """
    Dataset for supervised training of condition enhancers (Night, Rain, Fog)
    using input degraded frames and pseudo-reference target frames.
    """
    def __init__(
        self,
        image_paths: List[Path],
        target_fn: Callable[[Image.Image], Image.Image],
        img_size: int = 256,
        is_train: bool = True,
    ):
        self.image_paths = [Path(p) for p in image_paths if Path(p).is_file()]
        self.target_fn = target_fn
        self.img_size = img_size
        self.is_train = is_train

        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size), Image.Resampling.BILINEAR),
            transforms.ToTensor(),
        ])

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        p = self.image_paths[idx]
        raw_img = Image.open(p).convert("RGB")
        target_img = self.target_fn(raw_img)

        input_tensor = self.transform(raw_img)
        target_tensor = self.transform(target_img)

        return {
            "input": input_tensor,
            "target": target_tensor,
            "path": str(p),
        }


def export_yolo_dataset(
    records: List[Dict[str, Any]],
    source_img_dir: Path,
    output_dataset_dir: Path,
    split: str = "train"
) -> int:
    """
    Exports parsed annotations into YOLO-compliant folder structure:
      <output_dataset_dir>/images/<split>/<image_name>.jpg
      <output_dataset_dir>/labels/<split>/<image_name>.txt
    """
    out_dir = Path(output_dataset_dir)
    img_out = out_dir / "images" / split
    lbl_out = out_dir / "labels" / split
    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)

    exported = 0
    for rec in records:
        name = rec.get("image_name", "")
        if not name.endswith(".jpg"):
            name += ".jpg"
        stem = Path(name).stem

        src_path = Path(source_img_dir) / name
        if not src_path.exists():
            continue

        # Copy image if not already present
        dst_img = img_out / name
        if not dst_img.exists():
            shutil.copy2(src_path, dst_img)

        # Write YOLO label format
        dst_lbl = lbl_out / f"{stem}.txt"
        with open(dst_lbl, "w", encoding="utf-8") as f:
            for obj in rec.get("objects", []):
                cid = obj.get("class_id", 0)
                bx = obj.get("bbox_yolo", [])
                if len(bx) == 4:
                    f.write(f"{cid} {bx[0]:.6f} {bx[1]:.6f} {bx[2]:.6f} {bx[3]:.6f}\n")
        exported += 1

    logger.info("Exported %d images to YOLO format in %s", exported, img_out)
    return exported
