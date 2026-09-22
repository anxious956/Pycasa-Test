"""Step 7: run EVERY public pycasa function one by one against the HC004 data.

Usage:
    python scripts/step7_full_api_test.py            # runs all sections in separate processes
    python scripts/step7_full_api_test.py io         # a single section

Why section by section: every Casa session keeps the video in RAM (21 frames ~82 MiB) and
`copy()` does a full deepcopy. Running them all in one process raises MemoryError.
Also, importing YOLOv5 changes the YOLO26 result in the same process; section isolation fixes that too.

Results: outputs/step7_api_test_results.json + outputs/step7_api_test_report.md
Figures are saved to outputs/step7_figs/*.png instead of being shown in a window.
"""
import os, sys, time, json, gc, traceback

os.environ.setdefault("MPLBACKEND", "Agg")
import numpy as np
import matplotlib.pyplot as plt

FIG_DIR = "outputs/step7_figs"
RESULT_JSON = "outputs/step7_api_test_results.json"
os.makedirs(FIG_DIR, exist_ok=True)

_fig_counter = [0]
CURRENT = ["init"]

def _fake_show(*a, **k):
    for num in plt.get_fignums():
        _fig_counter[0] += 1
        try:
            plt.figure(num).savefig(f"{FIG_DIR}/{CURRENT[0]}_{_fig_counter[0]:02d}.png", dpi=70)
        except Exception:
            pass
    plt.close("all")

plt.show = _fake_show
# Start the backend for real first (otherwise _backend_mod stays None and FigureCanvas errors out),
# then stop pycasa from switching to TkAgg: every request is redirected to Agg.
_real_switch = plt.switch_backend
_real_switch("Agg")
plt.switch_backend = lambda *a, **k: None

import pycasa as pc

RESULTS = []
FRAMES = 20                                         # final_frame -> 21 frames (~82 MiB/session)
# Data and weights live inside the project folder (see setup_env.bat)
PROJ_ROOT = os.environ.get("PYCASA_PROJECT_ROOT") or os.path.abspath(".")
PROJ_DATA = os.environ.get("PYCASA_DATA") or os.path.join(PROJ_ROOT, "pycasa_data")
DATA = os.path.join(PROJ_DATA, "sys-casa/rawdata/sub-HC004/ses-01")
VIDEO = f"{DATA}/sys-casa_sub-HC004_ses-01_run-005_video.avi"
GT_DIR = f"{DATA}/sys-casa_sub-HC004_ses-01_run-005_gt"
W_Y26 = os.path.join(PROJ_ROOT, "yolo26-weights/sys-casa_yolo26s.pt")


def run(name, fn, expect_error=None):
    """Run a single API call and record PASS/FAIL."""
    CURRENT[0] = "".join(c if c.isalnum() else "_" for c in name)[:50]
    t0 = time.time()
    print(f"\n>>> {name}", flush=True)
    try:
        out = fn()
        dt = round(time.time() - t0, 1)
        if expect_error:
            RESULTS.append({"section": SECTION, "name": name, "status": "FAIL", "sec": dt,
                            "note": f"expected {expect_error.__name__} not raised, result: {str(out)[:150]}"})
            print(f"    FAIL (expected {expect_error.__name__} not raised)", flush=True)
        else:
            RESULTS.append({"section": SECTION, "name": name, "status": "PASS", "sec": dt,
                            "note": out if isinstance(out, str) else ""})
            print(f"    PASS {dt}s {out if isinstance(out, str) else ''}", flush=True)
    except Exception as e:
        dt = round(time.time() - t0, 1)
        if expect_error and isinstance(e, expect_error):
            RESULTS.append({"section": SECTION, "name": name, "status": "PASS", "sec": dt,
                            "note": f"expected error: {type(e).__name__}: {str(e)[:150]}"})
            print(f"    PASS (expected error) {type(e).__name__}: {str(e)[:150]}", flush=True)
        else:
            RESULTS.append({"section": SECTION, "name": name, "status": "FAIL", "sec": dt,
                            "note": f"{type(e).__name__}: {str(e)[:300]}"})
            print(f"    FAIL {type(e).__name__}: {str(e)[:300]}", flush=True)
            traceback.print_exc(limit=2)
    finally:
        gc.collect()


def fresh(**kw):
    """A new session; use this instead of copy() (deepcopy eats 191 MiB)."""
    kw.setdefault("final_frame", FRAMES)
    kw.setdefault("verbose", False)
    return pc.io.load_default_data(**kw)


# =========================================================== SECTION: io
def sec_io():
    run("io.load_default_data(final_frame=20)",
        lambda: f"frames={fresh().get_video()['number_frame_used']}")
    run("io.load_default_data(um_per_px/volume_ml/chamber_depth_um override)",
        lambda: str({k: fresh(um_per_px=0.5, volume_ml=3, chamber_depth_um=10).get_meta()[k]
                     for k in ("um_per_px", "volume_ml", "chamber_depth_um")}))
    run("io.load_default_data(initial_frame=10, final_frame=20)",
        lambda: f"frames={fresh(initial_frame=10).get_video()['number_frame_used']}")
    run("io.load_default_data(sampling_rate=15)",
        lambda: f"fps={fresh(sampling_rate=15).get_meta()['sampling_rate']}")
    run("io.load_default_data(magnification='20x')",
        lambda: f"magnification={fresh(magnification='20x').get_meta()['magnification']}")
    run("io.load_default_data(download=False) from cache",
        lambda: f"frames={fresh(download=False).get_video()['number_frame_used']}")
    run("session.io.load_default_data() wrapper",
        lambda: f"um_per_px={pc.Casa().io.load_default_data(final_frame=5, verbose=False).get_meta()['um_per_px']}")
    run("session.io.load_default_data(volume_ml=...) wrapper/module signature parity",
        lambda: pc.Casa().io.load_default_data(final_frame=5, volume_ml=2.2, verbose=False))
    run("io.load_video(video, groundtruth_detections_path)",
        lambda: (lambda s: f"frames={s.get_video()['number_frame_used']} gt_frames={len(s.get_groundtruth())} "
                           f"fps={s.get_meta()['sampling_rate']}")(
            pc.io.load_video(VIDEO, groundtruth_detections_path=GT_DIR, final_frame=20,
                             um_per_px=0.24, volume_ml=2.2, chamber_depth_um=20.7,
                             verbose=False, show_progress=False)))
    run("io.load_video(video) without GT, sampling_rate=25",
        lambda: f"fps={pc.io.load_video(VIDEO, final_frame=10, sampling_rate=25, verbose=False, show_progress=False).get_meta()['sampling_rate']}")
    run("io.load_video(groundtruth_tracks_path=GT_DIR) (GT has no track ids)",
        lambda: f"gt_tracks={len(pc.io.load_video(VIDEO, groundtruth_tracks_path=GT_DIR, final_frame=10, verbose=False, show_progress=False).get_groundtruth_tracks())}")
    run("io.load_video(dilution_factor=2)",
        lambda: f"dilution={pc.io.load_video(VIDEO, final_frame=5, dilution_factor=2, verbose=False, show_progress=False).get_meta().get('dilution_factor')}")
    run("io.load_video(nonexistent file) -> expects error",
        lambda: pc.io.load_video("C:/nope/x.avi", verbose=False), expect_error=Exception)
    run("session.io.load_video() wrapper",
        lambda: f"frames={pc.Casa().io.load_video(VIDEO, final_frame=5, verbose=False, show_progress=False).get_video()['number_frame_used']}")


# =========================================================== SECTION: casa (getter/setter)
def sec_casa():
    s = fresh()
    run("Casa.info()", lambda: (s.info(), "printed to screen")[1])
    run("Casa.copy() is it an independent copy",
        lambda: (lambda c: f"new object={c is not s}, meta identical={c.get_meta() == s.get_meta()}")(s.copy()))
    run("set_um_per_px(0.3)", lambda: str(fresh().set_um_per_px(0.3).get_meta()["um_per_px"]))
    run("set_volume_ml(1.5)", lambda: str(fresh().set_volume_ml(1.5).get_meta()["volume_ml"]))
    run("set_chamber_depth_um(10)", lambda: str(fresh().set_chamber_depth_um(10).get_meta()["chamber_depth_um"]))
    run("set_dilution_factor(2)", lambda: str(fresh().set_dilution_factor(2).get_meta().get("dilution_factor")))
    run("set_um_per_px(-1) -> expects ValueError", lambda: s.set_um_per_px(-1), expect_error=ValueError)
    run("set_volume_ml('abc') -> expects TypeError", lambda: s.set_volume_ml("abc"), expect_error=Exception)
    run("set_chamber_depth_um(0) -> expects error", lambda: s.set_chamber_depth_um(0), expect_error=Exception)
    run("set_dilution_factor(-5) -> expects error", lambda: s.set_dilution_factor(-5), expect_error=Exception)
    run("get_casa() keys", lambda: str(list(s.get_casa().keys())))
    run("get_meta() keys", lambda: str(sorted(s.get_meta().keys())))
    run("get_video() keys", lambda: str(list(s.get_video().keys())))
    run("get_groundtruth() frame count", lambda: str(len(s.get_groundtruth())))
    run("get_groundtruth_tracks() (should be empty)", lambda: str(s.get_groundtruth_tracks()))
    run("get_detections() (empty)", lambda: str(s.get_detections()))
    run("get_detections(include_groundtruth=True)", lambda: str(list(s.get_detections(include_groundtruth=True).keys())))
    run("get_tracks() (empty)", lambda: str(s.get_tracks()))
    run("get_tracks(backend='sort') with no tracking", lambda: str(s.get_tracks(backend="sort")))
    run("get_motility() (empty)", lambda: str(s.get_motility()))
    run("get_assessment() (empty)", lambda: str(s.get_assessment()))
    run("get_assesment() (misspelled alias)", lambda: str(s.get_assesment()))
    run("get_assessment() is it a live reference (mutation test)",
        lambda: (lambda a: (a.update({"_probe": 1}), f"leaked into session={'_probe' in s.get_assessment()}")[1])(s.get_assessment()))


# =========================================================== SECTION: preprocessing
def sec_preprocessing():
    def vkeys(x):
        return str([k for k in x.get_video() if k.endswith("video")])

    p = fresh()
    run("preprocessing.grayscale()", lambda: (p.preprocessing.grayscale(show_progress=False), vkeys(p))[1])
    run("preprocessing.grayscale(overwrite=True)",
        lambda: (lambda c: (c.preprocessing.grayscale(overwrite=True, show_progress=False),
                            f"original_video.shape={np.asarray(c.get_video()['original_video']).shape}")[1])(fresh()))
    for meth, kw in [("otsu", {}), ("adaptive_gaussian", {"block_size": 15, "c": 3}), ("adaptive_mean", {}),
                     ("niblack", {"window_size": 21}), ("sauvola", {}), ("urbano", {})]:
        run(f"preprocessing.binarization.{meth}()",
            (lambda m=meth, k=kw: (getattr(p.preprocessing.binarization, m)(show_progress=False, **k),
                                   f"{vkeys(p)} dtype={np.asarray(p.get_video()['binary_video']).dtype} "
                                   f"uniq={np.unique(np.asarray(p.get_video()['binary_video'])[0])[:4].tolist()}")[1]))
    run("binarization.otsu() without grayscale (raw colour video)",
        lambda: (lambda c: (c.preprocessing.binarization.otsu(show_progress=False), vkeys(c))[1])(fresh()))
    run("binarization.adaptive_gaussian(block_size=4 even) -> expects error",
        lambda: p.preprocessing.binarization.adaptive_gaussian(block_size=4, show_progress=False),
        expect_error=Exception)
    run("binarization.niblack(window_size=0) -> expects error",
        lambda: p.preprocessing.binarization.niblack(window_size=0, show_progress=False), expect_error=Exception)
    for meth, kw in [("clahe", {"clip_limit": 3.0, "tile_grid_size": (4, 4)}), ("hist_equal", {}),
                     ("log", {}), ("median", {}), ("min_max", {}), ("z_score", {})]:
        run(f"preprocessing.normalization.{meth}()",
            (lambda m=meth, k=kw: (getattr(p.preprocessing.normalization, m)(show_progress=False, **k),
                                   f"{vkeys(p)} dtype={np.asarray(p.get_video()['normalized_video']).dtype}")[1]))
    run("normalization.min_max(overwrite=True)",
        lambda: (lambda c: (c.preprocessing.normalization.min_max(overwrite=True, show_progress=False), vkeys(c))[1])(fresh()))
    run("chain: grayscale -> clahe -> otsu",
        lambda: (lambda c: (c.preprocessing.grayscale(show_progress=False),
                            c.preprocessing.normalization.clahe(show_progress=False),
                            c.preprocessing.binarization.otsu(show_progress=False), vkeys(c))[3])(fresh()))


# =========================================================== SECTION: detection
def _det_eval(sess):
    sess.assessment.evaluate_detections()
    a = sess.get_assessment()["detection"]
    return f"tp={a['tp']} fp={a['fp']} fn={a['fn']} P={a['precision']} R={a['recall']} F1={a['F1']} frames={a['evaluated_frames']}"

def sec_detection_yolo26():
    run("detection.yolo() default (yolo26) + evaluate_detections",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.yolo(weights=<full ASCII path>) custom weights",
        lambda: (lambda c: (c.detection.yolo(weights=W_Y26, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.yolo(conf=0.5) high threshold",
        lambda: (lambda c: (c.detection.yolo(conf=0.5, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.yolo(conf=0.01) low threshold",
        lambda: (lambda c: (c.detection.yolo(conf=0.01, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.yolo(yolo_model='yolo99') -> expects error",
        lambda: fresh().detection.yolo(yolo_model="yolo99", show_progress=False), expect_error=Exception)
    run("detection.yolo(weights='C:/nope.pt') -> expects error",
        lambda: fresh().detection.yolo(weights="C:/nope.pt", show_progress=False), expect_error=Exception)
    run("detection.yolo(download=False) managed weights in cache",
        lambda: (lambda c: (c.detection.yolo(download=False, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("get_detections() row format (yolo26, frame 0)",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            str(np.asarray(c.get_detections()["0"])[:2].tolist()))[1])(fresh()))

def sec_detection_yolov5():
    run("detection.yolo(yolo_model='yolov5') + evaluate_detections",
        lambda: (lambda c: (c.detection.yolo(yolo_model="yolov5", show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.yolo(yolov5, conf=0.4)",
        lambda: (lambda c: (c.detection.yolo(yolo_model="yolov5", conf=0.4, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("yolo26 AFTER YOLOv5 (ordering dependency test)",
        lambda: (lambda c: (c.detection.yolo(yolo_model="yolov5", show_progress=False, verbose=False),
                            c.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False),
                            _det_eval(c))[2])(fresh()))

def sec_detection_classic():
    for m in ("cv-gmg", "cv-mog", "cv-mog2", "gm"):
        run(f"detection.detect_moving_cells(method='{m}')",
            (lambda mm=m: (lambda c: (c.detection.detect_moving_cells(method=mm, show_progress=False, verbose=False),
                                      _det_eval(c))[1])(fresh())))
    run("detection.detect_moving_cells(method='gm', low_memory=True)",
        lambda: (lambda c: (c.detection.detect_moving_cells(method="gm", low_memory=True, show_progress=False, verbose=False),
                            _det_eval(c))[1])(fresh()))
    run("detection.detect_moving_cells(method='xyz') -> expects error",
        lambda: fresh().detection.detect_moving_cells(method="xyz", show_progress=False), expect_error=Exception)
    run("detection.digital_washing() n_jobs=1",
        lambda: (lambda c: (c.detection.digital_washing(show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.digital_washing(n_jobs=4) parallel",
        lambda: (lambda c: (c.detection.digital_washing(n_jobs=4, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.digital_washing(motion_threshold=5, blob_min_pixel_area=30)",
        lambda: (lambda c: (c.detection.digital_washing(motion_threshold=5, blob_min_pixel_area=30,
                                                        show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.urbano_detection()",
        lambda: (lambda c: (c.detection.urbano_detection(show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.urbano_detection(blob_min_pixel_area=10, log_size=7)",
        lambda: (lambda c: (c.detection.urbano_detection(blob_min_pixel_area=10, log_size=7,
                                                         show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("assessment.evaluate_detections(match_min_distance_pixel=10)",
        lambda: (lambda c: (c.detection.urbano_detection(show_progress=False, verbose=False),
                            c.assessment.evaluate_detections(match_min_distance_pixel=10),
                            str(c.get_assessment()["detection"]))[2])(fresh()))
    run("assessment.evaluate_detections() with NO detection -> expects error",
        lambda: fresh().assessment.evaluate_detections(), expect_error=Exception)
    run("detection overwrite warning (urbano -> moving_cells)",
        lambda: (lambda c: (c.detection.urbano_detection(show_progress=False, verbose=False),
                            c.detection.detect_moving_cells(show_progress=False, verbose=False),
                            f"detection frame count={len(c.get_detections())}")[2])(fresh()))


# =========================================================== SECTION: tracking
def _trk_info(c):
    tr = c.get_tracks()
    if not tr:
        return "tracks empty"
    b = list(tr.keys())[0]
    return f"backend={b} " + " | ".join(f"{src}:{len(tr[b][src])} track" for src in tr[b])

def sec_tracking():
    run("tracking.sort() GT only",
        lambda: (lambda c: (c.tracking.sort(show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.sort(max_age=5, min_hits=1, iou_threshold=0.3)",
        lambda: (lambda c: (c.tracking.sort(max_age=5, min_hits=1, iou_threshold=0.3, show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.sort(initial_frame=10)",
        lambda: (lambda c: (c.tracking.sort(initial_frame=10, show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.sort(delete_temp=False)",
        lambda: (lambda c: (c.tracking.sort(delete_temp=False, show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.sort() GT + yolo26 (two sources)",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            c.tracking.sort(show_progress=False, verbose=False), _trk_info(c))[2])(fresh()))
    run("tracking.sort(skip_gt=True) yolo26 only",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            c.tracking.sort(skip_gt=True, show_progress=False, verbose=False), _trk_info(c))[2])(fresh()))
    run("tracking.sort(skip_gt=True) with NO detection",
        lambda: (lambda c: (c.tracking.sort(skip_gt=True, show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.jpdaf() GT only",
        lambda: (lambda c: (c.tracking.jpdaf(show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.jpdaf(frame_rate=60, p_delete=0.3, sigma_n_um=1)",
        lambda: (lambda c: (c.tracking.jpdaf(frame_rate=60, p_delete=0.3, sigma_n_um=1.0, show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.jpdaf(position_gate=5, velocity_gate_um=20, detection_probability=0.9)",
        lambda: (lambda c: (c.tracking.jpdaf(position_gate=5, velocity_gate_um=20, detection_probability=0.9,
                                             show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.jpdaf(skip_gt=True) yolo26",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            c.tracking.jpdaf(skip_gt=True, show_progress=False, verbose=False), _trk_info(c))[2])(fresh()))
    run("tracking.deepsort() GT only",
        lambda: (lambda c: (c.tracking.deepsort(show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.deepsort(max_age=10, n_init=2, max_iou_distance=0.5)",
        lambda: (lambda c: (c.tracking.deepsort(max_age=10, n_init=2, max_iou_distance=0.5,
                                                show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking overwrite: sort -> jpdaf, get_tracks() single backend",
        lambda: (lambda c: (c.tracking.sort(show_progress=False, verbose=False),
                            c.tracking.jpdaf(show_progress=False, verbose=False),
                            f"backends={list(c.get_tracks().keys())}")[2])(fresh()))
    run("get_tracks(backend='jpdaf') while sort is present",
        lambda: (lambda c: (c.tracking.sort(show_progress=False, verbose=False),
                            str(c.get_tracks(backend="jpdaf")))[1])(fresh()))
    run("assessment.evaluate_tracks() GT-sort vs yolo26-sort",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            c.tracking.sort(show_progress=False, verbose=False),
                            c.assessment.evaluate_tracks(),
                            json.dumps(c.get_assessment().get("tracks", {}), default=str)[:400])[3])(fresh()))
    run("assessment.evaluate_tracks(match_min_distance_pixel=10, backend='sort')",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            c.tracking.sort(show_progress=False, verbose=False),
                            c.assessment.evaluate_tracks(match_min_distance_pixel=10, backend="sort"),
                            "ok")[3])(fresh()))
    run("assessment.evaluate_tracks() with a single source (GT only)",
        lambda: (lambda c: (c.tracking.sort(show_progress=False, verbose=False),
                            c.assessment.evaluate_tracks(),
                            json.dumps(c.get_assessment().get("tracks", {}), default=str)[:300])[2])(fresh()))
    run("assessment.evaluate_tracks() with NO tracking -> expects error",
        lambda: fresh().assessment.evaluate_tracks(), expect_error=Exception)


# =========================================================== SECTION: motility
def _mot(c, kin=None, casa=None):
    c.motility.kinematic_parameters(show_progress=False, verbose=False, **(kin or {}))
    c.motility.casa_parameters(verbose=False, **(casa or {}))
    m = c.get_motility()["casa_parameters"]
    src = list(m)[0]
    g = m[src]
    return f"{src}: grades={g['grades']} motile={g['percent_motile']} conc={g['concentration_M_per_ml']} tracks={g['track_count']}"

def _sorted_gt():
    c = fresh()
    c.tracking.sort(show_progress=False, verbose=False)
    return c

def sec_motility():
    run("kinematic_parameters() + casa_parameters() [sort/GT]", lambda: _mot(_sorted_gt()))
    run("motility [jpdaf/GT]",
        lambda: (lambda c: (c.tracking.jpdaf(show_progress=False, verbose=False), _mot(c))[1])(fresh()))
    run("motility [deepsort/GT]",
        lambda: (lambda c: (c.tracking.deepsort(show_progress=False, verbose=False), _mot(c))[1])(fresh()))
    run("motility [sort/GT+yolo26 two sources]",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            c.tracking.sort(show_progress=False, verbose=False), _mot(c))[2])(fresh()))
    run("kinematic_parameters(window_size=15, overlap=0.5, smoothing_window=3, denoise_window=1, min_frame_rate_warn=0)",
        lambda: _mot(_sorted_gt(), kin=dict(window_size=15, overlap=0.5, smoothing_window=3,
                                            denoise_window=1, min_frame_rate_warn=0)))
    run("kinematic_parameters(frame_rate=60)", lambda: _mot(_sorted_gt(), kin=dict(frame_rate=60)))
    run("kinematic_parameters(conversion_required=False) pixel units",
        lambda: _mot(_sorted_gt(), kin=dict(conversion_required=False)))
    run("kinematic_parameters(overlap=1.5) invalid -> expects error",
        lambda: _sorted_gt().motility.kinematic_parameters(overlap=1.5, show_progress=False, verbose=False),
        expect_error=Exception)
    run("casa_parameters(velocity_metric='VAP', rapid=25, immotile=10, progressive_str=0.5)",
        lambda: _mot(_sorted_gt(), casa=dict(velocity_metric="VAP", rapid_threshold=25,
                                             immotile_threshold=10, progressive_str_threshold=0.5)))
    run("casa_parameters(velocity_metric='VSL')", lambda: _mot(_sorted_gt(), casa=dict(velocity_metric="VSL")))
    run("casa_parameters(volume_ml=1, chamber_depth_um=10, dilution_factor=2)",
        lambda: _mot(_sorted_gt(), casa=dict(volume_ml=1, chamber_depth_um=10, dilution_factor=2)))
    run("casa_parameters(experimental_parameters=True, n_subpopulations=2)",
        lambda: (lambda c: (_mot(c, casa=dict(experimental_parameters=True, n_subpopulations=2)),
                            "keys=" + str(list(c.get_motility()["casa_parameters"]["groundtruth"].keys())))[1])(_sorted_gt()))
    run("casa_parameters(hyperactivation thresholds, experimental)",
        lambda: _mot(_sorted_gt(), casa=dict(experimental_parameters=True, hyperactivation_vcl_threshold=30,
                                             hyperactivation_alh_threshold=1.0, hyperactivation_lin_threshold=0.5)))
    run("casa_parameters(velocity_metric='XYZ') -> expects error",
        lambda: _mot(_sorted_gt(), casa=dict(velocity_metric="XYZ")), expect_error=Exception)
    run("casa_parameters() with NO kinematic -> expects error",
        lambda: _sorted_gt().motility.casa_parameters(verbose=False), expect_error=Exception)
    run("kinematic_parameters() with NO tracking -> expects error",
        lambda: fresh().motility.kinematic_parameters(show_progress=False, verbose=False), expect_error=Exception)
    run("kinematic_parameters() when um_per_px=None",
        lambda: (lambda c: (c.tracking.sort(show_progress=False, verbose=False),
                            c.motility.kinematic_parameters(show_progress=False, verbose=False),
                            f"is kinematic empty={not c.get_motility().get('kinematic_parameters')}")[2])(
            pc.io.load_video(VIDEO, groundtruth_detections_path=GT_DIR, final_frame=20, verbose=False, show_progress=False)))
    run("get_motility() per-track kinematic keys",
        lambda: (lambda c: (_mot(c), str(list(next(iter(c.get_motility()["kinematic_parameters"]["groundtruth"].values())).keys())))[1])(_sorted_gt()))


# =========================================================== SECTION: visualization
def sec_visualization():
    s = fresh()
    run("visualization.plot_frame('original')", lambda: (s.visualization.plot_frame("original"), "png saved")[1])
    run("visualization.plot_frame(frame_index=5, show_detections=False)",
        lambda: (s.visualization.plot_frame("original", frame_index=5, show_detections=False), "png saved")[1])
    run("visualization.plot_frame('binarized') with NO binarization -> expects error",
        lambda: s.visualization.plot_frame("binarized"), expect_error=ValueError)
    run("visualization.plot_frame(frame_index=999) -> expects error",
        lambda: s.visualization.plot_frame(frame_index=999), expect_error=ValueError)
    run("visualization.timelapse() default (GT overlay)",
        lambda: (s.visualization.timelapse(), "png saved")[1])
    run("visualization.timelapse(image_type='original') legacy alias",
        lambda: (s.visualization.timelapse(image_type="original"), "png saved")[1])
    run("visualization.timelapse('normalized') with NO such layer -> expects error",
        lambda: s.visualization.timelapse(video_type="normalized"), expect_error=ValueError)

    pv = fresh()
    pv.preprocessing.grayscale(show_progress=False)
    pv.preprocessing.binarization.otsu(show_progress=False)
    pv.preprocessing.normalization.clahe(show_progress=False)
    pv.detection.yolo(show_progress=False, verbose=False)
    pv.tracking.sort(show_progress=False, verbose=False)
    run("visualization.plot_frame(['original','grayscale','binarized','normalized'])",
        lambda: (pv.visualization.plot_frame(["original", "grayscale", "binarized", "normalized"], frame_index=5), "png saved")[1])
    run("visualization.plot_frame('grayscale+binarized')",
        lambda: (pv.visualization.plot_frame("grayscale+binarized"), "png saved")[1])
    run("visualization.timelapse(tracks+ids+custom colours+max_track_gap)",
        lambda: (pv.visualization.timelapse(video_type="grayscale+binarized", show_tracks=True, show_track_ids=True,
                                            detection_color="blue", groundtruth_color="red",
                                            track_colors={"groundtruth": "yellow", "detection": "orange"},
                                            max_track_gap=5), "png saved")[1])
    run("visualization.interactive_motility_calculator()",
        lambda: (pv.visualization.interactive_motility_calculator(), "png saved")[1])
    run("visualization.interactive_motility_calculator(frame_rate=60, smoothing_window=3)",
        lambda: (pv.visualization.interactive_motility_calculator(frame_rate=60, smoothing_window=3), "png saved")[1])
    del pv
    gc.collect()

    mc = fresh()
    mc.detection.detect_moving_cells(show_progress=False, verbose=False)
    run("visualization.plot_frame('moving_cells')", lambda: (mc.visualization.plot_frame("moving_cells"), "png saved")[1])
    run("visualization.timelapse('moving_cells')", lambda: (mc.visualization.timelapse(video_type="moving_cells"), "png saved")[1])
    del mc
    gc.collect()

    run("visualization.motility_radar() with NO motility -> expects error",
        lambda: s.visualization.motility_radar(), expect_error=Exception)
    run("visualization.motility_density_scatter() with NO motility -> expects error",
        lambda: s.visualization.motility_density_scatter(), expect_error=Exception)
    run("visualization.interactive_motility_calculator() with NO tracking -> expects error",
        lambda: s.visualization.interactive_motility_calculator(), expect_error=Exception)
    del s
    gc.collect()

    m = fresh()
    m.tracking.sort(show_progress=False, verbose=False)
    m.motility.kinematic_parameters(show_progress=False, verbose=False)
    m.motility.casa_parameters(verbose=False)
    run("visualization.motility_radar()", lambda: (m.visualization.motility_radar(), "png saved")[1])
    run("visualization.motility_radar(show_legend=False, show_text=False)",
        lambda: (m.visualization.motility_radar(show_legend=False, show_text=False), "png saved")[1])
    run("visualization.motility_radar(axis=<supplied polar axis>)",
        lambda: (m.visualization.motility_radar(axis=plt.figure().add_subplot(111, polar=True)), _fake_show(), "png saved")[2])
    run("visualization.motility_density_scatter()", lambda: (m.visualization.motility_density_scatter(), "png saved")[1])
    run("meta['last_visualization'] was it written", lambda: str(m.get_meta().get("last_visualization"))[:200])


SECTIONS = {
    "io": sec_io,
    "casa": sec_casa,
    "preprocessing": sec_preprocessing,
    "detection_yolo26": sec_detection_yolo26,
    "detection_classic": sec_detection_classic,
    "detection_yolov5": sec_detection_yolov5,      # last: it pollutes global state
    "tracking": sec_tracking,
    "motility": sec_motility,
    "visualization": sec_visualization,
}


def _driver():
    """Run each section in a separate process and merge the results."""
    import subprocess
    if os.path.exists(RESULT_JSON):
        os.remove(RESULT_JSON)
    all_results = []
    for name in SECTIONS:
        print(f"\n{'='*30} SECTION: {name} {'='*30}", flush=True)
        env = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
        p = subprocess.run([sys.executable, __file__, name], env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        sys.stdout.write(p.stdout or "")
        part = f"outputs/_step7_part_{name}.json"
        if os.path.exists(part):
            all_results += json.load(open(part, encoding="utf-8"))
            os.remove(part)
        else:
            all_results.append({"section": name, "name": f"SECTION {name} crashed", "status": "FAIL", "sec": 0,
                                "note": (p.stderr or "")[-400:]})
    json.dump(all_results, open(RESULT_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    n_pass = sum(r["status"] == "PASS" for r in all_results)
    n_fail = len(all_results) - n_pass
    lines = [f"# pycasa full API test: {n_pass} PASS / {n_fail} FAIL / {len(all_results)} tests\n",
             "Each section was run in its own Python process, on the first 21 frames of the HC004 default dataset.",
             "For tests marked `-> expects error`, PASS means the function correctly raised an error.\n"]
    for sec in SECTIONS:
        rows = [r for r in all_results if r["section"] == sec]
        if not rows:
            continue
        sp = sum(r["status"] == "PASS" for r in rows)
        lines += [f"\n## {sec} ({sp}/{len(rows)})\n", "| Test | Result | Time (s) | Note |", "|---|---|---|---|"]
        for r in rows:
            lines.append(f"| `{r['name']}` | {'PASS' if r['status']=='PASS' else '**FAIL**'} | {r['sec']} | {r['note'].replace('|','/')[:200]} |")
    open("outputs/step7_api_test_report.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"\n===== {n_pass} PASS / {n_fail} FAIL / {len(all_results)} tests =====")
    for r in all_results:
        if r["status"] == "FAIL":
            print("FAIL:", r["section"], "|", r["name"], "->", r["note"][:200])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        SECTION = sys.argv[1]
        if SECTION in ("motility", "visualization"):
            FRAMES = 60          # the kinematic calculation wants 30 points per track
        SECTIONS[SECTION]()
        json.dump(RESULTS, open(f"outputs/_step7_part_{SECTION}.json", "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
    else:
        SECTION = "driver"
        _driver()
