"""Adim 7: pycasa'nin TUM public fonksiyonlarini HC004 verisiyle tek tek calistir.

Kullanim:
    python scripts/step7_full_api_test.py            # tum bolumleri ayri process'lerde calistirir
    python scripts/step7_full_api_test.py io         # tek bolum

Neden bolum bolum: her Casa session'i videoyu RAM'de tutuyor (21 frame ~82 MiB) ve
`copy()` tam deepcopy yapiyor. Hepsini tek process'te calistirinca MemoryError aliniyor.
Ayrica YOLOv5 import'u ayni process'te YOLO26 sonucunu degistiriyor; bolum izolasyonu bunu da cozuyor.

Sonuclar: outputs/step7_api_test_results.json + outputs/step7_api_test_report.md
Gorseller pencere yerine outputs/step7_figs/*.png olarak kaydedilir.
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
plt.switch_backend = lambda *a, **k: None          # Agg'de kal, Tk penceresi acma

import pycasa as pc

RESULTS = []
FRAMES = 20                                         # final_frame -> 21 frame (~82 MiB/session)
# Veri ve agirliklar proje klasorunun icinde (bkz. setup_env.bat)
PROJ_ROOT = os.environ.get("PYCASA_PROJECT_ROOT") or os.path.abspath(".")
PROJ_DATA = os.environ.get("PYCASA_DATA") or os.path.join(PROJ_ROOT, "pycasa_data")
DATA = os.path.join(PROJ_DATA, "sys-casa/rawdata/sub-HC004/ses-01")
VIDEO = f"{DATA}/sys-casa_sub-HC004_ses-01_run-005_video.avi"
GT_DIR = f"{DATA}/sys-casa_sub-HC004_ses-01_run-005_gt"
W_Y26 = os.path.join(PROJ_ROOT, "yolo26-weights/sys-casa_yolo26s.pt")


def run(name, fn, expect_error=None):
    """Bir API cagrisini calistir, PASS/FAIL kaydet."""
    CURRENT[0] = "".join(c if c.isalnum() else "_" for c in name)[:50]
    t0 = time.time()
    print(f"\n>>> {name}", flush=True)
    try:
        out = fn()
        dt = round(time.time() - t0, 1)
        if expect_error:
            RESULTS.append({"section": SECTION, "name": name, "status": "FAIL", "sec": dt,
                            "note": f"beklenen {expect_error.__name__} gelmedi, sonuc: {str(out)[:150]}"})
            print(f"    FAIL (beklenen {expect_error.__name__} gelmedi)", flush=True)
        else:
            RESULTS.append({"section": SECTION, "name": name, "status": "PASS", "sec": dt,
                            "note": out if isinstance(out, str) else ""})
            print(f"    PASS {dt}s {out if isinstance(out, str) else ''}", flush=True)
    except Exception as e:
        dt = round(time.time() - t0, 1)
        if expect_error and isinstance(e, expect_error):
            RESULTS.append({"section": SECTION, "name": name, "status": "PASS", "sec": dt,
                            "note": f"beklenen hata: {type(e).__name__}: {str(e)[:150]}"})
            print(f"    PASS (beklenen hata) {type(e).__name__}: {str(e)[:150]}", flush=True)
        else:
            RESULTS.append({"section": SECTION, "name": name, "status": "FAIL", "sec": dt,
                            "note": f"{type(e).__name__}: {str(e)[:300]}"})
            print(f"    FAIL {type(e).__name__}: {str(e)[:300]}", flush=True)
            traceback.print_exc(limit=2)
    finally:
        gc.collect()


def fresh(**kw):
    """Yeni bir session; copy() yerine bunu kullan (deepcopy 191 MiB yiyor)."""
    kw.setdefault("final_frame", FRAMES)
    kw.setdefault("verbose", False)
    return pc.io.load_default_data(**kw)


# =========================================================== BOLUM: io
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
    run("io.load_default_data(download=False) cache'den",
        lambda: f"frames={fresh(download=False).get_video()['number_frame_used']}")
    run("session.io.load_default_data() wrapper",
        lambda: f"um_per_px={pc.Casa().io.load_default_data(final_frame=5, verbose=False).get_meta()['um_per_px']}")
    run("session.io.load_default_data(volume_ml=...) wrapper/module imza paritesi",
        lambda: pc.Casa().io.load_default_data(final_frame=5, volume_ml=2.2, verbose=False))
    run("io.load_video(video, groundtruth_detections_path)",
        lambda: (lambda s: f"frames={s.get_video()['number_frame_used']} gt_frames={len(s.get_groundtruth())} "
                           f"fps={s.get_meta()['sampling_rate']}")(
            pc.io.load_video(VIDEO, groundtruth_detections_path=GT_DIR, final_frame=20,
                             um_per_px=0.24, volume_ml=2.2, chamber_depth_um=20.7,
                             verbose=False, show_progress=False)))
    run("io.load_video(video) GT'siz, sampling_rate=25",
        lambda: f"fps={pc.io.load_video(VIDEO, final_frame=10, sampling_rate=25, verbose=False, show_progress=False).get_meta()['sampling_rate']}")
    run("io.load_video(groundtruth_tracks_path=GT_DIR) (GT'de track id yok)",
        lambda: f"gt_tracks={len(pc.io.load_video(VIDEO, groundtruth_tracks_path=GT_DIR, final_frame=10, verbose=False, show_progress=False).get_groundtruth_tracks())}")
    run("io.load_video(dilution_factor=2)",
        lambda: f"dilution={pc.io.load_video(VIDEO, final_frame=5, dilution_factor=2, verbose=False, show_progress=False).get_meta().get('dilution_factor')}")
    run("io.load_video(olmayan dosya) -> hata beklenir",
        lambda: pc.io.load_video("C:/nope/x.avi", verbose=False), expect_error=Exception)
    run("session.io.load_video() wrapper",
        lambda: f"frames={pc.Casa().io.load_video(VIDEO, final_frame=5, verbose=False, show_progress=False).get_video()['number_frame_used']}")


# =========================================================== BOLUM: casa (getter/setter)
def sec_casa():
    s = fresh()
    run("Casa.info()", lambda: (s.info(), "ekrana basildi")[1])
    run("Casa.copy() bagimsiz kopya mi",
        lambda: (lambda c: f"yeni nesne={c is not s}, meta ayni={c.get_meta() == s.get_meta()}")(s.copy()))
    run("set_um_per_px(0.3)", lambda: str(fresh().set_um_per_px(0.3).get_meta()["um_per_px"]))
    run("set_volume_ml(1.5)", lambda: str(fresh().set_volume_ml(1.5).get_meta()["volume_ml"]))
    run("set_chamber_depth_um(10)", lambda: str(fresh().set_chamber_depth_um(10).get_meta()["chamber_depth_um"]))
    run("set_dilution_factor(2)", lambda: str(fresh().set_dilution_factor(2).get_meta().get("dilution_factor")))
    run("set_um_per_px(-1) -> ValueError beklenir", lambda: s.set_um_per_px(-1), expect_error=ValueError)
    run("set_volume_ml('abc') -> TypeError beklenir", lambda: s.set_volume_ml("abc"), expect_error=Exception)
    run("set_chamber_depth_um(0) -> hata beklenir", lambda: s.set_chamber_depth_um(0), expect_error=Exception)
    run("set_dilution_factor(-5) -> hata beklenir", lambda: s.set_dilution_factor(-5), expect_error=Exception)
    run("get_casa() keys", lambda: str(list(s.get_casa().keys())))
    run("get_meta() keys", lambda: str(sorted(s.get_meta().keys())))
    run("get_video() keys", lambda: str(list(s.get_video().keys())))
    run("get_groundtruth() frame sayisi", lambda: str(len(s.get_groundtruth())))
    run("get_groundtruth_tracks() (bos olmali)", lambda: str(s.get_groundtruth_tracks()))
    run("get_detections() (bos)", lambda: str(s.get_detections()))
    run("get_detections(include_groundtruth=True)", lambda: str(list(s.get_detections(include_groundtruth=True).keys())))
    run("get_tracks() (bos)", lambda: str(s.get_tracks()))
    run("get_tracks(backend='sort') tracking yokken", lambda: str(s.get_tracks(backend="sort")))
    run("get_motility() (bos)", lambda: str(s.get_motility()))
    run("get_assessment() (bos)", lambda: str(s.get_assessment()))
    run("get_assesment() (yazim hatali alias)", lambda: str(s.get_assesment()))
    run("get_assessment() canli referans mi (mutasyon testi)",
        lambda: (lambda a: (a.update({"_probe": 1}), f"session'a sizdi={'_probe' in s.get_assessment()}")[1])(s.get_assessment()))


# =========================================================== BOLUM: preprocessing
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
    run("binarization.otsu() grayscale yapilmadan (ham renkli video)",
        lambda: (lambda c: (c.preprocessing.binarization.otsu(show_progress=False), vkeys(c))[1])(fresh()))
    run("binarization.adaptive_gaussian(block_size=4 cift) -> hata beklenir",
        lambda: p.preprocessing.binarization.adaptive_gaussian(block_size=4, show_progress=False),
        expect_error=Exception)
    run("binarization.niblack(window_size=0) -> hata beklenir",
        lambda: p.preprocessing.binarization.niblack(window_size=0, show_progress=False), expect_error=Exception)
    for meth, kw in [("clahe", {"clip_limit": 3.0, "tile_grid_size": (4, 4)}), ("hist_equal", {}),
                     ("log", {}), ("median", {}), ("min_max", {}), ("z_score", {})]:
        run(f"preprocessing.normalization.{meth}()",
            (lambda m=meth, k=kw: (getattr(p.preprocessing.normalization, m)(show_progress=False, **k),
                                   f"{vkeys(p)} dtype={np.asarray(p.get_video()['normalized_video']).dtype}")[1]))
    run("normalization.min_max(overwrite=True)",
        lambda: (lambda c: (c.preprocessing.normalization.min_max(overwrite=True, show_progress=False), vkeys(c))[1])(fresh()))
    run("zincir: grayscale -> clahe -> otsu",
        lambda: (lambda c: (c.preprocessing.grayscale(show_progress=False),
                            c.preprocessing.normalization.clahe(show_progress=False),
                            c.preprocessing.binarization.otsu(show_progress=False), vkeys(c))[3])(fresh()))


# =========================================================== BOLUM: detection
def _det_eval(sess):
    sess.assessment.evaluate_detections()
    a = sess.get_assessment()["detection"]
    return f"tp={a['tp']} fp={a['fp']} fn={a['fn']} P={a['precision']} R={a['recall']} F1={a['F1']} frames={a['evaluated_frames']}"

def sec_detection_yolo26():
    run("detection.yolo() varsayilan (yolo26) + evaluate_detections",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.yolo(weights=<ASCII tam yol>) ozel agirlik",
        lambda: (lambda c: (c.detection.yolo(weights=W_Y26, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.yolo(conf=0.5) yuksek esik",
        lambda: (lambda c: (c.detection.yolo(conf=0.5, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.yolo(conf=0.01) dusuk esik",
        lambda: (lambda c: (c.detection.yolo(conf=0.01, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.yolo(yolo_model='yolo99') -> hata beklenir",
        lambda: fresh().detection.yolo(yolo_model="yolo99", show_progress=False), expect_error=Exception)
    run("detection.yolo(weights='C:/nope.pt') -> hata beklenir",
        lambda: fresh().detection.yolo(weights="C:/nope.pt", show_progress=False), expect_error=Exception)
    run("detection.yolo(download=False) managed agirlik cache'de",
        lambda: (lambda c: (c.detection.yolo(download=False, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("get_detections() satir formati (yolo26, frame 0)",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            str(np.asarray(c.get_detections()["0"])[:2].tolist()))[1])(fresh()))

def sec_detection_yolov5():
    run("detection.yolo(yolo_model='yolov5') + evaluate_detections",
        lambda: (lambda c: (c.detection.yolo(yolo_model="yolov5", show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.yolo(yolov5, conf=0.4)",
        lambda: (lambda c: (c.detection.yolo(yolo_model="yolov5", conf=0.4, show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("YOLOv5'ten SONRA yolo26 (sira bagimliligi testi)",
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
    run("detection.detect_moving_cells(method='xyz') -> hata beklenir",
        lambda: fresh().detection.detect_moving_cells(method="xyz", show_progress=False), expect_error=Exception)
    run("detection.digital_washing() n_jobs=1",
        lambda: (lambda c: (c.detection.digital_washing(show_progress=False, verbose=False), _det_eval(c))[1])(fresh()))
    run("detection.digital_washing(n_jobs=4) paralel",
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
    run("assessment.evaluate_detections() detection YOKKEN -> hata beklenir",
        lambda: fresh().assessment.evaluate_detections(), expect_error=Exception)
    run("detection overwrite uyarisi (urbano -> moving_cells)",
        lambda: (lambda c: (c.detection.urbano_detection(show_progress=False, verbose=False),
                            c.detection.detect_moving_cells(show_progress=False, verbose=False),
                            f"detection frame sayisi={len(c.get_detections())}")[2])(fresh()))


# =========================================================== BOLUM: tracking
def _trk_info(c):
    tr = c.get_tracks()
    if not tr:
        return "tracks bos"
    b = list(tr.keys())[0]
    return f"backend={b} " + " | ".join(f"{src}:{len(tr[b][src])} track" for src in tr[b])

def sec_tracking():
    run("tracking.sort() sadece GT",
        lambda: (lambda c: (c.tracking.sort(show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.sort(max_age=5, min_hits=1, iou_threshold=0.3)",
        lambda: (lambda c: (c.tracking.sort(max_age=5, min_hits=1, iou_threshold=0.3, show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.sort(initial_frame=10)",
        lambda: (lambda c: (c.tracking.sort(initial_frame=10, show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.sort(delete_temp=False)",
        lambda: (lambda c: (c.tracking.sort(delete_temp=False, show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.sort() GT + yolo26 (iki kaynak)",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            c.tracking.sort(show_progress=False, verbose=False), _trk_info(c))[2])(fresh()))
    run("tracking.sort(skip_gt=True) sadece yolo26",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            c.tracking.sort(skip_gt=True, show_progress=False, verbose=False), _trk_info(c))[2])(fresh()))
    run("tracking.sort(skip_gt=True) detection YOKKEN",
        lambda: (lambda c: (c.tracking.sort(skip_gt=True, show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.jpdaf() sadece GT",
        lambda: (lambda c: (c.tracking.jpdaf(show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.jpdaf(frame_rate=60, p_delete=0.3, sigma_n_um=1)",
        lambda: (lambda c: (c.tracking.jpdaf(frame_rate=60, p_delete=0.3, sigma_n_um=1.0, show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.jpdaf(position_gate=5, velocity_gate_um=20, detection_probability=0.9)",
        lambda: (lambda c: (c.tracking.jpdaf(position_gate=5, velocity_gate_um=20, detection_probability=0.9,
                                             show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.jpdaf(skip_gt=True) yolo26",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            c.tracking.jpdaf(skip_gt=True, show_progress=False, verbose=False), _trk_info(c))[2])(fresh()))
    run("tracking.deepsort() sadece GT",
        lambda: (lambda c: (c.tracking.deepsort(show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking.deepsort(max_age=10, n_init=2, max_iou_distance=0.5)",
        lambda: (lambda c: (c.tracking.deepsort(max_age=10, n_init=2, max_iou_distance=0.5,
                                                show_progress=False, verbose=False), _trk_info(c))[1])(fresh()))
    run("tracking overwrite: sort -> jpdaf, get_tracks() tek backend",
        lambda: (lambda c: (c.tracking.sort(show_progress=False, verbose=False),
                            c.tracking.jpdaf(show_progress=False, verbose=False),
                            f"backends={list(c.get_tracks().keys())}")[2])(fresh()))
    run("get_tracks(backend='jpdaf') sort varken",
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
    run("assessment.evaluate_tracks() tek kaynakla (sadece GT)",
        lambda: (lambda c: (c.tracking.sort(show_progress=False, verbose=False),
                            c.assessment.evaluate_tracks(),
                            json.dumps(c.get_assessment().get("tracks", {}), default=str)[:300])[2])(fresh()))
    run("assessment.evaluate_tracks() tracking YOKKEN -> hata beklenir",
        lambda: fresh().assessment.evaluate_tracks(), expect_error=Exception)


# =========================================================== BOLUM: motility
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
    run("motility [sort/GT+yolo26 iki kaynak]",
        lambda: (lambda c: (c.detection.yolo(show_progress=False, verbose=False),
                            c.tracking.sort(show_progress=False, verbose=False), _mot(c))[2])(fresh()))
    run("kinematic_parameters(window_size=15, overlap=0.5, smoothing_window=3, denoise_window=1, min_frame_rate_warn=0)",
        lambda: _mot(_sorted_gt(), kin=dict(window_size=15, overlap=0.5, smoothing_window=3,
                                            denoise_window=1, min_frame_rate_warn=0)))
    run("kinematic_parameters(frame_rate=60)", lambda: _mot(_sorted_gt(), kin=dict(frame_rate=60)))
    run("kinematic_parameters(conversion_required=False) piksel birimi",
        lambda: _mot(_sorted_gt(), kin=dict(conversion_required=False)))
    run("kinematic_parameters(overlap=1.5) gecersiz -> hata beklenir",
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
    run("casa_parameters(hyperactivation esikleri, experimental)",
        lambda: _mot(_sorted_gt(), casa=dict(experimental_parameters=True, hyperactivation_vcl_threshold=30,
                                             hyperactivation_alh_threshold=1.0, hyperactivation_lin_threshold=0.5)))
    run("casa_parameters(velocity_metric='XYZ') -> hata beklenir",
        lambda: _mot(_sorted_gt(), casa=dict(velocity_metric="XYZ")), expect_error=Exception)
    run("casa_parameters() kinematic YOKKEN -> hata beklenir",
        lambda: _sorted_gt().motility.casa_parameters(verbose=False), expect_error=Exception)
    run("kinematic_parameters() tracking YOKKEN -> hata beklenir",
        lambda: fresh().motility.kinematic_parameters(show_progress=False, verbose=False), expect_error=Exception)
    run("kinematic_parameters() um_per_px=None iken",
        lambda: (lambda c: (c.tracking.sort(show_progress=False, verbose=False),
                            c.motility.kinematic_parameters(show_progress=False, verbose=False),
                            f"kinematic bos mu={not c.get_motility().get('kinematic_parameters')}")[2])(
            pc.io.load_video(VIDEO, groundtruth_detections_path=GT_DIR, final_frame=20, verbose=False, show_progress=False)))
    run("get_motility() track basina kinematik anahtarlar",
        lambda: (lambda c: (_mot(c), str(list(next(iter(c.get_motility()["kinematic_parameters"]["groundtruth"].values())).keys())))[1])(_sorted_gt()))


# =========================================================== BOLUM: visualization
def sec_visualization():
    s = fresh()
    run("visualization.plot_frame('original')", lambda: (s.visualization.plot_frame("original"), "png kaydedildi")[1])
    run("visualization.plot_frame(frame_index=5, show_detections=False)",
        lambda: (s.visualization.plot_frame("original", frame_index=5, show_detections=False), "png kaydedildi")[1])
    run("visualization.plot_frame('binarized') binarization YOKKEN -> hata beklenir",
        lambda: s.visualization.plot_frame("binarized"), expect_error=ValueError)
    run("visualization.plot_frame(frame_index=999) -> hata beklenir",
        lambda: s.visualization.plot_frame(frame_index=999), expect_error=ValueError)
    run("visualization.timelapse() varsayilan (GT overlay)",
        lambda: (s.visualization.timelapse(), "png kaydedildi")[1])
    run("visualization.timelapse(image_type='original') eski alias",
        lambda: (s.visualization.timelapse(image_type="original"), "png kaydedildi")[1])
    run("visualization.timelapse('normalized') katman YOKKEN -> hata beklenir",
        lambda: s.visualization.timelapse(video_type="normalized"), expect_error=ValueError)

    pv = fresh()
    pv.preprocessing.grayscale(show_progress=False)
    pv.preprocessing.binarization.otsu(show_progress=False)
    pv.preprocessing.normalization.clahe(show_progress=False)
    pv.detection.yolo(show_progress=False, verbose=False)
    pv.tracking.sort(show_progress=False, verbose=False)
    run("visualization.plot_frame(['original','grayscale','binarized','normalized'])",
        lambda: (pv.visualization.plot_frame(["original", "grayscale", "binarized", "normalized"], frame_index=5), "png kaydedildi")[1])
    run("visualization.plot_frame('grayscale+binarized')",
        lambda: (pv.visualization.plot_frame("grayscale+binarized"), "png kaydedildi")[1])
    run("visualization.timelapse(tracks+ids+ozel renkler+max_track_gap)",
        lambda: (pv.visualization.timelapse(video_type="grayscale+binarized", show_tracks=True, show_track_ids=True,
                                            detection_color="blue", groundtruth_color="red",
                                            track_colors={"groundtruth": "yellow", "detection": "orange"},
                                            max_track_gap=5), "png kaydedildi")[1])
    run("visualization.interactive_motility_calculator()",
        lambda: (pv.visualization.interactive_motility_calculator(), "png kaydedildi")[1])
    run("visualization.interactive_motility_calculator(frame_rate=60, smoothing_window=3)",
        lambda: (pv.visualization.interactive_motility_calculator(frame_rate=60, smoothing_window=3), "png kaydedildi")[1])
    del pv
    gc.collect()

    mc = fresh()
    mc.detection.detect_moving_cells(show_progress=False, verbose=False)
    run("visualization.plot_frame('moving_cells')", lambda: (mc.visualization.plot_frame("moving_cells"), "png kaydedildi")[1])
    run("visualization.timelapse('moving_cells')", lambda: (mc.visualization.timelapse(video_type="moving_cells"), "png kaydedildi")[1])
    del mc
    gc.collect()

    run("visualization.motility_radar() motility YOKKEN -> hata beklenir",
        lambda: s.visualization.motility_radar(), expect_error=Exception)
    run("visualization.motility_density_scatter() motility YOKKEN -> hata beklenir",
        lambda: s.visualization.motility_density_scatter(), expect_error=Exception)
    run("visualization.interactive_motility_calculator() tracking YOKKEN -> hata beklenir",
        lambda: s.visualization.interactive_motility_calculator(), expect_error=Exception)
    del s
    gc.collect()

    m = fresh()
    m.tracking.sort(show_progress=False, verbose=False)
    m.motility.kinematic_parameters(show_progress=False, verbose=False)
    m.motility.casa_parameters(verbose=False)
    run("visualization.motility_radar()", lambda: (m.visualization.motility_radar(), "png kaydedildi")[1])
    run("visualization.motility_radar(show_legend=False, show_text=False)",
        lambda: (m.visualization.motility_radar(show_legend=False, show_text=False), "png kaydedildi")[1])
    run("visualization.motility_radar(axis=<verilen polar eksen>)",
        lambda: (m.visualization.motility_radar(axis=plt.figure().add_subplot(111, polar=True)), _fake_show(), "png kaydedildi")[2])
    run("visualization.motility_density_scatter()", lambda: (m.visualization.motility_density_scatter(), "png kaydedildi")[1])
    run("meta['last_visualization'] yazildi mi", lambda: str(m.get_meta().get("last_visualization"))[:200])


SECTIONS = {
    "io": sec_io,
    "casa": sec_casa,
    "preprocessing": sec_preprocessing,
    "detection_yolo26": sec_detection_yolo26,
    "detection_classic": sec_detection_classic,
    "detection_yolov5": sec_detection_yolov5,      # en sona: global durumu kirletiyor
    "tracking": sec_tracking,
    "motility": sec_motility,
    "visualization": sec_visualization,
}


def _driver():
    """Her bolumu ayri process'te calistir, sonuclari birlestir."""
    import subprocess
    if os.path.exists(RESULT_JSON):
        os.remove(RESULT_JSON)
    all_results = []
    for name in SECTIONS:
        print(f"\n{'='*30} BOLUM: {name} {'='*30}", flush=True)
        env = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
        p = subprocess.run([sys.executable, __file__, name], env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        sys.stdout.write(p.stdout or "")
        part = f"outputs/_step7_part_{name}.json"
        if os.path.exists(part):
            all_results += json.load(open(part, encoding="utf-8"))
            os.remove(part)
        else:
            all_results.append({"section": name, "name": f"BOLUM {name} cokti", "status": "FAIL", "sec": 0,
                                "note": (p.stderr or "")[-400:]})
    json.dump(all_results, open(RESULT_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    n_pass = sum(r["status"] == "PASS" for r in all_results)
    n_fail = len(all_results) - n_pass
    lines = [f"# pycasa tam API testi: {n_pass} PASS / {n_fail} FAIL / {len(all_results)} test\n",
             "Her bolum ayri Python process'inde, HC004 default datasinin ilk 21 frame'i ile calistirildi.",
             "`-> hata beklenir` yazan testlerde PASS, fonksiyonun dogru sekilde hata vermesi demektir.\n"]
    for sec in SECTIONS:
        rows = [r for r in all_results if r["section"] == sec]
        if not rows:
            continue
        sp = sum(r["status"] == "PASS" for r in rows)
        lines += [f"\n## {sec} ({sp}/{len(rows)})\n", "| Test | Sonuc | Sure (s) | Not |", "|---|---|---|---|"]
        for r in rows:
            lines.append(f"| `{r['name']}` | {'PASS' if r['status']=='PASS' else '**FAIL**'} | {r['sec']} | {r['note'].replace('|','/')[:200]} |")
    open("outputs/step7_api_test_report.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"\n===== {n_pass} PASS / {n_fail} FAIL / {len(all_results)} test =====")
    for r in all_results:
        if r["status"] == "FAIL":
            print("FAIL:", r["section"], "|", r["name"], "->", r["note"][:200])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        SECTION = sys.argv[1]
        if SECTION in ("motility", "visualization"):
            FRAMES = 60          # kinematik hesap track basina 30 nokta istiyor
        SECTIONS[SECTION]()
        json.dump(RESULTS, open(f"outputs/_step7_part_{SECTION}.json", "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
    else:
        SECTION = "driver"
        _driver()
