"""pix8 v2 - '8-bit akşam' çizim motoru (yandan bakış, ince pikselli, hacimli gölgeli).

Tuval 540x960, INTER_NEAREST ile x2 büyütülür (1080x1920).  Çekiciliğin sırrı:
  1) ince piksel (detay),  2) hacimli gölge: her obje ışık yönüne göre 4-6 tonluk rampayla,
  tonlar arası Bayer noktalı geçişle boyanır,  3) gölge tarafında ince parlak kenar ışığı,
  4) atmosfer: objenin arkasında geniş noktalı parıltı, ufukta sis, ışık alan kalın bulutlar.
Altyazı, sayaç ve EŞİK imzası büyütmeden SONRA net çizilir.
"""
import math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

CW, CH, SC = 540, 960, 2
W, H = CW * SC, CH * SC

_B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32
BAY = np.tile(_B4, (CH // 4 + 1, CW // 4 + 1))[:CH, :CW]

# ---- Gökyüzü paletleri (y, renk) – üstten ufka
DUSK = [(0, (40, 30, 84)), (220, (88, 54, 124)), (420, (176, 80, 122)), (540, (238, 132, 98)), (570, (252, 168, 108))]
NIGHT = [(0, (10, 10, 30)), (300, (24, 24, 62)), (600, (52, 42, 96))]
DAWN = [(0, (56, 50, 110)), (240, (126, 82, 144)), (430, (226, 124, 120)), (560, (255, 186, 122))]
LIT, GLOW, RIM = (255, 204, 116), (255, 170, 92), (255, 196, 140)
LIGHT_DUSK = (-0.65, -0.35, 0.68)     # ışık soldan-yukarıdan (gün batımı)
HARD_W = 0.10                         # ton geçiş şeridi genişliği (küçük = daha keskin, 8-bit)

# ---- Malzeme rampaları (koyu -> açık)
R_BIRD = [(84, 52, 52), (150, 98, 70), (212, 156, 100), (250, 208, 150)]
R_WING = [(48, 30, 40), (100, 66, 56), (156, 108, 76), (204, 158, 108)]
R_WOOD = [(40, 26, 46), (88, 58, 62), (150, 98, 80), (200, 140, 98)]
R_MOON = [(110, 108, 150), (190, 186, 204), (246, 240, 226)]
R_STONE = [(34, 26, 58), (64, 46, 88), (110, 74, 112), (170, 112, 128)]


def C(c, f=1.0):
    return tuple(int(max(0, min(255, round(v * f)))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ease(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def canvas(col=(0, 0, 0)):
    img = np.zeros((CH, CW, 3), np.uint8); img[:] = col; return img


def _box(cx, cy, rx, ry):
    return max(0, int(cx - rx - 1)), min(CW, int(cx + rx + 2)), max(0, int(cy - ry - 1)), min(CH, int(cy + ry + 2))


def ramp_fill(img, mask, lum, ramp, x0, y0):
    """lum (0..1) değerini rampaya noktalı geçişle eşle."""
    n = len(ramp); v = np.clip(lum, 0, 0.9999) * (n - 1); k = np.floor(v).astype(int); f = v - k
    k2 = np.minimum(k + 1, n - 1)
    h, w = mask.shape
    # 8-bit kuralı: tonlar keskin ayrılır; noktalı geçiş yalnızca sınırdaki dar şeritte
    f = np.clip((f - 0.5) / (2 * HARD_W) + 0.5, 0, 1)
    pick = np.where(BAY[y0:y0 + h, x0:x0 + w] < f, k2, k)
    R = np.array(ramp, np.uint8)
    sub = img[y0:y0 + h, x0:x0 + w]
    sub[mask] = R[pick[mask]]


def _light(L):
    L = np.array(L, float); return L / np.linalg.norm(L)


def shade_normals(img, mask, nx, ny, nz, ramp, x0, y0, light=LIGHT_DUSK, amb=0.18, rim=RIM, rim_w=0.32):
    L = _light(light)
    lum = amb + (1 - amb) * np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    ramp_fill(img, mask, lum, ramp, x0, y0)
    if rim is not None:  # gölge tarafında ince parlak kenar
        edge = mask & (nz < rim_w) & ((nx * L[0] + ny * L[1]) < -0.15)
        sub = img[y0:y0 + mask.shape[0], x0:x0 + mask.shape[1]]
        sub[edge] = (sub[edge] * 0.35 + np.array(rim) * 0.65).astype(np.uint8)


def ellipsoid(img, cx, cy, rx, ry, ramp, light=LIGHT_DUSK, rot=0.0, rim=RIM, amb=0.18, clip=None):
    x0, x1, y0, y1 = _box(cx, cy, max(rx, ry), max(rx, ry))
    if x0 >= x1 or y0 >= y1:
        return None
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(float)
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    c, s = math.cos(rot), math.sin(rot)
    u = (dx * c + dy * s) / rx; v = (-dx * s + dy * c) / ry
    r2 = u * u + v * v; mask = r2 <= 1
    if clip is not None:
        mask &= clip(xx, yy)
    nz = np.sqrt(np.clip(1 - r2, 0, 1)); nu, nv = u, v
    nx = nu * c - nv * s; ny = nu * s + nv * c
    shade_normals(img, mask, nx, ny, nz, ramp, x0, y0, light, amb, rim)
    return mask, (x0, y0)


def cylinder(img, x0, x1, y0, y1, ramp, light=LIGHT_DUSK, rim=RIM, amb=0.2, cap=True):
    """Dikey silindir (direk, kule)."""
    x0, x1, y0, y1 = int(x0), int(x1), max(0, int(y0)), min(CH, int(y1))
    if x1 <= x0 or y1 <= y0:
        return
    xs = np.arange(max(0, x0), min(CW, x1)); u = (xs + 0.5 - (x0 + x1) / 2) / ((x1 - x0) / 2)
    nx = np.tile(u, (y1 - y0, 1)); nz = np.sqrt(np.clip(1 - nx ** 2, 0, 1)); ny = np.zeros_like(nx)
    mask = np.ones_like(nx, bool)
    shade_normals(img, mask, nx, ny, nz, ramp, max(0, x0), y0, light, amb, rim)
    if cap:
        cv2.ellipse(img, ((x0 + x1) // 2, y0), ((x1 - x0) // 2, max(1, (x1 - x0) // 6)), 0, 0, 360, ramp[-1], -1, cv2.LINE_8)


def dgrad(img, stops, x0=0, x1=CW, bands=6):
    """Noktalı (Bayer) dikey gradyan."""
    for (ya, ca), (yb, cb) in zip(stops, stops[1:]):
        ya, yb = int(ya), int(min(yb, CH))
        if yb <= ya:
            continue
        ca, cb = np.array(ca, float), np.array(cb, float); ys = np.arange(ya, yb)
        t = ((ys - ya) / max(1, yb - ya))[:, None]; tt = t * bands; k = np.floor(tt); f = tt - k
        cA = ca + (cb - ca) * (k / bands); cB = ca + (cb - ca) * (np.minimum(k + 1, bands) / bands)
        m = BAY[ys, x0:x1] < f
        img[ya:yb, x0:x1] = np.where(m[..., None], cB[:, None, :], cA[:, None, :]).astype(np.uint8)
    return img


def sky(img, stops, horizon):
    s = [(y, c) for y, c in stops if y < horizon]
    last = stops[-1][1] if stops[-1][0] <= horizon else stops[len(s)][1]
    return dgrad(img, s + [(horizon, last)])


def blend_mask(img, mask, col, a):
    img[mask] = (img[mask] * (1 - a) + np.array(col) * a).astype(np.uint8)


def halo(img, cx, cy, r, col=GLOW, strength=0.7, a=0.6, power=1.4):
    x0, x1, y0, y1 = _box(cx, cy, r, r)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    m = (d < 1) & (BAY[y0:y1, x0:x1] < strength * np.clip(1 - d, 0, 1) ** power)
    blend_mask(img[y0:y1, x0:x1], m, col, a)


def glow_layers(img, cx, cy, r, col=GLOW):
    """Geniş, yumuşak atmosfer parıltısı (üç katman)."""
    halo(img, cx, cy, r, col, 0.55, 0.30, 1.0)
    halo(img, cx, cy, r * 0.6, col, 0.75, 0.40, 1.2)
    halo(img, cx, cy, r * 0.32, mix(col, (255, 240, 200), 0.5), 0.9, 0.55, 1.4)


def disc(img, cx, cy, r, col):
    cv2.circle(img, (int(cx), int(cy)), int(r), C(col), -1, lineType=cv2.LINE_8)


def rect(img, x0, y0, x1, y1, col):
    cv2.rectangle(img, (int(x0), int(y0)), (int(x1) - 1, int(y1) - 1), C(col), -1)


def dither_rect(img, x0, y0, x1, y1, col, level=0.5, a=1.0):
    x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(CW, int(x1)), min(CH, int(y1))
    if x0 < x1 and y0 < y1:
        blend_mask(img[y0:y1, x0:x1], BAY[y0:y1, x0:x1] < level, col, a)


def vgrad_rect(img, x0, y0, x1, y1, top, bot, bands=4):
    x0, x1 = max(0, int(x0)), min(CW, int(x1))
    if x0 < x1:
        dgrad(img, [(y0, top), (y1, bot)], x0, x1, bands)


def cloud_band(img, x, y, L, th, dark, lit, t=0.0, sp=0.0):
    """Kalın bulut bandı: üst koyu, alt kenarı güneşten ışık alır, uçları noktalı söner."""
    xx = int((x + sp * t) % (CW + L + 80)) - L - 40
    rect(img, xx, y, xx + L, y + th, dark)
    rect(img, xx + 10, y - max(1, th // 2), xx + L - 30, y, dark)
    rect(img, xx + 6, y + th, xx + L - 12, y + th + 2, lit)
    dither_rect(img, xx - 14, y, xx, y + th, dark, 0.5)
    dither_rect(img, xx + L, y, xx + L + 14, y + th, dark, 0.5)
    dither_rect(img, xx + 4, y + th + 2, xx + L - 20, y + th + 4, lit, 0.4)


def stars(img, seed, n, ymax, t):
    r = np.random.default_rng(seed)
    for i in range(n):
        x, y = int(r.integers(0, CW)), int(r.integers(0, ymax)); big = r.random() < 0.12
        tw = 0.5 + 0.5 * math.sin(t * (1.2 + r.random() * 3) + i)
        c = mix((60, 62, 110), (240, 240, 255), tw * (0.9 if big else 0.5))
        img[y, x] = c
        if big and tw > 0.6:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < CW and 0 <= y + dy < CH:
                    img[y + dy, x + dx] = mix(img[y + dy, x + dx], c, 0.5)


def skyline(seed, x0, x1, base, hmin, hmax, wmin=20, wmax=50, gap=(0, 8)):
    r = np.random.default_rng(seed); out = []; x = x0
    while x < x1:
        w = int(r.integers(wmin, wmax + 1)); h = int(r.integers(hmin, hmax + 1))
        wins = [(wx, wy, r.random()) for wy in range(base - h + 8, base - 6, 7) for wx in range(x + 4, x + w - 4, 6)]
        out.append(dict(x=x, w=w, h=h, base=base, wins=wins, ant=r.random() < 0.3, step=r.random() < 0.35))
        x += w + int(r.integers(gap[0], gap[1] + 1))
    return out


def draw_skyline(img, blds, col, lit_p=0.0, t=0.0, rim=None, haze=None, win=LIT):
    for b in blds:
        x, w, h, base = b['x'], b['w'], b['h'], b['base']
        rect(img, x, base - h, x + w, base, col)
        if b['step']:
            rect(img, x + w // 4, base - h - 10, x + w - w // 4, base - h, col)
        if b['ant']:
            cv2.line(img, (x + w // 2, base - h - 1), (x + w // 2, base - h - 18), C(col), 1)
        if rim:
            cv2.line(img, (x, base - h), (x + w - 1, base - h), C(rim), 1)
            cv2.line(img, (x, base - h), (x, base - 1), C(mix(col, rim, 0.35)), 1)
        for wx, wy, rr in b['wins']:
            if rr < lit_p and 0 <= wx < CW - 1 and 0 <= wy < CH - 1:
                f = 1.0 if math.sin(t * 1.7 + rr * 60) > -0.97 else 0.55
                img[wy:wy + 2, wx:wx + 2] = C(win, f)
    if haze:  # alt kısım sise karışsın
        top = min(b['base'] - b['h'] for b in blds); base = blds[0]['base']
        dither_rect(img, 0, base - (base - top) // 3, CW, base, haze, 0.35, 0.5)


def sea(img, y0, y1, top, bot, t, speed=10, seed=5, reflect=()):
    """reflect: [(x, yarı_genişlik, renk)] – güneş/ay/pencere yansımaları."""
    dgrad(img, [(y0, top), (y1, bot)], bands=5)
    r = np.random.default_rng(seed); hl = mix(top, (240, 210, 230), 0.3)
    for i in range(int((y1 - y0) * 1.8)):
        y = int(y0 + 2 + r.random() * (y1 - y0 - 3)); d = (y - y0) / max(1, y1 - y0)
        L = int(4 + 14 * d); x = int((r.random() * CW + speed * (0.3 + d) * t) % (CW + 30)) - 15
        cv2.line(img, (x, y), (x + L, y), C(mix(hl, bot, d * 0.6)), 1)
    for (rx, hw, col) in reflect:
        for y in range(y0 + 1, y1, 2):
            d = (y - y0) / max(1, y1 - y0)
            w = int(hw * (1 - 0.6 * d) + 3 * math.sin(t * 5 + y * 0.7))
            off = int(3 * math.sin(t * 3 + y * 0.3))
            if w > 0:
                cv2.line(img, (int(rx - w + off), y), (int(rx + w + off), y), C(mix(col, bot, d * 0.5)), 1)


# ---------------------------------------------------------------- kıyı çamurçulluğu
def godwit(img, x, y, s=1.0, mode='stand', phase=0.0, light=LIGHT_DUSK, rim=RIM, look=0.0):
    """Gerçekçi, hacimli gölgeli kıyı çamurçulluğu (sağa bakar).
    x,y gövde merkezi; s ölçek (s=1 -> gövde ~24 px); mode 'stand'|'fly'; phase kanat/nefes fazı (0..1)."""
    S = lambda v: v * s
    breathe = 0.6 * math.sin(phase * 2 * math.pi) if mode == 'stand' else 0
    wing_a = math.sin(phase * 2 * math.pi) if mode == 'fly' else 0
    if mode == 'stand':   # bacaklar
        for lx, kn in ((-2.0, 1.5), (2.5, -1.0)):
            p0 = (int(x + S(lx)), int(y + S(4))); p1 = (int(x + S(lx + kn)), int(y + S(12))); p2 = (int(x + S(lx)), int(y + S(21)))
            cv2.line(img, p0, p1, (52, 44, 50), max(1, int(S(1.1)))); cv2.line(img, p1, p2, (52, 44, 50), max(1, int(S(1.0))))
            cv2.line(img, p2, (int(p2[0] + S(3)), p2[1]), (52, 44, 50), 1); cv2.line(img, p2, (int(p2[0] - S(2)), p2[1]), (52, 44, 50), 1)
    if mode == 'fly':     # geriye uzanan bacaklar + uzak kanat (koyu)
        cv2.line(img, (int(x - S(7)), int(y + S(3))), (int(x - S(22)), int(y + S(4))), (52, 44, 50), max(1, int(S(1))))
        _wing(img, x, y, s, wing_a, R_WING[:-1], light, far=True)
    # kuyruk
    tail = np.array([(x - S(9), y - S(2)), (x - S(18), y - S(3.5)), (x - S(17), y + S(1)), (x - S(9), y + S(3))], np.int32)
    cv2.fillPoly(img, [tail], R_WING[1]); cv2.polylines(img, [tail[:2]], False, R_WING[3], 1)
    # gövde
    ellipsoid(img, x, y - breathe, S(12.5), S(5.8 + 0.2 * breathe), R_BIRD, light, rot=-0.16, rim=rim)
    ellipsoid(img, x + S(5.5), y - S(1.5) - breathe, S(6.5), S(4.6), R_BIRD, light, rot=-0.35, rim=rim)  # göğüs
    # ince boyun + küçük kafa
    if mode == 'fly':
        hx, hy = x + S(16), y - S(5.5)
        ellipsoid(img, x + S(11.5), y - S(3.5), S(5.0), S(2.4), R_BIRD, light, rot=-0.25, rim=rim)
    else:
        hx, hy = x + S(11.5 + look), y - S(10.5) - breathe
        ellipsoid(img, x + S(9.0), y - S(6.0) - breathe, S(2.4), S(5.4), R_BIRD, light, rot=-0.45, rim=rim)
    ellipsoid(img, hx, hy, S(3.5), S(3.1), R_BIRD, light, rot=-0.1, rim=rim)
    # göz şeridi ve göz
    cv2.line(img, (int(hx - S(2.0)), int(hy - S(1.2))), (int(hx + S(2.6)), int(hy - S(1.4))), C(R_BIRD[-1]), 1)
    ex, ey = int(hx + S(0.8)), int(hy - S(0.5))
    rect(img, ex, ey, ex + max(2, int(S(1.4))), ey + max(2, int(S(1.4))), (22, 16, 18)); img[ey, ex] = (255, 240, 220)
    # gaga: uzun, hafif yukarı kıvrık, pembe dip -> koyu uç
    n = max(8, int(S(20)))
    for i in range(n):
        u = i / (n - 1); bx = hx + S(2.8) + S(17) * u; by = hy + S(0.4) - S(2.4) * u * u
        th = max(1, int(round(S(1.3) * (1 - u) + 0.6)))
        col = mix((228, 150, 128), (58, 38, 40), ease((u - 0.35) / 0.65))
        cv2.line(img, (int(bx), int(by)), (int(bx), int(by + th - 1)), col, 1)
        if 0 <= int(by) < CH and 0 <= int(bx) < CW and u < 0.7:
            img[int(by), int(bx)] = mix(col, (255, 220, 200), 0.4)
    if mode == 'stand':   # katlanmış kanat, tüy desenli
        m = ellipsoid(img, x - S(2.5), y - S(1.8) - breathe, S(9.5), S(3.8), R_WING, light, rot=-0.2, rim=None)
        if m is not None:
            mask, (x0, y0) = m; hgt, wid = mask.shape
            yy, xx = np.mgrid[0:hgt, 0:wid]
            pat = mask & (((xx + 2 * yy) % max(3, int(S(4)))) == 0) & (BAY[y0:y0 + hgt, x0:x0 + wid] < 0.6)
            sub = img[y0:y0 + hgt, x0:x0 + wid]; sub[pat] = R_WING[0]
            pat2 = mask & (((xx + 2 * yy) % max(3, int(S(4)))) == 1)
            sub[pat2] = (sub[pat2] * 0.5 + np.array(R_WING[-1]) * 0.5).astype(np.uint8)
    else:                 # yakın kanat (açık)
        _wing(img, x, y, s, wing_a, R_WING, light, far=False)


def _wing(img, x, y, s, a, ramp, light, far):
    """Sivri uçlu, tırtıklı arka kenarlı kanat. a: -1 (aşağı) .. 1 (yukarı)."""
    S = lambda v: v * s
    sh = (x + S(-2 if far else 1), y - S(3.5 if far else 2))
    span = S(22 if far else 28)
    back = S(10) + S(14) * (1 - abs(a))
    tip = (sh[0] - back, sh[1] - span * a - S(1))
    lead = (sh[0] + S(1), sh[1] - span * 0.5 * a - S(1.5))
    base = (sh[0] - S(9), sh[1] + S(1.5))
    pts = [(sh[0] + S(5), sh[1]), lead, tip]
    for k in range(1, 5):  # arka kenar tüy tırtıkları
        u = k / 5
        px_ = tip[0] + (base[0] - tip[0]) * u; py_ = tip[1] + (base[1] - tip[1]) * u
        nrm = S(2.2) if k % 2 else 0
        pts.append((px_ + nrm * 0.3, py_ + nrm * (1 if a >= 0 else -1)))
    pts.append(base)
    poly = np.array(pts, np.int32)
    x0, y0 = poly.min(0); x1, y1 = poly.max(0) + 1
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(CW, x1), min(CH, y1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(mask, [poly - np.array([x0, y0])], 1); mask = mask.astype(bool)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(float)
    dist = np.hypot(xx - sh[0], yy - sh[1]) / max(1.0, math.hypot(tip[0] - sh[0], tip[1] - sh[1]))
    lum = (0.85 - 0.5 * np.clip(dist, 0, 1)) * (0.65 if far else 1.0) + (0.12 if a > 0 else 0)
    ramp_fill(img, mask, lum, ramp, x0, y0)
    img[y0:y1, x0:x1][mask & (dist > 0.78)] = ramp[0]
    cv2.line(img, (int(sh[0] + S(4)), int(sh[1])), (int(lead[0]), int(lead[1])), C(ramp[-1]), 1)
    cv2.line(img, (int(lead[0]), int(lead[1])), (int(tip[0]), int(tip[1])), C(ramp[-2]), 1)


def mirrored(img, draw, x, *args, light=LIGHT_DUSK, **kw):
    """Karakteri sola baktır: aynalanmış konumda ayrı tuvale çizip yatay çevirir.
    draw(tmp, x, ...) imzalı bir fonksiyon (örn. godwit). light, çevrilmeden önceki yön."""
    tmp = np.zeros_like(img)
    lx, ly, lz = light
    draw(tmp, CW - 1 - x, *args, light=(-lx, ly, lz), **kw)
    tmp = tmp[:, ::-1]; m = tmp.any(2)
    img[m] = tmp[m]
    return m


def outlined(img, draw, *args, col=(26, 16, 34), **kw):
    """Karakteri 1 px koyu konturla çiz (klasik 8-bit sprite görünümü)."""
    tmp = np.zeros_like(img); draw(tmp, *args, **kw)
    m = tmp.any(2)
    edge = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~m
    img[edge] = col; img[m] = tmp[m]


_PAL = {}


def palettize(img, key, n=40):
    """Sahneyi sınırlı palete indir (8-bit dili). Palet her sahne için ilk karede bir kez çıkarılır."""
    if key not in _PAL:
        q = Image.fromarray(img).quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pal = np.array(q.getpalette()[:n * 3], float).reshape(-1, 3)
        g = (np.arange(32) * 8 + 4).astype(float)
        cube = np.stack(np.meshgrid(g, g, g, indexing='ij'), -1).reshape(-1, 3)
        idx = np.argmin(((cube[:, None, :] - pal[None]) ** 2).sum(-1), 1)
        _PAL[key] = pal.astype(np.uint8)[idx].reshape(32, 32, 32, 3)
    lut = _PAL[key]; q = img >> 3
    return lut[q[..., 0], q[..., 1], q[..., 2]]


def tiny_bird(img, x, y, phase, col=(34, 24, 54)):
    a = math.sin(phase * 2 * math.pi)
    for dx in range(-4, 5):
        dy = -abs(dx) * a * 0.7
        xx, yy = int(x + dx), int(y + dy)
        if 0 <= xx < CW and 0 <= yy < CH:
            img[yy, xx] = col


def sparkle(img, x, y, size=4, col=(255, 250, 222)):
    for i in range(-size, size + 1):
        for (xx, yy) in ((x + i, y), (x, y + i)):
            if 0 <= xx < CW and 0 <= yy < CH:
                img[int(yy), int(xx)] = col if abs(i) <= size // 2 else GLOW
    halo(img, x, y, size * 4, GLOW, 0.7, 0.4)


def upscale(small, crop=None):
    if crop:
        x0, y0, cw, ch = crop
        x0 = max(0, min(CW - cw, int(x0))); y0 = max(0, min(CH - ch, int(y0)))
        small = small[y0:y0 + ch, x0:x0 + cw]
    return np.ascontiguousarray(cv2.resize(small, (W, H), interpolation=cv2.INTER_NEAREST))


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
