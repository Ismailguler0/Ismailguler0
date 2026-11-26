"""ÖRNEK SAHNE: kıyı çamurçulluğunun 11 günlük göçü (15 sn, seslendirmesiz test).
Yeni videoda bu dosyayı kopyala; sahne fonksiyonlarını ve zamanları konuya göre değiştir."""
import math
import numpy as np
from pix8 import *

DUR, FPS = 15.0, 30
T2, T3, T4, SIG_T = 5.0, 7.5, 12.5, 12.6
CAPS = [
    (0.3, 2.6, "[11 gün] boyunca", 1608),
    (2.6, 4.9, "[hiç konmadan] uçan bir kuş...", 1608),
    (5.1, 7.4, "[Kıyı çamurçulluğu]", 1608),
    (7.6, 10.0, "[Alaska]'dan [Tazmanya]'ya", 1608),
    (10.0, 12.4, "[13.000 km]'den fazla, tek seferde", 1608),
    (12.6, 14.95, "Üstelik bu, [ilk göçüydü.]", 1350),
]
TAKEOFF = 1.2      # sahne 2 içinde
LAND = 1.6         # sahne 4 içinde


def prog(tl):      # sahne 3 sayaç ilerlemesi
    return ease((tl - 0.4) / 3.8)


SFX = [(0.8, 'chirp'), (2.9, 'chirp'), (T2, 'whoosh'), (T2 + TAKEOFF, 'flutter'), (T3, 'whoosh'),
       (T4, 'whoosh'), (T4 + LAND, 'sparkle'), (SIG_T + 0.05, 'chime')]
_prev = None
for _f in range(int(T3 * FPS), int(T4 * FPS)):
    _d = min(11, 1 + int(prog(_f / FPS - T3) * 10.999))
    if _prev is not None and _d != _prev:
        SFX.append((_f / FPS, 'tick'))
    _prev = _d
SFX.append((T3 + 4.2, 'sparkle'))

FAR = skyline(1, -10, 280, 280, 22, 64, 12, 24, (0, 2))
MID = skyline(2, -6, 280, 282, 12, 38, 10, 22, (2, 8))
CLOUDS = [(20, 70, 60, (150, 76, 130), 3), (160, 112, 44, (204, 98, 124), 4), (60, 150, 80, (226, 116, 118), 2.5),
          (200, 190, 50, (244, 150, 110), 3.5), (100, 226, 70, (252, 170, 112), 2)]
GROUND = (26, 20, 48)


def harbor(t, bird=True):
    img = canvas(); sky(img, DUSK, 280)
    sun_x, sun_y = 196, 226
    halo(img, sun_x, sun_y, 56, (255, 180, 110), 0.8, 0.5); disc(img, sun_x, sun_y, 15, (255, 214, 150))
    disc(img, sun_x, sun_y - 2, 11, (255, 232, 180))
    streaks(img, CLOUDS, t)
    draw_skyline(img, FAR, (128, 72, 134), lit_p=0.08, t=t)
    draw_skyline(img, MID, (80, 52, 114), lit_p=0.28, t=t, rim=(150, 84, 130))
    for b in MID:
        for wx, wy, rr in b['wins']:
            if rr < 0.05:
                halo(img, wx, wy, 5, GLOW, 0.6, 0.45)
    # deniz feneri (sağda)
    rect(img, 240, 214, 250, 282, (60, 42, 92)); rect(img, 238, 206, 252, 214, (50, 36, 80))
    rect(img, 241, 200, 249, 206, (255, 214, 140))
    if int(t * 2) % 2 == 0:
        halo(img, 245, 203, 22, (255, 120, 90), 0.8, 0.5); img[202:205, 244:247] = (255, 110, 90)
    # ön plandaki ışıklı bina (solda)
    rect(img, 0, 222, 46, 336, (48, 34, 84)); rect(img, 0, 216, 50, 222, (40, 28, 72))
    cv2.line(img, (0, 216), (49, 216), C(RIM, 0.6), 1); cv2.line(img, (45, 222), (45, 335), C(RIM, 0.45), 1)
    halo(img, 22, 262, 34, GLOW, 0.75, 0.45)
    rect(img, 15, 252, 30, 272, (255, 196, 104)); rect(img, 22, 252, 23, 272, (190, 120, 70)); rect(img, 15, 261, 30, 262, (190, 120, 70))
    rect(img, 15, 252, 30, 254, (255, 228, 160))
    rect(img, 8, 296, 20, 336, (30, 22, 56))
    sea(img, 284, 336, (120, 66, 120), (54, 38, 90), t, sun_x=sun_x)
    rect(img, 0, 336, CW, CH, GROUND)
    dither_rect(img, 0, 336, CW, 344, (110, 60, 110), 0.5)
    # iskele
    rect(img, 46, 326, 150, 332, (70, 48, 64)); cv2.line(img, (46, 326), (149, 326), C(RIM, 0.7), 1)
    for px in (60, 92, 124):
        rect(img, px, 300, px + 6, 360, (58, 40, 58)); cv2.line(img, (px, 300), (px + 5, 300), C(RIM, 0.8), 1)
    return img


def scene1(t):
    img = harbor(t)
    for i in range(5):
        x = 300 - 22 * t - 7 * (i // 2 + 1) * (i > 0); y = 120 + (4 * (i // 2 + 1) * (1 if i % 2 else -1) if i else 0)
        tiny_bird(img, x + 7 * (i > 0) * (i // 2 + 1) * 2, y, int(t * 7) + i)
    godwit(img, 98, 282, 1.8, 'stand')
    return upscale(img)


def scene2(tl, t):
    img = harbor(t)
    if tl < TAKEOFF:
        godwit(img, 98, 282 - (1 if int(t * 3) % 3 == 0 else 0), 1.8, 'stand')
    else:
        u = tl - TAKEOFF
        godwit(img, 98 + 34 * u + 20 * u * u, 282 - 30 * u - 26 * u * u, 1.8, 'fly', int(u * 10))
    k = ease(tl / 1.0)
    cx = int(135 + (112 - 135) * k); cy = int(240 + (262 - 240) * k)
    return upscale(img, (cx - 67, cy - 120, 135, 240))


def scene3(tl, t):
    img = canvas(); sky(img, NIGHT, 300)
    stars(img, 9, 70, 260, t)
    halo(img, 214, 118, 34, (210, 210, 255), 0.7, 0.35); disc(img, 214, 118, 10, (236, 232, 214)); disc(img, 218, 115, 8, (26, 26, 66))
    streaks(img, [(x, y, L, c, -40) for (x, y, L, c, _) in
                  [(0, 120, 70, (54, 46, 100), 0), (150, 180, 50, (70, 54, 112), 0), (80, 236, 90, (84, 60, 120), 0)]], t)
    sea(img, 300, CH, (40, 36, 86), (14, 14, 40), t, sun_x=214, sun_col=(150, 150, 200), speed=-60)
    bob = 4 * math.sin(t * 3)
    godwit(img, 120, 200 + bob, 2.0, 'fly', int(t * 8), rim=(200, 200, 240))
    return upscale(img)


def scene4(tl, t):
    img = canvas(); sky(img, DAWN, 290)
    halo(img, 64, 276, 60, (255, 200, 130), 0.8, 0.5); disc(img, 64, 280, 16, (255, 226, 170))
    streaks(img, CLOUDS[1:], t)
    sea(img, 290, 360, (170, 100, 130), (70, 48, 100), t, sun_x=64, sun_col=(255, 200, 140))
    pts = np.array([(150, 300), (175, 268), (205, 258), (240, 246), (270, 250), (270, 360), (150, 360)], np.int32)
    cv2.fillPoly(img, [pts], (56, 38, 78)); cv2.polylines(img, [pts[:5]], False, C(RIM, 0.8), 1)
    for tx in (222, 246, 260):
        rect(img, tx, 230, tx + 3, 250, (40, 28, 56)); disc(img, tx + 1, 228, 6, (46, 34, 66))
    rect(img, 0, 360, CW, CH, GROUND); dither_rect(img, 0, 360, CW, 368, (120, 70, 110), 0.5)
    land = (206, 254)
    if tl < LAND:
        k = ease(tl / LAND)
        x = -20 + (land[0] + 20) * k; y = 170 + (land[1] - 170) * k - 30 * math.sin(math.pi * k)
        godwit(img, x, y, 1.3, 'fly', int(t * 9))
    else:
        godwit(img, land[0], land[1], 1.3, 'stand')
        if tl < LAND + 0.5 and int(tl * 12) % 2 == 0:
            sparkle(img, land[0] + 14, land[1] - 16)
    return upscale(img)


def frame_at(t):
    if t < T2:
        fr = scene1(t)
    elif t < T3:
        fr = scene2(t - T2, t)
    elif t < T4:
        tl = t - T3; fr = scene3(tl, t)
        if tl > 0.3:
            p = prog(tl); day = min(11, 1 + int(p * 10.999)); km = int(round(p * 13560 / 10)) * 10
            blit(fr, pill(f"Gün [{day}]", 52, F_BOLD), 300, 250)
            blit(fr, pill(f"[{km:,}".replace(',', '.') + "] km", 52, F_BOLD), 740, 250)
    else:
        fr = scene4(t - T4, t)
    captions(fr, t, CAPS)
    signature(fr, t, SIG_T)
    return fr
