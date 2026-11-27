"""Katman yığma (sprite stacking) ortak motoru – EŞİK 8-bit videoları.
Tuval 180x320, x6 büyütme, sabit palet (set_palette), dünya kamerası (cx, cy, açı, ekran_x, ekran_y)."""
import math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

CW, CH = 180, 320
SQ, ZS = 0.62, 0.85
OUTL = (12, 10, 24)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16
YY, XX = np.mgrid[0:CH, 0:CW]
BAY = BAYER[YY % 4, XX % 4]
_LUT = None
PRESS = '/home/user/esik-araclar/fontlar/node_modules/@expo-google-fonts/press-start-2p/400Regular/PressStart2P_400Regular.ttf'


def set_palette(pal):
    global _LUT
    P = np.array(pal, float)
    g = (np.arange(32) * 8 + 4).astype(float)
    cube = np.stack(np.meshgrid(g, g, g, indexing='ij'), -1).reshape(-1, 3)
    _LUT = P.astype(np.uint8)[np.argmin(((cube[:, None, :] - P[None]) ** 2).sum(-1), 1)].reshape(32, 32, 32, 3)


def pal8(img):
    q = np.clip(img, 0, 255).astype(np.uint8) >> 3
    return _LUT[q[..., 0], q[..., 1], q[..., 2]]


def shade_bake(S, light=(-0.5, -0.6, 0.6)):
    occ = (S[..., 3] > 0).astype(np.float32)
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

    def clear(s, m):
        s.S[m, 3] = 0

    def ball(s, cx, cy, cz, r, col, sz=1.0):
        s.put((s.x - cx) ** 2 + (s.y - cy) ** 2 + ((s.z - cz) / sz) ** 2 <= r * r, col)

    def bake(s):
        return shade_bake(s.S)


def superell(x, y, cx, cy, rx, ry, p=4):
    return (np.abs((x - cx) / rx) ** p + np.abs((y - cy) / ry) ** p) <= 1


def draw_stack(img, obj, S, wx, wy, own, cam, K=1.0, zoff=0.0, zmax=None, zmin_screen=None, outline=True):
    ccx, ccy, th, sx0, sy0 = cam
    nz, ny, nx = S.shape[:3]
    dx, dy = wx - ccx, wy - ccy; c0, s0 = math.cos(-th), math.sin(-th)
    rx, ry = dx * c0 - dy * s0, dx * s0 + dy * c0
    px, py = sx0 + rx * K, sy0 + ry * K * SQ
    phi = own - th; c, s = math.cos(phi), math.sin(phi)
    A = np.array([[K * c, -K * s, 0], [K * s * SQ, K * c * SQ, 0]], np.float64)
    R = math.hypot(nx, ny) * K / 2 + 2
    top = (nz + abs(zoff)) * K * ZS
    if px + R < 0 or px - R > CW or py + R + abs(zoff) * K < 0 or py - R - top > CH:
        return
    x0, y0 = int(px - R) - 1, int(py - R - top) - 1
    w, h = int(2 * R) + 3, int(2 * R + top + abs(zoff) * K) + 3
    for zz in range(nz if zmax is None else min(nz, zmax)):
        if zmin_screen is not None and zz + zoff < zmin_screen:
            continue
        sl = S[zz]
        if not sl[..., 3].any():
            continue
        A2 = A.copy()
        A2[0, 2] = px - x0 - (A[0, 0] * (nx - 1) / 2 + A[0, 1] * (ny - 1) / 2)
        A2[1, 2] = py - y0 - (zz + zoff) * K * ZS - (A[1, 0] * (nx - 1) / 2 + A[1, 1] * (ny - 1) / 2)
        out = cv2.warpAffine(sl, A2, (w, h), flags=cv2.INTER_NEAREST, borderValue=(0, 0, 0, 0))
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(CW, x0 + w), min(CH, y0 + h)
        if xa >= xb or ya >= yb:
            continue
        o = out[ya - y0:yb - y0, xa - x0:xb - x0]; m = o[..., 3] > 0
        img[ya:yb, xa:xb][m] = o[..., :3][m]
        if outline:
            obj[ya:yb, xa:xb][m] = True


def to_screen(wx, wy, cam, K, wz=0.0):
    ccx, ccy, th, sx0, sy0 = cam
    dx, dy = wx - ccx, wy - ccy; c0, s0 = math.cos(-th), math.sin(-th)
    return sx0 + (dx * c0 - dy * s0) * K, sy0 + (dx * s0 + dy * c0) * K * SQ - wz * K * ZS


def add_outline(img, obj):
    d = cv2.dilate(obj.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    img[d & ~obj] = OUTL


def glow(img, x, y, r, col=(255, 210, 130), a=0.35):
    d = np.hypot(XX - x, (YY - y) / 0.8) / max(1, r)
    m = (d < 1) & (BAY < (1 - d) * 0.9)
    img[m] = (img[m] * (1 - a) + np.array(col) * a).astype(np.uint8)


def shadow(img, cam, K, wx, wy, rx, ry=None, ang=0.0, a=0.65, ymin=0):
    X, Y = to_screen(wx, wy, cam, K)
    m = np.zeros((CH, CW), np.uint8)
    ry = rx if ry is None else ry
    cv2.ellipse(m, (int(X + 3), int(Y + 2)), (int(rx * K), int(ry * K * SQ)), math.degrees(ang - cam[2]), 0, 360, 1, -1)
    m[:ymin] = 0
    img[m > 0] = (img[m > 0] * a).astype(np.uint8)


def vgrad(img, stops, y0=0, y1=CH):
    for y in range(y0, y1):
        u = (y - y0) / max(1, y1 - y0) * (len(stops) - 1); i = min(len(stops) - 2, int(u)); f = u - i
        lvl = BAYER[y % 4, np.arange(CW) % 4] < f
        img[y] = np.where(lvl[:, None], stops[i + 1], stops[i])


def make_tile(base, c1, c2, T=96, f1=3, f2=4):
    yy, xx = np.mgrid[0:T, 0:T]
    tile = np.zeros((T, T, 3), np.uint8); tile[:] = base
    w = np.sin(xx / T * 2 * np.pi * f1 + np.sin(yy / T * 2 * np.pi * 2) * 1.5) * np.cos(yy / T * 2 * np.pi * f2)
    b = BAYER[yy % 4, xx % 4]
    tile[(w > 0.35) & (b < 0.5)] = c1
    tile[(w > 0.75) & (b < 0.6)] = c2
    return tile


def draw_plane(img, tile, cam, K, t=0.0, flow=(0.0, 0.0), y0=0):
    ccx, ccy, th, sx0, sy0 = cam
    c, s = math.cos(-th), math.sin(-th)
    A = np.array([[K * c, -K * s, 0], [K * s * SQ, K * c * SQ, 0]], np.float64)
    ox, oy = ccx - flow[0] * t, ccy - flow[1] * t
    A[0, 2] = sx0 - (A[0, 0] * ox + A[0, 1] * oy); A[1, 2] = sy0 - (A[1, 0] * ox + A[1, 1] * oy)
    pl = cv2.warpAffine(tile, A, (CW, CH), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_WRAP)
    img[y0:] = pl[y0:]


def fog(img, y0, depth, col):
    k = np.clip(1 - (np.arange(CH) - y0) / depth, 0, 1)[:, None]
    m = (BAY < k * 0.8) & (YY >= y0)
    img[m] = col


def press_text(img, txt, cx, cy, size, col, outl=OUTL):
    f = ImageFont.truetype(PRESS, size)
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    w = d.textlength(txt, font=f)
    for ox, oy in ((1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((cx - w / 2 + ox, cy - size / 2 + oy), txt, font=f, fill=outl)
    d.text((cx - w / 2, cy - size / 2), txt, font=f, fill=col)
    img[:] = np.array(im)


def flash(img, col, k):
    img[:] = (img * (1 - k) + np.array(col) * k).astype(np.uint8)


def shake(t, t0, dur=0.35, amp=5):
    if t0 <= t < t0 + dur:
        return int(amp * (1 - (t - t0) / dur)) * (1 if int(t * 40) % 2 else -1)
    return 0


def tube(V, pts, rad, col):
    for (px, py, pz) in pts:
        V.put((V.x - px) ** 2 + (V.y - py) ** 2 + (V.z - pz) ** 2 <= rad * rad, col)


def person(V, cx, cy, z0, body, head=(206, 166, 110), hat=None, h=1.0):
    """Küçük voksel insan (ayakta)."""
    x, y, z = V.x, V.y, V.z
    V.put(superell(x, y, cx, cy, 1.6 * h, 1.6 * h, 2.4) & (z >= z0) & (z < z0 + 6 * h), body)
    V.ball(cx, cy, z0 + 7.2 * h, 1.5 * h, head)
    if hat:
        V.put(superell(x, y, cx, cy, 1.8 * h, 1.8 * h, 2) & (z >= z0 + 8.2 * h) & (z < z0 + 9.4 * h), hat)
