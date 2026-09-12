# PyTorch Model Integration Area

This directory is reserved for holding the trained PyTorch VMamba baseline model weights and inference modules.

## Integration Plan

1. Place PyTorch checkpoint files (`.pt` or `.pth`) inside this folder:
   - Example: `model/vmamba_alzheimer_best.pth`
2. Create `model/inference.py` to:
   - Load PyTorch model architecture.
   - Preprocess input 3D/2D MRI slices (normalization, resize to 224x224/256x256, tensor conversion).
   - Execute inference pass (`model.eval()`).
   - Return softmax class probabilities for:
     - **Cognitively Normal (CN)**
     - **Mild Cognitive Impairment (MCI)**
     - **Alzheimer's Disease (AD)**
