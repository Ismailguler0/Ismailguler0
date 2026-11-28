"""EŞİK – Abdülhamid denizaltısı (katman yığma, iri 8-bit piksel, sabit palet)."""
import math, sys, importlib.util
import numpy as np, cv2
sys.path.insert(0, '/home/user/Ismailguler0/.claude/skills/sekiz-bit-aksam-video/scripts')
sys.path.insert(0, '/home/user/esik-araclar/ortak')
from pix8 import signature, captions
from ymotor import *

_sp = importlib.util.spec_from_file_location('kk_sky', '/home/user/esik-araclar/kizkulesi/kizkulesi.py')
KK = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(KK)      # tarihî İstanbul silüeti (Haliç)

DUR, FPS, SIG_T = 40.5, 30, 38.1
A_, B_, C_, D_, E_, F_, G_, H_ = 0.0, 6.1, 7.54, 12.8, 17.52, 26.12, 31.32, 34.56
TORP = 1.8            # 0-2 sn kancası: su altından torpido
DIVE = 15.6           # 16. sn civarı: denizaltı dalar
HOOK2 = 17.52         # 2. kanca: içine binecek tek denizci yok
MUSIC = dict(bpm=74, root=155.6)
CAPS = [(0.0, 3.0, "Su altından [torpido] atan...", 1608), (3.0, 6.0, "İlk denizaltı: [Osmanlı]!", 1608),
        (6.1, 7.5, "[1886], İstanbul", 1608), (7.54, 12.7, "[Parça parça] geldi, Haliç'te birleşti", 1608),
        (12.8, 15.5, "Adı: [ABDÜLHAMİD]", 1608), (15.5, 17.4, "Buharla çalışır, [dalar]", 1608),
        (17.52, 21.3, "Ama [binecek denizci] yok!", 1608), (21.46, 25.9, "\"Bu bir [demir tabut]\"", 1608),
        (26.12, 29.4, "Su altında [birkaç dakika]", 1608), (29.42, 31.2, "[Hiç] savaşa girmedi", 1608),
        (31.32, 34.4, "Haliç'te [paslanıp] gitti", 1608), (34.56, 38.1, "Sen olsan [biner miydin?]", 1608)]
SFX = [(0.0, 'boom'), (TORP, 'whoosh'), (TORP + 0.5, 'farboom'), (B_, 'whoosh'), (C_, 'whoosh'), (11.6, 'bell'),
       (11.65, 'sparkle'), (D_, 'whoosh'), (DIVE, 'rumble'), (HOOK2, 'boom'), (HOOK2 + 0.05, 'crash'), (F_, 'whoosh'),
       (G_, 'whoosh'), (H_, 'whoosh'), (SIG_T + 0.05, 'chime')] + [(26.4 + k * 0.5, 'tick') for k in range(6)]

set_palette([
    (8, 8, 20), (16, 14, 36), (28, 24, 60), (44, 38, 92), (70, 58, 128), (110, 90, 160), (170, 120, 180),
    (236, 120, 130), (252, 160, 120), (255, 204, 140), (255, 236, 180),
    (10, 34, 46), (14, 52, 66), (24, 80, 96), (50, 120, 130), (110, 180, 186), (200, 240, 236),
    (14, 36, 70), (22, 58, 104), (36, 90, 140), (70, 136, 186), (236, 246, 250),
    (30, 34, 34), (52, 60, 58), (84, 96, 92), (130, 144, 138), (180, 190, 184),
    (90, 44, 26), (140, 70, 36), (190, 110, 50),
    (70, 44, 30), (112, 74, 46), (164, 116, 70), (206, 166, 110),
    (226, 60, 58), (255, 252, 236), (240, 232, 218)])

STEEL, DSTEEL, LSTEEL = (52, 60, 58), (30, 34, 34), (130, 144, 138)


def sub_model(rust=0.0, hatch=False):
    V = Vox(98, 20, 28); x, y, z = V.x, V.y, V.z
    u = (x - 48) / 46
    rr = 6.8 * np.clip(1 - np.abs(u) ** 2.4, 0, 1) ** 0.5
    hull = (np.hypot(y - 9.5, z - 8) <= rr)
    V.put(hull, STEEL); V.put(hull & (z > 11), (84, 96, 92)); V.put(hull & (z < 4), DSTEEL)
    V.put(hull & ((x.astype(int) % 8) == 0) & (z > 9), DSTEEL)                         # perçin çizgileri
    tower = superell(x, y, 50, 9.5, 4.5, 3, 2.2) & (z >= 13) & (z < 20)
    V.put(tower, (84, 96, 92)); V.put(tower & (z == 17) & (np.abs(y - 9.5) > 2.2), (255, 204, 140))
    V.put(superell(x, y, 50, 9.5, 5, 3.4, 2.2) & (z == 13), DSTEEL)
    if hatch:
        V.put((np.abs(x - 50) < 2) & (np.abs(y - 9.5) < 2) & (z == 20), DSTEEL)
        V.put((np.abs(x - 47.5) < 0.7) & (np.abs(y - 9.5) < 2) & (z >= 20) & (z < 24), (130, 144, 138))
    else:
        V.put((np.abs(x - 50) < 2) & (np.abs(y - 9.5) < 2) & (z == 20), (130, 144, 138))
    V.put((np.hypot(x - 38, y - 9.5) < 1.6) & (z >= 13) & (z < 24), DSTEEL)              # katlanır baca
    V.put((np.hypot(x - 38, y - 9.5) < 1.7) & (z >= 22) & (z < 24), (140, 70, 36))
    V.put((np.abs(x - 2) < 1) & (np.abs(y - 9.5) < 0.8) & (z >= 2) & (z < 15), DSTEEL)  # dümen
    for a in range(4):                                                                   # pervane
        ang = a * math.pi / 2 + 0.4
        for k in range(6):
            V.put((np.abs(x - 0.5) < 0.8) & (np.abs(y - 9.5 - k * math.cos(ang)) < 0.8) & (np.abs(z - 8 - k * math.sin(ang)) < 0.8), (180, 190, 184))
    V.put((x > 93) & (np.hypot(y - 9.5, z - 8) < 1.3), (8, 8, 20))                       # torpido kovanı
    for k in range(40):                                                                  # güverte korkuluğu
        V.put((np.abs(x - (24 + k)) < 0.6) & (np.abs(y - 9.5) < 0.6) & (z == 15) & (k % 3 == 0), LSTEEL)
    if rust > 0:
        rng = np.random.default_rng(4)
        sel = V.S[..., 3] > 0
        noise = rng.random(V.S.shape[:3])
        m = sel & (noise < rust * 0.85)
        V.S[m, :3] = np.where((noise[m] < rust * 0.4)[:, None], (90, 44, 26), (140, 70, 36))
    return V.bake()


def pier_model(L=120):
    V = Vox(L, 18, 9); x, y, z = V.x, V.y, V.z
    V.put((y >= 2) & (y < 16) & (z >= 6) & (z < 8), (164, 116, 70))
    V.put((y >= 2) & (y < 16) & (z >= 6) & (z < 8) & (x.astype(int) % 4 == 0), (112, 74, 46))
    for px in range(4, L, 14):
        for py in (3, 14):
            V.put((np.abs(x - px) < 1) & (np.abs(y - py) < 1) & (z < 7), (70, 44, 30))
    return V.bake()


def sailors_model():
    V = Vox(24, 12, 16)
    for k, (px, py) in enumerate(((5, 4), (11, 7), (17, 4))):
        person(V, px, py, 0, (22, 58, 104), hat=(240, 232, 218), h=1.2)
    return V.bake()


def slip_model():
    V = Vox(112, 30, 6); x, y, z = V.x, V.y, V.z
    V.put((np.abs(y - 15) < 12) & (z < 2), (112, 74, 46))
    for k in range(0, 112, 10):
        V.put((np.abs(x - k) < 1.5) & (np.abs(y - 15) < 12) & (z == 2), (164, 116, 70))
    for s in (-5, 5):
        V.put((np.abs(y - 15 - s) < 1) & (z >= 2) & (z < 5), (70, 44, 30))
    return V.bake()


SUB, SUB_H = sub_model(), sub_model(0, True)
SUB_R = [sub_model(r) for r in (0.25, 0.5, 0.8)]
SECT = []
for i in range(3):
    S = SUB.copy(); m = np.zeros(S.shape[2], bool); m[i * 33:(i + 1) * 33] = True
    S[:, :, ~m, 3] = 0; SECT.append(S)
PIER, SAIL, SLIP = pier_model(), sailors_model(), slip_model()
SEA = make_tile((22, 58, 104), (36, 90, 140), (70, 136, 186))
SEA_N = make_tile((14, 36, 70), (22, 58, 104), (36, 90, 140))
HZ = 92


def surface(t, cam, K, night=False, flow=(1, 0)):
    img = np.zeros((CH, CW, 3), np.uint8)
    KK.draw_sky(img, t, night, cam[2])
    draw_plane(img, SEA_N if night else SEA, cam, K, t, flow, HZ)
    fog(img, HZ, 36, (70, 58, 128) if night else (236, 120, 130))
    return img


def underwater(t):
    img = np.zeros((CH, CW, 3), np.uint8)
    vgrad(img, [(50, 120, 130), (24, 80, 96), (14, 52, 66), (10, 34, 46), (8, 8, 20)])
    for k in range(5):                                                   # ışık huzmeleri
        x0 = int((k * 47 + t * 6) % 260) - 40
        p = np.array([(x0, 0), (x0 + 14, 0), (x0 + 70, CH), (x0 + 40, CH)], np.int32)
        m = np.zeros((CH, CW), np.uint8); cv2.fillPoly(m, [p], 1)
        mm = (m > 0) & (BAY < 0.25 * (1 - YY / CH))
        img[mm] = (110, 180, 186)
    img[CH - 26:] = (30, 34, 34); img[CH - 26:][BAY[CH - 26:] < 0.3] = (70, 44, 30)
    rng = np.random.default_rng(1)
    for k in range(30):
        bx = (rng.uniform(0, CW) + 4 * math.sin(t + k)) % CW; by = (rng.uniform(0, CH) - t * (20 + k % 5 * 6)) % CH
        img[int(by), int(bx)] = (200, 240, 236)
    return img


def bubbles(img, X, Y, t, n=12, spread=10):
    rng = np.random.default_rng(int(t * 10))
    for k in range(n):
        a = (t * 1.5 + k / n) % 1
        bx, by = int(X + rng.uniform(-spread, spread)), int(Y - a * 50)
        if 0 <= bx < CW and 0 <= by < CH:
            cv2.circle(img, (bx, by), 1 if k % 3 else 2, (200, 240, 236), 1)


def one(img, S, cam, K, wx=0, wy=0, own=0, zoff=0, zmin=None):
    obj = np.zeros((CH, CW), bool)
    draw_stack(img, obj, S, wx, wy, own, cam, K, zoff=zoff, zmin_screen=zmin)
    add_outline(img, obj)
    return obj


# ---------------------------------------------------------------- sahneler
def sA(t):
    K = 1.6; cam = (26, 0, 0.12 + 0.1 * math.sin(t * 0.5), CW / 2, 175)
    img = underwater(t)
    one(img, SUB, cam, K, zoff=2 * math.sin(t * 1.2))
    bx, by = to_screen(-40, 0, cam, K, 8)
    bubbles(img, bx, by, t)
    if t >= TORP:                                                         # torpido
        d = (t - TORP) * 24
        X0, Y0 = to_screen(46 + d, 0, cam, K, 8 + 2 * math.sin(t * 1.2))
        if X0 < CW + 10:
            cv2.line(img, (int(X0) - 16, int(Y0)), (int(X0), int(Y0)), (180, 190, 184), 4)
            cv2.line(img, (int(X0) - 16, int(Y0) - 1), (int(X0), int(Y0) - 1), (236, 246, 250), 1)
            img[int(Y0) - 2:int(Y0) + 3, max(0, int(X0) - 19):max(0, int(X0) - 16)] = (226, 60, 58)
            for k in range(14):
                bx_ = int(X0 - 20 - k * 4); by_ = int(Y0 + 3 * math.sin(k + t * 9))
                if 0 <= bx_ < CW:
                    cv2.circle(img, (bx_, by_), 1 + k % 2, (200, 240, 236), 1)
        if TORP + 0.45 < t < TORP + 0.75:
            flash(img, (255, 236, 180), 0.5 * (1 - (t - TORP - 0.45) / 0.3))
    if t < 0.25:
        flash(img, (200, 240, 236), 0.6 * (1 - t / 0.25))
    if t > 3.0:
        press_text(img, "İLK", 90, 60, 22, (255, 204, 140))
    return img


def sB(t):
    tl = t - B_; K = 1.0
    cam = (0, 0, 0.2, CW / 2, 220)
    img = surface(t, cam, K)
    for i in range(3):
        wx = -60 + i * 42 + tl * 8 - 20
        one(img, SECT[i], cam, K * 0.9, wx, 10 * (i - 1), 0.3 * i, zoff=0.6 * math.sin(t * 2 + i), zmin=0)
    press_text(img, "1886", 90, 128, 18, (255, 252, 236))
    return img


def sC(t):
    tl = t - C_; K = 1.45
    cam = (0, 0, 0.5 + tl * 0.12, CW / 2, 215)
    img = surface(t, cam, K, flow=(0, 0))
    one(img, SLIP, cam, K)
    k = min(1.0, tl / 4.0)
    gap = 26 * (1 - k * k)
    for i in range(3):
        one(img, SECT[i], cam, K, (i - 1) * gap, 0, 0, zoff=2)
    if t >= 11.6:
        X, Y = to_screen(0, 0, cam, K, 12)
        for a in range(8):
            r = (t - 11.6) * 80
            px, py = int(X + r * math.cos(a * 0.785)), int(Y + r * 0.6 * math.sin(a * 0.785))
            if 0 <= px < CW and 0 <= py < CH:
                img[py, px] = (255, 236, 180)
        if t < 11.85:
            flash(img, (255, 236, 180), 0.4)
    return img


def sD(t):
    tl = t - D_; K = 1.5
    cam = (0, 0, 2.2 + tl * 0.3, CW / 2, 215)
    img = surface(t, cam, K)
    dive = max(0.0, (t - DIVE) * 9)
    one(img, SUB, cam, K, zoff=-1 - dive + 0.8 * math.sin(t * 2), zmin=0)
    X, Y = to_screen(-10, 0, cam, K, 24 - dive)
    if dive < 12:
        for k in range(6):                                                # baca dumanı
            a = (t * 0.8 + k / 6) % 1
            cv2.circle(img, (int(X + a * 10), int(Y - a * 30)), int(2 + a * 4), (180, 190, 184) if a < 0.5 else (130, 144, 138), -1)
    if dive > 0:
        X2, Y2 = to_screen(0, 0, cam, K)
        bubbles(img, X2, Y2 + 4, t, 16, 40)
    return img


def sE(t):                                                                 # 2. kanca: kimse binmiyor
    tl = t - E_; K = 1.35
    sh = shake(t, HOOK2, 0.45, 6)
    cam = (10, 8, 0.45 + tl * 0.06, CW / 2 + sh, 215)
    img = surface(t, cam, K, flow=(0.5, 0))
    obj = np.zeros((CH, CW), bool)
    draw_stack(img, obj, PIER, 0, 22, 0, cam, K)
    draw_stack(img, obj, SUB_H, 0, 0, 0, cam, K, zoff=-1 + 0.6 * math.sin(t * 1.5), zmin_screen=0)
    jit = int(2 * math.sin(t * 20)) if t > HOOK2 else 0
    draw_stack(img, obj, SAIL, 50 + jit * 0.3, 24, math.pi, cam, K, zoff=8)
    add_outline(img, obj)
    if HOOK2 <= t < HOOK2 + 0.3:
        flash(img, (226, 60, 58), 0.6 * (1 - (t - HOOK2) / 0.3))
    if t > HOOK2:
        press_text(img, "?", 90 + sh, 70, 24 + int(3 * math.sin(t * 7)), (226, 60, 58))
    if t > 21.46:
        k = min(1.0, (t - 21.46) / 1.0)
        yy = YY[..., None]; d = np.hypot(XX - 90, YY - 200)[..., None] / 200
        img[:] = (img * (1 - 0.6 * k * np.clip(d, 0, 1))).astype(np.uint8)
    return img


def sF(t):
    tl = t - F_; K = 1.6
    cam = (0, 0, -0.2 + tl * 0.1, CW / 2, 185)
    img = underwater(t)
    rise = max(0.0, (t - 29.42) * 30)
    one(img, SUB, cam, K, zoff=-4 + rise + 1.5 * math.sin(t))
    bx, by = to_screen(-40, 0, cam, K, 8 + rise)
    bubbles(img, bx, by, t)
    sec = min(180, int(tl * 50))
    col = (226, 60, 58) if sec > 120 and int(t * 4) % 2 else (255, 252, 236)
    press_text(img, f"{sec // 60}:{sec % 60:02d}", 90, 60, 18, col)
    return img


def sG(t):
    tl = t - G_; K = 1.45
    cam = (10, 8, 3.4 + tl * 0.12, CW / 2, 215)
    img = surface(t, cam, K, flow=(0.3, 0))
    obj = np.zeros((CH, CW), bool)
    draw_stack(img, obj, PIER, 0, 22, 0, cam, K)
    r = min(2, int(tl / 1.1))
    draw_stack(img, obj, SUB_R[r], 0, 0, 0, cam, K, zoff=-2, zmin_screen=0)
    add_outline(img, obj)
    return img


def sH(t):
    tl = t - H_; K = 1.6
    cam = (10, 8, 4.0 + tl * 0.1, CW / 2, 220)
    img = surface(t, cam, K, night=True, flow=(0.3, 0))
    obj = np.zeros((CH, CW), bool)
    draw_stack(img, obj, PIER, 0, 22, 0, cam, K)
    draw_stack(img, obj, SUB_R[2], 0, 0, 0, cam, K, zoff=-2.5, zmin_screen=0)
    add_outline(img, obj)
    return img


def frame_at(t):
    for t0, fn in ((H_, sH), (G_, sG), (F_, sF), (E_, sE), (D_, sD), (C_, sC), (B_, sB), (A_, sA)):
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
