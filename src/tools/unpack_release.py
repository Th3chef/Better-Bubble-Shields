"""Recreate v5-options/ (the bubble/dome materials each style starts from, and the mod's own 1x1 textures) from a
release zip, so the repository doesn't have to store game-derived materials.

  python tools/unpack_release.py Better-Bubble-Shields-v7.zip

build_v7.py only changes OpacityMult / the Pack dome brightness / the colours on top of these, so the materials
taken from any v6 or newer release rebuild that release byte for byte.
"""
import io, os, sys, zipfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from hd2_patch import MATERIAL, resource_hash, read_archive, write_archive

PATCH = '9ba626afa44a3aa3.patch_0'
OUT = 'v5-options'
# v5-options/<folder>/<style> <- release <shield folder>/Style/<style>: the one material the build starts from
BASES = {
    'Relay and GSH-39': ('Relay', 'relay', ['Honeycomb', 'Clear - Medium', 'Clear - Low']),
    'Directional Shield': ('Directional Shield', 'directional', ['Honeycomb', 'Clear - Medium', 'Clear - Low']),
    'Shield Generator Pack': ('Shield Generator Pack', None, ['Honeycomb', 'Clear - Medium']),
}
PACK_DOME = 0xb97ca0894d4ac8ff
TEXTURES = {'Relay and GSH-39': 'Relay', 'Directional Shield': 'Directional Shield', 'Shield Generator Pack': 'Shield Generator Pack'}
slug = lambda s: s.lower().replace(' - ', '_').replace(' ', '_')

def main(zip_path):
    z = zipfile.ZipFile(zip_path)
    def extract_set(src_dir, dst_dir):
        os.makedirs(dst_dir, exist_ok=True)
        for ext in ('', '.gpu_resources', '.stream'):
            with open(os.path.join(dst_dir, PATCH + ext), 'wb') as f: f.write(z.read(f'{src_dir}/{PATCH}{ext}'))
    for folder, src in TEXTURES.items():
        extract_set(f'{src}/Textures', f'{OUT}/{folder}/Textures')
    for folder, (shield, fam, styles) in BASES.items():
        for style in styles:
            tmp = f'{OUT}/_tmp'; extract_set(f'{shield}/Style/{style}', tmp)
            ents = read_archive(f'{tmp}/{PATCH}')
            want = PACK_DOME if fam is None else resource_hash(f'mods/clear_bubble_shields/{fam}/{slug(style)}')
            [m] = [e for e in ents if e['tid'] == MATERIAL and e['fid'] == want]
            os.makedirs(f'{OUT}/{folder}/{style}', exist_ok=True)
            write_archive(f'{OUT}/{folder}/{style}/{PATCH}', [m], header_from=f'{tmp}/{PATCH}')
            for ext in ('', '.gpu_resources', '.stream'): os.remove(f'{tmp}/{PATCH}{ext}')
            os.rmdir(tmp)
    print('v5-options recreated from', os.path.basename(zip_path))

if __name__ == '__main__':
    main(sys.argv[1])
