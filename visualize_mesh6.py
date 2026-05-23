import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ---- Parameters ----
NOZZLE_DIA    = 1.8
CIRCLE_DIA    = 50.0
TOTAL_HEIGHT  = 50.0
RING_HEIGHT   = 1.2
LAYER_HEIGHT  = 4.5
N_OSC_PER_REV = 9.5
OVERLAP       = 1.0    # mm  inter-layer overlap
Z_AMP         = (LAYER_HEIGHT + OVERLAP) / 2   # = 2.75 mm
# --------------------

R = CIRCLE_DIA / 2
PHASE = -np.pi / 2

# Auto-calculate N_MESH_REVS so mesh z_base spans RING_HEIGHT+Z_AMP → TOTAL_HEIGHT-Z_AMP
z_base_s         = RING_HEIGHT + Z_AMP                          # 3.95 mm
z_base_tpre_start = TOTAL_HEIGHT - Z_AMP                        # 47.25 mm
z_mesh_needed    = z_base_tpre_start - z_base_s                 # 43.30 mm
N_MESH_REVS      = int(z_mesh_needed / LAYER_HEIGHT)            # 9
z_range          = N_MESH_REVS * LAYER_HEIGHT                   # 40.50 mm
z_base_end       = z_base_s + z_range                           # 44.45 mm
# Gap between mesh end and top pre-rev start
t_gap            = (z_base_tpre_start - z_base_end) / LAYER_HEIGHT * 2 * np.pi  # ~3.91 rad

# ==================================================
# 1. Bottom ring
# ==================================================
t0 = np.linspace(0, 2*np.pi, 3000)
x0, y0 = R*np.cos(t0), R*np.sin(t0)
z0 = np.full_like(t0, RING_HEIGHT)

# ==================================================
# 2. 0th pre-revolution  (t: 2π→4π)
#    FIXED: z_base from RING_HEIGHT-Z_AMP to RING_HEIGHT+Z_AMP (range = 2×Z_AMP)
#    → at start: peak = RING_HEIGHT (just at clip level, no arch)
#    → at end:   valley = RING_HEIGHT (connects to mesh start)
# ==================================================
t_pre_s, t_pre_e = 2*np.pi, 4*np.pi
t_pre = np.linspace(t_pre_s, t_pre_e, 6000)
z_base_pre = (RING_HEIGHT - Z_AMP) + (t_pre - t_pre_s)/(2*np.pi) * 2 * Z_AMP
z_pre_raw  = z_base_pre + Z_AMP * np.sin(N_OSC_PER_REV * t_pre + PHASE)
z_pre      = np.maximum(RING_HEIGHT, z_pre_raw)
x_pre, y_pre = R*np.cos(t_pre), R*np.sin(t_pre)

# ==================================================
# 3. Mesh
# ==================================================
t1_s = 4*np.pi
t1_e = t1_s + 2*np.pi * N_MESH_REVS
t1   = np.linspace(t1_s, t1_e, 25000)
z_base1 = z_base_s + (t1 - t1_s)/(t1_e - t1_s) * z_range
z1      = z_base1 + Z_AMP * np.sin(N_OSC_PER_REV * t1 + PHASE)
x1, y1  = R*np.cos(t1), R*np.sin(t1)
z1_end  = float(z1[-1])

# ==================================================
# 4. Transition  (bridge gap: z_base_end → TOTAL_HEIGHT-Z_AMP)
#    Continues mesh oscillation, no clipping needed
# ==================================================
t_trans_s = t1_e
t_trans_e = t1_e + t_gap
n_trans   = max(10, int(t_gap / (2*np.pi) * 2000))
t_trans   = np.linspace(t_trans_s, t_trans_e, n_trans)
z_base_trans = z_base_end + (t_trans - t_trans_s) / t_gap * (z_base_tpre_start - z_base_end)
z_trans      = z_base_trans + Z_AMP * np.sin(N_OSC_PER_REV * t_trans + PHASE)
x_trans, y_trans = R*np.cos(t_trans), R*np.sin(t_trans)

# ==================================================
# 5. Top pre-revolution
#    FIXED: z_base from TOTAL_HEIGHT-Z_AMP to TOTAL_HEIGHT+Z_AMP (range = 2×Z_AMP)
#    → at start: peak = TOTAL_HEIGHT (just at clip level)
#    → at end:   valley = TOTAL_HEIGHT (connects to top ring) — always clipped ✓
# ==================================================
t_tpre_s = t_trans_e
t_tpre_e = t_tpre_s + 2*np.pi
t_tpre   = np.linspace(t_tpre_s, t_tpre_e, 6000)
z_base_tpre = z_base_tpre_start + (t_tpre - t_tpre_s)/(2*np.pi) * 2 * Z_AMP
z_tpre_raw  = z_base_tpre + Z_AMP * np.sin(N_OSC_PER_REV * t_tpre + PHASE)
z_tpre      = np.minimum(TOTAL_HEIGHT, z_tpre_raw)
x_tpre, y_tpre = R*np.cos(t_tpre), R*np.sin(t_tpre)

# ==================================================
# 6. Top ring
# ==================================================
t2_s = t_tpre_e
t2_e = t2_s + 2*np.pi
t2   = np.linspace(t2_s, t2_e, 3000)
x2, y2 = R*np.cos(t2), R*np.sin(t2)
z2     = np.full_like(t2, TOTAL_HEIGHT)

# Combine
x_all = np.concatenate([x0, x_pre, x1, x_trans, x_tpre, x2])
y_all = np.concatenate([y0, y_pre, y1, y_trans, y_tpre, y2])
z_all = np.concatenate([z0, z_pre, z1, z_trans, z_tpre, z2])
t_all = np.concatenate([t0, t_pre, t1, t_trans, t_tpre, t2])

# ==================================================
# Figure
# ==================================================
fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor('#f8f8f8')

ax3 = fig.add_subplot(1, 2, 1, projection='3d')
ax3.set_facecolor('#f0f0f0')

theta_c = np.linspace(0, 2*np.pi, 120)
z_c     = np.linspace(0, TOTAL_HEIGHT, 40)
Th, Zc  = np.meshgrid(theta_c, z_c)
ax3.plot_surface(R*np.cos(Th), R*np.sin(Th), Zc, alpha=0.05, color='gray', linewidth=0)

ax3.plot(x0,     y0,     z0,     color='orangered',   lw=3.0, zorder=5, label='Bottom ring')
ax3.plot(x_pre,  y_pre,  z_pre,  color='limegreen',   lw=2.0, zorder=4, label='0th pre-rev')
sc = ax3.scatter(x1, y1, z1, c=z1, cmap='plasma', s=0.2, alpha=0.9)
ax3.plot(x_trans, y_trans, z_trans, color='cyan',     lw=1.5, zorder=4, label='Transition')
ax3.plot(x_tpre, y_tpre, z_tpre, color='gold',        lw=2.0, zorder=4, label='Top pre-rev')
ax3.plot(x2,     y2,     z2,     color='deepskyblue', lw=3.0, zorder=5, label='Top ring')

fig.colorbar(sc, ax=ax3, shrink=0.5, pad=0.02, label='Z (mm)')
ax3.set_xlabel('X (mm)', labelpad=6)
ax3.set_ylabel('Y (mm)', labelpad=6)
ax3.set_zlabel('Z (mm)', labelpad=6)
ax3.set_zlim(0, TOTAL_HEIGHT)
ax3.view_init(elev=22, azim=-55)
ax3.legend(fontsize=8, loc='upper left')
ax3.set_title(
    f'One-stroke mesh tube  (φ{CIRCLE_DIA}mm × H{TOTAL_HEIGHT}mm)\n'
    f'ring {RING_HEIGHT}mm | layer {LAYER_HEIGHT}mm | {N_OSC_PER_REV} osc/rev | OVERLAP {OVERLAP}mm',
    fontsize=10)

ax2 = fig.add_subplot(1, 2, 2)
ax2.set_facecolor('#f0f0f0')
circ = 2*np.pi*R

ax2.fill_between([0, circ], -0.5, 0, color='#aaa', alpha=0.35, label='Build plate')
ax2.axhline(RING_HEIGHT, color='orangered', lw=2.5, alpha=0.9,
            label=f'Bottom ring (Z={RING_HEIGHT}mm)')

arc_pre = (t_pre % (2*np.pi)) * R
ax2.plot(arc_pre, z_pre,     color='limegreen', lw=1.8, alpha=0.9, label='0th pre-rev')
ax2.plot(arc_pre, z_pre_raw, color='limegreen', lw=0.7, ls='--', alpha=0.3)

cmap = plt.cm.plasma
for rev in range(N_MESH_REVS + 1):
    mask = (t1 >= t1_s + rev*2*np.pi) & (t1 < t1_s + (rev+1)*2*np.pi)
    if not mask.any():
        continue
    col = cmap(rev / (N_MESH_REVS + 1))
    ax2.plot((t1[mask] % (2*np.pi)) * R, z1[mask], color=col, lw=1.1, alpha=0.85)

arc_trans = (t_trans % (2*np.pi)) * R
ax2.plot(arc_trans, z_trans, color='cyan', lw=1.5, alpha=0.9, label='Transition')

arc_tpre = (t_tpre % (2*np.pi)) * R
ax2.plot(arc_tpre, z_tpre,     color='gold', lw=1.8, alpha=0.9, label='Top pre-rev')
ax2.plot(arc_tpre, z_tpre_raw, color='gold', lw=0.7, ls='--', alpha=0.3)

ax2.axhline(TOTAL_HEIGHT, color='deepskyblue', lw=2.5, alpha=0.9,
            label=f'Top ring (Z={TOTAL_HEIGHT}mm)')

ax2.set_xlim(0, circ)
ax2.set_ylim(-1, TOTAL_HEIGHT + 1)
ax2.set_xlabel('Circumferential arc length (mm)', fontsize=9)
ax2.set_ylabel('Z (mm)', fontsize=9)
ax2.set_title('Unwrapped cylinder\nsolid=clipped, dashed=ghost (unclipped)', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=7.5, loc='center right')

plt.tight_layout()
plt.savefig('mesh_structure6.png', dpi=150, bbox_inches='tight')

print("Saved: mesh_structure6.png")
print(f"  Z_AMP         : {Z_AMP:.3f} mm  (LAYER_HEIGHT={LAYER_HEIGHT} + OVERLAP={OVERLAP}) / 2")
print(f"  N_MESH_REVS   : {N_MESH_REVS}  (auto)")
print(f"  Bottom ring   : Z = {RING_HEIGHT} mm flat")
print(f"  0th pre-rev   : z_base {RING_HEIGHT-Z_AMP:.2f}→{RING_HEIGHT+Z_AMP:.2f} mm (range=2×Z_AMP={2*Z_AMP:.2f}), clip≥{RING_HEIGHT}")
print(f"  Mesh          : {N_MESH_REVS} revs, z_base {z_base_s:.2f}→{z_base_end:.2f} mm")
print(f"  Transition    : z_base {z_base_end:.2f}→{z_base_tpre_start:.2f} mm ({t_gap/np.pi*0.5:.3f} rev)")
print(f"  Top pre-rev   : z_base {z_base_tpre_start:.2f}→{TOTAL_HEIGHT+Z_AMP:.2f} mm (range=2×Z_AMP={2*Z_AMP:.2f}), clip≤{TOTAL_HEIGHT}")
print(f"  Top ring      : Z = {TOTAL_HEIGHT} mm flat")
print(f"  Total         : one continuous stroke ({len(x_all):,} pts)")
