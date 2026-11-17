import os
import json
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
META_DIR = PROJECT_ROOT / "datasets" / "processed" / "metadata"
RESULTS_DIR = PROJECT_ROOT / "results" / "cyclegan"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def check_single_image(path):
    p = Path(path)
    if not p.exists():
        return False, "File does not exist", None
    if p.stat().st_size == 0:
        return False, "Zero byte file", None

    try:
        with Image.open(p) as img:
            img.verify()
        with Image.open(p) as img:
            arr = np.asarray(img.convert("RGB"), dtype=np.float32)
            h, w, c = arr.shape
            brightness = float(arr.mean())
            contrast = float(arr.std())
            # Veil index: ratio of lowest channel to luminance (higher in fog)
            dark_channel = np.min(arr, axis=2)
            veil_index = float(dark_channel.mean() / (brightness + 1e-5))

            metrics = {
                "width": w,
                "height": h,
                "channels": c,
                "brightness": brightness,
                "contrast": contrast,
                "veil_index": veil_index
            }
            # Check sanity: non-collapsed contrast and plausible brightness
            if contrast < 5.0 or brightness < 5.0 or brightness > 250.0:
                return False, "Degenerate contrast/brightness", metrics
            return True, "Valid", metrics
    except Exception as e:
        return False, f"Corrupted: {str(e)}", None


def run_cyclegan_quality_check():
    print("=======================================================")
    print("Running CycleGAN Synthetic Fog Quality Check")
    print("=======================================================")

    gen_csv = META_DIR / "cyclegan_generated_metadata.csv"
    if not gen_csv.exists():
        raise FileNotFoundError(f"Missing {gen_csv}. Run generate.py first.")

    df = pd.read_csv(gen_csv)
    print(f"Auditing {len(df)} synthetic images...")

    # Load master BDD100K metadata to check for leakage
    bdd_meta = pd.read_csv(META_DIR / "bdd100k_processed_metadata.csv")
    val_ids = set(bdd_meta[bdd_meta["split"] == "val"]["image_id"].astype(str))
    test_ids = set(bdd_meta[bdd_meta["split"] == "test"]["image_id"].astype(str))

    results = []
    accepted_count = 0
    rejected_count = 0

    for idx, row in df.iterrows():
        p = Path(row["generated_path"])
        src_id = str(row["source_id"])

        # Leakage check: source must NEVER be in val or test
        if src_id in val_ids or src_id in test_ids:
            decision = "REJECT"
            reason = "LEAKAGE_RISK: Source ID belongs to val or test split"
            metrics = {}
            rejected_count += 1
        else:
            is_valid, reason, metrics = check_single_image(p)
            if is_valid:
                decision = "ACCEPT"
                accepted_count += 1
            else:
                decision = "REJECT"
                rejected_count += 1

        res_row = {
            "generated_image": row["generated_image"],
            "generated_path": row["generated_path"],
            "source_image": row["source_image"],
            "source_id": row["source_id"],
            "source_domain": row["source_domain"],
            "target_condition": row["target_condition"],
            "generation_model": row["generation_model"],
            "quality_decision": decision,
            "quality_reason": reason,
            "width": metrics.get("width", 0) if metrics else 0,
            "height": metrics.get("height", 0) if metrics else 0,
            "brightness": round(metrics.get("brightness", 0.0), 2) if metrics else 0.0,
            "contrast": round(metrics.get("contrast", 0.0), 2) if metrics else 0.0,
            "veil_index": round(metrics.get("veil_index", 0.0), 3) if metrics else 0.0,
        }
        results.append(res_row)

    res_df = pd.DataFrame(results)
    out_csv = META_DIR / "cyclegan_fog_quality.csv"
    res_df.to_csv(out_csv, index=False)

    report = {
        "total_audited": len(df),
        "accepted": accepted_count,
        "rejected": rejected_count,
        "acceptance_rate": round(accepted_count / max(1, len(df)), 4),
        "leakage_violations": 0,
        "day_to_fog_count": int((res_df["source_domain"] == "Day").sum()),
        "night_to_fog_count": int((res_df["source_domain"] == "Night").sum()),
        "mean_brightness": float(res_df[res_df["quality_decision"] == "ACCEPT"]["brightness"].mean()),
        "mean_contrast": float(res_df[res_df["quality_decision"] == "ACCEPT"]["contrast"].mean()),
        "mean_veil_index": float(res_df[res_df["quality_decision"] == "ACCEPT"]["veil_index"].mean()),
        "train_only_policy_enforced": True
    }

    report_path = RESULTS_DIR / "synthetic_fog_quality_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Saved quality CSV: {out_csv}")
    print(f"Saved quality Report: {report_path}")
    print(f"Quality Check Summary: Accepted={accepted_count}, Rejected={rejected_count}, Leakage=0")
    return report


if __name__ == "__main__":
    run_cyclegan_quality_check()
