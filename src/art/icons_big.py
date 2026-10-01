"""512x512 versions of the v7 option icons for the gallery cards (art/make_art.py reads art/big/).
Same drawing as icons_v7.py, drawn at 4x and scaled to 512."""
import os, sys, pathlib
HERE = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(HERE.parent))
import icons_v7 as ic
ic.S = 4; ic.W = 256 * ic.S
OUT = HERE / 'big'; OUT.mkdir(exist_ok=True)
STYLES = {'Honeycomb': 'honeycomb', 'Clear - Medium': 'clear_medium', 'Clear - Low': 'clear_low', 'Invisible': 'invisible'}
n = 0
for key in ('relay', 'grenade', 'directional', 'pack'):
    ic.icon(key, 'Clear - Medium', rainbow=True, size=512).save(OUT / f'{key}_rainbow.png', optimize=True); n += 1
    for style, slug in STYLES.items():
        ic.icon(key, style, size=512).save(OUT / f'{key}_{slug}.png', optimize=True); n += 1
    for color in ic.SHOW:
        ic.icon(key, 'Clear - Medium', color, size=512).save(OUT / f'{key}_color_{color.lower()}.png', optimize=True); n += 1
print(n, 'big icons')
