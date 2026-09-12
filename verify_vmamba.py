"""
VMamba checkpoint verification script.
Run from the project root:  python verify_vmamba.py

Tests:
  1. Model imports without error
  2. Checkpoint loads with strict=True (zero missing / unexpected keys)
  3. Forward pass on a dummy (1, 3, 224, 224) tensor -> output shape (1, 4)
  4. Softmax produces valid probability distribution
  5. Image preprocessing pipeline works on a generated test image
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import torch
import torch.nn.functional as F
from PIL import Image

print("=" * 60)
print("  VMamba Checkpoint Verification")
print("=" * 60)

# 1. Import architecture
print("\n[1] Importing VMamba architecture ... ", end="", flush=True)
try:
    from model.vmamba import VMamba
    print("OK")
except Exception as e:
    print(f"FAILED\n  {e}")
    sys.exit(1)

# 2. Instantiate model
print("[2] Building model ... ", end="", flush=True)
try:
    model = VMamba(in_chans=3, embed_dim=32, depths=(1,1,1,1), num_classes=4, patch_size=4)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"OK  ({total_params:,} parameters)")
except Exception as e:
    print(f"FAILED\n  {e}")
    sys.exit(1)

# 3. Load checkpoint (strict=True)
ckpt_path = "model/best_vmamba.pth"
print(f"[3] Loading checkpoint with strict=True ... ", end="", flush=True)
try:
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    state_dict = ckpt.get("model_state_dict", ckpt)
    missing, unexpected = model.load_state_dict(state_dict, strict=True)
    epoch    = ckpt.get("epoch", "?")
    best_acc = ckpt.get("best_acc", float("nan"))
    print(f"OK  epoch={epoch}  best_acc={best_acc:.4f}%")
    if missing or unexpected:
        print(f"  MISSING ({len(missing)}): {missing[:3]}")
        print(f"  UNEXPECTED ({len(unexpected)}): {unexpected[:3]}")
        sys.exit(1)
    print(f"     Missing=0  Unexpected=0")
except Exception as e:
    print(f"FAILED\n  {e}")
    sys.exit(1)

# 4. Forward pass on dummy tensor
print("[4] Forward pass (1, 3, 224, 224) ... ", end="", flush=True)
try:
    model.eval()
    dummy = torch.randn(1, 3, 224, 224)
    with torch.no_grad():
        logits = model(dummy)
    assert logits.shape == (1, 4), f"Expected (1,4), got {logits.shape}"
    probs = F.softmax(logits, dim=1)[0]
    assert abs(probs.sum().item() - 1.0) < 1e-4
    print(f"OK  shape={tuple(logits.shape)}")
    names = ['MildDemented','ModerateDemented','NonDemented','VeryMildDemented']
    print(f"     Probs: { {n: round(probs[i].item(),4) for i,n in enumerate(names)} }")
except Exception as e:
    print(f"FAILED\n  {e}")
    sys.exit(1)

# 5. Full inference pipeline test
print("[5] run_inference() on synthetic image ... ", end="", flush=True)
try:
    tmp_path = "uploads/__verify_test__.jpg"
    os.makedirs("uploads", exist_ok=True)
    Image.new("RGB", (256, 256), color=(128, 100, 90)).save(tmp_path)

    from model.inference import run_inference, CLASS_NAMES
    result = run_inference(tmp_path)
    os.remove(tmp_path)

    assert result["error"] is None, f"Inference error: {result['error']}"
    assert result["predicted_class"] in CLASS_NAMES
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["all_probs"]) == 4
    print(f"OK")
    print(f"     Predicted : {result['predicted_class']}")
    print(f"     Confidence: {result['confidence']*100:.2f}%")
    print(f"     All probs : {result['all_probs']}")
except Exception as e:
    print(f"FAILED\n  {e}")
    sys.exit(1)

print()
print("=" * 60)
print("  ALL CHECKS PASSED")
print("=" * 60)
