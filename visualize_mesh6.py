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
PHASE = -np.pi / 2   # sin(9.5·4π − π/2) = −1 → mesh starts at valley

# ==================================================
# 1. Bottom ring  (t: 0→2π, constant Z = RING_HEIGHT)
# ==================================================
t0 = np.linspace(0, 2*np.pi, 3000)
x0, y0 = R*np.cos(t0), R*np.sin(t0)
z0 = np.full_like(t0, RING_HEIGHT)

# ==================================================
# 2. 0th pre-revolution  (t: 2π→4π)
#    z_base: −1.8 → 4.2 mm  (= RING_HEIGHT+Z_AMP−LAYER_HEIGHT → RING_HEIGHT+Z_AMP)
#    clip from BELOW at RING_HEIGHT  → arches grow from nothing to full height
# ==================================================
t_pre_s, t_pre_e = 2*np.pi, 4*np.pi
t_pre = np.linspace(t_pre_s, t_pre_e, 6000)
z_base_pre = (RING_HEIGHT + Z_AMP - LAYER_HEIGHT) + (t_pre - t_pre_s)/(2*np.pi) * LAYER_HEIGHT
z_pre = np.maximum(RING_HEIGHT, z_base_pre + Z_AMP * np.sin(N_OSC_PER_REV * t_pre + PHASE))
x_pre, y_pre = R*np.cos(t_pre), R*np.sin(t_pre)

# ==================================================
# 3. Mesh  (t: 4π → 4π + N_MESH_REVS·2π = 18π)
# ==================================================
t1_s = 4*np.pi
t1_e = t1_s + 2*np.pi * N_MESH_REVS
t1   = np.linspace(t1_s, t1_e, 25000)
z_base_s = RING_HEIGHT + Z_AMP          # 4.2 mm
z_range  = N_MESH_REVS * LAYER_HEIGHT   # 42 mm
z_base1  = z_base_s + (t1 - t1_s)/(t1_e - t1_s) * z_range
z1       = z_base1 + Z_AMP * np.sin(N_OSC_PER_REV * t1 + PHASE)
x1, y1  = R*np.cos(t1), R*np.sin(t1)

z_base_end = float(z_base_s + z_range)  # = 46.2 mm
z1_end     = float(z1[-1])              # ≈ 49.2 mm  (peak at t=18π)

# ==================================================
# 4. Top pre-revolution  (t: 18π→20π)
#    z_base: 46.2 → 52.2 mm  (= z_base_end → z_base_end + LAYER_HEIGHT)
#    clip from ABOVE at TOTAL_HEIGHT → arches shrink from full height to nothing
#    Mirror of 0th pre-rev:
#      top pre-rev valley at θ  =  z_base_end + θ/(2π)·LAYER_HEIGHT − Z_AMP
#      mesh last-rev peak at θ  =  z_base_end + θ/(2π)·LAYER_HEIGHT − Z_AMP  ← same!
#      → top pre-rev valleys sit exactly on the last mesh revolution's peaks ✓
# ==================================================
t_tpre_s = t1_e
t_tpre_e = t1_e + 2*np.pi
t_tpre   = np.linspace(t_tpre_s, t_tpre_e, 6000)
z_base_tpre = z_base_end + (t_tpre - t_tpre_s)/(2*np.pi) * LAYER_HEIGHT
z_tpre_raw  = z_base_tpre + Z_AMP * np.sin(N_OSC_PER_REV * t_tpre + PHASE)
z_tpre      = np.minimum(TOTAL_HEIGHT, z_tpre_raw)   # clip from ABOVE
x_tpre, y_tpre = R*np.cos(t_tpre), R*np.sin(t_tpre)

z_tpre_end = float(z_tpre[-1])   # ≈ 49.2 mm (last valley, unclipped)

# ==================================================
# 5. Short ramp  (valley 49.2 mm → top ring 50.0 mm, ¼ revolution)
# ==================================================
t_ramp_s = t_tpre_e
t_ramp_e = t_ramp_s + np.pi / 2
t_ramp   = np.linspace(t_ramp_s, t_ramp_e, 500)
z_ramp   = np.linspace(z_tpre_end, TOTAL_HEIGHT, 500)
x_ramp, y_ramp = R*np.cos(t_ramp), R*np.sin(t_ramp)

# ==================================================
# 6. Top ring  (flat at TOTAL_HEIGHT = 50 mm, 1 revolution)
# ==================================================
t2_s = t_ramp_e
t2_e = t2_s + 2*np.pi
t2   = np.linspace(t2_s, t2_e, 3000)
x2, y2 = R*np.cos(t2), R*np.sin(t2)
z2     = np.full_like(t2, TOTAL_HEIGHT)

# Combine into one continuous path
x_all = np.concatenate([x0, x_pre, x1, x_tpre, x_ramp, x2])
y_all = np.concatenate([y0, y_pre, y1, y_tpre, y_ramp, y2])
z_all = np.concatenate([z0, z_pre, z1, z_tpre, z_ramp, z2])
t_all = np.concatenate([t0, t_pre, t1, t_tpre, t_ramp, t2])

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
ax3.plot_surface(R*np.cos(Th), R*np.sin(Th), Zc, alpha=0.05, color='gray', linewidth=0)

ax3.plot(x0,     y0,     z0,     color='orangered',   lw=3.0, zorder=5, label='Bottom ring (Z=1.2mm flat)')
ax3.plot(x_pre,  y_pre,  z_pre,  color='limegreen',   lw=2.0, zorder=4, label='0th pre-rev (clip from below)')
sc = ax3.scatter(x1, y1, z1, c=z1, cmap='plasma', s=0.2, alpha=0.9)
ax3.plot(x_tpre, y_tpre, z_tpre, color='gold',        lw=2.0, zorder=4, label='Top pre-rev (clip from above)')
ax3.plot(x2,     y2,     z2,     color='deepskyblue', lw=3.0, zorder=5, label='Top ring (Z=50mm flat)')

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

ax2.fill_between([0, circ], -0.5, 0, color='#aaa', alpha=0.35, label='Build plate (Z=0)')

# Bottom ring
ax2.axhline(RING_HEIGHT,   color='orangered',   lw=2.5, alpha=0.9,
            label=f'Bottom ring (Z={RING_HEIGHT}mm)')

# 0th pre-rev
arc_pre = (t_pre % (2*np.pi)) * R
z_pre_raw = z_base_pre + Z_AMP * np.sin(N_OSC_PER_REV * t_pre + PHASE)
ax2.plot(arc_pre, z_pre,     color='limegreen', lw=1.8, alpha=0.9, label='0th pre-rev')
ax2.plot(arc_pre, z_pre_raw, color='limegreen', lw=0.7, ls='--', alpha=0.3)

# Mesh
cmap = plt.cm.plasma
for rev in range(N_MESH_REVS + 1):
    mask = (t1 >= t1_s + rev*2*np.pi) & (t1 < t1_s + (rev+1)*2*np.pi)
    if not mask.any():
        continue
    col = cmap(rev / (N_MESH_REVS + 1))
    ax2.plot((t1[mask] % (2*np.pi)) * R, z1[mask], color=col, lw=1.1, alpha=0.85)

# Top pre-rev
arc_tpre = (t_tpre % (2*np.pi)) * R
ax2.plot(arc_tpre, z_tpre,     color='gold', lw=1.8, alpha=0.9, label='Top pre-rev')
ax2.plot(arc_tpre, z_tpre_raw, color='gold', lw=0.7, ls='--', alpha=0.3)

# Top ring
ax2.axhline(TOTAL_HEIGHT, color='deepskyblue', lw=2.5, alpha=0.9,
            label=f'Top ring (Z={TOTAL_HEIGHT}mm)')

ax2.set_xlim(0, circ)
ax2.set_ylim(-1, TOTAL_HEIGHT + 1)
ax2.set_xlabel('Circumferential arc length (mm)', fontsize=9)
ax2.set_ylabel('Z (mm)', fontsize=9)
ax2.set_title('Unwrapped cylinder\n'
              'solid=clipped path, dashed=ghost (unclipped)', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=7.5, loc='center right')

plt.tight_layout()
plt.savefig('mesh_structure6.png', dpi=150, bbox_inches='tight')

print("Saved: mesh_structure6.png")
print(f"  Bottom ring   : Z = {RING_HEIGHT} mm flat")
print(f"  0th pre-rev   : z_base {RING_HEIGHT+Z_AMP-LAYER_HEIGHT:.1f}→{RING_HEIGHT+Z_AMP:.1f} mm, clip≥{RING_HEIGHT}")
print(f"  Mesh          : {N_MESH_REVS} revs, Z {float(z1[0]):.2f}→{z1_end:.2f} mm")
print(f"  Top pre-rev   : z_base {z_base_end:.1f}→{z_base_end+LAYER_HEIGHT:.1f} mm, clip≤{TOTAL_HEIGHT}")
print(f"  Top ring      : Z = {TOTAL_HEIGHT} mm flat")
print(f"  Total         : one continuous stroke ({len(x_all):,} pts)")
print()
print("Symmetry check (top pre-rev valley = mesh last-rev peak at same angle θ):")
for deg in [0, 45, 90, 135]:
    th = np.radians(deg)
    peak_mesh  = z_base_end + th/(2*np.pi)*LAYER_HEIGHT - Z_AMP  # last mesh rev: wrong sign
    valley_top = z_base_end + th/(2*np.pi)*LAYER_HEIGHT - Z_AMP
    print(f"  θ={deg:3d}°:  mesh peak ≈ {z_base_end + th/(2*np.pi)*LAYER_HEIGHT + Z_AMP:.2f} mm"
          f"   top-pre valley = {valley_top:.2f} mm")
