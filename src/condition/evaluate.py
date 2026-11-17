import os
import json
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import transforms
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt

from src.condition.model import MultiTaskConditionClassifier, TIME_CLASSES, WEATHER_CLASSES
from src.condition.train import ConditionDataset

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
MODELS_DIR = PROJECT_ROOT / "models" / "condition"
RESULTS_DIR = PROJECT_ROOT / "results" / "condition"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def plot_and_save_cm(cm, classes, title, save_path):
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.matshow(cm, cmap="Blues")
    fig.colorbar(cax)
    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, rotation=45, ha="left")
    ax.set_yticklabels(classes)
    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="red" if cm[i, j] > cm.max()/2 else "black")
    plt.title(title, pad=20)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def evaluate_condition_model():
    ckpt_path = MODELS_DIR / "condition_multitask_best.pth"
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint missing: {ckpt_path}. Run train.py first.")

    ckpt = torch.load(ckpt_path, map_location=DEVICE)
    model = MultiTaskConditionClassifier(pretrained=False).to(DEVICE)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    test_csv = RESULTS_DIR / "condition_test_split.csv"
    if not test_csv.exists():
        raise FileNotFoundError(f"Test split missing: {test_csv}")
    test_df = pd.read_csv(test_csv)

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    loader = DataLoader(ConditionDataset(test_df, val_transform), batch_size=32, shuffle=False)

    time_preds, time_targets, time_confs = [], [], []
    weather_preds, weather_targets, weather_confs = [], [], []
    img_names = []

    with torch.no_grad():
        for batch in loader:
            imgs = batch["image"].to(DEVICE)
            outputs = model(imgs)

            t_probs = F.softmax(outputs["time_logits"], dim=-1)
            w_probs = F.softmax(outputs["weather_logits"], dim=-1)

            t_pred = t_probs.argmax(dim=-1).cpu().numpy()
            w_pred = w_probs.argmax(dim=-1).cpu().numpy()

            time_preds.extend(t_pred)
            time_targets.extend(batch["time_label"].numpy())
            time_confs.extend(t_probs.max(dim=-1).values.cpu().numpy())

            weather_preds.extend(w_pred)
            weather_targets.extend(batch["weather_label"].numpy())
            weather_confs.extend(w_probs.max(dim=-1).values.cpu().numpy())
            img_names.extend(batch["image_name"])

    time_targets = np.array(time_targets)
    time_preds = np.array(time_preds)
    weather_targets = np.array(weather_targets)
    weather_preds = np.array(weather_preds)

    # Time metrics
    time_cm = confusion_matrix(time_targets, time_preds, labels=[0, 1])
    time_report = classification_report(time_targets, time_preds, target_names=TIME_CLASSES, output_dict=True)
    plot_and_save_cm(time_cm, TIME_CLASSES, "Time Classification Confusion Matrix", RESULTS_DIR / "time_confusion_matrix.png")
    pd.DataFrame(time_cm, index=TIME_CLASSES, columns=TIME_CLASSES).to_csv(RESULTS_DIR / "time_confusion_matrix.csv")

    # Weather metrics
    weather_cm = confusion_matrix(weather_targets, weather_preds, labels=[0, 1, 2])
    weather_report = classification_report(weather_targets, weather_preds, target_names=WEATHER_CLASSES, output_dict=True)
    plot_and_save_cm(weather_cm, WEATHER_CLASSES, "Weather Classification Confusion Matrix", RESULTS_DIR / "weather_confusion_matrix.png")
    pd.DataFrame(weather_cm, index=WEATHER_CLASSES, columns=WEATHER_CLASSES).to_csv(RESULTS_DIR / "weather_confusion_matrix.csv")

    # Combined prediction table
    records = []
    incorrect = []
    for i in range(len(img_names)):
        t_true = TIME_CLASSES[time_targets[i]]
        t_pred_str = TIME_CLASSES[time_preds[i]]
        w_true = WEATHER_CLASSES[weather_targets[i]]
        w_pred_str = WEATHER_CLASSES[weather_preds[i]]
        t_conf = float(time_confs[i])
        w_conf = float(weather_confs[i])
        is_correct = (t_true == t_pred_str and w_true == w_pred_str)

        row_dict = {
            "image_name": img_names[i],
            "true_time": t_true,
            "pred_time": t_pred_str,
            "time_confidence": t_conf,
            "time_correct": (t_true == t_pred_str),
            "true_weather": w_true,
            "pred_weather": w_pred_str,
            "weather_confidence": w_conf,
            "weather_correct": (w_true == w_pred_str),
            "composite_true": f"{t_true} + {w_true}",
            "composite_pred": f"{t_pred_str} + {w_pred_str}",
            "overall_correct": is_correct
        }
        records.append(row_dict)
        if not is_correct:
            incorrect.append(row_dict)

    pred_df = pd.DataFrame(records)
    pred_df.to_csv(RESULTS_DIR / "condition_test_predictions.csv", index=False)

    incorrect_df = pd.DataFrame(incorrect)
    incorrect_df.to_csv(RESULTS_DIR / "incorrect_predictions.csv", index=False)

    # Per-class summary
    per_class_rows = []
    for cls in TIME_CLASSES:
        m = time_report[cls]
        per_class_rows.append({"Head": "Time", "Class": cls, "Precision": m["precision"], "Recall": m["recall"], "F1-Score": m["f1-score"], "Support": m["support"]})
    for cls in WEATHER_CLASSES:
        m = weather_report[cls]
        per_class_rows.append({"Head": "Weather", "Class": cls, "Precision": m["precision"], "Recall": m["recall"], "F1-Score": m["f1-score"], "Support": m["support"]})
    per_class_df = pd.DataFrame(per_class_rows)
    per_class_df.to_csv(RESULTS_DIR / "per_class_metrics.csv", index=False)

    overall_report = {
        "model_architecture": "MultiTaskConditionClassifier (Shared ResNet-18 Backbone)",
        "heads": {
            "time": {"classes": TIME_CLASSES, "accuracy": float(time_report["accuracy"]), "macro_f1": float(time_report["macro avg"]["f1-score"])},
            "weather": {"classes": WEATHER_CLASSES, "accuracy": float(weather_report["accuracy"]), "macro_f1": float(weather_report["macro avg"]["f1-score"])}
        },
        "overall_composite_accuracy": float(pred_df["overall_correct"].mean()),
        "test_sample_size": len(pred_df),
        "mean_time_confidence": float(np.mean(time_confs)),
        "mean_weather_confidence": float(np.mean(weather_confs))
    }

    with open(RESULTS_DIR / "condition_evaluation_report.json", "w") as f:
        json.dump(overall_report, f, indent=2)

    print("Condition evaluation report saved to results/condition/condition_evaluation_report.json")
    print(f"Time Accuracy: {time_report['accuracy']:.4f} | Weather Accuracy: {weather_report['accuracy']:.4f} | Composite Accuracy: {overall_report['overall_composite_accuracy']:.4f}")
    return overall_report


if __name__ == "__main__":
    evaluate_condition_model()
