# Baştan sona kurulum ve komutlar

Kendi makinende sıfırdan tekrarlamak için. Sırayla uygula.
`<KULLANICI>` yerine kendi Windows kullanıcı adını yaz.

---

## BÖLÜM 1 — Kurulum (bir kez)

### 1.1 Python kontrolü (3.10 veya üstü gerekli)

```bash
python --version
```

### 1.2 pycasa kurulumu

```bash
pip install git+https://github.com/DFL-KamLab/pycasa.git
```

### 1.3 Eksik bağımlılıklar

pycasa sadece temel paketlerle geliyor. Hepsini kur:

```bash
pip install scikit-image scipy motmetrics huggingface_hub torch torchvision ultralytics matplotlib pandas pillow psutil PyYAML requests imageio ipython
```

### 1.4 SORT tracker (ayrı paket, extra'lara dahil değil)

```bash
pip install git+https://github.com/DFL-KamLab/sort.git
```

### 1.5 YOLOv5 reposu (pycasa bunu klonlamak için soru soruyor, kendimiz halledelim)

```bash
git clone --depth 1 https://github.com/ultralytics/yolov5.git %USERPROFILE%\.pycasa\yolov5
```

### 1.6 DeepSORT reposu (deepsort tracker'ı deneyeceksen)

```bash
git clone --depth 1 https://github.com/nwojke/deep_sort.git %USERPROFILE%\.pycasa\deepsort
```

### 1.7 Kurulum doğrulama

```bash
python -c "import pycasa, sort, skimage, torch, ultralytics, motmetrics; print('hepsi OK, cuda:', torch.cuda.is_available())"
```

---

## BÖLÜM 2 — Türkçe klasör sorunu (ÖNEMLİ)

YOLO ağırlıkları çalıştığın klasöre iniyor. Klasör yolunda Türkçe karakter varsa
(`Masaüstü` gibi) `torch.jit.load` dosyayı açamıyor ve YOLOv5 çöküyor.

Her terminal oturumunda, Python'u başlatmadan ÖNCE:

```bash
set PYCASA_PROJECT_ROOT=C:\Users\<KULLANICI>\.pycasa_data
```

Kalıcı yapmak istersen (yeni terminal açman gerekir):

```bash
setx PYCASA_PROJECT_ROOT C:\Users\<KULLANICI>\.pycasa_data
```

Doğrulama:

```bash
echo %PYCASA_PROJECT_ROOT%
```

---

## BÖLÜM 3 — IPython ile adım adım (Atilla'nın önerdiği yol)

```bash
ipython
```

IPython açıldıktan sonra aşağıdakileri **tek tek** yapıştır.

### Adım 1 — Default datayı yükle

```python
import pycasa as pc
self = pc.io.load_default_data()
```

İlk çalışmada HuggingFace'ten ~900 dosya iner (birkaç dakika). Sonraki çalışmalarda cache'den okur.
Ekranda `um_per_px=0.24`, `volume_ml=2.2`, `chamber_depth_um=20.7` otomatik ayarlandığını göreceksin.

Meta bilgilerini gör:

```python
self.info()
```

```python
self.get_meta()
```

GT var mı, track var mı:

```python
print("GT frame sayisi:", len(self.get_groundtruth()))
print("track:", self.get_tracks())
```

### Adım 2 — Sadece GT detection ile timelapse

```python
self.visualization.timelapse(video_type="original", show_detections=False, show_tracks=False, show_groundtruth=True)
```

Pencere açılır. Slider ile frame gez, Play'e bas, sağdaki butonlarla overlay aç/kapa.
**Devam etmek için pencereyi kapat.**

### Adım 3 — Üç detector + assessment

YOLOv5:

```python
self.detection.yolo(yolo_model="yolov5")
```

```python
self.assessment.evaluate_detections()
```

```python
import copy
sonuc_yolov5 = copy.deepcopy(self.get_assessment()["detection"])
sonuc_yolov5
```

YOLO26 (önceki detection'ın silindiğine dair uyarı göreceksin):

```python
self.detection.yolo(yolo_model="yolo26")
```

```python
self.assessment.evaluate_detections()
```

```python
sonuc_yolo26 = copy.deepcopy(self.get_assessment()["detection"])
sonuc_yolo26
```

Moving cells:

```python
self.detection.detect_moving_cells()
```

```python
self.assessment.evaluate_detections()
```

```python
sonuc_mc = copy.deepcopy(self.get_assessment()["detection"])
sonuc_mc
```

Üçünü yan yana bas:

```python
for ad, r in [("yolov5", sonuc_yolov5), ("yolo26", sonuc_yolo26), ("moving_cells", sonuc_mc)]:
    print(f"{ad:14s} tp={r['tp']:6d} fp={r['fp']:6d} fn={r['fn']:6d} P={r['precision']:6.2f} R={r['recall']:6.2f} F1={r['F1']:6.2f}")
```

**Not:** `copy.deepcopy` şart. `get_assessment()` canlı sözlük döndürüyor, kopyalamazsan yeni detector çalışınca eski sonucun da değişiyor.

### Adım 4 — Overwrite kuralı

Adım 3'te zaten gördün, uyarılar şöyleydi:

```
Warning: Previous detection result overwritten (yolov5 -> yolo26).
Warning: Previous detection result overwritten (yolo26 -> moving_cells).
```

Kanıtla: session'da tek detection seti var, o da en son çalışan:

```python
print("frame sayisi:", len(self.get_detections()))
```

Aynı kural tracking için de geçerli, adım 5'te göreceksin.

### Adım 5 — GT üstünde SORT ve JPDAF

Temiz session ile başla:

```python
self = pc.io.load_default_data()
```

SORT:

```python
self.tracking.sort()
```

```python
self.visualization.timelapse(video_type="original", show_detections=False, show_groundtruth=True, show_tracks=True)
```

Pencereyi kapat, sonra JPDAF (tracking overwrite uyarısını göreceksin):

```python
self.tracking.jpdaf()
```

```python
self.visualization.timelapse(video_type="original", show_detections=False, show_groundtruth=True, show_tracks=True)
```

Track sayılarını karşılaştır:

```python
tr = self.get_tracks()
backend = list(tr.keys())[0]
n = len(tr[backend]["groundtruth"])
print(backend, "track sayisi:", n, "| ortalama uzunluk:", sum(len(v) for v in tr[backend]["groundtruth"].values())/n)
```

### Adım 6a — GT + SORT → kinematik ve CASA

```python
self = pc.io.load_default_data()
```

```python
self.tracking.sort()
```

```python
self.motility.kinematic_parameters()
```

```python
self.motility.casa_parameters()
```

```python
casa_gt = copy.deepcopy(self.get_motility()["casa_parameters"]["groundtruth"])
casa_gt["grades"], casa_gt["concentration_M_per_ml"], casa_gt["total_sperm_count_M"]
```

### Adım 6b — YOLO26 + SORT → kinematik ve CASA

**Yeni bir IPython oturumunda çalıştır** (aynı oturumda YOLOv5 çalıştıysan YOLO26 sonucu değişiyor):

```python
import pycasa as pc, copy
self = pc.io.load_default_data()
```

```python
self.detection.yolo(yolo_model="yolo26")
```

```python
self.tracking.sort(skip_gt=True)
```

```python
self.motility.kinematic_parameters()
```

```python
self.motility.casa_parameters()
```

```python
casa_y26 = copy.deepcopy(self.get_motility()["casa_parameters"]["yolo26"])
casa_y26["grades"], casa_y26["concentration_M_per_ml"], casa_y26["total_sperm_count_M"]
```

### Adım 6c — HSTLI gerçek değerleriyle karşılaştır

HSTLI CSV'sindeki HC004 satırı (Unwashed Samples):
%Rapid 42, %Slow 23, %Non-progressive 9, %Immotile 26, Konsantrasyon 69 ×10⁶/mL, Toplam 151.8 ×10⁶

```python
hstli = {"rapid": 42, "slow": 23, "non_progressive": 9, "immotile": 26}
print(f"{'':14s} {'rapid':>7s} {'slow':>7s} {'nonprog':>8s} {'immotile':>9s}")
print(f"{'HSTLI':14s} {hstli['rapid']:7d} {hstli['slow']:7d} {hstli['non_progressive']:8d} {hstli['immotile']:9d}")
for ad, c in [("GT+SORT", casa_gt), ("YOLO26+SORT", casa_y26)]:
    g = c["grades"]
    print(f"{ad:14s} {g['rapid']:7.1f} {g['slow']:7.1f} {g['non_progressive']:8.1f} {g['immotile']:9.1f}")
```

CSV'yi kendin indirmek istersen:

```bash
curl -L -o hstli_reports.csv "https://huggingface.co/datasets/DFL-KamLab/HSTLI_A-Dataset-of-Human-Semen-Time-Lapse-Images/resolve/main/sys-casa/sys-casa_casaMotilityReports.csv"
```

---

## BÖLÜM 4 — Hazır scriptleri çalıştırma

Her biri tek komutla çalışır. Önce `set PYCASA_PROJECT_ROOT=...` yapmayı unutma.

```bash
python scripts/step1_load.py
```

```bash
python scripts/step2_timelapse_gt.py
```

```bash
python scripts/step3_detection_assessment.py
```

```bash
python scripts/step5_tracking_gt.py
```

```bash
python scripts/step5_timelapse_interactive.py
```

```bash
python scripts/step6_motility.py
```

Tüm API'yi test eden kapsamlı script (uzun sürer, ~15-25 dk):

```bash
python scripts/step7_full_api_test.py
```

Tek bölümünü çalıştırmak istersen:

```bash
python scripts/step7_full_api_test.py tracking
```

Bölüm isimleri: `io`, `casa`, `preprocessing`, `detection_yolo26`, `detection_classic`, `detection_yolov5`, `tracking`, `motility`, `visualization`

---

## BÖLÜM 5 — Karşılaşabileceğin hatalar

| Hata | Sebep | Çözüm |
|---|---|---|
| `No module named 'skimage'` | Eksik bağımlılık | Bölüm 1.3'teki pip komutu |
| `No module named 'sort'` | SORT ayrı paket | Bölüm 1.4 |
| `open file failed ... errno 2` (yolov5) | Türkçe karakterli yol | Bölüm 2, `PYCASA_PROJECT_ROOT` |
| `EOFError: EOF when reading a line` | YOLOv5 repo klon sorusu, stdin yok | Bölüm 1.5, repoyu elle klonla |
| `PytorchStreamReader failed locating constants.pkl` | Ağırlık dosyası bozuk/yanlış yol | `PYCASA_PROJECT_ROOT`'u ayarla, ağırlıkları sil ve tekrar indir |
| `MemoryError: Unable to allocate 191 MiB` | Çok fazla session/`copy()` | `final_frame` ile frame sayısını düşür, session'ları `del` et |
| `BrokenProcessPool` (digital_washing) | `n_jobs>1` Windows'ta sorunlu | `n_jobs=1` kullan |
| Timelapse penceresi açılmıyor | Agg backend | `set MPLBACKEND=tkagg` |
| Pencere kapanınca `invalid command name ..._on_timer` | Tk timer kapatılmamış | Zararsız, yoksay |
