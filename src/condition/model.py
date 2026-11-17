import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from torchvision.models import ResNet18_Weights

TIME_CLASSES = ["Day", "Night"]
WEATHER_CLASSES = ["Clear", "Rain", "Fog"]
FIVE_CLASSES = ["Day", "Night", "Rain", "Fog", "Unknown"]


class MultiTaskConditionClassifier(nn.Module):
    """
    Multi-task condition classification network:
    Input frame -> ResNet-18 backbone -> Dual heads:
        1. Time classifier: Day / Night
        2. Weather classifier: Clear / Rain / Fog
    """
    def __init__(self, pretrained=True, dropout=0.2):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        self.backbone = models.resnet18(weights=weights)
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()

        self.dropout = nn.Dropout(dropout)
        self.time_head = nn.Linear(in_features, 2)       # [Day, Night]
        self.weather_head = nn.Linear(in_features, 3)    # [Clear, Rain, Fog]
        # Legacy compatibility head (5-class: Day, Night, Rain, Fog, Unknown)
        self.legacy_head = nn.Linear(in_features, 5)

    def forward(self, x):
        features = self.backbone(x)
        features_drop = self.dropout(features)
        time_logits = self.time_head(features_drop)
        weather_logits = self.weather_head(features_drop)
        legacy_logits = self.legacy_head(features_drop)
        return {
            "time_logits": time_logits,
            "weather_logits": weather_logits,
            "legacy_logits": legacy_logits,
            "features": features
        }

    @torch.inference_mode()
    def predict(self, x):
        """
        Inference helper returning structured predictions.
        """
        self.eval()
        outputs = self.forward(x)
        time_probs = F.softmax(outputs["time_logits"], dim=-1)
        weather_probs = F.softmax(outputs["weather_logits"], dim=-1)

        time_idx = torch.argmax(time_probs, dim=-1)
        weather_idx = torch.argmax(weather_probs, dim=-1)

        batch_size = x.size(0)
        results = []
        for i in range(batch_size):
            t_class = TIME_CLASSES[time_idx[i].item()]
            w_class = WEATHER_CLASSES[weather_idx[i].item()]
            t_conf = time_probs[i, time_idx[i]].item()
            w_conf = weather_probs[i, weather_idx[i]].item()

            # Determine dominant condition for adaptive enhancement
            if w_class == "Fog":
                primary_condition = "Fog"
            elif w_class == "Rain":
                primary_condition = "Rain"
            elif t_class == "Night":
                primary_condition = "Night"
            else:
                primary_condition = "Day"

            composite = f"{t_class} + {w_class}"
            results.append({
                "time": t_class,
                "weather": w_class,
                "composite": composite,
                "primary_condition": primary_condition,
                "time_confidence": t_conf,
                "weather_confidence": w_conf,
                "overall_confidence": min(t_conf, w_conf)
            })
        return results if batch_size > 1 else results[0]


class ConditionClassifier5Class(nn.Module):
    """
    Standard ResNet-18 5-class single-head classifier (Day, Night, Rain, Fog, Unknown).
    Retained for 100% compatibility with notebooks 12 & 13.
    """
    def __init__(self, num_classes=5, pretrained=True):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        self.model = models.resnet18(weights=weights)
        in_features = self.model.fc.in_features
        self.model.fc = nn.Linear(in_features, num_classes)

    def forward(self, x):
        return self.model(x)
