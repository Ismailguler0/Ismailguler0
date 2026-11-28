"""EŞİK – Nusret mayın gemisi (katman yığma, iri 8-bit piksel, sabit palet)."""
import math, sys
import numpy as np, cv2
sys.path.insert(0, '/home/user/Ismailguler0/.claude/skills/sekiz-bit-aksam-video/scripts')
sys.path.insert(0, '/home/user/esik-araclar/ortak')
from pix8 import signature, captions
from ymotor import *

DUR, FPS, SIG_T = 42.85, 30, 40.45
A_, B_, C_, D_, E_, F_, G_ = 0.0, 4.86, 8.06, 11.64, 16.86, 27.58, 36.78
HOOK2 = 16.86
BOOMS = (33.0, 34.5, 35.9)              # Bouvet, Irresistible, Ocean
MUSIC = dict(bpm=78, root=164.8)
CAPS = [(0.0, 2.4, "Bu küçük gemi...", 1608), (2.4, 4.8, "[3 dev zırhlıyı] batırdı!", 1608),
        (4.9, 7.9, "[8 Mart 1915], Çanakkale", 1608), (8.06, 11.5, "Düşman [mayınları] temizliyor", 1608),
        (11.64, 15.4, "Işıklar [söner], gemi yola çıkar", 1608), (15.5, 16.8, "Adı: [NUSRET]", 1608),
        (16.86, 20.4, "Asıl dâhice olan: [NEREYE?]", 1608), (20.48, 26.5, "[26 mayın], kıyıya paralel", 1608),
        (26.6, 27.55, "Kimse [fark etmedi]", 1608), (27.6, 31.2, "[18 Mart]: donanma girer", 1608),
        (31.3, 36.7, "[Bouvet], [Irresistible], [Ocean]...", 1608), (36.78, 40.45, "Sen olsan [biner miydin?]", 1608)]
SFX = ([(0.0, 'boom'), (0.05, 'glare'), (2.6, 'farboom'), (3.0, 'farboom'), (3.4, 'farboom'), (B_, 'whoosh'), (C_, 'whoosh'),
        (D_, 'whoosh'), (12.4, 'blip'), (HOOK2, 'boom'), (HOOK2 + 0.05, 'crash'), (F_, 'whoosh'), (G_, 'whoosh'),
        (SIG_T + 0.05, 'chime')] + [(b, 'boom') for b in BOOMS] + [(b + 0.1, 'crash') for b in BOOMS]
       + [(20.6 + k * 0.22, 'tick') for k in range(26)])

set_palette([
    (6, 8, 16), (12, 18, 32), (20, 30, 50), (32, 46, 72), (52, 70, 100), (90, 110, 140), (150, 170, 196), (220, 232, 240),
    (10, 26, 44), (16, 42, 66), (28, 66, 96), (56, 104, 136), (110, 164, 190), (236, 246, 250),
    (60, 56, 56), (96, 92, 92), (140, 136, 134), (190, 186, 180), (30, 28, 30),
    (150, 30, 30), (226, 60, 58), (252, 140, 60), (255, 210, 120), (255, 246, 210),
    (70, 90, 50), (110, 130, 70), (160, 150, 100), (200, 180, 130), (112, 74, 46), (164, 116, 70)])

HULL, DECK, RED = (30, 28, 30), (164, 116, 70), (150, 30, 30)


def nusret_model():
    V = Vox(64, 18, 34); x, y, z = V.x, V.y, V.z
    u = (x - 31) / 29
    half = 6.5 * np.sqrt(np.clip(1 - np.where(u > 0, u ** 2, (u * 0.85) ** 2), 0, 1)) * (0.6 + 0.4 * np.clip(z / 6, 0, 1))
    hull = (np.abs(y - 8.5) <= half) & (z < 7) & (np.abs(u) < 1)
    V.put(hull, HULL); V.put(hull & (z < 2), RED); V.put(hull & (z == 6), DECK)
    V.put((x >= 26) & (x < 38) & (np.abs(y - 8.5) <= 3.5) & (z >= 7) & (z < 12), (190, 186, 180))   # köprüüstü
    V.put((x >= 25) & (x < 39) & (np.abs(y - 8.5) <= 4) & (z == 12), (96, 92, 92))
    V.put((x >= 28) & (x < 36) & (np.abs(y - 8.5) <= 3.6) & (z == 10) & (x.astype(int) % 2 == 0), (20, 30, 50))
    V.put((np.hypot(x - 22, y - 8.5) < 2.2) & (z >= 7) & (z < 20), (60, 56, 56))                      # baca
    V.put((np.hypot(x - 22, y - 8.5) < 2.3) & (z >= 17) & (z < 19), (150, 30, 30))
    V.put((np.hypot(x - 44, y - 8.5) < 0.8) & (z >= 7) & (z < 32), (112, 74, 46))                     # direk
    V.put((np.abs(x - 44) < 0.7) & (np.abs(y - 8.5) < 5) & (z == 26), (112, 74, 46))
    V.put((x > 44) & (x < 48) & (np.abs(y - 8.5) < 0.6) & (z >= 29) & (z < 32), (226, 60, 58))        # bayrak
    for k in range(6):                                                                                 # kıçta mayınlar
        for s in (-3, 3):
            V.ball(6 + k * 3.2, 8.5 + s, 8.4, 1.4, (30, 28, 30))
    return V.bake()


def battleship_model():
    V = Vox(112, 26, 40); x, y, z = V.x, V.y, V.z
    u = (x - 55) / 53
    half = 11 * np.sqrt(np.clip(1 - np.where(u > 0, u ** 2, (u * 0.7) ** 2), 0, 1)) * (0.65 + 0.35 * np.clip(z / 8, 0, 1))
    hull = (np.abs(y - 12.5) <= half) & (z < 10) & (np.abs(u) < 1)
    V.put(hull, (96, 92, 92)); V.put(hull & (z < 3), RED); V.put(hull & (z == 9), (140, 136, 134))
    V.put((x >= 40) & (x < 72) & (np.abs(y - 12.5) <= 6) & (z >= 10) & (z < 16), (140, 136, 134))
    V.put((x >= 46) & (x < 66) & (np.abs(y - 12.5) <= 4) & (z >= 16) & (z < 20), (190, 186, 180))
    for fx in (50, 60):
        V.put((np.hypot(x - fx, y - 12.5) < 2.6) & (z >= 16) & (z < 30), (60, 56, 56))
    for tx in (22, 90):                                                                                # taretler
        V.put((np.hypot(x - tx, y - 12.5) < 5) & (z >= 10) & (z < 14), (140, 136, 134))
        V.put((np.abs(y - 12.5) < 1) & (np.abs(z - 12) < 0.8) & (np.abs(x - tx - (8 if tx > 55 else -8)) < 6), (60, 56, 56))
    for mx in (38, 74):
        V.put((np.hypot(x - mx, y - 12.5) < 0.9) & (z >= 10) & (z < 38), (60, 56, 56))
    return V.bake()


def sweeper_model():
    V = Vox(30, 12, 20); x, y, z = V.x, V.y, V.z
    hull = superell(x, y, 15, 6, 13 - (3 - z) * 0.8, 4.5 - (3 - z) * 0.5, 2.2) & (z < 5)
    V.put(hull, (60, 56, 56)); V.put(hull & (z < 1), RED)
    V.put((x >= 13) & (x < 19) & (np.abs(y - 6) <= 2) & (z >= 5) & (z < 9), (190, 186, 180))
    V.put((np.hypot(x - 11, y - 6) < 1.2) & (z >= 5) & (z < 13), (30, 28, 30))
    V.put((np.hypot(x - 21, y - 6) < 0.6) & (z >= 5) & (z < 18), (112, 74, 46))
    return V.bake()


NUS, BB, SWP = nusret_model(), battleship_model(), sweeper_model()
SEA_N = make_tile((10, 26, 44), (16, 42, 66), (28, 66, 96))
SEA_D = make_tile((28, 66, 96), (56, 104, 136), (110, 164, 190))
LAND = make_tile((110, 130, 70), (160, 150, 100), (70, 90, 50), T=64, f1=5, f2=3)
HZ = 90
_r = np.random.default_rng(3)
STARS = [(_r.uniform(0, CW), _r.uniform(0, HZ - 8), _r.random()) for _ in range(50)]


def world_xy(cam, K):
    ccx, ccy, th, sx0, sy0 = cam
    sx = (XX - sx0) / K; sy = (YY - sy0) / (K * SQ)
    c, s = math.cos(th), math.sin(th)
    return ccx + sx * c - sy * s, ccy + sx * s + sy * c


def shore_x(wy):                         # Anadolu kıyısı (dünya x'i): koy içe kıvrılır
    return 70 + 24 * np.exp(-((wy - 0) / 70) ** 2)


def sky(img, t, night=True):
    if night:
        vgrad(img, [(6, 8, 16), (12, 18, 32), (20, 30, 50), (32, 46, 72)], 0, HZ)
        for x, y, d in STARS:
            if math.sin(t * (1 + 3 * d) + x) > -0.4:
                img[int(y), int(x)] = (220, 232, 240) if d > 0.6 else (90, 110, 140)
        cv2.circle(img, (140, 26), 6, (220, 232, 240), -1); cv2.circle(img, (143, 24), 5, (12, 18, 32), -1)
    else:
        vgrad(img, [(56, 104, 136), (110, 164, 190), (150, 170, 196), (220, 232, 240)], 0, HZ)
        cv2.circle(img, (40, 30), 9, (255, 246, 210), -1)
    # karşı kıyı tepeleri
    xs = np.arange(CW)
    h = (8 + 5 * np.sin(xs / 17 + 1) + 3 * np.sin(xs / 7)).astype(int)
    for x in xs:
        img[HZ - h[x]:HZ, x] = (32, 46, 72) if night else (90, 110, 140)


def sea_scene(t, cam, K, night=True, land=True, flow=(0, 0)):
    img = np.zeros((CH, CW, 3), np.uint8)
    sky(img, t, night)
    draw_plane(img, SEA_N if night else SEA_D, cam, K, t, flow, HZ)
    if land:
        wx, wy = world_xy(cam, K)
        m = (wx > shore_x(wy)) & (YY >= HZ)
        lt = np.zeros_like(img); draw_plane(lt, LAND, cam, K)
        img[m] = (lt[m] * (0.45 if night else 1.0)).astype(np.uint8)
        edge = m & ~np.roll(m, 1, axis=1)
        img[edge & (YY >= HZ)] = (236, 246, 250) if not night else (110, 164, 190)
    fog(img, HZ, 30, (32, 46, 72) if night else (150, 170, 196))
    return img


def wake(img, cam, K, t, wx, wy, ang, L=30):
    for k in range(20):
        d = 4 + k * L / 20; sp = 1.5 + k * 0.35
        for side in (-1, 1):
            X, Y = to_screen(wx - d * math.cos(ang) + side * sp * math.sin(ang), wy - d * math.sin(ang) - side * sp * math.cos(ang), cam, K)
            if 0 <= X < CW and HZ <= Y < CH and (k + int(t * 10)) % 3:
                img[int(Y), int(X)] = (236, 246, 250) if k < 9 else (110, 164, 190)


def mine_icon(img, X, Y, r, col=(30, 28, 30), lit=None):
    X, Y = int(X), int(Y)
    cv2.circle(img, (X, Y), r, col, -1)
    for a in range(0, 360, 60):
        px, py = int(X + (r + 1.5) * math.cos(math.radians(a))), int(Y + (r + 1.5) * math.sin(math.radians(a)))
        if 0 <= px < CW and 0 <= py < CH:
            img[py, px] = col
    if lit is not None and 0 <= X < CW and 0 <= Y < CH:
        img[max(0, Y - 1), X] = lit


def boom_fx(img, X, Y, k, R=40):
    if k < 0 or k > 1.2:
        return
    r = int(4 + R * min(1, k))
    col = (255, 246, 210) if k < 0.15 else (252, 140, 60) if k < 0.5 else (150, 30, 30)
    cv2.circle(img, (int(X), int(Y)), r, col, -1)
    if k > 0.3:
        cv2.circle(img, (int(X), int(Y) - int(r * 0.6)), int(r * 0.7), (96, 92, 92), -1)
    glow(img, X, Y, R * 2, (252, 140, 60), 0.4)


def ship(img, obj, S, wx, wy, ang, cam, K, t, sink=0.0, roll=0.6):
    shadow(img, cam, K, wx, wy, S.shape[2] * 0.42, S.shape[1] * 0.5, ang, 0.7, HZ)
    zo = roll * math.sin(t * 1.4 + wx) - sink
    draw_stack(img, obj, S, wx, wy, ang, cam, K, zoff=zo, zmin_screen=0 if sink > 0 else None)


# ---------------------------------------------------------------- sahneler
def mines_behind(img, cam, K, t, wx, wy, ang, t0, n=6):
    for k in range(n):
        a = ((t - t0) * 0.9 + k / n) % 1
        mx, my = wx - (14 + a * 40) * math.cos(ang), wy - (14 + a * 40) * math.sin(ang)
        X, Y = to_screen(mx, my, cam, K)
        if a < 0.08:
            Y -= (0.08 - a) * 120
        if 0 <= X < CW and HZ <= Y < CH:
            mine_icon(img, X, Y, 2)
            if a < 0.15:
                cv2.circle(img, (int(X), int(Y)), int(3 + a * 30), (236, 246, 250), 1)


def sA(t):
    K = 2.0; cam = (0, 0, 2.0 + t * 0.3, CW / 2, 220)
    img = sea_scene(t, cam, K, land=False)
    for k, tb in enumerate((2.6, 3.0, 3.4)):                    # ufukta 3 patlama
        boom_fx(img, 40 + k * 50, HZ - 4, (t - tb) / 0.8, 14)
    obj = np.zeros((CH, CW), bool)
    ship(img, obj, NUS, 0, 0, 0, cam, K, t)
    add_outline(img, obj)
    mines_behind(img, cam, K, t, 0, 0, 0, 0)
    if t < 0.25:
        flash(img, (255, 246, 210), 0.6 * (1 - t / 0.25))
    if t > 2.6:
        press_text(img, "3", 90, 40, 26, (226, 60, 58))
    return img


def sB(t):
    tl = t - B_; K = 0.55
    cam = (20, -40 + tl * 10, 1.57, CW / 2, 200)                 # boğaz, kuşbakışı
    img = sea_scene(t, cam, K, night=False)
    wx, wy = world_xy(cam, K)
    m = (wx < -70 - 15 * np.sin(wy / 60)) & (YY >= HZ)            # Avrupa kıyısı
    lt = np.zeros_like(img); draw_plane(lt, LAND, cam, K)
    img[m] = lt[m]
    press_text(img, "1915", 90, 130, 18, (255, 246, 210))
    return img


def sC(t):
    tl = t - C_; K = 1.0
    cam = (0, 20, 1.2 + tl * 0.05, CW / 2, 200)
    img = sea_scene(t, cam, K, night=False)
    obj = np.zeros((CH, CW), bool)
    items = [(to_screen(-30, -40, cam, K)[1], BB, -30, -40, 0.3), (to_screen(-10 + tl * 6, 30, cam, K)[1], SWP, -10 + tl * 6, 30, 0.0),
             (to_screen(20 + tl * 6, 55, cam, K)[1], SWP, 20 + tl * 6, 55, 0.0)]
    for _, S, wx, wy, a in sorted(items, key=lambda i: i[0]):
        ship(img, obj, S, wx, wy, a, cam, K, t)
    add_outline(img, obj)
    for k, (sx, sy) in enumerate(((-10 + tl * 6, 30), (20 + tl * 6, 55))):   # tarama telleri + patlayan mayın
        X, Y = to_screen(sx - 14, sy, cam, K); X2, Y2 = to_screen(sx - 34, sy + 12, cam, K)
        cv2.line(img, (int(X), int(Y)), (int(X2), int(Y2)), (190, 186, 180), 1)
    if 9.6 < t < 10.4:
        X, Y = to_screen(-30, 70, cam, K); boom_fx(img, X, Y, (t - 9.6) / 0.6, 12)
    return img


def sD(t):
    tl = t - D_; K = 2.2
    cam = (0, 0, 0.6 + tl * 0.35, CW / 2, 225)
    img = sea_scene(t, cam, K, land=False, flow=(-4, 0))
    obj = np.zeros((CH, CW), bool)
    ship(img, obj, NUS, 0, 0, 0, cam, K, t)
    add_outline(img, obj)
    wake(img, cam, K, t, -30, 0, 0)
    if t < 12.4 or (t < 12.7 and int(t * 20) % 2):              # fenerler söner
        for wx_, wy_, wz in ((12, 0, 32), (-28, 0, 12), (5, 0, 12)):
            X, Y = to_screen(wx_ - 0, wy_, cam, K, wz)
            glow(img, X, Y, 12, (255, 210, 120), 0.4)
    else:
        img[:] = (img * 0.85).astype(np.uint8)
    return img


MINES = [(i, 0) for i in range(26)]


def sE(t):                                                       # 16. sn kancası: koy haritası, kıyıya paralel mayınlar
    tl = t - E_; K = 1.1
    sh = shake(t, HOOK2, 0.4, 6)
    cam = (40, 0, math.pi / 2, CW / 2 + sh, 215)
    img = sea_scene(t, cam, K, night=True)
    lay = np.clip((t - 20.5) / 5.8, 0, 1)
    ny = -64 + 128 * lay
    hidden = t >= 26.68
    for i in range(26):                                          # mayın hattı (kıyıya paralel)
        my = -64 + i * 128 / 25
        if my > ny:
            continue
        mx = shore_x(np.array(my)) - 24
        X, Y = to_screen(float(mx), my, cam, K)
        if hidden:
            if int(t * 3) % 2 == 0 and t < 27.4:
                cv2.circle(img, (int(X), int(Y)), 2, (52, 70, 100), -1)
        else:
            mine_icon(img, X, Y + 2, 2, (6, 8, 16), None)
            if int(t * 4 + i) % 2:
                img[int(Y) + 2, int(X)] = (226, 60, 58)
    obj = np.zeros((CH, CW), bool)
    sx = float(shore_x(np.array(ny))) - 24
    ship(img, obj, NUS, sx, ny, math.pi / 2, cam, K, t, roll=0.3)
    add_outline(img, obj)
    if t < 20.5:                                                 # dönüş noktası: düşman rotası (kesik çizgi, U dönüşü)
        pts = [(-60 + 120 * k / 30, 0) for k in range(30)]
        for k in range(0, 40, 2):
            a = k / 40 * math.pi
            X, Y = to_screen(40 + 25 * math.sin(a) - 10, -25 * math.cos(a), cam, K)
            if 0 <= X < CW and 0 <= Y < CH:
                img[int(Y), int(X)] = (226, 60, 58)
        press_text(img, "?", 90 + sh, 120, 24 + int(3 * math.sin(t * 7)), (226, 60, 58))
    else:
        n = min(26, int(lay * 26) + 1)
        press_text(img, str(n), 90, 120, 22, (255, 210, 120))
    if HOOK2 <= t < HOOK2 + 0.3:
        flash(img, (226, 60, 58), 0.6 * (1 - (t - HOOK2) / 0.3))
    return img


def sF(t):                                                       # 18 Mart: zırhlılar girer, döner, batar
    tl = t - F_; K = 0.95
    cam = (30, 0, 0.35, CW / 2, 215)
    img = sea_scene(t, cam, K, night=False)
    obj = np.zeros((CH, CW), bool)
    items = []
    for k in range(3):
        d = tl * 22 - k * 62                                     # rota: arka arkaya gir, koyda sağa dön
        if d < 100:
            wx, wy, a = -100 + d, -50 + k * 22, 0.0
        else:
            a = min(math.pi * 0.6, (d - 100) / 40)
            wx, wy = 40 * math.sin(a), -50 + k * 22 + 40 * (1 - math.cos(a))
        sink = max(0.0, (t - BOOMS[k]) * 9) if t > BOOMS[k] else 0.0
        items.append((to_screen(wx, wy, cam, K)[1], wx, wy, a, sink, k))
    items.sort()
    for _, wx, wy, a, sink, k in items:
        if sink < 40:
            ship(img, obj, BB, wx, wy, a, cam, K, t, sink=sink)
    add_outline(img, obj)
    for _, wx, wy, a, sink, k in items:
        X, Y = to_screen(wx, wy, cam, K)
        boom_fx(img, X, Y - 10, (t - BOOMS[k]) / 0.9, 15)
        if sink > 0:
            for j in range(8):
                bx = int(X + (j - 4) * 5); by = int(Y - ((t * 30 + j * 7) % 14))
                if 0 <= bx < CW and HZ <= by < CH:
                    img[by, bx] = (236, 246, 250)
    for k, nm in enumerate(("BOUVET", "IRRESISTIBLE", "OCEAN")):
        if t >= BOOMS[k]:
            press_text(img, nm, 90, 60 + k * 18, 9, (226, 60, 58))
    return img


def sG(t):
    tl = t - G_; K = 2.2
    cam = (0, 0, 3.6 + tl * 0.2, CW / 2, 225)
    img = sea_scene(t, cam, K, land=False)
    obj = np.zeros((CH, CW), bool)
    ship(img, obj, NUS, 0, 0, 0, cam, K, t)
    add_outline(img, obj)
    X, Y = to_screen(12, 0, cam, K, 32); glow(img, X, Y, 14, (255, 210, 120), 0.3)
    return img


def frame_at(t):
    for t0, fn in ((G_, sG), (F_, sF), (E_, sE), (D_, sD), (C_, sC), (B_, sB), (A_, sA)):
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
