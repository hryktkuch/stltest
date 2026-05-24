import numpy as np

# ---- Shape Parameters ----
CIRCLE_DIA    = 30.0
TOTAL_HEIGHT  = 30.0
RING_HEIGHT   = 1.2
N_LAYERS      = 6
LAYER_HEIGHT  = (TOTAL_HEIGHT - RING_HEIGHT) / N_LAYERS  # 4.8 mm
N_OSC_PER_REV = 8
OVERLAP       = 1.0
Z_AMP         = (LAYER_HEIGHT + OVERLAP) / 2              # 2.9 mm
R             = CIRCLE_DIA / 2

# ---- Print Parameters ----
NOZZLE_DIA    = 1.8
FILAMENT_DIA  = 1.75
PRINT_SPEED   = 100 / 60  # 1.67 mm/s = F100 mm/min (ref: tbl_3axis_test)
TRAVEL_SPEED  = 100.0
NOZZLE_TEMP   = 200       # ref: tbl_3axis_test
BED_TEMP      = 60
BED_CX        = 210.0
BED_CY        = 210.0
PTS_PER_REV   = 200

# ---- Extrusion rates ----
filament_area = np.pi * (FILAMENT_DIA / 2) ** 2
E_RING = (NOZZLE_DIA * RING_HEIGHT)  / filament_area
E_MESH = (NOZZLE_DIA * Z_AMP)        / filament_area

F_PRINT  = int(PRINT_SPEED  * 60)
F_TRAVEL = int(TRAVEL_SPEED * 60)

def triangle_wave(x):
    return (2 / np.pi) * np.arcsin(np.sin(x))

def make_ring(z_val):
    t = np.linspace(0, 2 * np.pi, PTS_PER_REV)
    x = BED_CX + R * np.cos(t)
    y = BED_CY + R * np.sin(t)
    z = np.full_like(t, z_val)
    return x, y, z

def make_layer(n):
    z_mid   = RING_HEIGHT + (n + 0.5) * LAYER_HEIGHT
    phase_n = -np.pi / 2 + n * np.pi
    # Odd layers offset by half-oscillation so they start above the previous layer's peak.
    # Without this, odd layers start above the previous layer's valley → mid-air printing.
    t_offset = (n % 2) * np.pi / (2 * N_OSC_PER_REV)
    t = np.linspace(t_offset, t_offset + 2 * np.pi, PTS_PER_REV)
    x = BED_CX + R * np.cos(t)
    y = BED_CY + R * np.sin(t)
    z = z_mid + Z_AMP * triangle_wave(N_OSC_PER_REV * t + phase_n)
    return x, y, z

# ==================================================
# G-code output
# ==================================================
lines = []
def c(s): lines.append(s)

c('; ============================================')
c('; Zigzag Mesh Cylinder')
c(f'; Printer:   Elegoo Neptune 4 Max')
c(f'; Cylinder:  φ{CIRCLE_DIA}mm × H{TOTAL_HEIGHT}mm')
c(f'; Nozzle:    {NOZZLE_DIA}mm    Filament: {FILAMENT_DIA}mm')
c(f'; Layers:    {N_LAYERS} × {LAYER_HEIGHT:.2f}mm  +  ring {RING_HEIGHT}mm')
c(f'; N_OSC:     {N_OSC_PER_REV}  OVERLAP: {OVERLAP}mm  Z_AMP: ±{Z_AMP:.2f}mm')
c(f'; Material:  PLA   Nozzle {NOZZLE_TEMP}°C  Bed {BED_TEMP}°C')
c(f'; Speed:     {PRINT_SPEED}mm/s ({F_PRINT}mm/min)')
c(f'; Center:    X{BED_CX} Y{BED_CY}')
c(f'; E/mm ring: {E_RING:.4f}  E/mm mesh: {E_MESH:.4f}')
c('; ============================================')
c('')
c('; --- Start sequence ---')
c(f'M104 S{NOZZLE_TEMP}          ; Nozzle preheat')
c(f'M140 S{BED_TEMP}             ; Bed preheat')
c('G28                    ; Home all')
c(f'M109 S{NOZZLE_TEMP}          ; Wait nozzle temp')
c(f'M190 S{BED_TEMP}             ; Wait bed temp')
c('G21                    ; Units mm')
c('G90                    ; Absolute XYZ')
c('M83                    ; Relative extrusion')
c('G92 E0                 ; Reset extruder')
c('M106 S255              ; Fan 100%')
c('')

def emit_path(xs, ys, zs, e_rate, label, flow):
    c(f'; --- {label} ---')
    c(f'M221 S{flow}')
    # Travel to start
    c(f'G1 Z{zs[0]+5:.3f} F{F_TRAVEL}   ; Lift')
    c(f'G1 X{xs[0]:.3f} Y{ys[0]:.3f} F{F_TRAVEL}  ; Move to start')
    c(f'G1 Z{zs[0]:.3f} F{int(F_TRAVEL/2)}  ; Lower')
    c(f'G1 F{F_PRINT}')
    for i in range(1, len(xs)):
        dx = xs[i] - xs[i-1]
        dy = ys[i] - ys[i-1]
        dz = zs[i] - zs[i-1]
        seg = np.sqrt(dx*dx + dy*dy + dz*dz)
        if seg < 0.001:
            continue
        e_val = seg * e_rate
        c(f'G1 X{xs[i]:.3f} Y{ys[i]:.3f} Z{zs[i]:.3f} E{e_val:.5f}')

# Bottom ring
xs, ys, zs = make_ring(RING_HEIGHT)
emit_path(xs, ys, zs, E_RING, 'Bottom ring', 100)

# Zigzag layers
for n in range(N_LAYERS):
    xs, ys, zs = make_layer(n)
    emit_path(xs, ys, zs, E_MESH, f'Mesh layer {n+1}/{N_LAYERS}', 70)

# Top ring
xs, ys, zs = make_ring(TOTAL_HEIGHT)
emit_path(xs, ys, zs, E_RING, 'Top ring', 100)

c('')
c('; --- End sequence ---')
c('M106 S0                ; Fan off')
c('M104 S0                ; Nozzle off')
c('M140 S0                ; Bed off')
c(f'G1 Z{min(TOTAL_HEIGHT+10, 250):.0f} F{F_TRAVEL}  ; Lift')
c('G28 X0                 ; Home X')
c('M84                    ; Disable motors')

gcode = '\n'.join(lines)
with open('cylinder_zigzag.gcode', 'w') as f:
    f.write(gcode)

n_g1 = sum(1 for l in lines if l.startswith('G1'))
print('Generated: cylinder_zigzag.gcode')
print(f'  G1 moves    : {n_g1}')
print(f'  Total lines : {len(lines)}')
print(f'  LAYER_HEIGHT: {LAYER_HEIGHT:.2f} mm')
print(f'  Z_AMP       : ±{Z_AMP:.2f} mm')
print(f'  E/mm ring   : {E_RING:.4f}')
print(f'  E/mm mesh   : {E_MESH:.4f}')
print(f'  Print time  : ~{sum(np.sqrt((make_layer(n)[0][1:]-make_layer(n)[0][:-1])**2 + (make_layer(n)[1][1:]-make_layer(n)[1][:-1])**2 + (make_layer(n)[2][1:]-make_layer(n)[2][:-1])**2).sum() for n in range(N_LAYERS)) / PRINT_SPEED / 60:.1f} min (mesh only)')
