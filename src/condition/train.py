import os
import json
import time
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

from src.condition.model import MultiTaskConditionClassifier, ConditionClassifier5Class

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
MODELS_DIR = PROJECT_ROOT / "models" / "condition"
RESULTS_DIR = PROJECT_ROOT / "results" / "condition"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TIME_MAP = {"Day": 0, "Night": 1}
WEATHER_MAP = {"Clear": 0, "Rain": 1, "Fog": 2}
FIVE_CLASS_MAP = {"Day": 0, "Night": 1, "Rain": 2, "Fog": 3, "Unknown": 4}


class ConditionDataset(Dataset):
    def __init__(self, df, transform=None):
        self.df = df.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_name = str(row["image_name"])
        if not img_name.endswith(".jpg"):
            img_name += ".jpg"
        img_path = PROJECT_ROOT / "datasets" / "raw" / "BDD100K" / "images" / "100k" / str(row["split"]) / img_name

        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)

        time_label = TIME_MAP.get(row.get("time_label", "Day"), 0)
        weather_label = WEATHER_MAP.get(row.get("weather_label", "Clear"), 0)
        five_label = FIVE_CLASS_MAP.get(row.get("condition", "Day"), 4)

        return {
            "image": image,
            "time_label": torch.tensor(time_label, dtype=torch.long),
            "weather_label": torch.tensor(weather_label, dtype=torch.long),
            "five_label": torch.tensor(five_label, dtype=torch.long),
            "image_name": row["image_name"]
        }


def get_balanced_splits(meta_path, samples_per_class=1200, seed=42):
    np.random.seed(seed)
    df = pd.read_csv(meta_path)
    # Filter known classes
    df = df[df["time_label"].isin(["Day", "Night"]) & df["weather_label"].isin(["Clear", "Rain", "Fog"])].copy()

    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]
    test_df = df[df["split"] == "test"]

    # Sample balanced train sets across time and weather
    train_sampled = []
    for (t, w), group in train_df.groupby(["time_label", "weather_label"]):
        n = min(len(group), samples_per_class)
        train_sampled.append(group.sample(n=n, random_state=seed))
    train_balanced = pd.concat(train_sampled).sample(frac=1.0, random_state=seed).reset_index(drop=True)

    val_sampled = []
    for (t, w), group in val_df.groupby(["time_label", "weather_label"]):
        n = min(len(group), 250)
        val_sampled.append(group.sample(n=n, random_state=seed))
    val_balanced = pd.concat(val_sampled).sample(frac=1.0, random_state=seed).reset_index(drop=True)

    test_sampled = []
    for (t, w), group in test_df.groupby(["time_label", "weather_label"]):
        n = min(len(group), 300)
        test_sampled.append(group.sample(n=n, random_state=seed))
    test_balanced = pd.concat(test_sampled).sample(frac=1.0, random_state=seed).reset_index(drop=True)

    print(f"Condition splits -> Train: {len(train_balanced)}, Val: {len(val_balanced)}, Test: {len(test_balanced)}")
    return train_balanced, val_balanced, test_balanced


def train_condition_model(epochs=6, batch_size=32, lr=1e-4):
    print(f"Using device: {DEVICE}")
    meta_path = PROJECT_ROOT / "datasets" / "processed" / "metadata" / "condition_labels.csv"
    train_df, val_df, test_df = get_balanced_splits(meta_path)

    # Save test set partition for evaluation
    test_df.to_csv(RESULTS_DIR / "condition_test_split.csv", index=False)

    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_loader = DataLoader(ConditionDataset(train_df, train_transform), batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(ConditionDataset(val_df, val_transform), batch_size=batch_size, shuffle=False, num_workers=0)

    model = MultiTaskConditionClassifier(pretrained=True).to(DEVICE)
    # Also initialize standard 5-class model to train together
    model_5class = ConditionClassifier5Class(num_classes=5, pretrained=True).to(DEVICE)

    criterion_time = nn.CrossEntropyLoss()
    criterion_weather = nn.CrossEntropyLoss(weight=torch.tensor([1.0, 1.2, 2.5]).to(DEVICE)) # upweight fog
    criterion_5class = nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(list(model.parameters()) + list(model_5class.parameters()), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0
    history = []

    for epoch in range(1, epochs + 1):
        model.train()
        model_5class.train()
        total_loss, correct_time, correct_weather, total_samples = 0.0, 0, 0, 0

        start_t = time.time()
        for batch in train_loader:
            imgs = batch["image"].to(DEVICE)
            t_labels = batch["time_label"].to(DEVICE)
            w_labels = batch["weather_label"].to(DEVICE)
            five_labels = batch["five_label"].to(DEVICE)

            optimizer.zero_grad()
            outputs = model(imgs)
            out_5 = model_5class(imgs)

            l_time = criterion_time(outputs["time_logits"], t_labels)
            l_weather = criterion_weather(outputs["weather_logits"], w_labels)
            l_legacy = criterion_5class(outputs["legacy_logits"], five_labels)
            l_5 = criterion_5class(out_5, five_labels)

            loss = l_time + 1.2 * l_weather + 0.5 * l_legacy + 0.5 * l_5
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * imgs.size(0)
            correct_time += (outputs["time_logits"].argmax(dim=-1) == t_labels).sum().item()
            correct_weather += (outputs["weather_logits"].argmax(dim=-1) == w_labels).sum().item()
            total_samples += imgs.size(0)

        scheduler.step()
        train_time_acc = correct_time / total_samples
        train_weather_acc = correct_weather / total_samples
        train_loss = total_loss / total_samples

        # Validation
        model.eval()
        model_5class.eval()
        v_correct_time, v_correct_weather, v_total = 0, 0, 0
        with torch.no_grad():
            for batch in val_loader:
                imgs = batch["image"].to(DEVICE)
                t_labels = batch["time_label"].to(DEVICE)
                w_labels = batch["weather_label"].to(DEVICE)
                outputs = model(imgs)
                v_correct_time += (outputs["time_logits"].argmax(dim=-1) == t_labels).sum().item()
                v_correct_weather += (outputs["weather_logits"].argmax(dim=-1) == w_labels).sum().item()
                v_total += imgs.size(0)

        val_time_acc = v_correct_time / v_total
        val_weather_acc = v_correct_weather / v_total
        combined_val_acc = (val_time_acc + val_weather_acc) / 2.0
        elapsed = time.time() - start_t

        print(f"Epoch {epoch}/{epochs} ({elapsed:.1f}s) | Loss: {train_loss:.4f} | Time Val Acc: {val_time_acc:.4f} | Weather Val Acc: {val_weather_acc:.4f} | Combined: {combined_val_acc:.4f}")

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_time_acc": train_time_acc,
            "train_weather_acc": train_weather_acc,
            "val_time_acc": val_time_acc,
            "val_weather_acc": val_weather_acc,
            "combined_val_acc": combined_val_acc
        })

        if combined_val_acc > best_val_acc:
            best_val_acc = combined_val_acc
            # Save multi-task checkpoint
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_time_acc": val_time_acc,
                "val_weather_acc": val_weather_acc,
                "combined_val_acc": combined_val_acc,
                "time_classes": ["Day", "Night"],
                "weather_classes": ["Clear", "Rain", "Fog"]
            }, MODELS_DIR / "condition_multitask_best.pth")

            # Also save legacy 5-class checkpoint so existing code / legacy notebooks can load it seamlessly
            torch.save(model_5class.state_dict(), MODELS_DIR / "condition_resnet18_best.pth")
            print(f"  -> Saved best checkpoints at epoch {epoch} (Combined Acc: {best_val_acc:.4f})")

    pd.DataFrame(history).to_csv(RESULTS_DIR / "condition_training_history.csv", index=False)
    print("Condition model training complete.")
    return best_val_acc


if __name__ == "__main__":
    train_condition_model()
