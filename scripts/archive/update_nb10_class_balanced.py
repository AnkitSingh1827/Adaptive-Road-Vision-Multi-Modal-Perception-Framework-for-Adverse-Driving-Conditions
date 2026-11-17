import json
from pathlib import Path

def update_notebook():
    nb_path = Path("notebooks/10_class_balanced_10k_dataset_creation.ipynb")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Clean markdown in Cell 0
    cell0_source = """# Notebook 10 — Class-Balanced 10K Dataset + CycleGAN Fog (Train Only)

**Project:** Adaptive Road Vision Enhancement and Risk-Aware Object Detection  
**Purpose:** Create exactly 10,000 unique original images with a 70/10/20 split, actively balance **YOLO object-class instances** within the 7,000-image original training subset, then add all accepted CycleGAN fog images to training only.

## Class-balancing strategy

- **Train:** select 7,000 original images from the original BDD100K `train` pool using a label-aware greedy sampler that prioritizes underrepresented YOLO classes.
- **Validation:** select 1,000 original images from the original `val` split, stratified by condition.
- **Test:** select 2,000 original images from the original `test` split, stratified by condition.
- Add all accepted CycleGAN fog images to **train only**; copy source YOLO labels only after source provenance resolves to an original training image.
- Produce per-class instance/image counts before and after selection so class balance is measured, not assumed.

**Output:** `datasets/final_10k/` (separate, safe build from `datasets/final/`).
"""

    # Cell 1: Dynamic root discovery, link_or_copy, path setup
    cell1_source = """from pathlib import Path
import json, shutil, hashlib, random, math, warnings, os
import numpy as np
import pandas as pd
from PIL import Image

warnings.filterwarnings("ignore")
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

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

BDD_META = PROCESSED_META / "bdd100k_processed_metadata.csv"
SYNTH_META_CANDIDATES = [
    PROCESSED_META / "cyclegan_fog_accepted.csv",
    PROCESSED_META / "cyclegan_fog_quality.csv",
    PROJECT_ROOT / "results" / "cyclegan" / "cyclegan_fog_accepted.csv",
    PROJECT_ROOT / "datasets" / "cyclegan" / "cyclegan_fog_accepted.csv",
]
GEN_META = PROCESSED_META / "cyclegan_generated_metadata.csv"

FINAL_ROOT = PROJECT_ROOT / "datasets" / "final_10k"
FINAL_IMG = FINAL_ROOT / "images"
FINAL_LABEL = FINAL_ROOT / "labels"
FINAL_META = FINAL_ROOT / "metadata"
RESULTS_DIR = PROJECT_ROOT / "results" / "dataset_10k"

SPLIT_TARGETS = {"train": 7000, "val": 1000, "test": 2000}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
REQUIRE_YOLO_LABELS = True
REBUILD_OUTPUT = True  # Writes to datasets/final_10k, not datasets/final

for split in SPLIT_TARGETS:
    (FINAL_IMG / split).mkdir(parents=True, exist_ok=True)
    (FINAL_LABEL / split).mkdir(parents=True, exist_ok=True)
FINAL_META.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def link_or_copy(src, dst):
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        try:
            os.link(src, dst)
        except Exception:
            shutil.copy2(src, dst)

assert PROJECT_ROOT.exists(), f"Project root not found: {PROJECT_ROOT}"
assert BDD_META.exists(), f"Missing metadata: {BDD_META}"
SYNTH_META = next((p for p in SYNTH_META_CANDIDATES if p.exists()), None)
assert SYNTH_META is not None, "Accepted CycleGAN fog CSV not found. Check Notebook 09 output path."

print("Project:", PROJECT_ROOT)
print("BDD metadata:", BDD_META)
print("Synthetic fog metadata:", SYNTH_META)
print("Output (separate, safe build):", FINAL_ROOT)
"""

    # Cell 5: resolve_image and resolve_label with automatic BDD-to-YOLO conversion
    cell5_source = """CATEGORY_MAP = {
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

def first_file(paths):
    for p in paths:
        if p is not None:
            p = Path(str(p))
            if p.exists() and p.is_file():
                return p
    return None

def resolve_image(row):
    split = str(row["split"])
    name = Path(str(row["image_name"]))
    candidates = []
    if "image_path" in row and pd.notna(row.get("image_path")):
        candidates.append(Path(str(row.get("image_path"))))
    for base_name in [name.name, name.stem + ".jpg", name.stem + ".png", name.stem + ".jpeg"]:
        candidates.append(PROCESSED_IMG / split / base_name)
    return first_file(candidates)

def resolve_label(row, image_path=None):
    split = str(row["split"])
    stem = Path(image_path).stem if image_path is not None else Path(str(row.get("image_name"))).stem

    # 1. Existing txt in processed labels
    txt_candidates = [
        PROCESSED_LABEL / split / f"{stem}.txt"
    ]
    ann = row.get("annotation_file")
    if pd.notna(ann) and Path(str(ann)).suffix.lower() == ".txt":
        txt_candidates.append(PROCESSED_LABEL / split / Path(str(ann)).name)
    f_txt = first_file(txt_candidates)
    if f_txt:
        return f_txt

    # 2. Convert from raw BDD json if txt not yet generated
    json_candidates = [
        RAW_LABEL / split / f"{stem}.json",
    ]
    if pd.notna(ann):
        json_candidates.append(RAW_LABEL / split / Path(str(ann)).name)
        json_candidates.append(PROJECT_ROOT / "datasets" / "raw" / "BDD100K" / str(ann))
    f_json = first_file(json_candidates)
    if f_json:
        # Cache converted txt into PROCESSED_LABEL / split
        out_txt = PROCESSED_LABEL / split / f"{stem}.txt"
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        if not out_txt.exists():
            lines = bdd_json_to_yolo_lines(f_json)
            out_txt.write_text("\\n".join(lines) + ("\\n" if lines else ""), encoding="utf-8")
        return out_txt

    return None

resolved = []
for _, row in bdd.iterrows():
    img = resolve_image(row)
    label = resolve_label(row, img)
    resolved.append({
        **row.to_dict(),
        "resolved_image": str(img) if img else None,
        "resolved_label": str(label) if label else None,
        "image_exists": img is not None,
        "yolo_label_exists": label is not None
    })

resolved_df = pd.DataFrame(resolved)
print("Images resolved:", int(resolved_df["image_exists"].sum()), "/", len(resolved_df))
print("YOLO labels resolved:", int(resolved_df["yolo_label_exists"].sum()), "/", len(resolved_df))
resolved_df.groupby(["split", "project_condition"])[["image_exists", "yolo_label_exists"]].sum().to_csv(RESULTS_DIR / "source_resolution_by_condition.csv")

if not resolved_df["image_exists"].all():
    missing = resolved_df.loc[~resolved_df["image_exists"], ["split", "image_name", "image_id"]]
    missing.to_csv(RESULTS_DIR / "missing_source_images.csv", index=False)
    raise FileNotFoundError(f"{len(missing)} source images are missing. See {RESULTS_DIR / 'missing_source_images.csv'}")

if REQUIRE_YOLO_LABELS and not resolved_df["yolo_label_exists"].all():
    missing = resolved_df.loc[~resolved_df["yolo_label_exists"], ["split", "image_name", "image_id"]]
    missing.to_csv(RESULTS_DIR / "missing_source_yolo_labels.csv", index=False)
    print(f"Warning: {len(missing)} source YOLO labels missing.")
"""

    # Cell 7: class_names, parsing, and greedy class-balanced sampling with safe display
    cell7_source = """# Read class names from project configs when available; otherwise use standard BDD classes
import yaml
class_names = None
for cfg in [PROJECT_ROOT / "configs" / "dataset.yaml", PROJECT_ROOT / "configs" / "base.yaml"]:
    if cfg.exists():
        try:
            cfg_data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
            names = cfg_data.get("names")
            if isinstance(names, dict):
                class_names = [names[k] for k in sorted(names, key=lambda x: int(x))]
            elif isinstance(names, list):
                class_names = names
            if class_names:
                break
        except Exception:
            pass
if not class_names:
    class_names = ["person", "rider", "car", "truck", "bus", "train", "motorcycle", "bicycle", "traffic light", "traffic sign"]

def parse_yolo_label_counts(label_path):
    \"\"\"Return {class_id: instance_count}; empty labels return {}.\"\"\"
    counts = {}
    if label_path is None or pd.isna(label_path) or not Path(str(label_path)).is_file():
        return counts
    try:
        for line in Path(str(label_path)).read_text(encoding="utf-8").splitlines():
            vals = line.split()
            if not vals:
                continue
            if len(vals) != 5:
                continue
            cls = int(float(vals[0]))
            counts[cls] = counts.get(cls, 0) + 1
    except Exception:
        pass
    return counts

def add_label_count_vectors(df):
    df = df.copy()
    counts_list = []
    for p in df["resolved_label"]:
        counts_list.append(parse_yolo_label_counts(p))
    df["_class_counts"] = counts_list
    return df

def class_balanced_train_sample(df, n, seed=42):
    \"\"\"Unique-image greedy sampler that prioritizes underrepresented object classes.\"\"\"
    if len(df) < n:
        raise ValueError(f"Need {n} train images, but only {len(df)} are available.")
    df = add_label_count_vectors(df).reset_index(drop=True)
    class_ids = sorted({cid for d in df["_class_counts"] for cid in d})
    if not class_ids:
        # Fallback to random sampling if no labels are parsed
        print("Warning: No class IDs found in parsed labels. Using seeded random selection.")
        return df.sample(n=n, random_state=seed).reset_index(drop=True), {}

    # Class instance availability in original train pool
    available = {cid: int(sum(d.get(cid, 0) for d in df["_class_counts"])) for cid in class_ids}
    total_instances = sum(available.values())
    target_per_class = max(1, int(round((total_instances * n / len(df)) / max(len(class_ids), 1))))
    targets = {cid: min(available[cid], target_per_class) for cid in class_ids}

    rng = np.random.default_rng(seed)
    remaining = set(range(len(df)))
    selected_indices = []
    selected_counts = {cid: 0 for cid in class_ids}

    class_order = {cid: rng.permutation([i for i, d in enumerate(df["_class_counts"]) if d.get(cid, 0) > 0]).tolist() for cid in class_ids}
    class_pointer = {cid: 0 for cid in class_ids}
    remaining_images_per_class = {cid: len(class_order[cid]) for cid in class_ids}

    while len(selected_indices) < n:
        deficits = {cid: max(0, targets[cid] - selected_counts[cid]) for cid in class_ids}
        active = [cid for cid in class_ids if deficits[cid] > 0 and remaining_images_per_class[cid] > 0]
        if not active:
            break
        focus = max(active, key=lambda cid: (deficits[cid] / max(targets[cid], 1), 1 / max(available[cid], 1), rng.random()))
        order = class_order[focus]
        while class_pointer[focus] < len(order) and order[class_pointer[focus]] not in remaining:
            class_pointer[focus] += 1
        if class_pointer[focus] >= len(order):
            remaining_images_per_class[focus] = 0
            continue
        chosen_idx = order[class_pointer[focus]]
        class_pointer[focus] += 1
        selected_indices.append(chosen_idx)
        remaining.remove(chosen_idx)
        chosen_counts = df.at[chosen_idx, "_class_counts"]
        for cid, count in chosen_counts.items():
            selected_counts[cid] = selected_counts.get(cid, 0) + count
        for cid in chosen_counts:
            remaining_images_per_class[cid] = max(0, remaining_images_per_class.get(cid, 0) - 1)

    # Fill remaining slots with unique images
    if len(selected_indices) < n:
        need = n - len(selected_indices)
        remaining_indices = list(remaining)
        if len(remaining_indices) < need:
            raise ValueError("Not enough remaining unique images to fill the training split.")
        fill = rng.choice(remaining_indices, size=need, replace=False).tolist()
        selected_indices.extend(fill)

    chosen = df.loc[selected_indices].drop_duplicates(subset=["image_id"]).copy()
    if len(chosen) < n:
        leftovers = df.loc[~df.index.isin(chosen.index)].sample(n=n-len(chosen), random_state=seed)
        chosen = pd.concat([chosen, leftovers], ignore_index=False)
    chosen = chosen.drop(columns=["_class_counts"], errors="ignore").sample(frac=1, random_state=seed).reset_index(drop=True)
    assert len(chosen) == n and chosen["image_id"].is_unique
    return chosen, targets

def stratified_sample_exact(df, n, seed):
    \"\"\"Proportional condition-stratified sample with exact total n, without replacement.\"\"\"
    if len(df) < n:
        raise ValueError(f"Need {n} rows but only {len(df)} available.")
    counts = df["project_condition"].value_counts().sort_index()
    exact = counts / counts.sum() * n
    alloc = np.floor(exact).astype(int)
    alloc = pd.Series({c: min(int(alloc[c]), int(counts[c])) for c in counts.index})
    remainder = n - int(alloc.sum())
    fractions = (exact - np.floor(exact)).sort_values(ascending=False)
    while remainder > 0:
        changed = False
        for c in fractions.index:
            if alloc[c] < counts[c]:
                alloc[c] += 1
                remainder -= 1
                changed = True
                if remainder == 0:
                    break
        if not changed:
            raise ValueError("Could not allocate requested sample across available conditions.")
    pieces = []
    for c, take in alloc.items():
        if take:
            pieces.append(df[df["project_condition"] == c].sample(n=int(take), random_state=seed))
    return pd.concat(pieces).sample(frac=1, random_state=seed).reset_index(drop=True)

selected_parts = []
train_pool = resolved_df[(resolved_df["split"] == "train") & resolved_df["image_exists"]].copy()
if REQUIRE_YOLO_LABELS:
    pool_with_labels = train_pool[train_pool["yolo_label_exists"]].copy()
    if len(pool_with_labels) >= SPLIT_TARGETS["train"]:
        train_pool = pool_with_labels

train_selected, class_targets = class_balanced_train_sample(train_pool, SPLIT_TARGETS["train"], SEED + 1)
train_selected["target_split"] = "train"
selected_parts.append(train_selected)
print(f"train: class-balanced selection {len(train_selected)} from {len(train_pool)} available")
print("Per-class target instance counts:", {class_names[c] if c < len(class_names) else f'class_{c}': int(v) for c, v in class_targets.items()})

for split in ["val", "test"]:
    target = SPLIT_TARGETS[split]
    pool = resolved_df[(resolved_df["split"] == split) & resolved_df["image_exists"]].copy()
    if REQUIRE_YOLO_LABELS:
        pool_with_labels = pool[pool["yolo_label_exists"]].copy()
        if len(pool_with_labels) >= target:
            pool = pool_with_labels
    chosen = stratified_sample_exact(pool, target, SEED + {"val": 2, "test": 3}[split])
    chosen["target_split"] = split
    selected_parts.append(chosen)
    print(f"{split}: condition-stratified selection {len(chosen)} from {len(pool)} available")

selected = pd.concat(selected_parts, ignore_index=True)
assert len(selected) == 10000
assert selected.groupby("target_split").size().to_dict() == SPLIT_TARGETS
assert selected["image_id"].is_unique, "Selected image_id duplicates found."
sets = {s: set(selected.loc[selected.target_split == s, "image_id"]) for s in SPLIT_TARGETS}
assert not (sets["train"] & sets["val"] or sets["train"] & sets["test"] or sets["val"] & sets["test"])
print("Exact 10K sample and split disjointness: PASS")
print("Condition distribution:")
print(pd.crosstab(selected["target_split"], selected["project_condition"]))

# Save selected original metadata and pre-copy object-class balance diagnostics
def instance_counter(df):
    totals = {}
    image_presence = {}
    for label_path in df["resolved_label"]:
        d = parse_yolo_label_counts(label_path)
        for cid, count in d.items():
            totals[cid] = totals.get(cid, 0) + count
            image_presence[cid] = image_presence.get(cid, 0) + 1
    return totals, image_presence

pool_instances, pool_images = instance_counter(train_pool)
selected_train = selected[selected["target_split"] == "train"]
selected_instances, selected_images = instance_counter(selected_train)
class_balance_rows = []
for cid in sorted(set(pool_instances) | set(selected_instances)):
    name = class_names[cid] if cid < len(class_names) else f"class_{cid}"
    class_balance_rows.append({
        "class_id": cid, "class_name": name,
        "train_pool_instances": pool_instances.get(cid, 0),
        "train_pool_images_with_class": pool_images.get(cid, 0),
        "selected_7k_instances": selected_instances.get(cid, 0),
        "selected_7k_images_with_class": selected_images.get(cid, 0),
        "target_instances": class_targets.get(cid, 0),
        "selection_instance_rate": selected_instances.get(cid, 0) / max(pool_instances.get(cid, 0), 1),
    })
class_balance_pre = pd.DataFrame(class_balance_rows)
class_balance_pre.to_csv(RESULTS_DIR / "train_object_class_balance_before_synthetic.csv", index=False)
try:
    display(class_balance_pre)
except Exception:
    print(class_balance_pre)
"""

    # Cell 9: Load accepted CycleGAN fog list and normalize schema
    cell9_source = """synth = pd.read_csv(SYNTH_META)
print("Synthetic metadata rows:", len(synth))

# Filter for accepted quality decisions
if "quality_decision" in synth.columns:
    synth = synth[synth["quality_decision"].astype(str).str.upper().isin(["ACCEPT", "ACCEPTED", "PASS", "TRUE"])].copy()
elif "decision" in synth.columns:
    synth = synth[synth["decision"].astype(str).str.upper().isin(["ACCEPT", "ACCEPTED", "PASS", "TRUE"])].copy()

# Enrich with cyclegan_generated_metadata if available
if GEN_META.exists():
    gen_meta = pd.read_csv(GEN_META)
    synth_key = "file" if "file" in synth.columns else ("generated_image" if "generated_image" in synth.columns else None)
    if synth_key:
        merge_cols = [c for c in gen_meta.columns if c not in synth.columns or c == "generated_image"]
        synth = synth.merge(gen_meta[merge_cols], left_on=synth_key, right_on="generated_image", how="left")

# Normalize column names
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

# Resolve file paths on disk
def resolve_synth_file(row):
    for col in ["generated_path", "path"]:
        if col in row and pd.notna(row[col]):
            p = Path(str(row[col]))
            if p.exists() and p.is_file():
                return str(p)
    fname = str(row.get("generated_image", row.get("file", "")))
    sub = "generated_day_fog" if "dayfog_" in fname else "generated_night_fog"
    cand = PROJECT_ROOT / "datasets" / "cyclegan" / sub / fname
    if cand.exists():
        return str(cand)
    return str(row.get("generated_path", row.get("path", "")))

synth["generated_path_resolved"] = synth.apply(resolve_synth_file, axis=1)
missing_gen = synth[~synth["generated_path_resolved"].map(lambda x: Path(x).is_file())]
if len(missing_gen):
    missing_gen.to_csv(RESULTS_DIR / "missing_accepted_synthetic_fog.csv", index=False)
    raise FileNotFoundError(f"{len(missing_gen)} accepted synthetic images are missing. See diagnostic CSV.")

assert len(synth) > 0, "No accepted synthetic fog rows found."
print("Accepted synthetic fog images to add to TRAIN:", len(synth))
"""

    # Cell 11: Map each synthetic image to its original training source label
    cell11_source = """# Build source lookup from train pool
train_pool = resolved_df[(resolved_df["split"] == "train") & resolved_df["image_exists"]].copy()
source_lookup = {}
for _, r in train_pool.iterrows():
    img = Path(str(r["resolved_image"])) if pd.notna(r.get("resolved_image")) else None
    lab = Path(str(r["resolved_label"])) if pd.notna(r.get("resolved_label")) else None
    keys = {
        img.stem.lower() if img else None,
        Path(str(r["image_name"])).stem.lower(),
        str(r["image_id"]).lower()
    }
    for key in keys:
        if key and key not in source_lookup:
            source_lookup[key] = {
                "image": img,
                "label": lab,
                "image_id": str(r["image_id"]),
                "image_name": str(r["image_name"]),
                "split": "train"
            }

def lookup_synthetic_source(row):
    possible = []
    for col in ["source_id", "source_image", "source_path", "source_filename", "source_name", "image_name"]:
        if col in row and pd.notna(row[col]):
            val = str(row[col])
            possible.extend([Path(val).stem.lower(), val.lower()])
    for col in ["generated_image", "file", "generated_path_resolved"]:
        if col in row and pd.notna(row[col]):
            stem = Path(str(row[col])).stem.lower()
            clean = stem.replace("dayfog_", "").replace("nightfog_", "").replace("rainfog_", "")
            possible.extend([clean, stem])

    for key in possible:
        if key in source_lookup:
            return source_lookup[key]
    return None

synth["source_match"] = synth.apply(lookup_synthetic_source, axis=1)
synth["source_label_path"] = synth["source_match"].map(lambda x: str(x["label"]) if x and x["label"] else None)
synth["source_train_image_id"] = synth["source_match"].map(lambda x: x["image_id"] if x else None)

no_source = synth[synth["source_match"].isna()]
print("Synthetic rows without matched training source:", len(no_source))
assert len(no_source) == 0, f"{len(no_source)} synthetic images could not be matched to training source."

# Check synthetic source identities do not resolve to val/test
selected_by_id = selected.set_index("image_id")["target_split"].to_dict()
val_or_test_leak = [sid for sid in synth["source_train_image_id"] if selected_by_id.get(str(sid)) in ["val", "test"]]
assert len(val_or_test_leak) == 0, f"Synthetic leakage detected: {len(val_or_test_leak)} images from val/test!"

print("Synthetic sources successfully resolved 100% from train pool without leakage.")
"""

    # Cell 13: Build the new dataset with fast link_or_copy
    cell13_source = """if REBUILD_OUTPUT:
    for split in SPLIT_TARGETS:
        for folder in [FINAL_IMG / split, FINAL_LABEL / split]:
            folder.mkdir(parents=True, exist_ok=True)
            for p in folder.iterdir():
                if p.is_file() or p.is_symlink():
                    p.unlink()
    for p in FINAL_META.iterdir():
        if p.is_file():
            p.unlink()

records = []

# Copy 10,000 original images + labels to requested splits
for _, row in selected.iterrows():
    split = str(row["target_split"])
    src_img = Path(str(row["resolved_image"]))
    out_name = f"bdd_{row['image_id']}_{src_img.name}"
    dst_img = FINAL_IMG / split / out_name
    link_or_copy(src_img, dst_img)

    src_lab = Path(str(row["resolved_label"])) if pd.notna(row.get("resolved_label")) else None
    label_name = Path(out_name).stem + ".txt"
    dst_lab = FINAL_LABEL / split / label_name
    if src_lab and src_lab.is_file():
        link_or_copy(src_lab, dst_lab)
    else:
        dst_lab.write_text("", encoding="utf-8")

    records.append({
        "record_type": "original",
        "image_id": str(row["image_id"]),
        "image_name": out_name,
        "split": split,
        "project_condition": row["project_condition"],
        "source_path": str(src_img),
        "final_image_path": str(dst_img),
        "label_name": label_name,
        "synthetic": False,
        "source_id": str(row["image_id"]),
        "source_split": str(row["split"]),
        "source_domain": None,
        "source_image": None,
        "generation_model": None,
        "target_condition": None,
        "quality_decision": "ORIGINAL"
    })

# Add ALL accepted synthetic fog images to TRAIN only, with matched source YOLO labels
synth_records = []
for i, row in synth.reset_index(drop=True).iterrows():
    src_img = Path(str(row["generated_path_resolved"]))
    domain = str(row.get("source_domain", "unknown")).replace(" ", "_")
    source_id = str(row.get("source_train_image_id", f"source_{i}"))
    out_name = f"synthetic_fog_{domain}_{source_id}_{i:05d}{src_img.suffix.lower() if src_img.suffix else '.jpg'}"
    dst_img = FINAL_IMG / "train" / out_name
    dst_label = FINAL_LABEL / "train" / (Path(out_name).stem + ".txt")
    link_or_copy(src_img, dst_img)

    src_label = Path(str(row["source_label_path"])) if pd.notna(row.get("source_label_path")) else None
    if src_label and src_label.is_file():
        link_or_copy(src_label, dst_label)
    else:
        dst_label.write_text("", encoding="utf-8")

    rec = {
        "record_type": "synthetic_fog",
        "image_id": f"synthetic_{domain}_{source_id}_{i:05d}",
        "image_name": out_name,
        "split": "train",
        "project_condition": "Fog",
        "source_path": str(src_img),
        "final_image_path": str(dst_img),
        "label_name": dst_label.name,
        "synthetic": True,
        "source_id": source_id,
        "source_split": "train",
        "source_domain": domain,
        "source_image": str(row.get("source_image", "")),
        "generation_model": str(row.get("generation_model", f"{domain}_to_fog")),
        "target_condition": "Fog",
        "quality_decision": "ACCEPT"
    }
    synth_records.append(rec)
    records.append(rec)

final_meta = pd.DataFrame(records)
meta_csv = FINAL_META / "final_dataset_metadata.csv"
final_meta.to_csv(meta_csv, index=False)

print("Original selected:", int((~final_meta.synthetic).sum()))
print("Accepted synthetic fog added to train:", int(final_meta.synthetic.sum()))
print("Final counts including synthetic:\\n", final_meta.groupby("split").size())
"""

    # Cell 17: Safe display/plot fallback
    cell17_source = """original_counts = pd.crosstab(final_meta.loc[~final_meta.synthetic, "split"], final_meta.loc[~final_meta.synthetic, "project_condition"])
final_counts = pd.crosstab(final_meta["split"], final_meta["project_condition"])
print("Original 10K condition distribution:")
try:
    display(original_counts)
except Exception:
    print(original_counts)

print("Final distribution after adding synthetic fog:")
try:
    display(final_counts)
except Exception:
    print(final_counts)

original_counts.to_csv(RESULTS_DIR / "original_10k_condition_distribution.csv")
final_counts.to_csv(RESULTS_DIR / "final_condition_distribution_with_synthetic.csv")
"""

    nb["cells"][0]["source"] = [l + "\n" for l in cell0_source.strip().splitlines()]
    nb["cells"][1]["source"] = [l + "\n" for l in cell1_source.strip().splitlines()]
    nb["cells"][5]["source"] = [l + "\n" for l in cell5_source.strip().splitlines()]
    nb["cells"][7]["source"] = [l + "\n" for l in cell7_source.strip().splitlines()]
    nb["cells"][9]["source"] = [l + "\n" for l in cell9_source.strip().splitlines()]
    nb["cells"][11]["source"] = [l + "\n" for l in cell11_source.strip().splitlines()]
    nb["cells"][13]["source"] = [l + "\n" for l in cell13_source.strip().splitlines()]
    nb["cells"][17]["source"] = [l + "\n" for l in cell17_source.strip().splitlines()]

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

    print(f"Successfully updated {nb_path}")

if __name__ == "__main__":
    update_notebook()
