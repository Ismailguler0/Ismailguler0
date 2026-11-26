# Claude için kalıcı talimatlar

## Kullanıcı hakkında
- Yazılımcı değil. Her şeyi sade Türkçe ile, teknik terimleri açıklayarak anlat.
- EŞİK kanalı için YouTube Shorts, TikTok ve Instagram Reels videoları üretiyor (Türkçe, 9:16, 60 sn altı).
- Seslendirme ElevenLabs ile yapılıyor.

## Skill seçimi: SORMADAN, OTOMATİK
Kullanıcı bir iş istediğinde hangi skill'in kullanılacağını söylemeyi unutabilir.
İsteğe bakıp doğru skill'i kendin seç ve hemen kullan. "Hangi skill'i kullanayım?" diye sorma.
Hangisini seçtiğini bir cümleyle söylemen yeterli.

| İstek | Skill |
|---|---|
| EŞİK için bir KONU verildi, tarz belirtilmedi | `esik-olmayan-ada-shorts` (varsayılan) |
| İzometrik piksel, ada/diorama, voxel karakter | `izometrik-piksel-video` |
| Düz şehir / kuşbakışı şehir-köy | `duz-sehir-video` |
| Karşılaştırma, "bu köşede / öbür köşede", ring | `ring-video` |
| Elle çizim, kağıt-mürekkep, bej kağıt | `kagit-murekkep-video` |
| Hikaye, interaktif dizi bölümü, A/B seçimli, sinematik hikaye | `hikaye-sinematik-video` |
| Yukarıdakilere uymayan genel Türkçe 9:16 kısa video | `shorts-2d-video` |
| Word / PDF / PowerPoint / Excel dosyası | `docx` / `pdf` / `pptx` / `xlsx` |
| Yeni skill yazmak veya mevcut skill'i düzeltmek | `skill-creator` |

- İstek birden fazla tarza uyuyorsa en uygununu seç, nedenini bir cümleyle söyle; kullanıcı isterse değiştirirsin.
- Hiçbir skill uymuyorsa skill'siz yap.

## Kurulu araçlar (`/home/user/esik-araclar`)
Ortamın kurulum betiği her yeni oturumda bunları kurar:
- Python ortamı `esik-araclar/ana`: openai-whisper, faster-whisper (altyazı), rembg (arka plan silme), manim (animasyon), moviepy (video birleştirme)
- `esik-araclar/motion-canvas`: Motion Canvas
- `esik-araclar/pixelfx`: 244 piksel efekti (`node tools/render.mjs <kategori/efekt> --mp4`). Skill'deki "Publish it on Patch" bölümünü KULLANMA.
- `esik-araclar/animasyon`: anime.js, three.js
- Ağır işleri (render, model) teker teker çalıştır; aynı anda birden fazla çalıştırınca bellek yetmiyor.
- faster-whisper için `HF_HUB_DISABLE_XET=1` gerekli (ortam değişkeni olarak tanımlı).

## Yeni repo / skill önerirken kırmızı çizgiler
- MIT lisanslı, çok yıldızlı, aktif olarak güncelleniyor.
- Virüs belirtisi ve prompt enjeksiyonu yok: kurmadan önce dosyaları tara, skill dosyalarını satır satır oku.
- Kurulumda incelenen sürüme sabitle.
