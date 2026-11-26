#!/usr/bin/env python3
"""Sahne dosyasını çizer.
  render8.py <sahne.py> sheet <çıktı.png> [t1,t2,...]   -> 3x3 kontrol görüntüsü
  render8.py <sahne.py> frame <çıktı.png> <t>
  render8.py <sahne.py> video <çıktı.mp4>               -> sessiz video (30 fps, libx264)
Sahne dosyası DUR, FPS ve frame_at(t) -> 1080x1920 RGB uint8 tanımlar.
"""
import importlib.util, os, subprocess, sys
import numpy as np, cv2
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('sahne', sys.argv[1])
S = importlib.util.module_from_spec(spec); sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[1]))); spec.loader.exec_module(S)
mode, out = sys.argv[2], sys.argv[3]
FPS = getattr(S, 'FPS', 30); NF = int(round(S.DUR * FPS))

if mode == 'sheet':
    ts = [float(x) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 else list(np.linspace(0.5, S.DUR - 0.3, 9))
    tiles = [cv2.resize(S.frame_at(t), (360, 640), interpolation=cv2.INTER_AREA) for t in ts[:9]]
    while len(tiles) < 9:
        tiles.append(np.zeros_like(tiles[0]))
    Image.fromarray(np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, 9, 3)])).save(out)
elif mode == 'frame':
    Image.fromarray(S.frame_at(float(sys.argv[4]))).save(out)
elif mode == 'video':
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                          '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(NF):
        p.stdin.write(S.frame_at(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    print('video hazır:', out)
