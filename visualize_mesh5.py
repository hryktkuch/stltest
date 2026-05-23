import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ---- Parameters ----
NOZZLE_DIA    = 1.8
CIRCLE_DIA    = 50.0
TOTAL_HEIGHT  = 50.0
RING_HEIGHT   = 1.2
LAYER_HEIGHT  = 6.0
N_OSC_PER_REV = 9.5
Z_AMP         = LAYER_HEIGHT / 2   # = 3.0 mm
N_MESH_REVS   = 7
# --------------------

R = CIRCLE_DIA / 2

# PHASE = -π/2:  sin(9.5 * 4π - π/2) = sin(-π/2) = -1  → mesh starts at valley
PHASE = -np.pi / 2

# ------------------------------------------------------------------
# Key relationship (same PHASE, same N_OSC_PER_REV, half-integer):
#   0th pre-rev peak at angle θ  =  RING_HEIGHT + θ/(2π) * LAYER_HEIGHT
#   mesh valley at angle θ       =  RING_HEIGHT + θ/(2π) * LAYER_HEIGHT
#   → they are EQUAL at every angle θ  → 0th layer supports 1st mesh layer ✓
# ------------------------------------------------------------------

# ==================================================
# 1. Bottom ring  (t: 0→2π, constant Z = RING_HEIGHT)
# ==================================================
t0 = np.linspace(0, 2*np.pi, 3000)
x0, y0 = R*np.cos(t0), R*np.sin(t0)
z0 = np.full_like(t0, RING_HEIGHT)

# ==================================================
# 2. 0th pre-revolution  (t: 2π→4π)
#    z_base: from (RING_HEIGHT + Z_AMP - LAYER_HEIGHT) = -1.8 mm
#            to   (RING_HEIGHT + Z_AMP)                =  4.2 mm
#    z = max(RING_HEIGHT, z_base + Z_AMP*sin(...))
#    → valleys below RING_HEIGHT are clipped flat
#    → arches grow from zero to full height as z_base rises
# ==================================================
t_pre_s = 2*np.pi
t_pre_e = 4*np.pi
t_pre = np.linspace(t_pre_s, t_pre_e, 6000)

z_base_pre = (RING_HEIGHT + Z_AMP - LAYER_HEIGHT) \
             + (t_pre - t_pre_s) / (2*np.pi) * LAYER_HEIGHT
# at t=2π: z_base = -1.8,  peak = 1.2mm (= RING_HEIGHT, no clip), valleys clipped
# at t=4π: z_base =  4.2,  peak = 7.2mm, valley = 1.2mm (no clip)

z_pre_raw = z_base_pre + Z_AMP * np.sin(N_OSC_PER_REV * t_pre + PHASE)
z_pre     = np.maximum(z_pre_raw, RING_HEIGHT)  # clip at base ring level

x_pre, y_pre = R*np.cos(t_pre), R*np.sin(t_pre)

# ==================================================
# 3. Mesh  (t: 4π → 4π + N_MESH_REVS*2π)
#    first valley = RING_HEIGHT, no clipping needed
# ==================================================
t1_s = 4*np.pi
t1_e = t1_s + 2*np.pi * N_MESH_REVS
t1   = np.linspace(t1_s, t1_e, 25000)

z_base_s = RING_HEIGHT + Z_AMP      # 4.2 mm
z_range  = N_MESH_REVS * LAYER_HEIGHT  # 42 mm
z_base1  = z_base_s + (t1 - t1_s) / (t1_e - t1_s) * z_range
z1       = z_base1 + Z_AMP * np.sin(N_OSC_PER_REV * t1 + PHASE)
# at t=4π: z = 4.2 + 3*(-1) = 1.2mm ✓  continuous with pre-revolution

x1, y1 = R*np.cos(t1), R*np.sin(t1)
z1_end = float(z1[-1])   # ≈ 49.2 mm

# ==================================================
# 4. Top ring  (t: t1_e → t1_e+2π)
# ==================================================
t2_s = t1_e
t2   = np.linspace(t2_s, t2_s + 2*np.pi, 3000)
x2, y2 = R*np.cos(t2), R*np.sin(t2)
z2   = np.linspace(z1_end, TOTAL_HEIGHT, 3000)

# Combine
x_all = np.concatenate([x0, x_pre, x1, x2])
y_all = np.concatenate([y0, y_pre, y1, y2])
z_all = np.concatenate([z0, z_pre, z1, z2])
t_all = np.concatenate([t0, t_pre, t1, t2])

# ==================================================
# Figure
# ==================================================
fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor('#f8f8f8')

# ---- 3D view ----
ax3 = fig.add_subplot(1, 2, 1, projection='3d')
ax3.set_facecolor('#f0f0f0')

theta_c = np.linspace(0, 2*np.pi, 120)
z_c     = np.linspace(0, TOTAL_HEIGHT, 40)
Th, Zc  = np.meshgrid(theta_c, z_c)
ax3.plot_surface(R*np.cos(Th), R*np.sin(Th), Zc,
                 alpha=0.05, color='gray', linewidth=0)

ax3.plot(x0, y0, z0, color='orangered', lw=3.0, zorder=5,
         label=f'Bottom ring (Z={RING_HEIGHT}mm)')
ax3.plot(x_pre, y_pre, z_pre, color='limegreen', lw=2.0, zorder=4,
         label='0th pre-rev (clipped)')
sc = ax3.scatter(x1, y1, z1, c=z1, cmap='plasma', s=0.2, alpha=0.9)
ax3.plot(x2, y2, z2, color='deepskyblue', lw=3.0, zorder=5,
         label='Top ring')

fig.colorbar(sc, ax=ax3, shrink=0.5, pad=0.02, label='Z (mm)')
ax3.set_xlabel('X (mm)', labelpad=6)
ax3.set_ylabel('Y (mm)', labelpad=6)
ax3.set_zlabel('Z (mm)', labelpad=6)
ax3.set_zlim(0, TOTAL_HEIGHT)
ax3.view_init(elev=22, azim=-55)
ax3.legend(fontsize=8, loc='upper left')
ax3.set_title(
    f'One-stroke mesh tube  (φ{CIRCLE_DIA}mm × H{TOTAL_HEIGHT}mm)\n'
    f'ring {RING_HEIGHT}mm | layer {LAYER_HEIGHT}mm | {N_OSC_PER_REV} osc/rev',
    fontsize=10)

# ---- Unwrapped view ----
ax2 = fig.add_subplot(1, 2, 2)
ax2.set_facecolor('#f0f0f0')

circ = 2*np.pi*R

# Build plate
ax2.fill_between([0, circ], -0.5, 0, color='#aaa', alpha=0.35, label='Build plate (Z=0)')

# Bottom ring
ax2.axhline(RING_HEIGHT, color='orangered', lw=2.5, alpha=0.9,
            label=f'Bottom ring (Z={RING_HEIGHT}mm)')

# 0th pre-revolution
arc_pre = (t_pre % (2*np.pi)) * R
ax2.plot(arc_pre, z_pre, color='limegreen', lw=1.8, alpha=0.9,
         label='0th pre-rev (clipped)')
# Show unclipped ghost
ax2.plot(arc_pre, z_pre_raw, color='limegreen', lw=0.7, ls='--', alpha=0.35,
         label='0th pre-rev (unclipped, ghost)')

# Mesh
cmap = plt.cm.plasma
for rev in range(N_MESH_REVS + 1):
    mask = (t1 >= t1_s + rev*2*np.pi) & (t1 < t1_s + (rev+1)*2*np.pi)
    if not mask.any():
        continue
    col = cmap(rev / (N_MESH_REVS + 1))
    ax2.plot((t1[mask] % (2*np.pi)) * R, z1[mask], color=col, lw=1.1, alpha=0.85)

# Top ring
ax2.plot((t2 % (2*np.pi)) * R, z2, color='deepskyblue', lw=2.5, alpha=0.9,
         label='Top ring')

ax2.axhline(TOTAL_HEIGHT, color='deepskyblue', lw=0.8, ls='--', alpha=0.4)
ax2.set_xlim(0, circ)
ax2.set_ylim(-1, TOTAL_HEIGHT + 1)
ax2.set_xlabel('Circumferential arc length (mm)', fontsize=9)
ax2.set_ylabel('Z (mm)', fontsize=9)
ax2.set_title(
    'Unwrapped cylinder\n'
    'green=0th pre-rev (solid=clipped, dashed=ghost), colours=mesh revs',
    fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=7.5, loc='upper right')

plt.tight_layout()
plt.savefig('mesh_structure5.png', dpi=150, bbox_inches='tight')

print("Saved: mesh_structure5.png")
print(f"  Bottom ring : Z = {RING_HEIGHT} mm  (flat, 1 rev)")
print(f"  0th pre-rev : z_base -1.8→4.2 mm, clipped at {RING_HEIGHT} mm  (1 rev)")
print(f"  Mesh        : {N_MESH_REVS} revolutions, z1[0]={float(z1[0]):.3f} mm")
print(f"  Top ring    : {z1_end:.1f}→{TOTAL_HEIGHT} mm")
print(f"  Total path  : one continuous stroke ({len(x_all):,} pts)")
print()
print("Touching condition check:")
theta_check = np.linspace(0, 2*np.pi, 9, endpoint=False)
for th in theta_check[:4]:
    t_c = t_pre_s + th
    zb  = (RING_HEIGHT + Z_AMP - LAYER_HEIGHT) + th/(2*np.pi) * LAYER_HEIGHT
    peak_0 = zb + Z_AMP   # 0th pre-rev peak (unclipped)
    t_m  = t1_s + th
    zb_m = z_base_s
    val_1 = zb_m - Z_AMP  # mesh 1st rev valley (1st valley, sin=-1 at same phase)
    print(f"  θ={np.degrees(th):5.1f}°: 0th peak={peak_0:.3f}mm,  mesh valley≈{val_1:.3f}mm")
