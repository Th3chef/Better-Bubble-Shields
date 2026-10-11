import struct
S = 10000.0

def systems(d):
    """the particle systems of an effect file: a count at 24, then from 80 one record per system whose size sits at
    +256. Raises ValueError when the counts and sizes don't add up to the file (the format changed)."""
    if len(d) < 80: raise ValueError(f'only {len(d)} bytes: too short for an effect file')
    ns, = struct.unpack_from('<I', d, 24)
    o = 80; out = []
    for i in range(ns):
        if o + 260 > len(d): raise ValueError(f'system {i} of {ns} starts at {o}, past the end of the file ({len(d)} bytes)')
        size, = struct.unpack_from('<I', d, o + 256)
        if size == 0 or o + size > len(d): raise ValueError(f'system {i} of {ns} at {o} has size {size} (file {len(d)} bytes)')
        out.append(dict(start=o, end=o + size))
        o += size
    if o != len(d): raise ValueError(f'{ns} systems end at {o}, but the file has {len(d)} bytes')
    return out, o

def gradients(d, a, b):
    """color gradients: 10 key times (0..1, padded with 10000) followed by 10 RGB float triples in 0..255"""
    res = []
    o = a
    while o + 160 <= b:
        t = struct.unpack_from('<10f', d, o)
        if all((0 <= x <= 1.0001) or x == S for x in t) and S in t and all(x == S for x in t[t.index(S):]) and t.index(S) >= 1:
            rgb = struct.unpack_from('<30f', d, o + 40)
            k = t.index(S)
            if all(0 <= x <= 255.001 for x in rgb) and any(x > 1.5 for x in rgb[:3 * k]):
                res.append((o, t[:k], [rgb[3 * i:3 * i + 3] for i in range(10)]))
                o += 160; continue
        o += 4
    return res
