"""
Explainable AI (XAI) Module for VMamba Alzheimer's MRI Platform
===============================================================
Computes authentic spatial feature attribution for the trained VMamba model.

Methodology:
  1. Forward pass computes intermediate Stage 4 spatial feature maps (7x7x256).
  2. Backward gradient of the target predicted class logit w.r.t. Stage 4 representations.
  3. Channel importance weighting (Global Average Pooling of gradients).
  4. Rectified linear combination yields non-negative attribution magnitude.
  5. Bilinear upsampling to original MRI dimensions + Jet/Clinical heatmap mapping.
  6. Alpha-blended composite overlay with original structural MRI slice.

Operates purely locally with PyTorch and NumPy (no external API or heavy dependencies).
"""

import os
import logging
import numpy as np
from PIL import Image

import torch
import torch.nn.functional as F

from model.vmamba import VMamba

logger = logging.getLogger(__name__)

# Class definitions (ImageFolder alphabetical order)
CLASS_NAMES = [
    "MildDemented",
    "ModerateDemented",
    "NonDemented",
    "VeryMildDemented",
]


def apply_clinical_colormap(vals: np.ndarray) -> np.ndarray:
    """
    Applies standard Jet colormap to float array in [0, 1] -> returns (H, W, 3) uint8.
    Pure NumPy implementation without requiring external plotting libraries.
    """
    v = np.clip(vals, 0.0, 1.0)
    r = np.clip(1.5 - np.abs(v * 4.0 - 3.0), 0.0, 1.0)
    g = np.clip(1.5 - np.abs(v * 4.0 - 2.0), 0.0, 1.0)
    b = np.clip(1.5 - np.abs(v * 4.0 - 1.0), 0.0, 1.0)
    rgb = np.stack([r, g, b], axis=-1)
    return (rgb * 255.0).astype(np.uint8)


def generate_xai_explanation(
    image_path: str,
    model: VMamba,
    preprocess_transform,
    target_class_idx: int = None,
    alpha: float = 0.45,
) -> dict:
    """
    Generates genuine XAI spatial attribution maps and overlays for a given MRI scan.

    Parameters
    ----------
    image_path : str
        Absolute filesystem path to the MRI scan image.
    model : VMamba
        Loaded VMamba model instance.
    preprocess_transform : torchvision.transforms.Compose
        Standard preprocessing pipeline matching training.
    target_class_idx : int, optional
        Target class index to explain (defaults to argmax predicted class).
    alpha : float, optional
        Overlay blending weight in [0, 1] (default 0.45).

    Returns
    -------
    dict with keys:
        heatmap_filename : str
        overlay_filename : str
        predicted_class  : str
        confidence       : float
        error            : str | None
    """
    try:
        model.eval()

        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found at '{image_path}'")

        orig_img = Image.open(image_path).convert("RGB")
        orig_w, orig_h = orig_img.size

        tensor = preprocess_transform(orig_img).unsqueeze(0)

        # 1. Forward through early stages without graph
        with torch.no_grad():
            x = model.patch_embed(tensor)
            x = model.stage1(x)
            x = model.merge1(x)
            x = model.stage2(x)
            x = model.merge2(x)
            x = model.stage3(x)
            x = model.merge3(x)

        # 2. Stage 4 feature representations with gradient tracking
        feat_in = x.detach().requires_grad_(True)
        feat_out = model.stage4(feat_in)  # (1, 7, 7, 256)
        norm_out = model.norm(feat_out)
        pool_out = norm_out.mean(dim=[1, 2])
        logits = model.head(pool_out)

        probs = F.softmax(logits, dim=1)[0]

        if target_class_idx is None:
            target_class_idx = probs.argmax().item()

        pred_class = CLASS_NAMES[target_class_idx]
        pred_conf = probs[target_class_idx].item()

        # 3. Compute gradients of target class logit w.r.t. Stage 4 representations
        score = logits[0, target_class_idx]
        grads = torch.autograd.grad(score, feat_out)[0]  # (1, 7, 7, 256)

        # 4. Channel importance weights via Global Average Pooling
        weights = grads.mean(dim=(1, 2), keepdim=True)  # (1, 1, 1, 256)

        # 5. Weighted combination + ReLU rectification
        cam = (weights * feat_out).sum(dim=-1, keepdim=True)  # (1, 7, 7, 1)
        cam = F.relu(cam).permute(0, 3, 1, 2)  # (1, 1, 7, 7)

        # 6. Upsample spatial attribution map to original MRI slice dimensions
        cam_up = F.interpolate(
            cam, size=(orig_h, orig_w), mode="bilinear", align_corners=False
        )
        cam_np = cam_up[0, 0].detach().cpu().numpy()

        # Normalize attribution map to [0, 1]
        c_min, c_max = cam_np.min(), cam_np.max()
        if c_max > c_min:
            cam_norm = (cam_np - c_min) / (c_max - c_min)
        else:
            cam_norm = np.zeros_like(cam_np)

        # 7. Render Heatmap Image
        heatmap_rgb = apply_clinical_colormap(cam_norm)
        heatmap_img = Image.fromarray(heatmap_rgb)

        # 8. Render Composite Overlay Image
        orig_np = np.array(orig_img).astype(np.float32)
        heatmap_np = heatmap_rgb.astype(np.float32)

        overlay_np = (1.0 - alpha) * orig_np + alpha * heatmap_np
        overlay_np = np.clip(overlay_np, 0, 255).astype(np.uint8)
        overlay_img = Image.fromarray(overlay_np)

        # 9. Save Artifacts to upload directory
        dir_name = os.path.dirname(image_path)
        base_name = os.path.splitext(os.path.basename(image_path))[0]

        heatmap_filename = f"{base_name}_xai_heatmap.png"
        overlay_filename = f"{base_name}_xai_overlay.png"

        heatmap_path = os.path.join(dir_name, heatmap_filename)
        overlay_path = os.path.join(dir_name, overlay_filename)

        heatmap_img.save(heatmap_path, format="PNG")
        overlay_img.save(overlay_path, format="PNG")

        logger.info(
            "[XAI] Generated attribution for %s (class=%s, conf=%.1f%%)",
            base_name,
            pred_class,
            pred_conf * 100,
        )

        return {
            "heatmap_filename": heatmap_filename,
            "overlay_filename": overlay_filename,
            "predicted_class":  pred_class,
            "confidence":       pred_conf,
            "error":            None,
        }

    except Exception as exc:
        logger.error("[XAI] Attribution generation failed: %s", exc)
        return {
            "heatmap_filename": None,
            "overlay_filename": None,
            "predicted_class":  "Unknown",
            "confidence":       0.0,
            "error":            str(exc),
        }
