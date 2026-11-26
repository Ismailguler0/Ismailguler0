"""TEST: fırtınada deniz feneri – dalgalar kayalara çarpar, ışık 360° döner, kameraya gelince göz kamaşır."""
import math
import numpy as np
from pix8 import *

DUR, FPS = 12.5, 30
T2, T3, SIG_T = 6.8, 10.0, 10.1
CAPS = []
MUSIC = dict(bpm=78, root=196.0)
PERIOD = 3.5                       # ışığın bir tam turu (sn)
GLARES = [3.0, 6.5, 10.0]          # ışığın tam kameraya baktığı anlar
CRASHES = [1.0, 3.7, 5.8, 7.6, 9.4, 11.4]
HZ = 600
LAMP = (380, 293)

SFX = [(c, 'crash') for c in CRASHES] + [(g, 'glare') for g in GLARES] + \
      [(0.0, 'wind'), (3.0, 'wind'), (6.0, 'wind'), (9.0, 'wind'), (T2, 'whoosh')]


def beam_angle(t):
    return 2 * math.pi * (t - GLARES[0]) / PERIOD     # cos=1 -> kameraya bakıyor


STORM = [(0, (12, 10, 32)), (200, (30, 24, 64)), (420, (70, 42, 96)), (560, (150, 74, 106)), (600, (214, 112, 108))]
CL = [(0, 90, 360, 16, (24, 20, 52), (86, 56, 110), 26), (220, 170, 300, 14, (30, 24, 60), (104, 62, 116), 34),
      (60, 260, 420, 18, (38, 28, 70), (126, 70, 118), 22), (330, 360, 260, 12, (50, 34, 80), (160, 84, 116), 30),
      (0, 450, 380, 14, (66, 40, 90), (196, 100, 112), 18), (280, 520, 300, 10, (92, 52, 100), (226, 124, 112), 24)]
R_WHITE = [(70, 62, 104), (150, 140, 172), (226, 220, 222), (250, 246, 238)]
R_RED = [(70, 22, 40), (130, 40, 56), (196, 66, 70), (236, 104, 88)]
ROCK = np.array([(250, 640), (268, 606), (300, 590), (326, 560), (352, 556), (408, 552), (440, 560), (470, 548),
                 (500, 566), (540, 560), (540, 700), (250, 700)], np.int32)
_rm = np.zeros((CH, CW), np.uint8); cv2.fillPoly(_rm, [ROCK], 1); ROCK_M = _rm > 0
_yy, _xx = np.mgrid[0:CH, 0:CW]
_rng = np.random.default_rng(4)
ROCK_LUM = np.clip(0.18 + 0.55 * np.clip((470 - _xx) / 220, 0, 1) * np.clip((700 - _yy) / 150, 0, 1)
                   + 0.12 * (_rng.random((CH, CW)) < 0.08), 0, 1)


# ---------------------------------------------------------------- fırtına denizi
NL = 12                                  # dalga katmanı (uzak -> yakın), üst üste biner
SUN_X = 90                               # ufuktaki ışığın x'i (yansıma sütunu)
_nz = np.random.default_rng(21).random((64, 64))
_nz = cv2.resize(_nz, (256, 256), interpolation=cv2.INTER_CUBIC)
_nz = (_nz - _nz.min()) / (_nz.max() - _nz.min())            # dantel köpük için yumuşak gürültü


def layer_params(j):
    d = j / (NL - 1)
    return dict(d=d, base=HZ + 8 + 320 * d ** 1.6, A=6 + 92 * d ** 1.4, lam=60 + 320 * d, v=26 + 150 * d,
                ph=j * 2.3, ramp=[mix((70, 40, 96), (14, 12, 38), d ** 0.6), mix((132, 70, 120), (40, 32, 88), d ** 0.6),
                                  mix((196, 104, 128), (86, 70, 150), d ** 0.6), mix((246, 160, 140), (164, 152, 218), d ** 0.6)])


def crest_y(p, xs, t):
    k = 2 * math.pi / p['lam']; j = p['ph']
    s_ = (0.6 * np.sin(k * (xs - p['v'] * t) + j) + 0.28 * np.sin(2.3 * k * (xs - 0.6 * p['v'] * t) + 2 * j)
          + 0.22 * np.sin(0.7 * k * (xs + 0.35 * p['v'] * t) + 0.5 * j)
          + 0.14 * np.sin(5.1 * k * (xs - 1.4 * p['v'] * t) + 3 * j)) / 1.2          # üstünde çalkantı
    c = np.clip((s_ + 1) / 2, 0, 1) ** 1.7                                   # sivri, düzensiz tepeler
    env = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2 * math.pi * xs / (p['lam'] * 5.3) - t * 0.55 + j))   # dalga setleri
    heave = 0.18 * math.sin(t * 1.1 + j * 1.7)
    top = p['base'] - p['A'] * (0.25 + 0.85 * env) * (0.12 + c) - p['A'] * heave
    return top, c * (0.35 + 0.65 * env)


def draw_layer(img, j, t):
    p = layer_params(j); xs = np.arange(CW); d = p['d']
    top, c = crest_y(p, xs, t)
    slope = np.gradient(top)
    y0 = max(0, int(top.min()) - 2)
    yy = np.arange(y0, CH)[:, None]
    rel = (yy - top[None, :]) / max(5.0, p['A'] * 0.8)
    m = rel >= 0
    lum = 0.16 + 0.76 * np.exp(-rel * 2.0) * (0.35 + 0.65 * c[None, :])
    _rf(img, m, np.clip(lum, 0, 1), p['ramp'], y0)
    sub = img[y0:]
    # suya özgü kısa yatay parlama çizgileri (yüzeyde akar)
    hz = _nz[(yy * 3 + j * 29) % 256, ((xs[None, :] - p['v'] * 0.7 * t) / (6 + 10 * d)).astype(int) % 256]
    streak = m & (rel > 0.15) & (rel < 2.5) & (hz > 0.8 - 0.12 * np.exp(-rel)) & ((yy % 3) == 0)
    sub[streak] = p['ramp'][2]
    # yaşayan köpük: tepede beyaz, yamaçta delik deşik dantel, zamanla dağılır
    nzx = ((xs[None, :] - p['v'] * 0.9 * t) * (1.2 - 0.6 * d)).astype(int) % 256
    nzy = ((rel * 22 + j * 37 + t * 6)).astype(int) % 256
    lace = _nz[nzy, nzx]
    cap = np.clip((c[None, :] - 0.4) / 0.35, 0, 1)
    foam = m & (rel < 0.1 + 0.55 * cap) & (lace > 0.5 + 0.45 * rel / (0.1 + 0.55 * cap + 1e-6)) & (cap > 0)
    sub[foam & (BAY[y0:, :] < 0.85)] = (238, 240, 255)
    sub[foam & (BAY[y0:, :] >= 0.85)] = (180, 190, 236)
    # tepeden arkaya dökülen köpük izleri
    for x in np.nonzero(c > 0.45)[0][::2]:
        L = int(4 + 22 * d * (c[x] - 0.45) / 0.55)
        for q in range(L):
            xx = x - q; yy_ = int(top[min(CW - 1, max(0, xx))]) + 1 + q // 4
            if 0 <= xx < CW and 0 <= yy_ < CH and BAY[yy_, xx] < 0.7 - q / (L + 1) * 0.6:
                img[yy_, xx] = (214, 220, 250)
    # güneş yansıması: yalnız tepelerde küçük, seyrek parıltılar
    w = int(30 + 80 * d)
    for x in range(max(0, SUN_X - w), min(CW, SUN_X + w)):
        fall = 1 - abs(x - SUN_X) / w
        if c[x] > 0.25 and _nz[int(t * 30 + j * 13) % 256, (x * 5 + j * 7) % 256] > 0.72 - 0.15 * fall:
            yy_ = int(top[x]) + 1
            if 0 <= yy_ < CH:
                img[yy_, x] = (255, 214, 150)
                if x + 1 < CW:
                    img[yy_, x + 1] = (255, 190, 120)


def _rf(img, m, lum, ramp, y0):
    sub = img[y0:]
    n = len(ramp); v = np.clip(lum, 0, 0.9999) * (n - 1); k = np.floor(v).astype(int); f = v - k
    k2 = np.minimum(k + 1, n - 1)
    f = np.clip((f - 0.5) / (2 * HARD_W) + 0.5, 0, 1)
    pick = np.where(BAY[y0:y0 + m.shape[0], :m.shape[1]] < f, k2, k)
    R = np.array(ramp, np.uint8); sub[m] = R[pick[m]]


def breaker(img, t):
    """Her çarpmadan önce kayaya koşan, tepesi kıvrılan dev dalga."""
    for i, tc in enumerate(CRASHES):
        a = t - (tc - 1.4)
        if not (0 <= a < 1.45):
            continue
        k = min(1.0, a / 1.4); wx = -160 + (270 + 160) * ease(k) ** 0.8
        h = 70 + 80 * k; base = 690
        xs = np.arange(max(0, int(wx - 330)), min(CW, int(wx + 40)))
        if len(xs) < 2:
            continue
        u = (xs - (wx - 330)) / 370
        prof = np.where(u < 0.82, (np.clip(u, 0, 1) / 0.82) ** 1.8, 1 - (np.clip(u - 0.82, 0, 1) / 0.18) ** 0.7 * 0.9)
        top = base - h * np.clip(prof, 0, 1)
        y0 = max(0, int(top.min()) - 2); yy = np.arange(y0, CH)[:, None]
        m = (yy >= top[None, :]) & (yy < base + 30)
        rel = (yy - top[None, :]) / h
        lum = np.clip(0.95 - rel * 1.5, 0, 1) * (0.5 + 0.5 * np.clip(u[None, :] * 1.2, 0, 1))
        sub = img[:, xs[0]:xs[-1] + 1]
        _rf(sub, m, lum, [(16, 14, 44), (46, 38, 98), (92, 78, 156), (168, 160, 218)], y0)
        # kıvrılan beyaz dudak
        lipx = wx - 10; lipy = base - h
        r = np.random.default_rng(300 + i)
        for b in range(26):
            ang = math.pi * (0.1 + 0.9 * b / 26); rr = h * 0.22
            bx = lipx + rr * math.cos(ang) * 1.3 + r.random() * 6; by = lipy + rr * (1 - math.sin(ang)) + r.random() * 6
            disc(img, bx, by, 3 + r.random() * 4, (240, 242, 255) if r.random() < 0.7 else (190, 200, 240))
        # rüzgarın geriye savurduğu köpük
        for q in range(60):
            life = r.random(); age = (a * 1.8 + life) % 1.0
            x = lipx - 20 - age * 140 * (0.5 + r.random()); y = lipy - 10 - age * 30 + r.random() * 16
            if r.random() > age:
                rect(img, x, y, x + 1 + int(r.random() * 2), y + 1, (226, 230, 252))
        # dalganın yüzündeki köpük şeritleri
        for q in range(30):
            x = int(wx - 40 - r.random() * 220)
            if 0 <= x - xs[0] < len(top):
                ty = int(top[x - xs[0]]); L = int(6 + r.random() * 18)
                for kk in range(0, L, 2):
                    yy_ = ty + 6 + kk
                    if 0 <= yy_ < CH and 0 <= x - kk // 3 < CW:
                        img[yy_, x - kk // 3] = (176, 186, 232)


def sea_storm(img, t, part):
    if part == 'back':
        dgrad(img, [(HZ, (70, 50, 110)), (720, (26, 22, 62)), (CH, (10, 10, 28))], bands=5)
        for j in range(NL):
            if layer_params(j)['base'] < 655:
                draw_layer(img, j, t)
    else:
        for j in range(NL):
            if layer_params(j)['base'] >= 655:
                draw_layer(img, j, t)


def spray(img, t):
    for i, tc in enumerate(CRASHES):
        a = t - tc
        if not (0 <= a < 2.4):
            continue
        r = np.random.default_rng(100 + i)
        # su sisi: yayılan, sönen noktalı bulut
        mist = max(0.0, 1 - a / 2.4)
        halo(img, 300 - 30 * a, 520 - 40 * a, 120 + 120 * a, (190, 196, 236), 0.75 * mist, 0.5 * mist, 0.8)
        # dev köpük sütunu (fener lambasına kadar)
        if a < 1.9:
            H = 380 * math.sin(math.pi * min(a / 1.2, 1.0)) if a < 1.2 else 380 * max(0, 1 - (a - 1.2) / 0.7) * 0.6
            spread = 60 + 120 * a
            for b in range(90):
                u = r.random(); v = r.random()
                bx = 300 + (u - 0.5) * spread - 50 * a * v
                by = 650 - H * (v ** 0.55)
                br = (6 + 20 * r.random()) * (1 - 0.55 * v) * (1 - 0.35 * a)
                if br < 2:
                    continue
                x0, x1, y0, y1 = max(0, int(bx - br)), min(CW, int(bx + br + 1)), max(0, int(by - br)), min(CH, int(by + br + 1))
                if x0 >= x1 or y0 >= y1:
                    continue
                d = np.hypot(_xx[y0:y1, x0:x1] - bx, _yy[y0:y1, x0:x1] - by) / br
                sub = img[y0:y1, x0:x1]; bb = BAY[y0:y1, x0:x1]
                core = d < 0.62; ring = (d >= 0.62) & (d < 1) & (bb < 1.25 * (1 - d) + 0.1)
                shade = (_yy[y0:y1, x0:x1] - by) / br > 0.35
                sub[core & ~shade] = (246, 248, 255); sub[core & shade] = (178, 190, 232); sub[ring] = (206, 214, 244)
        # damlalar
        for _ in range(320):
            x0 = 250 + r.random() * 120; vx = -160 + r.random() * 260; vy = -(300 + r.random() * 420)
            sz = 1 + int(r.random() * 3); life = 1.2 + r.random() * 0.9
            if a > life:
                continue
            x = x0 + vx * a; y = 650 + vy * a + 0.5 * 560 * a * a
            if r.random() < (a / life) * 0.8 or y > 700:
                continue
            rect(img, x, y, x + sz, y + sz, (244, 246, 255) if r.random() < 0.6 else (170, 190, 230))
        # kayadan aşağı akan şelaleler (ince, düzensiz, kesik)
        if 0.6 < a < 2.4:
            fl = min(1.0, (a - 0.6) / 0.5) * max(0.0, 1 - (a - 1.6) / 0.8)
            for q in range(9):
                x = int(266 + r.random() * 200)
                ytop = int(np.interp(x, ROCK[:10, 0], ROCK[:10, 1])) + 2
                off = int((a * 260 + r.random() * 40)) % 14
                for y in range(ytop + off % 6, 700, 1):
                    if ((y + off) % 9) < 6 and r.random() < fl:
                        xx = x + int(2 * math.sin(y * 0.15 + q))
                        if 0 <= xx < CW - 1:
                            img[y, xx] = (226, 232, 252)
        # dipte köpük topakları
        if 0.4 < a < 2.4:
            fa = max(0.0, 1 - (a - 0.4) / 2.0)
            for b in range(int(40 * fa)):
                bx = 300 - r.random() * (60 + 220 * min(1, (a - 0.4) / 1.2)); by = 646 + r.random() * 20
                disc(img, bx, by, 1 + r.random() * 3, (232, 236, 252) if r.random() < 0.6 else (180, 192, 236))


def rain(img, t):
    r = np.random.default_rng(7)
    for i in range(220):
        x = (r.random() * (CW + 200) - 100 + 140 * t * (1 + r.random())) % (CW + 100) - 50
        y = (r.random() * CH + 900 * t * (0.8 + r.random() * 0.4)) % CH
        cv2.line(img, (int(x), int(y)), (int(x - 3), int(y + 8)), (110, 100, 160), 1)


def lighthouse(img, t, th):
    c, s = math.cos(th), math.sin(th)
    L = (-0.6, -0.3, 0.7)
    ramp_fill(img, ROCK_M, ROCK_LUM, R_STONE, 0, 0)
    cv2.polylines(img, [ROCK[:10]], False, C((150, 92, 120)), 1)
    # kule: bantlı, yukarı daralan silindir
    segs = [(556, 500, 34, R_WHITE), (500, 452, 32, R_RED), (452, 404, 30, R_WHITE), (404, 360, 28, R_RED), (360, 330, 27, R_WHITE)]
    for (yb, yt, hw, rp) in segs:
        cylinder(img, LAMP[0] - hw, LAMP[0] + hw, yt, yb, rp, light=L, rim=(170, 170, 230), cap=False)
    for y in (500, 452, 404):  # pencereler
        rect(img, LAMP[0] - 4, y - 30, LAMP[0] + 4, y - 18, (255, 196, 110) if y != 452 else (40, 30, 56))
    # galeri
    rect(img, 336, 322, 424, 332, (34, 26, 52)); cv2.line(img, (336, 322), (423, 322), (130, 110, 160), 1)
    for x in range(338, 424, 7):
        cv2.line(img, (x, 312), (x, 322), (40, 30, 60), 1)
    cv2.line(img, (338, 312), (422, 312), (50, 40, 72), 1)
    # fener odası
    bright = 0.35 + 0.65 * max(0.0, c)
    rect(img, 356, 266, 404, 314, mix((60, 50, 70), (255, 236, 170), bright))
    disc(img, LAMP[0], LAMP[1], 10, mix((200, 150, 90), (255, 255, 236), bright))
    for x in (356, 372, 388, 403):
        cv2.line(img, (x, 266), (x, 313), (28, 22, 40), 2)
    cv2.line(img, (356, 266), (403, 266), (28, 22, 40), 2)
    cv2.fillPoly(img, [np.array([(350, 266), (410, 266), (396, 248), (380, 238), (364, 248)], np.int32)], (110, 34, 50))
    cv2.line(img, (350, 266), (380, 238), (176, 70, 74), 1)
    rect(img, 378, 228, 382, 238, (40, 30, 56))
    glow_layers(img, LAMP[0], LAMP[1], 60 + 60 * max(0.0, c), (255, 220, 150))
    # dönen huzme: sola/sağa uzanır, boyu |sin| ile
    if abs(s) > 0.08:
        Lb = 560 * abs(s) ** 0.6; dirx = -1 if s > 0 else 1; spread = 26 + 60 * (1 - abs(s))
        tip = (LAMP[0] + dirx * Lb, LAMP[1] - 6)
        poly = np.array([(LAMP[0], LAMP[1] - 6), (tip[0], tip[1] - spread), (tip[0], tip[1] + spread), (LAMP[0], LAMP[1] + 6)], np.int32)
        m = np.zeros((CH, CW), np.uint8); cv2.fillPoly(m, [poly], 1); m = m > 0
        dist = np.abs(_xx - LAMP[0]) / max(1, Lb)
        lev = (0.55 * (1 - dist)) * (0.5 + 0.5 * abs(s)) * (1 if c < 0.3 else 0.6)
        blend_mask(img, m & (BAY < lev), (255, 236, 180), 0.55)
        blend_mask(img, m & (BAY < lev * 0.4), (255, 250, 220), 0.7)


def glare_fx(img, t, th):
    g = max(0.0, math.cos(th)) ** 10
    if g < 0.02:
        return
    lx, ly = LAMP
    halo(img, lx, ly, 120 + 380 * g, (255, 236, 190), 0.95, 0.65, 0.9)
    halo(img, lx, ly, 40 + 160 * g, (255, 252, 236), 1.0, 0.9, 1.2)
    th_ = int(1 + 4 * g)
    cv2.line(img, (0, ly), (CW, ly), (255, 246, 220), th_)
    cv2.line(img, (lx, ly - int(260 * g)), (lx, ly + int(260 * g)), (255, 246, 220), max(1, th_ - 1))
    for d in (-1, 1):
        cv2.line(img, (lx, ly), (int(lx + d * 120 * g), int(ly - 120 * g)), (255, 236, 200), 1)
        cv2.line(img, (lx, ly), (int(lx + d * 120 * g), int(ly + 120 * g)), (255, 236, 200), 1)
    if g > 0.25:  # tüm ekran kamaşması: önce noktalı, zirvede düz beyaz
        lev = min(1.0, (g - 0.25) * 1.6)
        blend_mask(img, BAY < lev, (255, 252, 240), 1.0)
        if g > 0.75:
            img[:] = (img * 0.3 + np.array([255, 252, 240]) * 0.7).astype(np.uint8)


def world(t):
    img = canvas(); sky(img, STORM, HZ)
    glow_layers(img, 90, HZ - 6, 200, (240, 120, 100))
    for (x, y, Lc, thc, dark, lit, sp) in CL:
        cloud_band(img, x, y, Lc, thc, dark, lit, t, sp)
    sea_storm(img, t, 'back')
    th = beam_angle(t)
    lighthouse(img, t, th)
    breaker(img, t)
    sea_storm(img, t, 'front')
    spray(img, t)
    rain(img, t)
    img = palettize(img, 'fener', 48)
    glare_fx(img, t, th)            # kamaşma paletten sonra (beyaz uçlar kaybolmasın)
    return img


def shake(t):
    for tc in CRASHES:
        a = t - tc
        if 0 <= a < 0.5:
            k = int(5 * (1 - a / 0.5))
            return (k if int(a * 30) % 2 else -k), (k if int(a * 30) % 3 else 0)
    return 0, 0


def frame_at(t):
    img = world(t)
    if t < T2 or t >= T3:
        dx, dy = shake(t)
        fr = upscale(np.roll(img, (dy, dx), (0, 1)) if (dx or dy) else img)
    else:
        tl = t - T2; k = ease(tl / 1.2)
        cx = int(270 + (LAMP[0] - 270) * k); cy = int(480 + (LAMP[1] + 60 - 480) * k)
        dx, dy = shake(t)
        fr = upscale(img, (cx - 135 + dx, cy - 240 + dy, 270, 480))
    if T3 <= t < T3 + 0.9:      # beyazdan geri açılma
        a = 1 - (t - T3) / 0.9
        fr[:] = (fr * (1 - a) + np.array([255, 250, 236]) * a).astype(np.uint8)
    captions(fr, t, CAPS)
    signature(fr, t, SIG_T)
    return fr
