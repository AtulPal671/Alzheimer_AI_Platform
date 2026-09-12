"""
VMamba: Visual State Space Model — Pure PyTorch Inference Implementation
========================================================================
Matches best_vmamba.pth exactly (91 state_dict keys, all float32).

Architecture — custom VMamba-Tiny variant:
  PatchEmbed : Conv2d(in_channels=3, out_channels=32, kernel=4, stride=4)
  Stage1     : 1× VSSBlock (dim=32)
  Merge1     : PatchMerging  → dim=64
  Stage2     : 1× VSSBlock (dim=64)
  Merge2     : PatchMerging  → dim=128
  Stage3     : 1× VSSBlock (dim=128)
  Merge3     : PatchMerging  → dim=256
  Stage4     : 1× VSSBlock (dim=256)
  Norm       : LayerNorm(256)
  Head       : Linear(256, 4)

SS2D config (derived from checkpoint tensors):
  K=4 scan directions, d_state=16, expand=2
  dt_rank = math.ceil(d_model / 16)  → 2 / 4 / 8 / 16 per stage
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Selective Scan — fully vectorised, O(L) memory, no Python loops
# ---------------------------------------------------------------------------

def selective_scan(u, delta, A, B, C, D_param, delta_softplus=True):
    """
    Direct sequential selective scan — numerically stable by construction.

    Recurrence:  h_t = dA_t * h_{t-1} + dB_t
                 y_t = einsum('bdn,bn->bd', h_t, C_t) + D * u_t

    Fully vectorised across (B, D, N); only the time dimension is sequential.
    For B=1, CPU inference this is fast enough and avoids all overflow/NaN issues
    that plague log-cumsum approximations when dA values are very small.

    Args
    ----
    u       : (B, D, L)
    delta   : (B, D, L)   dt_proj bias already added by caller
    A       : (D, N)      negative-definite state matrix
    B       : (B, N, L)
    C       : (B, N, L)
    D_param : (D,)
    delta_softplus : bool
    """
    if delta_softplus:
        delta = F.softplus(delta)

    B_size, D, L = u.shape
    N = A.shape[1]

    # Pre-compute time-varying transition matrices and inputs
    # dA[t] = exp(delta[t] * A) — shape (B, D, L, N)
    dA = torch.exp(delta.unsqueeze(-1) * A[None, :, None, :])
    # dB[t] = (delta[t] * u[t]) * B[t] — shape (B, D, L, N)
    #   delta*u:  (B, D, L) -> unsqueeze(-1) -> (B, D, L, 1)
    #   B: (B, N, L) -> permute -> (B, L, N) -> unsqueeze(1) -> (B, 1, L, N)
    dB = (delta * u).unsqueeze(-1) * B.permute(0, 2, 1).unsqueeze(1)

    # Sequential recurrence — h: (B, D, N) running state
    h = torch.zeros(B_size, D, N, device=u.device, dtype=u.dtype)
    ys = []
    for t in range(L):
        h = dA[:, :, t, :] * h + dB[:, :, t, :]     # (B, D, N)
        # y_t = sum_n h_n * C_n  for each (b, d)
        ys.append((h * C.permute(0, 2, 1)[:, t:t+1, :]).sum(dim=-1))  # (B, D)

    y = torch.stack(ys, dim=2)                        # (B, D, L)
    y = y + D_param[None, :, None] * u
    return y


# ---------------------------------------------------------------------------
# Cross-scan helpers  (4-direction 2-D scanning)
# ---------------------------------------------------------------------------

def cross_scan(x):
    """
    x  : (B, C, H, W)
    out: (B, 4, C, L)  —  4 scan directions
    """
    x_flat  = x.flatten(2)                       # row-major  (B, C, H*W)
    xt_flat = x.transpose(-2, -1).flatten(2)     # col-major  (B, C, W*H)
    return torch.stack([
        x_flat,
        x_flat.flip(-1),
        xt_flat,
        xt_flat.flip(-1),
    ], dim=1)                                     # (B, 4, C, L)


def cross_merge(ys, H, W):
    """
    ys : (B, 4, C, L)
    out: (B, H, W, C)  —  inverse scan + sum
    """
    B, _, C, L = ys.shape
    y0 = ys[:, 0]                                                       # (B, C, L)
    y1 = ys[:, 1].flip(-1)
    y2 = ys[:, 2].reshape(B, C, W, H).transpose(-2, -1).flatten(2)     # un-transpose
    y3 = ys[:, 3].flip(-1).reshape(B, C, W, H).transpose(-2, -1).flatten(2)
    y  = (y0 + y1 + y2 + y3).reshape(B, C, H, W).permute(0, 2, 3, 1)  # (B,H,W,C)
    return y


# ---------------------------------------------------------------------------
# SS2D — the selective-scan 2-D block (checkpoint key prefix: *.ss2d.*)
# ---------------------------------------------------------------------------

class SS2D(nn.Module):
    """
    Parameter names mirror the checkpoint exactly:
      in_proj, conv2d, out_norm, out_proj   — nn.Module submodules
      x_proj_weight, A_logs, Ds,
      dt_projs_weight, dt_projs_bias        — nn.Parameter
    """

    def __init__(self, d_model: int, d_state: int = 16,
                 d_conv: int = 3, expand: int = 2, K: int = 4):
        super().__init__()
        self.d_model  = d_model
        self.d_state  = d_state
        self.d_inner  = d_model * expand          # 64 / 128 / 256 / 512
        self.K        = K
        self.dt_rank  = math.ceil(d_model / 16)   # 2 / 4 / 8 / 16

        d_inner  = self.d_inner
        dt_rank  = self.dt_rank

        # ── sub-modules with named weight tensors ──
        self.in_proj  = nn.Linear(d_model, d_inner * 2, bias=False)
        self.conv2d   = nn.Conv2d(d_inner, d_inner, d_conv,
                                   groups=d_inner, padding=(d_conv - 1) // 2)
        self.act      = nn.SiLU()
        self.out_norm = nn.LayerNorm(d_inner)
        self.out_proj = nn.Linear(d_inner, d_model, bias=False)
        self.dropout  = nn.Identity()             # no-op; present so _metadata version key loads

        # ── stacked parameters (K separate projections, merged for speed) ──
        # x_proj_weight : (K, dt_rank + 2*d_state, d_inner)
        self.x_proj_weight   = nn.Parameter(torch.empty(K, dt_rank + d_state * 2, d_inner))
        # dt_projs_weight : (K, d_inner, dt_rank)
        self.dt_projs_weight = nn.Parameter(torch.empty(K, d_inner, dt_rank))
        # dt_projs_bias   : (K, d_inner)
        self.dt_projs_bias   = nn.Parameter(torch.empty(K, d_inner))
        # A_logs : (K * d_inner, d_state)
        self.A_logs = nn.Parameter(torch.empty(K * d_inner, d_state))
        # Ds     : (K * d_inner,)
        self.Ds     = nn.Parameter(torch.empty(K * d_inner))

    # ------------------------------------------------------------------
    def forward_core(self, x: torch.Tensor) -> torch.Tensor:
        """
        x   : (B, d_inner, H, W)  after conv + activation
        out : (B, H, W, d_inner)
        """
        B, C, H, W = x.shape
        K       = self.K
        d_inner = self.d_inner
        d_state = self.d_state
        dt_rank = self.dt_rank

        xs = cross_scan(x)                          # (B, 4, d_inner, L)
        A  = -torch.exp(self.A_logs)                # (K*d_inner, d_state)

        ys = []
        for k in range(K):
            u_k = xs[:, k]                          # (B, d_inner, L)

            # project: d_inner → dt_rank + 2*d_state
            x_dbl = F.linear(u_k.permute(0, 2, 1),
                             self.x_proj_weight[k])  # (B, L, dt_rank+2*d_state)

            dts_k = x_dbl[:, :, :dt_rank]
            Bs_k  = x_dbl[:, :, dt_rank:dt_rank + d_state]
            Cs_k  = x_dbl[:, :, dt_rank + d_state:]

            # dt projection: dt_rank → d_inner
            dt_k = (F.linear(dts_k, self.dt_projs_weight[k])
                    + self.dt_projs_bias[k])          # (B, L, d_inner)

            A_k = A[k * d_inner:(k + 1) * d_inner]   # (d_inner, d_state)
            D_k = self.Ds[k * d_inner:(k + 1) * d_inner]  # (d_inner,)

            y_k = selective_scan(
                u       = u_k,                        # (B, d_inner, L)
                delta   = dt_k.permute(0, 2, 1),      # (B, d_inner, L)
                A       = A_k,                        # (d_inner, d_state)
                B       = Bs_k.permute(0, 2, 1),      # (B, d_state, L)
                C       = Cs_k.permute(0, 2, 1),      # (B, d_state, L)
                D_param = D_k,
                delta_softplus=True,
            )                                         # (B, d_inner, L)
            ys.append(y_k)

        ys_t = torch.stack(ys, dim=1)               # (B, 4, d_inner, L)
        y    = cross_merge(ys_t, H, W)              # (B, H, W, d_inner)
        return self.out_norm(y)

    # ------------------------------------------------------------------
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x   : (B, H, W, d_model)
        out : (B, H, W, d_model)
        """
        d_inner = self.d_inner
        xz      = self.in_proj(x)                   # (B, H, W, 2*d_inner)
        x_in, z = xz[..., :d_inner], xz[..., d_inner:]

        x_in = self.act(self.conv2d(x_in.permute(0, 3, 1, 2)))  # (B,d_inner,H,W)

        y = self.forward_core(x_in)                 # (B, H, W, d_inner)
        y = y * F.silu(z)                           # gate
        return self.out_proj(y)                     # (B, H, W, d_model)


# ---------------------------------------------------------------------------
# Mlp — 2-layer feed-forward (checkpoint keys: mlp.fc1.*, mlp.fc2.*)
# ---------------------------------------------------------------------------

class Mlp(nn.Module):
    def __init__(self, dim: int, mlp_ratio: int = 4):
        super().__init__()
        self.fc1  = nn.Linear(dim, dim * mlp_ratio)
        self.act  = nn.GELU()
        self.fc2  = nn.Linear(dim * mlp_ratio, dim)
        self.drop = nn.Identity()

    def forward(self, x):
        return self.fc2(self.act(self.fc1(x)))


# ---------------------------------------------------------------------------
# VSSBlock — norm + ss2d + mlp with dual residuals
# ---------------------------------------------------------------------------

class VSSBlock(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.norm1     = nn.LayerNorm(dim)
        self.ss2d      = SS2D(d_model=dim)
        self.drop_path = nn.Identity()   # stochastic depth = 0 at inference
        self.norm2     = nn.LayerNorm(dim)
        self.mlp       = Mlp(dim)

    def forward(self, x):
        # residual 1 — state-space branch
        x = x + self.ss2d(self.norm1(x))
        # residual 2 — MLP branch
        x = x + self.mlp(self.norm2(x))
        return x


# ---------------------------------------------------------------------------
# VSSStage — wraps a ModuleList of VSSBlocks (key: stageN.blocks.*)
# ---------------------------------------------------------------------------

class VSSStage(nn.Module):
    def __init__(self, dim: int, depth: int = 1):
        super().__init__()
        self.blocks = nn.ModuleList([VSSBlock(dim) for _ in range(depth)])

    def forward(self, x):
        for blk in self.blocks:
            x = blk(x)
        return x


# ---------------------------------------------------------------------------
# PatchMerging — Swin-style 2×2 merge (keys: mergeN.norm.*, mergeN.reduction.*)
# ---------------------------------------------------------------------------

class PatchMerging(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.norm      = nn.LayerNorm(4 * dim)
        self.reduction = nn.Linear(4 * dim, 2 * dim, bias=False)

    def forward(self, x):
        # x: (B, H, W, C)
        x0 = x[:, 0::2, 0::2, :]
        x1 = x[:, 1::2, 0::2, :]
        x2 = x[:, 0::2, 1::2, :]
        x3 = x[:, 1::2, 1::2, :]
        x  = torch.cat([x0, x1, x2, x3], dim=-1)  # (B, H/2, W/2, 4C)
        return self.reduction(self.norm(x))         # (B, H/2, W/2, 2C)


# ---------------------------------------------------------------------------
# PatchEmbed  (key: patch_embed.projection.*)
# ---------------------------------------------------------------------------

class PatchEmbed(nn.Module):
    def __init__(self, in_chans: int = 3, embed_dim: int = 32, patch_size: int = 4):
        super().__init__()
        self.projection = nn.Conv2d(in_chans, embed_dim, patch_size, stride=patch_size)

    def forward(self, x):
        # x: (B, 3, H, W)  →  (B, H/4, W/4, embed_dim)
        return self.projection(x).permute(0, 2, 3, 1)


# ---------------------------------------------------------------------------
# VMamba — full classifier (matches checkpoint 1-to-1)
# ---------------------------------------------------------------------------

class VMamba(nn.Module):
    """
    Custom VMamba-Tiny variant trained on Kaggle Alzheimer MRI dataset.

    embed_dim=32  →  stage dims: [32, 64, 128, 256]
    4 output classes:
        0 = MildDemented
        1 = ModerateDemented
        2 = NonDemented
        3 = VeryMildDemented
    """

    def __init__(
        self,
        in_chans:    int   = 3,
        embed_dim:   int   = 32,
        depths:      tuple = (1, 1, 1, 1),
        num_classes: int   = 4,
        patch_size:  int   = 4,
    ):
        super().__init__()
        dims = [embed_dim * (2 ** i) for i in range(len(depths))]  # [32,64,128,256]

        self.patch_embed = PatchEmbed(in_chans, embed_dim, patch_size)
        self.stage1      = VSSStage(dims[0], depths[0])
        self.merge1      = PatchMerging(dims[0])
        self.stage2      = VSSStage(dims[1], depths[1])
        self.merge2      = PatchMerging(dims[1])
        self.stage3      = VSSStage(dims[2], depths[2])
        self.merge3      = PatchMerging(dims[2])
        self.stage4      = VSSStage(dims[3], depths[3])
        self.norm        = nn.LayerNorm(dims[3])
        self.head        = nn.Linear(dims[3], num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, 3, 224, 224)
        x = self.patch_embed(x)   # (B, 56, 56, 32)

        x = self.stage1(x)        # (B, 56, 56, 32)
        x = self.merge1(x)        # (B, 28, 28, 64)

        x = self.stage2(x)        # (B, 28, 28, 64)
        x = self.merge2(x)        # (B, 14, 14, 128)

        x = self.stage3(x)        # (B, 14, 14, 128)
        x = self.merge3(x)        # (B,  7,  7, 256)

        x = self.stage4(x)        # (B,  7,  7, 256)

        x = self.norm(x)          # (B,  7,  7, 256)
        x = x.mean(dim=[1, 2])    # global average pool → (B, 256)
        x = self.head(x)          # (B, 4)
        return x
