import json
from pathlib import Path

nb_path = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision\notebooks\27_final_evaluation_CORRECTED.ipynb")

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Ensure Cell 1 imports display properly
c1_src = "".join(nb["cells"][1]["source"])
if "from IPython.display import display" not in c1_src:
    c1_lines = ["from IPython.display import display\n"] + nb["cells"][1]["source"]
    nb["cells"][1]["source"] = c1_lines

new_cell9_code = """try:
    from IPython.display import display
except ImportError:
    pass

def show(obj):
    try:
        from IPython.display import display as _disp
        _disp(obj)
    except Exception:
        if callable(globals().get("display")):
            display(obj)
        elif hasattr(globals().get("display"), "display") and callable(globals().get("display").display):
            globals().get("display").display(obj)
        else:
            print(obj)

condition_report = load_json(ARTIFACTS["condition_report"])
condition_predictions = load_csv(ARTIFACTS["condition_predictions"])

condition_metrics = []

# 1. Search condition report: check nested 'test', 'test_metrics', 'metrics', or top-level keys
if isinstance(condition_report, dict):
    test_dict = None
    for subkey in ["test", "test_metrics", "metrics"]:
        if isinstance(condition_report.get(subkey), dict):
            test_dict = condition_report[subkey]
            break
    if test_dict is None:
        test_dict = condition_report

    metric_keys = [
        "samples", "test_samples",
        "accuracy", "test_accuracy",
        "balanced_accuracy", "test_balanced_accuracy",
        "macro_precision", "test_macro_precision",
        "macro_recall", "test_macro_recall",
        "macro_f1", "test_macro_f1",
    ]
    for k in metric_keys:
        if k in test_dict:
            condition_metrics.append({"metric": k, "value": test_dict[k]})
        elif k in condition_report:
            condition_metrics.append({"metric": k, "value": condition_report[k]})

# 2. Fallback to condition_metrics_summary.csv if available
cond_summary_path = RESULTS / "condition" / "condition_metrics_summary.csv"
if not condition_metrics and cond_summary_path.exists():
    summary_df = load_csv(cond_summary_path)
    if summary_df is not None and not summary_df.empty:
        test_row = summary_df[summary_df["split"].astype(str).str.lower() == "test"]
        if test_row.empty:
            test_row = summary_df.iloc[[-1]]
        for col in ["samples", "accuracy", "balanced_accuracy", "macro_precision", "macro_recall", "macro_f1"]:
            if col in test_row.columns:
                condition_metrics.append({"metric": col, "value": float(test_row.iloc[0][col])})

# 3. Fallback to computing directly from condition_predictions DataFrame
if not condition_metrics and condition_predictions is not None and not condition_predictions.empty:
    if "correct" in condition_predictions.columns:
        acc = float(condition_predictions["correct"].mean())
    elif "true_condition" in condition_predictions.columns and "predicted_condition" in condition_predictions.columns:
        acc = float((condition_predictions["true_condition"] == condition_predictions["predicted_condition"]).mean())
    else:
        acc = None

    if acc is not None:
        condition_metrics.append({"metric": "accuracy", "value": acc})
        condition_metrics.append({"metric": "samples", "value": len(condition_predictions)})

    if "true_condition" in condition_predictions.columns and "predicted_condition" in condition_predictions.columns:
        classes = sorted(condition_predictions["true_condition"].dropna().unique())
        recalls, precisions, f1s = [], [], []
        for c in classes:
            tp = int(((condition_predictions["true_condition"] == c) & (condition_predictions["predicted_condition"] == c)).sum())
            fn = int(((condition_predictions["true_condition"] == c) & (condition_predictions["predicted_condition"] != c)).sum())
            fp = int(((condition_predictions["true_condition"] != c) & (condition_predictions["predicted_condition"] == c)).sum())
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            recalls.append(rec)
            precisions.append(prec)
            f1s.append(f1)
        if recalls:
            condition_metrics.append({"metric": "balanced_accuracy", "value": float(np.mean(recalls))})
            condition_metrics.append({"metric": "macro_precision", "value": float(np.mean(precisions))})
            condition_metrics.append({"metric": "macro_recall", "value": float(np.mean(recalls))})
            condition_metrics.append({"metric": "macro_f1", "value": float(np.mean(f1s))})

if condition_metrics:
    condition_metrics_df = pd.DataFrame(condition_metrics).drop_duplicates("metric")
    print("=== Condition Test Evaluation Metrics ===")
    show(condition_metrics_df)
else:
    condition_metrics_df = pd.DataFrame(columns=["metric", "value"])
    print("No condition metrics were found or computed.")

# Display per-class metrics if available
per_class_df = None
if isinstance(condition_report, dict) and "test" in condition_report and "per_class" in condition_report["test"]:
    per_class_df = pd.DataFrame(condition_report["test"]["per_class"])
elif (RESULTS / "condition" / "condition_test_per_class_metrics.csv").exists():
    per_class_df = load_csv(RESULTS / "condition" / "condition_test_per_class_metrics.csv")

if per_class_df is not None and not per_class_df.empty:
    print("\\n=== Per-Class Performance ===")
    show(per_class_df)

# Display confusion matrix if available
cm_path = first_existing(
    RESULTS / "condition" / "condition_confusion_matrix.csv",
    RESULTS / "condition" / "condition_test_confusion_matrix_raw.csv"
)
if cm_path:
    cm_df = load_csv(cm_path)
    if cm_df is not None and not cm_df.empty:
        print("\\n=== Confusion Matrix ===")
        show(cm_df)

if condition_predictions is not None and not condition_predictions.empty:
    print(f"\\nCondition test predictions: {len(condition_predictions):,}")
    print("Prediction columns:", list(condition_predictions.columns))
"""

lines = [line + "\n" for line in new_cell9_code.split("\n")]
if lines and lines[-1] == "\n":
    lines = lines[:-1]
elif lines:
    lines[-1] = lines[-1].rstrip("\n")

nb["cells"][9]["source"] = lines

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Updated NB27 with safe display handler successfully!")
