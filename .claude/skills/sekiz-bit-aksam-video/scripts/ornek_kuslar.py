"""ÖRNEK SAHNE (v2): kıyı çamurçulluğunun 11 günlük göçü (15 sn, seslendirmesiz test).
Yeni videoda bu dosyayı kopyala; sahneleri ve zamanları konuya göre değiştir.
Tuval 540x960 (x2 büyütme). Ufuk ~y570, altyazı bölgesi tuvalde y~760-840 (koyu zemin)."""
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
TAKEOFF, LAND = 1.25, 1.7


def prog(tl):
    return ease((tl - 0.4) / 3.8)


SFX = [(0.8, 'chirp'), (2.9, 'chirp'), (T2, 'whoosh'), (T2 + TAKEOFF, 'flutter'), (T3, 'whoosh'),
       (T4, 'whoosh'), (T4 + LAND, 'sparkle'), (SIG_T + 0.05, 'chime'), (T3 + 4.2, 'sparkle')]
_prev = None
for _f in range(int(T3 * FPS), int(T4 * FPS)):
    _d = min(11, 1 + int(prog(_f / FPS - T3) * 10.999))
    if _prev is not None and _d != _prev:
        SFX.append((_f / FPS, 'tick'))
    _prev = _d

HZ = 570
FAR = skyline(1, -20, 560, HZ, 40, 130, 24, 50, (0, 4))
MID = skyline(2, 80, 560, HZ + 4, 26, 84, 22, 46, (4, 14))
CL_DUSK = [(40, 150, 260, 8, (66, 44, 110), (214, 112, 130), 4), (300, 232, 180, 6, (88, 52, 118), (236, 132, 118), 6),
           (110, 330, 300, 10, (120, 62, 124), (250, 156, 112), 3), (360, 410, 150, 6, (156, 72, 122), (255, 176, 118), 5),
           (40, 470, 210, 5, (176, 82, 118), (255, 190, 126), 2.5)]
GROUND = (22, 16, 42)
POST_X, POST_TOP, BIRD_S = 196, 604, 2.6
BIRD_Y = POST_TOP - 21 * BIRD_S


def clouds(img, items, t, sp_mul=1.0):
    for (x, y, L, th, dark, lit, sp) in items:
        cloud_band(img, x, y, L, th, dark, lit, t, sp * sp_mul)


def harbor(t):
    img = canvas(); sky(img, DUSK, HZ)
    sx, sy = 392, 468
    glow_layers(img, sx, sy, 230, (255, 170, 110))
    disc(img, sx, sy, 32, (255, 200, 140)); disc(img, sx, sy - 3, 26, (255, 222, 168)); disc(img, sx - 4, sy - 8, 14, (255, 240, 200))
    clouds(img, CL_DUSK, t)
    draw_skyline(img, FAR, (136, 76, 138), lit_p=0.05, t=t, haze=(204, 104, 128))
    draw_skyline(img, MID, (84, 54, 118), lit_p=0.3, t=t, rim=(176, 98, 134))
    for b in MID:
        for wx, wy, rr in b['wins']:
            if rr < 0.04:
                halo(img, wx + 1, wy + 1, 9, GLOW, 0.6, 0.4)
    # deniz feneri (hacimli silindir) + dönen ışık
    cylinder(img, 470, 494, 452, HZ + 6, R_STONE)
    for yb in (482, 520):
        cylinder(img, 470, 494, yb, yb + 10, [(90, 30, 46), (140, 46, 56), (196, 66, 64), (232, 104, 84)], cap=False)
    rect(img, 466, 446, 498, 452, (40, 30, 64)); rect(img, 472, 428, 492, 446, (255, 222, 150))
    cv2.fillPoly(img, [np.array([(468, 428), (496, 428), (482, 414)], np.int32)], (60, 36, 70))
    glow_layers(img, 482, 437, 70, (255, 200, 130))
    ang = math.sin(t * 1.6)
    beam = np.array([(482, 437), (482 - 260 * ang, 400), (482 - 260 * ang, 470)], np.int32) if abs(ang) > 0.15 else None
    if beam is not None:
        m = np.zeros((CH, CW), np.uint8); cv2.fillPoly(m, [beam], 1)
        blend_mask(img, (m > 0) & (BAY < 0.35 * abs(ang)), (255, 214, 160), 0.35)
    sea(img, HZ + 4, 672, (128, 70, 122), (50, 34, 86), t,
        reflect=[(sx, 30, (255, 186, 120)), (482, 6, (255, 210, 150)), (60, 8, (255, 196, 110))])
    # ön plandaki ışıklı bina (solda)
    vgrad_rect(img, 0, 430, 96, 680, (58, 40, 94), (34, 24, 66))
    rect(img, 0, 420, 104, 432, (44, 30, 78)); cv2.line(img, (0, 420), (103, 420), C(RIM, 0.55), 1)
    cv2.line(img, (95, 432), (95, 679), C(RIM, 0.4), 1)
    glow_layers(img, 48, 522, 120, (255, 170, 90))
    vgrad_rect(img, 28, 494, 70, 552, (255, 226, 160), (255, 176, 92))
    rect(img, 48, 494, 50, 552, (170, 104, 60)); rect(img, 28, 521, 70, 523, (170, 104, 60))
    rect(img, 24, 552, 74, 556, (80, 56, 90))
    rect(img, 14, 596, 40, 680, (30, 22, 56)); img[636:640, 34:37] = (255, 200, 120)
    sea_level = 672
    # iskele: tahta güverte + hacimli direkler
    vgrad_rect(img, 96, 652, 330, 668, (126, 84, 78), (60, 40, 56)); cv2.line(img, (96, 652), (329, 652), C(RIM, 0.7), 1)
    for k in range(98, 330, 18):
        cv2.line(img, (k, 653), (k, 667), (52, 34, 50), 1)
    for px in (130, POST_X, 262, 318):
        cylinder(img, px - 8, px + 8, POST_TOP if px == POST_X else 628, 760, R_WOOD)
    rect(img, 0, sea_level + 8, CW, CH, GROUND)
    dither_rect(img, 0, sea_level + 8, CW, sea_level + 20, (110, 58, 110), 0.5)
    dither_rect(img, 0, sea_level + 20, CW, sea_level + 32, (80, 44, 96), 0.3)
    return img


def scene1(t):
    img = harbor(t)
    for i in range(7):
        k = (i + 1) // 2; side = 1 if i % 2 else -1
        tiny_bird(img, 600 - 46 * t + 12 * k, 250 + side * 7 * k, t * 1.6 + i * 0.13)
    godwit(img, POST_X - 6, BIRD_Y, BIRD_S, 'stand', t * 0.5, look=0.6 * math.sin(t * 0.9))
    return upscale(img)


def scene2(tl, t):
    img = harbor(t)
    if tl < TAKEOFF:
        godwit(img, POST_X - 6, BIRD_Y, BIRD_S, 'stand', t * 0.5)
    else:
        u = tl - TAKEOFF
        godwit(img, POST_X - 6 + 70 * u + 40 * u * u, BIRD_Y - 50 * u - 60 * u * u, BIRD_S, 'fly', u * 3.2)
    k = ease(tl / 1.1)
    cx = int(270 + (POST_X + 30 - 270) * k); cy = int(480 + (BIRD_Y - 480) * k)
    return upscale(img, (cx - 135, cy - 240, 270, 480))


CL_NIGHT = [(0, 200, 220, 7, (30, 30, 70), (120, 120, 170), -50), (260, 330, 160, 6, (36, 34, 80), (140, 136, 186), -80),
            (100, 470, 300, 9, (44, 38, 88), (160, 150, 196), -110)]


def scene3(tl, t):
    img = canvas(); sky(img, NIGHT, 600)
    stars(img, 9, 160, 560, t)
    glow_layers(img, 420, 220, 170, (190, 190, 250))
    ellipsoid(img, 420, 220, 26, 26, R_MOON, light=(-0.7, -0.3, 0.65), rim=None, amb=0.08)
    for (cx_, cy_, r_) in ((412, 212, 4), (428, 230, 3), (418, 232, 2)):
        disc(img, cx_, cy_, r_, (176, 172, 192))
    clouds(img, CL_NIGHT, t)
    sea(img, 600, CH, (42, 38, 90), (12, 12, 36), t, speed=-90, reflect=[(420, 22, (190, 190, 230))])
    bob = 6 * math.sin(t * 2.6)
    godwit(img, 230, 400 + bob, 3.6, 'fly', t * 3.0, light=(0.6, -0.5, 0.6), rim=(200, 204, 255))
    return upscale(img)


CL_DAWN = [(60, 170, 240, 7, (92, 70, 138), (240, 168, 150), 3), (320, 260, 170, 6, (130, 84, 146), (255, 190, 150), 4),
           (40, 380, 280, 9, (176, 98, 136), (255, 208, 150), 2)]


def scene4(tl, t):
    img = canvas(); sky(img, DAWN, 580)
    glow_layers(img, 130, 560, 240, (255, 196, 130))
    disc(img, 130, 566, 34, (255, 214, 160)); disc(img, 126, 560, 22, (255, 236, 196))
    clouds(img, CL_DAWN, t)
    sea(img, 580, 720, (176, 104, 132), (64, 44, 98), t, reflect=[(130, 34, (255, 200, 140))])
    pts = np.array([(290, 610), (330, 556), (380, 532), (440, 510), (500, 498), (540, 502), (540, 720), (290, 720)], np.int32)
    m = np.zeros((CH, CW), np.uint8); cv2.fillPoly(m, [pts], 1); m = m > 0
    yy, xx = np.mgrid[0:CH, 0:CW]
    lum = 0.15 + 0.45 * np.clip((560 - xx) / 300, 0, 1) * np.clip((720 - yy) / 230, 0, 1)
    ramp_fill(img, m, lum, R_STONE, 0, 0)
    cv2.polylines(img, [pts[:6]], False, C(RIM, 0.85), 1)
    for tx in (452, 494, 522):
        rect(img, tx, 452, tx + 5, 506, (36, 26, 54))
        ellipsoid(img, tx + 2, 446, 16, 14, [(26, 30, 46), (40, 48, 62), (66, 72, 80), (120, 104, 96)], light=(-0.8, -0.4, 0.5), rim=RIM)
    rect(img, 0, 720, CW, CH, GROUND); dither_rect(img, 0, 720, CW, 734, (120, 70, 110), 0.5)
    land = (420, 509 - 21 * 2.4)
    if tl < LAND:
        k = ease(tl / LAND)
        x = 600 + (land[0] - 600) * k; y = 330 + (land[1] - 330) * k - 60 * math.sin(math.pi * k)
        mirrored(img, godwit, x, y, 2.4, 'fly', t * 3.2, light=(-0.65, -0.35, 0.68))
    else:
        mirrored(img, godwit, land[0], land[1], 2.4, 'stand', t * 0.5, light=(-0.65, -0.35, 0.68))
        if tl < LAND + 0.6 and int(tl * 12) % 2 == 0:
            sparkle(img, land[0] - 40, land[1] - 40, 5)
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
