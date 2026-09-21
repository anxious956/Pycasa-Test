# Rapor görselleri

`scripts/make_report_gifs.py` ve `scripts/make_report_figs.py` ile üretildi.
Hepsi HC004 default datasının ilk 61 frame'i (0-60) kullanılarak hazırlandı.

## Animasyonlar

Her görsel üç formatta var:

| Format | Ne zaman kullan | Boyut |
|---|---|---|
| `.mp4` | **PowerPoint** ve sunumlar. H.264, 896x716, 61 kare | 1.7-3.2 MB |
| `.gif` | GitHub, markdown, e-posta. 576x460, 31 kare | ~4.5 MB |
| `.png` | Animasyon koyamadığın yer. Ortadaki kare | ~0.3 MB |

PowerPoint'e MP4 koy, GIF değil. Daha küçük dosya, iki katı kare, daha net görüntü.
Slayda sürükleyip bırak, sonra Oynatma sekmesinden Otomatik ve Döngü seçeneklerini işaretle.

### İçerikler

| Dosya | İçerik | Rapor bölümü |
|---|---|---|
| `01_gt_only` | Sadece gerçek etiketler (yeşil kutular) | Adım 2 |
| `02_gt_vs_yolo26` | Gerçek etiketler + YOLO26 tespitleri | Adım 3 |
| `03_sort_gt` | Gerçek etiketler üstünde SORT yörüngeleri | Adım 5 |
| `04_jpdaf_gt` | Gerçek etiketler üstünde JPDAF yörüngeleri | Adım 5 |
| `05_full` | Hepsi bir arada: iki kutu seti + iki yörünge seti | Adım 6 |

## Durgun grafikler (PNG)

| Dosya | İçerik |
|---|---|
| `06_radar_gt` | Sekiz kinematik parametrenin radar grafiği, gerçek etiketler |
| `06_radar_yolo26` | Aynısı, YOLO26 tespitleri üstünde |
| `07_yogunluk_gt` | Parametre çiftlerinin yoğunluk dağılımı, gerçek etiketler |
| `07_yogunluk_yolo26` | Aynısı, YOLO26 tespitleri üstünde |
| `08_katmanlar` | Orijinal, gri tonlama, ikili ve normalize görüntü yan yana |

## Renk anahtarı

- Yeşil kutu: gerçek etiket
- Kırmızı kutu: YOLO26 tespiti
- Mavi iz: gerçek etiketler üstünde çıkarılan yörünge
- Turuncu iz: YOLO26 tespitleri üstünde çıkarılan yörünge

## Yeniden üretmek için

```
call setup_env.bat
python scripts/make_report_gifs.py
python scripts/make_report_figs.py
```
