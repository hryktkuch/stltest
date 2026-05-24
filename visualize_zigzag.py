import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ---- Parameters ----
CIRCLE_DIA    = 30.0
TOTAL_HEIGHT  = 30.0
RING_HEIGHT   = 1.2    # flat ring height (bottom & top)
LAYER_HEIGHT  = 5.0
N_OSC_PER_REV = 8      # integer OK (phase per layer set explicitly)
OVERLAP       = 1.0    # mm  peaks embed into adjacent layer
Z_AMP         = (LAYER_HEIGHT + OVERLAP) / 2  # 3.0 mm

R        = CIRCLE_DIA / 2   # 15 mm
N_LAYERS = int((TOTAL_HEIGHT - RING_HEIGHT) / LAYER_HEIGHT)  # 5
PTS      = 1000

def triangle_wave(x):
    return (2 / np.pi) * np.arcsin(np.sin(x))

# Bottom ring: flat circle at Z = RING_HEIGHT
t_ring = np.linspace(0, 2*np.pi, PTS)
x_bot = R * np.cos(t_ring);  y_bot = R * np.sin(t_ring);  z_bot = np.full(PTS, RING_HEIGHT)
x_top = R * np.cos(t_ring);  y_top = R * np.sin(t_ring);  z_top = np.full(PTS, TOTAL_HEIGHT)

# Zigzag layers (start from RING_HEIGHT)
layers = []
for n in range(N_LAYERS):
    z_mid   = RING_HEIGHT + (n + 0.5) * LAYER_HEIGHT
    phase_n = -np.pi / 2 + n * np.pi
    t = np.linspace(0, 2 * np.pi, PTS)
    x = R * np.cos(t)
    y = R * np.sin(t)
    z = z_mid + Z_AMP * triangle_wave(N_OSC_PER_REV * t + phase_n)
    layers.append((x, y, z))

print(f"N_LAYERS = {N_LAYERS}")
print(f"Zigzag Z range: {RING_HEIGHT + 0 - Z_AMP:.1f} ~ {RING_HEIGHT + N_LAYERS*LAYER_HEIGHT + Z_AMP:.1f} mm")
print(f"Bottom ring: Z = {RING_HEIGHT} mm")
print(f"Top ring:    Z = {TOTAL_HEIGHT} mm")

# ==================================================
# Figure
# ==================================================
fig = plt.figure(figsize=(16, 9))
fig.patch.set_facecolor('#f8f8f8')
cmap = plt.cm.plasma

# ---- 3D view ----
ax3 = fig.add_subplot(1, 2, 1, projection='3d')
ax3.set_facecolor('#f0f0f0')

theta_c = np.linspace(0, 2*np.pi, 120)
z_c     = np.linspace(0, TOTAL_HEIGHT, 40)
Th, Zc  = np.meshgrid(theta_c, z_c)
ax3.plot_surface(R*np.cos(Th), R*np.sin(Th), Zc, alpha=0.05, color='gray', linewidth=0)

# Rings
ax3.plot(x_bot, y_bot, z_bot, color='orangered',   lw=3.0, zorder=5, label=f'Bottom ring (Z={RING_HEIGHT}mm)')
ax3.plot(x_top, y_top, z_top, color='deepskyblue', lw=3.0, zorder=5, label=f'Top ring (Z={TOTAL_HEIGHT}mm)')

# Zigzag layers
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
    f'ring {RING_HEIGHT}mm | layer {LAYER_HEIGHT}mm | {N_OSC_PER_REV} osc/rev | OVERLAP {OVERLAP}mm',
    fontsize=10)

# ---- Unwrapped view ----
ax2 = fig.add_subplot(1, 2, 2)
ax2.set_facecolor('#f0f0f0')
circ = 2 * np.pi * R
arc  = t_ring * R

ax2.fill_between([0, circ], -0.5, 0, color='#aaa', alpha=0.35, label='Build plate')

# Rings
ax2.axhline(RING_HEIGHT,   color='orangered',   lw=2.5, alpha=0.9, label=f'Bottom ring (Z={RING_HEIGHT}mm)')
ax2.axhline(TOTAL_HEIGHT,  color='deepskyblue', lw=2.5, alpha=0.9, label=f'Top ring (Z={TOTAL_HEIGHT}mm)')

# Zigzag layers
for n, (x, y, z) in enumerate(layers):
    col = cmap((n + 0.5) / N_LAYERS)
    ax2.plot(arc, z, color=col, lw=1.5, alpha=0.9, label=f'Layer {n+1}')

# Layer boundaries + overlap zones
for n in range(N_LAYERS + 1):
    ax2.axhline(RING_HEIGHT + n * LAYER_HEIGHT, color='gray', lw=0.8, ls='--', alpha=0.4)
for n in range(1, N_LAYERS):
    boundary = RING_HEIGHT + n * LAYER_HEIGHT
    ax2.axhspan(boundary - OVERLAP/2, boundary + OVERLAP/2,
                color='red', alpha=0.12, zorder=0)
ax2.plot([], [], color='red', alpha=0.4, lw=6, label=f'Overlap zone (±{OVERLAP/2}mm)')

ax2.set_xlim(0, circ)
ax2.set_ylim(-1, TOTAL_HEIGHT + 1)
ax2.set_xlabel('Circumferential arc length (mm)', fontsize=9)
ax2.set_ylabel('Z (mm)', fontsize=9)
ax2.set_title(f'Unwrapped cylinder\nbottom/top ring + {N_LAYERS} zigzag layers', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=8, loc='center right')

plt.tight_layout()
plt.savefig('mesh_zigzag.png', dpi=150, bbox_inches='tight')
print("Saved: mesh_zigzag.png")
