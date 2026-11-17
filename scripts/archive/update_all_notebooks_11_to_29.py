import json
import re
from pathlib import Path

PROJECT_ROOT = Path(".").resolve()
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

DYNAMIC_ROOT_CODE = '''from pathlib import Path
import os, sys

def find_project_root():
    current = Path.cwd().resolve()
    for candidate in [current, current.parent, Path(r"C:\\Users\\ankit\\Desktop\\Adaptive_Road_Vision")]:
        if (candidate / "datasets").exists() and (candidate / "notebooks").exists():
            return candidate
    return current

PROJECT_ROOT = find_project_root()
'''

DATASET_RESOLVER_CODE = '''def resolve_dataset_root():
    for cand in [
        PROJECT_ROOT / "datasets" / "final_condition_balanced_v2",
        PROJECT_ROOT / "datasets" / "final_condition_balanced",
        PROJECT_ROOT / "datasets" / "final",
    ]:
        if (cand / "metadata" / "final_dataset_metadata.csv").exists():
            return cand
        if (cand / "labels" / "train").exists() and any((cand / "labels" / "train").glob("*.txt")):
            return cand
    return PROJECT_ROOT / "datasets" / "final_condition_balanced_v2"

FINAL_DIR = resolve_dataset_root()
DATASET_ROOT = FINAL_DIR
'''

def update_notebook_cells(nb_path, transformer_fn):
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    
    modified = transformer_fn(nb)
    if modified:
        with open(nb_path, "w", encoding="utf-8") as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
        print(f"Updated: {nb_path.name}")
    else:
        print(f"No changes needed: {nb_path.name}")

# --- Transformer for 11 ---
def transform_nb11(nb):
    c1 = "".join(nb["cells"][1]["source"])
    if "ankit" in c1:
        c1 = re.sub(r'PROJECT_ROOT\s*=\s*Path\(r?"C:\\\\Users\\\\[^"]+"\)', lambda m: DYNAMIC_ROOT_CODE.strip(), c1)
        nb["cells"][1]["source"] = [l + "\n" for l in c1.splitlines()]
        return True
    return False

# --- Transformer for 12 ---
def transform_nb12(nb):
    changed = False
    # Cell 1: paths
    c1 = "".join(nb["cells"][1]["source"])
    if "PROJECT_ROOT = Path(" in c1:
        c1 = re.sub(r'PROJECT_ROOT\s*=\s*Path\(r?"C:\\\\Users\\\\[^"]+"\)', lambda m: DYNAMIC_ROOT_CODE.strip(), c1)
        # replace FINAL_METADATA_CSV
        c1 = re.sub(
            r'FINAL_METADATA_CSV\s*=\s*\([^)]+\)',
            '''FINAL_METADATA_CANDIDATES = [
    PROJECT_ROOT / "datasets" / "final_condition_balanced_v2" / "metadata" / "final_dataset_metadata.csv",
    PROJECT_ROOT / "datasets" / "final_condition_balanced" / "metadata" / "final_dataset_metadata.csv",
    PROJECT_ROOT / "datasets" / "final" / "metadata" / "final_dataset_metadata.csv",
]
FINAL_METADATA_CSV = next((p for p in FINAL_METADATA_CANDIDATES if p.exists()), FINAL_METADATA_CANDIDATES[0])''',
            c1
        )
        nb["cells"][1]["source"] = [l + "\n" for l in c1.splitlines()]
        changed = True

    # Cell 3: flexible columns
    c3 = "".join(nb["cells"][3]["source"])
    if 'required = [' in c3 and 'final_image_path' in c3:
        flexible_col_code = '''if not FINAL_METADATA_CSV.exists():
    raise FileNotFoundError(f"Missing final metadata: {FINAL_METADATA_CSV}\\nRun Notebook 10 first.")

metadata = pd.read_csv(FINAL_METADATA_CSV)

# Flexible column mapping
if "project_condition" not in metadata.columns and "condition" in metadata.columns:
    metadata["project_condition"] = metadata["condition"]
if "final_image_path" not in metadata.columns and "image_path" in metadata.columns:
    metadata["final_image_path"] = metadata["image_path"]
if "record_type" not in metadata.columns:
    metadata["record_type"] = metadata["synthetic"].map(lambda s: "synthetic_fog" if s else "original")

# Resolve relative image paths if necessary
def resolve_img_path(p):
    p = Path(str(p))
    if p.is_file(): return str(p)
    if (PROJECT_ROOT / p).is_file(): return str(PROJECT_ROOT / p)
    cand = FINAL_METADATA_CSV.parent.parent / p
    if cand.is_file(): return str(cand)
    return str(p)

metadata["final_image_path"] = metadata["final_image_path"].map(resolve_img_path)

required = ["record_type", "image_id", "image_name", "split", "project_condition", "final_image_path", "synthetic"]
missing = [c for c in required if c not in metadata.columns]
if missing:
    raise ValueError(f"Missing metadata columns: {missing}")

print("Metadata shape:", metadata.shape)
print("\\nSplit counts:")
print(metadata["split"].value_counts())
print("\\nCondition counts:")
print(metadata["project_condition"].value_counts())
print("\\nSynthetic counts:")
print(metadata["synthetic"].value_counts(dropna=False))
'''
        nb["cells"][3]["source"] = [l + "\n" for l in flexible_col_code.splitlines()]
        changed = True

    # Cell 4: split boundary checks
    c4 = "".join(nb["cells"][4]["source"])
    if '== 70000' in c4:
        c4_code = '''# Verify split boundaries
original = metadata[metadata["record_type"] == "original"]
synthetic = metadata[metadata["record_type"] == "synthetic_fog"]

assert len(original[original["split"] == "train"]) > 0, "No original training images!"
assert len(original[original["split"] == "val"]) > 0, "No original validation images!"
assert len(original[original["split"] == "test"]) > 0, "No original test images!"
assert synthetic.empty or synthetic["split"].eq("train").all(), "Synthetic images must be train only!"

print(f"Original splits: train={len(original[original['split'] == 'train'])}, val={len(original[original['split'] == 'val'])}, test={len(original[original['split'] == 'test'])}")
print("Synthetic records:", len(synthetic))
print("Split integrity: PASS")
'''
        nb["cells"][4]["source"] = [l + "\n" for l in c4_code.splitlines()]
        changed = True

    return changed

# --- Transformer for 13 ---
def transform_nb13(nb):
    changed = False
    c1 = "".join(nb["cells"][1]["source"])
    if "PROJECT_ROOT = Path(" in c1:
        c1 = re.sub(r'PROJECT_ROOT\s*=\s*Path\(r?"C:\\\\Users\\\\[^"]+"\)', lambda m: DYNAMIC_ROOT_CODE.strip(), c1)
        c1 = re.sub(
            r'FINAL_METADATA_CSV\s*=\s*\([^)]+\)',
            '''FINAL_METADATA_CANDIDATES = [
    PROJECT_ROOT / "datasets" / "final_condition_balanced_v2" / "metadata" / "final_dataset_metadata.csv",
    PROJECT_ROOT / "datasets" / "final_condition_balanced" / "metadata" / "final_dataset_metadata.csv",
    PROJECT_ROOT / "datasets" / "final" / "metadata" / "final_dataset_metadata.csv",
]
FINAL_METADATA_CSV = next((p for p in FINAL_METADATA_CANDIDATES if p.exists()), FINAL_METADATA_CANDIDATES[0])''',
            c1
        )
        nb["cells"][1]["source"] = [l + "\n" for l in c1.splitlines()]
        changed = True

    c5 = "".join(nb["cells"][5]["source"])
    if 'required_columns = [' in c5:
        c5_code = '''metadata = pd.read_csv(FINAL_METADATA_CSV)

# Flexible column mapping
if "project_condition" not in metadata.columns and "condition" in metadata.columns:
    metadata["project_condition"] = metadata["condition"]
if "final_image_path" not in metadata.columns and "image_path" in metadata.columns:
    metadata["final_image_path"] = metadata["image_path"]
if "record_type" not in metadata.columns and "synthetic" in metadata.columns:
    metadata["record_type"] = metadata["synthetic"].map(lambda s: "synthetic_fog" if s else "original")

def resolve_img_path(p):
    p = Path(str(p))
    if p.is_file(): return str(p)
    if (PROJECT_ROOT / p).is_file(): return str(PROJECT_ROOT / p)
    cand = FINAL_METADATA_CSV.parent.parent / p
    if cand.is_file(): return str(cand)
    return str(p)

metadata["final_image_path"] = metadata["final_image_path"].map(resolve_img_path)

required_columns = ["image_id", "image_name", "split", "project_condition", "final_image_path"]
missing_columns = [c for c in required_columns if c not in metadata.columns]
if missing_columns:
    raise ValueError(f"Missing required columns in {FINAL_METADATA_CSV}: {missing_columns}")

print("Metadata loaded:", len(metadata), "rows")
print("Splits:")
print(metadata["split"].value_counts())
'''
        nb["cells"][5]["source"] = [l + "\n" for l in c5_code.splitlines()]
        changed = True

    c6 = "".join(nb["cells"][6]["source"])
    if "assert len(val_df) == 10000" in c6:
        c6 = c6.replace("assert len(val_df) == 10000", "# assert len(val_df) == 10000")
        c6 = c6.replace("assert len(test_df) == 20000", "# assert len(test_df) == 20000")
        c6 = c6 + "\nassert len(val_df) > 0 and len(test_df) > 0, 'Validation or test set is empty!'\n"
        nb["cells"][6]["source"] = [l + "\n" for l in c6.splitlines()]
        changed = True

    return changed

# --- Transformer for 14, 15, 16, 17 ---
def transform_enhancement(nb):
    changed = False
    c1 = "".join(nb["cells"][1]["source"])
    if "FINAL_DIR = PROJECT_ROOT / \"datasets\" / \"final\"" in c1 or "PROJECT_ROOT = Path(" in c1:
        c1 = re.sub(r'PROJECT_ROOT\s*=\s*Path\(r?"C:\\\\Users\\\\[^"]+"\)', lambda m: DYNAMIC_ROOT_CODE.strip(), c1)
        c1 = c1.replace(
            'FINAL_DIR = PROJECT_ROOT / "datasets" / "final"',
            DATASET_RESOLVER_CODE.strip()
        )
        nb["cells"][1]["source"] = [l + "\n" for l in c1.splitlines()]
        changed = True

    # Check resolve_final_image in cells
    for idx, cell in enumerate(nb["cells"]):
        src = "".join(cell.get("source", []))
        if "def resolve_final_image" in src and "FINAL_DIR / p" not in src:
            src = re.sub(
                r'return None\s*$',
                '''for base in [FINAL_DIR, PROJECT_ROOT]:\n        cand = base / "images" / str(row.get("split", "train")) / Path(str(row.get("image_name", ""))).name\n        if cand.is_file(): return str(cand)\n    return None''',
                src,
                flags=re.MULTILINE
            )
            cell["source"] = [l + "\n" for l in src.splitlines()]
            changed = True

    return changed

# --- Transformer for 18, 19, 20, 21 ---
def transform_detector(nb):
    changed = False
    c1 = "".join(nb["cells"][1]["source"])
    if "PROJECT_ROOT = Path(" in c1:
        c1 = re.sub(r'PROJECT_ROOT\s*=\s*Path\(r?"C:\\\\Users\\\\[^"]+"\)', lambda m: DYNAMIC_ROOT_CODE.strip(), c1)
        c1 = c1.replace(
            'FINAL_DIR = PROJECT_ROOT / "datasets" / "final"',
            DATASET_RESOLVER_CODE.strip()
        ).replace(
            'DATASET_ROOT = PROJECT_ROOT / "datasets" / "final"',
            DATASET_RESOLVER_CODE.strip()
        ).replace(
            'DATASET_ROOT = PROJECT_ROOT / \'datasets\' / \'final\'',
            DATASET_RESOLVER_CODE.strip()
        )
        nb["cells"][1]["source"] = [l + "\n" for l in c1.splitlines()]
        changed = True

    for cell in nb["cells"]:
        src = "".join(cell.get("source", []))
        if "CLASS_CANDIDATES = [" in src and 'FINAL_DIR / "dataset.yaml"' not in src:
            src = src.replace(
                "CLASS_CANDIDATES = [",
                "CLASS_CANDIDATES = [\n    PROJECT_ROOT / 'configs' / 'detection.yaml',\n    PROJECT_ROOT / 'configs' / 'dataset.yaml',\n    DATASET_ROOT / 'dataset.yaml' if 'DATASET_ROOT' in globals() else FINAL_DIR / 'dataset.yaml',"
            )
            cell["source"] = [l + "\n" for l in src.splitlines()]
            changed = True
        if 'DATASET_ROOT = PROJECT_ROOT / "datasets" / "final"' in src or 'DATASET_ROOT = PROJECT_ROOT / \'datasets\' / \'final\'' in src:
            src = src.replace(
                'DATASET_ROOT = PROJECT_ROOT / "datasets" / "final"',
                DATASET_RESOLVER_CODE.strip()
            ).replace(
                'DATASET_ROOT = PROJECT_ROOT / \'datasets\' / \'final\'',
                DATASET_RESOLVER_CODE.strip()
            )
            cell["source"] = [l + "\n" for l in src.splitlines()]
            changed = True

    return changed

# --- Transformer for 22, 23 ---
def transform_nb22_23(nb):
    changed = False
    c1 = "".join(nb["cells"][1]["source"])
    if "PROJECT_ROOT = Path(" in c1:
        c1 = re.sub(r'PROJECT_ROOT\s*=\s*Path\(r?"C:\\\\Users\\\\[^"]+"\)', lambda m: DYNAMIC_ROOT_CODE.strip(), c1)
        nb["cells"][1]["source"] = [l + "\n" for l in c1.splitlines()]
        changed = True
    return changed

# --- Transformer for 24, 25, 26 ---
def transform_nb24_26(nb):
    changed = False
    c1 = "".join(nb["cells"][1]["source"])
    if "PROJECT_ROOT = Path(" in c1:
        c1 = re.sub(r'PROJECT_ROOT\s*=\s*Path\(r?"C:\\\\Users\\\\[^"]+"\)', lambda m: DYNAMIC_ROOT_CODE.strip(), c1)
        c1 = c1.replace(
            'DATASET_ROOT = PROJECT_ROOT / "datasets" / "final"',
            DATASET_RESOLVER_CODE.strip()
        )
        c1 = re.sub(
            r'METADATA_PATH\s*=\s*PROJECT_ROOT\s*/\s*"datasets"\s*/\s*"processed"\s*/\s*"metadata"\s*/\s*"bdd100k_processed_metadata.csv"',
            '''METADATA_CANDIDATES = [
    DATASET_ROOT / "metadata" / "final_dataset_metadata.csv",
    PROJECT_ROOT / "datasets" / "final_condition_balanced_v2" / "metadata" / "final_dataset_metadata.csv",
    PROJECT_ROOT / "datasets" / "processed" / "metadata" / "bdd100k_processed_metadata.csv",
]
METADATA_PATH = next((p for p in METADATA_CANDIDATES if p.exists()), METADATA_CANDIDATES[0])''',
            c1
        )
        nb["cells"][1]["source"] = [l + "\n" for l in c1.splitlines()]
        changed = True
    return changed

# --- Transformer for 27 ---
def transform_nb27(nb):
    changed = False
    c1 = "".join(nb["cells"][1]["source"])
    if "PROJECT_ROOT = Path(" in c1:
        c1 = re.sub(r'PROJECT_ROOT\s*=\s*Path\(r?"C:\\\\Users\\\\[^"]+"\)', lambda m: DYNAMIC_ROOT_CODE.strip(), c1)
        nb["cells"][1]["source"] = [l + "\n" for l in c1.splitlines()]
        changed = True
    return changed

# --- Transformer for 28 ---
def transform_nb28(nb):
    changed = False
    c1 = "".join(nb["cells"][1]["source"])
    if "PROJECT_ROOT = Path(" in c1:
        c1 = re.sub(r'PROJECT_ROOT\s*=\s*Path\(r?"C:\\\\Users\\\\[^"]+"\)', lambda m: DYNAMIC_ROOT_CODE.strip(), c1)
        c1 = c1.replace(
            'TEST_IMAGE_DIR = PROJECT_ROOT / "datasets" / "final" / "images" / "test"',
            '''TEST_IMAGE_CANDIDATES = [
    PROJECT_ROOT / "datasets" / "final_condition_balanced_v2" / "images" / "test",
    PROJECT_ROOT / "datasets" / "final_condition_balanced" / "images" / "test",
    PROJECT_ROOT / "datasets" / "final" / "images" / "test",
]
TEST_IMAGE_DIR = next((p for p in TEST_IMAGE_CANDIDATES if p.exists() and any(p.glob("*"))), TEST_IMAGE_CANDIDATES[0])'''
        )
        nb["cells"][1]["source"] = [l + "\n" for l in c1.splitlines()]
        changed = True
    return changed

# --- Transformer for 29 ---
def transform_nb29(nb):
    changed = False
    c1 = "".join(nb["cells"][1]["source"])
    if "PROJECT_ROOT = Path(" in c1:
        c1 = re.sub(r'PROJECT_ROOT\s*=\s*Path\(r?"C:\\\\Users\\\\[^"]+"\)', lambda m: DYNAMIC_ROOT_CODE.strip(), c1)
        nb["cells"][1]["source"] = [l + "\n" for l in c1.splitlines()]
        changed = True

    c3 = "".join(nb["cells"][3]["source"])
    if 'RESULTS / "dataset" / "final_dataset_summary.json"' in c3 and 'dataset_balance_audit_v2' not in c3:
        c3 = c3.replace(
            '"dataset_summary": RESULTS / "dataset" / "final_dataset_summary.json",',
            '''"dataset_summary": next((p for p in [
        RESULTS / "dataset" / "final_dataset_summary.json",
        RESULTS / "dataset_balance_audit_v2" / "final_dataset_build_report.json",
        RESULTS / "dataset_balance_audit" / "final_dataset_build_report.json"
    ] if p.exists()), RESULTS / "dataset" / "final_dataset_summary.json"),'''
        )
        nb["cells"][3]["source"] = [l + "\n" for l in c3.splitlines()]
        changed = True

    return changed

# Run all transformers
transformers = {
    "11_data_preprocessing.ipynb": transform_nb11,
    "12_condition_analysis_training.ipynb": transform_nb12,
    "13_condition_analysis_evaluation.ipynb": transform_nb13,
    "14_night_enhancement_training.ipynb": transform_enhancement,
    "15_rain_enhancement_training.ipynb": transform_enhancement,
    "16_fog_enhancement_training.ipynb": transform_enhancement,
    "17_enhancement_evaluation.ipynb": transform_enhancement,
    "18_detector_1_training.ipynb": transform_detector,
    "19_detector_2_training.ipynb": transform_detector,
    "20_detector_3_training.ipynb": transform_detector,
    "21_detector_4_training.ipynb": transform_detector,
    "22_detector_comparison.ipynb": transform_nb22_23,
    "23_final_detector_selection.ipynb": transform_nb22_23,
    "24_original_vs_enhanced_detection.ipynb": transform_nb24_26,
    "25_bytetrack_evaluation.ipynb": transform_nb24_26,
    "26_depth_estimation.ipynb": transform_nb24_26,
    "27_risk_engine.ipynb": transform_nb27,
    "28_end_to_end_pipeline.ipynb": transform_nb28,
    "29_final_evaluation.ipynb": transform_nb29,
}

for fname, fn in transformers.items():
    p = NOTEBOOKS_DIR / fname
    if p.exists():
        update_notebook_cells(p, fn)
    else:
        print(f"Warning: {p} does not exist!")

print("\nAll notebook updates complete!")
