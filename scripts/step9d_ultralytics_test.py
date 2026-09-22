"""Adim 9d: Sebep yolov5 reposu mu, yoksa ultralytics import'u mu?

Bulgu: bu yolov5 reposu (Ultralytics'in yeni surumu) dogrudan ultralytics'e
bagimli -- models/common.py `import ultralytics`, utils/__init__.py ise
`from ultralytics.utils import ...` yapiyor. YOLO26 yolu da zaten ultralytics
kullaniyor, yani paket ortak. Degisen sey SIRA olabilir.

Kosullar (her biri ayri process, hepsi YOLO26 calistirir):
  A  hicbir on import yok                       -> izole referans (6390)
  C  yolov5 reposu import edildi                -> kirli referans (6003)
  G  sadece `import ultralytics`                -> C'ye esitse sebep ultralytics
  H  sadece `ultralytics.utils.patches`         -> torch.load yamasi tek basina yetiyor mu

    python scripts/step9d_ultralytics_test.py
"""
import os, sys, json, subprocess

OUT = "outputs/step9d_ultralytics.json"


def calistir(kod):
    if kod == "G":
        import ultralytics  # noqa: F401
    elif kod == "H":
        from ultralytics.utils import patches  # noqa: F401

    import pycasa as pc
    if kod == "C":
        from pycasa.detection._yolo import _temporary_sys_path, _ensure_yolov5_pkg
        with _temporary_sys_path(str(_ensure_yolov5_pkg())):
            from models.common import AutoShape  # noqa: F401

    import torch
    torch_load_yamali = torch.load.__module__.startswith("ultralytics")

    s = pc.io.load_default_data(final_frame=40, verbose=False)
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    n = sum(len(v) for v in s.get_detections().values())

    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[kod] = {"detections": n, "tp": a["tp"], "fp": a["fp"], "F1": a["F1"],
              "torch_load_patched": torch_load_yamali}
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2)
    print(f"  {kod}: detections={n} tp={a['tp']} fp={a['fp']} F1={a['F1']} "
          f"| torch.load yamali={torch_load_yamali}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        calistir(sys.argv[1])
    else:
        if os.path.exists(OUT):
            os.remove(OUT)
        etiket = {"A": "on import yok", "C": "yolov5 reposu",
                  "G": "sadece ultralytics", "H": "sadece ultralytics.utils.patches"}
        for k in ("A", "C", "G", "H"):
            print(f"\n=== {k}: {etiket[k]} ===", flush=True)
            p = subprocess.run([sys.executable, __file__, k],
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            for satir in (p.stdout or "").splitlines():
                if satir.strip().startswith(k + ":"):
                    print(" ", satir.strip())
            if p.returncode != 0:
                print("  !! hata:", (p.stderr or "")[-250:])

        d = json.load(open(OUT, encoding="utf-8"))
        if all(k in d for k in "ACGH"):
            A, C, G, Hh = (d[k]["detections"] for k in "ACGH")
            print(f"\n  A on import yok      : {A}")
            print(f"  C yolov5 reposu      : {C}")
            print(f"  G sadece ultralytics : {G}")
            print(f"  H sadece patches     : {Hh}")
            print()
            if G == C and C != A:
                print("  SONUC: `import ultralytics` tek basina farki uretiyor.")
                print("  Yani sebep yolov5 reposu degil, ultralytics'in import edilme SIRASI.")
                if Hh == C:
                    print("  Ayrica ultralytics.utils.patches tek basina yetiyor (torch.load yamasi).")
            elif G == A:
                print("  SONUC: ultralytics tek basina yetmiyor, fark yolov5 reposundan geliyor.")
            else:
                print("  SONUC: tablo belirsiz.")
