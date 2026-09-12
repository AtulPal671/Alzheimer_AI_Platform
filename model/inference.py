"""
VMamba Inference Module — NeuroScan AI Platform
================================================
Provides input validation, singleton model loader, and `run_inference(file_path)`
that returns a structured result dict for a given brain MRI image file.

Class mapping (ImageFolder alphabetical order, confirmed by user & dataset):
    Index 0  →  MildDemented
    Index 1  →  ModerateDemented
    Index 2  →  NonDemented
    Index 3  →  VeryMildDemented

Preprocessing (matches Kaggle Alzheimer MRI training pipeline):
    1. PIL open → force RGB (handles grayscale / palette MRIs)
    2. Resize to 224 × 224
    3. ToTensor   → [0.0, 1.0], shape (3, 224, 224)
    4. Normalize  → ImageNet mean / std per channel
    5. Unsqueeze  → batch dim → (1, 3, 224, 224)

Input Validation:
    Enforces domain constraints of brain MRI scans (resolution, grayscale/chromaticity,
    contrast/dynamic range, dark background perimeter, anatomical foreground mask ratio,
    and bilateral anatomical symmetry) before any inference or database operations.
"""

import os
import threading
import logging

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from model.vmamba import VMamba

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "best_vmamba.pth")

CLASS_NAMES = [
    "MildDemented",
    "ModerateDemented",
    "NonDemented",
    "VeryMildDemented",
]

_INPUT_SIZE   = 224
_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD  = [0.229, 0.224, 0.225]

# ---------------------------------------------------------------------------
# Preprocessing pipeline
# ---------------------------------------------------------------------------

_preprocess = transforms.Compose([
    transforms.Resize((_INPUT_SIZE, _INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
])

# ---------------------------------------------------------------------------
# Domain Input Validation
# ---------------------------------------------------------------------------

def validate_mri_image(image_path: str) -> tuple[bool, str | None]:
    """
    Validates whether an uploaded file is a valid brain MRI scan before inference.
    Rejects non-MRI images (paintings, photos, screenshots, documents, blank/noise, corrupted files).

    Returns:
        (is_valid: bool, error_message: str | None)
    """
    if not os.path.isfile(image_path):
        return False, "Invalid input: Image file not found."

    # 1. Structural File Verification
    try:
        with Image.open(image_path) as img_check:
            img_check.verify()
        # Re-open after verify() closes the handle
        img = Image.open(image_path)
    except Exception as exc:
        logger.warning("[Validation] File integrity check failed for %s: %s", image_path, exc)
        return False, "Invalid input: Please upload a valid brain MRI scan (corrupted or unreadable image file)."

    # 2. Dimension and Aspect Ratio Bounds
    width, height = img.size
    if width < 64 or height < 64:
        logger.warning("[Validation] Resolution %dx%d is too low for MRI analysis", width, height)
        return False, "Invalid input: Image resolution is too low for brain MRI analysis (minimum 64×64)."

    aspect_ratio = width / height
    if aspect_ratio < 0.4 or aspect_ratio > 2.5:
        logger.warning("[Validation] Aspect ratio %.2f outside MRI bounds", aspect_ratio)
        return False, "Invalid input: Please upload a valid brain MRI scan (invalid anatomical aspect ratio)."

    # Convert to RGB array for multi-channel analysis
    img_rgb = img.convert("RGB")
    arr = np.array(img_rgb, dtype=np.float32)

    # 3. Grayscale / Chromaticity Check
    # Medical MRI scans are single-channel grayscale. Even in 3-channel RGB containers,
    # channel differences |R - G|, |R - B|, |G - B| are near zero.
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    rg_diff = np.abs(r - g).mean()
    rb_diff = np.abs(r - b).mean()
    gb_diff = np.abs(g - b).mean()
    chroma_score = float((rg_diff + rb_diff + gb_diff) / 3.0)

    if chroma_score > 10.0:
        logger.warning("[Validation] Non-grayscale image rejected (chroma_score=%.2f): %s", chroma_score, image_path)
        return False, "Invalid input: Please upload a valid brain MRI scan (color image / non-MRI detected)."

    # Compute luminance (Grayscale intensity 0..255)
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b

    # 4. Contrast & Dynamic Range (Reject blank, solid, or flat noise images)
    min_val, max_val = float(gray.min()), float(gray.max())
    std_val = float(gray.std())
    if (max_val - min_val) < 35.0 or std_val < 12.0:
        logger.warning("[Validation] Insufficient contrast (range=%.1f, std=%.1f): %s", max_val - min_val, std_val, image_path)
        return False, "Invalid input: Please upload a valid brain MRI scan (insufficient contrast or blank image)."

    # 5. Background Perimeter vs. Center Anatomical Contrast
    # In a brain MRI scan, the skull/brain is centered in the field of view surrounded by dark/black background.
    h, w = gray.shape
    bh = max(2, int(h * 0.08))
    bw = max(2, int(w * 0.08))
    border_pixels = np.concatenate([
        gray[:bh, :].flatten(),
        gray[-bh:, :].flatten(),
        gray[:, :bw].flatten(),
        gray[:, -bw:].flatten()
    ])
    border_mean = float(border_pixels.mean())
    border_median = float(np.median(border_pixels))

    center_box = gray[int(h * 0.25):int(h * 0.75), int(w * 0.25):int(w * 0.75)]
    center_mean = float(center_box.mean())

    if border_mean > 75.0:
        logger.warning("[Validation] Bright border perimeter rejected (border_mean=%.2f): %s", border_mean, image_path)
        return False, "Invalid input: Please upload a valid brain MRI scan (image lacks characteristic dark background perimeter)."

    if center_mean <= (border_mean + 15.0):
        logger.warning("[Validation] Central anatomical contrast missing (center=%.2f, border=%.2f): %s", center_mean, border_mean, image_path)
        return False, "Invalid input: Please upload a valid brain MRI scan (central anatomical structure missing)."

    # 6. Anatomical Foreground Mask Ratio
    # Brain tissue foreground mask (pixels above background noise floor)
    bg_thresh = max(15.0, border_median + 10.0)
    fg_mask = gray > bg_thresh
    fg_ratio = float(fg_mask.mean())

    if fg_ratio < 0.15 or fg_ratio > 0.88:
        logger.warning("[Validation] Anatomical foreground ratio out of range (fg_ratio=%.2f): %s", fg_ratio, image_path)
        return False, "Invalid input: Please upload a valid brain MRI scan (anatomical mask out of normal range)."

    # 7. Bilateral Anatomical Symmetry Check
    center_w = w // 2
    min_w = min(center_w, w - center_w)
    lh = gray[:, center_w - min_w:center_w]
    rh = np.fliplr(gray[:, center_w:center_w + min_w])
    rel_diff = float(np.abs(lh - rh).mean() / (center_mean + 1e-5))

    if rel_diff > 0.80:
        logger.warning("[Validation] Bilateral symmetry check failed (rel_diff=%.2f): %s", rel_diff, image_path)
        return False, "Invalid input: Please upload a valid brain MRI scan (fails anatomical bilateral structure check)."

    return True, None


# ---------------------------------------------------------------------------
# Singleton model state
# ---------------------------------------------------------------------------

_model: VMamba | None = None
_model_lock = threading.Lock()
_load_error: str | None = None


def _build_and_load_model() -> VMamba:
    """
    Instantiate the VMamba architecture and load best_vmamba.pth.
    Called exactly once. Raises on any mismatch (strict=True).
    """
    model = VMamba(
        in_chans=3,
        embed_dim=32,
        depths=(1, 1, 1, 1),
        num_classes=4,
        patch_size=4,
    )

    if not os.path.isfile(_CHECKPOINT_PATH):
        raise FileNotFoundError(
            f"VMamba checkpoint not found at: {_CHECKPOINT_PATH}"
        )

    ckpt = torch.load(_CHECKPOINT_PATH, map_location="cpu", weights_only=False)

    # The checkpoint wraps the state-dict under 'model_state_dict'
    state_dict = ckpt.get("model_state_dict", ckpt)

    missing, unexpected = model.load_state_dict(state_dict, strict=True)

    model.eval()
    logger.info(
        "[VMamba] Checkpoint loaded — epoch %s, best_acc=%.2f%%",
        ckpt.get("epoch", "?"),
        ckpt.get("best_acc", float("nan")),
    )
    return model


def get_model() -> VMamba:
    """
    Returns the singleton model, loading it on first call.
    Thread-safe. Raises on load failure so Flask can log it at startup.
    """
    global _model, _load_error
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        if _load_error is not None:
            raise RuntimeError(_load_error)
        try:
            _model = _build_and_load_model()
        except Exception as exc:
            _load_error = str(exc)
            logger.error("[VMamba] Model load failed: %s", exc)
            raise
    return _model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_inference(image_path: str) -> dict:
    """
    Run domain validation and VMamba inference on a single image file.

    Parameters
    ----------
    image_path : str
        Absolute path to the uploaded image.

    Returns
    -------
    dict with keys:
        is_valid        : bool   — True if input passed brain MRI domain validation
        predicted_class : str | None — e.g. "MildDemented"
        confidence      : float  — highest-class probability, range [0, 1]
        all_probs       : dict | None — {class_name: probability} for all 4 classes
        heatmap_filename: str | None
        overlay_filename: str | None
        error           : str | None — set if validation or inference failed
    """
    # ── 1. DOMAIN VALIDATION (Must pass before model inference) ──────
    is_valid, validation_err = validate_mri_image(image_path)
    if not is_valid:
        logger.info("[VMamba] Input rejected during validation: %s", validation_err)
        return {
            "is_valid":         False,
            "predicted_class":  None,
            "confidence":       0.0,
            "all_probs":        None,
            "heatmap_filename": None,
            "overlay_filename": None,
            "error":            validation_err or "Invalid input: Please upload a valid brain MRI scan.",
        }

    # ── 2. MODEL INFERENCE ──────────────────────────────────────────
    try:
        model = get_model()

        # Preprocess
        try:
            img = Image.open(image_path).convert("RGB")
        except Exception as exc:
            raise ValueError(f"Cannot open image '{image_path}': {exc}") from exc

        tensor = _preprocess(img).unsqueeze(0)  # (1, 3, 224, 224)

        # Forward pass
        with torch.no_grad():
            logits = model(tensor)  # (1, 4)

        probs = F.softmax(logits, dim=1)[0]  # (4,)

        predicted_idx   = probs.argmax().item()
        predicted_class = CLASS_NAMES[predicted_idx]
        confidence      = probs[predicted_idx].item()

        all_probs = {
            name: round(probs[i].item(), 6)
            for i, name in enumerate(CLASS_NAMES)
        }

        # ── 3. XAI Feature Attribution ──────────────────────────────
        xai_res = {}
        try:
            from model.xai import generate_xai_explanation
            xai_res = generate_xai_explanation(
                image_path=image_path,
                model=model,
                preprocess_transform=_preprocess,
                target_class_idx=predicted_idx,
            )
        except Exception as xai_exc:
            logger.warning("[VMamba] XAI attribution generation skipped: %s", xai_exc)
            xai_res = {"heatmap_filename": None, "overlay_filename": None, "error": str(xai_exc)}

        logger.info(
            "[VMamba] Inference → %s (%.1f%%)",
            predicted_class,
            confidence * 100,
        )

        return {
            "is_valid":         True,
            "predicted_class":  predicted_class,
            "confidence":       confidence,
            "all_probs":        all_probs,
            "heatmap_filename": xai_res.get("heatmap_filename"),
            "overlay_filename": xai_res.get("overlay_filename"),
            "error":            None,
        }

    except Exception as exc:
        logger.error("[VMamba] Inference error: %s", exc)
        return {
            "is_valid":         False,
            "predicted_class":  None,
            "confidence":       0.0,
            "all_probs":        None,
            "heatmap_filename": None,
            "overlay_filename": None,
            "error":            str(exc),
        }
