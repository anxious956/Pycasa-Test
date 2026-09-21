# pycasa tam API testi: 83 PASS / 36 FAIL / 119 test

Her bolum ayri Python process'inde, HC004 default datasinin ilk 21 frame'i ile calistirildi.
`-> hata beklenir` yazan testlerde PASS, fonksiyonun dogru sekilde hata vermesi demektir.


## io (13/14)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `io.load_default_data(final_frame=20)` | PASS | 0.3 | frames=21 |
| `io.load_default_data(um_per_px/volume_ml/chamber_depth_um override)` | PASS | 0.7 | {'um_per_px': 0.5, 'volume_ml': 3.0, 'chamber_depth_um': 10.0} |
| `io.load_default_data(initial_frame=10, final_frame=20)` | PASS | 0.2 | frames=11 |
| `io.load_default_data(sampling_rate=15)` | PASS | 0.2 | fps=15.0 |
| `io.load_default_data(magnification='20x')` | PASS | 0.2 | magnification=20x |
| `io.load_default_data(download=False) cache'den` | PASS | 0.2 | frames=21 |
| `session.io.load_default_data() wrapper` | PASS | 0.1 | um_per_px=0.24 |
| `session.io.load_default_data(volume_ml=...) wrapper/module imza paritesi` | **FAIL** | 0.0 | TypeError: _SessionIONamespace.load_default_data() got an unexpected keyword argument 'volume_ml' |
| `io.load_video(video, groundtruth_detections_path)` | PASS | 0.2 | frames=21 gt_frames=900 fps=30.0 |
| `io.load_video(video) GT'siz, sampling_rate=25` | PASS | 0.0 | fps=25.0 |
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

## preprocessing (16/19)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `preprocessing.grayscale()` | PASS | 0.3 | ['original_video', 'grayscale_video'] |
| `preprocessing.grayscale(overwrite=True)` | PASS | 0.4 | original_video.shape=(21, 1024, 1280) |
| `preprocessing.binarization.otsu()` | PASS | 0.6 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.adaptive_gaussian()` | PASS | 0.4 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.adaptive_mean()` | PASS | 0.3 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.niblack()` | PASS | 1.0 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.sauvola()` | PASS | 1.0 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.urbano()` | PASS | 5.1 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 1] |
| `binarization.otsu() grayscale yapilmadan (ham renkli video)` | **FAIL** | 0.7 | MemoryError: Unable to allocate 105. MiB for an array with shape (21, 1024, 1280) and data type float32 |
| `binarization.adaptive_gaussian(block_size=4 cift) -> hata beklenir` | PASS | 0.0 | beklenen hata: ValueError: `block_size` must be an odd integer >= 3. |
| `binarization.niblack(window_size=0) -> hata beklenir` | PASS | 0.0 | beklenen hata: ValueError: `window_size` must be >= 3. |
| `preprocessing.normalization.clahe()` | PASS | 0.2 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.hist_equal()` | PASS | 1.6 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.log()` | PASS | 1.3 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.median()` | PASS | 1.1 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.min_max()` | PASS | 0.6 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.z_score()` | **FAIL** | 0.6 | MemoryError: Unable to allocate 315. MiB for an array with shape (21, 1024, 1280, 3) and data type float32 |
| `normalization.min_max(overwrite=True)` | PASS | 0.9 | ['original_video', 'normalized_video'] |
| `zincir: grayscale -> clahe -> otsu` | **FAIL** | 0.6 | MemoryError: Unable to allocate 105. MiB for an array with shape (21, 1024, 1280) and data type float32 |

## detection_yolo26 (2/8)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `detection.yolo() varsayilan (yolo26) + evaluate_detections` | **FAIL** | 2.6 | RuntimeError: cuDNN error: CUDNN_STATUS_INTERNAL_ERROR_DEVICE_ALLOCATION_FAILED |
| `detection.yolo(weights=<ASCII tam yol>) ozel agirlik` | **FAIL** | 0.3 | RuntimeError: No frames could be read from: C:\Users\Esmer\OneDrive\Masaüstü\PYCASA TRY\pycasa_data\sys-casa\rawdata\sub-HC004\ses-01\sys-casa_sub-HC004_ses-01_run-005_video.avi |
| `detection.yolo(conf=0.5) yuksek esik` | **FAIL** | 0.0 | MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |
| `detection.yolo(conf=0.01) dusuk esik` | **FAIL** | 0.0 | MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |
| `detection.yolo(yolo_model='yolo99') -> hata beklenir` | PASS | 0.3 | beklenen hata: RuntimeError: No frames could be read from: C:\Users\Esmer\OneDrive\Masaüstü\PYCASA TRY\pycasa_data\sys-casa\rawdata\sub-HC004\ses-01\sys-casa_sub-HC004_ses-01_run- |
| `detection.yolo(weights='C:/nope.pt') -> hata beklenir` | PASS | 0.0 | beklenen hata: MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |
| `detection.yolo(download=False) managed agirlik cache'de` | **FAIL** | 0.0 | MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |
| `get_detections() satir formati (yolo26, frame 0)` | **FAIL** | 0.0 | MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |

## detection_classic (6/14)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `detection.detect_moving_cells(method='cv-gmg')` | PASS | 1.7 | tp=0 fp=1 fn=101 P=0.0 R=0.0 F1=0.0 frames=1 |
| `detection.detect_moving_cells(method='cv-mog')` | PASS | 0.8 | tp=69 fp=16 fn=32 P=81.18 R=68.32 F1=74.19 frames=1 |
| `detection.detect_moving_cells(method='cv-mog2')` | PASS | 0.5 | tp=90 fp=248 fn=11 P=26.63 R=89.11 F1=41.0 frames=1 |
| `detection.detect_moving_cells(method='gm')` | **FAIL** | 0.6 | MemoryError: Unable to allocate 105. MiB for an array with shape (21, 1024, 1280) and data type float32 |
| `detection.detect_moving_cells(method='gm', low_memory=True)` | **FAIL** | 2.0 | MemoryError: Unable to allocate 200. MiB for an array with shape (20, 1024, 1280) and data type float64 |
| `detection.detect_moving_cells(method='xyz') -> hata beklenir` | PASS | 0.3 | beklenen hata: ValueError: method xyz is invalid. |
| `detection.digital_washing() n_jobs=1` | **FAIL** | 2.3 | MemoryError: Unable to allocate 200. MiB for an array with shape (20, 1024, 1280) and data type float64 |
| `detection.digital_washing(n_jobs=4) paralel` | **FAIL** | 0.7 | MemoryError: Unable to allocate 105. MiB for an array with shape (21, 1024, 1280) and data type float32 |
| `detection.digital_washing(motion_threshold=5, blob_min_pixel_area=30)` | **FAIL** | 2.8 | MemoryError: Unable to allocate 200. MiB for an array with shape (20, 1024, 1280) and data type float64 |
| `detection.urbano_detection()` | PASS | 5.5 | tp=1920 fp=589 fn=207 P=76.52 R=90.27 F1=82.83 frames=21 |
| `detection.urbano_detection(blob_min_pixel_area=10, log_size=7)` | PASS | 5.1 | tp=1813 fp=546 fn=314 P=76.85 R=85.24 F1=80.83 frames=21 |
| `assessment.evaluate_detections(match_min_distance_pixel=10)` | **FAIL** | 0.5 | MemoryError: Unable to allocate 105. MiB for an array with shape (21, 1024, 1280) and data type float32 |
| `assessment.evaluate_detections() detection YOKKEN -> hata beklenir` | **FAIL** | 0.3 | beklenen Exception gelmedi, sonuc: <pycasa.casa.casa.Casa object at 0x000001CD233F6BD0> |
| `detection overwrite uyarisi (urbano -> moving_cells)` | **FAIL** | 0.3 | MemoryError: Unable to allocate 105. MiB for an array with shape (21, 1024, 1280) and data type float32 |

## detection_yolov5 (1/3)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `detection.yolo(yolo_model='yolov5') + evaluate_detections` | PASS | 6.5 | tp=1539 fp=631 fn=588 P=70.92 R=72.36 F1=71.63 frames=21 |
| `detection.yolo(yolov5, conf=0.4)` | **FAIL** | 0.9 | MemoryError:  |
| `YOLOv5'ten SONRA yolo26 (sira bagimliligi testi)` | **FAIL** | 0.0 | RuntimeError: No frames could be read from: C:\Users\Esmer\OneDrive\Masaüstü\PYCASA TRY\pycasa_data\sys-casa\rawdata\sub-HC004\ses-01\sys-casa_sub-HC004_ses-01_run-005_video.avi |

## tracking (9/19)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `tracking.sort() sadece GT` | PASS | 1.0 | backend=sort groundtruth:114 track |
| `tracking.sort(max_age=5, min_hits=1, iou_threshold=0.3)` | PASS | 0.3 | backend=sort groundtruth:168 track |
| `tracking.sort(initial_frame=10)` | PASS | 0.3 | backend=sort groundtruth:105 track |
| `tracking.sort(delete_temp=False)` | PASS | 0.3 | backend=sort groundtruth:114 track |
| `tracking.sort() GT + yolo26 (iki kaynak)` | **FAIL** | 2.3 | RuntimeError: CUDA error: out of memory
CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
For debugging consider passing CUDA_LAUN |
| `tracking.sort(skip_gt=True) sadece yolo26` | **FAIL** | 0.5 | RuntimeError: CUDA error: out of memory
CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
For debugging consider passing CUDA_LAUN |
| `tracking.sort(skip_gt=True) detection YOKKEN` | PASS | 0.2 | backend=sort  |
| `tracking.jpdaf() sadece GT` | PASS | 1.5 | backend=jpdaf groundtruth:115 track |
| `tracking.jpdaf(frame_rate=60, p_delete=0.3, sigma_n_um=1)` | PASS | 1.5 | backend=jpdaf groundtruth:138 track |
| `tracking.jpdaf(position_gate=5, velocity_gate_um=20, detection_probability=0.9)` | PASS | 20.8 | backend=jpdaf groundtruth:81 track |
| `tracking.jpdaf(skip_gt=True) yolo26` | **FAIL** | 0.7 | RuntimeError: bad allocation |
| `tracking.deepsort() sadece GT` | **FAIL** | 0.0 | RuntimeError: No frames could be read from: C:\Users\Esmer\OneDrive\Masaüstü\PYCASA TRY\pycasa_data\sys-casa\rawdata\sub-HC004\ses-01\sys-casa_sub-HC004_ses-01_run-005_video.avi |
| `tracking.deepsort(max_age=10, n_init=2, max_iou_distance=0.5)` | **FAIL** | 0.0 | MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |
| `tracking overwrite: sort -> jpdaf, get_tracks() tek backend` | **FAIL** | 0.0 | MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |
| `get_tracks(backend='jpdaf') sort varken` | **FAIL** | 0.0 | MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |
| `assessment.evaluate_tracks() GT-sort vs yolo26-sort` | **FAIL** | 0.0 | MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |
| `assessment.evaluate_tracks(match_min_distance_pixel=10, backend='sort')` | **FAIL** | 0.0 | MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |
| `assessment.evaluate_tracks() tek kaynakla (sadece GT)` | **FAIL** | 0.0 | MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |
| `assessment.evaluate_tracks() tracking YOKKEN -> hata beklenir` | PASS | 0.0 | beklenen hata: MemoryError: Unable to allocate 78.8 MiB for an array with shape (21, 1024, 1280, 3) and data type uint8 |

## motility (13/18)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `kinematic_parameters() + casa_parameters() [sort/GT]` | PASS | 1.5 | groundtruth: grades={'rapid': 47.52, 'slow': 28.71, 'non_progressive': 2.97, 'immotile': 20.79} motile=79.21 conc=61.21 tracks=101 |
| `motility [jpdaf/GT]` | PASS | 4.4 | groundtruth: grades={'rapid': 41.51, 'slow': 31.13, 'non_progressive': 2.83, 'immotile': 24.53} motile=75.47 conc=67.76 tracks=106 |
| `motility [deepsort/GT]` | PASS | 2.4 | groundtruth: grades={'rapid': 44.33, 'slow': 29.9, 'non_progressive': 5.15, 'immotile': 20.62} motile=79.38 conc=63.02 tracks=97 |
| `motility [sort/GT+yolo26 iki kaynak]` | **FAIL** | 2.4 | RuntimeError: CUDA error: CUDA-capable device(s) is/are busy or unavailable
CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
For  |
| `kinematic_parameters(window_size=15, overlap=0.5, smoothing_window=3, denoise_window=1, min_frame_rate_warn=0)` | PASS | 1.2 | groundtruth: grades={'rapid': 52.29, 'slow': 9.17, 'non_progressive': 29.36, 'immotile': 9.17} motile=90.83 conc=61.21 tracks=109 |
| `kinematic_parameters(frame_rate=60)` | **FAIL** | 0.5 | RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `kinematic_parameters(conversion_required=False) piksel birimi` | PASS | 1.0 | groundtruth: grades={'rapid': 47.52, 'slow': 28.71, 'non_progressive': 2.97, 'immotile': 20.79} motile=79.21 conc=61.21 tracks=101 |
| `kinematic_parameters(overlap=1.5) gecersiz -> hata beklenir` | PASS | 0.3 | beklenen hata: RuntimeError: No tracks with enough points were found in any tracked source. Required points per track: 30. |
| `casa_parameters(velocity_metric='VAP', rapid=25, immotile=10, progressive_str=0.5)` | **FAIL** | 0.0 | MemoryError: Unable to allocate 229. MiB for an array with shape (61, 1024, 1280, 3) and data type uint8 |
| `casa_parameters(velocity_metric='VSL')` | PASS | 0.9 | groundtruth: grades={'rapid': 12.87, 'slow': 42.57, 'non_progressive': 0.0, 'immotile': 44.55} motile=55.45 conc=61.21 tracks=101 |
| `casa_parameters(volume_ml=1, chamber_depth_um=10, dilution_factor=2)` | PASS | 0.8 | groundtruth: grades={'rapid': 47.52, 'slow': 28.71, 'non_progressive': 2.97, 'immotile': 20.79} motile=79.21 conc=253.4 tracks=101 |
| `casa_parameters(experimental_parameters=True, n_subpopulations=2)` | PASS | 0.9 | keys=['grades', 'grades_std', 'percent_motile', 'percent_motile_std', 'counts', 'track_count', 'cells_per_frame', 'concentration_M_per_ml', 'concentration_M_per_ml_std', 'dilution_factor', 'volume_ml' |
| `casa_parameters(hyperactivation esikleri, experimental)` | PASS | 1.2 | groundtruth: grades={'rapid': 47.52, 'slow': 28.71, 'non_progressive': 2.97, 'immotile': 20.79} motile=79.21 conc=61.21 tracks=101 |
| `casa_parameters(velocity_metric='XYZ') -> hata beklenir` | PASS | 1.1 | beklenen hata: ValueError: `velocity_metric` must be one of ('VAP', 'VCL', 'VSL'), got 'XYZ'. |
| `casa_parameters() kinematic YOKKEN -> hata beklenir` | PASS | 0.4 | beklenen hata: RuntimeError: No kinematic parameters found. Run `self.motility.kinematic_parameters()` before `casa_parameters()`. |
| `kinematic_parameters() tracking YOKKEN -> hata beklenir` | PASS | 0.0 | beklenen hata: RuntimeError: No frames could be read from: C:\Users\Esmer\OneDrive\Masaüstü\PYCASA TRY\pycasa_data\sys-casa\rawdata\sub-HC004\ses-01\sys-casa_sub-HC004_ses-01_run- |
| `kinematic_parameters() um_per_px=None iken` | **FAIL** | 0.5 | ValueError: `um_per_px` is required when conversion is requested. |
| `get_motility() track basina kinematik anahtarlar` | **FAIL** | 0.0 | MemoryError: Unable to allocate 229. MiB for an array with shape (61, 1024, 1280, 3) and data type uint8 |

## visualization (0/1)

| Test | Sonuc | Sure (s) | Not |
|---|---|---|---|
| `BOLUM visualization cokti` | **FAIL** | 0 | \Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\pycasa\utils\_video_helpers.py", line 62, in _convert_video_to_grayscale
    g = block[.. |
