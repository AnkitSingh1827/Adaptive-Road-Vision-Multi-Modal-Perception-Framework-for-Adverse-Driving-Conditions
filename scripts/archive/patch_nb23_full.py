import json
from pathlib import Path

nb_path = Path("notebooks/23_bytetrack_evaluation_CORRECTED.ipynb")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

def to_source(code_str):
    lines = code_str.strip().split("\n")
    return [l + "\n" for l in lines[:-1]] + ([lines[-1]] if lines else [])

# Cell 1: Environment & Paths
nb["cells"][1]["source"] = to_source('''from pathlib import Path
import os
import json
import re
import math
import numpy as np
import pandas as pd
from PIL import Image
import torch
import matplotlib.pyplot as plt

def find_project_root():
    current = Path.cwd().resolve()
    for candidate in [current, current.parent, current.parent.parent]:
        if (candidate / "datasets").exists() and (candidate / "models").exists():
            return candidate
    return Path(r"C:\\Users\\ankit\\Desktop\\Adaptive_Road_Vision")

PROJECT_ROOT = find_project_root()
if not PROJECT_ROOT.exists():
    raise FileNotFoundError(
        f"Project root not found: {PROJECT_ROOT}. Update PROJECT_ROOT to your actual project folder."
    )
os.chdir(PROJECT_ROOT)

def resolve_dataset_root():
    candidates = [
        PROJECT_ROOT / "datasets" / "final_condition_balanced_v2",
        PROJECT_ROOT / "datasets" / "final_condition_balanced",
        PROJECT_ROOT / "datasets" / "final",
    ]
    for cand in candidates:
        if (cand / "metadata" / "final_dataset_metadata.csv").exists():
            return cand
    return candidates[0]

FINAL_DIR = resolve_dataset_root()
DATASET_ROOT = FINAL_DIR
METADATA_CANDIDATES = [
    DATASET_ROOT / "metadata" / "final_dataset_metadata.csv",
    PROJECT_ROOT / "datasets" / "final_condition_balanced_v2" / "metadata" / "final_dataset_metadata.csv",
    PROJECT_ROOT / "datasets" / "processed" / "metadata" / "bdd100k_processed_metadata.csv",
]
METADATA_PATH = next((p for p in METADATA_CANDIDATES if p.exists()), None)
SELECTION_PATH = PROJECT_ROOT / "results" / "detection" / "final_detector_selection.json"
RESULT_ROOT = PROJECT_ROOT / "results" / "tracking"
MODEL_ROOT = PROJECT_ROOT / "models"
RESULT_ROOT.mkdir(parents=True, exist_ok=True)

DEVICE = 0 if torch.cuda.is_available() else "cpu"
TORCH_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Project root:", PROJECT_ROOT)
print("Dataset root:", DATASET_ROOT)
print("Metadata:", METADATA_PATH)
print("Ultralytics Device:", DEVICE)
print("PyTorch Device:", TORCH_DEVICE)''')

# Cell 3: Detector Selection & Metadata
nb["cells"][3]["source"] = to_source('''from ultralytics import YOLO

if METADATA_PATH is None:
    raise FileNotFoundError(
        "Could not find final dataset metadata. Expected metadata/final_dataset_metadata.csv "
        "under one of the configured dataset folders."
    )

if not SELECTION_PATH.exists():
    fallback = MODEL_ROOT / "detection" / "final_selected_detector.pt"
    if not fallback.exists():
        raise FileNotFoundError(
            f"Final detector selection report is missing ({SELECTION_PATH}) and fallback checkpoint "
            f"does not exist ({fallback}). Run Notebook 21 and Notebook 20 first."
        )
    selected_detector = "Final selected detector (fallback path)"
    selected_model = "selected detector"
    selected_checkpoint = fallback
else:
    selection = json.loads(SELECTION_PATH.read_text(encoding="utf-8"))
    selected_detector = selection.get("selected_detector", "Selected detector")
    selected_model = selection.get("selected_model", "Unknown")
    checkpoint_value = selection.get("stable_downstream_checkpoint") or selection.get("selected_checkpoint")
    if not checkpoint_value:
        raise KeyError(
            "Selection JSON has no stable_downstream_checkpoint or selected_checkpoint. "
            "Re-run Notebook 21 to generate a valid selection report."
        )
    selected_checkpoint = Path(checkpoint_value)
    if not selected_checkpoint.is_absolute():
        selected_checkpoint = (PROJECT_ROOT / selected_checkpoint).resolve()

if not selected_checkpoint.exists():
    raise FileNotFoundError(
        f"Selected detector checkpoint not found: {selected_checkpoint}. "
        "Do not substitute a different model silently; rerun Notebook 21 or correct its report."
    )

print("Selected detector:", selected_detector)
print("Selected model:", selected_model)
print("Checkpoint:", selected_checkpoint)

metadata = pd.read_csv(METADATA_PATH)
if "split" not in metadata.columns:
    raise KeyError(f"Metadata file has no 'split' column: {METADATA_PATH}")
if "project_condition" not in metadata.columns:
    if "condition" in metadata.columns:
        metadata["project_condition"] = metadata["condition"]
    elif "weather" in metadata.columns:
        metadata["project_condition"] = metadata["weather"]
    else:
        metadata["project_condition"] = "Unknown"
if "image_name" not in metadata.columns and "image_path" not in metadata.columns:
    raise KeyError("Metadata must contain image_name or image_path.")

test_meta = metadata[metadata["split"].astype(str).str.strip().str.lower().isin(["test", "testing"])].copy()
if test_meta.empty:
    raise ValueError("No test rows found in metadata. Check split names and dataset preparation.")
print("Test rows in metadata:", len(test_meta))''')

# Cell 4: Initialize detector
nb["cells"][4]["source"] = to_source('''from ultralytics import YOLO

try:
    import ultralytics
    print("Ultralytics version:", ultralytics.__version__)
except Exception:
    pass

detector = YOLO(str(selected_checkpoint))
print("Loaded detector:", selected_checkpoint)''')

# Cell 8: ByteTrack configuration
nb["cells"][8]["source"] = to_source('''TRACKER_CONFIG = "bytetrack.yaml"
IMAGE_SIZE = 640
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.50

# Set this to an integer for a quick smoke test (e.g., 50 or 100).
# Set to None to evaluate the full available test set.
MAX_FRAMES = None

print("Tracker:", TRACKER_CONFIG)
print("Image size:", IMAGE_SIZE)
print("Confidence threshold:", CONF_THRESHOLD)
print("IoU threshold:", IOU_THRESHOLD)
print("Max frames:", MAX_FRAMES if MAX_FRAMES is not None else "ALL")''')

# Cell 10: Enhancement models
nb["cells"][10]["source"] = to_source('''import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms

class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(channels, channels, 3, padding=1),
            nn.InstanceNorm2d(channels, affine=True),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, channels, 3, padding=1),
            nn.InstanceNorm2d(channels, affine=True),
        )

    def forward(self, x):
        return x + self.block(x)


class ConditionEnhancer(nn.Module):
    """
    Compact residual encoder-decoder matching the architecture
    trained in Notebooks 14 (Night), 15 (Rain), and 16 (Fog).
    """
    def __init__(self, base_channels=32, num_res_blocks=4):
        super().__init__()
        self.enc1 = nn.Sequential(
            nn.Conv2d(3, base_channels, 3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.enc2 = nn.Sequential(
            nn.Conv2d(base_channels, base_channels * 2, 3, stride=2, padding=1),
            nn.ReLU(inplace=True),
        )
        self.enc3 = nn.Sequential(
            nn.Conv2d(base_channels * 2, base_channels * 4, 3, stride=2, padding=1),
            nn.ReLU(inplace=True),
        )
        self.res = nn.Sequential(*[ResidualBlock(base_channels * 4) for _ in range(num_res_blocks)])
        self.dec2 = nn.Sequential(
            nn.Conv2d(base_channels * 4, base_channels * 2, 3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.dec1 = nn.Sequential(
            nn.Conv2d(base_channels * 2, base_channels, 3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.out = nn.Conv2d(base_channels, 3, 3, padding=1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)

        z = self.res(e3)

        z = F.interpolate(z, size=e2.shape[-2:], mode="bilinear", align_corners=False)
        z = self.dec2(z) + e2

        z = F.interpolate(z, size=e1.shape[-2:], mode="bilinear", align_corners=False)
        z = self.dec1(z) + e1

        residual = torch.tanh(self.out(z)) * 0.5
        return torch.clamp(x + residual, 0.0, 1.0)


# Backward compatibility alias
EnhancementNet = ConditionEnhancer


def load_enhancer(path):
    checkpoint = torch.load(path, map_location=TORCH_DEVICE)

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        state = checkpoint["model_state_dict"]
    elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        state = checkpoint["state_dict"]
    elif isinstance(checkpoint, dict):
        state = checkpoint
    else:
        state = checkpoint.state_dict()

    cleaned = {k.replace("module.", ""): v for k, v in state.items()}
    model = ConditionEnhancer().to(TORCH_DEVICE)
    try:
        model.load_state_dict(cleaned, strict=True)
    except RuntimeError as exc:
        raise RuntimeError(
            f"Checkpoint architecture does not match ConditionEnhancer: {path}."
        ) from exc
    model.eval()
    return model


enhancer_paths = {
    "Night": MODEL_ROOT / "enhancement" / "night" / "night_enhancer_best.pth",
    "Rain": MODEL_ROOT / "enhancement" / "rain" / "rain_enhancer_best.pth",
    "Fog": MODEL_ROOT / "enhancement" / "fog" / "fog_enhancer_best.pth",
}

enhancers = {}

for condition, path in enhancer_paths.items():
    if path.exists():
        try:
            enhancers[condition] = load_enhancer(path)
            print("Loaded:", condition, path)
        except Exception as e:
            print("Could not load", condition, ":", e)
    else:
        print("Missing:", path)

print("Active enhancement models loaded:", list(enhancers.keys()))

enhance_transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
])


def enhance_image(image, condition):
    if condition not in enhancers:
        return image.copy()

    tensor = enhance_transform(image).unsqueeze(0).to(TORCH_DEVICE)

    with torch.inference_mode():
        output = enhancers[condition](tensor)[0].cpu()

    enhanced = transforms.ToPILImage()(output)
    return enhanced.resize(image.size, Image.Resampling.BILINEAR)''')

# Cell 12: Tracking helper with reset_tracker
nb["cells"][12]["source"] = to_source('''def reset_tracker(model):
    """Safely reset ByteTrack state between video sequences without reloading weights from disk."""
    if hasattr(model, "predictor") and model.predictor is not None:
        if hasattr(model.predictor, "trackers"):
            for t in model.predictor.trackers:
                t.reset()
                if hasattr(t, "reset_id"):
                    t.reset_id()


def make_tracker():
    return detector


def run_sequence(sequence_df, mode="original", tracker=None):
    if tracker is None:
        tracker = detector
    reset_tracker(tracker)
    rows = []

    for i, row in enumerate(sequence_df.itertuples(index=False)):
        image_path = Path(row.resolved_image_path)
        condition = str(row.project_condition)

        image = Image.open(image_path).convert("RGB")

        if mode == "enhanced":
            input_image = enhance_image(image, condition)
        else:
            input_image = image

        results = tracker.track(
            source=np.asarray(input_image),
            persist=True,
            tracker=TRACKER_CONFIG,
            imgsz=IMAGE_SIZE,
            conf=CONF_THRESHOLD,
            iou=IOU_THRESHOLD,
            device=DEVICE,
            verbose=False,
        )

        result = results[0]

        if result.boxes is None or len(result.boxes) == 0:
            detection_count = 0
            track_ids = np.array([], dtype=np.int64)
            confs = np.array([], dtype=np.float32)
            classes = np.array([], dtype=np.int64)
            untracked_detections = 0
        else:
            detection_count = int(len(result.boxes))
            ids = result.boxes.id
            if ids is None:
                track_ids = np.array([], dtype=np.int64)
                untracked_detections = detection_count
            else:
                track_ids = ids.cpu().numpy().astype(np.int64)
                untracked_detections = max(0, detection_count - len(track_ids))
            confs = result.boxes.conf.cpu().numpy().astype(np.float32)
            classes = result.boxes.cls.cpu().numpy().astype(np.int64)

        unique_ids = set(track_ids.tolist())

        rows.append({
            "sequence_id": str(row.sequence_id),
            "image_name": str(getattr(row, "image_name", Path(row.resolved_image_path).name)),
            "frame_number": int(row.frame_number),
            "condition": condition,
            "mode": mode,
            "detections": detection_count,
            "tracked_detections": int(len(track_ids)),
            "untracked_detections": int(untracked_detections),
            "active_tracks": int(len(unique_ids)),
            "mean_confidence": float(confs.mean()) if len(confs) else 0.0,
            "track_ids": ",".join(map(str, sorted(unique_ids))),
            "class_ids": ",".join(map(str, classes.tolist())),
        })

    return rows''')

# Cell 14: Loop over sequences
nb["cells"][14]["source"] = to_source('''eval_meta = test_meta.copy()

if MAX_FRAMES is not None:
    eval_meta = eval_meta.head(MAX_FRAMES).copy()

all_rows = []

for mode in ["original", "enhanced"]:
    print(f"Running ByteTrack mode: {mode}")

    for sequence_id, seq_df in eval_meta.groupby("sequence_id", sort=False):
        # Require chronological order inside each sequence.
        seq_df = seq_df.sort_values(
            ["frame_number", "image_name"]
        )

        try:
            rows = run_sequence(seq_df, mode=mode, tracker=detector)
            all_rows.extend(rows)
        except Exception as e:
            print(f"Sequence failed: {sequence_id} | {e}")

    print("Completed:", mode)

tracking_df = pd.DataFrame(all_rows)

if tracking_df.empty:
    raise RuntimeError("No tracking results were produced.")

print("Tracking rows:", len(tracking_df))
display(tracking_df.head())''')

# Cell 16: Sequence metrics
nb["cells"][16]["source"] = to_source('''def sequence_metrics(df):
    rows = []

    for (mode, sequence_id), g in df.groupby(
        ["mode", "sequence_id"], sort=False
    ):
        active_counts = g["active_tracks"].to_numpy()
        detection_counts = g["detections"].to_numpy()

        # Number of track IDs observed over the sequence.
        all_ids = set()
        for text in g["track_ids"].fillna(""):
            if text:
                all_ids.update(
                    int(x) for x in str(text).split(",") if x.strip()
                )

        # Track appearances per frame.
        appearance_counts = {}
        for text in g["track_ids"].fillna(""):
            if text:
                for x in str(text).split(","):
                    if x.strip():
                        tid = int(x)
                        appearance_counts[tid] = appearance_counts.get(tid, 0) + 1

        lifespans = list(appearance_counts.values())

        rows.append({
            "mode": mode,
            "sequence_id": sequence_id,
            "frames": len(g),
            "mean_detections_per_frame": float(detection_counts.mean()) if len(detection_counts) else 0.0,
            "mean_active_tracks": float(active_counts.mean()) if len(active_counts) else 0.0,
            "max_active_tracks": int(active_counts.max()) if len(active_counts) else 0,
            "unique_track_ids": len(all_ids),
            "mean_track_lifespan_frames": (
                float(np.mean(lifespans)) if lifespans else 0.0
            ),
            "max_track_lifespan_frames": (
                int(max(lifespans)) if lifespans else 0
            ),
        })

    return pd.DataFrame(rows)


sequence_df = sequence_metrics(tracking_df)
display(sequence_df.head(20))''')

# Cell 19: Continuity metrics
nb["cells"][19]["source"] = to_source('''def continuity_metrics(df):
    rows = []

    for (mode, sequence_id), g in df.groupby(
        ["mode", "sequence_id"], sort=False
    ):
        g = g.sort_values(["frame_number", "image_name"])

        previous_ids = None
        continued = 0
        transitions = 0

        for text in g["track_ids"].fillna(""):
            current_ids = set(
                int(x) for x in str(text).split(",") if x.strip()
            ) if text else set()

            if previous_ids is not None:
                transitions += 1
                continued += len(previous_ids.intersection(current_ids))

            previous_ids = current_ids

        total_obs = sum(
            len(set(
                int(x) for x in str(text).split(",") if x.strip()
            )) if text else 0
            for text in g["track_ids"].fillna("")
        )
        continuity = (continued / total_obs) if total_obs > 0 else 0.0

        rows.append({
            "mode": mode,
            "sequence_id": sequence_id,
            "consecutive_frame_transitions": transitions,
            "continued_track_observations": continued,
            "continuity_ratio": float(continuity),
        })

    return pd.DataFrame(rows)


continuity_df = continuity_metrics(tracking_df)
display(continuity_df.head(20))

continuity_summary = (
    continuity_df.groupby("mode")
    .agg(
        sequences=("sequence_id", "nunique"),
        mean_continuity_ratio=("continuity_ratio", "mean"),
        median_continuity_ratio=("continuity_ratio", "median"),
    )
    .reset_index()
)

display(continuity_summary)''')

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("SUCCESS: notebooks/23_bytetrack_evaluation_CORRECTED.ipynb has been updated with all verified code!")
