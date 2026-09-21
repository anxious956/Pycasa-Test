import json, copy, csv
import numpy as np
import pycasa as pc

# Adim 6: (a) GT + SORT  (b) YOLO26 + SORT  -> kinematic + CASA parametreleri,
#         HSTLI sys-casa_casaMotilityReports.csv (HC004, unwashed) ile karsilastirma.

def _clean(o):
    if isinstance(o, dict): return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_clean(v) for v in o]
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.ndarray): return o.tolist()
    return o

results = {}

def pipeline(name, use_yolo26):
    print(f"\n{'#'*25} {name} {'#'*25}")
    s = pc.io.load_default_data()
    if use_yolo26:
        s.detection.yolo(yolo_model="yolo26")
        s.tracking.sort(skip_gt=True)          # sadece yolo26 detectionlari track'le
    else:
        s.tracking.sort()                       # detection yok -> sadece GT
    s.motility.kinematic_parameters()          # VCL, VSL, VAP, LIN, ALH, WOB, STR, MAD
    s.motility.casa_parameters()               # %rapid/%slow/%non-progressive/%immotile, concentration
    m = copy.deepcopy(s.get_motility())
    print("motility keys:", list(m.keys()))
    results[name] = _clean(m)

pipeline("gt_sort", use_yolo26=False)
pipeline("yolo26_sort", use_yolo26=True)

json.dump(results, open("outputs/step6_motility_results.json", "w"), indent=2)
print("\n=== RAW MOTILITY DUMP (truncated) ===")
for k, v in results.items():
    print(f"\n--- {k} ---")
    print(json.dumps(v, indent=1)[:3500])
