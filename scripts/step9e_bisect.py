"""Step 9e: bisect the yolov5 import chain to find the guilty module.

models/common.py imports the modules below. We import each one ALONE, in its
own process, and then run YOLO26. A module that pulls the result down to 6003
(contaminated) is guilty; one that leaves it at 6390 (isolated) is innocent.

Usage (from the project folder, after setup_env):
    python scripts/step9e_bisect.py            # all candidates
    python scripts/step9e_bisect.py general    # a single candidate

Paste the output as-is; the table stands on its own.
"""
import os, sys, json, subprocess

OUT = "outputs/step9e_bisect.json"
FRAMES = 40

# name -> import statement (runs with the yolov5 directory added to sys.path)
CANDIDATES = {
    "none":         None,                                              # reference A
    "plotting":     "from ultralytics.utils.plotting import Annotator",  # line 38
    "utils_init":   "import utils",                                    # utils/__init__.py
    "dataloaders":  "from utils.dataloaders import letterbox",         # line 41
    "general":      "import utils.general",                            # line 42
    "torch_utils":  "from utils.torch_utils import smart_inference_mode",  # line 59
    "common_full":  "from models.common import AutoShape",             # reference C
}


def run_condition(name):
    statement = CANDIDATES[name]
    import pycasa as pc
    if statement:
        from pycasa.detection._yolo import _temporary_sys_path, _ensure_yolov5_pkg
        with _temporary_sys_path(str(_ensure_yolov5_pkg())):
            exec(statement, {})
    s = pc.io.load_default_data(final_frame=FRAMES, verbose=False)
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    n = sum(len(v) for v in s.get_detections().values())
    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[name] = {"detections": n, "tp": a["tp"], "fp": a["fp"], "F1": a["F1"]}
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2)
    print(f"  {name}: detections={n} tp={a['tp']} fp={a['fp']} F1={a['F1']}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_condition(sys.argv[1])
        sys.exit()
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
    contaminated = d.get("common_full", {}).get("detections")
    print(f"\n{'candidate':13s} {'import':48s} {'det':>6s} {'FP':>6s} {'F1':>7s}  verdict")
    print("-" * 95)
    for name, statement in CANDIDATES.items():
        r = d.get(name)
        if not r:
            print(f"{name:13s} {(statement or '-')[:48]:48s} {'ERROR':>6s}"); continue
        if name in ("none", "common_full"):
            verdict = "reference"
        elif r["detections"] == contaminated:
            verdict = "GUILTY  <-- reproduces the difference alone"
        elif r["detections"] == isolated:
            verdict = "innocent"
        else:
            verdict = "partial (neither isolated nor contaminated)"
        print(f"{name:13s} {(statement or '-')[:48]:48s} {r['detections']:>6d} {r['fp']:>6d} {r['F1']:>7.2f}  {verdict}")
    print(f"\nisolated={isolated}  contaminated={contaminated}")
