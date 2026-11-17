"""
Monocular Depth Estimation Interface using Depth Anything V2.
Generates relative dense depth maps from RGB road images.
"""

from pathlib import Path
from typing import Union, Tuple, Optional
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
import logging

logger = logging.getLogger(__name__)

DEFAULT_DEPTH_MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"


class DepthEstimator:
    """
    Wrapper for Depth Anything V2 monocular depth estimation model.
    """
    def __init__(
        self,
        model_id: str = DEFAULT_DEPTH_MODEL_ID,
        device: Optional[str] = None,
        input_size: int = 518,
    ):
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.input_size = input_size
        self.processor = None
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from transformers import AutoImageProcessor, AutoModelForDepthEstimation
        except ImportError as e:
            raise ImportError("Install transformers: pip install transformers accelerate") from e

        logger.info("Loading Depth Anything V2 (%s) on %s...", self.model_id, self.device)
        self.processor = AutoImageProcessor.from_pretrained(self.model_id)
        self.model = AutoModelForDepthEstimation.from_pretrained(self.model_id)
        self.model.to(self.device)
        self.model.eval()

    @torch.inference_mode()
    def predict_depth_map(self, image: Union[Image.Image, np.ndarray]) -> np.ndarray:
        """
        Infers dense relative depth map for a single PIL image or RGB numpy array.
        Returns 2D float32 numpy array of shape (height, width), normalized to [0, 1].
        Higher values represent closer proximity in relative depth.
        """
        if isinstance(image, np.ndarray):
            pil_img = Image.fromarray(image.astype(np.uint8))
        else:
            pil_img = image.convert("RGB")

        orig_w, orig_h = pil_img.size

        inputs = self.processor(images=pil_img, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model(**inputs)
        predicted_depth = outputs.predicted_depth

        # Interpolate back to original frame dimensions
        prediction = F.interpolate(
            predicted_depth.unsqueeze(1),
            size=(orig_h, orig_w),
            mode="bicubic",
            align_corners=False,
        ).squeeze().cpu().numpy()

        # Normalize depth map to [0, 1]
        d_min = prediction.min()
        d_max = prediction.max()
        if d_max - d_min > 1e-5:
            norm_depth = (prediction - d_min) / (d_max - d_min)
        else:
            norm_depth = np.zeros_like(prediction)

        return norm_depth.astype(np.float32)

    @staticmethod
    def colorize_depth(depth_map: np.ndarray, colormap: str = "inferno") -> Image.Image:
        """
        Converts a normalized 2D depth map into a colorized PIL image for visualization.
        """
        import matplotlib.cm as cm
        cmap = cm.get_cmap(colormap)
        colored = (cmap(depth_map)[:, :, :3] * 255.0).astype(np.uint8)
        return Image.fromarray(colored)
