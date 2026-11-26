"""pix8 - 8-bit akşam tarzı için çizim motoru (yandan bakış piksel sahne).

Her şey 270x480 küçük tuvale çizilir, sonra INTER_NEAREST ile x4 büyütülür (1080x1920).
Altyazı, sayaç ve EŞİK imzası büyütmeden SONRA net (pikselsiz) çizilir.
"""
import math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

CW, CH, SC = 270, 480, 4
W, H = CW * SC, CH * SC

_B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32
BAY = np.tile(_B4, (CH // 4 + 1, CW // 4 + 1))[:CH, :CW]

# ---- Paletler (üstten ufka doğru durak noktaları)
DUSK = [(0, (44, 34, 88)), (110, (92, 56, 126)), (200, (186, 84, 122)), (262, (246, 146, 96))]
NIGHT = [(0, (12, 12, 34)), (150, (26, 26, 66)), (300, (58, 44, 100))]
DAWN = [(0, (60, 52, 112)), (120, (132, 84, 146)), (210, (232, 128, 120)), (270, (255, 190, 120))]
LIT = (255, 200, 110)          # yanan pencere
GLOW = (255, 170, 90)          # sıcak parıltı
RIM = (255, 176, 110)          # gün batımı kenar ışığı


def C(c, f=1.0):
    return tuple(int(max(0, min(255, round(v * f)))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def canvas(col=(0, 0, 0)):
    img = np.zeros((CH, CW, 3), np.uint8); img[:] = col
    return img


def dgrad(img, stops, x0=0, x1=CW, bands=4):
    """Noktalı (Bayer dither) dikey gradyan. stops: [(y, renk), ...]"""
    for (ya, ca), (yb, cb) in zip(stops, stops[1:]):
        ya, yb = int(ya), int(min(yb, CH))
        if yb <= ya:
            continue
        ca, cb = np.array(ca, float), np.array(cb, float)
        ys = np.arange(ya, yb)
        t = ((ys - ya) / max(1, yb - ya))[:, None]
        tt = t * bands; k = np.floor(tt); f = tt - k
        cA = ca + (cb - ca) * (k / bands); cB = ca + (cb - ca) * (np.minimum(k + 1, bands) / bands)
        m = BAY[ys, x0:x1] < f
        img[ya:yb, x0:x1] = np.where(m[..., None], cB[:, None, :], cA[:, None, :]).astype(np.uint8)
    last_y, last_c = stops[-1]
    return img


def sky(img, stops, horizon):
    s = [(y, c) for y, c in stops if y < horizon] + [(horizon, stops[-1][1])]
    return dgrad(img, s)


def blend_mask(img, mask, col, a):
    img[mask] = (img[mask] * (1 - a) + np.array(col) * a).astype(np.uint8)


def halo(img, cx, cy, r, col=GLOW, strength=0.7, a=0.6):
    """Işığın etrafında noktalı parıltı (örnekteki gibi)."""
    x0, x1 = max(0, int(cx - r)), min(CW, int(cx + r + 1))
    y0, y1 = max(0, int(cy - r)), min(CH, int(cy + r + 1))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    m = (d < 1) & (BAY[y0:y1, x0:x1] < strength * np.clip(1 - d, 0, 1) ** 1.4)
    sub = img[y0:y1, x0:x1]
    blend_mask(sub, m, col, a)


def disc(img, cx, cy, r, col):
    cv2.circle(img, (int(cx), int(cy)), int(r), C(col), -1, lineType=cv2.LINE_8)


def rect(img, x0, y0, x1, y1, col):
    cv2.rectangle(img, (int(x0), int(y0)), (int(x1) - 1, int(y1) - 1), C(col), -1)


def dither_rect(img, x0, y0, x1, y1, col, level=0.5, a=1.0):
    x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(CW, int(x1)), min(CH, int(y1))
    if x0 >= x1 or y0 >= y1:
        return
    m = BAY[y0:y1, x0:x1] < level
    blend_mask(img[y0:y1, x0:x1], m, col, a)


def streaks(img, items, t):
    """Yatay çizgi bulutlar. items: [(x, y, uzunluk, renk, hız)]"""
    for x, y, L, col, sp in items:
        xx = int((x + sp * t) % (CW + L + 40)) - L - 20
        cv2.line(img, (xx, y), (xx + L, y), C(col), 1)
        cv2.line(img, (xx + 4, y + 1), (xx + L - 6, y + 1), C(col, 0.82), 1)


def stars(img, rng_seed, n, ymax, t):
    r = np.random.default_rng(rng_seed)
    for i in range(n):
        x, y = int(r.integers(0, CW)), int(r.integers(0, ymax))
        tw = 0.5 + 0.5 * math.sin(t * (1.5 + r.random() * 3) + i)
        c = mix((70, 70, 120), (230, 230, 255), tw if r.random() < 0.3 else 0.35)
        img[y, x] = c


def skyline(seed, x0, x1, base, hmin, hmax, wmin=10, wmax=26, gap=(0, 4)):
    r = np.random.default_rng(seed); out = []; x = x0
    while x < x1:
        w = int(r.integers(wmin, wmax + 1)); h = int(r.integers(hmin, hmax + 1))
        wins = [(wx, wy, r.random()) for wy in range(base - h + 4, base - 3, 4)
                for wx in range(x + 2, x + w - 2, 3)]
        out.append(dict(x=x, w=w, h=h, base=base, wins=wins,
                        ant=r.random() < 0.25, step=r.random() < 0.3))
        x += w + int(r.integers(gap[0], gap[1] + 1))
    return out


def draw_skyline(img, blds, col, lit_p=0.0, t=0.0, rim=None):
    for b in blds:
        x, w, h, base = b['x'], b['w'], b['h'], b['base']
        rect(img, x, base - h, x + w, base, col)
        if b['step']:
            rect(img, x + w // 4, base - h - 5, x + w - w // 4, base - h, col)
        if b['ant']:
            cv2.line(img, (x + w // 2, base - h - 1), (x + w // 2, base - h - 9), C(col), 1)
        if rim:
            cv2.line(img, (x, base - h), (x + w - 1, base - h), C(rim), 1)
        for wx, wy, rr in b['wins']:
            if rr < lit_p and 0 <= wx < CW and 0 <= wy < CH:
                flick = 1.0 if math.sin(t * 2 + rr * 50) > -0.95 else 0.6
                img[wy, wx] = C(LIT, flick)


def sea(img, y0, y1, top, bot, t, sun_x=None, sun_col=GLOW, seed=5, speed=8):
    dgrad(img, [(y0, top), (y1, bot)])
    r = np.random.default_rng(seed)
    for i in range(int((y1 - y0) * 2.2)):
        y = int(y0 + 2 + r.random() * (y1 - y0 - 3))
        depth = (y - y0) / max(1, (y1 - y0))
        L = int(3 + 6 * depth); x = int((r.random() * CW + speed * (0.4 + depth) * t) % (CW + 20)) - 10
        cv2.line(img, (x, y), (x + L, y), C(mix(top, (230, 200, 220), 0.35)), 1)
    if sun_x is not None:
        for y in range(y0 + 1, y1, 2):
            w = int(10 * (1 - (y - y0) / (y1 - y0)) + 3 + 2 * math.sin(t * 6 + y))
            cv2.line(img, (int(sun_x - w), y), (int(sun_x + w), y), C(sun_col), 1)


def godwit(img, x, y, s=1.0, mode='stand', frame=0, rim=RIM):
    """Yandan kıyı çamurçulluğu (sağa bakar). x,y gövde merkezi. mode: stand | fly"""
    body, dark, belly, head, beak = (184, 132, 86), (104, 72, 50), (222, 168, 116), (196, 146, 98), (214, 142, 122)
    X, Y = int(x), int(y)
    S = lambda v: int(round(v * s))
    if mode == 'stand':
        for lx in (-1, 2):
            cv2.line(img, (X + S(lx), Y + S(3)), (X + S(lx) - S(1), Y + S(10)), (70, 54, 46), 1)
    cv2.fillPoly(img, [np.array([(X - S(5), Y - S(1)), (X - S(12), Y - S(2)), (X - S(5), Y + S(2))], np.int32)], dark)
    cv2.ellipse(img, (X, Y), (S(7), S(4)), -8, 0, 360, body, -1, lineType=cv2.LINE_8)
    cv2.ellipse(img, (X + S(1), Y + S(2)), (S(5), S(2)), -8, 0, 180, belly, -1, lineType=cv2.LINE_8)
    cv2.fillPoly(img, [np.array([(X + S(3), Y - S(3)), (X + S(7), Y - S(7)), (X + S(9), Y - S(5)), (X + S(6), Y)], np.int32)], head)
    disc(img, X + S(8), Y - S(6), max(1, S(2.6)), head)
    img[min(CH - 1, max(0, Y - S(7))), min(CW - 1, max(0, X + S(9)))] = (28, 22, 20)
    cv2.line(img, (X + S(10), Y - S(6)), (X + S(19), Y - S(8)), beak, max(1, S(0.7)), lineType=cv2.LINE_8)
    if mode == 'stand':
        cv2.ellipse(img, (X - S(1), Y - S(1)), (S(5), S(2)), -8, 180, 360, dark, -1, lineType=cv2.LINE_8)
    else:
        up = frame % 2 == 0
        tip = (X - S(4), Y - S(13)) if up else (X - S(5), Y + S(11))
        cv2.fillPoly(img, [np.array([(X - S(3), Y - S(1)), (X + S(3), Y - S(1)), tip], np.int32)], dark)
    if rim:  # sırt kenar ışığı
        for i in range(-S(5), S(4)):
            yy = Y - int(round(S(4) * math.sqrt(max(0, 1 - (i / max(1, S(7))) ** 2)))) - 0
            if 0 <= yy < CH and 0 <= X + i < CW:
                img[yy, X + i] = C(rim)


def tiny_bird(img, x, y, frame, col=(30, 24, 50)):
    pts = [(-2, -1), (-1, 0), (0, 0), (1, 0), (2, -1)] if frame % 2 == 0 else [(-2, 1), (-1, 0), (0, 0), (1, 0), (2, 1)]
    for dx, dy in pts:
        xx, yy = int(x + dx), int(y + dy)
        if 0 <= xx < CW and 0 <= yy < CH:
            img[yy, xx] = col


def sparkle(img, x, y, big=True, col=(255, 250, 220)):
    for dx, dy in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)] + ([(2, 0), (-2, 0), (0, 2), (0, -2)] if big else []):
        xx, yy = int(x + dx), int(y + dy)
        if 0 <= xx < CW and 0 <= yy < CH:
            img[yy, xx] = col if abs(dx) + abs(dy) <= 1 else GLOW


def upscale(small, crop=None):
    if crop:
        x0, y0, cw, ch = crop
        x0 = max(0, min(CW - cw, int(x0))); y0 = max(0, min(CH - ch, int(y0)))
        small = small[y0:y0 + ch, x0:x0 + cw]
    return np.ascontiguousarray(cv2.resize(small, (W, H), interpolation=cv2.INTER_NEAREST))


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- net yazılar
FD = '/home/user/esik-araclar/fontlar/node_modules/@expo-google-fonts/'
F_MED = FD + 'poppins/500Medium/Poppins_500Medium.ttf'
F_BOLD = FD + 'poppins/700Bold/Poppins_700Bold.ttf'
F_LORA = FD + 'lora/400Regular/Lora_400Regular.ttf'
_fc = {}


def font(path, size):
    if (path, size) not in _fc:
        _fc[(path, size)] = ImageFont.truetype(path, size)
    return _fc[(path, size)]


def pill(text, size=46, path=F_MED, kw=(255, 150, 60), fg=(250, 240, 226), alpha=0.84, pad=(30, 16)):
    """[köşeli parantez] içi turuncu anahtar kelime."""
    f = font(path, size); segs, cur, k = [], '', False
    for ch in text:
        if ch in '[]':
            if cur:
                segs.append((cur, k))
            cur, k = '', ch == '['
        else:
            cur += ch
    if cur:
        segs.append((cur, k))
    full = ''.join(s for s, _ in segs); asc, desc = f.getmetrics()
    w = int(f.getlength(full)) + 2 * pad[0]; h = asc + desc + 2 * pad[1]
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(30, 26, 26, int(255 * alpha)))
    x = pad[0]
    for s, kk in segs:
        d.text((x, pad[1]), s, font=f, fill=(kw if kk else fg) + (255,)); x += f.getlength(s)
    return np.array(im)


def blit(frame, rgba, cx, cy, a=1.0):
    h, w = rgba.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb or a <= 0:
        return
    src = rgba[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32)
    al = src[..., 3:4] / 255.0 * a
    dst = frame[ya:yb, xa:xb].astype(np.float32)
    frame[ya:yb, xa:xb] = (dst * (1 - al) + src[..., :3] * al).astype(np.uint8)


def make_sig():
    f = font(F_LORA, 92); sp = 34; L = "EŞİK"
    ws = [f.getlength(c) for c in L]; asc, desc = f.getmetrics()
    im = Image.new('RGBA', (int(sum(ws) + sp * 3) + 20, asc + desc + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 10
    for c, w in zip(L, ws):
        d.text((x, 10), c, font=f, fill=(246, 228, 196, 255)); x += w + sp
    return np.array(im)


_SIG = None


def signature(frame, t, t0, line_col=(255, 150, 60)):
    global _SIG
    if t < t0:
        return
    if _SIG is None:
        _SIG = make_sig()
    blit(frame, _SIG, W / 2, 1490, min(1.0, (t - t0) / 0.6))
    lw = int(164 * ease((t - t0 - 0.4) / 0.35))
    if lw > 1:
        cv2.rectangle(frame, (W // 2 - lw // 2, 1570), (W // 2 + lw // 2, 1574), line_col, -1)


def captions(frame, t, caps, cache={}):
    for a, b, text, y in caps:
        if a <= t < b:
            if text not in cache:
                cache[text] = pill(text)
            blit(frame, cache[text], W / 2, y, min(1.0, (t - a) / 0.12, (b - t) / 0.12))
