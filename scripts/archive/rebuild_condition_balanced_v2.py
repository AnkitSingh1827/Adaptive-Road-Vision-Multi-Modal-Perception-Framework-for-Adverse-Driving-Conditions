import os
import sys
import json
import shutil
import random
import math
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
from PIL import Image

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

PROJECT_ROOT = Path(".").resolve()
META_DIR = PROJECT_ROOT / "datasets" / "processed" / "metadata"
BDD_META = META_DIR / "bdd100k_processed_metadata.csv"
OUTPUT_ROOT = PROJECT_ROOT / "datasets" / "final_condition_balanced_v2"
REPORT_ROOT = PROJECT_ROOT / "results" / "dataset_balance_audit_v2"
REPORT_ROOT.mkdir(parents=True, exist_ok=True)

SPLIT_MODE = "recommended_70_train"
TARGET_TOTAL = 15000
USE_ALL_ACCEPTED_SYNTHETIC = True
SYNTHETIC_TRAIN_CAP = None
MIN_ORIGINAL_TRAIN_IMAGES = 1000
BALANCE_CONDITIONS = ["Day", "Night", "Rain", "Fog"]
INCLUDE_UNKNOWN = True
REQUIRE_LABELS = True

print("Project root:", PROJECT_ROOT)

# 1. Load BDD
bdd = pd.read_csv(BDD_META)
if "image_id" not in bdd.columns:
    bdd["image_id"] = bdd["image_name"].astype(str).map(lambda x: Path(x).stem)
bdd["split"] = bdd["split"].astype(str).str.lower().str.strip()
bdd["project_condition"] = bdd["project_condition"].fillna("Unknown").astype(str).str.strip().str.title()
aliases = {"Daytime": "Day", "Nighttime": "Night", "Rainy": "Rain", "Foggy": "Fog"}
bdd["project_condition"] = bdd["project_condition"].replace(aliases)

# 2. Locate original images and labels
RAW_ROOT = PROJECT_ROOT / "datasets" / "raw" / "BDD100K"
RAW_IMG_ROOT = RAW_ROOT / "images" / "100k"
RAW_LABEL_ROOT = RAW_ROOT / "labels"
IMG_ROOT = PROJECT_ROOT / "datasets" / "processed" / "images"
LABEL_ROOT = PROJECT_ROOT / "datasets" / "processed" / "labels"

existing_images = {}
existing_labels = {}
for sp in ["train", "val", "test"]:
    img_dir = RAW_IMG_ROOT / sp
    lab_dir = RAW_LABEL_ROOT / sp
    existing_images[sp] = set(os.listdir(img_dir)) if img_dir.exists() else set()
    existing_labels[sp] = set(os.listdir(lab_dir)) if lab_dir.exists() else set()

splits = bdd["split"].values
stems = bdd["image_name"].astype(str).map(lambda x: Path(x).stem).values

resolved_imgs = [
    str(RAW_IMG_ROOT / sp / f"{st}.jpg") if f"{st}.jpg" in existing_images.get(sp, set())
    else (str(IMG_ROOT / sp / f"{st}.jpg") if (IMG_ROOT / sp / f"{st}.jpg").is_file() else None)
    for sp, st in zip(splits, stems)
]
resolved_labs = [
    str(RAW_LABEL_ROOT / sp / f"{st}.json") if f"{st}.json" in existing_labels.get(sp, set())
    else (str(LABEL_ROOT / sp / f"{st}.txt") if (LABEL_ROOT / sp / f"{st}.txt").is_file() else None)
    for sp, st in zip(splits, stems)
]

pool = bdd.copy()
pool["resolved_image"] = resolved_imgs
pool["resolved_label"] = resolved_labs
pool["image_exists"] = pool["resolved_image"].notna()
pool["label_exists"] = pool["resolved_label"].notna()
pool = pool[pool.image_exists & pool.label_exists].copy()
print("Usable candidates:", len(pool))

# 3. Find synthetic
synth_candidates = [
    META_DIR / "cyclegan_fog_accepted.csv",
    PROJECT_ROOT / "results" / "cyclegan" / "cyclegan_fog_accepted.csv",
    PROJECT_ROOT / "datasets" / "cyclegan" / "cyclegan_fog_accepted.csv",
]
SYNTH_META = next((p for p in synth_candidates if p.exists()), None)
sraw = pd.read_csv(SYNTH_META)
dec_col = next((c for c in ["decision", "quality_decision", "status"] if c in sraw.columns), None)
if dec_col:
    s = sraw[sraw[dec_col].astype(str).str.upper().isin(["ACCEPT", "ACCEPTED", "PASS", "TRUE", "1", "YES"])].copy()
else:
    s = sraw.copy()

def resolve_synth(row):
    for col in ["generated_path", "path", "image_path", "file"]:
        if col in row and pd.notna(row[col]):
            p = Path(str(row[col]))
            if p.is_file():
                return str(p)
            if (PROJECT_ROOT / p).is_file():
                return str(PROJECT_ROOT / p)
    fname = str(row.get("generated_image", row.get("file", "")))
    for folder in [PROJECT_ROOT / "datasets" / "cyclegan" / "generated_day_fog",
                   PROJECT_ROOT / "datasets" / "cyclegan" / "generated_night_fog"]:
        q = folder / fname
        if q.is_file():
            return str(q)
    return None

s["resolved_synthetic_path"] = s.apply(resolve_synth, axis=1)
s = s[s.resolved_synthetic_path.notna()].drop_duplicates("resolved_synthetic_path").reset_index(drop=True)
synthetic_count = len(s)
synth_to_use = synthetic_count
print("Accepted synthetic fog images:", synthetic_count)

# 4. Splits & targets
split_ratios = {"train": 0.70, "test": 0.20, "val": 0.10}
split_targets = {k: int(round(TARGET_TOTAL * v)) for k, v in split_ratios.items()}
split_targets[list(split_targets.keys())[0]] += TARGET_TOTAL - sum(split_targets.values())

orig_targets = {k: int(split_targets[k]) for k in split_targets}
orig_targets["train"] -= int(synth_to_use)
print("Original targets:", orig_targets)

# 5. Fast label parser
CATEGORY_MAP = {
    "pedestrian": "person", "person": "person", "rider": "rider", "car": "car",
    "truck": "truck", "bus": "bus", "train": "train", "motor": "motorcycle",
    "motorcycle": "motorcycle", "bike": "bicycle", "bicycle": "bicycle",
    "traffic light": "traffic light", "traffic sign": "traffic sign",
}
CLASS_NAMES = ["person", "rider", "car", "truck", "bus", "train", "motorcycle", "bicycle", "traffic light", "traffic sign"]
CLASS_TO_IDX = {name: idx for idx, name in enumerate(CLASS_NAMES)}

def bdd_json_to_yolo_lines(json_path, image_path):
    with Image.open(image_path) as im:
        img_w, img_h = im.size
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    lines = []
    for frame in data.get("frames", []):
        for obj in frame.get("objects", []):
            cat = CATEGORY_MAP.get(str(obj.get("category", "")).strip().lower())
            if cat is None or cat not in CLASS_TO_IDX:
                continue
            box = obj.get("box2d")
            if not box:
                continue
            x1, y1, x2, y2 = float(box["x1"]), float(box["y1"]), float(box["x2"]), float(box["y2"])
            x1 = max(0.0, min(float(img_w), x1))
            x2 = max(0.0, min(float(img_w), x2))
            y1 = max(0.0, min(float(img_h), y1))
            y2 = max(0.0, min(float(img_h), y2))
            w, h = x2 - x1, y2 - y1
            if w <= 0 or h <= 0:
                continue
            lines.append(f"{CLASS_TO_IDX[cat]} {(x1+x2)/2/img_w:.6f} {(y1+y2)/2/img_h:.6f} {w/img_w:.6f} {h/img_h:.6f}")
    return lines

# 6. Allocate quotas with fixed Unknown
def allocate_condition_quotas(candidates, n, conditions, prioritize_unknown=True):
    capacities = {c: int((candidates["project_condition"] == c).sum()) for c in conditions}
    quotas = {c: 0 for c in conditions}
    left = int(n)

    # Allocate all available Unknown images up to capacity
    if prioritize_unknown and capacities.get("Unknown", 0) > 0 and left > 0:
        take = min(capacities["Unknown"], left)
        quotas["Unknown"] = take
        left -= take

    major = [c for c in ["Day", "Fog", "Night", "Rain"] if c in capacities]
    while left > 0:
        active = [c for c in major if quotas[c] < capacities[c]]
        if not active:
            break
        per = max(1, left // len(active))
        progressed = False
        for c in active:
            take = min(per, capacities[c] - quotas[c], left)
            quotas[c] += take
            left -= take
            progressed = progressed or take > 0
            if left == 0:
                break
        if not progressed:
            break

    while left > 0:
        active = [c for c in conditions if quotas.get(c, 0) < capacities.get(c, 0)]
        if not active:
            raise ValueError(f"Not enough candidates for n={n}")
        active_major = [c for c in major if c in active]
        c = min(active_major, key=lambda x: quotas.get(x, 0)) if active_major else active[0]
        quotas[c] = quotas.get(c, 0) + 1
        left -= 1
    return {k: v for k, v in quotas.items() if v > 0}

ALL_CONDITIONS = ["Day", "Fog", "Night", "Rain", "Unknown"]
source_map = {"train": "train", "test": "test", "val": "val"}
selected_parts = []

for out_split, n in orig_targets.items():
    source_split = source_map[out_split]
    candidates = pool[(pool["split"] == source_split) & pool["project_condition"].isin(ALL_CONDITIONS)].copy()
    quotas = allocate_condition_quotas(candidates, n, ALL_CONDITIONS, prioritize_unknown=True)
    print(f"{out_split} quotas:", quotas)
    for j, (cond, take) in enumerate(quotas.items()):
        condition_pool = candidates[candidates["project_condition"] == cond]
        chosen = condition_pool.sample(n=take, random_state=SEED + len(selected_parts)*100 + j).copy()
        chosen["target_split"] = out_split
        chosen["record_type"] = "original"
        selected_parts.append(chosen)

selected_originals = pd.concat(selected_parts, ignore_index=True)
print("Originals selected:", len(selected_originals))
print("Unknown in originals:", (selected_originals["project_condition"] == "Unknown").sum())

# 7. Match synthetic fog sources
train_source = pool[pool.split == "train"].copy()
lookup = {}
for _, r in train_source.iterrows():
    ann = r.get("resolved_label")
    info = {"image_id": str(r["image_id"]), "label": str(ann), "image": str(r["resolved_image"]), "condition": str(r["project_condition"])}
    for k in [Path(str(r["image_name"])).stem.lower(), Path(str(r["resolved_image"])).stem.lower(), str(r["image_id"]).lower()]:
        lookup.setdefault(k, info)

def synth_source_match(row):
    candidates = []
    for c in ["source_id", "source_image_id", "source_image", "source_filename", "source_name", "source_path", "source_file", "image_id"]:
        if c in row and pd.notna(row[c]):
            candidates.append(Path(str(row[c])).stem.lower())
    stem = Path(str(row["resolved_synthetic_path"])).stem.lower()
    for prefix in ["day_to_fog_", "night_to_fog_", "dayfog_", "nightfog_", "synthetic_fog_"]:
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
    candidates += [stem, Path(stem).stem.lower()]
    for k in candidates:
        if k in lookup:
            return lookup[k]
    return None

s["source_match"] = s.apply(synth_source_match, axis=1)
s["source_train_image_id"] = s["source_match"].map(lambda x: x["image_id"] if isinstance(x, dict) else None)
s["source_label_path"] = s["source_match"].map(lambda x: x["label"] if isinstance(x, dict) else None)
s["source_image_path"] = s["source_match"].map(lambda x: x["image"] if isinstance(x, dict) else None)
s_used = s.iloc[:synth_to_use].copy().reset_index(drop=True)
print("Synthetic matched:", len(s_used))

# 8. Fast copy or link to OUTPUT_ROOT
for split in ["train", "test", "val"]:
    (OUTPUT_ROOT / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "labels" / split).mkdir(parents=True, exist_ok=True)
(OUTPUT_ROOT / "metadata").mkdir(parents=True, exist_ok=True)

def copy_file(src, dst):
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)

def write_label(src_lab_path, dst_lab_path, source_image_path):
    src_lab_path, dst_lab_path = Path(src_lab_path), Path(dst_lab_path)
    if dst_lab_path.exists():
        return
    dst_lab_path.parent.mkdir(parents=True, exist_ok=True)
    if src_lab_path.suffix.lower() == ".json":
        lines = bdd_json_to_yolo_lines(src_lab_path, source_image_path)
        dst_lab_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    else:
        shutil.copy2(src_lab_path, dst_lab_path)

out_rows = []
for _, r in selected_originals.iterrows():
    split = str(r["target_split"])
    src_img = Path(str(r["resolved_image"]))
    out_name = f"bdd_{r['image_id']}_{src_img.name}"
    dst_img = OUTPUT_ROOT / "images" / split / out_name
    dst_lab = OUTPUT_ROOT / "labels" / split / (Path(out_name).stem + ".txt")
    copy_file(src_img, dst_img)
    write_label(r["resolved_label"], dst_lab, r["resolved_image"])
    out_rows.append({
        "image_id": str(r["image_id"]), "image_name": out_name, "split": split,
        "condition": str(r["project_condition"]), "synthetic": False,
        "source_split": str(r["split"]), "source_id": str(r["image_id"]),
        "source_image": str(src_img), "image_path": str(dst_img), "label_path": str(dst_lab)
    })

for i, r in s_used.iterrows():
    src = Path(str(r["resolved_synthetic_path"]))
    source_id = str(r["source_train_image_id"])
    out_name = f"cyclegan_fog_{source_id}_{i:05d}{src.suffix.lower() or '.jpg'}"
    dst_img = OUTPUT_ROOT / "images" / "train" / out_name
    dst_lab = OUTPUT_ROOT / "labels" / "train" / (Path(out_name).stem + ".txt")
    copy_file(src, dst_img)
    write_label(r["source_label_path"], dst_lab, r["source_image_path"])
    out_rows.append({
        "image_id": f"synthetic_{source_id}_{i:05d}", "image_name": out_name, "split": "train",
        "condition": "Fog", "synthetic": True, "source_split": "train", "source_id": source_id,
        "source_image": str(src), "image_path": str(dst_img), "label_path": str(dst_lab)
    })

final_meta = pd.DataFrame(out_rows)
final_meta.to_csv(OUTPUT_ROOT / "metadata" / "final_dataset_metadata.csv", index=False)
print("Final metadata saved. Total rows:", len(final_meta))

# 9. Verify assertions
expected_unknown = sum(
    min(
        int(((pool["split"] == src_split) & (pool["project_condition"] == "Unknown")).sum()),
        int(orig_targets[out_split])
    )
    for out_split, src_split in [("train", "train"), ("test", "test"), ("val", "val")]
)
actual_unknown = int((final_meta["condition"] == "Unknown").sum())
print(f"expected_unknown: {expected_unknown}, actual_unknown: {actual_unknown}")
assert actual_unknown == expected_unknown, f"Mismatch: expected {expected_unknown}, got {actual_unknown}"
print("ASSERTION PASSED SUCCESSFULLY!")
