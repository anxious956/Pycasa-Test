"""Adim 9e: yolov5 import zincirini ikiye bolerek suclu modulu bul.

models/common.py su modulleri import ediyor. Her birini TEK BASINA, ayri bir
process'te import edip YOLO26'yi calistiriyoruz. Sonucu 6003'e (kirli) ceken
modul suclu; 6390'da (izole) birakan masum.

Kullanim (proje klasorunde, setup_env'den sonra):
    python scripts/step9e_bisect.py            # tum adaylar
    python scripts/step9e_bisect.py general    # tek aday

Ciktiyi oldugu gibi yapistir; tablo tek basina okunur.
"""
import os, sys, json, subprocess

OUT = "outputs/step9e_bisect.json"
FRAMES = 40

# ad -> import ifadesi (yolov5 dizini sys.path'e eklenmis halde calisir)
ADAYLAR = {
    "none":         None,                                              # referans A
    "plotting":     "from ultralytics.utils.plotting import Annotator",  # satir 38
    "utils_init":   "import utils",                                    # utils/__init__.py
    "dataloaders":  "from utils.dataloaders import letterbox",         # satir 41
    "general":      "import utils.general",                            # satir 42
    "torch_utils":  "from utils.torch_utils import smart_inference_mode",  # satir 59
    "common_full":  "from models.common import AutoShape",             # referans C
}


def calistir(ad):
    ifade = ADAYLAR[ad]
    import pycasa as pc
    if ifade:
        from pycasa.detection._yolo import _temporary_sys_path, _ensure_yolov5_pkg
        with _temporary_sys_path(str(_ensure_yolov5_pkg())):
            exec(ifade, {})
    s = pc.io.load_default_data(final_frame=FRAMES, verbose=False)
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    n = sum(len(v) for v in s.get_detections().values())
    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[ad] = {"detections": n, "tp": a["tp"], "fp": a["fp"], "F1": a["F1"]}
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2)
    print(f"  {ad}: detections={n} tp={a['tp']} fp={a['fp']} F1={a['F1']}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        calistir(sys.argv[1])
        sys.exit()
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
    kirli = d.get("common_full", {}).get("detections")
    print(f"\n{'aday':13s} {'import':48s} {'det':>6s} {'FP':>6s} {'F1':>7s}  hukum")
    print("-" * 95)
    for ad, ifade in ADAYLAR.items():
        r = d.get(ad)
        if not r:
            print(f"{ad:13s} {(ifade or '-')[:48]:48s} {'HATA':>6s}"); continue
        if ad in ("none", "common_full"):
            hukum = "referans"
        elif r["detections"] == kirli:
            hukum = "SUCLU  <-- farki tek basina uretiyor"
        elif r["detections"] == izole:
            hukum = "masum"
        else:
            hukum = "kismi (ne izole ne kirli)"
        print(f"{ad:13s} {(ifade or '-')[:48]:48s} {r['detections']:>6d} {r['fp']:>6d} {r['F1']:>7.2f}  {hukum}")
    print(f"\nizole={izole}  kirli={kirli}")
