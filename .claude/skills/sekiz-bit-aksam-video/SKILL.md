---
name: sekiz-bit-aksam-video
description: EŞİK kanalı için '8-bit akşam' tarzında Türkçe 9:16 kısa video (Shorts/Reels/TikTok) yapar - yandan bakış piksel sahneler, mor-pembe-turuncu noktalı (dither) akşam gökyüzü, katmanlı şehir silüetleri, yanan pencereler ve etraflarında noktalı parıltılar, çizgi bulutlar. Kullanıcı '8-bit', 'piksel akşam', 'gün batımı piksel', 'retro piksel', 'şu örnekteki gibi (roketli piksel video)' derse ya da piksel tarzı isteyip izometrik/ada demezse MUTLAKA bunu kullan. İzometrik ada/diorama istenirse izometrik-piksel-video kullanılır.
---

# 8-bit akşam – 9:16 kısa video

Kullanıcının beğendiği referans: yandan bakış, iri pikselli bir akşam sahnesi (roket rampası, şehir silüeti,
ışıklı pencere, mor-turuncu gökyüzü, noktalı parıltılar). Bu tarzı **kendi orijinal sahnelerimizle** kullan;
referans videonun roketini, sahnesini veya yazılarını kopyalama. Her zaman Türkçe çalış.

Kanal formatı aynen kalır: tek ekran, alt yazı hapı, en sonda EŞİK imzası. Bölünmüş ekran yapma.

## Ses
- Seslendirmeyi kullanıcı yapar ve mp3 yükler. ElevenLabs ile ses üretme.
- Önce metni yaz: ilk cümle merak uyandıran bir kanca, kısa cümleler, "..." ile duraklar, sayılar yazıyla.
  ElevenLabs metnini tek kod bloğunda ver.
- Kullanıcı "deneme/test" isterse seslendirmesiz yap: bilgiler ekranda yazı, arkada müzik ve efekt.
- Ses gelince: sessizlikleri kırp (-35 dB, ≥0.25 sn), highpass 70, hafif kompresör, loudnorm I=-16.
  Altyazıları silencedetect (-28 dB, d=0.08) ile bulunan konuşma parçalarına yerleştir.

## Hazır araçlar (`scripts/`)
Bu dosyaları baştan yazma, kullan:
- `pix8.py` – çizim motoru: `dgrad`/`sky` (noktalı gradyan), `halo` (noktalı parıltı), `skyline`/`draw_skyline`
  (yanan pencereli silüet), `streaks` (çizgi bulut), `sea` (dalga + güneş yansıması), `stars`, `disc`, `rect`,
  `dither_rect`, `godwit`/`tiny_bird` (örnek karakterler), `sparkle`, `upscale` (crop ile kamera),
  `captions`, `pill`, `signature` (EŞİK imzası). Paletler: `DUSK`, `NIGHT`, `DAWN`.
- `render8.py <sahne.py> sheet|frame|video <çıktı>` – kontrol görüntüsü veya sessiz video.
- `chipaudio.py <sahne.py> <çıktı.wav> [ses.mp3]` – sakin 8-bit müzik + efektler; ses verilirse müziği ~14 dB altında tutar ve konuşmada kısar.
- `ornek_kuslar.py` – tam örnek sahne dosyası (15 sn). Yeni videoda bunu çalışma klasörüne kopyalayıp konuya göre değiştir.
  Sahne dosyası şunları tanımlar: `DUR`, `FPS`, `CAPS`, `SFX`, `SIG_T`, `frame_at(t)`.

Çalışma klasörü: `/home/user/esik-araclar/<konu>/`. Python: `/home/user/esik-araclar/ana/bin/python`.
Sahne dosyası `from pix8 import *` yapar; `render8.py` scripts klasörünü yola ekler.

## Görsel kurallar (tarzın özü)
- **Piksel kuralı:** her şey 270×480 tuvalde çizilir, x4 en yakın komşu büyütme. Kamera sadece tam piksel
  crop ile hareket eder (z=2 için 135×240 pencere). Yumuşak bulanıklık, döndürme, ölçekleme yok.
- **Gökyüzü:** üstte koyu mor → pembe → ufukta turuncu; bantlar arası Bayer noktalı geçiş. Konu gece ise `NIGHT`
  (yıldızlar + ay parıltısı), sabah ise `DAWN`.
- **Derinlik katmanları:** uzak silüet (pembe-mor, az pencere) → orta silüet (koyu mor, daha çok yanan pencere,
  üst kenarda ince sıcak ışık çizgisi) → ön plan (en koyu, büyük ve detaylı obje). En az üç katman.
- **Işık:** her sıcak ışığın (pencere, lamba, güneş, alev) etrafında `halo` ile noktalı parıltı. Ön planda en az
  bir büyük, yanan pencere/lamba olsun – sahnenin sıcaklığı buradan gelir.
- **Kenar ışığı:** ön plan objelerinin üst kenarına gün batımı rengi (`RIM`) 1 px çizgi.
- **Ana karakter/obje büyük:** sahnenin yıldızı ekran genişliğinin en az 1/5'i kadar olsun; küçük kalırsa ölçeği büyüt
  ya da z=2 crop kullan.
- **Hep hareket:** bulutlar kayar, dalgalar akar, pencereler ara ara titrer, yıldızlar parlar, karakter nefes alır.
- Ana görseller ekranın üst ve orta kısmında (son kare y 200–1300); altyazılar için alt kısım koyu zemin olsun.
- Sahne geçişi: düz kesme + "whoosh" sesi. 3–5 sahne, her biri bir bilgiyi gösterir.
- Bilgileri ekranda öğe olarak göster: sayaçlar (`pill` ile "Gün [7]", "[8.630] km"), etiketler, parıltı.

## Altyazı ve imza
- Net yazı (büyütmeden sonra): koyu yuvarlak hap (30,26,26, %84), Poppins Medium 46 px, sıcak beyaz; anahtar kelime
  turuncu (255,150,60) – metinde `[köşeli parantez]` ile işaretle. Merkez y≈1608.
- Ekranda sayılar rakamla (13.560), isimler gerçek yazılışıyla.
- **EŞİK imzası** (her videoda): `signature(frame, t, SIG_T)` – Lora 92 px krem, harf arası 34 px, y≈1490, altında
  5 px çizgi (y≈1572) ortadan büyür. Bitişten ~2.4 sn önce başlar. İmza açıkken altyazıyı y≈1350'ye al.

## Ses tasarımı
- Müzik: sakin 8-bit, A minör pentatonik, ~92 BPM (`MUSIC = dict(bpm=..., root=...)` ile değiştirilebilir).
- Efektler `SFX` listesinde: `chirp` (kuş), `whoosh` (kesme), `tick` (sayaç), `sparkle` (varış/ödül),
  `flutter` (kanat), `chime` (imza), `blip` (yazı belirmesi – altyazılarda otomatik). Her efekti olayın tam karesine koy.
- Son karışım loudnorm I=-14, TP=-1.2.

## İş akışı
1. Konuyu web'de doğrula (sayı, tarih). Emin olunamayan bilgiyi metne koyma.
2. Metin + ElevenLabs metni (test ise atla).
3. `ornek_kuslar.py`'yi kopyala, sahneleri konuya göre yeniden tasarla.
4. `render8.py ... sheet` ile 9 karelik kontrol görüntüsü al ve bak: karakter yeterince büyük mü, yazılar bir şeyle
   çakışıyor mu, imza okunuyor mu? Karakterlere `frame` ile büyük boyutta bak. Düzelt.
5. `render8.py ... video` → `chipaudio.py` → birleştir:
   `ffmpeg -i video.mp4 -i ses.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart son.mp4`
6. Ağır işleri teker teker çalıştır (bellek sınırlı).
7. SendUserFile ile gönder; kısa Türkçe özet: süre, sahne sayısı, sesle ne yapıldı, müzik seviyesi, düzeltme teklifi.
