"""EŞİK – Göbekli Tepe (katman yığma, iri 8-bit piksel, sabit palet)."""
import math, sys
import numpy as np, cv2
sys.path.insert(0, '/home/user/Ismailguler0/.claude/skills/sekiz-bit-aksam-video/scripts')
sys.path.insert(0, '/home/user/esik-araclar/ortak')
from pix8 import signature, captions
from ymotor import *

DUR, FPS, SIG_T = 39.6, 30, 37.2
A_, B_, C_, D_, E_, F_, G_, H_, I_ = 0.0, 3.48, 7.46, 9.54, 13.34, 17.7, 22.64, 28.6, 34.62
STAMP = 16.0          # 16. sn: "11.600 YIL" damgası
HOOK2 = 17.7          # metindeki 2. kanca: toprak her şeyi gömer
MUSIC = dict(bpm=72, root=146.8)
CAPS = [(0.0, 3.4, "Piramitlerden [7000 yıl] önce!", 1608), (3.48, 4.8, "[Şanlıurfa]'da bir tepe", 1608),
        (4.86, 7.4, "Altında dev [T taşları]", 1608), (7.46, 9.5, "Boyu [5,5 metre]", 1608),
        (9.54, 13.3, "[Tilki], [yaban domuzu], [akrep]", 1608), (13.34, 15.9, "Yaşı: [11.600 yıl]", 1608),
        (15.98, 17.6, "[Yazı] bile yokken...", 1608), (17.7, 22.5, "Hepsini [toprağa gömdüler]?", 1608),
        (22.64, 24.5, "Neden? [Kimse bilmiyor]", 1608), (24.62, 28.5, "Belki [kendiliğinden] doldu", 1608),
        (28.6, 31.7, "Sadece [onda biri] kazıldı", 1608), (31.8, 34.5, "Asıl sır [toprağın altında]", 1608),
        (34.62, 37.2, "Sence [kim yaptı?]", 1608)]
SFX = ([(0.0, 'boom'), (0.05, 'glare'), (B_, 'whoosh'), (4.86, 'rumble'), (C_, 'whoosh'), (D_, 'whoosh'), (E_, 'whoosh'),
        (STAMP, 'boom'), (STAMP + 0.05, 'crash'), (HOOK2, 'rumble'), (HOOK2 + 0.05, 'whoosh'), (G_, 'whoosh'), (24.7, 'wind'),
        (H_, 'whoosh'), (31.8, 'sparkle'), (I_, 'whoosh'), (SIG_T + 0.05, 'chime')]
       + [(13.5 + k * 0.2, 'tick') for k in range(12)])

set_palette([
    (10, 8, 18), (22, 18, 36), (40, 30, 60), (70, 50, 90), (110, 70, 110), (200, 110, 100), (250, 170, 110), (255, 220, 150),
    (240, 228, 200), (214, 200, 170), (180, 164, 130), (140, 124, 96), (96, 82, 64), (60, 50, 42),
    (170, 128, 80), (130, 94, 60), (90, 64, 42), (50, 36, 28),
    (176, 170, 90), (130, 136, 64), (86, 96, 50),
    (226, 60, 58), (255, 150, 60), (110, 170, 200), (200, 236, 250), (250, 250, 250), (206, 160, 120)])

STONE, STONE2, DIRT, GRASS = (214, 200, 170), (180, 164, 130), (150, 110, 70), (150, 150, 70)

FOX = ["..x....x.", "..xx..xx.", "...xxxx..", "xxxxxxx..", ".xxxxxx..", ".x.x.x.x."]
BOAR = ["...xxxxxx.", "xxxxxxxxxx", "xxxxxxxxx.", ".xxxxxxx..", ".x.x..x.x."]
SCORP = ["x.....x", ".x...x.", "..xxx..", "x.xxx.x", "..xxx..", "...x...", "...x...", "..x...."]


def carve(V, bmp, x0, z0, yface, col, sc=1):
    for r, row in enumerate(bmp):
        for c, ch in enumerate(row):
            if ch == 'x':
                zz = z0 + (len(bmp) - 1 - r) * sc
                V.put((V.x >= x0 + c * sc) & (V.x < x0 + (c + 1) * sc) & (V.z >= zz) & (V.z < zz + sc) & (np.abs(V.y - yface) < 0.7), col)


def pillar_model():
    V = Vox(28, 12, 64); x, y, z = V.x, V.y, V.z
    V.put((x >= 10) & (x < 18) & (y >= 3) & (y < 9) & (z < 46), STONE)
    V.put((x >= 3) & (x < 25) & (y >= 3) & (y < 9) & (z >= 46) & (z < 58), STONE)
    V.put((x >= 3) & (x < 25) & (y >= 3) & (y < 9) & (z >= 46) & (z < 58) & (((x + z).astype(int) % 7) == 0), STONE2)
    V.put((x >= 10) & (x < 18) & (y >= 3) & (y < 9) & (z < 46) & (((x * 3 + z).astype(int) % 9) == 0), STONE2)
    for side in (8.6, 2.4):                                         # kabartmalar (iki yüz)
        carve(V, FOX, 4, 48, side, (96, 82, 64), 2)
        carve(V, BOAR, 9, 30, side, (96, 82, 64), 1)
        carve(V, SCORP, 11, 14, side, (96, 82, 64), 1)
    for s in (-1, 1):                                                # gövdeye oyulmuş kollar
        V.put((np.abs(x - 14 - s * 3.5) < 0.6) & (np.abs(y - 8.6) < 0.7) & (z >= 22) & (z < 40), (140, 124, 96))
    V.put((x >= 11) & (x < 17) & (np.abs(y - 8.6) < 0.7) & (z == 22), (140, 124, 96))
    return V.bake()


def pyramid_model():
    V = Vox(36, 36, 22); x, y, z = V.x, V.y, V.z
    m = (np.maximum(np.abs(x - 17.5), np.abs(y - 17.5)) <= 17 - z * 0.8)
    V.put(m, (240, 228, 200)); V.put(m & (z.astype(int) % 3 == 0), (214, 200, 170))
    return V.bake()


def enclosure(level=0, n=96):
    V = Vox(n, n, 36); x, y, z = V.x, V.y, V.z
    c = (n - 1) / 2; r = np.hypot(x - c, y - c); a = np.arctan2(y - c, x - c)
    V.put((r < 44) & (z < 1), (180, 164, 130))
    wall = (r >= 39) & (r < 45) & (z < 9)
    V.put(wall, (140, 124, 96)); V.put(wall & (((a * 20).astype(int) + z.astype(int)) % 3 == 0), (96, 82, 64))
    for k in range(10):                                              # çevre dikilitaşları
        ang = k / 10 * 2 * math.pi; px, py = c + 34 * math.cos(ang), c + 34 * math.sin(ang)
        tx, ty = -math.sin(ang), math.cos(ang)                       # duvara teğet yönde yassı
        u = (x - px) * tx + (y - py) * ty; v = (x - px) * math.cos(ang) + (y - py) * math.sin(ang)
        V.put((np.abs(u) < 1.6) & (np.abs(v) < 1.1) & (z < 16), STONE)
        V.put((np.abs(u) < 1.6) & (v > -1.1) & (v < 4.5) & (z >= 16) & (z < 20), STONE)
    for s in (-1, 1):                                                # iki büyük orta taş
        V.put((np.abs(x - c - s * 7) < 1.6) & (np.abs(y - c) < 3) & (z < 26), STONE)
        V.put((np.abs(x - c - s * 7) < 1.6) & (np.abs(y - c) < 7) & (z >= 26) & (z < 31), STONE)
        V.put((np.abs(x - c - s * 7) < 1.7) & (np.abs(y - c - 1) < 0.6) & (z >= 10) & (z < 22) & ((z.astype(int) % 4) < 2), (140, 124, 96))
    if level > 0:
        soil = (r < 46) & (z < level) & (V.S[..., 3] == 0)
        V.put(soil, DIRT); V.put(soil & (((x * 7 + y * 3 + z * 5).astype(int) % 11) == 0), (130, 94, 60))
        V.put((r < 46) & (z == level - 1) & (V.S[..., 3] > 0) & soil, (170, 128, 80))
    return V


def hill_model(dig=False, xray=False):
    n = 112; E = enclosure(0, 96)
    V = Vox(n, n, 44); x, y, z = V.x, V.y, V.z
    o = (n - 96) // 2
    c = (n - 1) / 2; r = np.hypot(x - c, y - c)
    h = 40 * np.clip(1 - (r / 56) ** 2, 0, 1)
    dome = z < h
    if not xray:
        V.put(dome, DIRT); V.put(dome & (z >= h - 2), GRASS); V.put(dome & (z >= h - 2) & ((x * 5 + y * 3).astype(int) % 7 == 0), (130, 136, 64))
    else:
        V.S[:36, o:o + 96, o:o + 96] = E.S
        sel = V.S[..., 3] > 0
        V.S[sel, :3] = np.where((V.S[sel, :3].astype(int).sum(-1) > 450)[:, None], (200, 236, 250), (110, 170, 200))
        return V.S
    if dig:
        pit = (np.abs(x - c - 16) < 17) & (np.abs(y - c - 14) < 17)
        Ep = enclosure(0, 96).S
        full = np.zeros_like(V.S); full[:36, o:o + 96, o:o + 96] = Ep
        V.S[pit] = full[pit]
        rim = pit & ~((np.abs(x - c - 16) < 16) & (np.abs(y - c - 14) < 16)) & (z < 8)
        V.put(rim, (90, 64, 42))
    return V.bake()


PILLAR, PYR = pillar_model(), pyramid_model()
ENC = [enclosure(lv).bake() for lv in (0, 6, 12, 18, 24, 30, 34)]
HILL, HILL_DIG, HILL_X = hill_model(), hill_model(True), hill_model(False, True)
PLAIN = make_tile((176, 170, 90), (170, 128, 80), (130, 136, 64), T=64, f1=4, f2=5)
PLAIN_N = make_tile((40, 30, 60), (70, 50, 90), (22, 18, 36), T=64, f1=4, f2=5)
HZ = 96
_r = np.random.default_rng(6)
STARS = [(_r.uniform(0, CW), _r.uniform(0, HZ - 8), _r.random()) for _ in range(70)]


def land(t, cam, K, night=False):
    img = np.zeros((CH, CW, 3), np.uint8)
    if night:
        vgrad(img, [(10, 8, 18), (22, 18, 36), (40, 30, 60), (70, 50, 90)], 0, HZ)
        for x, y, d in STARS:
            if math.sin(t * (1 + 3 * d) + x) > -0.4:
                img[int(y), int(x)] = (250, 250, 250) if d > 0.6 else (110, 70, 110)
    else:
        vgrad(img, [(40, 30, 60), (110, 70, 110), (200, 110, 100), (250, 170, 110), (255, 220, 150)], 0, HZ)
        cv2.circle(img, (130, HZ - 10), 12, (255, 220, 150), -1)
    xs = np.arange(CW); hh = (6 + 3 * np.sin(xs / 23 + cam[2] * 3) + 2 * np.sin(xs / 9)).astype(int)
    for xx in xs:
        img[HZ - hh[xx]:HZ, xx] = (40, 30, 60) if night else (110, 70, 110)
    draw_plane(img, PLAIN_N if night else PLAIN, cam, K, y0=HZ)
    fog(img, HZ, 30, (40, 30, 60) if night else (200, 110, 100))
    return img


def stack1(img, cam, K, S, wx=0, wy=0, own=0, zoff=0, sh=None):
    obj = np.zeros((CH, CW), bool)
    if sh:
        shadow(img, cam, K, wx, wy, sh, sh, 0, 0.7, HZ)
    draw_stack(img, obj, S, wx, wy, own, cam, K, zoff=zoff)
    add_outline(img, obj)
    return obj


# ---------------------------------------------------------------- sahneler
def sA(t):
    K = 2.4; cam = (0, 0, 0.4 + t * 0.35, CW / 2, 250)
    img = land(t, cam, K)
    obj = np.zeros((CH, CW), bool)
    items = sorted([(to_screen(0, 0, cam, K)[1], PILLAR, 0, 0), (to_screen(26, 14, cam, K)[1], PYR, 26, 14)], key=lambda i: i[0])
    for _, S, wx, wy in items:
        shadow(img, cam, K, wx, wy, 12, 8, 0, 0.7, HZ)
        draw_stack(img, obj, S, wx, wy, 0, cam, K * (1 if S is PILLAR else 0.5))
    add_outline(img, obj)
    if t < 0.25:
        flash(img, (255, 220, 150), 0.6 * (1 - t / 0.25))
    if t > 1.2:
        press_text(img, "7000 YIL", 90, 60, 14, (255, 150, 60))
    return img


def sB(t):
    tl = t - B_; K = 1.1
    cam = (0, 0, 0.3 + tl * 0.2, CW / 2, 230)
    img = land(t, cam, K)
    if t < 4.86:
        stack1(img, cam, K, HILL, sh=50)
    else:
        u = min(1.0, (t - 4.86) / 0.6)
        stack1(img, cam, K, HILL_DIG if u < 1 and int(t * 12) % 2 else ENC[0], sh=46)
        if t < 5.2:
            flash(img, (255, 220, 150), 0.4)
    return img


def sC(t):
    tl = t - C_; K = 2.6
    cam = (0, 0, 1.0 + tl * 0.3, CW / 2, 262)
    img = land(t, cam, K)
    obj = np.zeros((CH, CW), bool)
    shadow(img, cam, K, 0, 0, 12, 8, 0, 0.7, HZ)
    draw_stack(img, obj, PILLAR, 0, 0, 0, cam, K)
    pv = Vox(6, 6, 20); person(pv, 3, 3, 0, (226, 60, 58), h=1.6)
    draw_stack(img, obj, pv.bake(), 14, 10, 0, cam, K)
    add_outline(img, obj)
    X0, Y0 = to_screen(-16, 0, cam, K)                              # ölçü çubuğu
    top = Y0 - 58 * K * ZS
    cv2.line(img, (int(X0), int(Y0)), (int(X0), int(top)), (255, 150, 60), 1)
    for yy in (int(Y0), int(top)):
        cv2.line(img, (int(X0) - 3, yy), (int(X0) + 3, yy), (255, 150, 60), 1)
    press_text(img, "5,5 m", int(X0) - 4, int((Y0 + top) / 2), 8, (255, 220, 150))
    return img


def sD(t):
    tl = t - D_; K = 3.6
    cam = (0, 0, -0.5 + tl * 0.45, CW / 2, 330)
    img = land(t, cam, K)
    stack1(img, cam, K, PILLAR, sh=10)
    glow(img, 90, 120, 60, (255, 220, 150), 0.18)
    return img


def sE(t):
    tl = t - E_; K = 1.25
    sh = shake(t, STAMP, 0.4, 6)
    cam = (0, 0, 1.2 + tl * 0.25, CW / 2 + sh, 228)
    img = land(t, cam, K)
    stack1(img, cam, K, ENC[0], sh=46)
    n = int(11600 * min(1.0, tl / 2.4))
    if t < STAMP:
        press_text(img, f"{n:,}".replace(',', '.'), 90, 70, 16, (255, 220, 150))
    else:
        k = min(1.0, (t - STAMP) / 0.15)
        press_text(img, "11.600", 90 + sh, 62, int(28 - 8 * k), (255, 150, 60))
        press_text(img, "YIL", 90 + sh, 92, 14, (255, 150, 60))
        if t < STAMP + 0.25:
            flash(img, (255, 220, 150), 0.6 * (1 - (t - STAMP) / 0.25))
    return img


def sF(t):                                                          # 2. kanca: toprak doldurur
    tl = t - F_; K = 1.25
    cam = (0, 0, 2.3 + tl * 0.2, CW / 2, 228)
    img = land(t, cam, K, night=False)
    img[:] = (img * 0.85).astype(np.uint8)
    lv = min(len(ENC) - 1, int(tl / 4.2 * (len(ENC) - 1)))
    stack1(img, cam, K, ENC[lv], sh=46)
    rng = np.random.default_rng(int(t * 20))
    for k in range(60):                                             # yağan toprak
        X = rng.uniform(30, 150); Y = (rng.uniform(0, 200) + t * 120) % 200 + 40
        img[int(Y):int(Y) + 2, int(X)] = (130, 94, 60) if k % 2 else (170, 128, 80)
    if HOOK2 <= t < HOOK2 + 0.3:
        flash(img, (90, 64, 42), 0.6 * (1 - (t - HOOK2) / 0.3))
    return img


def sG(t):
    tl = t - G_; K = 1.1
    cam = (0, 0, 3.0 + tl * 0.18, CW / 2, 232)
    img = land(t, cam, K)
    stack1(img, cam, K, HILL, sh=50)
    if t < 24.62:
        for k in range(3):
            press_text(img, "?", 50 + k * 40, 70 + int(6 * math.sin(t * 4 + k)), 18, (255, 150, 60))
    else:
        rng = np.random.default_rng(int(t * 25))                    # yağmur + kayan toprak
        for k in range(80):
            X, Y = rng.uniform(0, CW), rng.uniform(0, CH)
            cv2.line(img, (int(X), int(Y)), (int(X) - 2, int(Y) + 5), (110, 170, 200), 1)
        img[:] = (img * 0.8).astype(np.uint8)
    return img


def sH(t):
    tl = t - H_; K = 1.3
    cam = (0, 0, 0.9 + tl * 0.15, CW / 2, 238)
    img = land(t, cam, K)
    stack1(img, cam, K, HILL_DIG, sh=50)
    if t < 31.8:
        press_text(img, "1/10", 90, 64, 18, (255, 220, 150))
    elif int(t * 5) % 2 == 0 or t > 33.5:                           # röntgen: gömülü taşlar
        o = np.zeros((CH, CW), bool); tmp = img.copy()
        draw_stack(tmp, o, HILL_X, 0, 0, 0, cam, K)
        m = o & (BAY < 0.6)
        img[m] = tmp[m]
    return img


def sI(t):
    tl = t - I_; K = 1.2
    cam = (0, 0, 2.0 + tl * 0.12, CW / 2, 238)
    img = land(t, cam, K, night=True)
    stack1(img, cam, K, HILL_DIG, sh=50)
    img[:] = (img * 0.75).astype(np.uint8)
    return img


def frame_at(t):
    for t0, fn in ((I_, sI), (H_, sH), (G_, sG), (F_, sF), (E_, sE), (D_, sD), (C_, sC), (B_, sB), (A_, sA)):
        if t >= t0:
            img = fn(t); break
    img = pal8(img)
    fr = np.ascontiguousarray(cv2.resize(img, (1080, 1920), interpolation=cv2.INTER_NEAREST))
    if t > SIG_T - 0.3:
        k = min(1.0, (t - SIG_T + 0.3) / 0.6); yy = np.arange(1920)[:, None, None]
        fr[:] = (fr * (1 - 0.55 * k * np.clip((yy - 1250) / 300, 0, 1))).astype(np.uint8)
    captions(fr, t, CAPS)
    signature(fr, t, SIG_T)
    return fr
