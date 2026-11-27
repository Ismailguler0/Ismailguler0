"""EŞİK – Kız Kulesi'nin Yılanı (katman yığma / sprite stacking, iri 8-bit piksel, sabit palet)."""
import math, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/user/Ismailguler0/.claude/skills/sekiz-bit-aksam-video/scripts')
from pix8 import signature, captions

VOICE_DUR = 56.05
DUR, FPS = 58.6, 30
SIG_T = 56.2
A_, B_, C_, D_, E_, F_, G_, H_ = 0.0, 6.62, 13.9, 18.5, 23.1, 28.72, 39.7, 49.95
BUILD0, BUILD1 = 14.0, 16.2           # 16. saniye kancası: kule katman katman yükselir, 16.2'de patlar
MUSIC = dict(bpm=84, root=196.0)
CAPS = [(0.0, 3.0, "Denizin ortasında bir [kule]", 1608), (3.0, 6.6, "Bir [yılandan] saklanmak için!", 1608),
        (6.7, 9.95, "Efsaneye göre bir [kâhin]...", 1608), (10.0, 13.8, "[18 yaşında] yılan sokacak!", 1608),
        (14.0, 16.2, "Kral, kızını [karadan] kaçırır", 1608), (16.2, 18.5, "[DENİZİN ORTASINA] bir kule!", 1608),
        (18.6, 21.3, "Yiyecek sadece [kayıkla] gelir", 1608), (21.3, 23.1, "Ve [18.] doğum günü...", 1608),
        (23.2, 26.3, "Babasından bir sepet [üzüm]", 1608), (26.3, 28.7, "Dibinde bir [yılan]!", 1608),
        (28.72, 31.1, "Bir [efsane] daha var", 1608), (31.2, 33.7, "[Battal Gazi] prensesi kaçırır", 1608),
        (33.7, 36.1, "Atına atlar, [Üsküdar'a] sürer", 1608), (36.25, 39.6, "\"Atı alan [Üsküdar'ı] geçti\"", 1608),
        (39.78, 41.4, "Peki [gerçekte]?", 1608), (41.5, 45.1, "İlk kule: [12. yüzyıl], Bizans", 1608),
        (45.3, 47.6, "Yüzyıllarca [deniz feneri]", 1608), (47.6, 49.9, "Salgında [karantina evi]", 1608),
        (50.0, 51.9, "Ama yılan... hâlâ [bir sır]", 1608), (52.0, 55.1, "[Yılan mı?] [Battal Gazi mi?]", 1608),
        (55.1, 56.2, "[Yorumlara] yaz!", 1608)]
SFX = ([(0.0, 'boom'), (0.05, 'glare'), (B_, 'whoosh'), (10.0, 'bell'), (C_, 'whoosh'), (D_, 'whoosh'), (E_, 'whoosh'),
        (26.45, 'crash'), (F_, 'whoosh'), (G_, 'whoosh'), (41.5, 'chime'), (H_, 'rumble'), (BUILD1, 'boom'),
        (BUILD1 + 0.05, 'sparkle'), (SIG_T + 0.05, 'chime')]
       + [(BUILD0 + k * 0.2, 'tick') for k in range(11)]
       + [(29.0 + k * 0.42, 'tick') for k in range(25)])
CW, CH = 180, 320
SQ, ZS = 0.62, 0.85
OUTL = (12, 10, 24)
HZ = 92                                  # ufuk çizgisi (küçük tuval satırı)

PAL = np.array([
    (8, 8, 20), (16, 14, 36), (28, 24, 60), (44, 38, 92), (70, 58, 128), (110, 90, 160), (170, 120, 180),   # gece-mor
    (236, 120, 130), (252, 160, 120), (255, 204, 140), (255, 236, 180),                                    # akşam
    (14, 36, 70), (22, 58, 104), (36, 90, 140), (70, 136, 186), (140, 196, 226), (236, 246, 250),          # deniz
    (52, 48, 62), (86, 82, 98), (128, 124, 136), (176, 170, 172), (214, 206, 196), (240, 232, 218),       # taş
    (110, 112, 130), (150, 156, 176),                                                                      # kurşun kubbe
    (120, 46, 40), (186, 70, 52), (226, 60, 58),                                                           # kiremit/bayrak
    (24, 60, 34), (44, 104, 48), (90, 160, 64), (170, 214, 96),                                            # yılan
    (80, 30, 90), (130, 60, 150), (186, 110, 200),                                                         # üzüm
    (70, 44, 30), (112, 74, 46), (164, 116, 70), (206, 166, 110),                                          # ahşap
    (255, 70, 60), (255, 252, 236)], float)
_g = (np.arange(32) * 8 + 4).astype(float)
_cube = np.stack(np.meshgrid(_g, _g, _g, indexing='ij'), -1).reshape(-1, 3)
LUT = PAL.astype(np.uint8)[np.argmin(((_cube[:, None, :] - PAL[None]) ** 2).sum(-1), 1)].reshape(32, 32, 32, 3)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16
YY, XX = np.mgrid[0:CH, 0:CW]
BAY = BAYER[YY % 4, XX % 4]


def pal8(img):
    q = np.clip(img, 0, 255).astype(np.uint8) >> 3
    return LUT[q[..., 0], q[..., 1], q[..., 2]]


# ---------------------------------------------------------------- voksel modeller
def shade_bake(S, light=(-0.5, -0.6, 0.6)):
    occ = (S[..., 3] > 0).astype(np.float32); nz = S.shape[0]
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


def superell(x, y, cx, cy, rx, ry, p=4):
    return (np.abs((x - cx) / rx) ** p + np.abs((y - cy) / ry) ** p) <= 1


def tube(V, pts, rad, col, belly=None):
    """Noktalar boyunca yuvarlak kesitli boru (yılan gövdesi)."""
    for (px, py, pz) in pts:
        m = (V.x - px) ** 2 + (V.y - py) ** 2 + ((V.z - pz) * 1.1) ** 2 <= rad * rad
        V.put(m, col)
        if belly is not None:
            V.put(m & (V.z < pz - rad * 0.4), belly)


TCX, TCY = 41.0, 33.0                      # kule merkezi (model içinde)


def tower_model(snake=False):
    V = Vox(72, 72, 58); x, y, z = V.x, V.y, V.z
    ang = np.arctan2(y - 36, x - 36)
    rr = 31 + 2.5 * np.sin(ang * 3 + 1) + 1.5 * np.sin(ang * 7)
    rock = (np.hypot(x - 36, y - 36) <= rr - z * 1.2) & (z < 4)
    V.put(rock, (86, 82, 98)); V.put(rock & ((x.astype(int) * 7 + y.astype(int) * 3) % 11 == 0), (52, 48, 62))
    V.put(rock & (z >= 3), (128, 124, 136))
    plat = superell(x, y, 37, 36, 25, 22, 4) & (z >= 4) & (z < 6)
    V.put(plat, (214, 206, 196))
    wall = plat & ~superell(x, y, 37, 36, 23.6, 20.6, 4)
    V.put(superell(x, y, 37, 36, 25, 22, 4) & ~superell(x, y, 37, 36, 23.6, 20.6, 4) & (z >= 6) & (z < 8), (176, 170, 172))
    # ana yapı
    bld = superell(x, y, 29, 39, 13, 10, 6) & (z >= 6) & (z < 18)
    V.put(bld, (240, 232, 218))
    edge = bld & ~superell(x, y, 29, 39, 12, 9, 6)
    V.put(edge & (z >= 10) & (z < 14) & ((x.astype(int) + y.astype(int)) % 4 == 0), (36, 90, 140))
    V.put(superell(x, y, 29, 39, 13.6, 10.6, 6) & (z >= 18) & (z < 20), (186, 70, 52))
    V.put(superell(x, y, 29, 39, 9, 6, 6) & (z == 20), (120, 46, 40))
    # kule gövdesi
    rt = np.hypot(x - TCX, y - TCY); at = np.arctan2(y - TCY, x - TCX)
    body = superell(x, y, TCX, TCY, 6.5, 6.5, 2.6) & (z >= 6) & (z < 38)
    V.put(body, (240, 232, 218))
    shell = body & ~superell(x, y, TCX, TCY, 5.5, 5.5, 2.6)
    win = shell & (((z >= 30) & (z < 34)) | ((z >= 20) & (z < 23))) & (np.cos(at * 4) > 0.55)
    V.put(win, (28, 24, 60))
    V.put(superell(x, y, TCX, TCY, 8.2, 8.2, 2.6) & (z >= 36) & (z < 38), (176, 170, 172))   # balkon
    lant = superell(x, y, TCX, TCY, 5, 5, 2.4) & (z >= 38) & (z < 43)
    V.put(lant, (255, 204, 140)); V.put(lant & (np.cos(at * 4) > 0.8), (86, 82, 98))
    V.put(superell(x, y, TCX, TCY, 6, 6, 2.4) & (z == 43), (110, 112, 130))
    cone = (rt <= 5.6 * (1 - (z - 44) / 9)) & (z >= 44) & (z < 53)
    V.put(cone, (150, 156, 176)); V.put(cone & (x < TCX), (110, 112, 130))
    V.put((rt < 0.8) & (z >= 53) & (z < 58), (214, 206, 196))
    V.put((x > TCX + 0.5) & (x < TCX + 5) & (np.abs(y - TCY) < 0.6) & (z >= 54) & (z < 57), (226, 60, 58))
    if snake:
        pts = []
        for k in range(260):
            u = k / 259; a = u * 3.3 * 2 * math.pi
            pts.append((TCX + 8.6 * math.cos(a), TCY + 8.6 * math.sin(a), 8 + u * 27))
        tube(V, pts, 1.9, (44, 104, 48), (170, 214, 96))
        for k in range(0, 260, 9):
            px, py, pz = pts[k]; V.put((np.abs(x - px) < 1) & (np.abs(y - py) < 1) & (np.abs(z - pz - 1.6) < 0.7), (24, 60, 34))
        a = 3.3 * 2 * math.pi; hx, hy = TCX + 10.5 * math.cos(a), TCY + 10.5 * math.sin(a)
        tube(V, [(hx, hy, 36 + k * 0.5) for k in range(8)], 2.4, (44, 104, 48))
        V.put((x - hx) ** 2 + (y - hy - 2) ** 2 + (z - 40) ** 2 <= 9.5, (90, 160, 64))
        for s_ in (-1.6, 1.6):
            V.put((np.abs(x - hx - s_) < 0.8) & (np.abs(y - hy - 4) < 0.9) & (np.abs(z - 41) < 0.8), (255, 70, 60))
    return shade_bake(V.S)


def ball_model():
    V = Vox(40, 40, 36); x, y, z = V.x, V.y, V.z
    r = np.hypot(x - 19.5, y - 19.5)
    V.put((r <= 10 - z * 0.5) & (z < 6), (112, 74, 46)); V.put((r <= 11) & (z < 2), (70, 44, 30))
    V.put((r <= 7) & (z >= 6) & (z < 8), (206, 166, 110))
    sph = (x - 19.5) ** 2 + (y - 19.5) ** 2 + (z - 20) ** 2 <= 13 ** 2
    V.put(sph, (110, 90, 160)); V.put(sph & (z > 26) & (x < 18) & (y < 18), (186, 110, 200))
    V.put(sph & (z > 29) & (x < 15) & (y < 15), (255, 236, 180))
    return shade_bake(V.S)


def basket_model():
    V = Vox(40, 40, 22); x, y, z = V.x, V.y, V.z
    r = np.hypot(x - 19.5, y - 19.5); a = np.arctan2(y - 19.5, x - 19.5)
    bk = (r <= 12 + z * 0.25) & (r >= 10.5 + z * 0.25) & (z < 10) | ((r <= 12) & (z < 1))
    V.put(bk, (164, 116, 70)); V.put(bk & (((a * 6).astype(int) + z.astype(int)) % 2 == 0), (112, 74, 46))
    V.put((r <= 15) & (r >= 13.5) & (z >= 9) & (z < 10), (206, 166, 110))
    rng = np.random.default_rng(3)
    for _ in range(46):
        rr, aa = rng.uniform(0, 10), rng.uniform(0, 6.28); gx, gy = 19.5 + rr * math.cos(aa), 19.5 + rr * math.sin(aa)
        gz = 9 + (10 - rr) * 0.55 + rng.uniform(0, 2)
        g = (x - gx) ** 2 + (y - gy) ** 2 + (z - gz) ** 2 <= 4.4
        V.put(g, (130, 60, 150) if rng.random() < 0.6 else (186, 110, 200))
    V.put((np.abs(y - 19.5) < 0.8) & (np.abs(np.hypot(x - 19.5, z - 9) - 13) < 0.9) & (z >= 9), (112, 74, 46))
    return shade_bake(V.S)


def snakehead_model():
    V = Vox(24, 24, 30); x, y, z = V.x, V.y, V.z
    pts = [(12 + 3 * math.sin(k / 6), 12 + 1.5 * math.cos(k / 8), k * 0.5) for k in range(48)]
    tube(V, pts, 2.2, (44, 104, 48), (170, 214, 96))
    V.put((x - 12) ** 2 + ((y - 14) / 1.4) ** 2 + (z - 25) ** 2 <= 9, (90, 160, 64))
    for s_ in (-1.6, 1.6):
        V.put((np.abs(x - 12 - s_) < 0.8) & (np.abs(y - 16.5) < 0.9) & (np.abs(z - 26) < 0.8), (255, 70, 60))
    V.put((np.abs(x - 12) < 0.5) & (y > 18) & (y < 22) & (np.abs(z - 24) < 0.5), (226, 60, 58))
    return shade_bake(V.S)


def boat_model():
    V = Vox(40, 20, 16); x, y, z = V.x, V.y, V.z
    hull = superell(x, y, 19.5, 9.5, 18 - (3 - z) * 1.2, 7 - (3 - z) * 0.8, 2.2) & (z < 5)
    V.put(hull, (112, 74, 46)); V.put(hull & ~superell(x, y, 19.5, 9.5, 16, 5.5, 2.2) & (z == 4), (164, 116, 70))
    V.put(superell(x, y, 22, 9.5, 2.5, 3, 2) & (z >= 3) & (z < 9), (36, 90, 140))       # kayıkçı
    V.put((x - 22) ** 2 + (y - 9.5) ** 2 + (z - 10.5) ** 2 <= 3.5, (206, 166, 110))
    V.put((np.abs(x - 23) < 4) & (np.abs(y - 9.5) < 9) & (np.abs(z - 6) < 0.6) & (np.abs(x - 23 - (y - 9.5) * 0.1) < 0.7), (164, 116, 70))
    V.put((np.hypot(x - 12, y - 9.5) < 3) & (z >= 3) & (z < 6), (164, 116, 70))         # sepet
    V.put((np.hypot(x - 12, y - 9.5) < 2.4) & (z == 6), (130, 60, 150))
    return shade_bake(V.S)


def horse_model(frame, princess=True):
    V = Vox(54, 22, 44); x, y, z = V.x, V.y, V.z
    BR, DB = (112, 74, 46), (70, 44, 30)
    V.put(((x - 26) / 13) ** 2 + ((y - 11) / 5.5) ** 2 + ((z - 18) / 6) ** 2 <= 1, BR)        # gövde
    for k in range(10):                                                                          # boyun
        V.put((x - (37 + k * 0.9)) ** 2 + (y - 11) ** 2 + (z - (21 + k * 1.1)) ** 2 <= 9, BR)
    V.put(((x - 47) / 5) ** 2 + ((y - 11) / 2.6) ** 2 + ((z - 31) / 2.6) ** 2 <= 1, BR)         # baş
    V.put((np.abs(x - 41) < 4) & (np.abs(y - 11) < 1) & (z > 24) & (z < 33), DB)                # yele
    V.put((np.abs(x - 48) < 0.7) & (np.abs(y - 12.6) < 0.7) & (np.abs(z - 32) < 0.7), (8, 8, 20))
    sw = 4.5 if frame == 0 else -4.5
    for lx, ly, s in ((18, 8, 1), (18, 14, -1), (34, 8, -1), (34, 14, 1)):
        off = sw * s
        for zz in range(0, 14):
            fx = lx + off * (1 - zz / 14)
            V.put((np.abs(x - fx) < 1.4) & (np.abs(y - ly) < 1.2) & (z == zz), BR if zz > 2 else DB)
    for k in range(9):                                                                           # kuyruk
        V.put((x - (12 - k * 0.8)) ** 2 + (y - 11) ** 2 + (z - (20 - k * 1.0)) ** 2 <= 2.5, DB)
    # süvari
    V.put(superell(x, y, 27, 11, 4, 4.5, 2.5) & (z >= 22) & (z < 33), (44, 104, 48))
    V.put((x - 27) ** 2 + (y - 11) ** 2 + (z - 35.5) ** 2 <= 7, (206, 166, 110))
    V.put((x - 27) ** 2 + (y - 11) ** 2 + ((z - 38.5) * 1.3) ** 2 <= 9, (240, 232, 218))      # sarık
    V.put(((x - 22) / 3) ** 2 + ((y - 11) / 5) ** 2 + ((z - 27) / 6) ** 2 <= 1, (186, 70, 52))  # pelerin
    if princess:                                                                                 # arkasında prenses
        V.put(superell(x, y, 20, 11, 3.4, 4.2, 2.2) & (z >= 21) & (z < 30), (236, 120, 130))
        V.put(superell(x, y, 20, 11, 4.2, 5.2, 2.2) & (z >= 20) & (z < 23), (236, 120, 130))
        V.put((x - 20) ** 2 + (y - 11) ** 2 + (z - 32) ** 2 <= 5, (206, 166, 110))
        V.put(((x - 19) ** 2 + (y - 11) ** 2 + ((z - 33) * 0.8) ** 2 <= 7) & (x < 20.5), (255, 204, 140))
        V.put((np.abs(x - 19) < 1.6) & (np.abs(y - 11) < 2.6) & (z >= 33) & (z < 36), (240, 232, 218))
    for k in range(12):                                                                          # kılıç
        V.put((np.abs(x - (30 + k * 0.5)) < 0.7) & (np.abs(y - 15) < 0.7) & (np.abs(z - (32 + k)) < 0.7), (214, 206, 196))
    return shade_bake(V.S)


def house_model(w, d, h, wall, seed):
    V = Vox(w + 2, d + 2, h + 8); x, y, z = V.x, V.y, V.z
    b = (x >= 1) & (x <= w) & (y >= 1) & (y <= d) & (z < h)
    V.put(b, wall)
    rng = np.random.default_rng(seed)
    lit = rng.random((h, d + 2, w + 2)) < 0.5
    edge = b & ((x == 1) | (x == w) | (y == 1) | (y == d)) & (z.astype(int) % 4 == 2) & (((x + y).astype(int)) % 3 == 0)
    V.put(edge & lit[np.clip(z.astype(int), 0, h - 1), y.astype(int), x.astype(int)], (255, 204, 140))
    V.put(edge & ~lit[np.clip(z.astype(int), 0, h - 1), y.astype(int), x.astype(int)], (28, 24, 60))
    roof = (z >= h) & (np.abs(y - (d + 1) / 2) <= (d + 1) / 2 - (z - h) * 1.0) & (x >= 0) & (x <= w + 1)
    V.put(roof & (z < h + 6), (186, 70, 52))
    return shade_bake(V.S)


def mosque_model():
    V = Vox(44, 30, 50); x, y, z = V.x, V.y, V.z
    V.put(superell(x, y, 22, 15, 11, 10, 6) & (z < 10), (214, 206, 196))
    V.put((x - 22) ** 2 + (y - 15) ** 2 + ((z - 10) * 1.0) ** 2 <= 81, (150, 156, 176))
    V.put((np.hypot(x - 22, y - 15) < 0.8) & (z >= 18) & (z < 22), (255, 204, 140))
    for mx in (5, 39):
        V.put((np.hypot(x - mx, y - 15) < 2) & (z < 36), (240, 232, 218))
        V.put((np.hypot(x - mx, y - 15) < 3) & (z >= 28) & (z < 29), (176, 170, 172))
        V.put((np.hypot(x - mx, y - 15) < 2 * (1 - (z - 36) / 9)) & (z >= 36) & (z < 45), (150, 156, 176))
    return shade_bake(V.S)


def bg_boat_model():
    V = Vox(40, 20, 18); x, y, z = V.x, V.y, V.z
    hull = superell(x, y, 19.5, 9.5, 18 - (3 - z) * 1.2, 7 - (3 - z) * 0.8, 2.2) & (z < 5)
    V.put(hull, (112, 74, 46)); V.put(hull & ~superell(x, y, 19.5, 9.5, 16, 5.5, 2.2) & (z == 4), (164, 116, 70))
    V.put(superell(x, y, 24, 9.5, 2.8, 3.2, 2) & (z >= 3) & (z < 10), (44, 104, 48))
    V.put(((x - 26) / 2) ** 2 + ((y - 9.5) / 3.5) ** 2 + ((z - 7) / 3) ** 2 <= 1, (186, 70, 52))
    V.put((x - 24) ** 2 + (y - 9.5) ** 2 + (z - 11.5) ** 2 <= 3.5, (206, 166, 110))
    V.put((x - 24) ** 2 + (y - 9.5) ** 2 + ((z - 13.5) * 1.3) ** 2 <= 5, (240, 232, 218))
    V.put((np.abs(x - 22) < 4) & (np.abs(y - 9.5) < 9) & (np.abs(z - 6) < 0.6) & (np.abs(x - 22 - (y - 9.5) * 0.1) < 0.7), (164, 116, 70))
    V.put(superell(x, y, 12, 9.5, 3, 3.6, 2) & (z >= 3) & (z < 9), (236, 120, 130))
    V.put((x - 12) ** 2 + (y - 9.5) ** 2 + (z - 10.5) ** 2 <= 3.5, (206, 166, 110))
    V.put(((x - 11) ** 2 + (y - 9.5) ** 2 + ((z - 11.5) * 0.8) ** 2 <= 5) & (x < 12.5), (255, 204, 140))
    V.put((np.abs(x - 11) < 1.4) & (np.abs(y - 9.5) < 2.2) & (z >= 12) & (z < 14), (240, 232, 218))
    return shade_bake(V.S)


TOWER, TOWER_SN, BALL, BASKET, SNHEAD, BOAT = tower_model(), tower_model(True), ball_model(), basket_model(), snakehead_model(), boat_model()
HORSE = [horse_model(0), horse_model(1)]
_hr = np.random.default_rng(9)
HOUSES = [house_model(int(_hr.integers(10, 16)), int(_hr.integers(9, 13)), int(_hr.integers(8, 16)),
                      [(240, 232, 218), (252, 160, 120), (214, 206, 196), (255, 204, 140)][i % 4], i) for i in range(6)]
MOSQUE = mosque_model()
BGBOAT = bg_boat_model()
COBBLE = np.zeros((24, 24, 3), np.uint8); COBBLE[:] = (86, 82, 98)
for _j in range(0, 24, 6):
    COBBLE[_j, :] = (52, 48, 62)
    for _i in range((_j // 6 % 2) * 4, 24, 8):
        COBBLE[_j:_j + 6, _i] = (52, 48, 62); COBBLE[_j + 2, (_i + 3) % 24] = (128, 124, 136)


# ---------------------------------------------------------------- çizim
def draw_stack(img, obj, S, wx, wy, own, cam, K=1.0, zoff=0.0, zmax=None, zmin_screen=None):
    ccx, ccy, th, sx0, sy0 = cam
    nz, ny, nx = S.shape[:3]
    dx, dy = wx - ccx, wy - ccy; c0, s0 = math.cos(-th), math.sin(-th)
    rx, ry = dx * c0 - dy * s0, dx * s0 + dy * c0
    px, py = sx0 + rx * K, sy0 + ry * K * SQ
    phi = own - th; c, s = math.cos(phi), math.sin(phi)
    A = np.array([[K * c, -K * s, 0], [K * s * SQ, K * c * SQ, 0]], np.float64)
    R = math.hypot(nx, ny) * K / 2 + 2
    top = nz * K * ZS + abs(zoff) * K * ZS
    if px + R < 0 or px - R > CW or py + R < -top or py - R - top > CH:
        return
    x0, y0 = int(px - R) - 1, int(py - R - top) - 1
    w, h = int(2 * R) + 3, int(2 * R + top) + 3
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
        img[ya:yb, xa:xb][m] = o[..., :3][m]; obj[ya:yb, xa:xb][m] = True


def to_screen(wx, wy, cam, K):
    ccx, ccy, th, sx0, sy0 = cam
    dx, dy = wx - ccx, wy - ccy; c0, s0 = math.cos(-th), math.sin(-th)
    return sx0 + (dx * c0 - dy * s0) * K, sy0 + (dx * s0 + dy * c0) * K * SQ


def add_outline(img, obj):
    d = cv2.dilate(obj.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    img[d & ~obj] = OUTL


def glow(img, x, y, r, col=(255, 210, 130), a=0.35):
    d = np.hypot(XX - x, (YY - y) / 0.8) / max(1, r)
    m = (d < 1) & (BAY < (1 - d) * 0.9)
    img[m] = (img[m] * (1 - a) + np.array(col) * a).astype(np.uint8)


# deniz dokusu (döşenebilir)
def make_sea(night):
    T = 96; tile = np.zeros((T, T, 3), np.float32)
    yy, xx = np.mgrid[0:T, 0:T]
    base = np.array((14, 36, 70) if night else (22, 58, 104), np.float32)
    tile[:] = base
    w = np.sin(xx / T * 2 * np.pi * 3 + np.sin(yy / T * 2 * np.pi * 2) * 1.5) * np.cos(yy / T * 2 * np.pi * 4)
    b = BAYER[yy % 4, xx % 4]
    tile[(w > 0.35) & (b < 0.5)] = (22, 58, 104) if night else (36, 90, 140)
    tile[(w > 0.75) & (b < 0.6)] = (36, 90, 140) if night else (70, 136, 186)
    return tile.astype(np.uint8)


SEA_D, SEA_N = make_sea(False), make_sea(True)


def draw_sea(img, cam, K, t, night=False, flow=(0.0, 6.0)):
    ccx, ccy, th, sx0, sy0 = cam
    c, s = math.cos(-th), math.sin(-th)
    A = np.array([[K * c, -K * s, 0], [K * s * SQ, K * c * SQ, 0]], np.float64)
    ox, oy = ccx - flow[0] * t, ccy - flow[1] * t
    A[0, 2] = sx0 - (A[0, 0] * ox + A[0, 1] * oy); A[1, 2] = sy0 - (A[1, 0] * ox + A[1, 1] * oy)
    sea = cv2.warpAffine(SEA_N if night else SEA_D, A, (CW, CH), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_WRAP)
    img[HZ:] = sea[HZ:]
    # ufka doğru sis
    k = np.clip(1 - (np.arange(CH) - HZ) / 40, 0, 1)[:, None]
    fogm = (BAY < k * 0.8) & (YY >= HZ)
    img[fogm] = (70, 58, 128) if night else (236, 120, 130)


_sr = np.random.default_rng(4)
STARS = [(_sr.uniform(0, CW), _sr.uniform(0, HZ - 10), _sr.random()) for _ in range(60)]
SKY_D = [(44, 38, 92), (110, 90, 160), (236, 120, 130), (252, 160, 120), (255, 204, 140)]
SKY_N = [(8, 8, 20), (16, 14, 36), (28, 24, 60), (44, 38, 92), (70, 58, 128)]


SW = 400                                   # silüet şeridi genişliği (dönerek kayar)


def build_skyline(seed, hmax, n_mosque, base_off):
    """Tarihî İstanbul silüeti: alçak evler, kubbeli camiler, minareler, serviler. Maske + ışık noktaları."""
    rng = np.random.default_rng(seed)
    M = np.zeros((40, SW), bool); H = 40; lights = []; chim = []
    x = 0
    while x < SW:                                                    # alçak ahşap evler (çatılı)
        w = int(rng.integers(4, 9)); h = int(rng.integers(2, hmax))
        M[H - h:H, x:x + w] = True
        for k in range(w // 2 + 1):                                  # kırma çatı
            M[H - h - k - 1, x + k:x + w - k] = True if k < 2 else M[H - h - k - 1, x + k:x + w - k]
        if rng.random() < 0.35:
            lights.append((x + int(rng.integers(1, max(2, w - 1))), H - int(rng.integers(1, max(2, h))), rng.random() * 6))
        if rng.random() < 0.15:
            chim.append((x + w // 2, H - h - 3, rng.random() * 6))
        x += w + int(rng.integers(0, 2))
    for k in range(int(SW / 12)):                                    # serviler
        cx = int(rng.integers(0, SW)); ch = int(rng.integers(6, 12))
        for yy in range(ch):
            r = int((yy / ch) * 1.6 + 0.4)
            M[H - yy - 1 - base_off, max(0, cx - r):cx + r + 1] = True if yy < ch else False
        M[H - base_off:H, cx] = True
    for k in range(n_mosque):                                        # camiler
        cx = int((k + 0.5) * SW / n_mosque + rng.integers(-15, 15)); r = int(rng.integers(5, 9))
        base = H - int(rng.integers(5, 8))
        M[base:H, cx - r - 3:cx + r + 4] = True
        yy, xx = np.mgrid[0:H, 0:SW]
        M |= ((xx - cx) ** 2 + ((yy - base) * 1.15) ** 2 <= r * r) & (yy <= base)
        M[base - r - 3:base - r, cx] = True                         # alem
        for s_ in (-1, 1) if rng.random() < 0.7 else (-1, 1, -2, 2):
            mx = cx + s_ * (r + 5); mh = int(rng.integers(16, 24))
            M[H - mh:H, mx] = True; M[H - mh - 3:H - mh, mx] = True
            M[H - mh + 4, mx - 1:mx + 2] = True                      # şerefe
            lights.append((mx, H - mh + 4, rng.random() * 6))        # mahya/kandil
        for s_ in (-1, 1):                                           # yarım kubbeler
            M |= ((xx - (cx + s_ * r)) ** 2 + ((yy - base - 2) * 1.3) ** 2 <= (r * 0.6) ** 2) & (yy <= base + 2)
    return M, lights, chim


SKY_FAR = build_skyline(21, 5, 3, 0)
SKY_NEAR = build_skyline(12, 8, 4, 0)
_bird = np.random.default_rng(8)
GULLS = [(_bird.uniform(0, 300), _bird.uniform(20, 70), _bird.uniform(6, 14), _bird.random() * 6) for _ in range(5)]


def draw_sky(img, t, night=False, shift=0.0):
    stops = SKY_N if night else SKY_D
    for y in range(HZ):
        u = y / HZ * (len(stops) - 1); i = min(len(stops) - 2, int(u)); f = u - i
        lvl = BAYER[y % 4, np.arange(CW) % 4] < f
        img[y] = np.where(lvl[:, None], stops[i + 1], stops[i])
    for x, y, d in STARS:
        if y < HZ * (0.9 if night else 0.35) and math.sin(t * (1 + d * 3) + x) > -0.3:
            img[int(y), int(x)] = (255, 236, 180) if d > 0.6 else (170, 120, 180)
    if not night:
        cv2.circle(img, (142, HZ - 8), 11, (255, 236, 180), -1)
    else:
        cv2.circle(img, (40, 30), 8, (255, 236, 180), -1); cv2.circle(img, (44, 27), 7, tuple(int(c) for c in img[12, 2]), -1)
    # yelkenli kadırga ufukta süzülür
    sx = int((t * 3 + shift * 0.6) % (CW + 40)) - 20
    hc = (44, 38, 92) if night else (110, 90, 160)
    img[HZ - 3:HZ, max(0, sx - 6):max(0, sx + 6)] = hc
    for k in range(8):
        w = 4 - abs(k - 4) // 2
        img[HZ - 4 - k, max(0, sx - w):max(0, sx + w + 1)] = (196, 170, 200) if not night else (90, 80, 130)
    # iki katmanlı tarihî silüet (kamera dönünce kayar = derinlik)
    for (M, lights, chim), par, col in ((SKY_FAR, 0.5, (70, 58, 128) if night else (170, 120, 180)),
                                       (SKY_NEAR, 1.0, (28, 24, 60) if night else (70, 58, 128))):
        off = int(shift * 30 * par) % SW
        Mr = np.roll(M, -off, axis=1)[:, :CW]
        reg = img[HZ - 40:HZ]
        reg[Mr] = col
        for (lx, ly, ph) in lights:                                  # kandil ışıkları: seyrek, sıcak, titrek
            X = (lx - off) % SW
            if X < CW and (night or par == 1.0):
                if math.sin(t * 3 + ph * 7) > (-0.6 if night else 0.4):
                    reg[ly, X] = (255, 204, 140) if math.sin(t * 9 + ph) > -0.2 else (252, 160, 120)
        if par == 1.0:
            for (cx, cy, ph) in chim:                                # baca dumanı
                X = (cx - off) % SW
                for k in range(5):
                    a = (t * 0.4 + k / 5 + ph) % 1
                    xx, yy = int(X + 3 * a + math.sin(a * 6 + ph)), int(cy - a * 10)
                    if 0 <= xx < CW and 0 <= yy < 40:
                        reg[yy, xx] = (110, 90, 160) if night else (236, 206, 200)
    if not night:                                                    # martılar
        for (gx, gy, sp, ph) in GULLS:
            X = int((gx + t * sp) % 300) - 60; Y = int(gy + 3 * math.sin(t + ph))
            wing = 1 if math.sin(t * 8 + ph) > 0 else 0
            if 2 <= X < CW - 3 and 2 <= Y < HZ:
                img[Y, X] = (44, 38, 92); img[Y - wing, X - 1] = img[Y - wing, X + 1] = (44, 38, 92)
                img[Y - wing - 1 + (1 - wing), X - 2] = img[Y - wing - 1 + (1 - wing), X + 2] = (44, 38, 92)


def foam_ring(img, cam, K, t, cx=0.0, cy=0.0, R=31.0, n=90):
    for i in range(n):
        a = i / n * 2 * math.pi
        rr = R + 1.5 * math.sin(a * 5 + t * 3) + 1.0 * math.sin(a * 3 - t * 2)
        X, Y = to_screen(cx + rr * math.cos(a), cy + rr * math.sin(a), cam, K)
        if 0 <= X < CW - 1 and HZ <= Y < CH - 1 and (math.sin(a * 11 + t * 6) > -0.2):
            img[int(Y), int(X)] = (236, 246, 250)
            if math.sin(a * 7 - t * 4) > 0.5:
                img[int(Y), int(X) + 1] = (140, 196, 226)


def shadow(img, cam, K, wx, wy, r):
    X, Y = to_screen(wx, wy, cam, K)
    m = np.zeros((CH, CW), np.uint8)
    cv2.ellipse(m, (int(X + 3), int(Y + 2)), (int(r * K), int(r * K * SQ)), 0, 0, 360, 1, -1)
    img[m > 0] = (img[m > 0] * 0.65).astype(np.uint8)


def tower_scene(t, cam, K, model, night=False, zmax=None, flow=(0, 5)):
    img = np.zeros((CH, CW, 3), np.uint8)
    draw_sky(img, t, night, cam[2]); draw_sea(img, cam, K, t, night, flow)
    shadow(img, cam, K, 0, 0, 30)
    foam_ring(img, cam, K, t)
    obj = np.zeros((CH, CW), bool)
    draw_stack(img, obj, model, 0, 0, 0, cam, K, zmax=zmax)
    add_outline(img, obj)
    return img, obj


def lantern_xy(cam, K):
    X, Y = to_screen(TCX - 35.5, TCY - 35.5, cam, K)
    return X, Y - 40 * K * ZS


def eye_xy(cam, K):
    a = 3.3 * 2 * math.pi; hx, hy = TCX + 10.5 * math.cos(a) - 35.5, TCY + 10.5 * math.sin(a) + 3 - 35.5
    X, Y = to_screen(hx, hy, cam, K)
    return X, Y - 41 * K * ZS


def press_text(img, txt, cx, cy, size, col):
    f = ImageFont.truetype('/home/user/esik-araclar/fontlar/node_modules/@expo-google-fonts/press-start-2p/400Regular/PressStart2P_400Regular.ttf', size)
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    w = d.textlength(txt, font=f)
    d.text((cx - w / 2 + 1, cy - size / 2 + 1), txt, font=f, fill=OUTL)
    d.text((cx - w / 2, cy - size / 2), txt, font=f, fill=col)
    img[:] = np.array(im)


# ---------------------------------------------------------------- sahneler
def sA(t):                          # kanca: yılanın sardığı kule
    K = 2.15 - 0.1 * t / 6.6
    cam = (0, 4, 0.6 + t * 0.32, CW / 2, 228)
    img, _ = tower_scene(t, cam, K, TOWER_SN)
    ex, ey = eye_xy(cam, K)
    glow(img, ex, ey, 9 + 2 * math.sin(t * 8), (255, 70, 60), 0.4)
    if t < 0.28:                     # ilk anda kırmızı flaş
        img[:] = (img * 0.4 + np.array((255, 70, 60)) * 0.6).astype(np.uint8)
    return img


def sB(t):                          # kâhin ve kristal küre
    tl = t - B_
    img = np.zeros((CH, CW, 3), np.uint8)
    for y in range(CH):
        k = y / CH; img[y] = (np.array((16, 14, 36)) * (1 - k) + np.array((44, 38, 92)) * k)
    img[:] = np.clip(img + (BAY[..., None] - 0.5) * 18, 0, 255).astype(np.uint8)
    # masa örtüsü
    cv2.ellipse(img, (90, 236), (80, 40), 0, 0, 360, (80, 30, 90), -1)
    cv2.ellipse(img, (90, 236), (80, 40), 0, 0, 360, (130, 60, 150), 1)
    for cx_, ph in ((22, 0), (158, 1.7)):                      # mumlar
        cv2.rectangle(img, (cx_ - 2, 196), (cx_ + 2, 214), (240, 232, 218), -1)
        fl = int(2 * math.sin(t * 13 + ph))
        cv2.ellipse(img, (cx_, 192 + fl // 2), (2, 4), 0, 0, 360, (255, 204, 140), -1)
        glow(img, cx_, 192, 22, (255, 204, 140), 0.25)
    cam = (0, 0, tl * 0.5, 90, 238)
    obj = np.zeros((CH, CW), bool)
    draw_stack(img, obj, BALL, 0, 0, 0, cam, 3.0)
    add_outline(img, obj)
    by = 238 - 20 * 3.0 * ZS
    glow(img, 90, by, 40, (186, 110, 200), 0.3)
    for k in range(14):                                         # küre içinde dönen duman
        a = t * 1.6 + k * 0.45; r_ = 8 + 18 * ((k * 0.37 + t * 0.2) % 1)
        X, Y = int(90 + r_ * math.cos(a)), int(by + r_ * 0.8 * math.sin(a))
        img[Y:Y + 2, X:X + 2] = (236, 246, 250) if k % 3 == 0 else (186, 110, 200)
    if t >= 10.0:
        k = min(1.0, (t - 10.0) / 0.25)
        press_text(img, "18", 90, by, int(16 + 10 * k), (255, 70, 60) if int(t * 4) % 2 == 0 else (255, 236, 180))
    if 10.0 <= t < 10.2:
        img[:] = (img * 0.5 + 120).astype(np.uint8)
    return img


def sC(t):                          # 16. SANİYE KANCASI: kule katman katman yükselir
    tl = t - C_
    u = np.clip((t - BUILD0) / (BUILD1 - BUILD0), 0, 1)
    zmax = int(4 + 54 * (u ** 1.3)) if t < BUILD1 else None
    K = 2.6 - 0.6 * min(1.0, max(0.0, t - BUILD1) / 1.2)
    cam = (0, 6, 2.1 + tl * 0.35, CW / 2, 238)
    if t >= BUILD1 and t < BUILD1 + 0.35:
        sh = int(5 * (1 - (t - BUILD1) / 0.35)) * (1 if int(t * 40) % 2 else -1)
        cam = (sh * 0.5, 6, cam[2], CW / 2 + sh, 238)
    img, obj = tower_scene(t, cam, K, TOWER, zmax=zmax)
    if t < BUILD1 and zmax is not None:                         # yeni katmanın parıltısı
        X, Y = to_screen(5, -2, cam, K)
        ly = int(Y - zmax * K * ZS)
        for xx_ in range(int(X - 18), int(X + 18), 3):
            if 0 <= xx_ < CW and 0 <= ly < CH and (xx_ + int(t * 30)) % 6 < 3:
                img[ly, xx_] = (255, 236, 180)
    if BUILD1 <= t < BUILD1 + 0.45:                              # patlama: beyaz flaş + halka
        k = (t - BUILD1) / 0.45
        img[:] = (img * k + np.array((255, 252, 236)) * (1 - k)).astype(np.uint8)
        X, Y = lantern_xy(cam, K)
        cv2.circle(img, (int(X), int(Y)), int(10 + 120 * k), (255, 204, 140), 2)
    if t >= BUILD1:
        X, Y = lantern_xy(cam, K); glow(img, X, Y, 18, (255, 204, 140), 0.35)
    return img


def sD(t):                          # kayık kuleye gidiyor
    tl = t - D_; K = 1.35
    cam = (0, 30, 0.35, CW / 2, 170)
    img = np.zeros((CH, CW, 3), np.uint8)
    draw_sky(img, t, False, cam[2]); draw_sea(img, cam, K, t)
    shadow(img, cam, K, 0, 0, 30); foam_ring(img, cam, K, t)
    by = 120 - tl * 14
    shadow(img, cam, K, 0, by, 16)
    items = sorted([(to_screen(0, 0, cam, K)[1], 'T'), (to_screen(4, by, cam, K)[1], 'B')])
    obj = np.zeros((CH, CW), bool)
    for _, w in items:
        if w == 'T':
            draw_stack(img, obj, TOWER, 0, 0, 0, cam, K)
        else:
            draw_stack(img, obj, BOAT, 4, by, -math.pi / 2, cam, K, zoff=0.6 * math.sin(t * 3))
    add_outline(img, obj)
    for k in range(10):                                         # kayık izi
        X, Y = to_screen(4 + (k % 2 * 2 - 1) * (3 + k), by + 16 + k * 4, cam, K)
        if HZ <= Y < CH and 0 <= X < CW and (k + int(t * 8)) % 3:
            img[int(Y), int(X)] = (236, 246, 250)
    if t > 21.3:
        X, Y = lantern_xy(cam, K); glow(img, X, Y, 14, (255, 204, 140), 0.3)
        press_text(img, "18", int(X), int(Y - 26), 14, (255, 236, 180))
    return img


def sE(t):                          # üzüm sepeti ve yılan
    tl = t - E_
    img = np.zeros((CH, CW, 3), np.uint8)
    for y in range(CH):
        k = y / CH; img[y] = (np.array((44, 38, 92)) * (1 - k) + np.array((112, 74, 46)) * k)
    img[:] = np.clip(img + (BAY[..., None] - 0.5) * 22, 0, 255).astype(np.uint8)
    cv2.ellipse(img, (90, 246), (86, 44), 0, 0, 360, (164, 116, 70), -1)        # ahşap masa
    for k in range(-80, 90, 14):
        cv2.line(img, (90 + k, 206), (90 + int(k * 1.2), 290), (112, 74, 46), 1)
    cam = (0, 0, 0.4 + tl * 0.45, 90, 250)
    K = 3.1
    obj = np.zeros((CH, CW), bool)
    sh = np.zeros((CH, CW), np.uint8); cv2.ellipse(sh, (94, 254), (52, 30), 0, 0, 360, 1, -1)
    img[sh > 0] = (img[sh > 0] * 0.65).astype(np.uint8)
    draw_stack(img, obj, BASKET, 0, 0, 0, cam, K)
    rise = np.clip((t - 26.4) / 0.9, 0, 1)
    if rise > 0:
        draw_stack(img, obj, SNHEAD, 0, 2, math.pi * 0.15 + 0.3 * math.sin(t * 5), cam, K,
                   zoff=-24 + 30 * (1 - (1 - rise) ** 3), zmin_screen=10)
    add_outline(img, obj)
    if rise > 0:
        ey = 250 - (6 + 30 * (1 - (1 - rise) ** 3)) * K * ZS - 0
        glow(img, 90, ey - 14, 16, (255, 70, 60), 0.3)
    if 26.45 <= t < 26.75:
        img[:] = (img * 0.45 + np.array((255, 70, 60)) * 0.55).astype(np.uint8)
    return img


SHORE = 160.0
F_LAND = 33.7                       # kıyıya çıkış: ata binip Üsküdar sokaklarında dörtnala


def sF(t):
    if t < F_LAND:                                               # kayıkla kuleden kıyıya
        tl = t - F_; L = F_LAND - F_
        by = 34 + (SHORE - 46) * (tl / L)
        K = 1.6
        cam = (0, by + 22, math.pi / 2, CW / 2, 205)
        img = np.zeros((CH, CW, 3), np.uint8)
        draw_sky(img, t, True, cam[2] + by * 0.004); draw_sea(img, cam, K, t, night=True, flow=(1.5, 0))
        sx_, _ = to_screen(0, SHORE, cam, K)
        if sx_ < CW:
            x0 = max(0, int(sx_))
            img[HZ:, x0:] = (86, 82, 98); img[HZ:, x0:x0 + 2] = (236, 246, 250)
        items = []
        shadow(img, cam, K, 0, 0, 30); foam_ring(img, cam, K, t)
        items.append((to_screen(0, 0, cam, K)[1], TOWER, 0, 0, 0, 0))
        for i, H in enumerate(HOUSES):
            hx = -46 + (i % 3) * 30; hy = SHORE + 22 + (i // 3) * 26
            items.append((to_screen(hx, hy, cam, K)[1], H, hx, hy, math.pi / 2, 0))
        shadow(img, cam, K, 4, by, 12)
        items.append((to_screen(4, by, cam, K)[1] + 0.5, BGBOAT, 4, by, math.pi / 2, 0.6 * math.sin(t * 3)))
        items.sort(key=lambda it: it[0])
        obj = np.zeros((CH, CW), bool)
        for _, S, wx, wy, own, zo in items:
            draw_stack(img, obj, S, wx, wy, own, cam, K, zoff=zo)
        add_outline(img, obj)
        for k in range(12):                                      # kayık izi
            X, Y = to_screen(4 + (k % 2 * 2 - 1) * (3 + k * 0.6), by - 18 - k * 3, cam, K)
            if HZ <= Y < CH and 0 <= X < CW and (k + int(t * 8)) % 3:
                img[int(Y), int(X)] = (236, 246, 250)
        X, Y = lantern_xy(cam, K); glow(img, X, Y, 14, (255, 204, 140), 0.3)
        return img
    tl = t - F_LAND                                              # Üsküdar sokakları
    ry = 10 + 34 * tl
    K = 1.7
    cam = (0, ry + 8, math.pi / 2, CW / 2, 210)
    img = np.zeros((CH, CW, 3), np.uint8)
    draw_sky(img, t, True, cam[2] + ry * 0.004)
    ccx, ccy, th, sx0, sy0 = cam
    A = np.array([[K * math.cos(-th), -K * math.sin(-th), 0], [K * math.sin(-th) * SQ, K * math.cos(-th) * SQ, 0]])
    A[0, 2] = sx0 - (A[0, 0] * ccx + A[0, 1] * ccy); A[1, 2] = sy0 - (A[1, 0] * ccx + A[1, 1] * ccy)
    gr = cv2.warpAffine(COBBLE, A, (CW, CH), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_WRAP)
    img[HZ:] = gr[HZ:]
    fog_k = np.clip(1 - (np.arange(CH) - HZ) / 30, 0, 1)[:, None]
    img[(BAY < fog_k * 0.8) & (YY >= HZ)] = (44, 38, 92)
    items = []
    base = int(ry // 40) * 40
    for j in range(-3, 6):                                       # sokağın iki yanında evler, arada cami
        yy_ = base + j * 40
        for side, hx in ((0, -36), (1, 34)):
            H = HOUSES[(j * 2 + side) % len(HOUSES)]
            items.append((to_screen(hx, yy_ + side * 14, cam, K)[1], H, hx, yy_ + side * 14, math.pi / 2, 0))
        if j % 3 == 0:
            items.append((to_screen(74, yy_ + 20, cam, K)[1], MOSQUE, 74, yy_ + 20, math.pi / 2, 0))
    gal = int(t * 7) % 2
    items.append((to_screen(4, ry, cam, K)[1] + 0.5, HORSE[gal], 4, ry, math.pi / 2, abs(math.sin(t * 7 * math.pi)) * 2.5))
    items.sort(key=lambda it: it[0])
    obj = np.zeros((CH, CW), bool)
    for _, S, wx, wy, own, zo in items:
        if S is HORSE[gal]:
            shadow(img, cam, K, 4, ry, 12)
        draw_stack(img, obj, S, wx, wy, own, cam, K, zoff=zo)
    add_outline(img, obj)
    for j in range(-3, 6):                                       # kandil fenerleri
        X, Y = to_screen(22, base + j * 40 + 26, cam, K); Y -= 18 * K * ZS
        if -20 < X < CW + 20:
            glow(img, X, Y, 16, (255, 204, 140), 0.3)
            if 0 <= int(X) < CW and 0 <= int(Y) < CH:
                img[int(Y), int(X)] = (255, 236, 180)
    X, Y = to_screen(4, ry, cam, K)
    for k in range(10):                                          # toz
        a = (t * 3 + k / 10) % 1
        px_, py_ = int(X - 22 - 26 * a + (k % 3) * 3), int(Y + 2 - 10 * a * (1 - a) * 3)
        if 0 <= px_ < CW - 1 and HZ <= py_ < CH - 1:
            img[py_, px_:px_ + 2] = (128, 124, 136) if a < 0.5 else (86, 82, 98)
    return img


def sG(t):                          # tarih: fener ışığı döner
    tl = t - G_; K = 1.75
    cam = (0, 4, 1.0 + tl * 0.18, CW / 2, 220)
    img, _ = tower_scene(t, cam, K, TOWER, night=True, flow=(0, 3))
    X, Y = lantern_xy(cam, K)
    a = t * 1.3
    ov = np.zeros((CH, CW), np.uint8)
    p = [(X, Y), (X + 230 * math.cos(a - 0.12), Y + 120 * math.sin(a - 0.12)), (X + 230 * math.cos(a + 0.12), Y + 120 * math.sin(a + 0.12))]
    cv2.fillPoly(ov, [np.array(p, np.int32)], 1)
    m = (ov > 0) & (BAY < 0.45)
    img[m] = (img[m] * 0.4 + np.array((255, 236, 180)) * 0.6).astype(np.uint8)
    glow(img, X, Y, 22, (255, 236, 180), 0.45)
    if t >= 47.6:                                               # karantina: sarı bayrak
        fx, fy = int(X + 2), int(Y - 30 * K * ZS * 0.25)
        img[fy - 2:fy + 3, fx + 3:fx + 10] = (255, 204, 140) if int(t * 3) % 2 else (252, 160, 120)
    return img


def sH(t):                          # final: gecede yılanlı kule, kırmızı gözler
    tl = t - H_; K = 2.0 + 0.25 * min(1.0, tl / 6)
    cam = (0, 4, 4.0 + tl * 0.25, CW / 2, 232)
    img, _ = tower_scene(t, cam, K, TOWER_SN, night=True, flow=(0, 3))
    img[:] = (img * 0.82).astype(np.uint8)
    ex, ey = eye_xy(cam, K)
    glow(img, ex, ey, 12, (255, 70, 60), 0.45)
    X, Y = lantern_xy(cam, K); glow(img, X, Y, 16, (255, 204, 140), 0.3)
    return img


def frame_at(t):
    if t < B_:
        img = sA(t)
    elif t < C_:
        img = sB(t)
    elif t < D_:
        img = sC(t)
    elif t < E_:
        img = sD(t)
    elif t < F_:
        img = sE(t)
    elif t < G_:
        img = sF(t)
    elif t < H_:
        img = sG(t)
    else:
        img = sH(t)
    img = pal8(img)
    fr = np.ascontiguousarray(cv2.resize(img, (1080, 1920), interpolation=cv2.INTER_NEAREST))
    if t > SIG_T - 0.3:
        k = min(1.0, (t - SIG_T + 0.3) / 0.6); yy = np.arange(1920)[:, None, None]
        fr[:] = (fr * (1 - 0.55 * k * np.clip((yy - 1250) / 300, 0, 1))).astype(np.uint8)
    captions(fr, t, CAPS)
    signature(fr, t, SIG_T)
    return fr
