"""Better Bubble Shields v7 (formerly Clear Bubble Shields): per shield a Style dropdown and a separate Color dropdown.
v7: the Color option also recolors the generator glow, the bubble hit flash and the break effect.

How the two dropdowns stay independent (Arsenal can't merge two options into one file):
  Relay & G/SH-39, Directional: the Style option ships the shield's unit(s) re-pointed to our own
    material 'mods/clear_bubble_shields/<shield>/<style>' plus that material in the game's color.
    The Color option (listed after it, so it deploys later and wins) ships all three of our
    materials again in the chosen color. The game's own shield materials are no longer touched.
  Shield Generator Pack: the dome is a particle effect. The Style option ships the dome material
    (as in v5); the Color option ships the two dome particle files with their color keys changed.
  Color 'Default' just re-includes the shield's Textures folder (a no-op) since Include can't be empty.
  v7: each Color option also ships the device's own effect files (generator glow + break effect) recoloured, our
    recoloured copies of the coloured effect materials they use, the bubble's hit flash colour (ColorDamaged) and,
    on the G/SH-39, its glowing rows in the device's material table. Inputs come from update.py (game/).
"""
import json, os, shutil, struct, sys
from hd2_patch import resource_hash, read_archive, write_archive, MATERIAL, UNIT
from particles import systems, gradients

V5, GAME, OUT = 'v5-options', 'game', 'build'
VERSION = 'v7'
PARTICLES = 0xa8193123526fad64
TEXTURE = 0xcd4238c6a0c69e32
INPUTS = json.load(open('game/inputs.json'))   # written by update.py from the live game
PATCH = '9ba626afa44a3aa3.patch_0'
TEST = sys.argv[1] if len(sys.argv) > 1 else ''
TEST_GUID = 'c0d0b3a2-6e1f-4f7a-9a55-2b8e4c1d7f06'
LIVE_GUID = '6656e576-93de-4f5b-9568-29d5dba5d369'

names = {}
for l in open('shadervariables.txt'):
    p = l.split()
    if len(p) == 2:
        try: names[int(p[1], 16)] = p[0]
        except ValueError: pass
names[0x06776dda] = 'ShieldColor'   # also the particle 'color' channel hash; confirmed in game on the Relay (Test 1)

def material_vars(m):
    ntex, = struct.unpack_from('<I', m, 64); nv, = struct.unpack_from('<I', m, 104)
    o = 136 + 12 * ntex; recs = []
    for _ in range(nv):
        k, _e, vid, voff, _s = struct.unpack_from('<5I', m, o); recs.append((k, vid, voff)); o += 20
    return {names.get(vid, '%08x' % vid): (o + voff, k + 1) for k, vid, voff in recs if k < 4}

def get(m, v, n): a, c = v[n]; return struct.unpack_from('<%df' % c, m, a)
def put(m, v, n, vals): a, c = v[n]; assert len(vals) == c; struct.pack_into('<%df' % c, m, a, *vals)

COLORS = [  # name, normalized RGB (max channel 1)
    ('White',  (1.00, 1.00, 1.00)), ('Red', (1.00, 0.06, 0.04)), ('Orange', (1.00, 0.38, 0.03)),
    ('Yellow', (1.00, 0.85, 0.06)), ('Green', (0.12, 1.00, 0.18)), ('Cyan', (0.05, 0.85, 1.00)),
    ('Blue',   (0.08, 0.28, 1.00)), ('Purple', (0.55, 0.12, 1.00)), ('Pink', (1.00, 0.25, 0.65)),
    ('Dark',   None),   # smoky dark tint
]
STYLES = ['Honeycomb', 'Clear - Medium', 'Clear - Low']   # menu order (Honeycomb is the default), then Invisible
STYLE_TEXT = {
    'Clear - Medium': 'No honeycomb or cloud, just an even tint at 50% opacity so you can still tell where the shield is.',
    'Clear - Low': 'No honeycomb or cloud, a faint tint at 25% opacity.',
    'Honeycomb': 'Keeps the honeycomb but removes the swirling cloud and ripple, and is more see-through.',
    'Invisible': 'The bubble is completely invisible. The generator glow, hit flash and break effect stay (they follow the Color option).',
}
RELAY_MAT = 0xbf6c75e150316e2a
# 'bubble': the shield's bubble model, re-pointed to our own materials 'mods/clear_bubble_shields/<fam>/<style>'
#           built from the v5 materials in v5-options/<src>.
# Found in game (Test 5): model 0x274d... is the G/SH-39 grenade's bubble, 0xc6e9... is the Relay's dome.
# The Shield Generator Pack's bubble reuses one of those two models, so it follows that shield's settings;
# the Pack's own options drive its particle layers (glowing dome texture and the line along the top).
SHIELDS = [
    dict(folder='Relay', key='relay', short='Relay', textures='Relay and GSH-39',
         name='FX-12 Shield Generator Relay', desc='The deployable Shield Generator Relay dome.', colored='the bubble, its hit flash, the glow on the generator and the break effect',
         bubble=dict(units=[(0xc6e942a840ef3e09, 'c6e942a840ef3e09')], vanilla_mat=RELAY_MAT, src='Relay and GSH-39', fam='relay')),
    dict(folder='GSH-39 Shield', key='grenade', short='G/SH-39 Shield', textures='Relay and GSH-39',
         name='G/SH-39 Shield', desc='The bubble of the G/SH-39 Shield grenade.', colored='the bubble, its hit flash, the glow on the grenade and the break effect',
         bubble=dict(units=[(0x274d3f4191c8320c, '274d3f4191c8320c')], vanilla_mat=RELAY_MAT, src='Relay and GSH-39', fam='grenade')),
    dict(folder='Directional Shield', key='directional', short='Directional Shield', textures='Directional Shield',
         name='SH-51 Directional Shield', desc='The shield panel of the SH-51 Directional Shield backpack.', colored='the shield panel, its hit flash and the break effect',
         bubble=dict(units=[(resource_hash('content/fac_helldivers/equipment/backpacks/directional_energy_shield/directional_energy_shield'), 'b56fa3f5510000ab')],
                     vanilla_mat=0x9952274912730c5c, src='Directional Shield', fam='directional')),
    dict(folder='Shield Generator Pack', key='pack', short='Shield Generator Pack', textures='Shield Generator Pack',
         name='SH-32 Shield Generator Pack', desc="The SH-32 Shield Generator Pack's glowing dome layer and the line along its top.", colored='the dome, the glow on the backpack and the break effect',
         dome_mat=0xb97ca0894d4ac8ff,
         # the glowing line along the top of the Pack dome: two particle layers with their own materials
         edge_mats=[(0x4aa3db36d543a125, ('Emissive', 'MinEmissive')), (0xff5ae79ce33fd342, ('EmissiveIntensity', 'MinEmissive'))]),
]
slug = lambda s: s.lower().replace(' - ', '_').replace(' ', '_')

def v5_material(folder, style):
    ents = read_archive(f'{V5}/{folder}/{style}/{PATCH}')
    [m] = [e for e in ents if e['tid'] == MATERIAL]
    return bytearray(m['data'])

LUM = lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def matched(base, rgb):
    """rgb (max channel 1) scaled so it looks as bright as the game's colour 'base': at least the same peak
    channel and the same luminance (blue/purple need more than the peak to look as bright as amber)."""
    k = max(max(base), LUM(base) / LUM(rgb))
    return tuple(c * k for c in rgb)

def bubble_color(base, rgb):
    if rgb is None: return (0.035, 0.035, 0.04)
    return tuple(round(c, 4) for c in matched(base, rgb))

# Shield Pack dome particle systems: the dome itself (material b97c...) and the two edge layers
# (the bright line along the top of the dome; materials 4aa3... and ff5a...)
PACK_SYSTEM_MATERIALS = (0xb97ca0894d4ac8ff, 0x4aa3db36d543a125, 0xff5ae79ce33fd342)

def game(fid, tid, part='main'):
    """a vanilla game file as extracted by update.py"""
    fid = fid if isinstance(fid, str) else '%016x' % fid
    return open(f'{GAME}/0x{fid}.{tid:016x}.{part}', 'rb').read()

# ---- v7: generator glow, hit flash and break effect --------------------------------------------------------
# Tuning (only needs a look if the game changes how these effects are coloured):
SAT_MIN = 0.2          # colour keys / tints less saturated than this are white or grey highlights: left alone
FX_TINTS = ('Tint', 'Tint01', 'Tint02', 'ColorTint', 'ShieldColor')   # effect-material colour variables
LUT_EMISSIVE = 5.0     # device material table: rows with an emission strength (column 1 x) at least this glow
DARK = lambda base: (max(base) * 0.14, max(base) * 0.14, max(base) * 0.16)

def sat(c): return 0 if max(c) <= 0 else (max(c) - min(c)) / max(c)

def fx_color(base, rgb, limit=None):
    """the new colour for an effect key or tint: keeps the original's peak brightness and how white-hot it was
    (a pale yellow core becomes a pale blue core, a deep amber spark a deep blue one), then lifts it to the
    original's luminance so blue/purple don't look dimmer. limit = 255 for particle keys."""
    if rgb is None: new = DARK(base)
    else:
        V, s = max(base), sat(base)
        new = [V * (1 - s * (1 - t)) for t in rgb]
        new = [c * min(4.0, max(1.0, LUM(base) / max(LUM(new), 1e-6))) for c in new]
    if limit and max(new) > limit: new = [c * limit / max(new) for c in new]
    return tuple(new)

def recolor_particles(d, rgb):
    """every colour key in an effect file. Systems that draw the Pack dome or its edge keep the v6 recipe."""
    d = bytearray(d); sy, _ = systems(d); n = 0
    for s in sy:
        seg = d[s['start']:s['end']]
        dome = any(struct.pack('<Q', m) in seg for m in PACK_SYSTEM_MATERIALS)
        for off, times, keys in gradients(d, s['start'], s['end']):
            for i in range(len(times)):
                base = keys[i]
                if dome:
                    new = DARK(base) if rgb is None else matched(base, rgb)
                    over = max(new) / 255.0                    # particle colors are 0-255: scale down evenly, keep the hue
                    if over > 1: new = tuple(c / over for c in new)
                elif max(base) < 3 or sat(base) < SAT_MIN: continue
                else: new = fx_color(base, rgb, 255)
                struct.pack_into('<3f', d, off + 40 + 12 * i, *new); n += 1
    return d, n

def fx_material(mid, cname, rgb):
    """our own copy of an effect material with its colour tints changed (the game's material is shared with
    other effects, so it is never changed itself); None if it has no coloured tint"""
    m = bytearray(game(mid, MATERIAL)); v = material_vars(m); changed = []
    for name in FX_TINTS:
        if name in v and v[name][1] == 3 and sat(get(m, v, name)) >= SAT_MIN:
            put(m, v, name, fx_color(get(m, v, name), rgb)); changed.append(name)
    if not changed: return None, []
    return dict(fid=resource_hash(f'mods/clear_bubble_shields/fx/{slug(cname)}/{mid}'), tid=MATERIAL, data=bytes(m)), changed

def recolor_lut(key, rgb):
    """the device's material table (23x8 RGBA16F): recolour the glowing rows (strong emission, coloured)"""
    lut = INPUTS['luts'].get(key)
    if not lut: return None, 0
    import numpy as np
    gpu = bytearray(game(lut, TEXTURE, 'gpu')); a = np.frombuffer(bytes(gpu[:23 * 8 * 8]), '<f2').reshape(8, 23, 4).astype(np.float32)
    rows = [r for r in range(8) if a[r, 1, 0] >= LUT_EMISSIVE and sat(a[r, 0, :3]) >= SAT_MIN]
    if not rows: return None, 0
    for r in rows: a[r, 0, :3] = fx_color(tuple(a[r, 0, :3]), rgb, float(a[r, 0, :3].max()))   # never brighter than the game made it
    gpu[:23 * 8 * 8] = a.astype('<f2').tobytes()
    return dict(fid=int(lut, 16), tid=TEXTURE, data=game(lut, TEXTURE), gpu=bytes(gpu)), len(rows)

def fx_entries(key, cname, rgb):
    """the Color option's effect files: the device's own effects (found by update.py) with their colour keys
    changed and their coloured materials pointed at our recoloured copies, plus the device's glowing rows"""
    ents, log, mats = [], [], {}
    for pid in INPUTS['fx'][key]:
        d, n = recolor_particles(game(pid, PARTICLES), rgb)
        for mid in INPUTS['fx_materials']:
            old = struct.pack('<Q', int(mid, 16))
            spots = [o for o in range(0, len(d) - 7, 4) if d[o:o + 8] == old]   # references sit on 4-byte boundaries
            if not spots: continue
            assert len(spots) == bytes(d).count(old), f'{pid}: {mid} also matches outside a reference'
            if mid not in mats: mats[mid] = fx_material(mid, cname, rgb)
            ent, changed = mats[mid]
            if ent:
                for o in spots: struct.pack_into('<Q', d, o, ent['fid'])
        ents.append(dict(fid=int(pid, 16), tid=PARTICLES, data=bytes(d))); log.append((pid, n, 'keys'))
    for mid, (ent, changed) in sorted(mats.items()):
        if ent: ents.append(ent); log.append((mid, changed, 'copy'))
    lut, rows = recolor_lut(key, rgb)
    if lut: ents.append(lut); log.append((INPUTS['luts'][key], rows, 'glow rows'))
    assert any(x[1] for x in log if x[2] == 'keys'), f'{key}: no effect colour keys found'
    return ents, log

# brightness of the Pack's top line per style, relative to the game (follows the dome: v5 Intensity 8 / 2 / 5)
EDGE_SCALE = {'Clear - Medium': 1.0, 'Clear - Low': 0.5, 'Honeycomb': 1.0, 'Invisible': 0.0}

# Bubble opacity per style (tested in game: Medium 50%, Low 25%; Honeycomb 20%).
OPACITY = {'Honeycomb': 0.2, 'Clear - Medium': 0.5, 'Clear - Low': 0.25, 'Invisible': 0.0}
# Shield Pack glowing layer per style. Clear - Low is built from the Clear - Medium material at half brightness
# (Medium 50% / Low 25%). Honeycomb: Test 6 values (full dome brightness, 2.5x stronger honeycomb) were right.
PACK = {'Honeycomb': dict(Intensity=8.0, Tex02Intensity=1.5), 'Clear - Medium': dict(Intensity=10.0),
        'Clear - Low': dict(Intensity=5.0), 'Invisible': dict(Intensity=0.0, MinEmissive=0.0)}
PACK_SOURCE = {'Honeycomb': 'Honeycomb', 'Clear - Medium': 'Clear - Medium', 'Clear - Low': 'Clear - Medium', 'Invisible': 'Clear - Medium'}

def tune(style, m, v):
    """bubble materials: set the style's opacity"""
    put(m, v, 'OpacityMult', (OPACITY[style],))

def write(folder, entries):
    os.makedirs(folder, exist_ok=True)
    write_archive(f'{folder}/{PATCH}', entries, header_from=f'{V5}/Relay and GSH-39/Clear - Medium/{PATCH}')

def build():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(f'{OUT}/images')
    from PIL import Image                                       # Arsenal shows it small: ship 512x512 (art/make_art.py makes the 1254 art)
    Image.open('thumbnail.png').convert('RGB').resize((512, 512), Image.LANCZOS).save(f'{OUT}/thumbnail.png', optimize=True)
    options, log = [], []
    for sh in SHIELDS:
        F, key = sh['folder'], sh['key']
        shutil.copytree(f"{V5}/{sh['textures']}/Textures", f'{OUT}/{F}/Textures')
        style_subs, color_subs = [], []
        for style in STYLES + ['Invisible']:
            src = 'Clear - Low' if style == 'Invisible' else style
            bub = sh.get('bubble'); ents = []
            for uid, fname in (bub['units'] if bub else []):
                m = v5_material(bub['src'], src); v = material_vars(m); tune(style, m, v)
                if style == 'Invisible': put(m, v, 'OpacityMult', (0.0,))
                mid = resource_hash(f"mods/clear_bubble_shields/{bub['fam']}/{slug(style)}")
                ents.append(dict(fid=mid, tid=MATERIAL, data=bytes(m)))
                main = bytearray(game(fname, UNIT))
                old = struct.pack('<Q', bub['vanilla_mat']); assert main.count(old) == 1
                main[main.find(old):main.find(old) + 8] = struct.pack('<Q', mid)
                ents.append(dict(fid=uid, tid=UNIT, data=bytes(main), gpu=game(fname, UNIT, 'gpu')))
            if 'dome_mat' in sh:          # the Pack's particle dome layer (v5 Pack material)
                m = v5_material(F, PACK_SOURCE[style]); v = material_vars(m)
                for name, value in PACK[style].items(): put(m, v, name, (value,))
                ents.append(dict(fid=sh['dome_mat'], tid=MATERIAL, data=bytes(m)))
            for eid, vars_ in sh.get('edge_mats', []):
                m = bytearray(game(eid, MATERIAL)); v = material_vars(m)
                for name in vars_: put(m, v, name, tuple(x * EDGE_SCALE[style] for x in get(m, v, name)))
                ents.append(dict(fid=eid, tid=MATERIAL, data=bytes(m)))
            write(f'{OUT}/{F}/Style/{style}', ents)
            style_subs.append({'Name': style, 'Description': STYLE_TEXT[style],
                               'Image': f'images/{key}_style_{slug(style)}.png', 'Include': [f'{F}/Style/{style}']})
        color_subs.append({'Name': 'Default', 'Description': "The game's own color.",
                            'Image': f'images/{key}_color_default.png', 'Include': [f'{F}/Textures']})
        for cname, rgb in COLORS:
            ents = []; bub = sh.get('bubble')
            for style in (STYLES if bub else []):
                m = v5_material(bub['src'], style); v = material_vars(m); tune(style, m, v)
                put(m, v, 'ShieldColor', bubble_color(get(m, v, 'ShieldColor'), rgb))
                put(m, v, 'ColorDamaged', bubble_color(get(m, v, 'ColorDamaged'), rgb))   # hit flash (v7)
                ents.append(dict(fid=resource_hash(f"mods/clear_bubble_shields/{bub['fam']}/{slug(style)}"), tid=MATERIAL, data=bytes(m)))
            fx_ents, fx_log = fx_entries(key, cname, rgb)
            ents += fx_ents; log += [(F, cname) + x for x in fx_log]
            write(f'{OUT}/{F}/Color/{cname}', ents)
            color_subs.append({'Name': cname, 'Description': f'{cname} shield' + (' (a smoky dark tint).' if rgb is None else '.'),
                                'Image': f'images/{key}_color_{slug(cname)}.png', 'Include': [f'{F}/Color/{cname}']})
        options.append({'Name': sh['name'], 'Description': sh['desc'] + ' Pick the style here and the color in the next option.',
                        'Image': f'images/{key}.png', 'Include': [f'{F}/Textures'], 'SubOptions': style_subs})
        options.append({'Name': f'{sh["short"]} - Color',
                        'Description': f'Color of the {sh["short"]}: {sh["colored"]}. Works with any style; needs the {sh["short"]} option above turned on.',
                        'Image': f'images/{key}_color.png', 'SubOptions': color_subs})
    name = f'Better Bubble Shields - {VERSION}' + (f' Test {TEST}' if TEST else '')
    man = {'Version': 1, 'Guid': TEST_GUID if TEST else LIVE_GUID, 'Name': name,
           'Description': ("Every bubble shield your way (formerly Clear Bubble Shields). For each shield, pick a style: Honeycomb "
               "(keeps the honeycomb, no swirling cloud or ripple), Clear - Medium (50%), Clear - Low (25%) or Invisible; and, in its "
               "own dropdown, a color: the game's own, White, Red, Orange, Yellow, Green, Cyan, Blue, Purple, Pink or Dark. "
               "The color also covers the generator glow, the hit flash and the break effect. Turn a shield off to keep it vanilla. Covers the FX-12 Shield Generator Relay, G/SH-39 Shield, SH-51 Directional Shield "
               "and SH-32 Shield Generator Pack. Built for the September 2026 game version; after a game update "
               "that changes these shields the mod is rebuilt from the new game files. Inspired by Muchacho5894's 'Bubble Shields - No honeycomb - No cloud "
               "- 0.1 Opacity' (Nexus mod 14108); this mod uses its own textures."),
           'IconPath': 'thumbnail.png', 'Options': options}
    json.dump(man, open(f'{OUT}/manifest.json', 'w'), indent=2)
    # stamp: which game files this build used (update.py compares against it after a game patch)
    import hashlib
    files = sorted(f for f in os.listdir(GAME) if f.startswith('0x'))
    json.dump({'inputs': INPUTS, 'md5': {f: hashlib.md5(open(f'{GAME}/{f}', 'rb').read()).hexdigest() for f in files}},
              open(f'{GAME}/built_from.json', 'w'), indent=1)
    return man, log

if __name__ == '__main__':
    man, log = build()
    for l in log[:4]: print(l)
    print(len(man['Options']), 'options:', [ (o['Name'], len(o['SubOptions'])) for o in man['Options']])
