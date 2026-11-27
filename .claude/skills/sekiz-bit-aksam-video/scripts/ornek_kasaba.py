"""Katman yığma v2: HER ŞEY dilimlerden (araba, evler, ağaçlar, lambalar, yol), dönen kamera, yuvarlak ve ince pikselli modeller."""
import math, sys
import numpy as np, cv2
sys.path.insert(0, '/home/user/Ismailguler0/.claude/skills/sekiz-bit-aksam-video/scripts')
from pix8 import signature, palettize

DUR, FPS = 13.0, 30
T_DRIVE, SIG_T = 3.0, 10.6
CAPS = []
SFX = [(T_DRIVE, 'whoosh'), (SIG_T + 0.05, 'chime')]
MUSIC = dict(bpm=120, root=220.0)
CW, CH = 180, 320                  # x6 -> 1080x1920 (iri 8-bit piksel)
OUTL = (44, 28, 44)
SQ, ZS = 0.62, 0.85
PAL8 = np.array([  # elle seçilmiş sabit 8-bit palet
    (24, 18, 40), (44, 28, 44), (40, 30, 84), (70, 46, 96), (112, 70, 112), (160, 96, 120), (214, 120, 112), (240, 150, 114),
    (70, 50, 90), (112, 86, 132), (150, 122, 172),
    (120, 26, 40), (180, 44, 50), (226, 62, 58), (250, 124, 106),
    (90, 130, 190), (150, 204, 236), (214, 236, 250),
    (30, 60, 40), (52, 100, 56), (84, 140, 70), (120, 180, 92), (176, 210, 120), (48, 44, 60),
    (104, 70, 48), (150, 100, 64), (210, 176, 150),
    (66, 62, 80), (96, 92, 110), (206, 196, 182),
    (255, 226, 130), (255, 252, 236), (240, 150, 190), (190, 90, 60)], float)
_g = (np.arange(32) * 8 + 4).astype(float)
_cube = np.stack(np.meshgrid(_g, _g, _g, indexing='ij'), -1).reshape(-1, 3)
LUT8 = PAL8.astype(np.uint8)[np.argmin(((_cube[:, None, :] - PAL8[None]) ** 2).sum(-1), 1)].reshape(32, 32, 32, 3)


def pal8(img):
    q = img >> 3
    return LUT8[q[..., 0], q[..., 1], q[..., 2]]                # ekran ezilmesi (eğik bakış) ve katman yüksekliği


# ---------------------------------------------------------------- yuvarlak voksel modeller (dilim resmi olarak)
def shade_bake(S, light=(-0.5, -0.6, 0.6)):
    """Dilimlere hafif hacim gölgesi pişir: alt katlar koyu, ışığa bakan kenarlar açık."""
    a = S[..., 3] > 0; nz = S.shape[0]
    occ = a.astype(np.float32)
    gx = np.zeros_like(occ); gy = np.zeros_like(occ); gz = np.zeros_like(occ)
    gx[:, :, 1:-1] = occ[:, :, :-2] - occ[:, :, 2:]; gy[:, 1:-1] = occ[:, :-2] - occ[:, 2:]; gz[1:-1] = occ[:-2] - occ[2:]
    gz[-1] = occ[-1]; gz[0] = gz[0]
    n = np.stack([gx, gy, gz + 0.35], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6
    L = np.array(light); L /= np.linalg.norm(L)
    lum = 0.7 + 0.45 * np.clip(n @ L, -0.6, 1)
    lum = np.where(lum > 1.0, 1.12, np.where(lum > 0.8, 0.92, 0.7))          # sadece 3 ton
    zf = np.where(np.arange(nz) < nz * 0.25, 0.85, 1.0)[:, None, None]
    S[..., :3] = np.clip(S[..., :3] * (lum * zf)[..., None], 0, 255).astype(np.uint8)
    return S


class Vox:
    def __init__(s, nx, ny, nz):
        s.S = np.zeros((nz, ny, nx, 4), np.uint8)
        s.z, s.y, s.x = np.mgrid[0:nz, 0:ny, 0:nx].astype(np.float32)

    def put(s, m, col):
        s.S[m, :3] = col; s.S[m, 3] = 255

    def bake(s):
        return shade_bake(s.S)


def superell(x, y, cx, cy, rx, ry, p=4):
    return (np.abs((x - cx) / rx) ** p + np.abs((y - cy) / ry) ** p) <= 1


def car_model():
    V = Vox(62, 32, 26); x, y, z = V.x, V.y, V.z
    RED, DRED, LRED, GLASS, DARK, CHR = (226, 60, 58), (160, 34, 44), (250, 120, 104), (160, 214, 240), (36, 32, 42), (226, 226, 234)
    body = superell(x, y, 31, 15.5, 30, 14.5, 3.5) & (z >= 4) & (z < 13 - 2.5 * (np.abs((x - 31) / 30) ** 6))
    V.put(body, RED); V.put(body & (z < 6), DRED); V.put(body & (z >= 11), LRED)
    k = np.clip(z - 13, 0, 99)
    cab = superell(x, y, 30, 15.5, 13 - 0.55 * k, 11.5 - 0.25 * k, 3) & (z >= 12) & (z < 22)
    V.put(cab, GLASS)
    pillar = cab & ((np.abs(x - 30) < 1.2) | (z >= 20))
    V.put(pillar, RED); V.put(cab & (z >= 21), LRED)
    for cxw in (14, 48):
        for (y0, y1) in ((0, 6), (26, 32)):
            w = ((x - cxw) ** 2 + (z - 6) ** 2 <= 36) & (y >= y0) & (y < y1)
            V.put(w, DARK); V.put(w & ((x - cxw) ** 2 + (z - 6) ** 2 <= 8), CHR)
    V.put(superell(x, y, 60.5, 8, 1.5, 3, 2) & (z >= 7) & (z < 10), (255, 236, 140))
    V.put(superell(x, y, 60.5, 23, 1.5, 3, 2) & (z >= 7) & (z < 10), (255, 236, 140))
    V.put(superell(x, y, 1.5, 8, 1.5, 3, 2) & (z >= 8) & (z < 10), (255, 90, 70))
    V.put(superell(x, y, 1.5, 23, 1.5, 3, 2) & (z >= 8) & (z < 10), (255, 90, 70))
    V.put(body & (z >= 6) & (z < 7) & ((x < 3) | (x > 58)), CHR)
    return V.bake()


def palm_model(seed):
    r = np.random.default_rng(seed); V = Vox(30, 30, 46); x, y, z = V.x, V.y, V.z
    cxz = 15 + 3 * np.sin(z / 18 + seed); cyz = 15 + 2 * np.cos(z / 22 + seed)
    trunk = ((x - cxz) ** 2 + (y - cyz) ** 2 <= 4.2) & (z < 38)
    V.put(trunk, (138, 96, 60)); V.put(trunk & (z.astype(int) % 4 == 0), (104, 70, 46))
    tx, ty = 15 + 3 * math.sin(38 / 18 + seed), 15 + 2 * math.cos(38 / 22 + seed)
    for kk in range(8):
        a = kk * 2 * math.pi / 8 + r.random() * 0.3
        for u in np.linspace(0, 13, 40):
            fx, fy, fz = tx + u * math.cos(a), ty + u * math.sin(a), 39 - u * u / 14
            m = ((x - fx) ** 2 + (y - fy) ** 2 + ((z - fz) * 1.4) ** 2 <= 2.4 * (1 - u / 16))
            V.put(m, (76, 158, 72) if kk % 2 else (100, 184, 86))
    V.put(((x - tx) ** 2 + (y - ty) ** 2 + (z - 38) ** 2 <= 9), (90, 170, 80))
    for kk in range(3):
        V.put(((x - tx - 2 * math.cos(kk * 2)) ** 2 + (y - ty - 2 * math.sin(kk * 2)) ** 2 + (z - 36) ** 2 <= 2.2), (130, 90, 50))
    return V.bake()


def tree_model(seed, autumn=False):
    r = np.random.default_rng(seed); V = Vox(30, 30, 36); x, y, z = V.x, V.y, V.z
    V.put(((x - 15) ** 2 + (y - 15) ** 2 <= 3) & (z < 16), (120, 84, 56))
    cols = [(190, 100, 50), (230, 150, 60), (250, 190, 90)] if autumn else [(54, 120, 60), (80, 156, 74), (120, 190, 96)]
    for k in range(7):
        bx, by, bz, br = 15 + r.uniform(-6, 6), 15 + r.uniform(-6, 6), 22 + r.uniform(-4, 6), r.uniform(6, 9)
        m = (x - bx) ** 2 + (y - by) ** 2 + ((z - bz) * 1.1) ** 2 <= br * br
        V.put(m & (V.S[..., 3] == 0), cols[k % 3])
    return V.bake()


def house_model(w, d, h, wall, roof, seed):
    r = np.random.default_rng(seed); V = Vox(w + 4, d + 4, h + d // 2 + 6); x, y, z = V.x, V.y, V.z
    walls = (x >= 2) & (x < w + 2) & (y >= 2) & (y < d + 2) & (z < h)
    V.put(walls, wall)
    for zz in range(4, h - 4, 9):                                        # pencereler
        for xx in range(6, w - 2, 9):
            lit = r.random() < 0.6
            col = (255, 214, 120) if lit else (70, 84, 120)
            for yy in (2, d + 1):
                V.put((x >= xx) & (x < xx + 4) & (z >= zz) & (z < zz + 5) & (y == yy), col)
        for yy in range(6, d - 2, 9):
            col = (255, 214, 120) if r.random() < 0.5 else (70, 84, 120)
            for xw in (2, w + 1):
                V.put((y >= yy) & (y < yy + 4) & (z >= zz) & (z < zz + 5) & (x == xw), col)
    V.put((x >= w // 2 - 1) & (x < w // 2 + 4) & (z < 8) & (y == d + 1), (120, 76, 52))
    rz = z - h                                                            # üçgen çatı (sırt x boyunca)
    roofm = (rz >= 0) & (np.abs(y - (d / 2 + 2)) <= (d / 2 + 2) - rz) & (x >= 0) & (x < w + 4)
    V.put(roofm, roof); V.put(roofm & (rz.astype(int) % 3 == 0), tuple(int(c * 0.82) for c in roof))
    V.put((x >= w - 4) & (x < w - 1) & (y >= 4) & (y < 7) & (z >= h) & (z < h + d // 2 + 4), (150, 80, 70))
    return V.bake()


def lamp_model():
    V = Vox(7, 7, 34); x, y, z = V.x, V.y, V.z
    V.put(((x - 3) ** 2 + (y - 3) ** 2 <= 1.2) & (z < 28), (50, 46, 58))
    V.put(((x - 3) ** 2 + (y - 3) ** 2 <= 6) & (z >= 28) & (z < 32), (255, 224, 140))
    V.put(((x - 3) ** 2 + (y - 3) ** 2 <= 7) & (z >= 32), (50, 46, 58))
    return V.bake()


def bush_model(seed):
    r = np.random.default_rng(seed); V = Vox(16, 16, 10); x, y, z = V.x, V.y, V.z
    V.put((x - 8) ** 2 + (y - 8) ** 2 + ((z - 2) * 1.6) ** 2 <= 42, (70, 140, 70))
    for k in range(6):
        fx, fy = r.uniform(3, 13), r.uniform(3, 13)
        V.put(((x - fx) ** 2 + (y - fy) ** 2 <= 1.4) & (V.S[..., 3] > 0) & (z >= 3), [(250, 150, 190), (250, 240, 140), (255, 255, 255)][k % 3])
    return V.bake()


CAR = car_model()

# ---------------------------------------------------------------- dünya (birim = voksel)
WW, WH = 640, 720
rng = np.random.default_rng(3)
GROUND = np.zeros((WH, WW, 3), np.uint8); GROUND[:] = (100, 154, 78)
sp = rng.random((WH, WW))
GROUND[sp < 0.08] = (122, 178, 92); GROUND[sp > 0.94] = (80, 128, 62)
GROUND[(sp > 0.5) & (sp < 0.5025)] = (250, 232, 130); GROUND[(sp > 0.6) & (sp < 0.6015)] = (250, 170, 200)
GRASS = GROUND.copy()
RX0, RY0, RX1, RY1, RW, RC = 100, 100, 540, 620, 48, 46
road = np.zeros((WH, WW), np.uint8)
cv2.rectangle(road, (RX0 - RW // 2, RY0 - RW // 2), (RX1 + RW // 2, RY1 + RW // 2), 1, -1)
cv2.rectangle(road, (RX0 + RW // 2, RY0 + RW // 2), (RX1 - RW // 2, RY1 - RW // 2), 0, -1)
curb = cv2.dilate(road, np.ones((7, 7), np.uint8)) - road
GROUND[curb > 0] = (206, 196, 182); GROUND[road > 0] = (72, 68, 84); GROUND[(road > 0) & (sp < 0.05)] = (84, 80, 96)
for x in range(RX0, RX1, 20):
    GROUND[RY0 - 1:RY0 + 1, x:x + 10] = (244, 222, 120); GROUND[RY1 - 1:RY1 + 1, x:x + 10] = (244, 222, 120)
for y in range(RY0, RY1, 20):
    GROUND[y:y + 10, RX0 - 1:RX0 + 1] = (244, 222, 120); GROUND[y:y + 10, RX1 - 1:RX1 + 1] = (244, 222, 120)
cv2.circle(GROUND, (320, 360), 42, (206, 196, 182), -1); cv2.circle(GROUND, (320, 360), 38, (72, 128, 196), -1)
for a in np.linspace(0, 2 * np.pi, 9)[:-1]:
    cv2.circle(GROUND, (int(320 + 26 * math.cos(a)), int(360 + 20 * math.sin(a))), 3, (110, 180, 90), -1)
G4 = np.dstack([GROUND, np.full((WH, WW), 255, np.uint8)])[None]   # tek dilimli "zemin modeli"

OBJS = []   # (dilimler, dünya x, dünya y, kendi açısı)
for i, (x, y, w, d, h, wall, roof) in enumerate([(200, 190, 64, 48, 30, (238, 204, 172), (196, 84, 64)), (380, 186, 72, 54, 38, (184, 212, 232), (96, 104, 156)),
                                                  (196, 500, 66, 52, 26, (242, 232, 184), (176, 96, 62)), (390, 506, 64, 50, 34, (214, 184, 222), (126, 74, 114))]):
    OBJS.append((house_model(w, d, h, wall, roof, i), x, y, 0.0))
PALMS = [palm_model(i) for i in range(4)]
for i, (x, y) in enumerate([(46, 240), (46, 460), (594, 280), (594, 520), (240, 40), (440, 40), (280, 680), (480, 680)]):
    OBJS.append((PALMS[i % 4], x, y, i * 0.7))
TREES = [tree_model(i, autumn=(i % 3 == 0)) for i in range(6)]
for i, (x, y) in enumerate([(260, 330), (390, 300), (250, 410), (400, 420), (300, 250), (340, 470)]):
    OBJS.append((TREES[i], x, y, i * 1.1))
LAMP = lamp_model()
for (x, y) in [(70, 140), (70, 580), (570, 160), (570, 600), (320, 70), (320, 650)]:
    OBJS.append((LAMP, x, y, 0.0))
BUSHES = [bush_model(i) for i in range(4)]
for i, (x, y) in enumerate([(160, 260), (470, 270), (170, 440), (470, 450), (150, 350), (500, 360), (120, 160), (520, 560)]):
    OBJS.append((BUSHES[i % 4], x, y, i * 0.9))


# ---------------------------------------------------------------- rota + kamera
def build_route():
    pts = []
    corners = [(RX0, RY1), (RX0, RY0), (RX1, RY0), (RX1, RY1)]
    for i in range(4):
        a = np.array(corners[i], float); b = np.array(corners[(i + 1) % 4], float); c = np.array(corners[(i + 2) % 4], float)
        d1 = (b - a) / np.linalg.norm(b - a); d2 = (c - b) / np.linalg.norm(c - b)
        pts += list(np.linspace(a + d1 * RC, b - d1 * RC, 60))
        p0, p2 = b - d1 * RC, b + d2 * RC
        pts += [(1 - s) ** 2 * p0 + 2 * (1 - s) * s * b + s * s * p2 for s in np.linspace(0, 1, 24)]
    P = np.array(pts); cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    return P, cum


RP, RCUM = build_route()


def route(u):
    u = u % RCUM[-1]; i = max(1, min(len(RP) - 1, int(np.searchsorted(RCUM, u))))
    a = (u - RCUM[i - 1]) / max(1e-6, RCUM[i] - RCUM[i - 1]); p = RP[i - 1] + (RP[i] - RP[i - 1]) * a
    dv = RP[i] - RP[i - 1]
    return p[0], p[1], math.atan2(dv[1], dv[0])


def speed(t):
    return 80 + 60 * min(1.0, max(0.0, (t - T_DRIVE) / 1.2))


NF = int(DUR * FPS) + 2
_u = np.concatenate([[0], np.cumsum([speed(T_DRIVE + i / FPS) / FPS for i in range(NF)])])
STATE = [route(_u[i] + 380) for i in range(NF)]
_hd = np.unwrap([s[2] for s in STATE])
_cam = np.copy(_hd)
for i in range(1, len(_cam)):                                             # kamera açısı yumuşak takip
    _cam[i] = _cam[i - 1] + (_hd[i] - _cam[i - 1]) * 0.08


def car_state(t):
    i = min(NF - 1, max(0, int(round((t - T_DRIVE) * FPS))))
    x, y, _ = STATE[i]
    return x, y, _hd[i], _cam[i]


# ---------------------------------------------------------------- dilim çizici
def draw_stack(img, obj, S, wx, wy, own, cam, K=1.0, outline=True, zoff=0.0):
    """S: (Z,Y,X,4). Model merkezi (wx,wy) dünyada; kamera (cx,cy,θc, ekran merkezi)."""
    ccx, ccy, th, sx0, sy0 = cam
    nz, ny, nx = S.shape[:3]
    dx, dy = wx - ccx, wy - ccy
    c0, s0 = math.cos(-th), math.sin(-th)
    rx, ry = dx * c0 - dy * s0, dx * s0 + dy * c0
    px, py = sx0 + rx * K, sy0 + ry * K * SQ
    phi = own - th
    c, s = math.cos(phi), math.sin(phi)
    A = np.array([[K * c, -K * s, 0], [K * s * SQ, K * c * SQ, 0]], np.float64)
    R = math.hypot(nx, ny) * K / 2 + 2
    if px + R < 0 or px - R > CW or py + R < -nz * K * ZS or py - R > CH:
        return
    x0, y0 = int(px - R) - 1, int(py - R - nz * K * ZS) - 1
    w, h = int(2 * R) + 3, int(2 * R + nz * K * ZS) + 3
    for z in range(nz):
        sl = S[z]
        if not sl[..., 3].any():
            continue
        A2 = A.copy()
        A2[0, 2] = px - x0 - (A[0, 0] * (nx - 1) / 2 + A[0, 1] * (ny - 1) / 2)
        A2[1, 2] = py - y0 - (z + zoff) * K * ZS - (A[1, 0] * (nx - 1) / 2 + A[1, 1] * (ny - 1) / 2)
        out = cv2.warpAffine(sl, A2, (w, h), flags=cv2.INTER_NEAREST, borderValue=(0, 0, 0, 0))
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(CW, x0 + w), min(CH, y0 + h)
        if xa >= xb or ya >= yb:
            continue
        o = out[ya - y0:yb - y0, xa - x0:xb - x0]; m = o[..., 3] > 0
        img[ya:yb, xa:xb][m] = o[..., :3][m]
        if outline:
            obj[ya:yb, xa:xb][m] = True
    return ry


def draw_ground(img, cam, K):
    ccx, ccy, th, sx0, sy0 = cam
    c, s = math.cos(-th), math.sin(-th)
    A = np.array([[K * c, -K * s, 0], [K * s * SQ, K * c * SQ, 0]], np.float64)
    A[0, 2] = sx0 - (A[0, 0] * ccx + A[0, 1] * ccy); A[1, 2] = sy0 - (A[1, 0] * ccx + A[1, 1] * ccy)
    img[:] = cv2.warpAffine(GRASS, A, (CW, CH), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_WRAP)   # sonsuz çimen
    out = cv2.warpAffine(G4[0], A, (CW, CH), flags=cv2.INTER_NEAREST, borderValue=(0, 0, 0, 0))
    m = out[..., 3] > 0
    img[m] = out[..., :3][m]


def to_screen(wx, wy, cam, K):
    ccx, ccy, th, sx0, sy0 = cam
    dx, dy = wx - ccx, wy - ccy; c0, s0 = math.cos(-th), math.sin(-th)
    return sx0 + (dx * c0 - dy * s0) * K, sy0 + (dx * s0 + dy * c0) * K * SQ


def glow(img, x, y, r, col=(255, 210, 130), a=0.32):
    yy, xx = np.mgrid[0:CH, 0:CW]
    B = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16)[yy % 4, xx % 4]
    d = np.hypot(xx - x, (yy - y) / SQ) / max(1, r)
    m = (d < 1) & (B < (1 - d) * 0.9)
    img[m] = (img[m] * (1 - a) + np.array(col) * a).astype(np.uint8)


def add_outline(img, obj):
    d = cv2.dilate(obj.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    img[d & ~obj] = OUTL


def turntable(t):
    img = np.zeros((CH, CW, 3), np.uint8)
    for y in range(CH):
        k = y / CH; img[y] = (np.array((40, 30, 84)) * (1 - k) + np.array((240, 140, 110)) * k) // 4 * 4
    cx, cy = 90, 200
    for rr, col in ((75, (70, 50, 90)), (73, (112, 86, 132))):
        cv2.ellipse(img, (cx, cy + (4 if rr == 75 else 2)), (rr, int(rr * SQ)), 0, 0, 360, col, -1, cv2.LINE_8)
    cv2.ellipse(img, (cx, cy + 2), (73, int(73 * SQ)), 0, 0, 360, (150, 122, 172), 1, cv2.LINE_8)
    obj = np.zeros((CH, CW), bool)
    cam = (0.0, 0.0, -t * 2 * math.pi / 3.0, cx, cy)
    yy, xx = np.mgrid[0:CH, 0:CW]
    bay = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 - 0.47)[yy % 4, xx % 4]
    img[:] = np.clip(img + bay[..., None] * 34, 0, 255).astype(np.uint8)            # gökyüzü geçişlerinde nokta doku
    draw_stack(img, obj, CAR, 0.0, 0.0, 0.0, cam, K=2.0)
    add_outline(img, obj)
    return pal8(img)


def drive(t):
    cx, cy, hd, th = car_state(t)
    camth = th + math.pi / 2                                              # araba ekranda yukarı baksın
    K = 1.2
    cam = (cx, cy, camth, CW / 2, CH * 0.66)
    img = np.zeros((CH, CW, 3), np.uint8)
    draw_ground(img, cam, K)
    # far ışığı ve gölgeler
    fx, fy = to_screen(cx + 60 * math.cos(hd), cy + 60 * math.sin(hd), cam, K)
    glow(img, fx, fy, 25, (255, 236, 170), 0.32)
    sh = np.zeros((CH, CW), np.uint8)
    items = []
    for (S, x, y, own) in OBJS:
        X, Y = to_screen(x, y, cam, K)
        if -40 < X < CW + 40 and -60 < Y < CH + 80:
            r = max(S.shape[1], S.shape[2]) * K * 0.42
            cv2.ellipse(sh, (int(X + 2), int(Y + 2)), (int(r), int(r * SQ)), 0, 0, 360, 1, -1)
            items.append((Y, S, x, y, own))
    X, Y = to_screen(cx, cy, cam, K)
    cv2.ellipse(sh, (int(X + 2), int(Y + 2)), (int(30 * K * 0.55), int(30 * K * SQ * 0.55)), math.degrees(hd - camth), 0, 360, 1, -1)
    img[sh > 0] = (img[sh > 0] * 0.68).astype(np.uint8)
    items.append((Y + 1, CAR, cx, cy, hd))
    items.sort(key=lambda it: it[0])
    obj = np.zeros((CH, CW), bool)
    for _, S, x, y, own in items:
        draw_stack(img, obj, S, x, y, own, cam, K)
    add_outline(img, obj)
    for (S, x, y, own) in OBJS:                                          # lamba parıltısı
        if S is LAMP:
            X, Y = to_screen(x, y, cam, K)
            if -30 < X < CW + 30 and -30 < Y < CH + 30:
                glow(img, X, Y - 30 * K * ZS, 17, (255, 210, 130), 0.3)
    for k in range(6):                                                    # egzoz dumanı
        a = (t * 3 + k / 6) % 1.0
        ex, ey = cx - (32 + a * 34) * math.cos(hd), cy - (32 + a * 34) * math.sin(hd)
        X, Y = to_screen(ex, ey, cam, K)
        cv2.circle(img, (int(X), int(Y - (8 + 14 * a) * K * ZS)), int(2 + 3 * a), (224, 218, 234) if a < 0.6 else (186, 182, 200), -1, cv2.LINE_8)
    img[:] = np.clip(img.astype(np.float32) * np.array([1.05, 0.92, 0.96]) + np.array([10, 0, 12]), 0, 255).astype(np.uint8)
    return pal8(img)


def frame_at(t):
    img = turntable(t) if t < T_DRIVE else drive(t)
    fr = np.ascontiguousarray(cv2.resize(img, (1080, 1920), interpolation=cv2.INTER_NEAREST))
    if t > SIG_T - 0.3:
        k = min(1.0, (t - SIG_T + 0.3) / 0.6); yy = np.arange(1920)[:, None, None]
        fr[:] = (fr * (1 - 0.6 * k * np.clip((yy - 1250) / 300, 0, 1))).astype(np.uint8)
    signature(fr, t, SIG_T)
    return fr
