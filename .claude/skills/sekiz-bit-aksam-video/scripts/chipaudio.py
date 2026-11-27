#!/usr/bin/env python3
"""Sakin 8-bit müzik + efektler.  Kullanım: chipaudio.py <sahne.py> <çıktı.wav> [ses.mp3]

Sahne dosyası şunları tanımlar: DUR, CAPS [(baş, son, metin, y)], SFX [(zaman, tür)],
isteğe bağlı MUSIC = dict(bpm=..., root=...).  Türler: chirp whoosh tick sparkle flutter chime blip.
Ses kaydı verilirse müzik konuşma sırasında ~2 dB kısılır ve ses ~14 dB altında tutulur.
"""
import importlib.util, sys, wave, subprocess
import numpy as np

spec = importlib.util.spec_from_file_location('sahne', sys.argv[1])
S = importlib.util.module_from_spec(spec); sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
sys.path.insert(0, __import__('os').path.dirname(sys.argv[1])); spec.loader.exec_module(S)
SR = 48000; DUR = S.DUR; N = int(SR * DUR)
rng = np.random.default_rng(11)
music = np.zeros(N); sfx = np.zeros(N)
M = dict(bpm=92, root=220.0); M.update(getattr(S, 'MUSIC', {}))


def add(buf, t0, sig):
    i = int(t0 * SR)
    if 0 <= i < N:
        j = min(N, i + len(sig)); buf[i:j] += sig[:j - i]


def tt(d):
    return np.arange(int(d * SR)) / SR


def sq(f, t, duty=0.5):
    ph = np.cumsum(f) / SR if np.ndim(f) else f * t
    return np.where((ph % 1) < duty, 1.0, -1.0)


def tri(f, t):
    return 2 * np.abs(2 * ((f * t) % 1) - 1) - 1


def env(t, a=0.006, d=0.15, s=0.35):
    e = np.where(t < a, t / a, s + (1 - s) * np.exp(-(t - a) / d))
    return e * np.clip((t[-1] - t) / 0.04, 0, 1)


# ---- müzik: A minör pentatonik, yumuşak kare melodi + üçgen bas + hafif davul
BEAT = 60 / M['bpm']; EI = BEAT / 2; BAR = BEAT * 4; r = M['root']
SC = [r * 2 ** (k / 12) for k in (12, 15, 17, 19, 22, 24, 27)]
PATS = [[0, -1, 2, 3, 4, -1, 3, 2], [1, 2, -1, 0, 1, -1, -1, -1], [4, -1, 5, 4, 3, 2, 3, -1], [2, 1, 0, -1, 0, -1, -1, -1]]
ROOTS = [r / 2, r / 2 * 2 ** (8 / 12), r / 2 * 2 ** (3 / 12), r / 2 * 2 ** (10 / 12)]   # Am F C G
for b in range(int(np.ceil(DUR / BAR))):
    t0 = b * BAR
    for i, n in enumerate(PATS[b % 4]):
        if n >= 0:
            t = tt(EI * 0.95); add(music, t0 + i * EI, 0.075 * sq(SC[n], t, 0.25) * env(t, d=0.18, s=0.25))
    for i in range(4):
        t = tt(BEAT * 0.95); add(music, t0 + i * BEAT, 0.18 * tri(ROOTS[b % 4], t) * env(t, d=0.4, s=0.6))
    if b >= 1:
        for i in range(8):
            t = tt(0.03); add(music, t0 + i * EI, 0.022 * np.diff(rng.standard_normal(len(t) + 1)) * np.exp(-t / 0.01))
        for bt in (1, 3):
            t = tt(0.12); add(music, t0 + bt * BEAT, 0.06 * rng.standard_normal(len(t)) * np.exp(-t / 0.035))
        for bt in (0, 2):
            t = tt(0.14); f = 110 * np.exp(-t / 0.05) + 45
            add(music, t0 + bt * BEAT, 0.28 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.07))
fade = np.ones(N); a, z = int(0.5 * SR), int(1.0 * SR)
fade[:a] = np.linspace(0, 1, a); fade[-z:] = np.linspace(1, 0, z); music *= fade


def chirp(t0):
    for k in range(2):
        t = tt(0.05); add(sfx, t0 + k * 0.08, 0.06 * sq(np.linspace(2200, 3300, len(t)), t) * np.exp(-t / 0.03))


def whoosh(t0):
    t = tt(0.4); lp = np.convolve(rng.standard_normal(len(t)), np.ones(30) / 30, mode='same')
    add(sfx, t0 - 0.2, 0.9 * lp * np.sin(np.pi * t / t[-1]) ** 2)


def blip(t0, f0=700, f1=1000):
    t = tt(0.06); add(sfx, t0, 0.05 * sq(np.linspace(f0, f1, len(t)), t) * np.exp(-t / 0.03))


def tick(t0):
    t = tt(0.025); add(sfx, t0, 0.045 * sq(1500, t) * np.exp(-t / 0.01))


def sparkle(t0):
    for i, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
        t = tt(0.07); add(sfx, t0 + i * 0.06, 0.055 * sq(f, t, 0.25) * np.exp(-t / 0.05))


def flutter(t0):
    for i in range(7):
        t = tt(0.03); add(sfx, t0 + i * 0.045, 0.11 * rng.standard_normal(len(t)) * np.exp(-t / 0.008))


def chime(t0):
    t = tt(1.0); add(sfx, t0, 0.09 * (tri(880, t) + 0.6 * tri(1320, t)) * np.exp(-t / 0.35))


def _lp(x, k):
    return np.convolve(x, np.ones(k) / k, mode='same')


def crash(t0):
    """Dalga çarpması: sert vuruş + uzun köpük hışırtısı."""
    t = tt(1.6); nz = rng.standard_normal(len(t))
    body = _lp(nz, 6) * np.exp(-t / 0.5) * np.clip(t / 0.01, 0, 1)
    low = _lp(nz, 60) * np.exp(-t / 0.25) * 4
    th = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t / 0.2) + 35) / SR) * np.exp(-t / 0.18)
    add(sfx, t0, 0.35 * body + 0.5 * low + 0.35 * th)


def wind(t0, dur=3.0):
    t = tt(dur); nz = _lp(rng.standard_normal(len(t)), 40)
    sw = 0.6 + 0.4 * np.sin(2 * np.pi * t / dur * 1.5 + rng.random() * 6)
    add(sfx, t0, 0.5 * nz * sw * np.sin(np.pi * t / dur))


def glare(t0):
    """Göz kamaşması: yükselen parlak akor + parıltı hışırtısı."""
    t = tt(1.0); e = np.sin(np.pi * np.clip(t / 1.0, 0, 1)) ** 2
    ch = sum(tri(f, t) for f in (1046.5, 1318.5, 1568.0, 2093.0)) / 4
    add(sfx, t0 - 0.5, 0.14 * ch * e + 0.05 * np.diff(rng.standard_normal(len(t) + 1)) * e)


def boom(t0, far=False):
    """Derin patlama gümlemesi (far=True: uzaktan gelen boğuk bum)."""
    tn = tt(3.0 if not far else 2.0); f = (60 if not far else 45) * np.exp(-tn / 0.5) + 22
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tn / (0.9 if not far else 0.6))
    nz = _lp(rng.standard_normal(len(tn)), 30 if not far else 120) * np.exp(-tn / (0.7 if not far else 0.4))
    add(sfx, t0, (0.8 * s + 1.4 * nz) * (1.0 if not far else 0.45))


def bell(t0):
    """İtfaiye çanı: iki vuruş."""
    for k in range(3):
        tn = tt(0.6); ch = sum(np.sin(2 * np.pi * f * tn) * np.exp(-tn / 0.25) for f in (1180, 1770, 2650)) / 3
        add(sfx, t0 + k * 0.28, 0.12 * ch)


def rumble(t0, dur=2.0):
    tn = tt(dur); nz = _lp(rng.standard_normal(len(tn)), 200)
    add(sfx, t0, 2.2 * nz * (tn / dur) ** 1.5)


KIND = dict(boom=boom, farboom=lambda t: boom(t, True), bell=bell, rumble=rumble, crash=crash, wind=wind, glare=glare, chirp=chirp, whoosh=whoosh, blip=blip, tick=tick, sparkle=sparkle, flutter=flutter, chime=chime)
for c in S.CAPS:
    blip(c[0] + 0.02)
for t0, k in S.SFX:
    KIND[k](t0)

voice = None
if len(sys.argv) > 3:
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', sys.argv[3], '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True).stdout
    v = np.frombuffer(raw, np.float32).astype(float)[:N]; voice = np.zeros(N); voice[:len(v)] = v
    w = int(0.05 * SR); rms = np.sqrt(np.convolve(voice ** 2, np.ones(w) / w, mode='same'))
    duck = np.where(rms > 0.02, 10 ** (-2 / 20), 1.0); duck = np.convolve(duck, np.ones(w) / w, mode='same')
    vr = np.sqrt(np.mean(voice[voice != 0] ** 2)) + 1e-9; mr = np.sqrt(np.mean(music ** 2)) + 1e-9
    music = music * (vr / mr) * 10 ** (-14 / 20) * duck

mix = (music if voice is not None else 0.8 * music) + sfx + (voice if voice is not None else 0)
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.8
pcm = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
tmp = sys.argv[2] + '.raw.wav'
with wave.open(tmp, 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes(pcm.tobytes())
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-af', 'loudnorm=I=-14:TP=-1.2:LRA=11', '-ar', str(SR), sys.argv[2]], check=True)
__import__('os').remove(tmp)
print('ses hazır:', sys.argv[2])
