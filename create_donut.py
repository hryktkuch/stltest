import numpy as np
import struct

def write_stl_binary(filename, triangles, normals):
    with open(filename, 'wb') as f:
        f.write(b'\x00' * 80)
        f.write(struct.pack('<I', len(triangles)))
        for tri, norm in zip(triangles, normals):
            f.write(struct.pack('<fff', *norm))
            for v in tri:
                f.write(struct.pack('<fff', *v))
            f.write(struct.pack('<H', 0))

def create_donut_stl(outer_r, inner_r, h, n=360):
    triangles = []
    normals = []
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)

    for i in range(n):
        a0, a1 = angles[i], angles[(i + 1) % n]
        c0, s0 = np.cos(a0), np.sin(a0)
        c1, s1 = np.cos(a1), np.sin(a1)

        # Top face (z = h), normal up
        oi0 = (inner_r * c0, inner_r * s0, h)
        oo0 = (outer_r * c0, outer_r * s0, h)
        oo1 = (outer_r * c1, outer_r * s1, h)
        oi1 = (inner_r * c1, inner_r * s1, h)
        triangles += [[oi0, oo0, oo1], [oi0, oo1, oi1]]
        normals += [(0, 0, 1), (0, 0, 1)]

        # Bottom face (z = 0), normal down
        bi0 = (inner_r * c0, inner_r * s0, 0)
        bo0 = (outer_r * c0, outer_r * s0, 0)
        bo1 = (outer_r * c1, outer_r * s1, 0)
        bi1 = (inner_r * c1, inner_r * s1, 0)
        triangles += [[bi0, bo1, bo0], [bi0, bi1, bo1]]
        normals += [(0, 0, -1), (0, 0, -1)]

        mid = (a0 + a1) / 2

        # Outer wall
        on = (np.cos(mid), np.sin(mid), 0)
        triangles += [
            [bo0, bo1, oo1],
            [bo0, oo1, oo0],
        ]
        normals += [on, on]

        # Inner wall
        inn = (-np.cos(mid), -np.sin(mid), 0)
        triangles += [
            [bi0, oi1, bi1],
            [bi0, oi0, oi1],
        ]
        normals += [inn, inn]

    return triangles, normals


outer_diameter = 400.0
inner_diameter = 360.0
height = 0.4

tris, norms = create_donut_stl(outer_diameter / 2, inner_diameter / 2, height)
filename = "donut_od400_id360_h0.4.stl"
write_stl_binary(filename, tris, norms)

print(f"作成完了: {filename}")
print(f"  外径: {outer_diameter} mm")
print(f"  穴径: {inner_diameter} mm")
print(f"  リング幅: {(outer_diameter - inner_diameter) / 2} mm")
print(f"  厚さ: {height} mm")
print(f"  三角形数: {len(tris)}")
