"""
Phase 2 experiment: single strand air printing — 3×3 = 9 combos

Fixed (from Phase 1 confirmed):
  RING_HEIGHT=0.8mm, Ring speed=15mm/s, Approach=8mm,
  Unretract=8mm (distributed), Overlap=-4°
  N_OSC_PER_REV=12, N_LAYERS=1, OVERLAP=1.0mm, Fan=100% during mesh

Adhesion reinforcement:
  N_RINGS=2 concentric rings (inner to outer) for more bed contact area
  RING_DWELL_MS=5000ms cooling dwell after rings before mesh starts

Factor A (rows, Y): PRINT_SPEED = 0.5 / 1.5 / 4.5 mm/s
Factor B (cols, X): DWELL_MS    = 1500 / 3000 / 6000 ms

Each unit: N_RINGS base rings → dwell → 1 zigzag mesh layer

Grid layout (single column, Y axis):
  [1] Speed=0.5 Dwell=1500  Y=48
  [2] Speed=0.5 Dwell=3000  Y=90
  ...
  [9] Speed=4.5 Dwell=6000  Y=384
"""

import numpy as np

# ---- Fixed printer settings ----
NOZZLE_DIA   = 1.8
FILAMENT_DIA = 1.75
NOZZLE_TEMP  = 200
BED_TEMP     = 60
F_TRAVEL     = 6000
RETRACT_MM   = 3.0

# ---- Fixed ring settings (Phase 1 confirmed) ----
RING_HEIGHT   = 0.8    # mm
RING_SPEED    = 15     # mm/s
APPROACH_MM   = 8.0    # mm
UNRETRACT_MM  = 8.0    # mm (fully distributed over approach)
OVERLAP_DEG   = -4.0   # degrees

# ---- Base adhesion reinforcement ----
N_RINGS       = 2      # concentric rings printed inner→outer; 1 = single ring
RING_DWELL_MS = 5000   # ms: cooling dwell after all rings before mesh starts

# ---- Fixed mesh geometry ----
N_OSC_PER_REV = 8
OVERLAP        = 1.0   # mm: layer-to-layer embedding
CIRCLE_DIA     = 30.0  # mm
RING_R         = CIRCLE_DIA / 2

# Derived geometry (1 layer only)
LAYER_HEIGHT   = 3.65  # mm (consistent with 8-layer full print)
Z_AMP          = (LAYER_HEIGHT + OVERLAP) / 2

# ---- Fixed process ----
FLOW_RING      = 100   # M221 %
FLOW_MESH      = 50    # M221 %
PTS            = 200

# ---- Mini purge geometry ----
MINI_PURGE_LEN = 30.0  # mm
MINI_PURGE_GAP = 12.0  # mm: gap between purge line bottom and ring bottom

# ---- Experimental factors ----
SPEED_VALS = [0.5, 1.5, 4.5]    # Factor A: mm/s (rows)
DWELL_VALS = [1500, 3000, 6000]  # Factor B: ms

# ---- Selected combos for this run ----
# Full 3x3: [(sp, dw) for sp in SPEED_VALS for dw in DWELL_VALS]
# Unit 4 = (1.5, 1500), Unit 7 = (4.5, 1500)
COMBOS = [(1.5, 1500), (4.5, 1500)]

# ---- Grid: single column along Y axis ----
CX_CENTER = 150          # fixed X for all units
CY_LIST   = [100, 300]   # mm: manually set for sufficient spacing (170mm gap between outer edges)

# ---- Helpers ----
filament_area = np.pi * (FILAMENT_DIA / 2) ** 2
E_RING = NOZZLE_DIA * RING_HEIGHT / filament_area
E_MESH = np.pi * (NOZZLE_DIA / 2) ** 2 / filament_area

# Safe travel Z: above mesh peak + margin
Z_MESH_PEAK = RING_HEIGHT + 0.5 * LAYER_HEIGHT + Z_AMP
Z_SAFE      = Z_MESH_PEAK + 5.0

def triangle_wave(x):
    return (2 / np.pi) * np.arcsin(np.sin(x))

lines = []
def c(s): lines.append(s)

# ---- Header ----
c('; ==================================================')
c('; Phase 2: Single strand air printing — 3×3 = 9 combos')
c('; ==================================================')
c(f'; Fixed: RING_HEIGHT={RING_HEIGHT}mm  Ring speed={RING_SPEED}mm/s')
c(f';        Approach={APPROACH_MM}mm  Unretract={UNRETRACT_MM}mm  Overlap={OVERLAP_DEG}°')
c(f';        N_RINGS={N_RINGS}  RING_DWELL={RING_DWELL_MS}ms')
c(f';        N_OSC={N_OSC_PER_REV}  LAYER_HEIGHT={LAYER_HEIGHT}mm  Z_AMP=±{Z_AMP:.2f}mm')
c(f';        E/mm ring={E_RING:.4f}  E/mm mesh={E_MESH:.4f}')
c(f';        Z_SAFE={Z_SAFE:.2f}mm')
c('; Factor A: PRINT_SPEED = ' + str(SPEED_VALS) + ' mm/s')
c('; Factor B: DWELL_MS    = ' + str(DWELL_VALS) + ' ms')
c('; Layout: single column X=' + str(CX_CENTER) + ', Y increases')
c(';')
c('; Unit  Speed      Dwell    CenterY')
for i, (sp, dw) in enumerate(COMBOS):
    c(f';  [{i+1:2d}]  {sp}mm/s    {dw}ms    Y={CY_LIST[i]}')
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
c('M221 S100              ; Reset flow rate')
c('')

# Initial purge
c('; --- Initial purge ---')
c('G1 Z10 F3000')
c('G1 X20 Y20 F6000')
c(f'G1 Z{RING_HEIGHT:.2f} F2000')
c('G92 E0')
c('G1 E10 F100')
c('G1 X150 E50 F400')
c('G1 X170 F5000')
c(f'G1 E-{RETRACT_MM:.1f} F600')
c('G92 E0')
c('')

def emit_ring(cx, cy):
    """Print N_RINGS concentric base rings (inner→outer), then cooling dwell."""
    z           = RING_HEIGHT
    f_r         = int(RING_SPEED * 60)
    overlap_rad = np.deg2rad(OVERLAP_DEG)

    c(f'M221 S{FLOW_RING}')

    for ring_idx in range(N_RINGS):
        # Radii: innermost first, outermost (RING_R) last
        r = RING_R - (N_RINGS - 1 - ring_idx) * NOZZLE_DIA

        # Travel to approach start
        ax = cx + r + APPROACH_MM
        c(f'G1 Z{Z_SAFE:.2f} F{F_TRAVEL}')
        c(f'G1 X{ax:.3f} Y{cy:.3f} F{F_TRAVEL}')
        c(f'G1 Z{z:.3f} F{F_TRAVEL // 2}')
        # Approach with distributed un-retract
        e_approach = RETRACT_MM + APPROACH_MM * E_RING
        c(f'G1 X{cx + r:.3f} Y{cy:.3f} E{e_approach:.5f} F{f_r}')
        # Ring arc (360° + overlap)
        end_angle = 2 * np.pi + overlap_rad
        t  = np.linspace(0, end_angle, PTS)
        xs = cx + r * np.cos(t)
        ys = cy + r * np.sin(t)
        prev_x, prev_y = cx + r, cy
        c(f'G1 F{f_r}')
        for i in range(len(xs)):
            dx = xs[i] - prev_x; dy = ys[i] - prev_y
            seg = np.sqrt(dx*dx + dy*dy)
            if seg < 0.001: continue
            c(f'G1 X{xs[i]:.3f} Y{ys[i]:.3f} Z{z:.3f} E{seg * E_RING:.5f}')
            prev_x, prev_y = xs[i], ys[i]
        c(f'G1 E-{RETRACT_MM:.1f} F600')
        c('G92 E0')

    # Lift and cooling dwell before mesh
    if RING_DWELL_MS > 0:
        c(f'G1 Z{Z_SAFE:.2f} F{F_TRAVEL}')
        c(f'G4 P{RING_DWELL_MS}              ; Cool rings before mesh')

def emit_mesh_layer(cx, cy, print_speed, dwell_ms):
    """Print 1 zigzag mesh layer (n=0, even layer, valley start clipped)."""
    n        = 0
    z_mid    = RING_HEIGHT + 0.5 * LAYER_HEIGHT
    phase_n  = -np.pi / 2  # even layer: valley start
    t_offset = 0.0
    f_m      = int(print_speed * 60)

    t  = np.linspace(t_offset, t_offset + 2 * np.pi, PTS)
    xs = cx + RING_R * np.cos(t)
    ys = cy + RING_R * np.sin(t)
    zs = z_mid + Z_AMP * triangle_wave(N_OSC_PER_REV * t + phase_n)
    zs = np.maximum(zs, RING_HEIGHT)  # clip valleys to ring height

    # Apex detection
    dz = np.diff(zs)
    is_apex = np.zeros(len(t), dtype=bool)
    for i in range(1, len(dz)):
        if dz[i-1] > 0 and dz[i] <= 0:
            is_apex[i] = True
        elif dz[i-1] < 0 and dz[i] >= 0:
            is_apex[i] = True

    c(f'M221 S{FLOW_MESH}')
    c(f'G1 Z{Z_SAFE:.3f} F{F_TRAVEL}')
    c(f'G1 X{xs[0]:.3f} Y{ys[0]:.3f} F{F_TRAVEL}')
    c(f'G1 Z{zs[0]:.3f} F{F_TRAVEL // 2}')
    c(f'G1 E{RETRACT_MM:.1f} F300')
    c(f'G1 F{f_m}')
    for i in range(1, len(xs)):
        dx = xs[i]-xs[i-1]; dy = ys[i]-ys[i-1]; dz_i = zs[i]-zs[i-1]
        seg = np.sqrt(dx*dx + dy*dy + dz_i*dz_i)
        if seg < 0.001: continue
        c(f'G1 X{xs[i]:.3f} Y{ys[i]:.3f} Z{zs[i]:.3f} E{seg * E_MESH:.5f}')
        if is_apex[i] and dwell_ms > 0:
            c(f'G4 P{dwell_ms}')
    c(f'G1 E-{RETRACT_MM:.1f} F600')
    c('G92 E0')

# ---- Grid ----
for i, (print_speed, dwell_ms) in enumerate(COMBOS):
    cx = CX_CENTER
    cy = CY_LIST[i]

    c(f'; ============================================================')
    c(f'; [{i+1:2d}]  Speed={print_speed}mm/s  Dwell={dwell_ms}ms')
    c(f'; Center: X{cx} Y{cy}')
    c(f'; ============================================================')

    # Mini purge
    px0 = cx - MINI_PURGE_LEN / 2
    px1 = cx + MINI_PURGE_LEN / 2
    py  = cy - RING_R - MINI_PURGE_GAP
    f_r = int(RING_SPEED * 60)
    c('; Mini purge')
    c(f'G1 Z{Z_SAFE:.2f} F{F_TRAVEL}')
    c(f'G1 X{px0:.1f} Y{py:.1f} F{F_TRAVEL}')
    c(f'G1 Z{RING_HEIGHT:.2f} F2000')
    c('G92 E0')
    c('G1 E3 F150')
    c(f'G1 X{px1:.1f} E{MINI_PURGE_LEN * E_RING:.4f} F{f_r}')
    c(f'G1 E-{RETRACT_MM:.1f} F600')
    c('G92 E0')

    # Base rings + dwell
    c(f'; Base rings (N={N_RINGS}) + cooling dwell')
    emit_ring(cx, cy)

    # Fan ON before mesh
    c('M106 S255             ; Fan 100% for air printing')

    # Mesh layer
    c('; Mesh layer (n=0)')
    emit_mesh_layer(cx, cy, print_speed, dwell_ms)

    # Fan OFF after unit
    c('M106 S0               ; Fan off before next ring')
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
with open('experiment_phase2.gcode', 'w') as f:
    f.write(gcode)

n_g1 = sum(1 for l in lines if l.startswith('G1'))
n_g4 = sum(1 for l in lines if l.startswith('G4'))
print('Generated: experiment_phase2.gcode')
print(f'  G1 moves : {n_g1}')
print(f'  G4 dwells: {n_g4}')
print(f'  Lines    : {len(lines)}')
print()
print(f'Geometry: N_OSC={N_OSC_PER_REV}  Span={np.pi*CIRCLE_DIA/N_OSC_PER_REV:.1f}mm'
      f'  Z_AMP=±{Z_AMP:.2f}mm  Angle={np.degrees(np.arctan(2*Z_AMP/(np.pi*CIRCLE_DIA/N_OSC_PER_REV))):.1f}°')
print()
print(f'Ring radii (N_RINGS={N_RINGS}): ' +
      ', '.join(f'R={RING_R - (N_RINGS-1-k)*NOZZLE_DIA:.1f}mm' for k in range(N_RINGS)))
print(f'Ring dwell: {RING_DWELL_MS}ms after all rings')
print()
print(f'Layout (single column X={CX_CENTER}):')
print(f'  {"Unit":4}  {"Speed":10}  {"Dwell":8}  CenterY')
for i, (sp, dw) in enumerate(COMBOS):
    print(f'  [{i+1:2d}]   {sp}mm/s      {dw}ms      Y={CY_LIST[i]}')
print()
print(f'Bed check:')
print(f'  First purge Y: {CY_LIST[0] - RING_R - MINI_PURGE_GAP:.0f}mm')
print(f'  Last ring top Y: {CY_LIST[-1] + RING_R:.0f}mm  (limit: 400mm)')
