import struct
S = 10000.0
def systems(d):
    ns, = struct.unpack_from('<I', d, 24)
    o = 80; out = []
    for i in range(ns):
        maxp, nc = struct.unpack_from('<II', d, o)
        unk3, = struct.unpack_from('<I', d, o + 76)
        clo, cls, off3, size = [struct.unpack_from('<I', d, o + k)[0] for k in (232, 240, 252, 256)]
        out.append(dict(start=o, end=o + size, maxp=maxp, nc=nc, render=unk3 != 0xffffffff))
        o += size
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
