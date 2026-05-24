"""
Phase 1 experiment: ring base adhesion
Factor A (Y / rows): nozzle Z = ring bead height
Factor B (X / cols): print speed

Layout on 400×400mm bed:

          Speed 5mm/s   Speed 10mm/s  Speed 15mm/s
Z=1.0mm  [3,1] X70      [3,2] X150    [3,3] X230
Z=0.8mm  [2,1] X70      [2,2] X150    [2,3] X230
Z=0.6mm  [1,1] X70      [1,2] X150    [1,3] X230
          Y=70           Y=70          Y=70
(row 1 at Y=70, row 2 at Y=160, row 3 at Y=250)

Each unit: 30mm mini-purge line below ring, then φ30mm ring.
"""

import numpy as np

# ---- Fixed ----
NOZZLE_DIA   = 1.8
FILAMENT_DIA = 1.75
NOZZLE_TEMP  = 200
BED_TEMP     = 60
F_TRAVEL     = 6000
RING_R       = 15.0     # φ30mm
PTS          = 200

filament_area = np.pi * (FILAMENT_DIA / 2) ** 2

# ---- Experimental factors ----
Z_VALUES     = [0.6, 0.8, 1.0]   # rows (Y increases)
SPEED_VALUES = [5,   10,  15 ]   # cols (X increases)  mm/s

# ---- Grid centers ----
CX = [70, 150, 230]   # X centers per speed column
CY = [70, 160, 250]   # Y centers per Z row

# ---- Helpers ----
def e_rate(z):
    """E value per mm of travel for a rectangular bead NOZZLE_DIA × z."""
    return NOZZLE_DIA * z / filament_area

lines = []
def c(s): lines.append(s)

# ==================================================
# Header / map
# ==================================================
c('; ==================================================')
c('; Ring Base Adhesion Experiment — Phase 1')
c('; ==================================================')
c('; Factor A rows (Y): Z height')
c('; Factor B cols (X): print speed')
c(';')
c('; Grid map (ring center positions):')
c(';         Speed=5      Speed=10     Speed=15  mm/s')
for ri, z in reversed(list(enumerate(Z_VALUES))):
    row_str = f'; Z={z}mm  '
    for ci, sp in enumerate(SPEED_VALUES):
        row_str += f' [{ri+1},{ci+1}]X{CX[ci]}Y{CY[ri]}  '
    c(row_str)
c(';')
c('; Each unit: mini-purge line (30mm) then ring (φ30mm)')
c('; ==================================================')
c('')

# ==================================================
# Start sequence
# ==================================================
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

# Initial nozzle purge (before the grid)
c('; --- Initial purge (prime nozzle before grid) ---')
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

# ==================================================
# Grid
# ==================================================
def travel_to(x, y, z_lift, z_land):
    c(f'G1 Z{z_lift:.2f} F{F_TRAVEL}')
    c(f'G1 X{x:.3f} Y{y:.3f} F{F_TRAVEL}')
    c(f'G1 Z{z_land:.3f} F{F_TRAVEL // 2}')

for ri, z in enumerate(Z_VALUES):
    for ci, speed in enumerate(SPEED_VALUES):
        cx  = CX[ci]
        cy  = CY[ri]
        er  = e_rate(z)
        f   = int(speed * 60)
        z_lift = z + 3.0

        c(f'; ============================================================')
        c(f'; [{ri+1},{ci+1}]  Z={z}mm  speed={speed}mm/s  E/mm={er:.4f}')
        c(f'; Ring center: X{cx} Y{cy}')
        c(f'; ============================================================')

        # --- Mini purge line (30mm, centered below ring) ---
        px0 = cx - 15.0
        px1 = cx + 15.0
        py  = cy - RING_R - 12   # 12mm clearance below ring
        c('; Mini purge')
        travel_to(px0, py, z_lift, z)
        c('G92 E0')
        c(f'G1 E3 F150')                          # slow initial prime
        c(f'G1 X{px1:.1f} E{30*er:.4f} F{f}')    # purge stroke
        c(f'G1 E-3 F600')                         # retract
        c('G92 E0')

        # --- Ring ---
        t  = np.linspace(0, 2 * np.pi, PTS)
        xs = cx + RING_R * np.cos(t)
        ys = cy + RING_R * np.sin(t)
        c('; Ring')
        travel_to(xs[0], ys[0], z_lift, z)
        c('G1 E3 F300')
        c(f'G1 F{f}')
        for i in range(1, len(xs)):
            dx  = xs[i] - xs[i-1]
            dy  = ys[i] - ys[i-1]
            seg = np.sqrt(dx*dx + dy*dy)
            if seg < 0.001:
                continue
            c(f'G1 X{xs[i]:.3f} Y{ys[i]:.3f} Z{z:.3f} E{seg*er:.5f}')
        c(f'G1 E-3 F600')
        c('G92 E0')
        c('')

# ==================================================
# End sequence
# ==================================================
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
print(f'Grid: {len(Z_VALUES)} Z values × {len(SPEED_VALUES)} speeds = {len(Z_VALUES)*len(SPEED_VALUES)} combos')
print()
print('Layout (ring centers):')
print(f'{"":12}', end='')
for sp in SPEED_VALUES:
    print(f'Speed={sp:2d}mm/s    ', end='')
print()
for ri, z in reversed(list(enumerate(Z_VALUES))):
    print(f'Z={z}mm      ', end='')
    for ci in range(len(SPEED_VALUES)):
        print(f'X{CX[ci]:3d} Y{CY[ri]:3d}       ', end='')
    print()
print()
print('Estimated time (rings only, no dwell):')
total_circ = 2 * np.pi * RING_R
for ri, z in enumerate(Z_VALUES):
    for ci, speed in enumerate(SPEED_VALUES):
        t_ring = total_circ / speed
        print(f'  [{ri+1},{ci+1}] Z={z}mm {speed}mm/s → {t_ring:.0f}s/ring')
