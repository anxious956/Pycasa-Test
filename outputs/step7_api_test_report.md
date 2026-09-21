# pycasa tam API testi: 101 PASS / 18 FAIL / 119 test

Her bolum ayri Python process'inde, HC004 default datasinin ilk 21 frame'i ile calistirildi.
`-> hata beklenir` yazan testlerde PASS, fonksiyonun dogru sekilde hata vermesi demektir.


## io (13/14)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `io.load_default_data(final_frame=20)` | PASS | 0.5 | frames=21 |
| `io.load_default_data(um_per_px/volume_ml/chamber_depth_um override)` | PASS | 0.7 | {'um_per_px': 0.5, 'volume_ml': 3.0, 'chamber_depth_um': 10.0} |
| `io.load_default_data(initial_frame=10, final_frame=20)` | PASS | 0.2 | frames=11 |
| `io.load_default_data(sampling_rate=15)` | PASS | 0.2 | fps=15.0 |
| `io.load_default_data(magnification='20x')` | PASS | 0.2 | magnification=20x |
| `io.load_default_data(download=False) cache'den` | PASS | 0.2 | frames=21 |
| `session.io.load_default_data() wrapper` | PASS | 0.1 | um_per_px=0.24 |
| `session.io.load_default_data(volume_ml=...) wrapper/module imza paritesi` | **FAIL** | 0.0 | TypeError: _SessionIONamespace.load_default_data() got an unexpected keyword argument 'volume_ml' |
| `io.load_video(video, groundtruth_detections_path)` | PASS | 0.2 | frames=21 gt_frames=900 fps=30.0 |
| `io.load_video(video) GT'siz, sampling_rate=25` | PASS | 0.1 | fps=25.0 |
| `io.load_video(groundtruth_tracks_path=GT_DIR) (GT'de track id yok)` | PASS | 0.2 | gt_tracks=1 |
| `io.load_video(dilution_factor=2)` | PASS | 0.0 | dilution=2.0 |
| `io.load_video(olmayan dosya) -> hata beklenir` | PASS | 0.0 | beklenen hata: FileNotFoundError: Video file does not exist: C:\nope\x.avi |
| `session.io.load_video() wrapper` | PASS | 0.0 | frames=6 |

## casa (23/23)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `Casa.info()` | PASS | 0.0 | ekrana basildi |
| `Casa.copy() bagimsiz kopya mi` | PASS | 0.1 | yeni nesne=True, meta ayni=True |
| `set_um_per_px(0.3)` | PASS | 0.2 | 0.3 |
| `set_volume_ml(1.5)` | PASS | 0.2 | 1.5 |
| `set_chamber_depth_um(10)` | PASS | 0.2 | 10.0 |
| `set_dilution_factor(2)` | PASS | 0.2 | 2.0 |
| `set_um_per_px(-1) -> ValueError beklenir` | PASS | 0.0 | beklenen hata: ValueError: `um_per_px` must be > 0. |
| `set_volume_ml('abc') -> TypeError beklenir` | PASS | 0.0 | beklenen hata: TypeError: `volume_ml` must be a numeric value. |
| `set_chamber_depth_um(0) -> hata beklenir` | PASS | 0.0 | beklenen hata: ValueError: `chamber_depth_um` must be > 0. |
| `set_dilution_factor(-5) -> hata beklenir` | PASS | 0.0 | beklenen hata: ValueError: `dilution_factor` must be > 0. |
| `get_casa() keys` | PASS | 0.0 | ['meta', 'video', 'detections', 'tracks', 'motility', 'assessment'] |
| `get_meta() keys` | PASS | 0.0 | ['chamber_depth_um', 'duration_sec', 'height', 'magnification', 'sampling_rate', 'total_duration_sec', 'total_number_frame', 'um_per_px', 'video_path', 'volume_ml', 'width'] |
| `get_video() keys` | PASS | 0.0 | ['path', 'initial_frame', 'final_frame', 'number_frame_used', 'original_video'] |
| `get_groundtruth() frame sayisi` | PASS | 0.0 | 900 |
| `get_groundtruth_tracks() (bos olmali)` | PASS | 0.0 | {} |
| `get_detections() (bos)` | PASS | 0.0 | {} |
| `get_detections(include_groundtruth=True)` | PASS | 0.0 | ['groundtruth', 'groundtruth_detections_path'] |
| `get_tracks() (bos)` | PASS | 0.0 | {} |
| `get_tracks(backend='sort') tracking yokken` | PASS | 0.0 | {} |
| `get_motility() (bos)` | PASS | 0.0 | {} |
| `get_assessment() (bos)` | PASS | 0.0 | {} |
| `get_assesment() (yazim hatali alias)` | PASS | 0.0 | {} |
| `get_assessment() canli referans mi (mutasyon testi)` | PASS | 0.0 | session'a sizdi=True |

## preprocessing (19/19)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `preprocessing.grayscale()` | PASS | 0.2 | ['original_video', 'grayscale_video'] |
| `preprocessing.grayscale(overwrite=True)` | PASS | 0.4 | original_video.shape=(21, 1024, 1280) |
| `preprocessing.binarization.otsu()` | PASS | 0.5 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.adaptive_gaussian()` | PASS | 0.4 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.adaptive_mean()` | PASS | 0.3 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.niblack()` | PASS | 1.0 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.sauvola()` | PASS | 1.0 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.urbano()` | PASS | 4.5 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 1] |
| `binarization.otsu() grayscale yapilmadan (ham renkli video)` | PASS | 0.7 | ['original_video', 'binary_video'] |
| `binarization.adaptive_gaussian(block_size=4 cift) -> hata beklenir` | PASS | 0.0 | beklenen hata: ValueError: `block_size` must be an odd integer >= 3. |
| `binarization.niblack(window_size=0) -> hata beklenir` | PASS | 0.0 | beklenen hata: ValueError: `window_size` must be >= 3. |
| `preprocessing.normalization.clahe()` | PASS | 0.1 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.hist_equal()` | PASS | 0.9 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.log()` | PASS | 1.0 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.median()` | PASS | 1.1 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.min_max()` | PASS | 0.5 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.z_score()` | PASS | 0.6 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=float32 |
| `normalization.min_max(overwrite=True)` | PASS | 0.8 | ['original_video', 'normalized_video'] |
| `zincir: grayscale -> clahe -> otsu` | PASS | 1.0 | ['original_video', 'grayscale_video', 'normalized_video', 'binary_video'] |

## detection_yolo26 (8/8)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `detection.yolo() varsayilan (yolo26) + evaluate_detections` | PASS | 5.5 | tp=2101 fp=1221 fn=26 P=63.25 R=98.78 F1=77.12 frames=21 |
| `detection.yolo(weights=<ASCII tam yol>) ozel agirlik` | PASS | 2.6 | tp=2101 fp=1221 fn=26 P=63.25 R=98.78 F1=77.12 frames=21 |
| `detection.yolo(conf=0.5) yuksek esik` | PASS | 2.4 | tp=2068 fp=1141 fn=59 P=64.44 R=97.23 F1=77.51 frames=21 |
| `detection.yolo(conf=0.01) dusuk esik` | PASS | 2.8 | tp=2120 fp=4024 fn=7 P=34.51 R=99.67 F1=51.26 frames=21 |
| `detection.yolo(yolo_model='yolo99') -> hata beklenir` | PASS | 0.2 | beklenen hata: ValueError: `yolo_model` must be one of ('yolov5', 'yolo26'), got 'yolo99'. |
| `detection.yolo(weights='C:/nope.pt') -> hata beklenir` | PASS | 0.2 | beklenen hata: FileNotFoundError: Custom `weights` path was not found: 'C:/nope.pt'. On Windows use a raw string: r'D:\path\to\weights.pt' |
| `detection.yolo(download=False) managed agirlik cache'de` | PASS | 2.5 | tp=2101 fp=1221 fn=26 P=63.25 R=98.78 F1=77.12 frames=21 |
| `get_detections() satir formati (yolo26, frame 0)` | PASS | 2.6 | [['0', '0.910138', '0.828910', '0.037355', '0.046788'], ['0', '0.556985', '0.449665', '0.036418', '0.045641']] |

## detection_classic (13/14)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `detection.detect_moving_cells(method='cv-gmg')` | PASS | 1.5 | tp=0 fp=1 fn=101 P=0.0 R=0.0 F1=0.0 frames=1 |
| `detection.detect_moving_cells(method='cv-mog')` | PASS | 0.8 | tp=69 fp=16 fn=32 P=81.18 R=68.32 F1=74.19 frames=1 |
| `detection.detect_moving_cells(method='cv-mog2')` | PASS | 0.5 | tp=90 fp=248 fn=11 P=26.63 R=89.11 F1=41.0 frames=1 |
| `detection.detect_moving_cells(method='gm')` | PASS | 3.4 | tp=79 fp=9 fn=22 P=89.77 R=78.22 F1=83.6 frames=1 |
| `detection.detect_moving_cells(method='gm', low_memory=True)` | PASS | 2.9 | tp=79 fp=9 fn=22 P=89.77 R=78.22 F1=83.6 frames=1 |
| `detection.detect_moving_cells(method='xyz') -> hata beklenir` | PASS | 0.2 | beklenen hata: ValueError: method xyz is invalid. |
| `detection.digital_washing() n_jobs=1` | PASS | 16.3 | tp=84 fp=15 fn=17 P=84.85 R=83.17 F1=84.0 frames=1 |
| `detection.digital_washing(n_jobs=4) paralel` | PASS | 17.5 | tp=84 fp=15 fn=17 P=84.85 R=83.17 F1=84.0 frames=1 |
| `detection.digital_washing(motion_threshold=5, blob_min_pixel_area=30)` | PASS | 15.7 | tp=58 fp=3 fn=43 P=95.08 R=57.43 F1=71.6 frames=1 |
| `detection.urbano_detection()` | PASS | 5.0 | tp=1920 fp=589 fn=207 P=76.52 R=90.27 F1=82.83 frames=21 |
| `detection.urbano_detection(blob_min_pixel_area=10, log_size=7)` | PASS | 4.8 | tp=1813 fp=546 fn=314 P=76.85 R=85.24 F1=80.83 frames=21 |
| `assessment.evaluate_detections(match_min_distance_pixel=10)` | PASS | 4.9 | {'tp': 1599, 'fp': 910, 'fn': 528, 'precision': np.float64(63.73), 'recall': np.float64(75.18), 'F0.5': np.float64(65.73), 'F1': np.float64(68.98), 'F2': np.float64(72.57), 'evaluated_frames': 21} |
| `assessment.evaluate_detections() detection YOKKEN -> hata beklenir` | **FAIL** | 0.2 | beklenen Exception gelmedi, sonuc: <pycasa.casa.casa.Casa object at 0x000002B803CFE060> |
| `detection overwrite uyarisi (urbano -> moving_cells)` | PASS | 5.9 | detection frame sayisi=1 |

## detection_yolov5 (3/3)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `detection.yolo(yolo_model='yolov5') + evaluate_detections` | PASS | 6.4 | tp=1539 fp=631 fn=588 P=70.92 R=72.36 F1=71.63 frames=21 |
| `detection.yolo(yolov5, conf=0.4)` | PASS | 2.3 | tp=1413 fp=315 fn=714 P=81.77 R=66.43 F1=73.31 frames=21 |
| `YOLOv5'ten SONRA yolo26 (sira bagimliligi testi)` | PASS | 3.3 | tp=2101 fp=1025 fn=26 P=67.21 R=98.78 F1=79.99 frames=21 |

## tracking (18/19)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `tracking.sort() sadece GT` | PASS | 0.8 | backend=sort groundtruth:114 track |
| `tracking.sort(max_age=5, min_hits=1, iou_threshold=0.3)` | PASS | 0.3 | backend=sort groundtruth:168 track |
| `tracking.sort(initial_frame=10)` | PASS | 0.3 | backend=sort groundtruth:105 track |
| `tracking.sort(delete_temp=False)` | PASS | 0.3 | backend=sort groundtruth:114 track |
| `tracking.sort() GT + yolo26 (iki kaynak)` | PASS | 5.0 | backend=sort groundtruth:114 track / yolo26:239 track |
| `tracking.sort(skip_gt=True) sadece yolo26` | PASS | 3.0 | backend=sort yolo26:239 track |
| `tracking.sort(skip_gt=True) detection YOKKEN` | PASS | 0.2 | backend=sort  |
| `tracking.jpdaf() sadece GT` | PASS | 1.4 | backend=jpdaf groundtruth:115 track |
| `tracking.jpdaf(frame_rate=60, p_delete=0.3, sigma_n_um=1)` | PASS | 1.5 | backend=jpdaf groundtruth:138 track |
| `tracking.jpdaf(position_gate=5, velocity_gate_um=20, detection_probability=0.9)` | PASS | 11.6 | backend=jpdaf groundtruth:81 track |
| `tracking.jpdaf(skip_gt=True) yolo26` | PASS | 6.2 | backend=jpdaf yolo26:203 track |
| `tracking.deepsort() sadece GT` | PASS | 1.3 | backend=deepsort groundtruth:127 track |
| `tracking.deepsort(max_age=10, n_init=2, max_iou_distance=0.5)` | PASS | 0.8 | backend=deepsort groundtruth:180 track |
| `tracking overwrite: sort -> jpdaf, get_tracks() tek backend` | PASS | 1.6 | backends=['jpdaf'] |
| `get_tracks(backend='jpdaf') sort varken` | PASS | 0.4 | {} |
| `assessment.evaluate_tracks() GT-sort vs yolo26-sort` | PASS | 3.8 | {} |
| `assessment.evaluate_tracks(match_min_distance_pixel=10, backend='sort')` | PASS | 3.3 | ok |
| `assessment.evaluate_tracks() tek kaynakla (sadece GT)` | PASS | 0.3 | {} |
| `assessment.evaluate_tracks() tracking YOKKEN -> hata beklenir` | **FAIL** | 0.2 | beklenen Exception gelmedi, sonuc: <pycasa.casa.casa.Casa object at 0x000001A6869A41D0> |

## motility (4/18)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `kinematic_parameters() + casa_parameters() [sort/GT]` | **FAIL** | 0.8 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `motility [jpdaf/GT]` | **FAIL** | 1.4 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `motility [deepsort/GT]` | **FAIL** | 0.8 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `motility [sort/GT+yolo26 iki kaynak]` | **FAIL** | 5.0 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `kinematic_parameters(window_size=15, overlap=0.5, smoothing_window=3, denoise_window=1, min_frame_rate_warn=0)` | PASS | 0.4 | groundtruth: grades={'rapid': 48.98, 'slow': 3.06, 'non_progressive': 44.9, 'immotile': 3.06} motile=96.94 conc=62.4 tracks=98 |
| `kinematic_parameters(frame_rate=60)` | **FAIL** | 0.3 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `kinematic_parameters(conversion_required=False) piksel birimi` | **FAIL** | 0.3 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `kinematic_parameters(overlap=1.5) gecersiz -> hata beklenir` | PASS | 0.3 | beklenen hata: RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `casa_parameters(velocity_metric='VAP', rapid=25, immotile=10, progressive_str=0.5)` | **FAIL** | 0.3 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `casa_parameters(velocity_metric='VSL')` | **FAIL** | 0.4 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `casa_parameters(volume_ml=1, chamber_depth_um=10, dilution_factor=2)` | **FAIL** | 0.4 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `casa_parameters(experimental_parameters=True, n_subpopulations=2)` | **FAIL** | 0.3 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `casa_parameters(hyperactivation esikleri, experimental)` | **FAIL** | 0.3 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `casa_parameters(velocity_metric='XYZ') -> hata beklenir` | PASS | 0.3 | beklenen hata: RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `casa_parameters() kinematic YOKKEN -> hata beklenir` | PASS | 0.3 | beklenen hata: RuntimeError: No kinematic parameters found. Run `self.motility.kinematic_parameters()` before `casa_parameters()`. |
| `kinematic_parameters() tracking YOKKEN -> hata beklenir` | **FAIL** | 0.2 | beklenen Exception gelmedi, sonuc: <pycasa.casa.casa.Casa object at 0x0000018518097BC0> |
| `kinematic_parameters() um_per_px=None iken` | **FAIL** | 0.3 | ValueError: `um_per_px` is required when conversion is requested. |
| `get_motility() track basina kinematik anahtarlar` | **FAIL** | 0.3 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |

## visualization (0/1)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `BOLUM visualization cokti` | **FAIL** | 0 | ematic_parameters
    kinematic_parameters(
  File "C:\Users\Esmer\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pycasa\mo |
