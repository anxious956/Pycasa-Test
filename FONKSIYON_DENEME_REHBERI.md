# pycasa'nın bütün fonksiyonlarını baştan sona deneme rehberi

IPython'da sırayla yapıştır. Her bloğun altında ne görmen gerektiği yazıyor.
Sayılar benim ölçtüklerim, sende birkaç birim oynayabilir.

Hızlı olsun diye çoğu yerde **61 frame** kullanıyoruz (`final_frame=60`).
Sebebi: moving-cells ilk 20 frame'i arka plan eğitimine harcıyor, kinematik hesap
da track başına 30 nokta istiyor. Daha azıyla bu iki grup çalışmaz.

---

## 0. Başlangıç

PowerShell kullan (Windows 11 varsayılanı). Proje klasöründe:

```bash
. .\setup_env.ps1
```

Sonra IPython'u başlat:

```bash
python -m IPython
```

`ipython` komutu doğrudan çalışmıyor, PATH'te değil. `python -m IPython` her zaman çalışır.

cmd kullanıyorsan ortam ayarı için `call setup_env.bat`, gerisi aynı.

---

## 1. io — veri yükleme

### 1.1 Default data

```python
import pycasa as pc, copy, numpy as np
self = pc.io.load_default_data()
```
Beklenen: `um_per_px=0.24`, `volume_ml=2.2`, `chamber_depth_um=20.7` otomatik ayarlanır.
`frames=101/901, size=1280x1024, fps=30.00`, GT'de 900 frame / 81179 etiket.

### 1.2 Frame aralığı ve parametre ezme

```python
s = pc.io.load_default_data(final_frame=60)
print(s.get_video()["number_frame_used"])
```
Beklenen: `61`

```python
s2 = pc.io.load_default_data(initial_frame=10, final_frame=20, verbose=False)
print(s2.get_video()["number_frame_used"])
```
Beklenen: `11`

```python
s3 = pc.io.load_default_data(final_frame=5, um_per_px=0.5, volume_ml=3, chamber_depth_um=10, verbose=False)
print({k: s3.get_meta()[k] for k in ("um_per_px","volume_ml","chamber_depth_um")})
```
Beklenen: `{'um_per_px': 0.5, 'volume_ml': 3.0, 'chamber_depth_um': 10.0}`

```python
s4 = pc.io.load_default_data(final_frame=5, sampling_rate=15, magnification="20x", verbose=False)
print(s4.get_meta()["sampling_rate"], s4.get_meta()["magnification"])
```
Beklenen: `15.0 20x`

### 1.3 Kendi videon (load_video)

```python
import os
DATA = os.path.join(os.environ["PYCASA_DATA"], "sys-casa/rawdata/sub-HC004/ses-01")
VIDEO = f"{DATA}/sys-casa_sub-HC004_ses-01_run-005_video.avi"
GT = f"{DATA}/sys-casa_sub-HC004_ses-01_run-005_gt"
v = pc.io.load_video(VIDEO, groundtruth_detections_path=GT, final_frame=60,
                     um_per_px=0.24, volume_ml=2.2, chamber_depth_um=20.7, verbose=False)
print(v.get_video()["number_frame_used"], "frame,", len(v.get_groundtruth()), "GT frame")
```
Beklenen: `61 frame, 900 GT frame`

```python
try:
    pc.io.load_video("C:/yok/x.avi", verbose=False)
except Exception as e:
    print(type(e).__name__, e)
```
Beklenen: `FileNotFoundError Video file does not exist: ...`

### 1.4 Bilinen sorun: wrapper'da eksik parametre

```python
try:
    pc.Casa().io.load_default_data(final_frame=5, volume_ml=2.2, verbose=False)
except TypeError as e:
    print("BULGU:", e)
```
Beklenen: `unexpected keyword argument 'volume_ml'`.
Modül fonksiyonunda var ama session wrapper'ında yok.

---

## 2. Casa — getter, setter, info

```python
self = pc.io.load_default_data(final_frame=60)
self.info()
```
Beklenen: oturumun yapılandırılmış özeti.

```python
print(list(self.get_casa().keys()))
print(sorted(self.get_meta().keys()))
print(list(self.get_video().keys()))
```
Beklenen sırasıyla: `['meta','video','detections','tracks','motility','assessment']`,
11 meta anahtarı, `['path','initial_frame','final_frame','number_frame_used','original_video']`

```python
print("GT frame:", len(self.get_groundtruth()))
print("GT track:", self.get_groundtruth_tracks())
print("detection:", self.get_detections())
print("track:", self.get_tracks())
print("motility:", self.get_motility())
print("assessment:", self.get_assessment())
```
Beklenen: GT 900, gerisi boş. Default datada GT track yok.

```python
c = self.copy()
print("yeni nesne:", c is not self)
print(self.set_um_per_px(0.3).get_meta()["um_per_px"])
print(self.set_volume_ml(1.5).get_meta()["volume_ml"])
print(self.set_chamber_depth_um(10).get_meta()["chamber_depth_um"])
print(self.set_dilution_factor(2).get_meta()["dilution_factor"])
```
Beklenen: `True`, sonra `0.3 1.5 10.0 2.0`

```python
for f, v in [(self.set_um_per_px, -1), (self.set_volume_ml, "abc"), (self.set_chamber_depth_um, 0)]:
    try: f(v)
    except Exception as e: print(type(e).__name__, ":", e)
```
Beklenen: üçü de düzgün `ValueError` / `TypeError` veriyor.

Değerleri geri al:

```python
self = pc.io.load_default_data(final_frame=60)
```

---

## 3. preprocessing

### 3.1 Grayscale

```python
p = pc.io.load_default_data(final_frame=60, verbose=False)
p.preprocessing.grayscale()
print([k for k in p.get_video() if k.endswith("video")])
```
Beklenen: `['original_video', 'grayscale_video']`

`overwrite=True` orijinali değiştirir:

```python
o = pc.io.load_default_data(final_frame=10, verbose=False)
o.preprocessing.grayscale(overwrite=True)
print(np.asarray(o.get_video()["original_video"]).shape)
```
Beklenen: `(11, 1024, 1280)` — renk kanalı gitti.

### 3.2 Binarization (6 yöntem)

```python
for m in ["otsu", "adaptive_gaussian", "adaptive_mean", "niblack", "sauvola", "urbano"]:
    getattr(p.preprocessing.binarization, m)()
    b = np.asarray(p.get_video()["binary_video"])
    print(f"{m:20s} dtype={b.dtype} degerler={np.unique(b[0])[:3]}")
```
Beklenen: altısı da çalışır, ikili görüntü üretir. `urbano` en yavaşı (~10 sn).

```python
try:
    p.preprocessing.binarization.adaptive_gaussian(block_size=4)
except Exception as e:
    print(type(e).__name__, ":", e)
```
Beklenen: `block_size must be an odd integer >= 3` — doğrulama çalışıyor.

### 3.3 Normalization (6 yöntem)

```python
for m in ["clahe", "hist_equal", "log", "median", "min_max", "z_score"]:
    getattr(p.preprocessing.normalization, m)()
    n = np.asarray(p.get_video()["normalized_video"])
    print(f"{m:12s} dtype={n.dtype} min={n.min():.2f} max={n.max():.2f}")
```
Beklenen: `z_score` float32, diğerleri uint8.

### 3.4 Zincirleme

```python
z = pc.io.load_default_data(final_frame=30, verbose=False)
z.preprocessing.grayscale()
z.preprocessing.normalization.clahe()
z.preprocessing.binarization.otsu()
print([k for k in z.get_video() if k.endswith("video")])
```
Beklenen: dördü birden listede.

---

## 4. detection — 4 farklı aile

Not: her yeni detector öncekini siler, uyarı basar. Sonucu `deepcopy` ile sakla.

```python
def dene(fn, **kw):
    s = pc.io.load_default_data(final_frame=60, verbose=False)
    fn(s, **kw)
    s.assessment.evaluate_detections()
    a = copy.deepcopy(s.get_assessment()["detection"])
    print(f"  tp={a['tp']:5d} fp={a['fp']:5d} fn={a['fn']:5d} P={a['precision']:6.2f} R={a['recall']:6.2f} F1={a['F1']:6.2f}")
    return s, a
```

### 4.1 YOLO26

```python
print("yolo26 varsayilan (conf=0.15)")
s_y26, a_y26 = dene(lambda s: s.detection.yolo(yolo_model="yolo26"))
```
Beklenen: recall ~%99, precision ~%63, F1 ~%77.

```python
print("conf=0.5"); dene(lambda s: s.detection.yolo(yolo_model="yolo26", conf=0.5))
print("conf=0.01"); dene(lambda s: s.detection.yolo(yolo_model="yolo26", conf=0.01))
```
Beklenen: eşik yükselince precision artar, düşünce FP patlar (F1 ~%51'e iner).

Detection satır formatı:

```python
print(np.asarray(s_y26.get_detections()["0"])[:2].tolist())
```
Beklenen: `[['0', '0.910138', '0.828910', '0.037355', '0.046788'], ...]`
Yani YOLO formatı: sınıf, merkez x, merkez y, genişlik, yükseklik (normalize).

### 4.2 YOLOv5

```python
print("yolov5"); dene(lambda s: s.detection.yolo(yolo_model="yolov5"))
```
Beklenen: YOLO26'dan daha dengeli, precision daha yüksek, recall daha düşük.

Hatalı girdiler:

```python
for kw in [dict(yolo_model="yolo99"), dict(weights="C:/yok.pt")]:
    try: pc.io.load_default_data(final_frame=5, verbose=False).detection.yolo(**kw)
    except Exception as e: print(type(e).__name__, ":", str(e)[:90])
```
Beklenen: ikisi de net hata veriyor.

### 4.3 Moving cells (4 yöntem)

```python
for m in ["cv-gmg", "cv-mog", "cv-mog2", "gm"]:
    print(m); dene(lambda s, mm=m: s.detection.detect_moving_cells(method=mm))
```
Beklenen sıralama: `gm` en iyi (F1 ~%84), `cv-mog` iyi, `cv-mog2` çok FP üretiyor,
`cv-gmg` en zayıf. Hepsi ilk 20 frame'i eğitime harcıyor.

```python
print("gm + low_memory"); dene(lambda s: s.detection.detect_moving_cells(method="gm", low_memory=True))
```
Beklenen: `gm` ile birebir aynı sonuç, daha az bellek.

### 4.4 Digital washing ve Urbano

```python
print("digital_washing"); dene(lambda s: s.detection.digital_washing())
```
Beklenen: F1 ~%84. Yavaş (~90 sn).
`n_jobs=4` Windows'ta `BrokenProcessPool` verebilir, `n_jobs=1` kal.

```python
print("digital_washing sikilastirilmis")
dene(lambda s: s.detection.digital_washing(motion_threshold=5, blob_min_pixel_area=30))
```
Beklenen: precision ~%95'e çıkar, recall düşer.

```python
print("urbano"); dene(lambda s: s.detection.urbano_detection())
print("urbano ayarli"); dene(lambda s: s.detection.urbano_detection(blob_min_pixel_area=10, log_size=7))
```
Beklenen: F1 ~%83.

### 4.5 Overwrite kuralı ve assessment eşiği

```python
ov = pc.io.load_default_data(final_frame=30, verbose=False)
ov.detection.urbano_detection()
ov.detection.detect_moving_cells()
```
Beklenen: `Warning: Previous detection result overwritten (urbano_detection -> moving_cells).`

```python
s_y26.assessment.evaluate_detections(match_min_distance_pixel=10)
print(s_y26.get_assessment()["detection"])
```
Beklenen: eşleştirme mesafesi 20'den 10'a inince TP düşer, FP artar.

---

## 5. tracking — 3 tracker

```python
def izle(fn, **kw):
    s = pc.io.load_default_data(final_frame=60, verbose=False)
    fn(s)
    tr = s.get_tracks(); b = list(tr)[0]
    for src in tr[b]:
        n = len(tr[b][src]); L = sum(len(t) for t in tr[b][src].values())/n
        print(f"  {b}/{src}: {n} track, ortalama uzunluk {L:.1f}")
    return s
```

### 5.1 SORT

```python
print("sort varsayilan"); t_sort = izle(lambda s: s.tracking.sort())
```
Beklenen: `Warning: No detections found, tracking will only run on GT`, ~114 track.

```python
print("sort gevsek"); izle(lambda s: s.tracking.sort(max_age=5, min_hits=1, iou_threshold=0.3))
print("sort initial_frame=10"); izle(lambda s: s.tracking.sort(initial_frame=10))
```
Beklenen: gevşek ayarla track sayısı artar (~168), kısa parçalı track'ler çoğalır.

### 5.2 JPDAF

```python
print("jpdaf"); t_jp = izle(lambda s: s.tracking.jpdaf())
```
Beklenen: ~115 track, SORT'tan uzun track'ler. Yavaş (~10 frame/s).

```python
print("jpdaf ayarli"); izle(lambda s: s.tracking.jpdaf(frame_rate=60, p_delete=0.3, sigma_n_um=1.0))
print("jpdaf dar kapi"); izle(lambda s: s.tracking.jpdaf(position_gate=5, velocity_gate_um=20, detection_probability=0.9))
```
Beklenen: dar kapı track sayısını düşürür (~81).

### 5.3 DeepSORT

```python
print("deepsort"); izle(lambda s: s.tracking.deepsort())
print("deepsort ayarli"); izle(lambda s: s.tracking.deepsort(max_age=10, n_init=2, max_iou_distance=0.5))
```
Beklenen: ~127 track. İlk çalıştırmada `~/.pycasa/deepsort` reposunu ister.

### 5.4 Detection üstünde tracking

```python
d = pc.io.load_default_data(final_frame=60, verbose=False)
d.detection.yolo(yolo_model="yolo26")
d.tracking.sort()
tr = d.get_tracks()["sort"]
print({k: len(v) for k, v in tr.items()})
```
Beklenen: `{'groundtruth': 114, 'yolo26': 239}` — iki kaynak birden.

```python
d2 = pc.io.load_default_data(final_frame=60, verbose=False)
d2.detection.yolo(yolo_model="yolo26")
d2.tracking.sort(skip_gt=True)
print(list(d2.get_tracks()["sort"]))
```
Beklenen: `['yolo26']` — GT atlandı.

### 5.5 Tracking overwrite

```python
w = pc.io.load_default_data(final_frame=30, verbose=False)
w.tracking.sort(); w.tracking.jpdaf()
print("backend:", list(w.get_tracks()))
print("sort hala var mi:", w.get_tracks(backend="sort"))
```
Beklenen: `['jpdaf']` ve `{}` — SORT silindi.

### 5.6 Track değerlendirmesi

```python
d.assessment.evaluate_tracks()
print(list(d.get_assessment()["tracking"]))
```
Beklenen: ekrana iki matris basar, GT track'leri ile yolo26 track'lerini karşılaştırır.

```
MOTA (%)  [row = ground-truth role, col = prediction role]
                 | sort:groundtruth |      sort:yolo26
sort:groundtruth |                - |            51.98
sort:yolo26      |            66.68 |                -

IDF1 (%)  [symmetric]
sort:groundtruth |                - |            76.94
```

Sözlük anahtarları: `['sources','reference','track_counts','match_min_distance_pixel','pairs','skipped']`.
Dikkat: anahtar `tracking`, `tracks` değil.

```python
tek = pc.io.load_default_data(final_frame=30, verbose=False)
tek.tracking.sort(); tek.assessment.evaluate_tracks()
print(tek.get_assessment()["tracking"]["reason"])
```
Beklenen: `need_at_least_two_track_sets` — tek kaynakla düzgün atlıyor.

---

## 6. motility — kinematik ve CASA

```python
m = pc.io.load_default_data(final_frame=60, verbose=False)
m.tracking.sort()
m.motility.kinematic_parameters()
```
Beklenen: 3 uyarı (30 fps düşük, SCA varsayılanları) ve VCL/VSL/VAP/LIN/ALH/WOB/STR/MAD özeti.

```python
k = m.get_motility()["kinematic_parameters"]["groundtruth"]
print("track sayisi:", len(k))
print("parametreler:", list(next(iter(k.values()))))
print("ornek track:", {kk: round(vv[0], 2) for kk, vv in list(next(iter(k.values())).items())[:8]})
```
Beklenen: `['VCL','VSL','VAP','LIN','ALH','WOB','STR','MAD','frame_ranges']`

```python
m.motility.casa_parameters()
c = copy.deepcopy(m.get_motility()["casa_parameters"]["groundtruth"])
print(c["grades"]); print("motil %:", c["percent_motile"], "| konsantrasyon:", c["concentration_M_per_ml"])
```
Beklenen: rapid ~%48, slow ~%29, non-prog ~%3, immotile ~%21.

### 6.1 Kinematik parametre varyantları

```python
def kin(**kw):
    s = pc.io.load_default_data(final_frame=60, verbose=False)
    s.tracking.sort(verbose=False)
    s.motility.kinematic_parameters(verbose=False, **kw)
    s.motility.casa_parameters(verbose=False)
    print(" ", s.get_motility()["casa_parameters"]["groundtruth"]["grades"])

print("varsayilan");      kin()
print("kucuk pencere");   kin(window_size=15, overlap=0.5, smoothing_window=3, denoise_window=1, min_frame_rate_warn=0)
print("frame_rate=60");   kin(frame_rate=60)
print("piksel birimi");   kin(conversion_required=False)
```
Beklenen: `frame_rate=60` hızları iki katına çıkarır, rapid ~%80'e fırlar.
Bu, fps'yi yanlış vermenin sonucu ne kadar değiştirdiğini gösterir.

### 6.2 CASA eşik varyantları

```python
def casa(**kw):
    s = pc.io.load_default_data(final_frame=60, verbose=False)
    s.tracking.sort(verbose=False); s.motility.kinematic_parameters(verbose=False)
    s.motility.casa_parameters(verbose=False, **kw)
    print(" ", s.get_motility()["casa_parameters"]["groundtruth"]["grades"])

print("VCL varsayilan"); casa()
print("VAP + dusuk esik"); casa(velocity_metric="VAP", rapid_threshold=25, immotile_threshold=10, progressive_str_threshold=0.5)
print("VSL");             casa(velocity_metric="VSL")
print("hacim/derinlik/dilusyon"); casa(volume_ml=1, chamber_depth_um=10, dilution_factor=2)
```
Beklenen: VSL en katı metrik, immotile ~%45'e çıkar. Hacim ve derinlik
oranları değiştirmez, sadece konsantrasyonu etkiler.

### 6.3 Deneysel parametreler

```python
e = pc.io.load_default_data(final_frame=60, verbose=False)
e.tracking.sort(verbose=False); e.motility.kinematic_parameters(verbose=False)
e.motility.casa_parameters(experimental_parameters=True, n_subpopulations=2, verbose=False)
print(list(e.get_motility()["casa_parameters"]["groundtruth"]))
```
Beklenen: normal anahtarlara ek olarak hiperaktivasyon ve alt popülasyon alanları.

### 6.4 Bilinen sorunlar

```python
bos = pc.io.load_default_data(final_frame=60, verbose=False)
bos.motility.kinematic_parameters()
print("BULGU, sessizce bos dondu:", bos.get_motility())
```
Beklenen: `{'kinematic_parameters': {}}`. Tracking yapılmadı ama hata da uyarı da yok.

```python
for ov in (1.5, -0.5, 5.0):
    s = pc.io.load_default_data(final_frame=60, verbose=False)
    s.tracking.sort(verbose=False)
    s.motility.kinematic_parameters(overlap=ov, verbose=False)
    t0 = next(iter(s.get_motility()["kinematic_parameters"]["groundtruth"].values()))
    print(f"BULGU overlap={ov}: hata yok, {len(t0['VCL'])} pencere")
```
Beklenen: üçü de kabul ediliyor. `overlap` 0 ile 1 arasında olmalı ama doğrulanmıyor.

---

## 7. visualization — 5 fonksiyon

Bu fonksiyonlar pencere açar. Devam etmek için pencereyi kapat.

```python
vis = pc.io.load_default_data(final_frame=60, verbose=False)
vis.preprocessing.grayscale(); vis.preprocessing.binarization.otsu()
vis.preprocessing.normalization.clahe()
vis.detection.yolo(yolo_model="yolo26"); vis.tracking.sort()
vis.motility.kinematic_parameters(verbose=False); vis.motility.casa_parameters(verbose=False)
```

### 7.1 plot_frame

```python
vis.visualization.plot_frame("original", frame_index=5)
```

```python
vis.visualization.plot_frame(["original", "grayscale", "binarized", "normalized"], frame_index=5)
```
Beklenen: dört katman yan yana.

```python
try: pc.io.load_default_data(final_frame=5, verbose=False).visualization.plot_frame("binarized")
except ValueError as e: print("dogru hata:", e)
```

### 7.2 timelapse

```python
vis.visualization.timelapse()
```
Beklenen: GT kutuları yeşil, kırmızı kutular yolo26.

```python
vis.visualization.timelapse(video_type="grayscale+binarized", show_tracks=True, show_track_ids=True,
                            detection_color="blue", groundtruth_color="red",
                            track_colors={"groundtruth": "yellow", "detection": "orange"}, max_track_gap=5)
```
Beklenen: iki katman yan yana, track çizgileri ve ID etiketleri.

### 7.3 motility_radar

```python
vis.visualization.motility_radar()
```
Beklenen: 8 kinematik parametrenin radar grafiği.

```python
vis.visualization.motility_radar(show_legend=False, show_text=False)
```

### 7.4 motility_density_scatter

```python
vis.visualization.motility_density_scatter()
```
Beklenen: parametre çiftlerinin yoğunluk dağılımı.

### 7.5 interactive_motility_calculator

```python
vis.visualization.interactive_motility_calculator()
```
Beklenen: track seçip parametrelerini canlı inceleyebildiğin pencere.

```python
print(vis.get_meta()["last_visualization"])
```
Beklenen: en son açılan görselin kaydı.

---

## 8. Hepsini otomatik çalıştırmak istersen

```bash
python scripts/step7_full_api_test.py
```

140 testi çalıştırır, `outputs/step7_api_test_report.md` dosyasına tablo yazar.
Tek bölüm için: `python scripts/step7_full_api_test.py tracking`

---

## Akılda tutulacak 5 şey

1. Sonuçları `copy.deepcopy()` ile sakla. Getter'lar canlı sözlük döndürüyor.
2. YOLOv5 ve YOLO26'yı aynı oturumda çalıştırma, sonuç değişiyor.
3. Yeni detector öncekini, yeni tracker öncekini siler.
4. Kinematik hesap track başına 30 nokta ister, az frame'le çalışmaz.
5. `overlap` 0 ile 1 arasında olmalı, kütüphane kontrol etmiyor.
