"""Refresh game/ from the installed game and say whether a rebuild is needed (patch-proofing).

  python update.py <Helldivers 2 data folder> [hd2raw binary]

Finds every input by what it is (not by a stored id): each shield's archive from its device's unit name, the
particle effects that live only in that archive (generator glow + break effect), the materials and textures
those effects and devices use, and the game materials each style starts from (the bubble model's material on the
bubble shader, the Pack effect's material on the dome shader), then extracts them into game/ and compares with
game/built_from.json. Exit 0 = no update needed, 2 = inputs changed (run build_v7.py), 1 = needs a person.
hd2raw: tools/hd2raw (Go, built on Filediver's reader; see tools/hd2raw/README.txt). It reads the game's file
table once and answers every request in that one session.
"""
import hashlib, json, os, struct, subprocess, sys
from hd2_patch import resource_hash

MATERIAL, UNIT, PARTICLES, TEXTURE = 'eac0b497876adedf', 'e0a48d0be9a7453f', 'a8193123526fad64', 'cd4238c6a0c69e32'
BASE = 'content/fac_helldivers/'
SHIELD_UNITS = {   # the shield's device; its archive holds the device's own effects
    'relay': BASE + 'hellpod/energy_shield/energy_shield',
    'grenade': BASE + 'equipment/throwables/energy_shield_grenade/energy_shield_grenade',
    'pack': BASE + 'equipment/backpacks/energy_shield_backpack/energy_shield_backpack',
    'directional': BASE + 'equipment/backpacks/directional_energy_shield/directional_energy_shield_backpack',
}
# bubble models re-pointed by the Style options (v6) + the Pack's dome edge materials (v5)
BUBBLE_UNITS = [0xc6e942a840ef3e09, 0x274d3f4191c8320c, resource_hash(BASE + 'equipment/backpacks/directional_energy_shield/directional_energy_shield')]
BUBBLE_OF = {'relay': 0, 'grenade': 1, 'directional': 2}   # index into BUBBLE_UNITS
EDGE_MATS = [0x4aa3db36d543a125, 0xff5ae79ce33fd342]
BUBBLE_SHADER, DOME_SHADER = 0x717b4e0431528b44, 0xc9373e9ef86d372c
# ids found on the September 2026 build, only used to report what moved
KNOWN_FX = {'relay': ['438301bc21965f45', 'bdab1d123cb4b577'], 'grenade': ['2970dc9e5d8c665c', '3169d7e999299bae', 'b9121e86d3cdc226'],
            'pack': ['1cbc1844b252f92b', 'd0890b4b8276a347'], 'directional': ['7d8d944aad609c4e']}
KNOWN_BASES = {'relay': 'bf6c75e150316e2a', 'grenade': 'bf6c75e150316e2a', 'directional': '9952274912730c5c', 'pack': 'b97ca0894d4ac8ff'}
KNOWN_LUTS = {'grenade': 'f35e8d0bf947897a'}   # the device material tables the build recolors (glowing rows)
LUT_SLOT = 0x7e662968        # device material: per-region material table (23x8 RGBA16F)

class Fail(Exception): pass

class Game:
    """one hd2raw session: the game's file table is read once"""
    def __init__(self, tool, data):
        self.p = subprocess.Popen([tool, data, 'serve'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        if self.p.stdout.readline().strip() != 'ready': raise Fail('hd2raw could not read the game data folder')
    def cmd(self, *args):
        self.p.stdin.write(' '.join(args) + '\n'); self.p.stdin.flush()
        ans = self.p.stdout.readline().strip()
        if not ans.startswith('ok'): raise Fail(f'hd2raw {args[0]}: {ans or "stopped"}')
    def close(self):
        self.p.stdin.close(); self.p.wait()

def main():
    data = sys.argv[1]; tool = sys.argv[2] if len(sys.argv) > 2 else 'tools/hd2raw/hd2raw'
    os.makedirs('game', exist_ok=True)
    for f in os.listdir('game'):        # start clean so game/ only holds what this game version needs
        if f.startswith('0x'): os.remove('game/' + f)
    g = Game(tool, data)
    g.cmd('index', 'game/index.tsv')
    rows = {}
    for l in open('game/index.tsv'):
        p = l.rstrip('\n').split('\t'); rows[(p[0], p[1])] = dict(name=p[2], arch=p[7].split(','))
    def get(ids):
        ids = sorted(set(ids))
        if ids: g.cmd('get', 'game', *['%s.%s' % i for i in ids])
        for i, t in ids:
            if not os.path.exists('game/0x%s.%s.main' % (i, t)): raise Fail(f'{i}.{t} did not come out of the game')
    def blob(i, t, part='main'):
        return open('game/0x%s.%s.%s' % (i, t, part), 'rb').read()
    def refs(d, kind):   # u64 ids of that type referenced anywhere in d (references sit on 4-byte boundaries)
        out = []
        for o in range(0, len(d) - 7, 4):
            v = '%016x' % struct.unpack_from('<Q', d, o)[0]
            if (v, kind) in rows and v not in out: out.append(v)
        return out
    def parent(m): return struct.unpack_from('<Q', blob(m, MATERIAL), 24)[0]
    problems, inputs = [], {'fx': {}, 'fx_materials': [], 'luts': {}, 'bubble_units': [], 'edge_materials': [], 'base_materials': {}}
    devices = {}
    for key, uname in SHIELD_UNITS.items():
        uid = '%016x' % resource_hash(uname)
        if (uid, UNIT) not in rows: problems.append(f'{key}: device unit {uname} not found'); continue
        arch = set(rows[(uid, UNIT)]['arch'])
        # the device's own effects: particle files that live only in the device's archive(s)
        fx = sorted(i for (i, t), r in rows.items() if t == PARTICLES and set(r['arch']) <= arch)
        # v7 used a looser rule (in the device's archive and at most one more); keep any effect v7 shipped that the
        # strict rule drops, and say so, so a hotfix can't silently drop an effect from the Color option
        kept = sorted(i for (i, t), r in rows.items() if t == PARTICLES and i in KNOWN_FX[key] and i not in fx
                      and len(r['arch']) <= 2 and set(r['arch']) & arch)
        if kept:
            print(f'WARNING {key}: {kept} also live in another archive ' +
                  str(sorted({a for i in kept for a in rows[(i, PARTICLES)]['arch']} - arch)) + '; kept as in v7: check they are only this device\'s effects')
            fx = sorted(fx + kept)
        if not fx: problems.append(f'{key}: no effects of its own found')
        if fx != KNOWN_FX[key]: print(f'{key}: effects moved: {KNOWN_FX[key]} -> {fx}')
        inputs['fx'][key] = fx; devices[key] = uid
    seen = {}
    for key, fx in inputs['fx'].items():   # the four lists must not overlap (one effect file in two Color options)
        for i in fx:
            if i in seen: problems.append(f'effect {i} found for both {seen[i]} and {key}')
            seen[i] = key
    inputs['bubble_units'] = ['%016x' % u for u in BUBBLE_UNITS]; inputs['edge_materials'] = ['%016x' % e for e in EDGE_MATS]
    for u in inputs['bubble_units']:
        if (u, UNIT) not in rows: problems.append(f'bubble model {u} not found')
    if problems: raise Fail('\n  '.join(problems))
    get([(i, PARTICLES) for fx in inputs['fx'].values() for i in fx] + [(u, UNIT) for u in devices.values()]
        + [(u, UNIT) for u in inputs['bubble_units']] + [(m, MATERIAL) for m in inputs['edge_materials']])
    inputs['fx_materials'] = sorted({m for fx in inputs['fx'].values() for i in fx for m in refs(blob(i, PARTICLES), MATERIAL)})
    dev_mats = {key: [m for m in refs(blob(uid, UNIT), MATERIAL) if not rows[(m, MATERIAL)]['name'].startswith('content/art_shared/')]
                for key, uid in devices.items()}
    bub_mats = {key: refs(blob(inputs['bubble_units'][i], UNIT), MATERIAL) for key, i in BUBBLE_OF.items()}
    get([(m, MATERIAL) for m in inputs['fx_materials']] + [(m, MATERIAL) for ms in dev_mats.values() for m in ms]
        + [(m, MATERIAL) for ms in bub_mats.values() for m in ms])
    # the game materials each style starts from (v7.0.1): the bubble model's one material on the bubble shader, and
    # the one material on the dome shader among the Pack's own effects
    bases = {key: [m for m in ms if parent(m) == BUBBLE_SHADER] for key, ms in bub_mats.items()}
    pack_mats = {m for i in inputs['fx']['pack'] for m in refs(blob(i, PARTICLES), MATERIAL)}
    bases['pack'] = sorted(m for m in pack_mats if parent(m) == DOME_SHADER)
    for key, found in bases.items():
        if len(found) != 1: problems.append(f'{key}: expected one style base material, found {found or "none"}'); continue
        inputs['base_materials'][key] = found[0]
        if found[0] != KNOWN_BASES[key]: print(f'{key}: style base material moved: {KNOWN_BASES[key]} -> {found[0]}')
    for key, ms in dev_mats.items():
        luts = []                      # the device's own material table (where its glowing parts get their color)
        for m in ms:
            d = blob(m, MATERIAL); nt, = struct.unpack_from('<I', d, 64)
            keys = struct.unpack_from('<%dI' % nt, d, 136); ids = struct.unpack_from('<%dQ' % nt, d, 136 + 4 * nt)
            if LUT_SLOT in keys:
                lut = '%016x' % ids[keys.index(LUT_SLOT)]
                if lut not in luts: luts.append(lut)
        if len(luts) > 1: problems.append(f'{key}: {len(luts)} device material tables found ({", ".join(luts)}), expected one'); continue
        own = [l for l in luts if len(rows[(l, TEXTURE)]['arch']) == 1]   # only ever touch a table the device owns alone
        if luts and not own: print(f'{key}: device material table {luts[0]} is shared with other archives: left alone')
        if key in KNOWN_LUTS:
            if not own: problems.append(f'{key}: its device material table (was {KNOWN_LUTS[key]}) is gone or now shared with other things'); continue
            if own[0] != KNOWN_LUTS[key]: print(f'{key}: device material table moved: {KNOWN_LUTS[key]} -> {own[0]}')
        if own: inputs['luts'][key] = own[0]
    if problems: raise Fail('\n  '.join(problems))
    get([(l, TEXTURE) for l in inputs['luts'].values()] + [(m, MATERIAL) for m in inputs['base_materials'].values()])
    # the Pack Style option changes the dome and edge materials in place (a particle effect can only be pointed at
    # them by shipping the effect): check nothing but the Pack's own effects uses them
    pack_only = [inputs['base_materials']['pack']] + inputs['edge_materials']
    g.cmd('grep', PARTICLES, ','.join(struct.pack('<Q', int(m, 16)).hex() for m in pack_only), 'game/pack_refs_fx.tsv')
    g.cmd('grep', UNIT, ','.join(struct.pack('<Q', int(m, 16)).hex() for m in pack_only), 'game/pack_refs_units.tsv')
    others = []
    for f, kind in (('game/pack_refs_fx.tsv', 'effect'), ('game/pack_refs_units.tsv', 'unit')):
        for l in open(f):
            p = l.rstrip('\n').split('\t')
            if kind == 'effect' and p[0] in inputs['fx']['pack']: continue
            others.append(f'{kind} {p[0]} {p[1]} uses {pack_only[int(p[2][3:])]}')
    g.close()
    if others: raise Fail('the Shield Pack materials the Style option changes are used outside the Pack:\n  ' + '\n  '.join(others))
    files = sorted(f for f in os.listdir('game') if f.startswith('0x'))
    stamp = {f: hashlib.md5(open('game/' + f, 'rb').read()).hexdigest() for f in files}
    old = json.load(open('game/built_from.json')) if os.path.exists('game/built_from.json') else None
    json.dump(inputs, open('game/inputs.json', 'w'), indent=1)
    if old and old.get('inputs') == inputs and old.get('md5') == stamp:
        print('no update needed'); sys.exit(0)
    changed = sorted(set(stamp) ^ set((old or {}).get('md5', {})) | {f for f in stamp if (old or {}).get('md5', {}).get(f) != stamp[f]})
    found = ' and in what update.py found' if old and old.get('inputs') != inputs else ''
    print(f'inputs changed ({len(changed)} files{found}), rebuild with build_v7.py:', changed[:20]); sys.exit(2)

if __name__ == '__main__':
    try: main()
    except Fail as e:
        print('NEEDS A PERSON:\n  ' + str(e)); sys.exit(1)
