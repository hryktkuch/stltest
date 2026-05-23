import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ---- Parameters ----
NOZZLE_DIA    = 1.8
CIRCLE_DIA    = 50.0
TOTAL_HEIGHT  = 50.0
RING_HEIGHT   = 1.2    # top/bottom ring layer height (nozzle at constant Z)
LAYER_HEIGHT  = 6.0    # Z advance per mesh revolution
N_OSC_PER_REV = 9.5   # half-integer → phase inverts each revolution → touching
Z_AMP         = LAYER_HEIGHT / 2   # = 3.0 mm
N_MESH_REVS   = 7
# --------------------

R = CIRCLE_DIA / 2

# Phase: sin(9.5 * 2π + π/2) = sin(19π + π/2) = -1  → mesh starts at valley (Z = RING_HEIGHT)
PHASE = np.pi / 2

# ==================================================
# 1. Bottom ring  — flat horizontal circle at Z = RING_HEIGHT
#    (nozzle moves at constant height 1.2 mm, 1 revolution)
# ==================================================
t0 = np.linspace(0, 2 * np.pi, 3000)
x0 = R * np.cos(t0)
y0 = R * np.sin(t0)
z0 = np.full_like(t0, RING_HEIGHT)           # ← CONSTANT Z = 1.2 mm

# ==================================================
# 2. Mesh section
#    z_base: RING_HEIGHT + Z_AMP → (same + N_MESH_REVS × LAYER_HEIGHT)
#    first valley = z_base_start − Z_AMP = RING_HEIGHT   ← touches top of bottom ring
# ==================================================
t1_s = 2 * np.pi
t1_e = t1_s + 2 * np.pi * N_MESH_REVS
t1   = np.linspace(t1_s, t1_e, 25000)

z_base_s = RING_HEIGHT + Z_AMP              # 4.2 mm
z_range  = N_MESH_REVS * LAYER_HEIGHT       # 42 mm
z_base1  = z_base_s + (t1 - t1_s) / (t1_e - t1_s) * z_range
z1       = z_base1 + Z_AMP * np.sin(N_OSC_PER_REV * t1 + PHASE)
# z1[0] = 4.2 + 3*sin(19π + π/2) = 4.2 + 3*(-1) = 1.2 mm ✓

x1 = R * np.cos(t1)
y1 = R * np.sin(t1)
z1_end = float(z1[-1])   # ≈ 49.2 mm (last oscillation peak)

# ==================================================
# 3. Top ring  — gradual ramp from z1_end to TOTAL_HEIGHT (≈ 0.8 mm rise)
#    (nozzle at near-constant height, 1 revolution)
# ==================================================
t2_s = t1_e
t2   = np.linspace(t2_s, t2_s + 2 * np.pi, 3000)
x2   = R * np.cos(t2)
y2   = R * np.sin(t2)
z2   = np.linspace(z1_end, TOTAL_HEIGHT, 3000)   # flatten to top

# Combine
x_all = np.concatenate([x0, x1, x2])
y_all = np.concatenate([y0, y1, y2])
z_all = np.concatenate([z0, z1, z2])
t_all = np.concatenate([t0, t1, t2])

# ==================================================
# Mesh node positions (valleys & peaks of mesh oscillation)
# ==================================================
def osc_nodes(t_arr, z_arr, t_s, t_e, n_osc, phase):
    nodes = []
    for k in range(int(n_osc * N_MESH_REVS) + 4):
        for target in [1, -1]:  # peak / valley
            tp = (np.arcsin(target) - phase + k * 2 * np.pi) / n_osc
            if t_s <= tp <= t_e:
                idx = int((tp - t_s) / (t_e - t_s) * (len(t_arr) - 1))
                nodes.append(((tp % (2 * np.pi)) * R, z_arr[idx]))
        # negative arcsin branch
        for target in [1, -1]:
            tp = (np.pi - np.arcsin(target) - phase + k * 2 * np.pi) / n_osc
            if t_s <= tp <= t_e:
                idx = int((tp - t_s) / (t_e - t_s) * (len(t_arr) - 1))
                nodes.append(((tp % (2 * np.pi)) * R, z_arr[idx]))
    return zip(*nodes) if nodes else ([], [])

node_arc, node_z = osc_nodes(t1, z1, t1_s, t1_e, N_OSC_PER_REV, PHASE)
node_arc, node_z = list(node_arc), list(node_z)

# ==================================================
# Figure
# ==================================================
fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor('#f8f8f8')

# ---- 3D view ----
ax3 = fig.add_subplot(1, 2, 1, projection='3d')
ax3.set_facecolor('#f0f0f0')

# Cylinder reference
theta_c = np.linspace(0, 2 * np.pi, 120)
z_c     = np.linspace(0, TOTAL_HEIGHT, 40)
Th, Zc  = np.meshgrid(theta_c, z_c)
ax3.plot_surface(R * np.cos(Th), R * np.sin(Th), Zc,
                 alpha=0.05, color='gray', linewidth=0)

# Bottom ring (flat horizontal circle)
ax3.plot(x0, y0, z0, color='orangered', lw=3.0, zorder=5, label=f'Bottom ring (Z={RING_HEIGHT}mm flat)')

# Mesh
sc = ax3.scatter(x1, y1, z1, c=z1, cmap='plasma', s=0.2, alpha=0.9)

# Top ring
ax3.plot(x2, y2, z2, color='deepskyblue', lw=3.0, zorder=5, label=f'Top ring (~{z1_end:.1f}→{TOTAL_HEIGHT}mm)')

fig.colorbar(sc, ax=ax3, shrink=0.5, pad=0.02, label='Z (mm)')
ax3.set_xlabel('X (mm)', labelpad=6)
ax3.set_ylabel('Y (mm)', labelpad=6)
ax3.set_zlabel('Z (mm)', labelpad=6)
ax3.set_zlim(0, TOTAL_HEIGHT)
ax3.view_init(elev=22, azim=-55)
ax3.legend(fontsize=8, loc='upper left')
ax3.set_title(
    f'One-stroke mesh tube\n'
    f'φ{CIRCLE_DIA}mm × H{TOTAL_HEIGHT}mm  |  ring {RING_HEIGHT}mm flat  |  '
    f'{N_OSC_PER_REV} osc/rev  |  layer {LAYER_HEIGHT}mm',
    fontsize=10)

# ---- Unwrapped view ----
ax2 = fig.add_subplot(1, 2, 2)
ax2.set_facecolor('#f0f0f0')

circ = 2 * np.pi * R

# Build plate (Z = 0)
ax2.axhspan(0, 0, color='k', lw=0)
ax2.fill_between([0, circ], -0.5, 0, color='#aaa', alpha=0.35, label='Build plate (Z=0)')

# Bottom ring: horizontal line at Z = RING_HEIGHT
ax2.axhline(RING_HEIGHT, color='orangered', lw=2.5, alpha=0.9, label=f'Bottom ring (Z={RING_HEIGHT}mm)')

# Mesh
cmap = plt.cm.plasma
for rev in range(N_MESH_REVS + 1):
    mask = (t1 >= t1_s + rev * 2 * np.pi) & (t1 < t1_s + (rev + 1) * 2 * np.pi)
    if not mask.any():
        continue
    col = cmap(rev / (N_MESH_REVS + 1))
    ax2.plot((t1[mask] % (2 * np.pi)) * R, z1[mask], color=col, lw=1.1, alpha=0.85)

# Top ring
ax2.plot((t2 % (2 * np.pi)) * R, z2,
         color='deepskyblue', lw=2.5, alpha=0.9, label=f'Top ring (~{z1_end:.1f}mm)')

# Mesh nodes
if node_arc:
    ax2.scatter(node_arc, node_z, c='black', s=14, zorder=5, alpha=0.5, label='Mesh nodes')

ax2.axhline(TOTAL_HEIGHT, color='deepskyblue', lw=1.0, ls='--', alpha=0.5)
ax2.set_xlim(0, circ)
ax2.set_ylim(-0.8, TOTAL_HEIGHT + 1)
ax2.set_xlabel('Circumferential arc length (mm)', fontsize=9)
ax2.set_ylabel('Z (mm)', fontsize=9)
ax2.set_title('Unwrapped cylinder\n(each colour = 1 revolution, dots = mesh nodes)', fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=8, loc='upper right')

# Annotate first valley
ax2.annotate('Mesh valley\ntouches bottom ring\n(Z=1.2mm)',
             xy=(0, RING_HEIGHT), xytext=(15, 4),
             arrowprops=dict(arrowstyle='->', color='orangered'),
             fontsize=7.5, color='orangered')

plt.tight_layout()
plt.savefig('mesh_structure4.png', dpi=150, bbox_inches='tight')

print("Saved: mesh_structure4.png")
print(f"  Bottom ring : Z = {RING_HEIGHT} mm flat  (1 revolution)")
print(f"  Mesh start  : first valley = {float(z1[0]):.3f} mm  (= RING_HEIGHT ✓)")
print(f"  Mesh        : {N_MESH_REVS} revolutions, {N_OSC_PER_REV} osc/rev, "
      f"Z_AMP = ±{Z_AMP} mm")
print(f"  Mesh end    : Z = {z1_end:.2f} mm")
print(f"  Top ring    : Z {z1_end:.1f} → {TOTAL_HEIGHT} mm  ({TOTAL_HEIGHT-z1_end:.1f} mm rise)")
print(f"  Total       : one continuous stroke ({len(x_all):,} pts)")
