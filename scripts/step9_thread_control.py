"""Step 9: controlled experiment for the YOLO26 ordering dependency.

Question: after importing YOLOv5, YOLO26 produces different results. Is the
cause the change in the OpenCV thread count, or some other global state that
the import leaves behind?

Wrong test: saying "cv2.getNumThreads() reads differently across the two runs".
That only shows the variable changed, not that the variable changed the RESULT.

Right test: treat the thread count as an independent variable in a 2x2 design.
  A  no import,  default threads
  B  no import,  threads forced to 1
  C  import,     threads at 1 (the state the import leaves behind)
  D  import,     threads restored to the default

Expectations:
  If threads are the cause -> A != B  and  D ~ A  (restoring threads closes the gap)
  If the import is the cause -> A ~ B  and  C ~ D  (the gap persists regardless of threads)

Each condition runs in a SEPARATE process; an import cannot be undone in place.

    python scripts/step9_thread_control.py           # run all four
    python scripts/step9_thread_control.py A         # a single condition
"""
import os, sys, json, subprocess

OUT = "outputs/step9_thread_control.json"
FRAMES = 40
CONDITIONS = {
    "A": ("no import", "default threads"),
    "B": ("no import", "threads forced to 1"),
    "C": ("import YES", "threads at 1 (post-import state)"),
    "D": ("import YES", "threads restored to default"),
}


def run_condition(code):
    import cv2
    import pycasa as pc

    default_cv2 = cv2.getNumThreads()
    imported = False

    if code in ("C", "D"):
        from pycasa.detection._yolo import _temporary_sys_path, _ensure_yolov5_pkg
        with _temporary_sys_path(str(_ensure_yolov5_pkg())):
            from models.common import AutoShape, DetectMultiBackend   # noqa: F401
        imported = True

    if code == "B":
        cv2.setNumThreads(1)
    elif code == "D":
        cv2.setNumThreads(default_cv2)      # restore the value the import lowered

    import torch
    measured = {
        "cv2_threads": cv2.getNumThreads(),
        "torch_threads": torch.get_num_threads(),
        "torch_interop": torch.get_num_interop_threads(),
        "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
        "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
        "tf32_matmul": bool(torch.backends.cuda.matmul.allow_tf32),
        "tf32_cudnn": bool(torch.backends.cudnn.allow_tf32),
        "float32_matmul_precision": torch.get_float32_matmul_precision(),
        "grad_enabled": torch.is_grad_enabled(),
    }

    s = pc.io.load_default_data(final_frame=FRAMES, verbose=False)
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    n = sum(len(v) for v in s.get_detections().values())

    result = {"condition": code, "description": CONDITIONS[code], "yolov5_import": imported,
              "cv2_default": default_cv2, "environment": measured,
              "detections": n, "tp": a["tp"], "fp": a["fp"], "fn": a["fn"],
              "precision": a["precision"], "recall": a["recall"], "F1": a["F1"]}

    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[code] = result
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"  {code}: detections={n} tp={a['tp']} fp={a['fp']} F1={a['F1']} "
          f"| cv2_threads={measured['cv2_threads']} torch_threads={measured['torch_threads']}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_condition(sys.argv[1])
    else:
        if os.path.exists(OUT):
            os.remove(OUT)
        for k, (imp, thr) in CONDITIONS.items():
            print(f"\n=== {k}: {imp}, {thr} ===", flush=True)
            p = subprocess.run([sys.executable, __file__, k],
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            for line in (p.stdout or "").splitlines():
                if line.strip().startswith(k + ":"):
                    print(" ", line.strip())
            if p.returncode != 0:
                print("  !! error:", (p.stderr or "")[-250:])

        d = json.load(open(OUT, encoding="utf-8"))
        print("\n" + "=" * 78)
        print(f"{'Cond.':6s} {'yolov5':8s} {'cv2thr':7s} {'detections':11s} {'FP':8s} {'F1':7s}")
        print("-" * 78)
        for k in CONDITIONS:
            if k in d:
                r = d[k]
                print(f"{k:6s} {str(r['yolov5_import']):8s} {r['environment']['cv2_threads']:<7d} "
                      f"{r['detections']:<11d} {r['fp']:<8d} {r['F1']:<7.2f}")
        # interpretation
        if all(k in d for k in "ABCD"):
            A, B, C, D = (d[k]["detections"] for k in "ABCD")
            print("-" * 78)
            print(f"A vs B (threads only, no import)          : {A} vs {B} -> "
                  f"{'NO DIFFERENCE' if A == B else 'DIFFERENT'}")
            print(f"C vs D (threads only, with import)        : {C} vs {D} -> "
                  f"{'NO DIFFERENCE' if C == D else 'DIFFERENT'}")
            print(f"A vs C (import only)                      : {A} vs {C} -> "
                  f"{'NO DIFFERENCE' if A == C else 'DIFFERENT'}")
            print(f"B vs D (threads equal, import only)       : {B} vs {D} -> "
                  f"{'NO DIFFERENCE' if B == D else 'DIFFERENT'}")
            if A == B and C == D and A != C:
                print("\nCONCLUSION: the thread count does not change the result; the import does.")
            elif A != B:
                print("\nCONCLUSION: the thread count alone changes the result; the claim must be withdrawn.")
            else:
                print("\nCONCLUSION: the table is inconclusive, more controls are needed.")
        print("\nResults ->", os.path.abspath(OUT))
