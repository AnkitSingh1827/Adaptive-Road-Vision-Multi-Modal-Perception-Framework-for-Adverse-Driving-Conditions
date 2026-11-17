from pathlib import Path
import torch
import torchvision.transforms as transforms
from PIL import Image

from src.enhancement.night import NightEnhancer
from src.enhancement.rain import RainEnhancer
from src.enhancement.fog import FogEnhancer

PROJECT_ROOT = Path(r"C:\Users\ankit\Desktop\Adaptive_Road_Vision")
MODELS_DIR = PROJECT_ROOT / "models" / "enhancement"


class AdaptiveEnhancer:
    """
    Unified Adaptive Road Vision Enhancer:
    Dynamically routes frames to Night, Rain, or Fog enhancer based on condition analysis.
    If condition is Day + Clear, passes frame through without distortion.
    """
    def __init__(self, device=None, img_size=256):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.img_size = img_size
        self.to_tensor = transforms.ToTensor()
        self.models = {}
        self._load_models()

    def _load_models(self):
        configs = [
            ("Night", NightEnhancer(32, 4), MODELS_DIR / "night" / "night_enhancer_best.pth"),
            ("Rain", RainEnhancer(32, 4), MODELS_DIR / "rain" / "rain_enhancer_best.pth"),
            ("Fog", FogEnhancer(32, 4), MODELS_DIR / "fog" / "fog_enhancer_best.pth"),
        ]
        for name, model, path in configs:
            if path.exists():
                ckpt = torch.load(path, map_location=self.device)
                model.load_state_dict(ckpt["model_state_dict"])
                model.to(self.device).eval()
                self.models[name] = model
                print(f"[AdaptiveEnhancer] Loaded {name} enhancer from {path.name}")
            else:
                print(f"[AdaptiveEnhancer] Warning: Checkpoint missing for {name}: {path}")

    @torch.inference_mode()
    def enhance_pil(self, pil_image, condition_label):
        """
        Enhances a PIL image adaptively based on predicted condition.
        Returns: enhanced PIL image (same size as original).
        """
        cond = condition_label.strip()
        # Determine target model
        target_model = None
        if "Fog" in cond:
            target_model = self.models.get("Fog")
        elif "Rain" in cond:
            target_model = self.models.get("Rain")
        elif "Night" in cond:
            target_model = self.models.get("Night")

        if target_model is None:
            # Condition is clear / day -> no restoration needed
            return pil_image.copy()

        orig_w, orig_h = pil_image.size
        resized = pil_image.resize((self.img_size, self.img_size), Image.Resampling.BILINEAR)
        x = self.to_tensor(resized).unsqueeze(0).to(self.device)

        out = target_model(x)[0].cpu()
        out_np = (out.permute(1, 2, 0).numpy() * 255.0).clip(0, 255).astype("uint8")
        out_pil = Image.fromarray(out_np).resize((orig_w, orig_h), Image.Resampling.BILINEAR)
        return out_pil
