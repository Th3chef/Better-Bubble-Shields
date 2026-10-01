"""v7 Arsenal icons (256x256; art/icons_big.py draws the same at 512 for the gallery art): per shield the style
icons (game color), the color icons (Clear - Medium in that color, with the generator glow in that color too), the
shield option icon and a rainbow icon for the color option. Directional Shield = sideways oval."""
import math, json
from PIL import Image, ImageDraw, ImageFilter, ImageChops
S = 2; W = 256 * S
SHOW = {'Default': (226, 172, 58), 'White': (235, 235, 235), 'Red': (225, 45, 40), 'Orange': (240, 120, 30),
        'Yellow': (245, 220, 50), 'Green': (60, 210, 80), 'Cyan': (50, 205, 230), 'Blue': (55, 105, 240),
        'Purple': (150, 70, 235), 'Pink': (240, 95, 175), 'Dark': (38, 38, 44)}
RAINBOW = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Pink']
P = lambda *v: [x * S for x in v]

def background():
    im = Image.new('RGB', (W, W)); d = ImageDraw.Draw(im)
    for y in range(W):
        t = y / (227 * S)
        d.line([(0, y), (W, y)], fill=(int(20 + 12 * t), int(24 + 14 * t), int(18 + 10 * t)) if y < 227 * S else (33, 40, 27))
    blobs = Image.new('RGBA', (W, W), (0, 0, 0, 0)); b = ImageDraw.Draw(blobs)
    for (x, y, rx, ry, c) in [(58, 105, 18, 6, (70, 58, 45)), (212, 127, 19, 7, (45, 70, 40)), (57, 158, 24, 8, (90, 80, 55)),
                              (185, 181, 36, 11, (75, 90, 55)), (126, 222, 46, 10, (50, 45, 35))]:
        b.ellipse(P(x - rx, y - ry, x + rx, y + ry), fill=c + (170,))
    blobs = blobs.filter(ImageFilter.GaussianBlur(3 * S)); im.paste(blobs, (0, 0), blobs)
    return im

def helldiver(d, cx, base, scale=1.0, pack=False):
    s = lambda v: v * scale
    body, dark, visor = (52, 54, 50), (36, 38, 35), (60, 64, 58)
    d.rounded_rectangle(P(cx - s(9), base - s(22), cx - s(2), base), radius=2 * S, fill=dark)       # legs
    d.rounded_rectangle(P(cx + s(2), base - s(22), cx + s(9), base), radius=2 * S, fill=dark)
    d.rounded_rectangle(P(cx - s(14), base - s(52), cx + s(14), base - s(20)), radius=6 * S, fill=body)  # torso
    d.ellipse(P(cx - s(10), base - s(72), cx + s(10), base - s(52)), fill=visor)                     # helmet
    d.rounded_rectangle(P(cx - s(20), base - s(50), cx - s(13), base - s(28)), radius=3 * S, fill=body)  # arms
    d.rounded_rectangle(P(cx + s(13), base - s(50), cx + s(20), base - s(28)), radius=3 * S, fill=body)
    if pack:
        d.rounded_rectangle(P(cx - s(12), base - s(54), cx + s(12), base - s(26)), radius=4 * S, fill=(92, 86, 70), outline=(55, 52, 44), width=2 * S)
        d.ellipse(P(cx - s(5), base - s(49), cx + s(5), base - s(39)), fill=(255, 214, 20))

def device(im, key, glow=(255, 214, 20)):
    d = ImageDraw.Draw(im)
    if key == 'relay':
        d.rectangle(P(113, 197, 143, 227), fill=(112, 102, 74), outline=(70, 64, 48), width=S)
        d.rectangle(P(122, 185, 134, 197), fill=(96, 88, 64))
        d.ellipse(P(121, 174, 135, 188), fill=glow)
    elif key == 'grenade':   # a small shield grenade lying on the ground
        d.rounded_rectangle(P(116, 206, 140, 226), radius=5 * S, fill=(92, 96, 88), outline=(60, 62, 58), width=S)
        d.rectangle(P(116, 213, 140, 217), fill=glow)
        d.ellipse(P(123, 198, 133, 208), fill=glow)
    elif key == 'pack':      # the old Directional icon: pole with a light under a curved band
        d.polygon(P(122, 190, 134, 190, 137, 240, 119, 240), fill=(62, 62, 64))
        d.ellipse(P(121, 175, 135, 189), fill=glow)
    else:
        helldiver(d, 128, 252, 2.1, pack=True)

def mask(key, rim=False):
    m = Image.new('L', (W, W), 0); d = ImageDraw.Draw(m)
    if key == 'directional':
        d.ellipse(P(22, 78, 234, 190), fill=255)            # sideways oval in front of the helldiver
    elif key == 'pack':
        box = lambda r: P(128 - r, 160 - r, 128 + r, 160 + r)
        d.pieslice(box(100), 208, 332, fill=255); d.pieslice(box(72), 200, 340, fill=0)
    else:
        d.pieslice(P(10, 109, 246, 345), 180, 360, fill=255)
    if rim:
        m = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(2 * 3 * S + 1)))
    return m

def hexes(key):
    m = Image.new('L', (W, W), 0); d = ImageDraw.Draw(m); r = 22 * S; h = math.sqrt(3) * r
    for col in range(-2, 16):
        for row in range(-2, 16):
            x = col * 1.5 * r; y = row * h + (h / 2 if col % 2 else 0)
            d.line([(x + r * math.cos(math.radians(60 * k)), y + r * math.sin(math.radians(60 * k))) for k in range(7)], fill=255, width=3 * S)
    return ImageChops.multiply(m, mask(key))

def over(im, m, color, alpha):
    im.paste(Image.new('RGB', (W, W), color), (0, 0), m.point(lambda v: int(v * alpha)))

def rim_color(c, name): return (95, 95, 105) if name == 'Dark' else tuple(min(255, int(v * 1.1 + 25)) for v in c)

def icon(key, style, color='Default', rainbow=False, size=256):
    im = background()
    behind = key == 'directional'          # the helldiver stands behind the oval, drawn first
    glow = (255, 214, 20) if color == 'Default' or rainbow else (70, 70, 80) if color == 'Dark' else SHOW[color]
    device(im, key, glow)
    if style == 'Invisible':
        dash = Image.new('L', (W, W), 0); dd = ImageDraw.Draw(dash)
        for k in range(0, W, 16 * S): dd.rectangle([k, 0, k + 8 * S, W], fill=255)
        over(im, ImageChops.multiply(mask(key, True), dash), (150, 150, 150), 0.55)
    elif rainbow:
        x0, _, x1, _ = mask(key).getbbox(); band = (x1 - x0) / len(RAINBOW)
        for i, n in enumerate(RAINBOW):
            strip = Image.new('L', (W, W), 0); ImageDraw.Draw(strip).rectangle([x0 + i * band, 0, x0 + (i + 1) * band, W], fill=255)
            over(im, ImageChops.multiply(mask(key), strip), SHOW[n], 0.5)
            over(im, ImageChops.multiply(mask(key, True), strip), rim_color(SHOW[n], n), 0.95)
    else:
        c = SHOW[color]
        fill = {'Clear - Medium': 0.5, 'Clear - Low': 0.25, 'Honeycomb': 0.12}[style]
        rim = {'Clear - Medium': 0.95, 'Clear - Low': 0.6, 'Honeycomb': 0.9}[style]
        over(im, mask(key), c, fill)
        if style == 'Honeycomb': over(im, hexes(key), rim_color(c, color), 0.9)
        over(im, mask(key, True), rim_color(c, color), rim)
    return im.resize((size, size), Image.LANCZOS)

if __name__ == '__main__':
    man = json.load(open('build/manifest.json')); n = 0
    for opt in man['Options']:
        key = opt['Image'].split('/')[1].split('_')[0].split('.')[0]
        if opt['Image'].endswith('_color.png'): icon(key, 'Clear - Medium', rainbow=True).save('build/' + opt['Image'], optimize=True)
        else: icon(key, 'Clear - Medium').save('build/' + opt['Image'], optimize=True)
        n += 1
        for sub in opt['SubOptions']:
            if '_style_' in sub['Image']: im = icon(key, sub['Name'])
            else: im = icon(key, 'Clear - Medium', sub['Name'])
            im.save('build/' + sub['Image'], optimize=True); n += 1
    print(n, 'icons')
