import os
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as transforms
from tqdm import tqdm

from src.cyclegan.train import CycleGANGenerator

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
MODELS_DIR = PROJECT_ROOT / "models" / "cyclegan"
CYCLEGAN_DIR = PROJECT_ROOT / "datasets" / "cyclegan"
META_DIR = PROJECT_ROOT / "datasets" / "processed" / "metadata"

DAY_OUT_DIR = CYCLEGAN_DIR / "generated_day_fog"
NIGHT_OUT_DIR = CYCLEGAN_DIR / "generated_night_fog"
DAY_OUT_DIR.mkdir(parents=True, exist_ok=True)
NIGHT_OUT_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE = 256


def denorm_to_pil(tensor):
    t = tensor.detach().cpu().squeeze(0)
    t = (t * 0.5 + 0.5).clamp(0, 1)
    np_img = (t.permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)
    return Image.fromarray(np_img)


def generate_synthetic_fog(num_per_domain=300):
    print("=======================================================")
    print(f"Generating Synthetic Fog Images ({num_per_domain} per domain)")
    print("=======================================================")

    day_candidates = [
        MODELS_DIR / "day_to_fog" / "checkpoint_best.pth",
        MODELS_DIR / "day_to_fog" / "checkpoint_final.pth",
        MODELS_DIR / "day_to_fog_best.pth"
    ]
    night_candidates = [
        MODELS_DIR / "night_to_fog" / "checkpoint_best.pth",
        MODELS_DIR / "night_to_fog" / "checkpoint_final.pth",
        MODELS_DIR / "night_to_fog_best.pth"
    ]

    day_ckpt = next((p for p in day_candidates if p.exists()), None)
    night_ckpt = next((p for p in night_candidates if p.exists()), None)

    assert day_ckpt is not None, f"Missing Day->Fog checkpoint. Checked: {[str(p) for p in day_candidates]}"
    assert night_ckpt is not None, f"Missing Night->Fog checkpoint. Checked: {[str(p) for p in night_candidates]}"

    def _extract_generator_weights(path):
        payload = torch.load(path, map_location=DEVICE)
        for key in ["G_AB_state_dict", "generator", "generator_state_dict", "netG", "G_A"]:
            if key in payload:
                return payload[key]
        return payload

    G_day = CycleGANGenerator().to(DEVICE)
    G_day.load_state_dict(_extract_generator_weights(day_ckpt))
    G_day.eval()

    G_night = CycleGANGenerator().to(DEVICE)
    G_night.load_state_dict(_extract_generator_weights(night_ckpt))
    G_night.eval()

    source_csv = META_DIR / "cyclegan_source_images.csv"
    assert source_csv.exists(), f"Missing: {source_csv}"
    src_df = pd.read_csv(source_csv)

    # Strictly train split
    assert (src_df["split"] == "train").all(), "Leakage risk: source images are not all train!"

    day_sources = src_df[src_df["cyclegan_source_domain"] == "Day"].head(num_per_domain)
    night_sources = src_df[src_df["cyclegan_source_domain"] == "Night"].head(num_per_domain)

    transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    raw_dir = PROJECT_ROOT / "datasets" / "raw" / "BDD100K" / "images" / "100k" / "train"

    records = []

    # Generate Day -> Fog
    print(f"Generating {len(day_sources)} Day -> Fog images...")
    with torch.no_grad():
        for _, row in day_sources.iterrows():
            img_name = str(row["image_name"])
            if not img_name.endswith(".jpg"):
                img_name += ".jpg"
            src_path = raw_dir / img_name
            if not src_path.exists():
                src_path = CYCLEGAN_DIR / "day" / img_name
            if not src_path.exists():
                continue

            img = Image.open(src_path).convert("RGB")
            tensor = transform(img).unsqueeze(0).to(DEVICE)
            fake_fog = G_day(tensor)
            out_pil = denorm_to_pil(fake_fog)

            out_filename = f"synth_fog_day_{Path(img_name).stem}.jpg"
            out_path = DAY_OUT_DIR / out_filename
            out_pil.save(out_path, quality=92)

            records.append({
                "generated_image": out_filename,
                "generated_path": str(out_path),
                "source_image": img_name,
                "source_id": Path(img_name).stem,
                "source_domain": "Day",
                "target_condition": "Fog",
                "generation_model": "cyclegan_day_to_fog",
                "split": "train"
            })

    # Generate Night -> Fog
    print(f"Generating {len(night_sources)} Night -> Fog images...")
    with torch.no_grad():
        for _, row in night_sources.iterrows():
            img_name = str(row["image_name"])
            if not img_name.endswith(".jpg"):
                img_name += ".jpg"
            src_path = raw_dir / img_name
            if not src_path.exists():
                src_path = CYCLEGAN_DIR / "night" / img_name
            if not src_path.exists():
                continue

            img = Image.open(src_path).convert("RGB")
            tensor = transform(img).unsqueeze(0).to(DEVICE)
            fake_fog = G_night(tensor)
            out_pil = denorm_to_pil(fake_fog)

            out_filename = f"synth_fog_night_{Path(img_name).stem}.jpg"
            out_path = NIGHT_OUT_DIR / out_filename
            out_pil.save(out_path, quality=92)

            records.append({
                "generated_image": out_filename,
                "generated_path": str(out_path),
                "source_image": img_name,
                "source_id": Path(img_name).stem,
                "source_domain": "Night",
                "target_condition": "Fog",
                "generation_model": "cyclegan_night_to_fog",
                "split": "train"
            })

    out_df = pd.DataFrame(records)
    out_csv = META_DIR / "cyclegan_generated_metadata.csv"
    out_df.to_csv(out_csv, index=False)
    print(f"Saved generated metadata: {out_csv} ({len(out_df)} images generated)")
    return out_df


if __name__ == "__main__":
    generate_synthetic_fog()
