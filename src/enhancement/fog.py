import os
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageFilter

from src.enhancement.night import ResidualBlock

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
MODELS_DIR = PROJECT_ROOT / "models" / "enhancement" / "fog"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class FogEnhancer(nn.Module):
    """
    Fog dehazing & visibility recovery network:
    Removes atmospheric veil and restores dark-channel contrast for fog scenes.
    """
    def __init__(self, base_channels=32, num_res_blocks=4):
        super().__init__()
        self.enc1 = nn.Sequential(
            nn.Conv2d(3, base_channels, 3, padding=1),
            nn.ReLU(inplace=True)
        )
        self.enc2 = nn.Sequential(
            nn.Conv2d(base_channels, base_channels * 2, 3, stride=2, padding=1),
            nn.ReLU(inplace=True)
        )
        self.enc3 = nn.Sequential(
            nn.Conv2d(base_channels * 2, base_channels * 4, 3, stride=2, padding=1),
            nn.ReLU(inplace=True)
        )
        self.res = nn.Sequential(*[ResidualBlock(base_channels * 4) for _ in range(num_res_blocks)])
        self.dec2 = nn.Sequential(
            nn.Conv2d(base_channels * 4, base_channels * 2, 3, padding=1),
            nn.ReLU(inplace=True)
        )
        self.dec1 = nn.Sequential(
            nn.Conv2d(base_channels * 2, base_channels, 3, padding=1),
            nn.ReLU(inplace=True)
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


def make_fog_reference_target(img):
    """
    Pseudo-reference target for dehazing:
    Atmospheric light attenuation + contrast stretching.
    """
    img = img.convert("RGB")
    arr = np.asarray(img).astype(np.float32) / 255.0

    # Low frequency veil estimation
    smooth_img = img.filter(ImageFilter.GaussianBlur(radius=4.0))
    smooth = np.asarray(smooth_img).astype(np.float32) / 255.0

    # Dehaze adjustment: remove 35% of low-frequency veil and stretch dynamic range
    dehazed = (arr - 0.35 * smooth) / (1.0 - 0.35 + 1e-4)
    dehazed = np.clip(dehazed * 1.15, 0.0, 1.0)
    arr_out = (dehazed * 255.0).astype(np.uint8)
    return Image.fromarray(arr_out)
