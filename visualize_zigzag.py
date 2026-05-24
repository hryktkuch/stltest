import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ---- Parameters ----
CIRCLE_DIA    = 30.0
TOTAL_HEIGHT  = 30.0
LAYER_HEIGHT  = 5.0
N_OSC_PER_REV = 9.5   # half-integer → phase inverts per layer → diamond mesh
OVERLAP       = 0.0
Z_AMP         = (LAYER_HEIGHT + OVERLAP) / 2  # 2.5 mm

R        = CIRCLE_DIA / 2   # 15 mm
N_LAYERS = int(TOTAL_HEIGHT / LAYER_HEIGHT)  # 6
PTS      = 1000  # points per layer

def triangle_wave(x):
    """Linear zigzag: period 2π, amplitude ±1"""
    return (2 / np.pi) * np.arcsin(np.sin(x))

# Generate each layer independently
layers = []
for n in range(N_LAYERS):
    z_mid   = (n + 0.5) * LAYER_HEIGHT       # center Z of layer n
    phase_n = -np.pi / 2 + n * np.pi         # alternates -π/2, π/2, -π/2 ...
    t = np.linspace(0, 2 * np.pi, PTS)
    x = R * np.cos(t)
    y = R * np.sin(t)
    z = z_mid + Z_AMP * triangle_wave(N_OSC_PER_REV * t + phase_n)
    layers.append((x, y, z))

# Verify touching condition
print("Touching condition check (layer N peak = layer N+1 valley at same angle):")
t_check = np.pi / N_OSC_PER_REV   # first peak angle of layer 0
for n in range(N_LAYERS - 1):
    phase_n   = -np.pi / 2 + n * np.pi
    phase_n1  = -np.pi / 2 + (n+1) * np.pi
    z_mid_n   = (n + 0.5) * LAYER_HEIGHT
    z_mid_n1  = (n + 1.5) * LAYER_HEIGHT
    peak_n    = z_mid_n  + Z_AMP * triangle_wave(N_OSC_PER_REV * t_check + phase_n)
    valley_n1 = z_mid_n1 + Z_AMP * triangle_wave(N_OSC_PER_REV * t_check + phase_n1)
    print(f"  Layer {n} peak={peak_n:.2f}mm  Layer {n+1} valley={valley_n1:.2f}mm  "
          f"{'✓' if abs(peak_n - valley_n1) < 0.01 else '✗'}")

# ==================================================
# Figure
# ==================================================
fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor('#f8f8f8')
cmap = plt.cm.plasma

# ---- 3D view ----
ax3 = fig.add_subplot(1, 2, 1, projection='3d')
ax3.set_facecolor('#f0f0f0')

# Cylinder reference surface
theta_c = np.linspace(0, 2*np.pi, 120)
z_c     = np.linspace(0, TOTAL_HEIGHT, 40)
Th, Zc  = np.meshgrid(theta_c, z_c)
ax3.plot_surface(R*np.cos(Th), R*np.sin(Th), Zc, alpha=0.05, color='gray', linewidth=0)

for n, (x, y, z) in enumerate(layers):
    col = cmap((n + 0.5) / N_LAYERS)
    ax3.plot(x, y, z, color=col, lw=1.8, alpha=0.9, label=f'Layer {n+1}')

ax3.set_xlabel('X (mm)', labelpad=6)
ax3.set_ylabel('Y (mm)', labelpad=6)
ax3.set_zlabel('Z (mm)', labelpad=6)
ax3.set_zlim(0, TOTAL_HEIGHT)
ax3.view_init(elev=22, azim=-55)
ax3.legend(fontsize=8, loc='upper left')
ax3.set_title(
    f'Zigzag mesh cylinder  (φ{CIRCLE_DIA}mm × H{TOTAL_HEIGHT}mm)\n'
    f'layer {LAYER_HEIGHT}mm | {N_OSC_PER_REV} osc/rev | Z_AMP ±{Z_AMP}mm | {N_LAYERS} layers',
    fontsize=10)

# ---- Unwrapped view ----
ax2 = fig.add_subplot(1, 2, 2)
ax2.set_facecolor('#f0f0f0')
circ = 2 * np.pi * R

ax2.fill_between([0, circ], -0.5, 0, color='#aaa', alpha=0.35, label='Build plate')

t_flat = np.linspace(0, 2*np.pi, PTS)
arc    = t_flat * R

for n, (x, y, z) in enumerate(layers):
    col = cmap((n + 0.5) / N_LAYERS)
    ax2.plot(arc, z, color=col, lw=1.5, alpha=0.9, label=f'Layer {n+1}')

# Layer boundary lines
for n in range(N_LAYERS + 1):
    ax2.axhline(n * LAYER_HEIGHT, color='gray', lw=0.6, ls='--', alpha=0.4)

ax2.set_xlim(0, circ)
ax2.set_ylim(-1, TOTAL_HEIGHT + 1)
ax2.set_xlabel('Circumferential arc length (mm)', fontsize=9)
ax2.set_ylabel('Z (mm)', fontsize=9)
ax2.set_title(f'Unwrapped cylinder\n{N_LAYERS} independent layers, linear zigzag', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=8, loc='center right')

plt.tight_layout()
plt.savefig('mesh_zigzag.png', dpi=150, bbox_inches='tight')

print("\nSaved: mesh_zigzag.png")
print(f"  Cylinder    : φ{CIRCLE_DIA}mm × H{TOTAL_HEIGHT}mm")
print(f"  Layers      : {N_LAYERS} × {LAYER_HEIGHT}mm")
print(f"  Z_AMP       : ±{Z_AMP}mm")
print(f"  Osc/rev     : {N_OSC_PER_REV}")
print(f"  Wave type   : linear zigzag (triangle wave)")
print(f"  Path type   : {N_LAYERS} independent closed loops")
