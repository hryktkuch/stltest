"""
Phase 1c experiment: ring seam quality — 4×4 = 16 combos

Fixed (from Phase 1b results):
  Z=0.8mm, Speed=15mm/s, Approach=8mm

Factor A (rows, Y): UNRETRACT_OVER_MM
  アンリトラクトをアプローチ中の何mmにわたって分散させるか
  2 / 4 / 6 / 8 mm

Factor B (cols, X): OVERLAP_DEG
  リング終点が始点を何度上書きするか（継ぎ目カバー）
  0° / 2° / 4° / 6°

Grid layout (4 cols × 4 rows):

                Ov=0°     Ov=2°     Ov=4°     Ov=6°
Unret=8mm  →  [4,1]     [4,2]     [4,3]     [4,4]   Y=310
Unret=6mm  →  [3,1]     [3,2]     [3,3]     [3,4]   Y=230
Unret=4mm  →  [2,1]     [2,2]     [2,3]     [2,4]   Y=150
Unret=2mm  →  [1,1]     [1,2]     [1,3]     [1,4]   Y=70
              X=70      X=150     X=240     X=320
"""

import numpy as np

# ---- Fixed printer settings ----
NOZZLE_DIA   = 1.8
FILAMENT_DIA = 1.75
NOZZLE_TEMP  = 200
BED_TEMP     = 60
F_TRAVEL     = 6000
RETRACT_MM   = 3.0    # mm retracted during travel

# ---- Fixed experiment settings (from Phase 1b) ----
Z            = 0.8    # mm
SPEED        = 15     # mm/s
APPROACH_MM  = 8.0    # mm: radial approach distance

# ---- Ring geometry ----
RING_R       = 15.0   # mm (φ30mm)
PTS          = 200

# ---- Mini purge ----
MINI_PURGE_LEN = 30.0   # mm
MINI_PURGE_GAP = 12.0   # mm: clearance below ring

# ---- Experimental factors ----
UNRETRACT_VALS = [2, 4, 6, 8]   # Factor A: mm (rows)
OVERLAP_DEGS   = [0, 2, 4, 6]   # Factor B: degrees (cols)

# ---- Grid centers ----
CX = [70, 150, 240, 320]   # X per overlap column
CY = [70, 150, 230, 310]   # Y per unretract row

# ---- Helpers ----
filament_area = np.pi * (FILAMENT_DIA / 2) ** 2
er  = NOZZLE_DIA * Z / filament_area
f   = int(SPEED * 60)
z_lift = Z + 3.0

lines = []
def c(s): lines.append(s)

# ---- Header ----
c('; ==================================================')
c('; Ring Seam Experiment — Phase 1c')
c('; 4×4 = 16 combinations')
c('; ==================================================')
c(f'; Fixed: Z={Z}mm  Speed={SPEED}mm/s  Approach={APPROACH_MM}mm')
c('; Factor A rows (Y): UNRETRACT_OVER_MM = ' + str(UNRETRACT_VALS))
c('; Factor B cols (X): OVERLAP_DEG       = ' + str(OVERLAP_DEGS))
c(';')
c('; Grid map:')
c(';              Ov=0°      Ov=2°      Ov=4°      Ov=6°')
for ri, ur in reversed(list(enumerate(UNRETRACT_VALS))):
    row = f'; Unret={ur}mm  '
    for ci in range(len(OVERLAP_DEGS)):
        row += f'[{ri+1},{ci+1}]X{CX[ci]}Y{CY[ri]}   '
    c(row)
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

# ---- Grid ----
for ri, unretract_mm in enumerate(UNRETRACT_VALS):
    for ci, overlap_deg in enumerate(OVERLAP_DEGS):
        cx = CX[ci]
        cy = CY[ri]
        overlap_rad = np.deg2rad(overlap_deg)

        c(f'; ============================================================')
        c(f'; [{ri+1},{ci+1}]  Unretract={unretract_mm}mm  Overlap={overlap_deg}°')
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

        # Approach: distribute un-retract over first unretract_mm of movement
        remaining_approach = APPROACH_MM - unretract_mm
        if remaining_approach > 0:
            # Split: un-retract phase + normal extrusion phase
            mid_x = cx + RING_R + remaining_approach
            e_unret_seg = RETRACT_MM + unretract_mm * er
            c(f'G1 X{mid_x:.3f} Y{cy:.3f} E{e_unret_seg:.5f} F{f}')
            c(f'G1 X{cx + RING_R:.3f} Y{cy:.3f} E{remaining_approach * er:.5f} F{f}')
        else:
            # unretract_mm >= APPROACH_MM: all un-retract within approach
            e_approach = RETRACT_MM + APPROACH_MM * er
            c(f'G1 X{cx + RING_R:.3f} Y{cy:.3f} E{e_approach:.5f} F{f}')

        # Ring arc: 360° + overlap
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
with open('experiment_seam.gcode', 'w') as f:
    f.write(gcode)

n_g1 = sum(1 for l in lines if l.startswith('G1'))
print('Generated: experiment_seam.gcode')
print(f'  G1 moves : {n_g1}')
print(f'  Lines    : {len(lines)}')
print()
print(f'Fixed: Z={Z}mm  Speed={SPEED}mm/s  Approach={APPROACH_MM}mm  Retract={RETRACT_MM}mm')
print()
print('Grid map:')
print(f'{"":14}' + ''.join(f'Ov={d:1d}°      ' for d in OVERLAP_DEGS))
for ri, ur in reversed(list(enumerate(UNRETRACT_VALS))):
    row = f'Unret={ur}mm   '
    for ci in range(len(OVERLAP_DEGS)):
        row += f'[{ri+1},{ci+1}]X{CX[ci]:3d}Y{CY[ri]:3d}  '
    print(row)
