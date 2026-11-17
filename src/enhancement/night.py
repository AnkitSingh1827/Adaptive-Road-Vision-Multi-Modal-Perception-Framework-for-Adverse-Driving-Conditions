import os
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageEnhance

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
MODELS_DIR = PROJECT_ROOT / "models" / "enhancement" / "night"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


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


class NightEnhancer(nn.Module):
    """
    Night vision restoration network:
    Enhances underexposed road imagery, dark roads, headlights and pedestrian visibility.
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


def make_night_reference_target(img):
    """
    Pseudo-reference target for low-light enhancement:
    Gamma correction + Adaptive contrast enhancement.
    """
    img = Image.fromarray(np.asarray(img).astype(np.uint8))
    img = ImageEnhance.Brightness(img).enhance(1.55)
    img = ImageEnhance.Contrast(img).enhance(1.12)
    arr = np.asarray(img).astype(np.float32) / 255.0
    arr = np.power(np.clip(arr, 0.0, 1.0), 0.78)
    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)
