import json, sys, copy
import pycasa as pc
sys.path.insert(0, "scripts")
from render_gif import render

# Adim 3: GT ustunde YOLOv5, YOLO26 ve moving-cells detection + assessment
# Adim 4: pycasa ayni anda tek bir detection modeli tutar; yeni bir detector
#         calistirinca onceki sonuc overwrite edilir (asagida print ile gosteriyoruz).
self = pc.io.load_default_data()
results = {}

def run(name, fn, **kw):
    print(f"\n{'='*20} {name} {'='*20}")
    print("detection_method BEFORE:", self.get_meta().get("detection_method"), "| frames with detections:", len(self.get_detections()))
    fn(**kw)
    print("detection_method AFTER :", self.get_meta().get("detection_method"), "| frames with detections:", len(self.get_detections()))
    print("casa top-level keys:", list(self.get_casa().keys()))
    self.assessment.evaluate_detections()
    a = self.get_assessment()
    print("assessment keys:", list(a.keys()))
    results[name] = copy.deepcopy(a)   # deepcopy: get_assessment() ayni dict'i dondurur
    render(self, f"outputs/step3_{name}_frame0.png", show_gt=True,
           det_source=True, max_frames=1,
           title=f"{name} (red) vs GT (green)")

run("yolov5", self.detection.yolo, yolo_model="yolov5")
run("yolo26", self.detection.yolo, yolo_model="yolo26")
run("moving_cells", self.detection.detect_moving_cells)

def _clean(o):
    import numpy as np
    if isinstance(o, dict): return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, np.ndarray): return o.tolist()
    return o
json.dump(_clean(results), open("outputs/step3_detection_assessment.json", "w"), indent=2)
print("\nFINAL detections in session:", list(self.get_detections().keys()))
print("\n=== RAW ASSESSMENT DUMP ===")
print(json.dumps(_clean(results), indent=1)[:6000])
