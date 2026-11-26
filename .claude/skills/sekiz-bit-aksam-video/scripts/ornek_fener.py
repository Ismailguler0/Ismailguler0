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


def sea_storm(img, t):
    dgrad(img, [(HZ, (58, 40, 92)), (720, (26, 22, 62)), (CH, (10, 10, 28))], bands=5)
    for j in range(26):
        y0 = HZ + 4 + j * j * 0.55 + j * 3
        A = 1.5 + j * 0.45; lam = 38 + j * 7; sp = 30 + j * 4
        xs = np.arange(0, CW, 2)
        ys = y0 + A * np.sin(2 * math.pi * (xs + sp * t) / lam + j * 1.7)
        col = mix((120, 90, 150), (40, 34, 80), j / 26)
        pts = np.stack([xs, ys], 1).astype(np.int32)
        cv2.polylines(img, [pts], False, C(col), 1)
        crest = np.sin(2 * math.pi * (xs + sp * t) / lam + j * 1.7) < -0.85
        for x, y in pts[crest]:
            if 0 <= y < CH and BAY[y % CH, x] < 0.6:
                img[max(0, y - 1), x] = (200, 200, 230)
    # kayaya doğru gelen dev dalga
    for tc in CRASHES:
        a = t - (tc - 1.3)
        if 0 <= a < 1.3:
            k = a / 1.3; wx = int(-120 + (300 + 120) * k); h = int(24 + 60 * k)
            base = HZ + 60
            pts = np.array([(wx - 240, base), (wx - 120, base - h * 0.45), (wx - 30, base - h * 0.95), (wx + 4, base - h),
                            (wx + 22, base - h * 0.8), (wx + 26, base - h * 0.55), (wx + 14, base - h * 0.5), (wx + 40, base)], np.int32)
            cv2.fillPoly(img, [pts], (66, 52, 118))
            body = np.array([(wx - 200, base), (wx - 90, base - h * 0.5), (wx - 20, base - h * 0.8), (wx, base)], np.int32)
            cv2.fillPoly(img, [body], (96, 76, 150))
            cv2.polylines(img, [pts[1:7]], False, (236, 238, 252), 3)
            for q in range(0, int(h * 0.9), 3):  # kıvrılan tepe köpüğü
                dither_rect(img, wx - 60 + q * 0.4, base - h + q * 0.3, wx + 24, base - h + q * 0.3 + 3, (226, 230, 250), 0.55 - q / (h * 2))


def spray(img, t):
    for i, tc in enumerate(CRASHES):
        a = t - tc
        if not (0 <= a < 1.8):
            continue
        r = np.random.default_rng(100 + i)
        # köpük patlaması: kabarık topaklar, kenarları noktalı
        if a < 1.5:
            H = 230 * math.sin(math.pi * min(a / 1.05, 1.0)) * (1 if a < 1.05 else max(0, 1 - (a - 1.05) / 0.45))
            for b in range(46):
                u = r.random(); v = r.random()
                bx = 268 + u * 96 - 40 * a * (u - 0.5)
                by = 626 - H * (v ** 0.6)
                br = (5 + 16 * r.random()) * (1 - 0.5 * v) * (1 - 0.4 * a)
                if br < 2:
                    continue
                x0, x1, y0, y1 = max(0, int(bx - br)), min(CW, int(bx + br + 1)), max(0, int(by - br)), min(CH, int(by + br + 1))
                if x0 >= x1 or y0 >= y1:
                    continue
                d = np.hypot(_xx[y0:y1, x0:x1] - bx, _yy[y0:y1, x0:x1] - by) / br
                sub = img[y0:y1, x0:x1]; bb = BAY[y0:y1, x0:x1]
                core = d < 0.62; ring = (d >= 0.62) & (d < 1) & (bb < 1.25 * (1 - d) + 0.1)
                shade = (_yy[y0:y1, x0:x1] - by) / br > 0.35
                sub[core & ~shade] = (246, 248, 255); sub[core & shade] = (178, 190, 232)
                sub[ring] = (206, 214, 244)
        for _ in range(140):
            x0 = 262 + r.random() * 110; vx = -90 + r.random() * 150; vy = -(260 + r.random() * 260)
            sz = 1 + int(r.random() * 2.5); life = 1.0 + r.random() * 0.7
            if a > life:
                continue
            x = x0 + vx * a; y = 600 + vy * a + 0.5 * 520 * a * a
            fade = a / life
            if r.random() < fade * 0.8 or y > 660:
                continue
            col = (244, 246, 255) if r.random() < 0.6 else (170, 190, 230)
            rect(img, x, y, x + sz, y + sz, col)
        # yüzeyde yayılan köpük
        if a > 0.6:
            w = int(60 + 140 * min(1, (a - 0.6) / 1.0))
            dither_rect(img, 300 - w, 628, 300 + 20, 640, (220, 226, 245), 0.55 * (1 - (a - 0.6) / 1.2))


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
    sea_storm(img, t)
    th = beam_angle(t)
    lighthouse(img, t, th)
    spray(img, t)
    rain(img, t)
    img = palettize(img, 'fener', 48)
    glare_fx(img, t, th)            # kamaşma paletten sonra (beyaz uçlar kaybolmasın)
    return img


def shake(t):
    for tc in CRASHES:
        a = t - tc
        if 0 <= a < 0.4:
            k = int(3 * (1 - a / 0.4))
            return (k if int(a * 30) % 2 else -k), (k if int(a * 30) % 3 else 0)
    return 0, 0


def frame_at(t):
    img = world(t)
    if t < T2 or t >= T3:
        fr = upscale(img)
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
