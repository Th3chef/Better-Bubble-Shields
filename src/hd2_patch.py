import struct
MATERIAL, TEXTURE, UNIT, MAGIC = 0xeac0b497876adedf, 0xcd4238c6a0c69e32, 0xe0a48d0be9a7453f, 0xF0000011

def resource_hash(name):
    data = name.encode('utf-8'); mask, mix = (1 << 64) - 1, 0xC6A4A7935BD1E995
    value = len(data) * mix & mask; end = len(data) // 8 * 8
    for (word,) in struct.iter_unpack('<Q', data[:end]):
        word = word * mix & mask; word ^= word >> 47
        value = (value ^ (word * mix & mask)) * mix & mask
    if data[end:]:
        value = (value ^ int.from_bytes(data[end:], 'little')) * mix & mask
    value ^= value >> 47; value = value * mix & mask; value ^= value >> 47
    return value

def thin_hash(name):
    return resource_hash(name) >> 32

def read_archive(path):
    d = open(path, 'rb').read()
    try: g = open(path + '.gpu_resources', 'rb').read()
    except FileNotFoundError: g = b''
    try: s = open(path + '.stream', 'rb').read()
    except FileNotFoundError: s = b''
    magic, nt, n = struct.unpack_from('<III', d, 0); assert magic == MAGIC, hex(magic)
    out = []
    for i in range(n):
        fid, tid, off, soff, goff, _, _, size, ssize, gsize, _, _, _ = struct.unpack_from('<7Q6I', d, 72 + 32 * nt + 80 * i)
        out.append(dict(fid=fid, tid=tid, data=d[off:off + size], gpu=g[goff:goff + gsize], stream=s[soff:soff + ssize]))
    return out

DEFAULT_HEADER = bytes.fromhex('00000000ce09f5f400000000a05345216b807fe000af620300000000008f660000000000000000000000000000000000000000000000000000000000')

def write_archive(path, entries, header_from=None):
    hdr = open(header_from, 'rb').read()[12:72] if header_from else DEFAULT_HEADER
    unknown, unk56 = struct.unpack_from('<I', hdr, 0)[0], hdr[4:60]
    order = [MATERIAL, TEXTURE, UNIT]
    types = sorted({e['tid'] for e in entries}, key=lambda t: order.index(t) if t in order else 9)
    ents = sorted(entries, key=lambda e: types.index(e['tid']))
    head = struct.pack('<IIII', MAGIC, len(types), len(ents), unknown) + unk56
    for t in types: head += struct.pack('<QQQII', 0, t, sum(e['tid'] == t for e in ents), 16, 64)
    cursor = len(head) + 80 * len(ents); rows = body = b''; gpu = bytearray()
    for i, e in enumerate(ents, 1):
        goff = 0
        if e.get('gpu'):
            gpu += b'\0' * (-len(gpu) % 64); goff = len(gpu); gpu += e['gpu']
        rows += struct.pack('<7Q6I', e['fid'], e['tid'], cursor, 0, goff, 0, 0, len(e['data']), 0, len(e.get('gpu', b'')), 16, 64, i)
        body += e['data']; cursor += len(e['data'])
    toc = head + rows + body; toc += b'\0' * max(0, 256 * len(ents) - len(toc))
    open(path, 'wb').write(toc)
    open(path + '.gpu_resources', 'wb').write(bytes(gpu))
    open(path + '.stream', 'wb').write(b'')
