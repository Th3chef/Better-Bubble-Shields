"""Refresh game/ from the installed game and say whether a rebuild is needed (patch-proofing).

  python update.py <Helldivers 2 data folder> [hd2raw binary]

Finds every input by what it is (not by a stored id): each shield's archive from its device's unit name, the
particle effects that live only in that archive (generator glow + break effect), the materials and textures
those effects and devices use, then extracts them into game/ and compares with game/built_from.json.
Exit 0 = no update needed, 2 = inputs changed (run build_v7.py), 1 = needs a person.
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
EDGE_MATS = [0x4aa3db36d543a125, 0xff5ae79ce33fd342]
# ids found on the September 2026 build, only used to report what moved
KNOWN_FX = {'relay': ['438301bc21965f45', 'bdab1d123cb4b577'], 'grenade': ['2970dc9e5d8c665c', '3169d7e999299bae', 'b9121e86d3cdc226'],
            'pack': ['1cbc1844b252f92b', 'd0890b4b8276a347'], 'directional': ['7d8d944aad609c4e']}
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
    problems, inputs = [], {'fx': {}, 'fx_materials': [], 'luts': {}, 'bubble_units': [], 'edge_materials': []}
    devices = {}
    for key, uname in SHIELD_UNITS.items():
        uid = '%016x' % resource_hash(uname)
        if (uid, UNIT) not in rows: problems.append(f'{key}: device unit {uname} not found'); continue
        arch = rows[(uid, UNIT)]['arch']
        fx = sorted(i for (i, t), r in rows.items() if t == PARTICLES and len(r['arch']) <= 2 and set(r['arch']) & set(arch))
        if not fx: problems.append(f'{key}: no effects of its own found')
        if fx != KNOWN_FX[key]: print(f'{key}: effects moved: {KNOWN_FX[key]} -> {fx}')
        inputs['fx'][key] = fx; devices[key] = uid
    inputs['bubble_units'] = ['%016x' % u for u in BUBBLE_UNITS]; inputs['edge_materials'] = ['%016x' % e for e in EDGE_MATS]
    for u in inputs['bubble_units']:
        if (u, UNIT) not in rows: problems.append(f'bubble model {u} not found')
    if problems: raise Fail('\n  '.join(problems))
    get([(i, PARTICLES) for fx in inputs['fx'].values() for i in fx] + [(u, UNIT) for u in devices.values()]
        + [(u, UNIT) for u in inputs['bubble_units']] + [(m, MATERIAL) for m in inputs['edge_materials']])
    inputs['fx_materials'] = sorted({m for fx in inputs['fx'].values() for i in fx for m in refs(blob(i, PARTICLES), MATERIAL)})
    dev_mats = {key: [m for m in refs(blob(uid, UNIT), MATERIAL) if not rows[(m, MATERIAL)]['name'].startswith('content/art_shared/')]
                for key, uid in devices.items()}
    get([(m, MATERIAL) for m in inputs['fx_materials']] + [(m, MATERIAL) for ms in dev_mats.values() for m in ms])
    for key, ms in dev_mats.items():
        for m in ms:                  # the device's own material table (where its glowing parts get their colour)
            d = blob(m, MATERIAL); nt, = struct.unpack_from('<I', d, 64)
            keys = struct.unpack_from('<%dI' % nt, d, 136); ids = struct.unpack_from('<%dQ' % nt, d, 136 + 4 * nt)
            if LUT_SLOT in keys:
                lut = '%016x' % ids[keys.index(LUT_SLOT)]
                if len(rows[(lut, TEXTURE)]['arch']) == 1: inputs['luts'][key] = lut   # only ever touch a table the device owns alone
    get([(l, TEXTURE) for l in inputs['luts'].values()])
    g.close()
    files = sorted(f for f in os.listdir('game') if f.startswith('0x'))
    stamp = {f: hashlib.md5(open('game/' + f, 'rb').read()).hexdigest() for f in files}
    old = json.load(open('game/built_from.json')) if os.path.exists('game/built_from.json') else None
    json.dump(inputs, open('game/inputs.json', 'w'), indent=1)
    if old and old.get('inputs') == inputs and old.get('md5') == stamp:
        print('no update needed'); sys.exit(0)
    changed = sorted(set(stamp) ^ set((old or {}).get('md5', {})) | {f for f in stamp if (old or {}).get('md5', {}).get(f) != stamp[f]})
    print(f'inputs changed ({len(changed)} files), rebuild with build_v7.py:', changed[:20]); sys.exit(2)

if __name__ == '__main__':
    try: main()
    except Fail as e:
        print('NEEDS A PERSON:\n  ' + str(e)); sys.exit(1)
