import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ---- Parameters ----
NOZZLE_DIA    = 1.8    # mm
CIRCLE_DIA    = 50.0   # mm
TOTAL_HEIGHT  = 50.0   # mm
LAYER_HEIGHT  = 6.0    # mm  (Z advance per revolution)
N_OSC_PER_REV = 9.5   # oscillations per revolution (half-integer → diamond mesh)
# --------------------

R      = CIRCLE_DIA / 2
Z_AMP  = LAYER_HEIGHT / 2          # = 3 mm: adjacent loops exactly touch
n_revs = TOTAL_HEIGHT / LAYER_HEIGHT  # ≈ 8.3 revolutions

# Continuous parameter t = cumulative angle (0 … 2π × n_revs)
t = np.linspace(0, 2 * np.pi * n_revs, 20000)

x = R * np.cos(t)
y = R * np.sin(t)
z_base = t / (2 * np.pi * n_revs) * TOTAL_HEIGHT
z_osc  = Z_AMP * np.sin(N_OSC_PER_REV * t)
z      = np.clip(z_base + z_osc, 0, TOTAL_HEIGHT)

# ---- Figure ----
fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor('#f8f8f8')

# --- 3D view ---
ax3d = fig.add_subplot(1, 2, 1, projection='3d')
ax3d.set_facecolor('#f0f0f0')

# Cylinder surface (reference, very transparent)
theta_c = np.linspace(0, 2 * np.pi, 120)
z_c     = np.linspace(0, TOTAL_HEIGHT, 40)
Th, Zc  = np.meshgrid(theta_c, z_c)
ax3d.plot_surface(R * np.cos(Th), R * np.sin(Th), Zc,
                  alpha=0.06, color='gray', linewidth=0, antialiased=False)

# Nozzle path — colour by Z for depth cue
sc = ax3d.scatter(x, y, z, c=z, cmap='plasma', s=0.3, alpha=0.9, linewidths=0)
fig.colorbar(sc, ax=ax3d, shrink=0.5, pad=0.02, label='Z (mm)')

ax3d.set_xlabel('X (mm)', labelpad=6)
ax3d.set_ylabel('Y (mm)', labelpad=6)
ax3d.set_zlabel('Z (mm)', labelpad=6)
ax3d.set_zlim(0, TOTAL_HEIGHT)
ax3d.view_init(elev=22, azim=-55)
ax3d.set_title(
    f'3D mesh ribbon\n'
    f'φ{CIRCLE_DIA}mm × H{TOTAL_HEIGHT}mm  |  layer {LAYER_HEIGHT}mm  |  {N_OSC_PER_REV} osc/rev',
    fontsize=10)

# --- Unwrapped view ---
ax2d = fig.add_subplot(1, 2, 2)
ax2d.set_facecolor('#f0f0f0')

circ = 2 * np.pi * R                  # circumference ≈ 157 mm
arc  = (t % (2 * np.pi)) * R          # circumferential position (0…circ)

# Plot each revolution in a different colour shade
n_full = int(n_revs) + 1
cmap   = plt.cm.plasma
for rev in range(n_full):
    mask = (t >= rev * 2 * np.pi) & (t < (rev + 1) * 2 * np.pi)
    if not mask.any():
        continue
    col = cmap(rev / n_full)
    ax2d.plot(arc[mask], z[mask], color=col, lw=1.2, alpha=0.85)

# Mark mesh nodes (where adjacent loops touch: z_osc extremes)
peak_t = []
for k in range(int(N_OSC_PER_REV * n_revs) + 1):
    tp = (np.pi / 2 + k * 2 * np.pi) / N_OSC_PER_REV   # peaks of sin
    if 0 <= tp <= t[-1]:
        peak_t.append(tp)
    tp2 = (-np.pi / 2 + k * 2 * np.pi) / N_OSC_PER_REV  # troughs
    if 0 <= tp2 <= t[-1]:
        peak_t.append(tp2)

for tp in peak_t:
    idx = np.searchsorted(t, tp)
    if 0 < idx < len(t):
        ax2d.plot((tp % (2 * np.pi)) * R, z[idx], 'ko', ms=2.5, alpha=0.5)

ax2d.set_xlim(0, circ)
ax2d.set_ylim(-Z_AMP, TOTAL_HEIGHT + Z_AMP)
ax2d.set_xlabel('Circumferential arc length (mm)', fontsize=9)
ax2d.set_ylabel('Z (mm)', fontsize=9)
ax2d.set_title('Unwrapped cylinder view\n(each colour = 1 revolution, dots = mesh nodes)',
               fontsize=10)
ax2d.grid(True, alpha=0.3)
ax2d.axhline(0, color='k', lw=0.5, ls='--', alpha=0.4)
ax2d.axhline(TOTAL_HEIGHT, color='k', lw=0.5, ls='--', alpha=0.4)

# Add cell size annotations
cell_circ = circ / N_OSC_PER_REV
ax2d.annotate('', xy=(cell_circ, 5), xytext=(0, 5),
               arrowprops=dict(arrowstyle='<->', color='green', lw=1.2))
ax2d.text(cell_circ / 2, 5.8, f'{cell_circ:.0f}mm', ha='center', color='green', fontsize=8)
ax2d.annotate('', xy=(circ * 0.98, LAYER_HEIGHT), xytext=(circ * 0.98, 0),
               arrowprops=dict(arrowstyle='<->', color='darkred', lw=1.2))
ax2d.text(circ * 0.96, LAYER_HEIGHT / 2, f'{LAYER_HEIGHT:.0f}mm',
          ha='right', color='darkred', fontsize=8)

plt.tight_layout()
plt.savefig('mesh_structure2.png', dpi=150, bbox_inches='tight')
print("Saved: mesh_structure2.png")
print(f"  Z amplitude : {Z_AMP} mm")
print(f"  Revolutions : {n_revs:.1f}")
print(f"  Cell width  : {cell_circ:.1f} mm (circumferential)")
print(f"  Cell height : {LAYER_HEIGHT} mm")
print(f"  Mesh nodes  : {len(peak_t)}")
