"""Step 9b: is the YOLO26 difference caused by module shadowing?

Observation: the yolov5 repo's packages have GENERIC names -- `models` and
`utils`. Importing them registers those names in sys.modules. Ultralytics also
uses names like `utils` internally, so it may pick up yolov5's module instead of
its own. If that is the cause, clearing sys.modules after the import should
restore the isolated value.

Conditions (each in its own process):
  A  no import                          -> reference "isolated" value
  C  import, no cleanup                 -> reference "contaminated" value
  E  import, sys.modules cleared        -> if it returns to A, shadowing is the cause

    python scripts/step9b_module_shadow.py
"""
import os, sys, json, subprocess

OUT = "outputs/step9b_module_shadow.json"
FRAMES = 40


def run_condition(code):
    import pycasa as pc
    added = []

    if code in ("C", "E"):
        before_modules = set(sys.modules)
        from pycasa.detection._yolo import _temporary_sys_path, _ensure_yolov5_pkg
        with _temporary_sys_path(str(_ensure_yolov5_pkg())):
            from models.common import AutoShape, DetectMultiBackend   # noqa: F401
        added = sorted(set(sys.modules) - before_modules)

    removed = []
    if code == "E":
        # drop yolov5's generically named packages and their submodules from sys.modules
        for name in list(sys.modules):
            root = name.split(".")[0]
            if root in ("models", "utils"):
                del sys.modules[name]
                removed.append(name)

    s = pc.io.load_default_data(final_frame=FRAMES, verbose=False)
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    n = sum(len(v) for v in s.get_detections().values())

    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[code] = {"detections": n, "tp": a["tp"], "fp": a["fp"], "F1": a["F1"],
               "modules_added": len(added),
               "shadowing": [m for m in added if m.split(".")[0] in ("models", "utils")][:8],
               "modules_removed": len(removed)}
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"  {code}: detections={n} tp={a['tp']} fp={a['fp']} F1={a['F1']} "
          f"| added={len(added)} cleared={len(removed)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_condition(sys.argv[1])
    else:
        if os.path.exists(OUT):
            os.remove(OUT)
        for k in ("A", "C", "E"):
            print(f"\n=== {k} ===", flush=True)
            p = subprocess.run([sys.executable, __file__, k],
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            for line in (p.stdout or "").splitlines():
                if line.strip().startswith(k + ":"):
                    print(" ", line.strip())
            if p.returncode != 0:
                print("  !! error:", (p.stderr or "")[-250:])

        d = json.load(open(OUT, encoding="utf-8"))
        if all(k in d for k in "ACE"):
            A, C, E = (d[k]["detections"] for k in "ACE")
            print(f"\n  A (isolated)             : {A}")
            print(f"  C (import, no cleanup)   : {C}")
            print(f"  E (import, with cleanup) : {E}")
            print(f"  shadowing modules        : {d['C']['shadowing']}")
            print()
            if E == A and C != A:
                print("  CONCLUSION: cleanup closed the gap -> the cause is MODULE SHADOWING.")
                print("  Fix: remove 'models' and 'utils' from sys.modules after the yolov5 import.")
            elif E == C:
                print("  CONCLUSION: cleanup made no difference -> not shadowing, but some other persistent state.")
            else:
                print("  CONCLUSION: all three differ, the table is inconclusive.")
