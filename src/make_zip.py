"""Zip build/ into the Arsenal mod zip, reproducibly: entries sorted by name, every date 1980-01-01 00:00, fixed
permissions (files 644, folders 755), one compression setting (deflate, level 9). The same build/ always gives the
same zip bytes (with the same zlib).

  python make_zip.py [out.zip]     default: the name in build/manifest.json, e.g. Better-Bubble-Shields-v8.zip
"""
import json, os, sys, zipfile

BUILD = 'build'
DATE = (1980, 1, 1, 0, 0, 0)

def zip_name():
    name = json.load(open(f'{BUILD}/manifest.json'))['Name']          # 'Better Bubble Shields - v8 Test 1'
    return name.replace(' - ', ' ').replace(' ', '-') + '.zip'        # 'Better-Bubble-Shields-v8-Test-1.zip'

def entry(name, is_dir):
    zi = zipfile.ZipInfo(name, DATE)
    zi.create_system = 3                                              # Unix, so the permission bits are used
    if is_dir:
        zi.external_attr = (0o40755 << 16) | 0x10; zi.compress_type = zipfile.ZIP_STORED
    else:
        zi.external_attr = 0o100644 << 16; zi.compress_type = zipfile.ZIP_DEFLATED
    return zi

def make_zip(out):
    names = []
    for root, dirs, files in os.walk(BUILD):
        rel = os.path.relpath(root, BUILD).replace(os.sep, '/')
        if rel != '.': names.append((rel + '/', True))
        names += [((f if rel == '.' else f'{rel}/{f}'), False) for f in files]
    if os.path.abspath(out).startswith(os.path.abspath(BUILD) + os.sep): sys.exit('write the zip outside build/')
    with zipfile.ZipFile(out, 'w') as z:
        for name, is_dir in sorted(names):
            data = b'' if is_dir else open(os.path.join(BUILD, name), 'rb').read()
            z.writestr(entry(name, is_dir), data, compresslevel=None if is_dir else 9)
    return out, len(names)

if __name__ == '__main__':
    out, n = make_zip(sys.argv[1] if len(sys.argv) > 1 else zip_name())
    print(out, n, 'entries')
