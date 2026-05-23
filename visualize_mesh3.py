import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ---- Parameters ----
NOZZLE_DIA    = 1.8
CIRCLE_DIA    = 50.0
TOTAL_HEIGHT  = 50.0
RING_HEIGHT   = 1.2    # top/bottom solid ring thickness
LAYER_HEIGHT  = 6.0    # Z advance per mesh revolution
N_OSC_PER_REV = 9.5   # half-integer → phase inverts each revolution
Z_AMP         = LAYER_HEIGHT / 2   # = 3.0 mm (adjacent loops exactly touch)
N_MESH_REVS   = 7     # 7 × 9.5 = 66.5 half-cycles → starts valley, ends peak
# --------------------

R = CIRCLE_DIA / 2

# Phase offset: sin(9.5 * 2π + π/2) = sin(19π + π/2) = sin(3π/2) = -1 → valley at mesh start
PHASE = np.pi / 2

# ==================================================
# 1. Bottom ring  (1 revolution: Z 0 → RING_HEIGHT)
# ==================================================
t0 = np.linspace(0, 2 * np.pi, 2000)
x0 = R * np.cos(t0)
y0 = R * np.sin(t0)
z0 = np.linspace(0, RING_HEIGHT, 2000)

# ==================================================
# 2. Mesh section  (N_MESH_REVS revolutions)
#    z_base: (RING_HEIGHT + Z_AMP) → (RING_HEIGHT + Z_AMP + N_MESH_REVS * LAYER_HEIGHT)
#    valley at start = RING_HEIGHT (touches top of bottom ring)
#    peak  at end   ≈ RING_HEIGHT + (N_MESH_REVS+1) * LAYER_HEIGHT - Z_AMP
# ==================================================
t1_s = 2 * np.pi                            # continues from bottom ring
t1_e = t1_s + 2 * np.pi * N_MESH_REVS
t1   = np.linspace(t1_s, t1_e, 25000)

z_base_s = RING_HEIGHT + Z_AMP             # 4.2 mm
z_range   = N_MESH_REVS * LAYER_HEIGHT     # 42 mm
z_base1   = z_base_s + (t1 - t1_s) / (t1_e - t1_s) * z_range
z1        = z_base1 + Z_AMP * np.sin(N_OSC_PER_REV * t1 + PHASE)

x1 = R * np.cos(t1)
y1 = R * np.sin(t1)

z1_end = float(z1[-1])   # ≈ 49.2 mm (peak of last oscillation)

# ==================================================
# 3. Top ring  (1 revolution: Z z1_end → TOTAL_HEIGHT)
# ==================================================
t2_s = t1_e
t2   = np.linspace(t2_s, t2_s + 2 * np.pi, 2000)
x2   = R * np.cos(t2)
y2   = R * np.sin(t2)
z2   = np.linspace(z1_end, TOTAL_HEIGHT, 2000)

# ==================================================
# Combine into single continuous path
# ==================================================
x_all = np.concatenate([x0, x1, x2])
y_all = np.concatenate([y0, y1, y2])
z_all = np.concatenate([z0, z1, z2])
t_all = np.concatenate([t0, t1, t2])

# ==================================================
# Mesh node positions (peaks & valleys of oscillation)
# ==================================================
node_arc, node_z = [], []
for k in range(int(N_OSC_PER_REV * N_MESH_REVS) + 2):
    for sign, label in [(1, 'peak'), (-1, 'valley')]:
        # sin(N*t + PHASE) = sign → N*t + PHASE = arcsin(sign) = ±π/2
        tp = (sign * np.pi / 2 - PHASE + k * 2 * np.pi) / N_OSC_PER_REV
        if t1_s <= tp <= t1_e:
            idx = int((tp - t1_s) / (t1_e - t1_s) * (len(t1) - 1))
            node_arc.append((tp % (2 * np.pi)) * R)
            node_z.append(z1[idx])

# ==================================================
# Figure
# ==================================================
fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor('#f8f8f8')

# ---- 3D view ----
ax3 = fig.add_subplot(1, 2, 1, projection='3d')
ax3.set_facecolor('#f0f0f0')

theta_c = np.linspace(0, 2 * np.pi, 120)
z_c     = np.linspace(0, TOTAL_HEIGHT, 40)
Th, Zc  = np.meshgrid(theta_c, z_c)
ax3.plot_surface(R * np.cos(Th), R * np.sin(Th), Zc,
                 alpha=0.05, color='gray', linewidth=0)

ax3.plot(x0, y0, z0, color='orangered', lw=2.8, zorder=5, label='Bottom ring')
sc = ax3.scatter(x1, y1, z1, c=z1, cmap='plasma', s=0.2, alpha=0.9)
ax3.plot(x2, y2, z2, color='orangered', lw=2.8, zorder=5, label='Top ring')

fig.colorbar(sc, ax=ax3, shrink=0.5, pad=0.02, label='Z (mm)')
ax3.set_xlabel('X (mm)', labelpad=6)
ax3.set_ylabel('Y (mm)', labelpad=6)
ax3.set_zlabel('Z (mm)', labelpad=6)
ax3.set_zlim(0, TOTAL_HEIGHT)
ax3.view_init(elev=22, azim=-55)
ax3.legend(fontsize=9)
ax3.set_title(
    f'One-stroke mesh tube\n'
    f'φ{CIRCLE_DIA}mm × H{TOTAL_HEIGHT}mm  |  ring {RING_HEIGHT}mm  |  '
    f'layer {LAYER_HEIGHT}mm  |  {N_OSC_PER_REV} osc/rev',
    fontsize=10)

# ---- Unwrapped view ----
ax2 = fig.add_subplot(1, 2, 2)
ax2.set_facecolor('#f0f0f0')

circ = 2 * np.pi * R   # circumference ≈ 157 mm

# Bottom ring
ax2.plot((t0 % (2 * np.pi)) * R, z0,
         color='orangered', lw=2.5, alpha=0.95, label='Bottom ring')

# Mesh (colour by revolution)
cmap = plt.cm.plasma
for rev in range(N_MESH_REVS + 1):
    mask = (t1 >= t1_s + rev * 2 * np.pi) & (t1 < t1_s + (rev + 1) * 2 * np.pi)
    if not mask.any():
        continue
    col = cmap(rev / (N_MESH_REVS + 1))
    ax2.plot((t1[mask] % (2 * np.pi)) * R, z1[mask], color=col, lw=1.1, alpha=0.85)

# Top ring
ax2.plot((t2 % (2 * np.pi)) * R, z2,
         color='orangered', lw=2.5, alpha=0.95, label='Top ring')

# Mesh nodes
ax2.scatter(node_arc, node_z, c='black', s=10, zorder=5,
            alpha=0.55, label='Mesh nodes')

# Ring boundary lines
ax2.axhline(RING_HEIGHT, color='orangered', lw=0.8, ls='--', alpha=0.5)
ax2.axhline(z1_end,      color='orangered', lw=0.8, ls='--', alpha=0.5,
            label=f'Ring boundaries ({RING_HEIGHT}mm / {z1_end:.1f}mm)')

ax2.set_xlim(0, circ)
ax2.set_ylim(-1, TOTAL_HEIGHT + 1)
ax2.set_xlabel('Circumferential arc length (mm)', fontsize=9)
ax2.set_ylabel('Z (mm)', fontsize=9)
ax2.set_title('Unwrapped cylinder\n(each colour = 1 revolution, dots = mesh nodes)', fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=8, loc='upper right')

plt.tight_layout()
plt.savefig('mesh_structure3.png', dpi=150, bbox_inches='tight')

print("Saved: mesh_structure3.png")
print(f"  Bottom ring : Z  0.0 → {RING_HEIGHT} mm  (1 revolution)")
print(f"  Mesh        : Z {RING_HEIGHT} ↔ {z1_end:.1f} mm  ({N_MESH_REVS} revolutions, "
      f"{N_OSC_PER_REV} osc/rev)")
print(f"  Top ring    : Z {z1_end:.1f} → {TOTAL_HEIGHT} mm  (1 revolution)")
print(f"  Mesh nodes  : {len(node_arc)}")
print(f"  Total path  : one continuous stroke ({len(x_all):,} points)")
