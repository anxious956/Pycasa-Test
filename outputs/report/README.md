# Rapor görselleri

`scripts/make_report_gifs.py` ve `scripts/make_report_figs.py` ile üretildi.
Hepsi HC004 default datasının ilk 61 frame'i (0-60) kullanılarak hazırlandı.

## Animasyonlar (GIF, 31 kare)

| Dosya | İçerik | Rapor bölümü |
|---|---|---|
| `01_gt_only` | Sadece gerçek etiketler (yeşil kutular) | Adım 2 |
| `02_gt_vs_yolo26` | Gerçek etiketler + YOLO26 tespitleri | Adım 3 |
| `03_sort_gt` | Gerçek etiketler üstünde SORT yörüngeleri | Adım 5 |
| `04_jpdaf_gt` | Gerçek etiketler üstünde JPDAF yörüngeleri | Adım 5 |
| `05_full` | Hepsi bir arada: iki kutu seti + iki yörünge seti | Adım 6 |

Her GIF'in yanında aynı isimde bir PNG var, ortadaki kareyi içeriyor.
Rapora animasyon koyamazsan PNG'yi kullan.

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
