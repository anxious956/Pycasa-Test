"""Step 9c: is the cause the environment variables that yolov5 sets?

Importing yolov5 writes these variables (none of them were set at process start):
  OMP_NUM_THREADS=8, NUMEXPR_MAX_THREADS=8, KINETO_LOG_LEVEL=5,
  TF_CPP_MIN_LOG_LEVEL=2, TORCH_CPP_LOG_LEVEL=ERROR

Condition F: set these by hand BEFORE torch is imported and never import yolov5.
If the result drops to the contaminated value (6003), these variables are the
cause. If it stays at the isolated value (6390), they are not.

    python scripts/step9c_env_test.py F
"""
import os, sys, json

if len(sys.argv) > 1 and sys.argv[1] == "F":
    # must be set before torch/pycasa are imported, otherwise torch never reads them
    os.environ["OMP_NUM_THREADS"] = "8"
    os.environ["NUMEXPR_MAX_THREADS"] = "8"
    os.environ["KINETO_LOG_LEVEL"] = "5"
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
    os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"

import pycasa as pc
import torch

code = sys.argv[1] if len(sys.argv) > 1 else "A"
s = pc.io.load_default_data(final_frame=40, verbose=False)
s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
s.assessment.evaluate_detections()
a = s.get_assessment()["detection"]
n = sum(len(v) for v in s.get_detections().values())
print(f"  {code}: detections={n} tp={a['tp']} fp={a['fp']} F1={a['F1']} "
      f"| OMP={os.environ.get('OMP_NUM_THREADS')} torch_threads={torch.get_num_threads()}")

OUT = "outputs/step9c_env_test.json"
d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
d[code] = {"detections": n, "tp": a["tp"], "fp": a["fp"], "F1": a["F1"],
          "omp": os.environ.get("OMP_NUM_THREADS"), "torch_threads": torch.get_num_threads()}
json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2)
