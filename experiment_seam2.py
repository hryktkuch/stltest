"""
Phase 1d experiment: negative overlap test — 4 combos (1 row)

Fixed (from Phase 1b/1c):
  Z=0.8mm, Speed=15mm/s, Approach=8mm, Unretract=8mm (fully distributed)

Factor: OVERLAP_DEG = -6° / -4° / -2° / 0°
  (0° = reference from Phase 1c best result)

Layout (1 row, 4 cols):
  [1] Ov=-6°  X=70  Y=80
  [2] Ov=-4°  X=150 Y=80
  [3] Ov=-2°  X=240 Y=80
  [4] Ov= 0°  X=320 Y=80
"""

import numpy as np

# ---- Fixed printer settings ----
NOZZLE_DIA   = 1.8
FILAMENT_DIA = 1.75
NOZZLE_TEMP  = 200
BED_TEMP     = 60
F_TRAVEL     = 6000
RETRACT_MM   = 3.0

# ---- Fixed experiment settings ----
Z              = 0.8
SPEED          = 15
APPROACH_MM    = 8.0
UNRETRACT_MM   = 8.0   # fully distributed over approach

# ---- Ring geometry ----
RING_R         = 15.0
PTS            = 200

# ---- Mini purge ----
MINI_PURGE_LEN = 30.0
MINI_PURGE_GAP = 12.0

# ---- Experimental factor ----
OVERLAP_DEGS = [-6, -4, -2, 0]   # degrees

# ---- Grid ----
CX = [70, 150, 240, 320]
CY = 80

# ---- Helpers ----
filament_area = np.pi * (FILAMENT_DIA / 2) ** 2
er     = NOZZLE_DIA * Z / filament_area
f      = int(SPEED * 60)
z_lift = Z + 3.0

lines = []
def c(s): lines.append(s)

# ---- Header ----
c('; ==================================================')
c('; Ring Seam Experiment — Phase 1d: negative overlap')
c('; ==================================================')
c(f'; Fixed: Z={Z}mm  Speed={SPEED}mm/s'
  f'  Approach={APPROACH_MM}mm  Unretract={UNRETRACT_MM}mm')
c('; Factor: OVERLAP_DEG = ' + str(OVERLAP_DEGS))
c(';')
for ci, deg in enumerate(OVERLAP_DEGS):
    c(f'; [{ci+1}] Ov={deg:+d}°  X{CX[ci]} Y{CY}')
c('; ==================================================')
c('')

# ---- Start sequence ----
c(f'M104 S{NOZZLE_TEMP}')
c(f'M140 S{BED_TEMP}')
c('G28')
c('M106 S0')
c(f'M109 S{NOZZLE_TEMP}')
c(f'M190 S{BED_TEMP}')
c('G21')
c('G90')
c('M83')
c('G92 E0')
c('')

# Initial purge
c('; --- Initial purge ---')
c('G1 Z10 F3000')
c('G1 X20 Y20 F6000')
c(f'G1 Z{Z:.2f} F2000')
c('G92 E0')
c('G1 E10 F100')
c('G1 X150 E50 F400')
c('G1 X170 F5000')
c(f'G1 E-{RETRACT_MM:.1f} F600')
c('G92 E0')
c('')

# ---- Units ----
for ci, overlap_deg in enumerate(OVERLAP_DEGS):
    cx = CX[ci]
    cy = CY
    overlap_rad = np.deg2rad(overlap_deg)

    c(f'; ============================================================')
    c(f'; [{ci+1}]  Overlap={overlap_deg:+d}°')
    c(f'; Center: X{cx} Y{cy}')
    c(f'; ============================================================')

    # Mini purge
    px0 = cx - MINI_PURGE_LEN / 2
    px1 = cx + MINI_PURGE_LEN / 2
    py  = cy - RING_R - MINI_PURGE_GAP
    c('; Mini purge')
    c(f'G1 Z{z_lift:.2f} F{F_TRAVEL}')
    c(f'G1 X{px0:.1f} Y{py:.1f} F{F_TRAVEL}')
    c(f'G1 Z{Z:.2f} F2000')
    c('G92 E0')
    c('G1 E3 F150')
    c(f'G1 X{px1:.1f} E{MINI_PURGE_LEN * er:.4f} F{f}')
    c(f'G1 E-{RETRACT_MM:.1f} F600')
    c('G92 E0')

    # Ring: travel to approach start
    ax = cx + RING_R + APPROACH_MM
    c('; Ring')
    c(f'G1 Z{z_lift:.2f} F{F_TRAVEL}')
    c(f'G1 X{ax:.3f} Y{cy:.3f} F{F_TRAVEL}')
    c(f'G1 Z{Z:.3f} F{F_TRAVEL // 2}')

    # Approach: un-retract fully distributed over UNRETRACT_MM
    remaining = APPROACH_MM - UNRETRACT_MM
    if remaining > 0:
        mid_x = cx + RING_R + remaining
        c(f'G1 X{mid_x:.3f} Y{cy:.3f} E{RETRACT_MM + UNRETRACT_MM * er:.5f} F{f}')
        c(f'G1 X{cx + RING_R:.3f} Y{cy:.3f} E{remaining * er:.5f} F{f}')
    else:
        c(f'G1 X{cx + RING_R:.3f} Y{cy:.3f} E{RETRACT_MM + APPROACH_MM * er:.5f} F{f}')

    # Ring arc
    end_angle = 2 * np.pi + overlap_rad
    t  = np.linspace(0, end_angle, PTS)
    xs = cx + RING_R * np.cos(t)
    ys = cy + RING_R * np.sin(t)
    prev_x, prev_y = cx + RING_R, cy
    c(f'G1 F{f}')
    for i in range(len(xs)):
        dx  = xs[i] - prev_x
        dy  = ys[i] - prev_y
        seg = np.sqrt(dx*dx + dy*dy)
        if seg < 0.001:
            continue
        c(f'G1 X{xs[i]:.3f} Y{ys[i]:.3f} Z{Z:.3f} E{seg * er:.5f}')
        prev_x, prev_y = xs[i], ys[i]

    c(f'G1 E-{RETRACT_MM:.1f} F600')
    c('G92 E0')
    c('')

# ---- End sequence ----
c('; --- End ---')
c('M106 S0')
c('M104 S0')
c('M140 S0')
c('G1 Z80 F3000')
c('G28 X0')
c('M84')

gcode = '\n'.join(lines)
with open('experiment_seam2.gcode', 'w') as f:
    f.write(gcode)

n_g1 = sum(1 for l in lines if l.startswith('G1'))
print('Generated: experiment_seam2.gcode')
print(f'  G1 moves : {n_g1}')
print(f'  Lines    : {len(lines)}')
print()
print(f'Fixed: Z={Z}mm  Speed={SPEED}mm/s  Approach={APPROACH_MM}mm  Unretract={UNRETRACT_MM}mm')
print()
for ci, deg in enumerate(OVERLAP_DEGS):
    print(f'  [{ci+1}] Ov={deg:+d}°  X{CX[ci]} Y{CY}')
