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
- `pix8.py` – çizim motoru (540×960 tuval, x2 büyütme):
  - Hacim: `ellipsoid` (gövde, kafa, ay, ağaç tepesi), `cylinder` (direk, kule) – ışık yönüne göre rampa + noktalı ton geçişi + gölge tarafında kenar ışığı. `ramp_fill` ile her maskeye kendi ışık haritan.
  - Atmosfer: `glow_layers` (geniş 3 katmanlı parıltı), `halo`, `cloud_band` (kalın, alt kenarı ışık alan bulut), `stars`.
  - Ortam: `sky`/`dgrad`, `skyline`/`draw_skyline` (yanan pencere, kenar ışığı, sis), `sea` (dalga + güneş/ay/pencere yansımaları), `vgrad_rect`, `dither_rect`.
  - Karakter: `godwit` (gerçekçi kıyı kuşu; stand/fly, nefes, kanat fazı), `mirrored` (karakteri sola baktırır), `tiny_bird`, `sparkle`.
  - Rampalar: `R_BIRD`, `R_WING`, `R_WOOD`, `R_STONE`, `R_MOON`. Paletler: `DUSK`, `NIGHT`, `DAWN`.
  - `upscale` (crop ile kamera), `captions`, `pill`, `signature`.
- `render8.py <sahne.py> sheet|frame|video <çıktı>` – kontrol görüntüsü / tek kare / sessiz video.
- `chipaudio.py <sahne.py> <çıktı.wav> [ses.mp3]` – sakin 8-bit müzik + efektler; ses verilirse müziği ~14 dB altında tutar, konuşmada kısar.
- `ornek_kuslar.py` – tam örnek sahne dosyası (15 sn, 4 sahne). Yeni videoda kopyalayıp konuya göre değiştir.
  Sahne dosyası şunları tanımlar: `DUR`, `FPS`, `CAPS`, `SFX`, `SIG_T`, `frame_at(t)`.

Çalışma klasörü: `/home/user/esik-araclar/<konu>/`. Python: `/home/user/esik-araclar/ana/bin/python`.

## Görsel kurallar – çekiciliğin sırrı
Kullanıcı ilk düz renkli denemeyi "piksel ama çekici değil" diye reddetti. Referansı çekici yapan dört şey var;
dördü de her sahnede olmalı:
1. **İnce piksel = detay.** 540×960 tuval. Kamera sadece tam piksel crop ile hareket eder (yakın plan 270×480).
   Yumuşak bulanıklık, döndürme, ölçekleme yok.
2. **Hacimli gölge.** Hiçbir önemli obje düz tek renk olmasın. Ana karakter, direkler, kuleler, ay, kayalar
   ışık yönüne göre 4–6 tonla boyanır; tonlar noktalı geçişle birleşir. Işık yönü sahnedeki güneş/ay ile tutarlı
   olsun (gün batımı soldaysa sol yüzler turuncu, sağ yüzler mor).
3. **Kenar ışığı.** Gölge tarafındaki kenarda 1 px parlak çizgi (gün batımında sıcak `RIM`, gecede soğuk mavi-beyaz).
   Silüet binaların üst kenarında da ince ışık çizgisi.
4. **Atmosfer.** Güneş/ay/lamba/pencere etrafında `glow_layers`; ufukta sis; kalın, alt kenarı ışık alan bulutlar;
   suda ışık yansımaları. Ön planda en az bir büyük sıcak ışık kaynağı (pencere, fener).

Ayrıca:
- **Gerçekçi karakter:** gerçek hayvanın/objenin oranlarını kullan (ince boyun, uzun bacak, tüy deseni, gözde parlama
  pikseli). Önce karakteri boş gökyüzünde büyük çizip `frame` ile incele, "kardan adam" gibi üst üste toplar
  görünüyorsa oranları düzelt; sonra sahneye koy.
- **Ana karakter büyük:** genişliğin en az 1/5'i; yakın planda daha da büyük.
- **Derinlik:** uzak silüet (pembe-mor, sisli) → orta silüet (yanan pencereler) → ön plan (hacimli, detaylı).
- **Hep hareket:** bulut, dalga, pencere titremesi, yıldız, fener ışığı, karakterin nefesi/kafa hareketi.
- Karakter hikâyede anlamlı yöne baksın (varışta güneşe doğru gibi) – gerekirse `mirrored`.
- Ana görseller son karede y 200–1300; alt kısım koyu zemin (altyazı ve imza için).
- 3–5 sahne, düz kesme + whoosh. Bilgiler ekranda öğe olarak (sayaç hapları, parıltı).

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
