"""Better Bubble Shields art: thumbnail, Nexus header, gallery cards. HTML/CSS rendered with Playwright.
Needs: the comparison screenshots in PHOTOS (env BBS_PHOTOS, default ../photos), art/big/ (run icons_big.py first),
and the fonts next to this script: npm pack @fontsource/anton @fontsource/barlow-condensed, then untar each into
fontsource-anton-<ver>/ and fontsource-barlow-condensed-<ver>/."""
import os, pathlib
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).parent.resolve()
PHOTOS = pathlib.Path(os.environ.get('BBS_PHOTOS', HERE.parent / 'photos'))
VERSION = 'V7'
OUT = HERE / 'out'; OUT.mkdir(exist_ok=True)
A = lambda p: pathlib.Path(p).resolve().as_uri()
ANTON = A(next((HERE).glob('fontsource-anton-*/files/anton-latin-400-normal.woff2')))
B6 = A(next((HERE).glob('fontsource-barlow-condensed-*/files/barlow-condensed-latin-600-normal.woff2')))
B7 = A(next((HERE).glob('fontsource-barlow-condensed-*/files/barlow-condensed-latin-700-normal.woff2')))
HERO = A(PHOTOS / 'Comparison-Relay-After.png')
PACK = A(PHOTOS / 'Comparison-ShieldPack-After.png')
COLORS = [('Default', '#e2ac3a'), ('White', '#ebebeb'), ('Red', '#e12d28'), ('Orange', '#f0781e'), ('Yellow', '#f5dc32'),
          ('Green', '#3cd250'), ('Cyan', '#32cde6'), ('Blue', '#3769f0'), ('Purple', '#9646eb'), ('Pink', '#f05faf'), ('Dark', '#26262c')]
YEL = '#ffd200'
BASE = f"""
@font-face {{ font-family: Anton; src: url({ANTON}); }}
@font-face {{ font-family: Barlow; font-weight: 600; src: url({B6}); }}
@font-face {{ font-family: Barlow; font-weight: 700; src: url({B7}); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #14120c; color: #f2eee6; font-family: Barlow; font-weight: 700; overflow: hidden; }}
.y {{ color: {YEL}; }}
.title {{ font-family: Anton; text-transform: uppercase; line-height: .95; letter-spacing: .01em; }}
.cap {{ text-transform: uppercase; letter-spacing: .14em; }}
.badge {{ font-family: Anton; background: {YEL}; color: #14120c; display: inline-block; transform: skew(-8deg); }}
.frame {{ position: absolute; border: 2px solid {YEL}; pointer-events: none; }}
.stripes {{ position: absolute; background: repeating-linear-gradient(-55deg, {YEL} 0 14px, transparent 14px 26px); }}
.dots {{ display: flex; gap: 14px; }}
.dot {{ border-radius: 50%; border: 2px solid rgba(255,255,255,.55); }}
"""
def dots(size):
    return '<div class="dots">' + ''.join(f'<div class="dot" style="width:{size}px;height:{size}px;background:{c}"></div>' for _, c in COLORS) + '</div>'

def render(name, w, h, body, css=''):
    html = f'<!doctype html><html><head><meta charset="utf-8"><style>{BASE}{css}</style></head><body style="width:{w}px;height:{h}px">{body}</body></html>'
    p = OUT / f'{name}.html'; p.write_text(html)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={'width': w, 'height': h})
        pg.goto(p.as_uri()); pg.wait_for_timeout(400)
        pg.screenshot(path=str(OUT / f'{name}.png')); b.close()
    p.unlink()

SHIELDS = 'RELAY &middot; G/SH-39 &middot; DIRECTIONAL &middot; SHIELD PACK'

# 1. Thumbnail 1254x1254
render('Thumbnail-1254x1254', 1254, 1254, f"""
<div style="position:absolute;inset:0;background:url({PACK}) 52% 40%/cover"></div>
<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,9,6,.25) 0%,rgba(10,9,6,0) 25%,rgba(10,9,6,.55) 55%,rgba(10,9,6,.95) 78%,rgba(10,9,6,.98) 100%)"></div>
<div class="frame" style="inset:36px"></div>
<div class="stripes" style="left:72px;top:88px;width:120px;height:30px"></div>
<div class="badge" style="position:absolute;right:78px;top:72px;font-size:72px;padding:6px 26px">{VERSION}</div>
<div style="position:absolute;left:0;right:0;top:700px;text-align:center">
  <div class="title" style="font-size:150px">BETTER</div>
  <div class="title y" style="font-size:150px">BUBBLE SHIELDS</div>
  <div class="cap" style="font-size:40px;margin-top:34px">PICK YOUR STYLE &middot; PICK YOUR COLOR</div>
  <div style="display:flex;justify-content:center;margin-top:28px">{dots(40)}</div>
  <div class="cap" style="font-size:31px;margin-top:30px;color:#d8d2c6">{SHIELDS}</div>
</div>""")

# 2. Nexus header 1300x372
render('Nexus-Header-1300x372', 1300, 372, f"""
<div style="position:absolute;inset:0;background:url({HERO}) 50% 18%/cover"></div>
<div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(10,9,6,.95) 0%,rgba(10,9,6,.75) 38%,rgba(10,9,6,.1) 62%,rgba(10,9,6,.75) 100%)"></div>
<div class="frame" style="inset:14px"></div>
<div style="position:absolute;left:52px;top:52px">
  <div class="title" style="font-size:92px">BETTER</div>
  <div class="title y" style="font-size:92px">BUBBLE SHIELDS</div>
  <div style="margin-top:22px">{dots(24)}</div>
</div>
<div style="position:absolute;right:52px;top:60px;text-align:right">
  <div class="cap" style="font-size:30px;line-height:1.55">PICK YOUR STYLE<br>PICK YOUR COLOR<br>OR GO INVISIBLE</div>
  <div class="badge" style="font-size:50px;padding:2px 20px;margin-top:14px">{VERSION}</div>
</div>""")

# 3. Primary gallery 1920x1080
render('Nexus-Gallery-1920x1080', 1920, 1080, f"""
<div style="position:absolute;inset:0;background:url({HERO}) 60% 50%/cover"></div>
<div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(10,9,6,.96) 0%,rgba(10,9,6,.85) 30%,rgba(10,9,6,0) 55%)"></div>
<div class="frame" style="inset:36px"></div>
<div style="position:absolute;left:104px;top:120px">
  <div class="title" style="font-size:150px">BETTER</div>
  <div class="title y" style="font-size:150px">BUBBLE<br>SHIELDS</div>
  <div class="cap" style="font-size:40px;line-height:1.6;margin-top:34px">EVERY SHIELD, YOUR WAY<br>PICK YOUR STYLE<br>PICK YOUR COLOR<br>OR GO INVISIBLE</div>
  <div style="display:flex;align-items:center;gap:30px;margin-top:30px"><div class="badge" style="font-size:64px;padding:2px 24px">{VERSION}</div>{dots(34)}</div>
</div>
<div class="cap" style="position:absolute;left:104px;bottom:84px;font-size:30px;color:#d8d2c6">{SHIELDS}</div>""")

# 4. Options 1920x1080: four cards
def card(key, name, sub):
    styles = [('Honeycomb', True), ('Clear - Medium &middot; 50%', False), ('Clear - Low &middot; 25%', False), ('Invisible', False)]
    radios = ''.join(f'<div class="radio{" on" if on else ""}"><span></span>{s}</div>' for s, on in styles)
    sw = ''.join(f'<div class="sw{" on" if i == 0 else ""}" style="background:{c}"></div>' for i, (_, c) in enumerate(COLORS))
    return f"""<div class="card"><div class="img" style="background-image:url({A(HERE / f'big/{key}_rainbow.png')})"></div>
      <div class="body"><div class="head"><div class="tick">&#10003;</div><div><div class="nm">{name}</div><div class="sub cap">{sub}</div></div></div>
      <div class="lbl cap">STYLE</div>{radios}<div class="lbl cap">COLOR</div><div class="sws">{sw}</div></div></div>"""
OPT_CSS = f"""
.card {{ width: 404px; border: 2px solid {YEL}; background: #1c1a13; display:flex; flex-direction:column; }}
.card .img {{ height: 250px; background-size: cover; background-position: 50% 62%; border-bottom: 2px solid {YEL}; }}
.body {{ padding: 20px 22px 24px; }}
.head {{ display:flex; gap:14px; align-items:center; margin-bottom: 14px; }}
.tick {{ width: 38px; height: 38px; background: {YEL}; color: #14120c; font-size: 30px; display:flex; align-items:center; justify-content:center; flex:none; }}
.nm {{ font-family: Anton; font-size: 34px; color: {YEL}; line-height: 1; }}
.sub {{ font-size: 16px; color: #cfc9bd; margin-top: 4px; }}
.lbl {{ font-size: 18px; color: #a9a396; margin: 14px 0 8px; }}
.radio {{ display:flex; align-items:center; gap: 12px; font-size: 26px; text-transform: uppercase; letter-spacing: .06em; margin: 7px 0; color: #e8e3d8; }}
.radio span {{ width: 22px; height: 22px; border: 3px solid #e8e3d8; border-radius: 50%; }}
.radio.on {{ color: {YEL}; }} .radio.on span {{ border-color: {YEL}; background: radial-gradient({YEL} 45%, transparent 50%); }}
.sws {{ display:flex; gap: 8px; padding-left: 4px; }}
.sw {{ width: 24px; height: 24px; border-radius: 50%; border: 2px solid rgba(255,255,255,.5); }}
.sw.on {{ outline: 3px solid {YEL}; outline-offset: 3px; }}
"""
render('Options-1920x1080', 1920, 1080, f"""
<div class="frame" style="inset:36px"></div>
<div style="position:absolute;left:84px;top:78px;display:flex;align-items:center;gap:26px">
  <div class="title" style="font-size:84px">BETTER <span class="y">BUBBLE SHIELDS</span></div><div class="badge" style="font-size:52px;padding:0 18px">{VERSION}</div></div>
<div class="cap" style="position:absolute;right:84px;top:88px;text-align:right;font-size:26px;line-height:1.5">EVERY SHIELD HAS ITS OWN<br>STYLE AND COLOR</div>
<div style="position:absolute;left:84px;right:84px;top:218px;display:flex;justify-content:space-between">
  {card('relay', 'FX-12 RELAY', 'SHIELD GENERATOR RELAY')}{card('grenade', 'G/SH-39 SHIELD', 'SHIELD GRENADE')}
  {card('directional', 'SH-51 DIRECTIONAL', 'DIRECTIONAL SHIELD')}{card('pack', 'SH-32 SHIELD PACK', 'SHIELD GENERATOR PACK')}</div>
<div class="cap" style="position:absolute;left:0;right:0;bottom:70px;text-align:center;font-size:28px">
  <span class="y">TICK</span> A SHIELD &nbsp;&middot;&nbsp; <span class="y">PICK</span> A STYLE &nbsp;&middot;&nbsp; <span class="y">PICK</span> A COLOR &nbsp;&middot;&nbsp; <span class="y">UNTICK</span> TO KEEP IT VANILLA</div>
""", OPT_CSS)

# 5. Styles 1920x1080
STY = [('Honeycomb', 'honeycomb', 'THE DEFAULT', 'Keeps the honeycomb, no swirling cloud or ripple'),
       ('Clear - Medium', 'clear_medium', '50% OPACITY', 'No honeycomb or cloud, an even tint'),
       ('Clear - Low', 'clear_low', '25% OPACITY', 'No honeycomb or cloud, a faint tint'),
       ('Invisible', 'invisible', 'FULLY HIDDEN', 'No bubble at all; the glow, hit flash and break effect stay')]
cols = ''.join(f"""<div class="st"><div class="img" style="background-image:url({A(HERE / f'big/relay_{k}.png')})"></div>
  <div class="nm">{n.upper()}</div><div class="tag cap y">{t}</div><div class="ds">{d}</div></div>""" for n, k, t, d in STY)
render('Styles-1920x1080', 1920, 1080, f"""
<div class="frame" style="inset:36px"></div>
<div style="position:absolute;left:84px;top:78px;display:flex;align-items:center;gap:26px">
  <div class="title" style="font-size:84px">FOUR <span class="y">STYLES</span></div><div class="badge" style="font-size:52px;padding:0 18px">{VERSION}</div></div>
<div class="cap" style="position:absolute;right:84px;top:88px;text-align:right;font-size:26px;line-height:1.5">PICKED PER SHIELD<br>IN THE MOD'S OPTIONS</div>
<div style="position:absolute;left:84px;right:84px;top:250px;display:flex;justify-content:space-between">{cols}</div>
<div class="cap" style="position:absolute;left:0;right:0;bottom:70px;text-align:center;font-size:28px">WORKS WITH EVERY COLOR &nbsp;&middot;&nbsp; <span class="y">RELAY &middot; G/SH-39 &middot; DIRECTIONAL &middot; SHIELD PACK</span></div>
""", f""".st {{ width: 400px; text-align: center; }}
.st .img {{ height: 400px; background-size: cover; border: 2px solid {YEL}; }}
.st .nm {{ font-family: Anton; font-size: 46px; margin-top: 26px; }}
.st .tag {{ font-size: 26px; margin-top: 6px; }}
.st .ds {{ font-size: 25px; color: #cfc9bd; margin-top: 12px; line-height: 1.3; font-weight: 600; }}""")

# 6. Colors 1920x1080
cells = ''.join(f"""<div class="cl"><div class="img" style="background-image:url({A(HERE / f'big/relay_color_{n.lower()}.png')})"></div><div class="nm">{('GAME DEFAULT' if n == 'Default' else n.upper())}</div></div>""" for n, _ in COLORS)
render('Colors-1920x1080', 1920, 1080, f"""
<div class="frame" style="inset:36px"></div>
<div style="position:absolute;left:84px;top:78px;display:flex;align-items:center;gap:26px">
  <div class="title" style="font-size:84px">ELEVEN <span class="y">COLORS</span></div><div class="badge" style="font-size:52px;padding:0 18px">{VERSION}</div></div>
<div class="cap" style="position:absolute;right:84px;top:88px;text-align:right;font-size:26px;line-height:1.5">THE BUBBLE, ITS HIT FLASH, THE GENERATOR<br>GLOW AND THE BREAK EFFECT, PER SHIELD</div>
<div style="position:absolute;left:120px;right:120px;top:230px;display:flex;flex-wrap:wrap;justify-content:center;gap:34px 30px">{cells}</div>
<div class="cap" style="position:absolute;left:0;right:0;bottom:70px;text-align:center;font-size:28px">WORKS WITH EVERY STYLE &nbsp;&middot;&nbsp; <span class="y">RELAY &middot; G/SH-39 &middot; DIRECTIONAL &middot; SHIELD PACK</span></div>
""", f""".cl {{ width: 250px; text-align: center; }}
.cl .img {{ height: 250px; background-size: cover; border: 2px solid rgba(255,210,0,.7); }}
.cl .nm {{ font-size: 30px; letter-spacing: .1em; margin-top: 12px; }}""")
print(sorted(os.listdir(OUT)))
