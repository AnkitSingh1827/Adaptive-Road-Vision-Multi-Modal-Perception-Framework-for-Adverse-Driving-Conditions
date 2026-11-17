import json
from pathlib import Path

nb_path = Path("notebooks/17_enhancement_evaluation_CORRECTED_15K.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

new_cell_1_code = """from pathlib import Path
import json
import math
import random

import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter
import matplotlib.pyplot as plt

def find_project_root():
    current = Path.cwd().resolve()
    candidates = [current, *list(current.parents)]
    for candidate in candidates:
        if (candidate / "datasets").exists() and (candidate / "notebooks").exists():
            return candidate
    fallback = Path(r"C:\\Users\\ankit\\Desktop\\Adaptive_Road_Vision")
    if fallback.exists():
        return fallback
    return current

PROJECT_ROOT = find_project_root()

if not PROJECT_ROOT.exists():
    raise FileNotFoundError(
        f"Project root not found: {PROJECT_ROOT}. "
        "Edit PROJECT_ROOT to your Adaptive_Road_Vision folder."
    )

def resolve_dataset_root():
    candidates = [
        PROJECT_ROOT / "datasets" / "final_condition_balanced_v2",
        PROJECT_ROOT / "datasets" / "final_condition_balanced",
        PROJECT_ROOT / "datasets" / "final",
    ]
    for candidate in candidates:
        if (candidate / "metadata" / "final_dataset_metadata.csv").exists():
            return candidate
        if (candidate / "final_dataset_metadata.csv").exists():
            return candidate
    return candidates[0]

FINAL_DIR = resolve_dataset_root()
DATASET_ROOT = FINAL_DIR
MODEL_DIR = PROJECT_ROOT / "models" / "enhancement"
RESULTS_DIR = PROJECT_ROOT / "results" / "enhancement"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
IMAGE_SIZE = 256
BATCH_SIZE = 8
NUM_WORKERS = 0
MAX_VISUALS_PER_CONDITION = 4

random.seed(SEED)
np.random.seed(SEED)

print("Project root:", PROJECT_ROOT)
print("Dataset root:", FINAL_DIR)
print("Checkpoint root:", MODEL_DIR)
print("Output directory:", RESULTS_DIR)
"""

nb["cells"][1]["source"] = [line + "\n" for line in new_cell_1_code.splitlines()]

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Updated 17_enhancement_evaluation_CORRECTED_15K.ipynb successfully.")
