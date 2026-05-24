"""
Phase 1b experiment: ring base adhesion — 2×2×2×2 = 16 combos

Factor A (Z):        0.6 / 0.8 mm
Factor B (Speed):    10  / 15  mm/s
Factor C (Approach): なし / あり  (8mm radial approach before ring start)
Factor D (Overlap):  なし / あり  (360°+8° to cover seam)

Grid layout (4 cols × 4 rows):

                 Speed=10     Speed=10     Speed=15     Speed=15
                 Overlap=N    Overlap=Y    Overlap=N    Overlap=Y
Z=0.8,App=Y  →  [4,1]        [4,2]        [4,3]        [4,4]
Z=0.8,App=N  →  [3,1]        [3,2]        [3,3]        [3,4]
Z=0.6,App=Y  →  [2,1]        [2,2]        [2,3]        [2,4]
Z=0.6,App=N  →  [1,1]        [1,2]        [1,3]        [1,4]

Ring centers:
  Cols (X): 70, 150, 250, 330
  Rows (Y): 70, 160, 250, 340
"""

import numpy as np
from itertools import product

# ---- Fixed printer settings ----
NOZZLE_DIA   = 1.8
FILAMENT_DIA = 1.75
NOZZLE_TEMP  = 200
BED_TEMP     = 60
F_TRAVEL     = 6000
RING_R       = 15.0
PTS          = 200

# ---- Values for factor levels (change here to test different amounts) ----
APPROACH_MM  = 8.0    # mm: radial approach distance (Factor C = True)
OVERLAP_RAD  = 0.14   # rad ≈ 8°: extra arc past 360° (Factor D = True)

# ---- Mini purge per unit ----
MINI_PURGE_LEN = 30.0   # mm: length of mini purge line before each ring
MINI_PURGE_GAP = 12.0   # mm: clearance between purge line and ring bottom

filament_area = np.pi * (FILAMENT_DIA / 2) ** 2

def e_rate(z):
    return NOZZLE_DIA * z / filament_area

# ---- Experimental factors ----
# Each factor: (label, values)
Z_VALS       = [0.6, 0.8]    # Factor A — rows pair
SPEED_VALS   = [10,  15 ]    # Factor B — cols pair
APPROACH_VALS= [False, True] # Factor C — rows pair (inner)
OVERLAP_VALS = [False, True] # Factor D — cols pair (inner)

# Row index = (Z, Approach) in order:
#   row 0: Z=0.6, App=N
#   row 1: Z=0.6, App=Y
#   row 2: Z=0.8, App=N
#   row 3: Z=0.8, App=Y
ROW_COMBOS = [(z, app) for z in Z_VALS for app in APPROACH_VALS]

# Col index = (Speed, Overlap):
#   col 0: Speed=10, Ov=N
#   col 1: Speed=10, Ov=Y
#   col 2: Speed=15, Ov=N
#   col 3: Speed=15, Ov=Y
COL_COMBOS = [(sp, ov) for sp in SPEED_VALS for ov in OVERLAP_VALS]

CX = [70, 150, 250, 330]   # X centers per column
CY = [70, 160, 250, 340]   # Y centers per row

# ---- G-code builder ----
lines = []
def c(s): lines.append(s)

# ---- Header ----
c('; ==================================================')
c('; Ring Base Adhesion Experiment — Phase 1b')
c('; 2×2×2×2 = 16 combinations')
c('; ==================================================')
c('; Factor A: Z height    = 0.6 / 0.8 mm')
c('; Factor B: Speed       = 10  / 15  mm/s')
c('; Factor C: Approach    = N / Y  (8mm radial approach)')
c('; Factor D: Overlap     = N / Y  (360°+8° seam coverage)')
c(';')
c('; Grid map:')
c(';              Sp=10,Ov=N  Sp=10,Ov=Y  Sp=15,Ov=N  Sp=15,Ov=Y')
for ri, (z, app) in reversed(list(enumerate(ROW_COMBOS))):
    row_str = f'; Z={z},App={"Y" if app else "N"}  '
    for ci in range(len(COL_COMBOS)):
        row_str += f'[{ri+1},{ci+1}]X{CX[ci]}Y{CY[ri]}   '
    c(row_str)
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
c('G1 Z0.8 F2000')
c('G92 E0')
c('G1 E10 F100')
c('G1 X150 E50 F400')
c('G1 X170 F5000')
c('G1 E-5 F600')
c('G92 E0')
c('')

# ---- Grid ----
for ri, (z, approach) in enumerate(ROW_COMBOS):
    for ci, (speed, overlap) in enumerate(COL_COMBOS):
        cx     = CX[ci]
        cy     = CY[ri]
        er     = e_rate(z)
        f      = int(speed * 60)
        z_lift = z + 3.0

        app_str = 'Y' if approach else 'N'
        ov_str  = 'Y' if overlap  else 'N'
        c(f'; ============================================================')
        c(f'; [{ri+1},{ci+1}]  Z={z}mm  speed={speed}mm/s'
          f'  approach={app_str}  overlap={ov_str}')
        c(f'; Center: X{cx} Y{cy}')
        c(f'; ============================================================')

        # Mini purge (30mm line below ring)
        px0 = cx - MINI_PURGE_LEN / 2
        px1 = cx + MINI_PURGE_LEN / 2
        py  = cy - RING_R - MINI_PURGE_GAP
        c('; Mini purge')
        c(f'G1 Z{z_lift:.2f} F{F_TRAVEL}')
        c(f'G1 X{px0:.1f} Y{py:.1f} F{F_TRAVEL}')
        c(f'G1 Z{z:.2f} F2000')
        c('G92 E0')
        c('G1 E3 F150')
        c(f'G1 X{px1:.1f} E{30*er:.4f} F{f}')
        c('G1 E-3 F600')
        c('G92 E0')

        # Ring
        c('; Ring')
        if approach:
            # Travel to R+APPROACH_MM outside ring, un-retract there
            ax = cx + RING_R + APPROACH_MM
            c(f'G1 Z{z_lift:.2f} F{F_TRAVEL}')
            c(f'G1 X{ax:.3f} Y{cy:.3f} F{F_TRAVEL}')
            c(f'G1 Z{z:.3f} F{F_TRAVEL // 2}')
            c('G1 E3 F300')
            # Approach inward to ring start while extruding
            c(f'G1 X{cx + RING_R:.3f} Y{cy:.3f} E{APPROACH_MM * er:.5f} F{f}')
        else:
            # Travel directly to ring start
            c(f'G1 Z{z_lift:.2f} F{F_TRAVEL}')
            c(f'G1 X{cx + RING_R:.3f} Y{cy:.3f} F{F_TRAVEL}')
            c(f'G1 Z{z:.3f} F{F_TRAVEL // 2}')
            c('G1 E3 F300')

        # Arc: 360° or 360°+overlap
        end_angle = 2 * np.pi + (OVERLAP_RAD if overlap else 0.0)
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
            c(f'G1 X{xs[i]:.3f} Y{ys[i]:.3f} Z{z:.3f} E{seg*er:.5f}')
            prev_x, prev_y = xs[i], ys[i]

        c('G1 E-3 F600')
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
with open('experiment_base.gcode', 'w') as f:
    f.write(gcode)

n_g1 = sum(1 for l in lines if l.startswith('G1'))
print('Generated: experiment_base.gcode')
print(f'  G1 moves : {n_g1}')
print(f'  Lines    : {len(lines)}')
print()
print('Grid map:')
header = f'{"":18}' + ''.join(f'Sp={sp},Ov={"Y" if ov else "N"}  ' for sp, ov in COL_COMBOS)
print(header)
for ri, (z, app) in reversed(list(enumerate(ROW_COMBOS))):
    row = f'Z={z},App={"Y" if app else "N"}  '
    for ci in range(len(COL_COMBOS)):
        row += f'  [{ri+1},{ci+1}]X{CX[ci]:3d}Y{CY[ri]:3d}  '
    print(row)
