"""Adim 9f: utils/general.py'nin icini ikiye bol.

9e'de suclu utils.general cikti. Bu modul iki tur yan etki tasiyor:
  (1) ust duzeydeki ucuncu parti import'lar (ultralytics alt modulleri, torchvision...)
  (2) modul seviyesindeki ayar blogu (satir 79-87: printoptions, cv2 thread, env)

Her adayi TEK BASINA ayri process'te calistirip YOLO26 sonucuna bakiyoruz.
6003 -> suclu, 6390 -> masum.

    python scripts/step9f_bisect_general.py
"""
import os, sys, json, subprocess

OUT = "outputs/step9f_bisect_general.json"
FRAMES = 40

# ad -> (yolov5 dizini gerekli mi, calistirilacak kod)
ADAYLAR = {
    "none":            (False, None),
    "torchvision":     (False, "import torchvision"),
    "yaml_packaging":  (False, "import yaml, packaging"),
    "ul_data_conv":    (False, "import ultralytics.data.converter"),
    "ul_checks":       (False, "import ultralytics.utils.checks"),
    "ul_files":        (False, "import ultralytics.utils.files"),
    "ul_git":          (False, "import ultralytics.utils.git"),
    "ul_ops":          (False, "import ultralytics.utils.ops"),
    "ul_torch_utils":  (False, "import ultralytics.utils.torch_utils"),
    "ul_patches":      (False, "import ultralytics.utils.patches"),
    "y5_downloads":    (True,  "import utils.downloads"),
    "y5_metrics":      (True,  "import utils.metrics"),
    # satir 79-87 ayar blogu, import'suz, birlikte
    "ayar_blogu":      (False, "\n".join([
        "import os, platform, cv2, torch, numpy as np, pandas as pd",
        "NUM_THREADS = min(8, max(1, os.cpu_count() - 1))",
        "torch.set_printoptions(linewidth=320, precision=5, profile='long')",
        "np.set_printoptions(linewidth=320, formatter={'float_kind': '{:11.5g}'.format})",
        "pd.options.display.max_columns = 10",
        "cv2.setNumThreads(0)",
        "os.environ['NUMEXPR_MAX_THREADS'] = str(NUM_THREADS)",
        "os.environ['OMP_NUM_THREADS'] = str(NUM_THREADS)",
        "os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'",
        "os.environ['TORCH_CPP_LOG_LEVEL'] = 'ERROR'",
        "os.environ['KINETO_LOG_LEVEL'] = '5'",
    ])),
    "general_full":    (True,  "import utils.general"),
}


def calistir(ad):
    y5, kod = ADAYLAR[ad]
    import pycasa as pc
    if kod:
        if y5:
            from pycasa.detection._yolo import _temporary_sys_path, _ensure_yolov5_pkg
            with _temporary_sys_path(str(_ensure_yolov5_pkg())):
                exec(kod, {})
        else:
            exec(kod, {})
    s = pc.io.load_default_data(final_frame=FRAMES, verbose=False)
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    n = sum(len(v) for v in s.get_detections().values())
    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[ad] = {"detections": n, "fp": a["fp"], "F1": a["F1"]}
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        calistir(sys.argv[1]); sys.exit()
    if os.path.exists(OUT):
        os.remove(OUT)
    for ad in ADAYLAR:
        p = subprocess.run([sys.executable, __file__, ad],
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode != 0:
            print(f"  {ad}: HATA {(p.stderr or '')[-200:].strip()}", flush=True)
    d = json.load(open(OUT, encoding="utf-8"))
    izole = d.get("none", {}).get("detections")
    kirli = d.get("general_full", {}).get("detections")
    print(f"\n{'aday':16s} {'kod':44s} {'det':>6s} {'FP':>6s}  hukum")
    print("-" * 85)
    for ad, (_, kod) in ADAYLAR.items():
        r = d.get(ad)
        if not r:
            print(f"{ad:16s} {'-':44s} {'HATA':>6s}"); continue
        ilk = (kod or "-").split("\n")[0][:44]
        if ad in ("none", "general_full"): hukum = "referans"
        elif r["detections"] == kirli:     hukum = "SUCLU"
        elif r["detections"] == izole:     hukum = "masum"
        else:                              hukum = "kismi"
        print(f"{ad:16s} {ilk:44s} {r['detections']:>6d} {r['fp']:>6d}  {hukum}")
    print(f"\nizole={izole}  kirli={kirli}")
