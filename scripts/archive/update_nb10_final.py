import json
from pathlib import Path

def update_notebook():
    nb_path = Path("notebooks/10_final_dataset_creation.ipynb")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Cell 1: Dynamic root discovery and path definitions
    cell1_source = """from pathlib import Path
import json
import shutil
import random
import warnings
import os

import pandas as pd
import numpy as np

# Robust project root discovery (supports notebook, IDE, or terminal execution)
def find_project_root():
    current = Path.cwd().resolve()
    for candidate in [current, current.parent, Path(r"C:\\Users\\ankit\\Desktop\\Adaptive_Road_Vision")]:
        if (candidate / "datasets").exists() and (candidate / "notebooks").exists():
            return candidate
    return current

PROJECT_ROOT = find_project_root()

PROCESSED_IMG = PROJECT_ROOT / "datasets" / "processed" / "images"
PROCESSED_LABEL = PROJECT_ROOT / "datasets" / "processed" / "labels"
PROCESSED_META = PROJECT_ROOT / "datasets" / "processed" / "metadata"
RAW_LABEL = PROJECT_ROOT / "datasets" / "raw" / "BDD100K" / "labels"

SYNTH_META = PROCESSED_META / "cyclegan_fog_accepted.csv"
QUALITY_META = PROCESSED_META / "cyclegan_fog_quality.csv"
GEN_META = PROCESSED_META / "cyclegan_generated_metadata.csv"
BDD_META = PROCESSED_META / "bdd100k_processed_metadata.csv"
CONDITION_META = PROCESSED_META / "condition_labels.csv"

FINAL_ROOT = PROJECT_ROOT / "datasets" / "final"
FINAL_IMG = FINAL_ROOT / "images"
FINAL_LABEL = FINAL_ROOT / "labels"
FINAL_META = FINAL_ROOT / "metadata"

RESULTS_DIR = PROJECT_ROOT / "results" / "dataset"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

for split in ["train", "val", "test"]:
    (FINAL_IMG / split).mkdir(parents=True, exist_ok=True)
    (FINAL_LABEL / split).mkdir(parents=True, exist_ok=True)
FINAL_META.mkdir(parents=True, exist_ok=True)

FINAL_METADATA_CSV = FINAL_META / "final_dataset_metadata.csv"
FINAL_SUMMARY_JSON = RESULTS_DIR / "final_dataset_summary.json"

EXPECTED_SPLITS = {"train": 70000, "val": 10000, "test": 20000}

def link_or_copy(src, dst):
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        try:
            os.link(src, dst)
        except Exception:
            shutil.copy2(src, dst)

print("Project root:", PROJECT_ROOT)
print("Final dataset root:", FINAL_ROOT)
"""

    # Cell 10: find_source_image and find_label with BDD-to-YOLO conversion support
    cell10_source = """VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

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

def find_source_image(row):
    candidates = []
    image_path_value = row.get("image_path")
    image_name_value = row.get("image_name")

    if pd.notna(image_path_value):
        candidates.append(Path(str(image_path_value)))

    if pd.notna(image_name_value):
        name = Path(str(image_name_value))
        candidates.extend([
            PROCESSED_IMG / str(row["split"]) / name.name,
            PROCESSED_IMG / str(row["split"]) / (name.stem + ".jpg"),
            PROCESSED_IMG / str(row["split"]) / (name.stem + ".png"),
        ])

    for p in candidates:
        if p.exists() and p.is_file():
            return p

    return None

def find_or_create_label(row, dst_label_dir):
    split = str(row["split"])
    stem = Path(str(row["image_name"])).stem if pd.notna(row.get("image_name")) else str(row.get("image_id", ""))
    dst_txt = dst_label_dir / f"{stem}.txt"
    if dst_txt.exists():
        return dst_txt

    # Check pre-existing txt in processed labels
    txt_candidates = [
        PROCESSED_LABEL / split / f"{stem}.txt",
    ]
    for tc in txt_candidates:
        if tc.exists() and tc.is_file():
            link_or_copy(tc, dst_txt)
            return dst_txt

    # Check raw BDD json annotations
    json_candidates = [
        RAW_LABEL / split / f"{stem}.json",
    ]
    ann = row.get("annotation_file")
    if pd.notna(ann):
        json_candidates.append(RAW_LABEL / split / Path(str(ann)).name)
        json_candidates.append(PROJECT_ROOT / "datasets" / "raw" / "BDD100K" / str(ann))

    for jc in json_candidates:
        if jc.exists() and jc.is_file():
            lines = bdd_json_to_yolo_lines(jc)
            dst_txt.write_text("\\n".join(lines) + ("\\n" if lines else ""), encoding="utf-8")
            return dst_txt

    return None
"""

    # Cell 12: copy original images and labels
    cell12_source = """original_records = []
missing_images = []
missing_labels = []

for i, row in bdd.iterrows():
    split = str(row["split"])
    source_img = find_source_image(row)

    if source_img is None:
        missing_images.append({
            "image_id": row["image_id"],
            "image_name": row["image_name"],
            "split": split,
        })
        continue

    if (i + 1) % 25000 == 0:
        print(f"Processed {i+1}/100000 records...")
    destination = FINAL_IMG / split / source_img.name
    link_or_copy(source_img, destination)

    label_dst = find_or_create_label(row, FINAL_LABEL / split)
    label_name = label_dst.name if label_dst is not None else None

    if label_name is None:
        missing_labels.append({
            "image_id": row["image_id"],
            "image_name": row["image_name"],
            "split": split,
        })

    original_records.append({
        "record_type": "original",
        "image_id": str(row["image_id"]),
        "image_name": source_img.name,
        "split": split,
        "project_condition": row["project_condition"],
        "source_path": str(source_img),
        "final_image_path": str(destination),
        "label_name": label_name,
        "synthetic": False,
        "source_domain": None,
        "source_image": None,
        "source_id": str(row["image_id"]),
        "generation_model": None,
        "target_condition": None,
        "quality_decision": "ORIGINAL",
    })

print("Original records copied/linked:", len(original_records))
print("Missing original images:", len(missing_images))
print("Missing original labels:", len(missing_labels))

assert not missing_images, (
    "Some processed BDD images could not be found. "
    "Do not continue until the processed image paths are corrected."
)
"""

    # Cell 14: Load accepted synthetic fog metadata with schema normalization
    cell14_source = """synthetic = pd.read_csv(SYNTH_META)

print("Raw synthetic-fog rows:", len(synthetic))

# Filter for accepted images if decision column is present
if "quality_decision" in synthetic.columns:
    synthetic = synthetic[synthetic["quality_decision"].astype(str).str.upper().isin(["ACCEPT", "ACCEPTED", "PASS", "TRUE"])].copy()
elif "decision" in synthetic.columns:
    synthetic = synthetic[synthetic["decision"].astype(str).str.upper().isin(["ACCEPT", "ACCEPTED", "PASS", "TRUE"])].copy()

# Enrich with cyclegan_generated_metadata if available
if GEN_META.exists():
    gen_meta = pd.read_csv(GEN_META)
    synth_key = "file" if "file" in synthetic.columns else ("generated_image" if "generated_image" in synthetic.columns else None)
    if synth_key:
        merge_cols = [c for c in gen_meta.columns if c not in synthetic.columns or c == "generated_image"]
        synthetic = synthetic.merge(gen_meta[merge_cols], left_on=synth_key, right_on="generated_image", how="left")

# Standardize column names
if "generated_path" not in synthetic.columns and "path" in synthetic.columns:
    synthetic["generated_path"] = synthetic["path"]
if "generated_image" not in synthetic.columns and "file" in synthetic.columns:
    synthetic["generated_image"] = synthetic["file"]

if "source_domain" not in synthetic.columns or synthetic["source_domain"].isna().any():
    synthetic["source_domain"] = synthetic["generated_image"].astype(str).apply(
        lambda x: "day" if "dayfog_" in x else ("night" if "nightfog_" in x else "unknown")
    )

if "source_id" not in synthetic.columns or synthetic["source_id"].isna().any():
    synthetic["source_id"] = synthetic["generated_image"].astype(str).apply(
        lambda x: Path(x).stem.replace("dayfog_", "").replace("nightfog_", "").replace("rainfog_", "")
    )

if "source_image" not in synthetic.columns or synthetic["source_image"].isna().any():
    synthetic["source_image"] = synthetic["source_id"].apply(lambda x: f"{x}.jpg")

if "target_condition" not in synthetic.columns or synthetic["target_condition"].isna().any():
    synthetic["target_condition"] = "Fog"

if "generation_model" not in synthetic.columns or synthetic["generation_model"].isna().any():
    synthetic["generation_model"] = synthetic["source_domain"] + "_to_fog"

# Resolve generated image paths and ensure all exist
def resolve_synth_path(p_str):
    p = Path(str(p_str))
    if p.exists() and p.is_file():
        return p
    # Fallback to current project root path
    alt = PROJECT_ROOT / "datasets" / "cyclegan" / ("generated_day_fog" if "dayfog_" in p.name else "generated_night_fog") / p.name
    if alt.exists():
        return alt
    return p

synthetic["generated_path"] = synthetic["generated_path"].apply(resolve_synth_path).astype(str)

missing_generated = [
    p for p in synthetic["generated_path"]
    if not Path(p).exists()
]

print("Accepted synthetic-fog rows:", len(synthetic))
print("Missing generated files:", len(missing_generated))

assert not missing_generated, f"{len(missing_generated)} accepted synthetic-fog files do not exist."
"""

    # Cell 18: Copy accepted synthetic fog into final/train and create/copy labels
    cell18_source = """synthetic_records = []

for _, row in synthetic.iterrows():
    source_path = Path(row["generated_path"])

    # Distinct final filename for provenance and collision prevention.
    final_name = f"synthetic_fog_{row['source_domain']}_{row['source_id']}_{row['generated_image']}"

    destination = FINAL_IMG / "train" / final_name
    link_or_copy(source_path, destination)

    # Copy source training label if available (CycleGAN preserves geometry)
    src_label = FINAL_LABEL / "train" / f"{row['source_id']}.txt"
    dst_label = FINAL_LABEL / "train" / f"{Path(final_name).stem}.txt"
    label_name = None
    if src_label.exists():
        link_or_copy(src_label, dst_label)
        label_name = dst_label.name
    elif not dst_label.exists():
        # Create empty background label file if source image has no detected objects
        dst_label.write_text("", encoding="utf-8")
        label_name = dst_label.name

    synthetic_records.append({
        "record_type": "synthetic_fog",
        "image_id": f"synthetic_{row['source_domain']}_{row['source_id']}",
        "image_name": final_name,
        "split": "train",
        "project_condition": "Fog",
        "source_path": str(source_path),
        "final_image_path": str(destination),
        "label_name": label_name,
        "synthetic": True,
        "source_domain": row["source_domain"],
        "source_image": row["source_image"],
        "source_id": str(row["source_id"]),
        "generation_model": row.get(
            "generation_model",
            f"{row['source_domain']}_to_fog"
        ),
        "target_condition": "Fog",
        "quality_decision": "ACCEPT",
    })

print("Synthetic fog added to final/train:", len(synthetic_records))
"""

    # Replace cell contents
    nb["cells"][1]["source"] = [l + "\n" for l in cell1_source.strip().splitlines()]
    nb["cells"][10]["source"] = [l + "\n" for l in cell10_source.strip().splitlines()]
    nb["cells"][12]["source"] = [l + "\n" for l in cell12_source.strip().splitlines()]
    nb["cells"][14]["source"] = [l + "\n" for l in cell14_source.strip().splitlines()]
    nb["cells"][18]["source"] = [l + "\n" for l in cell18_source.strip().splitlines()]

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

    print(f"Successfully updated {nb_path}")

if __name__ == "__main__":
    update_notebook()
