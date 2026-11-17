import os
import json
from pathlib import Path
import pandas as pd
import numpy as np

def find_project_root():
    current = Path.cwd().resolve()
    for candidate in [current, current.parent, Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")]:
        if (candidate / "datasets").exists() and (candidate / "notebooks").exists():
            return candidate
    return current

PROJECT_ROOT = find_project_root()
print("1. Discovered PROJECT_ROOT:", PROJECT_ROOT)
assert PROJECT_ROOT.exists()

PROCESSED_META = PROJECT_ROOT / "datasets" / "processed" / "metadata"
PROCESSED_LABEL = PROJECT_ROOT / "datasets" / "processed" / "labels"
PROCESSED_IMG = PROJECT_ROOT / "datasets" / "processed" / "images"
RAW_LABEL = PROJECT_ROOT / "datasets" / "raw" / "BDD100K" / "labels"

# 2. Test synthetic loading & normalization
SYNTH_META = PROCESSED_META / "cyclegan_fog_accepted.csv"
assert SYNTH_META.exists(), "cyclegan_fog_accepted.csv missing"

synth = pd.read_csv(SYNTH_META)
if "quality_decision" in synth.columns:
    synth = synth[synth["quality_decision"].astype(str).str.upper().isin(["ACCEPT", "ACCEPTED", "PASS", "TRUE"])].copy()
elif "decision" in synth.columns:
    synth = synth[synth["decision"].astype(str).str.upper().isin(["ACCEPT", "ACCEPTED", "PASS", "TRUE"])].copy()

# Merge with cyclegan_generated_metadata if available
gen_meta_path = PROCESSED_META / "cyclegan_generated_metadata.csv"
if gen_meta_path.exists():
    gen_meta = pd.read_csv(gen_meta_path)
    synth_key = "file" if "file" in synth.columns else ("generated_image" if "generated_image" in synth.columns else None)
    if synth_key:
        merge_cols = [c for c in gen_meta.columns if c not in synth.columns or c == "generated_image"]
        synth = synth.merge(gen_meta[merge_cols], left_on=synth_key, right_on="generated_image", how="left")

if "generated_path" not in synth.columns and "path" in synth.columns:
    synth["generated_path"] = synth["path"]
if "generated_image" not in synth.columns and "file" in synth.columns:
    synth["generated_image"] = synth["file"]

if "source_domain" not in synth.columns or synth["source_domain"].isna().any():
    synth["source_domain"] = synth["generated_image"].astype(str).apply(
        lambda x: "day" if "dayfog_" in x else ("night" if "nightfog_" in x else "unknown")
    )

if "source_id" not in synth.columns or synth["source_id"].isna().any():
    synth["source_id"] = synth["generated_image"].astype(str).apply(
        lambda x: Path(x).stem.replace("dayfog_", "").replace("nightfog_", "").replace("rainfog_", "")
    )

if "source_image" not in synth.columns or synth["source_image"].isna().any():
    synth["source_image"] = synth["source_id"].apply(lambda x: f"{x}.jpg")

if "target_condition" not in synth.columns or synth["target_condition"].isna().any():
    synth["target_condition"] = "Fog"

if "generation_model" not in synth.columns or synth["generation_model"].isna().any():
    synth["generation_model"] = synth["source_domain"] + "_to_fog"

print(f"2. Synthetic metadata normalized: {len(synth)} accepted rows.")
print("   Columns include required:", all(c in synth.columns for c in ["generated_image", "generated_path", "source_image", "source_id", "source_domain", "target_condition"]))

# 3. Test BDD metadata and source matching
bdd = pd.read_csv(PROCESSED_META / "bdd100k_processed_metadata.csv")
train_ids = set(bdd.loc[bdd["split"] == "train", "image_id"].astype(str))
val_ids = set(bdd.loc[bdd["split"] == "val", "image_id"].astype(str))
test_ids = set(bdd.loc[bdd["split"] == "test", "image_id"].astype(str))

synth["source_id"] = synth["source_id"].astype(str)
overlap_train = synth["source_id"].isin(train_ids).sum()
overlap_val = synth["source_id"].isin(val_ids).sum()
overlap_test = synth["source_id"].isin(test_ids).sum()

print(f"3. Synthetic provenance check:")
print(f"   Matches train: {overlap_train} / {len(synth)}")
print(f"   Matches val: {overlap_val}")
print(f"   Matches test: {overlap_test}")
assert overlap_train == len(synth)
assert overlap_val == 0
assert overlap_test == 0

# 4. Test label resolution and conversion
CATEGORY_MAP = {
    'pedestrian': 'person', 'person': 'person', 'rider': 'rider', 'car': 'car',
    'truck': 'truck', 'bus': 'bus', 'train': 'train', 'motor': 'motorcycle',
    'motorcycle': 'motorcycle', 'bike': 'bicycle', 'bicycle': 'bicycle',
    'traffic light': 'traffic light', 'traffic sign': 'traffic sign'
}
CLASS_NAMES = ['person', 'rider', 'car', 'truck', 'bus', 'train', 'motorcycle', 'bicycle', 'traffic light', 'traffic sign']
CLASS_TO_IDX = {name: idx for idx, name in enumerate(CLASS_NAMES)}

def bdd_json_to_yolo_lines(json_path, img_w=1280.0, img_h=720.0):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        lines = []
        frames = data.get('frames', [])
        for frame in frames:
            for obj in frame.get('objects', []):
                cat = obj.get('category')
                norm_cat = CATEGORY_MAP.get(cat)
                if norm_cat is None or norm_cat not in CLASS_TO_IDX:
                    continue
                box = obj.get('box2d')
                if not box:
                    continue
                x1, y1, x2, y2 = float(box['x1']), float(box['y1']), float(box['x2']), float(box['y2'])
                x1 = max(0.0, min(img_w, x1))
                x2 = max(0.0, min(img_w, x2))
                y1 = max(0.0, min(img_h, y1))
                y2 = max(0.0, min(img_h, y2))
                w = x2 - x1
                h = y2 - y1
                if w <= 0 or h <= 0:
                    continue
                x_center = (x1 + x2) / 2.0 / img_w
                y_center = (y1 + y2) / 2.0 / img_h
                norm_w = w / img_w
                norm_h = h / img_h
                cls_idx = CLASS_TO_IDX[norm_cat]
                lines.append(f"{cls_idx} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")
        return lines
    except Exception:
        return []

sample_id = bdd.iloc[0]["image_id"]
sample_json = RAW_LABEL / "train" / f"{sample_id}.json"
sample_lines = bdd_json_to_yolo_lines(sample_json)
print(f"4. Sample label conversion for {sample_id}: {len(sample_lines)} boxes generated.")
assert len(sample_lines) > 0

print("All verification steps PASSED!")
