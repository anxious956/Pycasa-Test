"""Adim 9b: YOLO26 farkinin sebebi modul golgelemesi mi?

Gozlem: yolov5 reposunun paketleri GENEL isimli -- `models` ve `utils`.
Import edilince sys.modules'a bu isimlerle giriyorlar. Ultralytics de kendi
icinde `utils` gibi isimler kullaniyor; yolov5'inkini gorup yanlis modulu
alabilir. Eger sebep buysa, import'tan sonra sys.modules'i temizlemek
sonucu izole degere geri dondurur.

Kosullar (her biri ayri process):
  A  import yok                          -> referans "izole" deger
  C  import var, temizlik yok            -> referans "kirli" deger
  E  import var, sys.modules temizlendi  -> A'ya donerse sebep golgeleme

    python scripts/step9b_module_shadow.py
"""
import os, sys, json, subprocess

OUT = "outputs/step9b_module_shadow.json"
FRAMES = 40


def calistir(kod):
    import pycasa as pc
    eklenen = []

    if kod in ("C", "E"):
        oncesi = set(sys.modules)
        from pycasa.detection._yolo import _temporary_sys_path, _ensure_yolov5_pkg
        with _temporary_sys_path(str(_ensure_yolov5_pkg())):
            from models.common import AutoShape, DetectMultiBackend   # noqa: F401
        eklenen = sorted(set(sys.modules) - oncesi)

    temizlenen = []
    if kod == "E":
        # yolov5'in genel isimli paketlerini ve alt modullerini sys.modules'tan cikar
        for ad in list(sys.modules):
            kok = ad.split(".")[0]
            if kok in ("models", "utils"):
                del sys.modules[ad]
                temizlenen.append(ad)

    s = pc.io.load_default_data(final_frame=FRAMES, verbose=False)
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    n = sum(len(v) for v in s.get_detections().values())

    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[kod] = {"detections": n, "tp": a["tp"], "fp": a["fp"], "F1": a["F1"],
              "eklenen_modul": len(eklenen),
              "golgeleyen": [m for m in eklenen if m.split(".")[0] in ("models", "utils")][:8],
              "temizlenen_modul": len(temizlenen)}
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"  {kod}: detections={n} tp={a['tp']} fp={a['fp']} F1={a['F1']} "
          f"| eklenen={len(eklenen)} temizlenen={len(temizlenen)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        calistir(sys.argv[1])
    else:
        if os.path.exists(OUT):
            os.remove(OUT)
        for k in ("A", "C", "E"):
            print(f"\n=== {k} ===", flush=True)
            p = subprocess.run([sys.executable, __file__, k],
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            for satir in (p.stdout or "").splitlines():
                if satir.strip().startswith(k + ":"):
                    print(" ", satir.strip())
            if p.returncode != 0:
                print("  !! hata:", (p.stderr or "")[-250:])

        d = json.load(open(OUT, encoding="utf-8"))
        if all(k in d for k in "ACE"):
            A, C, E = (d[k]["detections"] for k in "ACE")
            print(f"\n  A (izole)            : {A}")
            print(f"  C (import, temizsiz) : {C}")
            print(f"  E (import, temizli)  : {E}")
            print(f"  golgeleyen modul     : {d['C']['golgeleyen']}")
            print()
            if E == A and C != A:
                print("  SONUC: temizlik farki kapatti -> sebep MODUL GOLGELEMESI.")
                print("  Duzeltme: yolov5 import'undan sonra sys.modules'tan 'models' ve 'utils' cikarilmali.")
            elif E == C:
                print("  SONUC: temizlik ise yaramadi -> sebep golgeleme DEGIL, baska bir kalici durum.")
            else:
                print("  SONUC: ucu de farkli, tablo belirsiz.")
