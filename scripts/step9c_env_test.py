"""Adim 9c: Sebep yolov5'in ayarladigi ortam degiskenleri mi?

yolov5 import'u su degiskenleri yaziyor (process basinda yoklardi):
  OMP_NUM_THREADS=8, NUMEXPR_MAX_THREADS=8, KINETO_LOG_LEVEL=5,
  TF_CPP_MIN_LOG_LEVEL=2, TORCH_CPP_LOG_LEVEL=ERROR

Kosul F: bu degiskenleri torch import edilmeden ONCE elle ayarla, yolov5'i
hic import etme. Sonuc kirli degere (6003) donerse sebep bu degiskenler.
Izole degerde (6390) kalirsa degil.

    python scripts/step9c_env_test.py F
"""
import os, sys, json

if len(sys.argv) > 1 and sys.argv[1] == "F":
    # torch/pycasa import edilmeden once ayarla, yoksa torch bunlari okumaz
    os.environ["OMP_NUM_THREADS"] = "8"
    os.environ["NUMEXPR_MAX_THREADS"] = "8"
    os.environ["KINETO_LOG_LEVEL"] = "5"
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
    os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"

import pycasa as pc
import torch

kod = sys.argv[1] if len(sys.argv) > 1 else "A"
s = pc.io.load_default_data(final_frame=40, verbose=False)
s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
s.assessment.evaluate_detections()
a = s.get_assessment()["detection"]
n = sum(len(v) for v in s.get_detections().values())
print(f"  {kod}: detections={n} tp={a['tp']} fp={a['fp']} F1={a['F1']} "
      f"| OMP={os.environ.get('OMP_NUM_THREADS')} torch_threads={torch.get_num_threads()}")

OUT = "outputs/step9c_env_test.json"
d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
d[kod] = {"detections": n, "tp": a["tp"], "fp": a["fp"], "F1": a["F1"],
          "omp": os.environ.get("OMP_NUM_THREADS"), "torch_threads": torch.get_num_threads()}
json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2)
