"""Step 9f: bisect the inside of utils/general.py.

Step 9e found utils.general guilty. That module carries two kinds of side effect:
  (1) top-level third-party imports (ultralytics submodules, torchvision...)
  (2) a module-level settings block (lines 79-87: printoptions, cv2 threads, env)

We run each candidate ALONE in its own process and look at the YOLO26 result.
6003 -> guilty, 6390 -> innocent.

    python scripts/step9f_bisect_general.py
"""
import os, sys, json, subprocess

OUT = "outputs/step9f_bisect_general.json"
FRAMES = 40

# name -> (does it need the yolov5 directory?, code to run)
CANDIDATES = {
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
    # the settings block from lines 79-87, no imports, applied together
    "settings_block":      (False, "\n".join([
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


def run_condition(name):
    needs_yolov5, code = CANDIDATES[name]
    import pycasa as pc
    if code:
        if needs_yolov5:
            from pycasa.detection._yolo import _temporary_sys_path, _ensure_yolov5_pkg
            with _temporary_sys_path(str(_ensure_yolov5_pkg())):
                exec(code, {})
        else:
            exec(code, {})
    s = pc.io.load_default_data(final_frame=FRAMES, verbose=False)
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    n = sum(len(v) for v in s.get_detections().values())
    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[name] = {"detections": n, "fp": a["fp"], "F1": a["F1"]}
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_condition(sys.argv[1]); sys.exit()
    if os.path.exists(OUT):
        os.remove(OUT)
    for name in CANDIDATES:
        p = subprocess.run([sys.executable, __file__, name],
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode != 0:
            print(f"  {name}: ERROR {(p.stderr or '')[-200:].strip()}", flush=True)
    d = json.load(open(OUT, encoding="utf-8"))
    isolated = d.get("none", {}).get("detections")
    contaminated = d.get("general_full", {}).get("detections")
    print(f"\n{'candidate':16s} {'code':44s} {'det':>6s} {'FP':>6s}  verdict")
    print("-" * 85)
    for name, (_, code) in CANDIDATES.items():
        r = d.get(name)
        if not r:
            print(f"{name:16s} {'-':44s} {'ERROR':>6s}"); continue
        first_line = (code or "-").split("\n")[0][:44]
        if name in ("none", "general_full"): verdict = "reference"
        elif r["detections"] == contaminated:     verdict = "GUILTY"
        elif r["detections"] == isolated:     verdict = "innocent"
        else:                              verdict = "partial"
        print(f"{name:16s} {first_line:44s} {r['detections']:>6d} {r['fp']:>6d}  {verdict}")
    print(f"\nisolated={isolated}  contaminated={contaminated}")
