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

def create_cube_stl(s):
    # All 12 triangles with correct outward normals (right-hand rule)
    tris = [
        # bottom z=0, normal (0,0,-1)
        [(0,0,0),(s,s,0),(s,0,0)],
        [(0,0,0),(0,s,0),(s,s,0)],
        # top z=s, normal (0,0,1)
        [(0,0,s),(s,0,s),(s,s,s)],
        [(0,0,s),(s,s,s),(0,s,s)],
        # front y=0, normal (0,-1,0)
        [(0,0,0),(s,0,0),(s,0,s)],
        [(0,0,0),(s,0,s),(0,0,s)],
        # back y=s, normal (0,1,0)
        [(0,s,0),(s,s,s),(s,s,0)],
        [(0,s,0),(0,s,s),(s,s,s)],
        # left x=0, normal (-1,0,0)
        [(0,0,0),(0,0,s),(0,s,s)],
        [(0,0,0),(0,s,s),(0,s,0)],
        # right x=s, normal (1,0,0)
        [(s,0,0),(s,s,s),(s,0,s)],
        [(s,0,0),(s,s,0),(s,s,s)],
    ]
    norms = [
        (0,0,-1),(0,0,-1),
        (0,0,1),(0,0,1),
        (0,-1,0),(0,-1,0),
        (0,1,0),(0,1,0),
        (-1,0,0),(-1,0,0),
        (1,0,0),(1,0,0),
    ]
    return tris, norms

size = 30.0
tris, norms = create_cube_stl(size)
filename = "cube_30mm.stl"
write_stl_binary(filename, tris, norms)
print(f"作成完了: {filename}")
print(f"  サイズ: {size} x {size} x {size} mm")
print(f"  三角形数: {len(tris)}")
