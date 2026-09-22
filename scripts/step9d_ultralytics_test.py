"""Step 9d: is the cause the yolov5 repo, or the ultralytics import itself?

Finding: this yolov5 repo (Ultralytics' newer release) depends directly on
ultralytics -- models/common.py does `import ultralytics` and utils/__init__.py
does `from ultralytics.utils import ...`. The YOLO26 path already uses
ultralytics too, so the package is shared. What changes may be the ORDER.

Conditions (each in its own process, all run YOLO26):
  A  no preceding import                       -> isolated reference (6390)
  C  yolov5 repo imported                      -> contaminated reference (6003)
  G  only `import ultralytics`                 -> if equal to C, ultralytics is the cause
  H  only `ultralytics.utils.patches`          -> is the torch.load patch alone enough?

    python scripts/step9d_ultralytics_test.py
"""
import os, sys, json, subprocess

OUT = "outputs/step9d_ultralytics.json"


def run_condition(code):
    if code == "G":
        import ultralytics  # noqa: F401
    elif code == "H":
        from ultralytics.utils import patches  # noqa: F401

    import pycasa as pc
    if code == "C":
        from pycasa.detection._yolo import _temporary_sys_path, _ensure_yolov5_pkg
        with _temporary_sys_path(str(_ensure_yolov5_pkg())):
            from models.common import AutoShape  # noqa: F401

    import torch
    torch_load_is_patched = torch.load.__module__.startswith("ultralytics")

    s = pc.io.load_default_data(final_frame=40, verbose=False)
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    n = sum(len(v) for v in s.get_detections().values())

    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[code] = {"detections": n, "tp": a["tp"], "fp": a["fp"], "F1": a["F1"],
               "torch_load_patched": torch_load_is_patched}
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2)
    print(f"  {code}: detections={n} tp={a['tp']} fp={a['fp']} F1={a['F1']} "
          f"| torch.load patched={torch_load_is_patched}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_condition(sys.argv[1])
    else:
        if os.path.exists(OUT):
            os.remove(OUT)
        labels = {"A": "no preceding import", "C": "yolov5 repo",
                  "G": "ultralytics only", "H": "ultralytics.utils.patches only"}
        for k in ("A", "C", "G", "H"):
            print(f"\n=== {k}: {labels[k]} ===", flush=True)
            p = subprocess.run([sys.executable, __file__, k],
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            for line in (p.stdout or "").splitlines():
                if line.strip().startswith(k + ":"):
                    print(" ", line.strip())
            if p.returncode != 0:
                print("  !! error:", (p.stderr or "")[-250:])

        d = json.load(open(OUT, encoding="utf-8"))
        if all(k in d for k in "ACGH"):
            A, C, G, Hh = (d[k]["detections"] for k in "ACGH")
            print(f"\n  A no preceding import : {A}")
            print(f"  C yolov5 repo         : {C}")
            print(f"  G ultralytics only    : {G}")
            print(f"  H patches only        : {Hh}")
            print()
            if G == C and C != A:
                print("  CONCLUSION: `import ultralytics` alone reproduces the difference.")
                print("  So the cause is not the yolov5 repo but the ORDER in which ultralytics is imported.")
                if Hh == C:
                    print("  ultralytics.utils.patches alone is also enough (the torch.load patch).")
            elif G == A:
                print("  CONCLUSION: ultralytics alone is not enough; the difference comes from the yolov5 repo.")
            else:
                print("  CONCLUSION: the table is inconclusive.")
