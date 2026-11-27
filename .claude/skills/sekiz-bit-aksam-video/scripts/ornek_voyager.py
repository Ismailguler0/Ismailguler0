"""EŞİK test – Voyager 1 (katman yığma, iri 8-bit piksel, sabit palet, seslendirmesiz)."""
import math, sys
import numpy as np, cv2
sys.path.insert(0, '/home/user/Ismailguler0/.claude/skills/sekiz-bit-aksam-video/scripts')
from pix8 import signature, captions, pill, blit, F_BOLD

DUR, FPS, SIG_T = 25.0, 30, 22.6
S1, S2, S3, S4, S5 = 0.0, 4.1, 9.1, 14.1, 19.1
MUSIC = dict(bpm=88, root=196.0)
CAPS = [(0.3, 2.2, "Bu araca mesaj gönderirsen...", 1608), (2.2, 4.0, "cevabı [2 gün] sonra gelir.", 1608),
        (4.3, 6.6, "[1979]: Jüpiter'in yanından", 1608), (6.7, 9.0, "[1980]: Satürn'ün yanından", 1608),
        (9.3, 11.6, "Üzerinde bir [Altın Plak] var", 1608), (11.6, 14.0, "[55 dilde] selam, müzik, sesler", 1608),
        (14.3, 16.6, "[1990]'da dönüp baktı...", 1608), (16.6, 19.0, "Dünya: bir [toz zerresi]", 1608),
        (19.3, 21.6, "Şimdi [1 ışık-günü] uzakta", 1608), (21.7, 24.9, "Sence plağı biri [bulacak mı?]", 1350)]
SFX = [(S2, 'whoosh'), (S3, 'whoosh'), (S4, 'whoosh'), (S5, 'whoosh'), (S3 + 0.3, 'sparkle'), (16.6, 'chime'),
       (SIG_T + 0.05, 'chime')] + [(19.3 + k * 0.2, 'tick') for k in range(8)]
CW, CH = 180, 320
SQ, ZS = 0.62, 0.85
OUTL = (14, 10, 22)

PAL = np.array([(6, 6, 16), (14, 12, 32), (26, 22, 56), (46, 38, 90), (80, 66, 130), (130, 120, 180),
                (60, 62, 70), (110, 112, 124), (170, 172, 184), (220, 222, 230), (250, 250, 255),
                (120, 80, 30), (190, 140, 50), (240, 200, 90), (255, 236, 160),
                (90, 50, 36), (150, 96, 60), (206, 160, 110), (236, 210, 170), (200, 80, 60),
                (180, 160, 120), (226, 206, 160), (40, 80, 160), (90, 150, 230), (170, 220, 255), (255, 140, 60)], float)
_g = (np.arange(32) * 8 + 4).astype(float)
_cube = np.stack(np.meshgrid(_g, _g, _g, indexing='ij'), -1).reshape(-1, 3)
LUT = PAL.astype(np.uint8)[np.argmin(((_cube[:, None, :] - PAL[None]) ** 2).sum(-1), 1)].reshape(32, 32, 32, 3)


def pal8(img):
    q = img >> 3
    return LUT[q[..., 0], q[..., 1], q[..., 2]]


# ---------------------------------------------------------------- voksel modeller
def shade_bake(S, light=(-0.5, -0.6, 0.6)):
    a = S[..., 3] > 0; occ = a.astype(np.float32); nz = S.shape[0]
    gx = np.zeros_like(occ); gy = np.zeros_like(occ); gz = np.zeros_like(occ)
    gx[:, :, 1:-1] = occ[:, :, :-2] - occ[:, :, 2:]; gy[:, 1:-1] = occ[:, :-2] - occ[:, 2:]; gz[1:-1] = occ[:-2] - occ[2:]; gz[-1] = occ[-1]
    n = np.stack([gx, gy, gz + 0.35], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6
    L = np.array(light); L /= np.linalg.norm(L)
    lum = 0.7 + 0.45 * np.clip(n @ L, -0.6, 1); lum = np.where(lum > 1.0, 1.12, np.where(lum > 0.8, 0.92, 0.7))
    S[..., :3] = np.clip(S[..., :3] * lum[..., None], 0, 255).astype(np.uint8)
    return S


class Vox:
    def __init__(s, nx, ny, nz):
        s.S = np.zeros((nz, ny, nx, 4), np.uint8); s.z, s.y, s.x = np.mgrid[0:nz, 0:ny, 0:nx].astype(np.float32)

    def put(s, m, col):
        s.S[m, :3] = col; s.S[m, 3] = 255


def voyager_model():
    V = Vox(96, 44, 26); x, y, z = V.x, V.y, V.z
    cx, cy = 34, 22
    r = np.hypot(x - cx, y - cy)
    dish = (r <= 19) & (z >= 14 + (r / 19) ** 2 * 6) & (z <= 16 + (r / 19) ** 2 * 6)       # çanak anten (parabol)
    V.put(dish, (236, 236, 244)); V.put(dish & (r > 17.5), (180, 180, 196))
    V.put((r <= 2) & (z >= 16) & (z < 24), (170, 172, 184))                               # besleme
    bus = (np.abs(x - cx) <= 7) & (np.abs(y - cy) <= 7) & (np.abs(x - cx) + np.abs(y - cy) <= 11) & (z >= 6) & (z < 14)
    V.put(bus, (120, 122, 136)); V.put(bus & (z >= 12), (170, 172, 184))
    V.put((np.hypot(x - (cx - 7.5), z - 10) <= 3) & (np.abs(y - cy) <= 0.8), (240, 200, 90))  # altın plak
    V.put((x > cx + 7) & (x < 94) & (np.abs(y - cy) <= 0.6) & (np.abs(z - 10) <= 0.6), (200, 200, 210))   # manyetometre
    V.put((np.abs(x - cx) <= 0.7) & (y < cy - 7) & (y > 4) & (np.abs(z - 9) <= 0.7), (160, 160, 170))      # RTG kolu
    for k in range(3):
        V.put((np.hypot(x - cx, z - 9) <= 2.2) & (y > 4 + k * 4) & (y < 7.2 + k * 4), (90, 60, 40))
    V.put((np.abs(x - (cx - 4)) <= 0.7) & (y > cy + 7) & (y < 42) & (np.abs(z - 9) <= 0.7), (160, 160, 170))  # bilim kolu
    V.put((np.abs(x - (cx - 4)) <= 2) & (y > 38) & (y < 43) & (np.abs(z - 9) <= 2), (200, 200, 210))
    return shade_bake(V.S)


def record_model():
    V = Vox(64, 64, 5); x, y, z = V.x, V.y, V.z
    r = np.hypot(x - 31.5, y - 31.5)
    disc = (r <= 31) & (z < 3)
    V.put(disc, (240, 200, 90)); V.put(disc & ((r.astype(int) % 4) == 0) & (r > 10), (190, 140, 50))
    V.put((r <= 9) & (z < 4), (255, 236, 160)); V.put((r <= 1.5), (120, 80, 30))
    V.put(disc & (z == 2) & (np.abs(x - y) < 1.2) & (r < 26) & (r > 12), (255, 236, 160))   # parlama çizgisi
    return shade_bake(V.S)


def rings_model():
    V = Vox(140, 140, 2); x, y, z = V.x, V.y, V.z
    r = np.hypot(x - 69.5, y - 69.5)
    ring = (r >= 42) & (r <= 69) & ~((r > 56) & (r < 58.5))
    V.put(ring, (206, 180, 130)); V.put(ring & (r > 62), (180, 156, 112)); V.put(ring & (r < 48), (226, 206, 160))
    return V.S


VOY, REC, RING = voyager_model(), record_model(), rings_model()


def draw_stack(img, obj, S, px, py, phi, K, sq=SQ):
    nz, ny, nx = S.shape[:3]; c, s = math.cos(phi), math.sin(phi)
    A = np.array([[K * c, -K * s, 0], [K * s * sq, K * c * sq, 0]], np.float64)
    R = math.hypot(nx, ny) * K / 2 + 2
    x0, y0 = int(px - R) - 1, int(py - R - nz * K * ZS) - 1; w, h = int(2 * R) + 3, int(2 * R + nz * K * ZS) + 3
    for zz in range(nz):
        sl = S[zz]
        if not sl[..., 3].any():
            continue
        A2 = A.copy()
        A2[0, 2] = px - x0 - (A[0, 0] * (nx - 1) / 2 + A[0, 1] * (ny - 1) / 2)
        A2[1, 2] = py - y0 - zz * K * ZS - (A[1, 0] * (nx - 1) / 2 + A[1, 1] * (ny - 1) / 2)
        out = cv2.warpAffine(sl, A2, (w, h), flags=cv2.INTER_NEAREST, borderValue=(0, 0, 0, 0))
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(CW, x0 + w), min(CH, y0 + h)
        if xa >= xb or ya >= yb:
            continue
        o = out[ya - y0:yb - y0, xa - x0:xb - x0]; m = o[..., 3] > 0
        img[ya:yb, xa:xb][m] = o[..., :3][m]; obj[ya:yb, xa:xb][m] = True


def add_outline(img, obj):
    d = cv2.dilate(obj.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    img[d & ~obj] = OUTL


# ---------------------------------------------------------------- uzay
_r = np.random.default_rng(5)
STARS = [(_r.uniform(0, CW), _r.uniform(0, CH), _r.uniform(0.2, 1.0), _r.integers(0, 100)) for _ in range(160)]


def space(t, drift=(0, 6)):
    img = np.zeros((CH, CW, 3), np.uint8)
    for y in range(CH):
        k = y / CH; img[y] = (np.array((6, 6, 16)) * (1 - k) + np.array((30, 26, 64)) * k).astype(np.uint8)
    yy, xx = np.mgrid[0:CH, 0:CW]
    bay = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 - 0.47)[yy % 4, xx % 4]
    img[:] = np.clip(img + bay[..., None] * 16, 0, 255).astype(np.uint8)
    for x, y, d, ph in STARS:
        X = int((x + drift[0] * t * d) % CW); Y = int((y + drift[1] * t * d) % CH)
        tw = 0.5 + 0.5 * math.sin(t * (1 + d * 3) + ph)
        img[Y, X] = (250, 250, 255) if (d > 0.8 and tw > 0.5) else (130, 120, 180) if d > 0.4 else (80, 66, 130)
    return img


def sphere(img, cx, cy, r, base, bands=None, spot=None, light=(-0.6, -0.4, 0.7), t=0.0):
    yy, xx = np.mgrid[0:CH, 0:CW].astype(float)
    nx, ny = (xx - cx) / r, (yy - cy) / r; r2 = nx * nx + ny * ny; m = r2 <= 1
    nz = np.sqrt(np.clip(1 - r2, 0, 1)); L = np.array(light); L /= np.linalg.norm(L)
    lum = np.clip(0.18 + 0.9 * (nx * L[0] + ny * L[1] + nz * L[2]), 0, 1.2)
    col = np.zeros((CH, CW, 3)); col[:] = base
    if bands:
        lat = (ny + 0.06 * np.sin(nx * 6 + t)) * len(bands)
        idx = np.clip(((lat + len(bands)) / 2).astype(int), 0, len(bands) - 1)
        col = np.array(bands, float)[idx]
    if spot:
        sx, sy, sr = spot
        sm = ((nx - sx) / sr) ** 2 + ((ny - sy) / (sr * 0.6)) ** 2 <= 1
        col[sm] = (200, 80, 60)
    out = np.clip(col * lum[..., None], 0, 255)
    img[m] = out[m].astype(np.uint8)
    return m


def voyager(img, obj, px, py, phi, K):
    draw_stack(img, obj, VOY, px, py, phi, K)


# ---------------------------------------------------------------- sahneler
def scene1(t):
    img = space(t); obj = np.zeros((CH, CW), bool)
    voyager(img, obj, 90, 175 + 3 * math.sin(t * 1.5), t * 0.6, 2.2)
    add_outline(img, obj)
    return pal8(img)


def scene2(t):
    tl = t - S2; img = space(t, (-10, 2)); obj = np.zeros((CH, CW), bool)
    if tl < 2.5:   # Jüpiter
        jx = 120 - 20 * tl
        sphere(img, jx, 120, 70, (200, 160, 110), bands=[(150, 96, 60), (236, 210, 170), (206, 160, 110), (236, 210, 170), (150, 96, 60), (206, 160, 110)],
               spot=(0.3, 0.35, 0.18), t=t * 0.3)
        voyager(img, obj, 60 + 14 * tl, 220, 0.8 + tl * 0.4, 1.1)
    else:          # Satürn + halkalar (halkalar da dilimlerden)
        u = tl - 2.5; sx_ = 110 - 16 * u
        o2 = np.zeros((CH, CW), bool)
        back = img.copy(); draw_stack(back, o2, RING, sx_, 130, 0.3 + u * 0.05, 1.3, sq=0.35)
        img[o2] = back[o2]
        m = sphere(img, sx_, 126, 40, (226, 206, 160), bands=[(206, 180, 130), (226, 206, 160), (180, 156, 112), (226, 206, 160)])
        front = img.copy(); o3 = np.zeros((CH, CW), bool); draw_stack(front, o3, RING, sx_, 130, 0.3 + u * 0.05, 1.3, sq=0.35)
        yy = np.arange(CH)[:, None] * np.ones((1, CW))
        fm = o3 & (yy > 126)
        img[fm] = front[fm]
        voyager(img, obj, 50 + 16 * u, 230, 1.4 + u * 0.4, 1.1)
    add_outline(img, obj)
    return pal8(img)


def scene3(t):
    tl = t - S3; img = space(t, (0, 3)); obj = np.zeros((CH, CW), bool)
    yy, xx = np.mgrid[0:CH, 0:CW]
    d = np.hypot(xx - 90, (yy - 160) / 0.7)
    img[d < 70] = np.clip(img[d < 70] + 14, 0, 255)
    draw_stack(img, obj, REC, 90, 170, tl * 0.9, 1.9, sq=0.55)
    add_outline(img, obj)
    if int(t * 6) % 3 == 0:
        sx_, sy_ = int(90 + 40 * math.cos(t * 2)), int(160 + 14 * math.sin(t * 2))
        img[sy_, sx_ - 2:sx_ + 3] = (255, 252, 236); img[sy_ - 2:sy_ + 3, sx_] = (255, 252, 236)
    return pal8(img)


def scene4(t):
    tl = t - S4; img = space(t, (0, 1)); obj = np.zeros((CH, CW), bool)
    beam = np.zeros((CH, CW), np.uint8)
    cv2.fillPoly(beam, [np.array([(0, 60), (180, 120), (180, 150), (0, 100)], np.int32)], 1)
    yy, xx = np.mgrid[0:CH, 0:CW]
    B = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16)[yy % 4, xx % 4]
    img[(beam > 0) & (B < 0.35)] = (130, 120, 180)
    ex, ey = 120, 128
    if tl > 2.3:
        k = min(1.0, (tl - 2.3) / 0.4)
        cv2.circle(img, (ex, ey), int(1 + 6 * (1 - k) * 0), (170, 220, 255), -1)
        img[ey, ex] = (170, 220, 255)
        if int(t * 4) % 2 == 0:
            cv2.circle(img, (ex, ey), 6, (240, 200, 90), 1)
    else:
        img[ey, ex] = (90, 150, 230)
    turn = min(1.0, tl / 2.0)
    voyager(img, obj, 60, 240, 2.6 + turn * 1.2, 1.3)
    add_outline(img, obj)
    return pal8(img)


def scene5(t):
    tl = t - S5; img = space(t, (0, 14)); obj = np.zeros((CH, CW), bool)
    k = min(1.0, tl / 5.5); K = 2.0 - 1.4 * k
    voyager(img, obj, 90, 140 - 20 * k, t * 0.4, K)
    add_outline(img, obj)
    return pal8(img)


def frame_at(t):
    if t < S2:
        img = scene1(t)
    elif t < S3:
        img = scene2(t)
    elif t < S4:
        img = scene3(t)
    elif t < S5:
        img = scene4(t)
    else:
        img = scene5(t)
    fr = np.ascontiguousarray(cv2.resize(img, (1080, 1920), interpolation=cv2.INTER_NEAREST))
    if S5 + 0.2 < t < SIG_T + 0.2:
        km = 25.9 * min(1.0, (t - S5 - 0.2) / 1.6)
        blit(fr, pill(f"[{km:.1f}".replace('.', ',') + "] milyar km", 60, F_BOLD), 540, 300)
    if t > SIG_T - 0.3:
        k = min(1.0, (t - SIG_T + 0.3) / 0.6); yy = np.arange(1920)[:, None, None]
        fr[:] = (fr * (1 - 0.5 * k * np.clip((yy - 1250) / 300, 0, 1))).astype(np.uint8)
    captions(fr, t, CAPS)
    signature(fr, t, SIG_T)
    return fr
