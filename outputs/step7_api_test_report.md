# pycasa full API test: 134 PASS / 6 FAIL / 140 tests

Each section was run in its own Python process, on the first 21 frames of the HC004 default dataset.
For tests marked `-> expects error`, PASS means the function correctly raised an error.


## io (13/14)

| Test | Result | Time (s) | Note |
|---|---|---|---|
| `io.load_default_data(final_frame=20)` | PASS | 13.9 | frames=21 |
| `io.load_default_data(um_per_px/volume_ml/chamber_depth_um override)` | PASS | 1.1 | {'um_per_px': 0.5, 'volume_ml': 3.0, 'chamber_depth_um': 10.0} |
| `io.load_default_data(initial_frame=10, final_frame=20)` | PASS | 0.3 | frames=11 |
| `io.load_default_data(sampling_rate=15)` | PASS | 0.3 | fps=15.0 |
| `io.load_default_data(magnification='20x')` | PASS | 0.4 | magnification=20x |
| `io.load_default_data(download=False) from cache` | PASS | 0.3 | frames=21 |
| `session.io.load_default_data() wrapper` | PASS | 0.3 | um_per_px=0.24 |
| `session.io.load_default_data(volume_ml=...) wrapper/module signature parity` | **FAIL** | 0.0 | TypeError: _SessionIONamespace.load_default_data() got an unexpected keyword argument 'volume_ml' |
| `io.load_video(video, groundtruth_detections_path)` | PASS | 0.3 | frames=21 gt_frames=900 fps=30.0 |
| `io.load_video(video) without GT, sampling_rate=25` | PASS | 0.1 | fps=25.0 |
| `io.load_video(groundtruth_tracks_path=GT_DIR) (GT has no track ids)` | PASS | 0.3 | gt_tracks=1 |
| `io.load_video(dilution_factor=2)` | PASS | 0.0 | dilution=2.0 |
| `io.load_video(nonexistent file) -> expects error` | PASS | 0.0 | expected error: FileNotFoundError: Video file does not exist: C:\nope\x.avi |
| `session.io.load_video() wrapper` | PASS | 0.0 | frames=6 |

## casa (23/23)

| Test | Result | Time (s) | Note |
|---|---|---|---|
| `Casa.info()` | PASS | 0.0 | printed to screen |
| `Casa.copy() is it an independent copy` | PASS | 0.2 | new object=True, meta identical=True |
| `set_um_per_px(0.3)` | PASS | 0.2 | 0.3 |
| `set_volume_ml(1.5)` | PASS | 0.2 | 1.5 |
| `set_chamber_depth_um(10)` | PASS | 0.2 | 10.0 |
| `set_dilution_factor(2)` | PASS | 0.2 | 2.0 |
| `set_um_per_px(-1) -> expects ValueError` | PASS | 0.0 | expected error: ValueError: `um_per_px` must be > 0. |
| `set_volume_ml('abc') -> expects TypeError` | PASS | 0.0 | expected error: TypeError: `volume_ml` must be a numeric value. |
| `set_chamber_depth_um(0) -> expects error` | PASS | 0.0 | expected error: ValueError: `chamber_depth_um` must be > 0. |
| `set_dilution_factor(-5) -> expects error` | PASS | 0.0 | expected error: ValueError: `dilution_factor` must be > 0. |
| `get_casa() keys` | PASS | 0.0 | ['meta', 'video', 'detections', 'tracks', 'motility', 'assessment'] |
| `get_meta() keys` | PASS | 0.0 | ['chamber_depth_um', 'duration_sec', 'height', 'magnification', 'sampling_rate', 'total_duration_sec', 'total_number_frame', 'um_per_px', 'video_path', 'volume_ml', 'width'] |
| `get_video() keys` | PASS | 0.0 | ['path', 'initial_frame', 'final_frame', 'number_frame_used', 'original_video'] |
| `get_groundtruth() frame count` | PASS | 0.0 | 900 |
| `get_groundtruth_tracks() (should be empty)` | PASS | 0.0 | {} |
| `get_detections() (empty)` | PASS | 0.0 | {} |
| `get_detections(include_groundtruth=True)` | PASS | 0.0 | ['groundtruth', 'groundtruth_detections_path'] |
| `get_tracks() (empty)` | PASS | 0.0 | {} |
| `get_tracks(backend='sort') with no tracking` | PASS | 0.0 | {} |
| `get_motility() (empty)` | PASS | 0.0 | {} |
| `get_assessment() (empty)` | PASS | 0.0 | {} |
| `get_assesment() (misspelled alias)` | PASS | 0.0 | {} |
| `get_assessment() is it a live reference (mutation test)` | PASS | 0.0 | leaked into session=True |

## preprocessing (19/19)

| Test | Result | Time (s) | Note |
|---|---|---|---|
| `preprocessing.grayscale()` | PASS | 0.2 | ['original_video', 'grayscale_video'] |
| `preprocessing.grayscale(overwrite=True)` | PASS | 0.5 | original_video.shape=(21, 1024, 1280) |
| `preprocessing.binarization.otsu()` | PASS | 0.6 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.adaptive_gaussian()` | PASS | 0.5 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.adaptive_mean()` | PASS | 0.5 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.niblack()` | PASS | 1.3 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.sauvola()` | PASS | 1.4 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 255] |
| `preprocessing.binarization.urbano()` | PASS | 5.2 | ['original_video', 'grayscale_video', 'binary_video'] dtype=uint8 uniq=[0, 1] |
| `binarization.otsu() without grayscale (raw colour video)` | PASS | 0.9 | ['original_video', 'binary_video'] |
| `binarization.adaptive_gaussian(block_size=4 even) -> expects error` | PASS | 0.0 | expected error: ValueError: `block_size` must be an odd integer >= 3. |
| `binarization.niblack(window_size=0) -> expects error` | PASS | 0.0 | expected error: ValueError: `window_size` must be >= 3. |
| `preprocessing.normalization.clahe()` | PASS | 0.2 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.hist_equal()` | PASS | 1.6 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.log()` | PASS | 1.4 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.median()` | PASS | 1.3 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.min_max()` | PASS | 0.6 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=uint8 |
| `preprocessing.normalization.z_score()` | PASS | 0.8 | ['original_video', 'grayscale_video', 'binary_video', 'normalized_video'] dtype=float32 |
| `normalization.min_max(overwrite=True)` | PASS | 1.0 | ['original_video', 'normalized_video'] |
| `chain: grayscale -> clahe -> otsu` | PASS | 1.5 | ['original_video', 'grayscale_video', 'normalized_video', 'binary_video'] |

## detection_yolo26 (8/8)

| Test | Result | Time (s) | Note |
|---|---|---|---|
| `detection.yolo() default (yolo26) + evaluate_detections` | PASS | 20.4 | tp=2101 fp=1221 fn=26 P=63.25 R=98.78 F1=77.12 frames=21 |
| `detection.yolo(weights=<full ASCII path>) custom weights` | PASS | 2.3 | tp=2101 fp=1221 fn=26 P=63.25 R=98.78 F1=77.12 frames=21 |
| `detection.yolo(conf=0.5) high threshold` | PASS | 2.1 | tp=2068 fp=1141 fn=59 P=64.44 R=97.23 F1=77.51 frames=21 |
| `detection.yolo(conf=0.01) low threshold` | PASS | 2.6 | tp=2120 fp=4024 fn=7 P=34.51 R=99.67 F1=51.26 frames=21 |
| `detection.yolo(yolo_model='yolo99') -> expects error` | PASS | 0.2 | expected error: ValueError: `yolo_model` must be one of ('yolov5', 'yolo26'), got 'yolo99'. |
| `detection.yolo(weights='C:/nope.pt') -> expects error` | PASS | 0.2 | expected error: FileNotFoundError: Custom `weights` path was not found: 'C:/nope.pt'. On Windows use a raw string: r'D:\path\to\weights.pt' |
| `detection.yolo(download=False) managed weights in cache` | PASS | 2.3 | tp=2101 fp=1221 fn=26 P=63.25 R=98.78 F1=77.12 frames=21 |
| `get_detections() row format (yolo26, frame 0)` | PASS | 2.3 | [['0', '0.910138', '0.828910', '0.037355', '0.046788'], ['0', '0.556985', '0.449665', '0.036418', '0.045641']] |

## detection_classic (13/14)

| Test | Result | Time (s) | Note |
|---|---|---|---|
| `detection.detect_moving_cells(method='cv-gmg')` | PASS | 1.6 | tp=0 fp=1 fn=101 P=0.0 R=0.0 F1=0.0 frames=1 |
| `detection.detect_moving_cells(method='cv-mog')` | PASS | 0.8 | tp=69 fp=16 fn=32 P=81.18 R=68.32 F1=74.19 frames=1 |
| `detection.detect_moving_cells(method='cv-mog2')` | PASS | 0.5 | tp=90 fp=248 fn=11 P=26.63 R=89.11 F1=41.0 frames=1 |
| `detection.detect_moving_cells(method='gm')` | PASS | 6.1 | tp=79 fp=9 fn=22 P=89.77 R=78.22 F1=83.6 frames=1 |
| `detection.detect_moving_cells(method='gm', low_memory=True)` | PASS | 3.0 | tp=79 fp=9 fn=22 P=89.77 R=78.22 F1=83.6 frames=1 |
| `detection.detect_moving_cells(method='xyz') -> expects error` | PASS | 0.2 | expected error: ValueError: method xyz is invalid. |
| `detection.digital_washing() n_jobs=1` | PASS | 16.7 | tp=84 fp=15 fn=17 P=84.85 R=83.17 F1=84.0 frames=1 |
| `detection.digital_washing(n_jobs=4) parallel` | PASS | 18.5 | tp=84 fp=15 fn=17 P=84.85 R=83.17 F1=84.0 frames=1 |
| `detection.digital_washing(motion_threshold=5, blob_min_pixel_area=30)` | PASS | 18.3 | tp=58 fp=3 fn=43 P=95.08 R=57.43 F1=71.6 frames=1 |
| `detection.urbano_detection()` | PASS | 6.1 | tp=1920 fp=589 fn=207 P=76.52 R=90.27 F1=82.83 frames=21 |
| `detection.urbano_detection(blob_min_pixel_area=10, log_size=7)` | PASS | 6.1 | tp=1813 fp=546 fn=314 P=76.85 R=85.24 F1=80.83 frames=21 |
| `assessment.evaluate_detections(match_min_distance_pixel=10)` | PASS | 6.1 | {'tp': 1599, 'fp': 910, 'fn': 528, 'precision': np.float64(63.73), 'recall': np.float64(75.18), 'F0.5': np.float64(65.73), 'F1': np.float64(68.98), 'F2': np.float64(72.57), 'evaluated_frames': 21} |
| `assessment.evaluate_detections() with NO detection -> expects error` | **FAIL** | 0.2 | expected Exception not raised, result: <pycasa.casa.casa.Casa object at 0x00000279B497A240> |
| `detection overwrite warning (urbano -> moving_cells)` | PASS | 6.0 | detection frame count=1 |

## detection_yolov5 (3/3)

| Test | Result | Time (s) | Note |
|---|---|---|---|
| `detection.yolo(yolo_model='yolov5') + evaluate_detections` | PASS | 15.9 | tp=1539 fp=631 fn=588 P=70.92 R=72.36 F1=71.63 frames=21 |
| `detection.yolo(yolov5, conf=0.4)` | PASS | 2.1 | tp=1413 fp=315 fn=714 P=81.77 R=66.43 F1=73.31 frames=21 |
| `yolo26 AFTER YOLOv5 (ordering dependency test)` | PASS | 3.0 | tp=2101 fp=1025 fn=26 P=67.21 R=98.78 F1=79.99 frames=21 |

## tracking (18/19)

| Test | Result | Time (s) | Note |
|---|---|---|---|
| `tracking.sort() GT only` | PASS | 1.4 | backend=sort groundtruth:114 track |
| `tracking.sort(max_age=5, min_hits=1, iou_threshold=0.3)` | PASS | 0.4 | backend=sort groundtruth:168 track |
| `tracking.sort(initial_frame=10)` | PASS | 0.3 | backend=sort groundtruth:105 track |
| `tracking.sort(delete_temp=False)` | PASS | 0.4 | backend=sort groundtruth:114 track |
| `tracking.sort() GT + yolo26 (two sources)` | PASS | 4.7 | backend=sort groundtruth:114 track / yolo26:239 track |
| `tracking.sort(skip_gt=True) yolo26 only` | PASS | 2.6 | backend=sort yolo26:239 track |
| `tracking.sort(skip_gt=True) with NO detection` | PASS | 0.2 | backend=sort  |
| `tracking.jpdaf() GT only` | PASS | 1.5 | backend=jpdaf groundtruth:115 track |
| `tracking.jpdaf(frame_rate=60, p_delete=0.3, sigma_n_um=1)` | PASS | 1.5 | backend=jpdaf groundtruth:138 track |
| `tracking.jpdaf(position_gate=5, velocity_gate_um=20, detection_probability=0.9)` | PASS | 11.5 | backend=jpdaf groundtruth:81 track |
| `tracking.jpdaf(skip_gt=True) yolo26` | PASS | 6.1 | backend=jpdaf yolo26:203 track |
| `tracking.deepsort() GT only` | PASS | 0.8 | backend=deepsort groundtruth:127 track |
| `tracking.deepsort(max_age=10, n_init=2, max_iou_distance=0.5)` | PASS | 0.8 | backend=deepsort groundtruth:180 track |
| `tracking overwrite: sort -> jpdaf, get_tracks() single backend` | PASS | 1.6 | backends=['jpdaf'] |
| `get_tracks(backend='jpdaf') while sort is present` | PASS | 0.4 | {} |
| `assessment.evaluate_tracks() GT-sort vs yolo26-sort` | PASS | 3.7 | {} |
| `assessment.evaluate_tracks(match_min_distance_pixel=10, backend='sort')` | PASS | 3.0 | ok |
| `assessment.evaluate_tracks() with a single source (GT only)` | PASS | 0.4 | {} |
| `assessment.evaluate_tracks() with NO tracking -> expects error` | **FAIL** | 0.2 | expected Exception not raised, result: <pycasa.casa.casa.Casa object at 0x00000206E31A84D0> |

## motility (15/18)

| Test | Result | Time (s) | Note |
|---|---|---|---|
| `kinematic_parameters() + casa_parameters() [sort/GT]` | PASS | 1.3 | groundtruth: grades={'rapid': 47.52, 'slow': 28.71, 'non_progressive': 2.97, 'immotile': 20.79} motile=79.21 conc=61.21 tracks=101 |
| `motility [jpdaf/GT]` | PASS | 4.3 | groundtruth: grades={'rapid': 41.51, 'slow': 31.13, 'non_progressive': 2.83, 'immotile': 24.53} motile=75.47 conc=67.76 tracks=106 |
| `motility [deepsort/GT]` | PASS | 2.3 | groundtruth: grades={'rapid': 44.33, 'slow': 29.9, 'non_progressive': 5.15, 'immotile': 20.62} motile=79.38 conc=63.02 tracks=97 |
| `motility [sort/GT+yolo26 two sources]` | PASS | 9.0 | groundtruth: grades={'rapid': 47.52, 'slow': 28.71, 'non_progressive': 2.97, 'immotile': 20.79} motile=79.21 conc=61.21 tracks=101 |
| `kinematic_parameters(window_size=15, overlap=0.5, smoothing_window=3, denoise_window=1, min_frame_rate_warn=0)` | PASS | 0.9 | groundtruth: grades={'rapid': 52.29, 'slow': 9.17, 'non_progressive': 29.36, 'immotile': 9.17} motile=90.83 conc=61.21 tracks=109 |
| `kinematic_parameters(frame_rate=60)` | PASS | 0.8 | groundtruth: grades={'rapid': 80.2, 'slow': 0.0, 'non_progressive': 17.82, 'immotile': 1.98} motile=98.02 conc=61.21 tracks=101 |
| `kinematic_parameters(conversion_required=False) pixel units` | PASS | 0.8 | groundtruth: grades={'rapid': 47.52, 'slow': 28.71, 'non_progressive': 2.97, 'immotile': 20.79} motile=79.21 conc=61.21 tracks=101 |
| `kinematic_parameters(overlap=1.5) invalid -> expects error` | **FAIL** | 1.4 | expected Exception not raised, result: <pycasa.casa.casa.Casa object at 0x00000261CD952270> |
| `casa_parameters(velocity_metric='VAP', rapid=25, immotile=10, progressive_str=0.5)` | PASS | 0.8 | groundtruth: grades={'rapid': 36.63, 'slow': 41.58, 'non_progressive': 0.99, 'immotile': 20.79} motile=79.21 conc=61.21 tracks=101 |
| `casa_parameters(velocity_metric='VSL')` | PASS | 0.8 | groundtruth: grades={'rapid': 12.87, 'slow': 42.57, 'non_progressive': 0.0, 'immotile': 44.55} motile=55.45 conc=61.21 tracks=101 |
| `casa_parameters(volume_ml=1, chamber_depth_um=10, dilution_factor=2)` | PASS | 0.8 | groundtruth: grades={'rapid': 47.52, 'slow': 28.71, 'non_progressive': 2.97, 'immotile': 20.79} motile=79.21 conc=253.4 tracks=101 |
| `casa_parameters(experimental_parameters=True, n_subpopulations=2)` | PASS | 0.9 | keys=['grades', 'grades_std', 'percent_motile', 'percent_motile_std', 'counts', 'track_count', 'cells_per_frame', 'concentration_M_per_ml', 'concentration_M_per_ml_std', 'dilution_factor', 'volume_ml' |
| `casa_parameters(hyperactivation thresholds, experimental)` | PASS | 0.9 | groundtruth: grades={'rapid': 47.52, 'slow': 28.71, 'non_progressive': 2.97, 'immotile': 20.79} motile=79.21 conc=61.21 tracks=101 |
| `casa_parameters(velocity_metric='XYZ') -> expects error` | PASS | 0.9 | expected error: ValueError: `velocity_metric` must be one of ('VAP', 'VCL', 'VSL'), got 'XYZ'. |
| `casa_parameters() with NO kinematic -> expects error` | PASS | 0.8 | expected error: RuntimeError: No kinematic parameters found. Run `self.motility.kinematic_parameters()` before `casa_parameters()`. |
| `kinematic_parameters() with NO tracking -> expects error` | **FAIL** | 0.4 | expected Exception not raised, result: <pycasa.casa.casa.Casa object at 0x00000261DA4DC260> |
| `kinematic_parameters() when um_per_px=None` | **FAIL** | 0.4 | ValueError: `um_per_px` is required when conversion is requested. |
| `get_motility() per-track kinematic keys` | PASS | 0.9 | ['VCL', 'VSL', 'VAP', 'LIN', 'ALH', 'WOB', 'STR', 'MAD', 'frame_ranges'] |

## visualization (22/22)

| Test | Result | Time (s) | Note |
|---|---|---|---|
| `visualization.plot_frame('original')` | PASS | 0.2 | png saved |
| `visualization.plot_frame(frame_index=5, show_detections=False)` | PASS | 0.1 | png saved |
| `visualization.plot_frame('binarized') with NO binarization -> expects error` | PASS | 0.0 | expected error: ValueError: No binarized video found. Run `self.preprocessing.binarization.otsu()` first. |
| `visualization.plot_frame(frame_index=999) -> expects error` | PASS | 0.0 | expected error: ValueError: `frame_index`=999 is out of range for 61 frame(s). |
| `visualization.timelapse() default (GT overlay)` | PASS | 0.2 | png saved |
| `visualization.timelapse(image_type='original') legacy alias` | PASS | 0.1 | png saved |
| `visualization.timelapse('normalized') with NO such layer -> expects error` | PASS | 0.0 | expected error: ValueError: `normalized` video is not available in casa['video']. Run the relevant preprocessing step first. |
| `visualization.plot_frame(['original','grayscale','binarized','normalized'])` | PASS | 0.5 | png saved |
| `visualization.plot_frame('grayscale+binarized')` | PASS | 0.4 | png saved |
| `visualization.timelapse(tracks+ids+custom colours+max_track_gap)` | PASS | 0.9 | png saved |
| `visualization.interactive_motility_calculator()` | PASS | 1.0 | png saved |
| `visualization.interactive_motility_calculator(frame_rate=60, smoothing_window=3)` | PASS | 0.8 | png saved |
| `visualization.plot_frame('moving_cells')` | PASS | 0.2 | png saved |
| `visualization.timelapse('moving_cells')` | PASS | 0.2 | png saved |
| `visualization.motility_radar() with NO motility -> expects error` | PASS | 0.0 | expected error: RuntimeError: No motility parameters found under 'kinematic_parameters'. Run `self.motility.kinematic_parameters()` first. |
| `visualization.motility_density_scatter() with NO motility -> expects error` | PASS | 0.0 | expected error: RuntimeError: No motility parameters found under 'kinematic_parameters'. Run `self.motility.kinematic_parameters()` first. |
| `visualization.interactive_motility_calculator() with NO tracking -> expects error` | PASS | 0.0 | expected error: RuntimeError: No tracks found. Run tracking first, or load imported ground-truth tracks via load_video(groundtruth_tracks_path=...). |
| `visualization.motility_radar()` | PASS | 0.2 | png saved |
| `visualization.motility_radar(show_legend=False, show_text=False)` | PASS | 0.1 | png saved |
| `visualization.motility_radar(axis=<supplied polar axis>)` | PASS | 0.1 | png saved |
| `visualization.motility_density_scatter()` | PASS | 0.3 | png saved |
| `meta['last_visualization'] was it written` | PASS | 0.0 | {'type': 'motility_density_scatter', 'tracking_backend': 'sort', 'detection_method': 'groundtruth'} |
