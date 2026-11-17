import os
from pathlib import Path
import random
from PIL import Image
import torch
from torch.utils.data import Dataset
import torchvision.transforms as transforms

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


class UnpairedCycleGANDataset(Dataset):
    """
    Unpaired dataset for CycleGAN training:
    Domain A: Day or Night images (Source)
    Domain B: Real Fog images (Target)
    """
    def __init__(self, domain_a_paths, domain_b_paths, img_size=256, is_train=True):
        self.domain_a_paths = [Path(p) for p in domain_a_paths if Path(p).suffix.lower() in IMG_EXTS]
        self.domain_b_paths = [Path(p) for p in domain_b_paths if Path(p).suffix.lower() in IMG_EXTS]
        self.is_train = is_train

        if is_train:
            self.transform = transforms.Compose([
                transforms.Resize((img_size, img_size), Image.Resampling.BICUBIC),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize((img_size, img_size), Image.Resampling.BICUBIC),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
            ])

    def __len__(self):
        return max(len(self.domain_a_paths), len(self.domain_b_paths))

    def __getitem__(self, idx):
        path_a = self.domain_a_paths[idx % len(self.domain_a_paths)]
        # For unpaired domain B, randomly sample when training
        if self.is_train:
            path_b = random.choice(self.domain_b_paths)
        else:
            path_b = self.domain_b_paths[idx % len(self.domain_b_paths)]

        img_a = Image.open(path_a).convert("RGB")
        img_b = Image.open(path_b).convert("RGB")

        return {
            "A": self.transform(img_a),
            "B": self.transform(img_b),
            "path_A": str(path_a),
            "path_B": str(path_b)
        }
