"""EŞİK – Mary Celeste: mürettebatsız gemi (katman yığma, iri 8-bit piksel, sabit palet)."""
import math, sys
import numpy as np, cv2
sys.path.insert(0, '/home/user/Ismailguler0/.claude/skills/sekiz-bit-aksam-video/scripts')
sys.path.insert(0, '/home/user/esik-araclar/ortak')
from pix8 import signature, captions
from ymotor import *

DUR, FPS, SIG_T = 43.3, 30, 40.9
A_, B_, C_, D_, E_, F_, G_, H_, I_ = 0.0, 4.85, 10.6, 14.5, 18.5, 25.4, 28.0, 31.4, 36.0
VANISH = 2.0          # 0-2 sn kancası: 10 kişi göz önünde kaybolur
HOOK2 = 17.2          # 16-17 sn kancası: "9 GÜN"
MUSIC = dict(bpm=76, root=174.6)
CAPS = [(0.0, 1.95, "Bu gemide [10 kişi] vardı", 1608), (1.95, 4.6, "Bulunduğunda: [kimse yok]", 1608),
        (4.9, 7.4, "[1872], Atlantik Okyanusu", 1608), (7.5, 10.5, "[Mary Celeste] tek başına süzülüyor", 1608),
        (10.7, 11.95, "Yükü [yerinde]", 1608), (12.0, 14.4, "[6 aylık] yiyecek ve su", 1608),
        (14.6, 17.15, "Seyir defterindeki [son not]...", 1608), (17.2, 18.5, "[9 GÜN] önceydi!", 1608),
        (18.6, 21.35, "Anlatılır ki çaylar [sıcaktı]", 1608), (21.4, 25.4, "Bunu [Conan Doyle] uydurdu", 1608),
        (25.5, 28.0, "Geminin tek [filikası] yoktu", 1608), (28.0, 31.4, "Fıçılardan [9 tanesi] boş", 1608),
        (31.5, 36.0, "Kaptan [patlamadan] mı korktu?", 1608), (36.1, 38.65, "Filika [hiç bulunamadı]", 1608),
        (38.7, 40.9, "Sence [ne oldu?] Yorumlara yaz", 1608)]
SFX = [(0.0, 'boom'), (VANISH, 'glare'), (VANISH + 0.05, 'sparkle'), (B_, 'whoosh'), (B_ + 0.2, 'wind'), (C_, 'whoosh'),
       (D_, 'whoosh'), (14.7, 'flutter'), (15.5, 'flutter'), (16.3, 'flutter'), (HOOK2, 'boom'), (HOOK2 + 0.05, 'crash'),
       (E_, 'whoosh'), (24.5, 'glare'), (F_, 'whoosh'), (G_, 'whoosh'), (30.1, 'bell'), (H_, 'whoosh'), (33.3, 'farboom'),
       (I_, 'whoosh'), (I_ + 0.2, 'wind'), (SIG_T + 0.05, 'chime')]

set_palette([
    (8, 8, 18), (16, 18, 34), (26, 30, 52), (40, 46, 72), (60, 68, 96), (90, 100, 128), (130, 140, 164), (180, 188, 204),
    (10, 30, 48), (16, 46, 70), (28, 70, 100), (60, 110, 140), (120, 170, 196), (220, 236, 244),
    (40, 30, 30), (70, 48, 40), (112, 74, 46), (164, 116, 70), (206, 166, 110), (240, 226, 196), (230, 220, 196), (196, 184, 160),
    (255, 204, 120), (255, 236, 180), (252, 150, 70), (226, 60, 58), (150, 30, 40),
    (206, 166, 140), (60, 90, 70), (250, 250, 250), (120, 60, 70)])

WOOD, DWOOD, LWOOD, SAIL, HULL = (164, 116, 70), (112, 74, 46), (206, 166, 110), (230, 220, 196), (70, 48, 40)


# ---------------------------------------------------------------- modeller
def ship_model(crew=False):
    V = Vox(100, 32, 72); x, y, z = V.x, V.y, V.z
    cx, cy = 48, 15.5
    u = (x - cx) / 44
    half = (9.5 * np.sqrt(np.clip(1 - np.where(u > 0, u, u * 0.8) ** 2, 0, 1))) * (0.55 + 0.45 * np.clip(z / 10, 0, 1))
    hull = (np.abs(y - cy) <= half) & (z < 11) & (np.abs(u) < 1)
    V.put(hull, HULL); V.put(hull & (z >= 7) & (z < 8), (240, 226, 196)); V.put(hull & (z < 3), (40, 30, 30))
    V.put(hull & (z == 10) & (np.abs(y - cy) <= half - 1), WOOD)
    V.put(hull & (z == 10) & (np.abs(y - cy) <= half - 1) & (x.astype(int) % 4 == 0), DWOOD)
    rail = hull & (np.abs(y - cy) > half - 1)
    V.put((np.abs(y - cy) <= half) & (np.abs(y - cy) > half - 1) & (z >= 11) & (z < 13) & (np.abs(u) < 0.97), DWOOD)
    V.put((x >= 18) & (x < 32) & (np.abs(y - cy) <= 4) & (z >= 11) & (z < 15), LWOOD)                     # kamara
    V.put((x >= 18) & (x < 32) & (np.abs(y - cy) <= 4.5) & (z == 15), DWOOD)
    V.put((x >= 52) & (x < 58) & (np.abs(y - cy) <= 3) & (z == 11), (40, 30, 30))                         # ambar kapağı
    for k in range(10):                                                                                      # cıvadra
        V.put((np.abs(x - (92 + k * 0.7)) < 0.8) & (np.abs(y - cy) < 0.8) & (np.abs(z - (12 + k * 0.6)) < 0.8), DWOOD)
    for mx, top in ((34, 66), (64, 70)):                                                                    # direkler
        V.put((np.hypot(x - mx, y - cy) < 1.1) & (z >= 10) & (z < top), DWOOD)
    for (z0, z1, w) in ((22, 34, 12), (36, 48, 10.5), (50, 60, 8.5), (62, 68, 6)):                           # kare yelkenler (ön direk)
        bil = 1.8 * (1 - ((y - cy) / w) ** 2)
        V.put((np.abs(x - (65 + bil)) < 0.8) & (np.abs(y - cy) <= w) & (z >= z0) & (z < z1), SAIL)
        V.put((np.abs(x - (65 + bil)) < 0.8) & (np.abs(y - cy) <= w) & (z == z0), (196, 184, 160))
        V.put((np.abs(x - 64) < 0.8) & (np.abs(y - cy) <= w + 1) & (z == z1), DWOOD)
    gaff = (x >= 12) & (x <= 34) & (z >= 16) & (z < 16 + (34 - (34 - x) * 0.25) * 1.25)                   # randa yelkeni
    V.put(gaff & (np.abs(y - (cy + 1.2 * np.sin((x - 12) / 22 * math.pi))) < 0.8), SAIL)
    for k in range(40):                                                                                      # halatlar
        f = k / 39
        for (ax, az, bx, bz) in ((64, 70, 98, 18), (34, 66, 64, 66), (34, 66, 8, 13)):
            px, pz = ax + (bx - ax) * f, az + (bz - az) * f
            V.put((np.abs(x - px) < 0.6) & (np.abs(y - cy) < 0.6) & (np.abs(z - pz) < 0.7), (40, 30, 30))
    for sy in (cy - 9.5, cy + 9.5):                                                                          # boş filika askıları
        V.put((np.abs(x - 10) < 0.7) & (np.abs(y - sy) < 0.7) & (z >= 11) & (z < 17), (130, 140, 164))
        V.put((np.abs(x - 16) < 0.7) & (np.abs(y - sy) < 0.7) & (z >= 11) & (z < 17), (130, 140, 164))
    V.put((x >= 3) & (x < 8) & (np.abs(y - cy) <= 1) & (z >= 6) & (z < 11), DWOOD)                         # dümen
    if crew:
        rng = np.random.default_rng(7)
        pos = [(24, cy - 6), (40, cy + 5), (44, cy - 5), (50, cy + 6), (56, cy - 6), (70, cy + 4), (74, cy - 4), (80, cy + 2), (12, cy + 3), (28, cy + 6)]
        cols = [(60, 90, 70), (40, 46, 72), (120, 60, 70), (40, 46, 72), (60, 68, 96), (112, 74, 46), (40, 46, 72), (60, 90, 70), (40, 30, 30), (150, 30, 40)]
        for (px, py), c in zip(pos, cols):
            person(V, px, py, 11, c, hat=(40, 30, 30) if rng.random() < 0.5 else None)
    return V.bake()


def cargo_model():
    V = Vox(64, 64, 22); x, y, z = V.x, V.y, V.z
    for (bx, by) in ((14, 14), (24, 12), (14, 25), (25, 24), (36, 16), (19, 36)):                          # fıçılar
        r = np.hypot(x - bx, y - by)
        b = (r <= 4.6 - 0.5 * np.abs(z - 5.5) / 5.5) & (z < 11)
        V.put(b, WOOD); V.put(b & ((z == 2) | (z == 8)), (60, 68, 96)); V.put((r <= 3.6) & (z == 10), DWOOD)
    for (bx, by, h) in ((44, 38, 9), (48, 50, 7), (36, 50, 12)):                                          # sandıklar
        b = (np.abs(x - bx) <= 5) & (np.abs(y - by) <= 5) & (z < h)
        V.put(b, LWOOD); V.put(b & ((np.abs(x - bx) > 4) | (np.abs(y - by) > 4) | (z == h - 1)), DWOOD)
    for (bx, by) in ((52, 22), (54, 30)):                                                                   # çuvallar
        V.ball(bx, by, 3, 5, (206, 166, 140), 0.7)
    for k in range(5):                                                                                       # su testileri
        V.put((np.hypot(x - (8 + k * 5), y - 52) < 2) & (z < 6), (120, 170, 196))
    return V.bake()


def hold_model(highlight=False):
    V = Vox(70, 60, 12); x, y, z = V.x, V.y, V.z
    V.put((z == 0), (40, 30, 30))
    k = 0; EMPTY = {2, 5, 9, 12, 16, 19, 23, 26, 28}
    for j in range(5):
        for i in range(6):
            bx, by = 8 + i * 10.6, 8 + j * 11
            r = np.hypot(x - bx, y - by)
            b = (r <= 4.6 - 0.5 * np.abs(z - 5.5) / 5.5) & (z >= 1) & (z < 11)
            emp = k in EMPTY and highlight
            V.put(b, (164, 116, 70)); V.put(b & ((z == 3) | (z == 8)), (226, 60, 58) if emp else (60, 68, 96))
            V.put((r <= 3.6) & (z == 10), (16, 18, 34) if emp else (112, 74, 46))
            k += 1
    return V.bake()


def book_model():
    V = Vox(64, 46, 6); x, y, z = V.x, V.y, V.z
    V.put((np.abs(x - 31.5) <= 30) & (np.abs(y - 22.5) <= 21) & (z < 2), (112, 74, 46))                  # kapak
    for side in (-1, 1):
        pg = (np.abs(x - (31.5 + side * 15)) <= 14) & (np.abs(y - 22.5) <= 19.5) & (z >= 2) & (z < 3 + (14 - np.abs(x - (31.5 + side * 15))) / 7)
        V.put(pg, (240, 226, 196))
        lines = pg & (z == (3 + (14 - np.abs(x - (31.5 + side * 15))) / 7).astype(int)) & (y.astype(int) % 3 == 0) & (np.abs(x - (31.5 + side * 15)) < 11)
        V.put(lines & ((x.astype(int) * 7 + y.astype(int)) % 5 != 0), (90, 100, 128))
    V.put((np.abs(x - 31.5) < 1) & (np.abs(y - 22.5) <= 21) & (z < 3), (70, 48, 40))
    # son satır kırmızı
    V.put((x >= 37) & (x < 56) & (np.abs(y - 33) < 0.6) & (z >= 3) & (z < 6), (150, 30, 40))
    return V.bake()


def table_model(cups=True):
    V = Vox(54, 54, 18); x, y, z = V.x, V.y, V.z
    r = np.hypot(x - 26.5, y - 26.5)
    V.put((r <= 24) & (z >= 13) & (z < 15), (164, 116, 70)); V.put((r <= 24) & (r > 22.5) & (z >= 13) & (z < 15), (112, 74, 46))
    V.put((r <= 3) & (z < 13), (112, 74, 46)); V.put((r <= 9) & (z < 2), (112, 74, 46))
    if cups:
        for (cx, cy) in ((14, 22), (36, 16), (34, 38)):
            rr = np.hypot(x - cx, y - cy)
            V.put((rr <= 5) & (z == 15), (240, 226, 196))
            V.put((rr <= 3) & (rr > 2) & (z >= 15) & (z < 19), (250, 250, 250))
            V.put((rr <= 2) & (z == 17), (150, 74, 46))
        tp = np.hypot(x - 24, y - 30)
        V.ball(24, 30, 18, 5.5, (230, 220, 196), 0.9)
        V.put((np.abs(y - 30) < 0.8) & (x > 28) & (x < 33) & (np.abs(z - (17 + (x - 28) * 0.5)) < 0.8), (230, 220, 196))
        V.put((np.hypot(x - 22, y - 12) <= 5) & (z == 15), (250, 250, 250))
        V.ball(22, 12, 16, 3, (206, 166, 110), 0.6)
    return V.bake()


def lifeboat_model():
    V = Vox(32, 16, 12); x, y, z = V.x, V.y, V.z
    hull = superell(x, y, 15.5, 7.5, 14 - (3 - z) * 1.0, 5.5 - (3 - z) * 0.7, 2.2) & (z < 5)
    V.put(hull, (240, 226, 196)); V.put(hull & (z < 2), (112, 74, 46))
    V.put(hull & ~superell(x, y, 15.5, 7.5, 12.5, 4.3, 2.2) & (z == 4), (112, 74, 46))
    V.clear(superell(x, y, 15.5, 7.5, 12.5, 4.3, 2.2) & (z >= 3))
    for k, px in enumerate((7, 11, 15, 19, 23)):
        person(V, px, 7.5 + (1.2 if k % 2 else -1.2), 2, [(40, 46, 72), (60, 90, 70), (120, 60, 70), (40, 46, 72), (150, 30, 40)][k], h=0.8)
    for sy in (0.5, 14.5):
        V.put((np.abs(y - sy) < 0.7) & (x > 9) & (x < 21) & (np.abs(z - 4 - (x - 15) * 0.15) < 0.7), (196, 184, 160))
    return V.bake()


SHIP, SHIP_CREW = ship_model(), ship_model(True)
CARGO, HOLD, HOLD_HL, BOOK, TABLE, TABLE0, LBOAT = cargo_model(), hold_model(), hold_model(True), book_model(), table_model(), table_model(False), lifeboat_model()
SEA = make_tile((10, 30, 48), (16, 46, 70), (60, 110, 140))
SEA_FOG = make_tile((40, 46, 72), (60, 68, 96), (90, 100, 128))
DECK = np.zeros((32, 32, 3), np.uint8); DECK[:] = (112, 74, 46); DECK[:, ::8] = (70, 48, 40); DECK[::16, 3::8] = (164, 116, 70)
DESK = np.zeros((32, 32, 3), np.uint8); DESK[:] = (70, 48, 40); DESK[::6] = (40, 30, 30)
HZ = 96
_r = np.random.default_rng(2)
CLOUDS = [(_r.uniform(-40, 220), _r.uniform(8, 80), _r.uniform(20, 60), _r.uniform(2, 8)) for _ in range(14)]


def sky(img, t, storm=True):
    vgrad(img, [(8, 8, 18), (16, 18, 34), (26, 30, 52), (40, 46, 72), (60, 68, 96)], 0, HZ)
    for (cx, cy, w, sp) in CLOUDS:
        X = int((cx + sp * t) % 260 - 40)
        cv2.ellipse(img, (X, int(cy)), (int(w), int(w * 0.18) + 2), 0, 0, 360, (40, 46, 72), -1)
        cv2.ellipse(img, (X - 4, int(cy) - 1), (int(w * 0.7), int(w * 0.1) + 1), 0, 0, 360, (60, 68, 96), -1)
    cv2.circle(img, (138, 30), 7, (220, 236, 244), -1)
    glow(img, 138, 30, 26, (180, 188, 204), 0.25)


def sea_scene(t, cam, K, flow=(0, 4), fogc=(60, 68, 96)):
    img = np.zeros((CH, CW, 3), np.uint8)
    sky(img, t)
    draw_plane(img, SEA, cam, K, t, flow, HZ)
    fog(img, HZ, 36, fogc)
    return img


def wake(img, cam, K, t, wx, wy, ang, L=40):
    for k in range(26):
        d = 6 + k * L / 26; sp = 2 + k * 0.4
        for side in (-1, 1):
            px = wx - d * math.cos(ang) + side * sp * math.sin(ang)
            py = wy - d * math.sin(ang) - side * sp * math.cos(ang)
            X, Y = to_screen(px, py, cam, K)
            if 0 <= X < CW and HZ <= Y < CH and (k + int(t * 10)) % 3:
                img[int(Y), int(X)] = (220, 236, 244) if k < 12 else (120, 170, 196)


def ship_at(img, obj, cam, K, t, model=SHIP, wx=0, wy=0, ang=0.0):
    shadow(img, cam, K, wx, wy, 40, 11, ang, 0.7, HZ)
    roll = 0.8 * math.sin(t * 1.3)
    draw_stack(img, obj, model, wx, wy, ang + 0.02 * math.sin(t * 0.9), cam, K, zoff=roll)
    wake(img, cam, K, t, wx - 44 * math.cos(ang), wy - 44 * math.sin(ang), ang)


# ---------------------------------------------------------------- sahneler
def sA(t):
    K = 1.25; cam = (0, 0, 2.3 + t * 0.22, CW / 2, 220)
    img = sea_scene(t, cam, K)
    vis = t < VANISH or (t < VANISH + 0.4 and int(t * 20) % 2 == 0)
    obj = np.zeros((CH, CW), bool)
    ship_at(img, obj, cam, K, t, SHIP_CREW if vis else SHIP)
    add_outline(img, obj)
    if t < 0.25:
        flash(img, (250, 250, 250), 0.6 * (1 - t / 0.25))
    if VANISH <= t < VANISH + 0.3:
        flash(img, (220, 236, 244), 0.7 * (1 - (t - VANISH) / 0.3))
    if t < VANISH:
        n = min(10, int(t / 0.17) + 1)
        press_text(img, str(n), 90, 40, 22, (255, 236, 180))
    elif t < 4.85:
        press_text(img, "0", 90, 40, 22, (226, 60, 58) if int(t * 4) % 2 else (255, 236, 180))
    return img


def sB(t):
    tl = t - B_; K = 0.95
    cam = (-30 + tl * 6, 10, 1.9 - tl * 0.05, CW / 2, 225)
    img = sea_scene(t, cam, K, flow=(0, 5))
    obj = np.zeros((CH, CW), bool)
    ship_at(img, obj, cam, K, t, SHIP, wx=-30 + tl * 6, wy=0, ang=0.0)
    add_outline(img, obj)
    if t < 7.4:
        press_text(img, "1872", 90, 132, 16, (255, 236, 180))
    return img


def sC(t):
    tl = t - C_; K = 3.1
    cam = (0, 0, 0.5 + tl * 0.4, CW / 2, 215)
    img = np.zeros((CH, CW, 3), np.uint8)
    draw_plane(img, DECK, cam, K)
    img[:] = (img * 0.8).astype(np.uint8)
    obj = np.zeros((CH, CW), bool)
    shadow(img, cam, K, 0, 0, 30, 30, 0, 0.7)
    draw_stack(img, obj, CARGO, 0, 0, 0, cam, K)
    add_outline(img, obj)
    glow(img, 40, 60, 60, (255, 204, 120), 0.2)
    return img


def page_flip(img, cam, K, a):
    """Sayfa çevirme: sırt etrafında dönen sayfa (2B dörtgen)."""
    L = 28; hw = 19.5
    ex = L * math.cos(a); ez = L * math.sin(a)
    p = [to_screen(0, -hw, cam, K, 3), to_screen(0, hw, cam, K, 3), to_screen(ex, hw, cam, K, 3 + ez), to_screen(ex, -hw, cam, K, 3 + ez)]
    p = np.array([(int(px), int(py)) for px, py in p], np.int32)
    cv2.fillPoly(img, [p], (230, 220, 196) if math.cos(a) > 0 else (196, 184, 160))
    cv2.polylines(img, [p], True, OUTL, 1)


def sD(t):
    tl = t - D_
    K = 2.5 + (0.5 * min(1.0, (t - HOOK2) / 0.4) if t >= HOOK2 else 0)
    sh = shake(t, HOOK2, 0.45, 6)
    cam = (0, 0, -0.35 + tl * 0.05, CW / 2 + sh, 200)
    img = np.zeros((CH, CW, 3), np.uint8)
    draw_plane(img, DESK, cam, K)
    obj = np.zeros((CH, CW), bool)
    shadow(img, cam, K, 0, 0, 32, 24, 0, 0.6)
    draw_stack(img, obj, BOOK, 0, 0, 0, cam, K)
    add_outline(img, obj)
    for k, t0 in enumerate((14.65, 15.45, 16.25)):               # 3 sayfa çevrilir
        if t0 <= t < t0 + 0.7:
            a = math.pi * (1 - (t - t0) / 0.7)
            page_flip(img, cam, K, a)
    cx_, cy_ = 30, 70                                            # mum
    cv2.rectangle(img, (cx_ - 3, cy_), (cx_ + 3, cy_ + 22), (240, 226, 196), -1)
    cv2.ellipse(img, (cx_, cy_ - 4 + int(math.sin(t * 12))), (2, 5), 0, 0, 360, (255, 204, 120), -1)
    glow(img, cx_, cy_ - 4, 60, (255, 204, 120), 0.22)
    if t >= HOOK2:
        k = min(1.0, (t - HOOK2) / 0.2)
        if t < HOOK2 + 0.3:
            flash(img, (226, 60, 58), 0.6 * (1 - (t - HOOK2) / 0.3))
        press_text(img, "9 GÜN", 90 + sh, 96, int(14 + 10 * k), (226, 60, 58) if int(t * 5) % 2 else (255, 236, 180))
    return img


def steam(img, cam, K, t, wx, wy):
    for k in range(9):
        a = (t * 0.6 + k / 9) % 1
        X, Y = to_screen(wx, wy, cam, K, 20 + a * 18)
        X += 3 * math.sin(a * 9 + t * 2 + k)
        if 0 <= X < CW and 0 <= Y < CH and a < 0.85:
            img[int(Y), int(X)] = (220, 236, 244) if a < 0.5 else (180, 188, 204)


def sE(t):
    tl = t - E_; K = 2.6
    cam = (0, 0, 0.8 + tl * 0.3, CW / 2, 225)
    img = np.zeros((CH, CW, 3), np.uint8)
    draw_plane(img, DECK, cam, K)
    img[:] = (img * 0.6).astype(np.uint8)
    obj = np.zeros((CH, CW), bool)
    shadow(img, cam, K, 0, 0, 24, 24, 0, 0.6)
    fake = t >= 24.5
    draw_stack(img, obj, TABLE0 if (fake and int(t * 10) % 3 != 0) or t > 24.9 else TABLE, 0, 0, 0, cam, K)
    add_outline(img, obj)
    if not fake:
        for (cx, cy) in ((14, 22), (36, 16), (34, 38)):
            steam(img, cam, K, t, cx - 26.5, cy - 26.5)
        glow(img, 90, 120, 70, (255, 204, 120), 0.25)
    else:
        g = img.mean(-1, keepdims=True)
        img[:] = np.clip(g * np.array([1.25, 1.0, 0.72]) + 10, 0, 255).astype(np.uint8)
        if t < 25.0:                                              # bozulma (glitch)
            rng = np.random.default_rng(int(t * 30))
            for _ in range(10):
                y0 = int(rng.integers(0, CH - 8)); h = int(rng.integers(2, 8)); s = int(rng.integers(-12, 12))
                img[y0:y0 + h] = np.roll(img[y0:y0 + h], s, axis=1)
        press_text(img, "UYDURMA", 90, 90, 14, (226, 60, 58))
    return img


def sF(t):
    tl = t - F_; K = 2.3
    cam = (-34, 0, 1.0 + tl * 0.25, CW / 2, 225)
    img = sea_scene(t, cam, K, flow=(0, 3))
    obj = np.zeros((CH, CW), bool)
    ship_at(img, obj, cam, K, t, SHIP)
    add_outline(img, obj)
    for sy in (-9.5, 9.5):                                        # sallanan boş halatlar
        for side in (-38, -32):
            X, Y = to_screen(side, sy, cam, K, 17 + 0.8 * math.sin(t * 1.3))
            sw = 3 * math.sin(t * 2 + side)
            for k in range(14):
                yy = int(Y + k); xx = int(X + sw * k / 14)
                if 0 <= xx < CW and 0 <= yy < CH:
                    img[yy, xx] = (196, 184, 160)
    if int(t * 3) % 2 == 0:                                       # filikanın olması gereken yer
        c = [to_screen(-41, 9.5 + dy, cam, K, 13 + 0.8 * math.sin(t * 1.3)) for dy in (-3, 3)] + \
            [to_screen(-29, 9.5 + dy, cam, K, 13 + 0.8 * math.sin(t * 1.3)) for dy in (3, -3)]
        p = np.array([(int(a), int(b)) for a, b in c], np.int32)
        for i in range(4):
            a, b = p[i], p[(i + 1) % 4]
            for f in np.linspace(0, 1, 16):
                if int(f * 16) % 2 == 0:
                    xx, yy = int(a[0] + (b[0] - a[0]) * f), int(a[1] + (b[1] - a[1]) * f)
                    if 0 <= xx < CW and 0 <= yy < CH:
                        img[yy, xx] = (226, 60, 58)
    return img


def sG(t):
    tl = t - G_; K = 2.1
    cam = (0, 0, 0.6 + tl * 0.35, CW / 2, 205)
    img = np.zeros((CH, CW, 3), np.uint8)
    vgrad(img, [(8, 8, 18), (26, 30, 52), (40, 30, 30)])
    obj = np.zeros((CH, CW), bool)
    hl = t >= 30.1 and (int(t * 4) % 2 == 0 or t > 30.9)
    draw_stack(img, obj, HOLD_HL if hl else HOLD, 0, 0, 0, cam, K)
    add_outline(img, obj)
    glow(img, 90, 40, 80, (255, 204, 120), 0.25)                 # ambar kapağından ışık
    if t >= 30.1:
        press_text(img, "9 / 1701", 90, 62, 12, (226, 60, 58))
    return img


def sH(t):
    tl = t - H_; K = 1.05
    cam = (10, 30, 2.6, CW / 2, 190)
    img = sea_scene(t, cam, K, flow=(0, 3))
    obj = np.zeros((CH, CW), bool)
    items = [(to_screen(0, 0, cam, K)[1], 'S'), (to_screen(20, 30 + tl * 9, cam, K)[1], 'L')]
    for _, w in sorted(items):
        if w == 'S':
            ship_at(img, obj, cam, K, t, SHIP)
        else:
            shadow(img, cam, K, 20, 30 + tl * 9, 14, 6, 1.4, 0.7, HZ)
            draw_stack(img, obj, LBOAT, 20, 30 + tl * 9, 1.4, cam, K, zoff=0.5 * math.sin(t * 3))
    add_outline(img, obj)
    X, Y = to_screen(7, 0, cam, K, 12)                            # ambardan sızan buhar
    for k in range(16):
        a = (t * 0.5 + k / 16) % 1
        xx, yy = int(X + 6 * math.sin(a * 7 + k)), int(Y - a * 50)
        if 0 <= xx < CW and 0 <= yy < CH:
            img[yy, xx] = (252, 150, 70) if a < 0.4 else (130, 140, 164)
    glow(img, X, Y, 18, (252, 150, 70), 0.35)
    if 33.3 <= t < 33.6:
        flash(img, (252, 150, 70), 0.5 * (1 - (t - 33.3) / 0.3))
    return img


def sI(t):
    tl = t - I_; K = 2.6
    cam = (0, tl * 6, 1.2 + tl * 0.08, CW / 2, 215)
    img = sea_scene(t, cam, K, flow=(0, 2), fogc=(90, 100, 128))
    obj = np.zeros((CH, CW), bool)
    shadow(img, cam, K, 0, tl * 6, 14, 6, 1.57, 0.7, HZ)
    wake(img, cam, K, t, 0, tl * 6 - 14, 1.57, 20)
    draw_stack(img, obj, LBOAT, 0, tl * 6, 1.57, cam, K, zoff=0.6 * math.sin(t * 3))
    add_outline(img, obj)
    f = min(0.85, tl / 5.5)                                       # sis yutar
    m = BAY < f
    img[m] = (img[m] * 0.3 + np.array((130, 140, 164)) * 0.7).astype(np.uint8)
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
