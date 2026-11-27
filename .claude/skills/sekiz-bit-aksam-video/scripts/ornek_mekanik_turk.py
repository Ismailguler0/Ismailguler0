"""EŞİK – Mekanik Türk: Napolyon'u yenen makine (katman yığma, iri 8-bit piksel, sabit palet)."""
import math, sys
import numpy as np, cv2
sys.path.insert(0, '/home/user/Ismailguler0/.claude/skills/sekiz-bit-aksam-video/scripts')
sys.path.insert(0, '/home/user/esik-araclar/ortak')
from pix8 import signature, captions
from ymotor import *

DUR, FPS, SIG_T = 46.5, 30, 44.1
A_, B_, C_, D_, E_, F_, G_, H_, I_ = 0.0, 4.3, 6.2, 10.0, 15.2, 20.4, 26.25, 36.6, 41.9
SLAM = 16.1           # 16. sn kancası: kapaklar çarpar, içeride bir gölge belirir
SWEEP = 23.3
MUSIC = dict(bpm=80, root=185.0)
CAPS = [(0.0, 2.75, "[Napolyon'u] yenen makine", 1608), (2.8, 4.3, "Adı: [TÜRK]", 1608),
        (4.4, 6.2, "[1770], Viyana", 1608), (6.25, 10.0, "Kaftanlı, sarıklı bir [figür]", 1608),
        (10.05, 13.95, "Kapaklar açılır...", 1608), (14.0, 15.2, "Sadece [dişliler]", 1608),
        (15.25, 17.45, "Ama dolabın bir [sırrı] vardı", 1608), (17.5, 20.35, "Yıllarca [kimseye] söylenmedi", 1608),
        (20.45, 23.25, "Anlatılır ki Napolyon [hile] yaptı", 1608), (23.3, 26.2, "Türk taşları [süpürdü]!", 1608),
        (26.3, 28.05, "Peki nasıl [düşünüyordu]?", 1608), (28.1, 32.15, "İçeride gizli bir [insan]!", 1608),
        (32.2, 36.5, "[Mum ışığı] ve [mıknatıslar]", 1608), (36.6, 38.65, "Türk bir [yangında] yok oldu", 1608),
        (38.7, 41.85, "Saklananların bazıları [bilinmiyor]", 1608), (41.9, 44.1, "Sen [anlar mıydın?] Yorumlara yaz", 1608)]
SFX = ([(0.0, 'boom'), (0.05, 'glare'), (2.8, 'bell'), (B_, 'whoosh'), (C_, 'whoosh'), (D_, 'whoosh'), (14.0, 'sparkle'),
        (SLAM, 'boom'), (SLAM + 0.05, 'crash'), (F_, 'whoosh'), (SWEEP, 'crash'), (G_, 'whoosh'), (28.8, 'chime'),
        (H_, 'whoosh'), (H_ + 0.1, 'rumble'), (I_, 'whoosh'), (SIG_T + 0.05, 'chime')]
       + [(10.2 + k * 0.3, 'tick') for k in range(12)] + [(21.0 + k * 0.6, 'tick') for k in range(4)])

set_palette([
    (8, 6, 14), (18, 14, 28), (32, 24, 44), (52, 40, 64), (80, 62, 90),
    (40, 30, 30), (70, 48, 40), (112, 74, 46), (164, 116, 70), (206, 166, 110),
    (120, 80, 30), (190, 140, 50), (255, 204, 120), (255, 236, 180),
    (240, 226, 196), (196, 184, 160), (140, 130, 120), (250, 250, 250),
    (150, 30, 40), (226, 60, 58), (252, 120, 60),
    (40, 46, 90), (70, 90, 150), (130, 150, 200),
    (206, 166, 140), (150, 110, 90), (40, 80, 60), (90, 140, 90),
    (120, 110, 100), (84, 76, 70), (54, 48, 46), (150, 140, 128)])

WD, DWD, GOLD, DGOLD = (112, 74, 46), (70, 48, 40), (255, 204, 120), (190, 140, 50)
CX0, CX1, CY0, CY1, CZ = 8, 56, 22, 42, 20                     # dolap sınırları (model içinde); ön yüz y=CY1


def gear(V, cx, cz, r, ph, y0, y1):
    x, y, z = V.x, V.y, V.z
    rr = np.hypot(x - cx, z - cz); a = np.arctan2(z - cz, x - cx)
    teeth = rr <= r + (np.cos(a * 8 + ph) > 0.2) * 1.2
    ring = teeth & (rr >= r - 1.3)
    spokes = (rr < r) & (np.abs(np.sin(a * 2 + ph / 4)) < 0.22)
    V.put((ring | spokes | (rr < 1.4)) & (y >= y0) & (y < y1), GOLD)
    V.put(ring & (y >= y0) & (y < y1) & (rr > r + 0.4), DGOLD)


def turk_model(mode='closed', ph=0.0, arm=0.0):
    """mode: closed | open (dişliler) | cut (içindeki insan)"""
    V = Vox(64, 64, 52); x, y, z = V.x, V.y, V.z
    cab = (x >= CX0) & (x < CX1) & (y >= CY0) & (y < CY1) & (z >= 2) & (z < CZ)
    V.put(cab, WD)
    edge = cab & ((x < CX0 + 1) | (x >= CX1 - 1) | (y < CY0 + 1) | (y >= CY1 - 1)) & ((z < 3) | (z >= CZ - 1))
    V.put(edge, GOLD)
    V.put(cab & ((x < CX0 + 1) | (x >= CX1 - 1)) & ((y < CY0 + 1) | (y >= CY1 - 1)), GOLD)
    front = cab & (y >= CY1 - 1)
    V.put(front & ((x.astype(int) - CX0) % 16 == 0), GOLD)                       # kapak çizgileri
    V.put(front & (z.astype(int) == 11) & ((x.astype(int) - CX0) % 16 == 8), GOLD)  # kulplar
    V.put(front & (z.astype(int) == 6) & (x > CX0 + 1) & (x < CX1 - 1), DGOLD)   # çekmece
    for fx in (CX0 + 1, CX1 - 2):
        for fy in (CY0 + 1, CY1 - 2):
            V.put((np.abs(x - fx) < 1.2) & (np.abs(y - fy) < 1.2) & (z < 2), DGOLD)
    # satranç tahtası
    bx0, by0 = 30, 24
    brd = (x >= bx0) & (x < bx0 + 20) & (y >= by0) & (y < by0 + 16) & (z == CZ)
    chk = (((x - bx0) // 2.5).astype(int) + ((y - by0) // 2).astype(int)) % 2 == 0
    V.put(brd & chk, (240, 226, 196)); V.put(brd & ~chk, DWD)
    rng = np.random.default_rng(1)
    for k in range(12):
        px, py = bx0 + 1.2 + 2.5 * int(rng.integers(0, 8)), by0 + 1 + 2 * int(rng.integers(0, 8))
        h = 2 + int(rng.integers(0, 2))
        V.put((np.hypot(x - px, y - py) < 1.0) & (z > CZ) & (z <= CZ + h), (250, 250, 250) if k % 2 else (40, 30, 30))
    # Türk figürü (dolabın arkasında oturur, oyuncuya +y yönünde bakar)
    fx, fy = 22, 20
    V.put(superell(x, y, fx, fy, 6.5, 4.5, 2.4) & (z >= CZ) & (z < CZ + 14), (226, 60, 58))
    V.put(superell(x, y, fx, fy, 6.5, 4.5, 2.4) & (z >= CZ) & (z < CZ + 14) & (np.abs(x - fx) < 1), GOLD)
    V.put(superell(x, y, fx, fy, 7.5, 5.2, 2.4) & (z >= CZ) & (z < CZ + 3), (150, 30, 40))
    V.ball(fx, fy + 0.5, CZ + 16.5, 3.4, (206, 166, 140))
    V.put(((x - fx) ** 2 + (y - fy - 2.5) ** 2 + ((z - CZ - 14.5) * 1.3) ** 2 <= 9) & (y > fy + 1), (40, 30, 30))   # sakal
    V.put(((x - fx) / 5.2) ** 2 + ((y - fy) / 5.2) ** 2 + ((z - CZ - 21) / 3.6) ** 2 <= 1, (240, 226, 196))      # sarık
    V.ball(fx, fy, CZ + 24.5, 1.4, (226, 60, 58))
    V.put((np.abs(x - fx + 1.2) < 0.7) & (np.abs(y - fy - 3.3) < 0.6) & (np.abs(z - CZ - 17) < 0.6), (8, 6, 14))
    V.put((np.abs(x - fx - 1.2) < 0.7) & (np.abs(y - fy - 3.3) < 0.6) & (np.abs(z - CZ - 17) < 0.6), (8, 6, 14))
    # sağ kol tahtaya uzanır (arm: 0 dinlenme, 1 süpürme)
    sw = arm * 10
    tube(V, [(fx + 5 + k * 0.5 + sw * k / 12, fy + 2 + k * 0.6, CZ + 11 - k * 0.7) for k in range(13)], 1.6, (226, 60, 58))
    V.ball(fx + 11 + sw, fy + 9.5, CZ + 2.5, 1.6, (206, 166, 140))
    # sol kol uzun çubuk (nargile/pipo) tutar
    tube(V, [(fx - 5 - k * 0.3, fy + 1 + k * 0.3, CZ + 11 - k * 0.4) for k in range(8)], 1.5, (226, 60, 58))
    for k in range(26):
        V.put((np.abs(x - (fx - 8 + k * 0.05)) < 0.6) & (np.abs(y - (fy + 4)) < 0.6) & (np.abs(z - (CZ + 1 + k * 0.85)) < 0.6), (164, 116, 70))
    if mode in ('open', 'cut'):
        V.clear((x > CX0 + 1) & (x < CX1 - 1) & (y >= CY0 + 1) & (z >= 3) & (z < CZ - 1))
        V.put((x > CX0) & (x < CX1) & (y >= CY0 + 1) & (y < CY0 + 3) & (z >= 3) & (z < CZ - 1), (18, 14, 28))  # iç arka
        V.put((x > CX0) & (x < CX1) & (y >= CY0 + 1) & (y < CY1 - 2) & (z == 3), (32, 24, 44))
        for dx in (CX0 + 1, CX1 - 2):                                             # açık kapaklar
            V.put((np.abs(x - dx) < 0.8) & (y >= CY1) & (y < CY1 + 14) & (z >= 3) & (z < CZ - 1), WD)
            V.put((np.abs(x - dx) < 0.8) & (y >= CY1) & (y < CY1 + 14) & ((z.astype(int) == 3) | (z.astype(int) == CZ - 2)), GOLD)
    if mode == 'open':
        for (gx, gz, r, s) in ((18, 11, 6, 1), (30, 9, 4.5, -1), (40, 12, 6.5, 1), (50, 8, 4, -1), (27, 15, 3, 1)):
            gear(V, gx, gz, r, ph * s * (8 / r), CY0 + 6, CY0 + 8)
            V.put((np.hypot(x - gx, z - gz) < 0.8) & (y >= CY0 + 2) & (y < CY0 + 7), (140, 130, 120))
    if mode == 'cut':
        V.clear((x > CX0) & (x < 29) & (y > CY0) & (y < CY1 - 1) & (z >= CZ - 1) & (z <= CZ))
        px, py = 24, 31                                                           # içerideki satranççı
        V.put(superell(x, y, px, py, 3.5, 3, 2.2) & (z >= 4) & (z < 12), (240, 226, 196))
        V.ball(px + 1, py + 0.5, 14, 2.6, (206, 166, 140))
        V.put(((x - px - 1) / 3) ** 2 + ((y - py - 0.5) / 3) ** 2 + ((z - 15.5) / 1.6) ** 2 <= 1, (40, 30, 30))
        tube(V, [(px + 2 + k * 0.6, py + 1, 10 + k * 0.6) for k in range(9)], 1.1, (240, 226, 196))   # yukarı uzanan el
        V.ball(px + 7.6, py + 1, 16, 1.2, (206, 166, 140))
        V.put((np.abs(x - 40) < 1) & (np.abs(y - 30) < 1) & (z >= 4) & (z < 8), (240, 226, 196))  # mum
        V.put((np.abs(x - 40) < 0.7) & (np.abs(y - 30) < 0.7) & (z >= 8) & (z < 10), (255, 236, 180))
        for k in range(8):                                                        # tavandaki mıknatıslar
            V.put((np.abs(x - (31 + k * 2.5)) < 0.7) & (np.abs(y - 30) < 6) & (z == CZ - 2) & (y.astype(int) % 2 == 0), (140, 130, 120))
            V.put((np.abs(x - (31 + k * 2.5)) < 0.7) & (np.abs(y - 30) < 6) & (z == CZ - 3) & (y.astype(int) % 4 == 0), (150, 30, 40))
    return V.bake()


def napoleon_model():
    V = Vox(26, 26, 40); x, y, z = V.x, V.y, V.z
    V.put((np.abs(x - 13) <= 6) & (np.abs(y - 13) <= 5) & (z >= 9) & (z < 11), (150, 30, 40))       # sandalye
    V.put((np.abs(x - 13) <= 6) & (np.abs(y - 18) <= 1) & (z >= 9) & (z < 24), (150, 30, 40))
    V.put((np.abs(x - 13) <= 6) & (np.abs(y - 18) <= 1.2) & (z >= 22) & (z < 24), GOLD)
    for lx in (8, 18):
        for ly in (9, 17):
            V.put((np.abs(x - lx) < 0.9) & (np.abs(y - ly) < 0.9) & (z < 9), DWD)
    V.put(superell(x, y, 13, 14, 4.5, 3.2, 2.4) & (z >= 11) & (z < 22), (40, 46, 90))                # mavi ceket
    V.put(superell(x, y, 13, 12, 2.2, 1.5, 2) & (z >= 12) & (z < 20), (250, 250, 250))                # yelek
    for s in (-2, 2):                                                                                  # beyaz pantolon
        V.put((np.abs(x - 13 - s) < 1.6) & (y >= 6) & (y < 13) & (z >= 10) & (z < 12), (250, 250, 250))
        V.put((np.abs(x - 13 - s) < 1.4) & (np.abs(y - 6) < 1.4) & (z < 10), (40, 30, 30))
    V.ball(13, 13.5, 24.5, 2.8, (206, 166, 140))
    V.put((((x - 13) / 7.5) ** 2 + ((y - 13.5) / 2.6) ** 2 <= 1) & (z >= 27) & (z < 29 + 2.5 * (1 - np.abs(x - 13) / 7.5)), (18, 14, 28))   # iki köşeli şapka
    V.put((np.abs(x - 13) < 0.8) & (np.abs(y - 11) < 0.7) & (np.abs(z - 28.5) < 0.8), (226, 60, 58))
    for s in (-1, 1):
        V.put((np.abs(x - 13 - s * 5.5) < 0.6) & (np.abs(y - 14) < 1.5) & (z >= 20) & (z < 22), GOLD)  # apolet
    tube(V, [(17.5 - k * 0.3, 12 - k * 0.6, 19 - k * 0.5) for k in range(9)], 1.4, (40, 46, 90))
    return V.bake()


TURK = turk_model()
TURK_OPEN = [turk_model('open', ph) for ph in (0.0, 0.4)]
TURK_CUT = turk_model('cut')
TURK_SWEEP = turk_model('closed', 0, 1.0)
NAPO = napoleon_model()
FLOOR = np.zeros((32, 32, 3), np.uint8); FLOOR[:] = (240, 226, 196)
FLOOR[:16, :16] = (196, 184, 160); FLOOR[16:, 16:] = (196, 184, 160)
FLOOR[::16] = (140, 130, 120); FLOOR[:, ::16] = (140, 130, 120)
HZ = 104


def hall(img, t, dark=0.0, night=False):
    vgrad(img, [(32, 24, 44), (52, 40, 64), (80, 62, 90), (112, 74, 46)], 0, HZ)
    for k in range(4):                                       # kemerli pencereler
        cx_ = 22 + k * 45
        cv2.rectangle(img, (cx_ - 9, 30), (cx_ + 9, HZ - 8), (18, 14, 28), -1)
        cv2.ellipse(img, (cx_, 30), (9, 9), 0, 180, 360, (18, 14, 28), -1)
        cv2.rectangle(img, (cx_ - 7, 30), (cx_ + 7, HZ - 10), (40, 46, 90), -1)
        cv2.ellipse(img, (cx_, 30), (7, 7), 0, 180, 360, (40, 46, 90), -1)
        img[30:HZ - 10, cx_] = (18, 14, 28); img[60, cx_ - 7:cx_ + 8] = (18, 14, 28)
        for s in range(6):
            sx_, sy_ = cx_ - 5 + (s * 7) % 11, 26 + (s * 13) % 60
            if math.sin(t * 2 + s + k) > 0.3:
                img[sy_, sx_] = (250, 250, 250)
        cv2.rectangle(img, (cx_ + 18, 14), (cx_ + 24, HZ), (164, 116, 70), -1)          # pilastr
        img[14:HZ, cx_ + 18] = (206, 166, 110)
    img[HZ - 3:HZ] = (190, 140, 50)
    for cx_ in (45, 135):                                    # avize
        cv2.line(img, (cx_, 0), (cx_, 14), (190, 140, 50), 1)
        cv2.ellipse(img, (cx_, 16), (12, 3), 0, 0, 360, (190, 140, 50), 1)
        for k in range(5):
            xx = cx_ - 10 + k * 5
            img[11:14, xx] = (255, 236, 180)
        glow(img, cx_, 14, 30, (255, 204, 120), 0.3)


def room(t, cam, K, dark=0.0):
    img = np.zeros((CH, CW, 3), np.uint8)
    draw_plane(img, FLOOR, cam, K, y0=HZ)
    img[HZ:] = (img[HZ:] * 0.72).astype(np.uint8)
    hall(img, t)
    fog(img, HZ, 30, (52, 40, 64))
    if dark:
        img[:] = (img * (1 - dark)).astype(np.uint8)
    return img


def scene_objs(img, cam, K, model, napo=True, sh=0):
    obj = np.zeros((CH, CW), bool)
    shadow(img, cam, K, 0, 0, 28, 16, 0, 0.6, HZ)
    items = [(to_screen(0, 0, cam, K)[1], model, 0, 0, 0)]
    if napo:
        shadow(img, cam, K, 6, 26, 9, 8, 0, 0.6, HZ)
        items.append((to_screen(6, 26, cam, K)[1], NAPO, 6, 26, 0))
    for _, S, wx, wy, own in sorted(items, key=lambda i: i[0]):
        draw_stack(img, obj, S, wx, wy, own, cam, K)
    add_outline(img, obj)
    return obj


def sA(t):
    K = 2.0 + (0.6 * min(1.0, (t - 2.8) / 0.5) if t > 2.8 else 0)
    cy = 4 if t < 2.8 else -2
    cam = (0, cy, 0.5 + t * 0.25, CW / 2, 225 if t < 2.8 else 245)
    img = room(t, cam, K)
    scene_objs(img, cam, K, TURK)
    if t < 0.3:
        flash(img, (255, 236, 180), 0.6 * (1 - t / 0.3))
    if 2.8 <= t < 3.0:
        flash(img, (250, 250, 250), 0.4)
    return img


def sB(t):
    tl = t - B_; K = 1.1
    cam = (0, 10, 0.0 + tl * 0.1, CW / 2, 215)
    img = room(t, cam, K)
    scene_objs(img, cam, K, TURK, napo=False)
    press_text(img, "1770", 90, 130, 16, (255, 236, 180))
    return img


def sC(t):
    tl = t - C_; K = 2.7
    cam = (-6, 0, 2.6 + tl * 0.35, CW / 2, 245)
    img = room(t, cam, K)
    scene_objs(img, cam, K, TURK, napo=False)
    return img


def sD(t):
    tl = t - D_; K = 2.5
    cam = (0, 8, 0.15 + 0.15 * math.sin(tl * 0.5), CW / 2, 225)
    img = room(t, cam, K)
    model = TURK if tl < 0.6 else TURK_OPEN[int(t * 7) % 2]
    scene_objs(img, cam, K, model, napo=False)
    if tl >= 0.6:
        X, Y = to_screen(0, 10, cam, K, 10)
        glow(img, X, Y, 40, (255, 204, 120), 0.25)
    return img


def sE(t):
    tl = t - E_; K = 2.5
    sh = shake(t, SLAM, 0.5, 7)
    cam = (0, 8, 0.15, CW / 2 + sh, 225)
    img = room(t, cam, K, dark=0.25 if t >= SLAM else 0)
    if t < SLAM:
        model = TURK_OPEN[int(t * 7) % 2]
    elif t < SLAM + 1.3 and int((t - SLAM) * 8) % 3 == 1:
        model = TURK_CUT
    else:
        model = TURK
    scene_objs(img, cam, K, model, napo=False)
    if SLAM <= t < SLAM + 0.3:
        flash(img, (226, 60, 58), 0.6 * (1 - (t - SLAM) / 0.3))
    if t >= SLAM + 0.3:
        press_text(img, "?", 90 + sh, 80, int(24 + 4 * math.sin(t * 6)), (226, 60, 58))
    return img


def sF(t):
    tl = t - F_; K = 2.3
    sh = shake(t, SWEEP, 0.45, 6)
    cam = (2, 14, -0.35 + tl * 0.12, CW / 2 + sh, 230)
    img = room(t, cam, K)
    scene_objs(img, cam, K, TURK_SWEEP if SWEEP <= t < SWEEP + 0.6 else TURK)
    if t < SWEEP:                                             # Napolyon'un hileli hamlesi (parlayan taş)
        X, Y = to_screen(8, 6, cam, K, 22 + 2 * math.sin(t * 6))
        glow(img, X, Y, 10, (226, 60, 58), 0.4)
    else:                                                     # taşlar uçar
        u = t - SWEEP
        rng = np.random.default_rng(5)
        for k in range(14):
            vx, vy, vz = rng.uniform(10, 40), rng.uniform(-10, 30), rng.uniform(20, 40)
            px, py = 8 + vx * u, 6 + vy * u; pz = 22 + vz * u - 60 * u * u
            if pz > 0:
                X, Y = to_screen(px, py, cam, K, pz)
                c = (250, 250, 250) if k % 2 else (40, 30, 30)
                cv2.rectangle(img, (int(X) - 1, int(Y) - 2), (int(X) + 1, int(Y) + 1), c, -1)
    return img


def sG(t):
    tl = t - G_; K = 2.6 + 0.3 * min(1.0, tl / 6)
    cam = (-2, 10, -0.25 + 0.35 * math.sin(tl * 0.6), CW / 2, 228)
    img = room(t, cam, K, dark=0.35)
    model = TURK if tl < 1.8 else TURK_CUT
    scene_objs(img, cam, K, model, napo=False)
    if tl >= 1.8:
        X, Y = to_screen(40 - 31.5, 30 - 31.5, cam, K, 10)
        glow(img, X, Y, 26 + 2 * math.sin(t * 9), (255, 204, 120), 0.4)
        if 28.1 <= t < 28.3:
            flash(img, (255, 236, 180), 0.5)
    return img


def sH(t):
    tl = t - H_; K = 2.2
    cam = (0, 4, 0.3 + tl * 0.1, CW / 2, 235)
    img = room(t, cam, K, dark=0.45)
    scene_objs(img, cam, K, TURK, napo=False)
    char = min(0.75, tl / 5)
    img[:] = (img * (1 - char * 0.6)).astype(np.uint8)
    rng = np.random.default_rng(int(t * 12))
    X0, Y0 = to_screen(0, 0, cam, K)
    for k in range(70):                                       # alevler
        a = (t * 1.4 + k / 70) % 1
        bx = X0 + (k * 37 % 90) - 45 + rng.uniform(-2, 2)
        by = Y0 + 10 - a * 90
        sz = int(4 * (1 - a)) + 1
        c = (255, 236, 180) if a < 0.2 else (252, 120, 60) if a < 0.5 else (226, 60, 58) if a < 0.8 else (80, 62, 90)
        if 0 <= bx < CW and 0 <= by < CH:
            cv2.rectangle(img, (int(bx), int(by)), (int(bx) + sz, int(by) + sz), c, -1)
    glow(img, X0, Y0 - 30, 80, (252, 120, 60), 0.35)
    return img


def sI(t):
    tl = t - I_; K = 2.3
    cam = (0, 4, 0.2 + tl * 0.05, CW / 2, 235)
    img = room(t, cam, K, dark=0.75)
    scene_objs(img, cam, K, TURK_CUT, napo=False)
    img[:] = (img * 0.55).astype(np.uint8)
    X, Y = to_screen(40 - 31.5, 30 - 31.5, cam, K, 10)
    glow(img, X, Y, 30 + 2 * math.sin(t * 9), (255, 204, 120), 0.45)
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
