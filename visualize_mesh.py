import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ---- Parameters (adjust freely) ----
NOZZLE_DIA   = 1.8    # mm
CIRCLE_DIA   = 50.0   # mm
Z_PITCH      = 3.0    # mm (Z oscillation period)
LINE_SPACING = 3.0    # mm (spacing between parallel lines)
# ------------------------------------

R = CIRCLE_DIA / 2
Z_AMP = Z_PITCH / 2   # amplitude: half-pitch so total excursion = Z_PITCH

fig = plt.figure(figsize=(13, 10))
ax = fig.add_subplot(111, projection='3d')

n_pts = 400

# X-direction lines: Z = +A*sin(2π x / pitch), phase = 0 → peaks up
y_lines = np.arange(-R, R + LINE_SPACING, LINE_SPACING)
for y0 in y_lines:
    if abs(y0) > R:
        continue
    x_half = np.sqrt(max(R**2 - y0**2, 0))
    x = np.linspace(-x_half, x_half, n_pts)
    z = Z_AMP * np.sin(2 * np.pi * x / Z_PITCH)
    ax.plot(x, np.full_like(x, y0), z,
            color='steelblue', linewidth=NOZZLE_DIA * 0.8, alpha=0.85)

# Y-direction lines: Z = -A*sin(2π y / pitch), phase = π → peaks down where X peaks up
x_lines = np.arange(-R, R + LINE_SPACING, LINE_SPACING)
for x0 in x_lines:
    if abs(x0) > R:
        continue
    y_half = np.sqrt(max(R**2 - x0**2, 0))
    y = np.linspace(-y_half, y_half, n_pts)
    z = -Z_AMP * np.sin(2 * np.pi * y / Z_PITCH)
    ax.plot(np.full_like(y, x0), y, z,
            color='tomato', linewidth=NOZZLE_DIA * 0.8, alpha=0.85)

# Boundary circle (reference)
theta = np.linspace(0, 2 * np.pi, 200)
ax.plot(R * np.cos(theta), R * np.sin(theta), np.zeros(200),
        'k--', linewidth=0.8, alpha=0.4, label='φ50mm boundary')

ax.set_xlabel('X (mm)', labelpad=8)
ax.set_ylabel('Y (mm)', labelpad=8)
ax.set_zlabel('Z (mm)', labelpad=8)
ax.set_title(
    f'3D Mesh Structure\n'
    f'Nozzle φ{NOZZLE_DIA}mm  |  Circle φ{CIRCLE_DIA}mm  |  '
    f'Z-pitch {Z_PITCH}mm  |  Line spacing {LINE_SPACING}mm',
    fontsize=11
)
ax.set_zlim(-Z_AMP * 1.5, Z_AMP * 1.5)
ax.view_init(elev=30, azim=-50)
ax.legend(loc='upper right', fontsize=9)

plt.tight_layout()
plt.savefig('mesh_structure.png', dpi=150, bbox_inches='tight')
print("Saved: mesh_structure.png")
