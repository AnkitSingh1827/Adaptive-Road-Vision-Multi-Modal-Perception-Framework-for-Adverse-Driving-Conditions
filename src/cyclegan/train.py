import os
import time
from pathlib import Path
import random
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from PIL import Image

from src.cyclegan.dataset import UnpairedCycleGANDataset

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
MODELS_DIR = PROJECT_ROOT / "models" / "cyclegan"
RESULTS_DIR = PROJECT_ROOT / "results" / "cyclegan"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class ResnetBlock(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.conv_block = nn.Sequential(
            nn.ReflectionPad2d(1),
            nn.Conv2d(dim, dim, 3, bias=False),
            nn.InstanceNorm2d(dim),
            nn.ReLU(True),
            nn.ReflectionPad2d(1),
            nn.Conv2d(dim, dim, 3, bias=False),
            nn.InstanceNorm2d(dim)
        )

    def forward(self, x):
        return x + self.conv_block(x)


class CycleGANGenerator(nn.Module):
    """
    Standard ResNet-based CycleGAN Generator (Johnson et al. 9/6 block architecture).
    """
    def __init__(self, input_nc=3, output_nc=3, ngf=64, n_blocks=6):
        super().__init__()
        layers = [
            nn.ReflectionPad2d(3),
            nn.Conv2d(input_nc, ngf, 7, bias=False),
            nn.InstanceNorm2d(ngf),
            nn.ReLU(True)
        ]
        # Downsampling
        mult = 1
        for _ in range(2):
            layers += [
                nn.Conv2d(ngf * mult, ngf * mult * 2, 3, stride=2, padding=1, bias=False),
                nn.InstanceNorm2d(ngf * mult * 2),
                nn.ReLU(True)
            ]
            mult *= 2

        # ResNet blocks
        for _ in range(n_blocks):
            layers.append(ResnetBlock(ngf * mult))

        # Upsampling
        for _ in range(2):
            layers += [
                nn.ConvTranspose2d(ngf * mult, ngf * mult // 2, 3, stride=2, padding=1, output_padding=1, bias=False),
                nn.InstanceNorm2d(ngf * mult // 2),
                nn.ReLU(True)
            ]
            mult //= 2

        layers += [
            nn.ReflectionPad2d(3),
            nn.Conv2d(ngf, output_nc, 7),
            nn.Tanh()
        ]
        self.model = nn.Sequential(*layers)

    def forward(self, x):
        return self.model(x)


class PatchGANDiscriminator(nn.Module):
    """
    70x70 PatchGAN Discriminator.
    """
    def __init__(self, input_nc=3, ndf=64):
        super().__init__()
        self.model = nn.Sequential(
            nn.Conv2d(input_nc, ndf, 4, stride=2, padding=1),
            nn.LeakyReLU(0.2, True),
            nn.Conv2d(ndf, ndf * 2, 4, stride=2, padding=1, bias=False),
            nn.InstanceNorm2d(ndf * 2),
            nn.LeakyReLU(0.2, True),
            nn.Conv2d(ndf * 2, ndf * 4, 4, stride=2, padding=1, bias=False),
            nn.InstanceNorm2d(ndf * 4),
            nn.LeakyReLU(0.2, True),
            nn.Conv2d(ndf * 4, ndf * 8, 4, stride=1, padding=1, bias=False),
            nn.InstanceNorm2d(ndf * 8),
            nn.LeakyReLU(0.2, True),
            nn.Conv2d(ndf * 8, 1, 4, stride=1, padding=1)
        )

    def forward(self, x):
        return self.model(x)


def train_cyclegan_domain(domain_name, source_paths, fog_paths, epochs=60, batch_size=4, lr=2e-4, patience=8):
    print(f"\n=======================================================")
    print(f"CycleGAN Training: {domain_name} -> Fog ({len(source_paths)} sources, {len(fog_paths)} fog)")
    print(f"Epochs: {epochs} | Early Stopping Patience: {patience} | Device: {DEVICE}")
    print(f"=======================================================")

    target_dir = MODELS_DIR / f"{domain_name.lower()}_to_fog"
    target_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = target_dir / "checkpoint_final.pth"
    best_ckpt_path = target_dir / "checkpoint_best.pth"

    dataset = UnpairedCycleGANDataset(source_paths, fog_paths, img_size=256, is_train=True)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    # Generators
    G_AB = CycleGANGenerator().to(DEVICE)  # Source -> Fog
    G_BA = CycleGANGenerator().to(DEVICE)  # Fog -> Source

    # Discriminators
    D_A = PatchGANDiscriminator().to(DEVICE)
    D_B = PatchGANDiscriminator().to(DEVICE)

    criterion_GAN = nn.MSELoss()
    criterion_cycle = nn.L1Loss()
    criterion_identity = nn.L1Loss()

    optimizer_G = torch.optim.Adam(
        list(G_AB.parameters()) + list(G_BA.parameters()),
        lr=lr, betas=(0.5, 0.999)
    )
    optimizer_D = torch.optim.Adam(
        list(D_A.parameters()) + list(D_B.parameters()),
        lr=lr, betas=(0.5, 0.999)
    )

    scaler = torch.amp.GradScaler("cuda") if DEVICE.type == "cuda" else None

    best_g_loss = float("inf")
    patience_counter = 0

    for epoch in range(1, epochs + 1):
        G_AB.train()
        G_BA.train()
        D_A.train()
        D_B.train()

        total_loss_G, total_loss_D, total_cycle = 0.0, 0.0, 0.0
        start_t = time.time()

        for i, batch in enumerate(loader):
            real_A = batch["A"].to(DEVICE)
            real_B = batch["B"].to(DEVICE)

            # -----------------
            #  Train Generators
            # -----------------
            optimizer_G.zero_grad()
            with torch.amp.autocast("cuda", enabled=(DEVICE.type == "cuda")):
                # Identity loss
                loss_id_A = criterion_identity(G_BA(real_A), real_A) * 5.0
                loss_id_B = criterion_identity(G_AB(real_B), real_B) * 5.0
                loss_identity = (loss_id_A + loss_id_B) / 2.0

                # GAN loss
                fake_B = G_AB(real_A)
                pred_fake_B = D_B(fake_B)
                target_real = torch.ones_like(pred_fake_B)
                target_fake = torch.zeros_like(pred_fake_B)
                loss_GAN_AB = criterion_GAN(pred_fake_B, target_real)

                fake_A = G_BA(real_B)
                pred_fake_A = D_A(fake_A)
                loss_GAN_BA = criterion_GAN(pred_fake_A, target_real)
                loss_GAN = (loss_GAN_AB + loss_GAN_BA) / 2.0

                # Cycle loss
                recov_A = G_BA(fake_B)
                loss_cycle_A = criterion_cycle(recov_A, real_A) * 10.0

                recov_B = G_AB(fake_A)
                loss_cycle_B = criterion_cycle(recov_B, real_B) * 10.0
                loss_cycle = (loss_cycle_A + loss_cycle_B) / 2.0

                # Total G loss
                loss_G = loss_GAN + loss_cycle + loss_identity

            if scaler:
                scaler.scale(loss_G).backward()
                scaler.step(optimizer_G)
                scaler.update()
            else:
                loss_G.backward()
                optimizer_G.step()

            # ---------------------
            #  Train Discriminators
            # ---------------------
            optimizer_D.zero_grad()
            with torch.amp.autocast("cuda", enabled=(DEVICE.type == "cuda")):
                loss_real_A = criterion_GAN(D_A(real_A), target_real)
                loss_fake_A = criterion_GAN(D_A(fake_A.detach()), target_fake)
                loss_D_A = (loss_real_A + loss_fake_A) / 2.0

                loss_real_B = criterion_GAN(D_B(real_B), target_real)
                loss_fake_B = criterion_GAN(D_B(fake_B.detach()), target_fake)
                loss_D_B = (loss_real_B + loss_fake_B) / 2.0

                loss_D = (loss_D_A + loss_D_B) / 2.0

            if scaler:
                scaler.scale(loss_D).backward()
                scaler.step(optimizer_D)
                scaler.update()
            else:
                loss_D.backward()
                optimizer_D.step()

            total_loss_G += loss_G.item()
            total_loss_D += loss_D.item()
            total_cycle += loss_cycle.item()

        avg_loss_G = total_loss_G / len(loader)
        avg_loss_D = total_loss_D / len(loader)
        avg_cycle = total_cycle / len(loader)
        elapsed = time.time() - start_t
        print(f"Epoch [{epoch:02d}/{epochs:02d}] {elapsed:.1f}s | G Loss: {avg_loss_G:.4f} (Cycle: {avg_cycle:.4f}) | D Loss: {avg_loss_D:.4f}")

        state_dict_payload = {
            "epoch": epoch,
            "generator": G_AB.state_dict(),
            "generator_state_dict": G_AB.state_dict(),
            "netG": G_AB.state_dict(),
            "G_A": G_AB.state_dict(),
            "G_AB_state_dict": G_AB.state_dict(),
            "G_BA_state_dict": G_BA.state_dict(),
            "domain": domain_name,
            "target": "Fog",
            "loss_G": avg_loss_G,
            "loss_cycle": avg_cycle
        }

        # Check for improvement and early stopping
        if avg_loss_G < best_g_loss - 1e-4:
            best_g_loss = avg_loss_G
            patience_counter = 0
            torch.save(state_dict_payload, best_ckpt_path)
            torch.save(state_dict_payload, ckpt_path)
            print(f"Saved best checkpoint: {best_ckpt_path}")
        else:
            patience_counter += 1
            torch.save(state_dict_payload, ckpt_path)
            if patience_counter >= patience:
                print(f"[EARLY STOPPING] Triggered at epoch {epoch}. Best G Loss: {best_g_loss:.4f}")
                break

    return ckpt_path


def main():
    day_paths = sorted(list((PROJECT_ROOT / "datasets" / "cyclegan" / "day").glob("*.jpg")))[:200]
    night_paths = sorted(list((PROJECT_ROOT / "datasets" / "cyclegan" / "night").glob("*.jpg")))[:200]
    fog_paths = sorted(list((PROJECT_ROOT / "datasets" / "cyclegan" / "fog").glob("*.jpg")))

    print(f"CycleGAN training setup: {len(day_paths)} Day, {len(night_paths)} Night, {len(fog_paths)} Fog")

    train_cyclegan_domain("Day", day_paths, fog_paths, epochs=60, batch_size=4, patience=8)
    train_cyclegan_domain("Night", night_paths, fog_paths, epochs=60, batch_size=4, patience=8)
    print("CycleGAN models trained and saved successfully.")


if __name__ == "__main__":
    main()
