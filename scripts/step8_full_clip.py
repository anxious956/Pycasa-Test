"""Adim 8: Adim 3, 5 ve 6'yi TUM klip uzerinde tekrarla (899/901 frame, ~30 saniye).

Neden: 101 frame sadece 3.4 saniyelik bir kesit. Konsantrasyon ve toplam sayi
hesaplari frame sayisina duyarli, cunku hucre/frame ortalamasindan turetiliyorlar.
Tam klip bu hatayi belirgin sekilde dusuruyor mu, olcuyoruz.

Bellek: 899 frame x 1280x1024x3 = ~3.5 GB. Her asama ayri process'te calisir,
yoksa MemoryError aliniyor. Ayrica YOLOv5 ve YOLO26 ayri process'te olmali,
yoksa YOLOv5 import'u YOLO26 sonucunu degistiriyor.

    python scripts/step8_full_clip.py            # tum asamalar
    python scripts/step8_full_clip.py yolo26     # tek asama
"""
import os, sys, json, subprocess, gc

OUT = "outputs/step8_full_clip.json"
ASAMALAR = ["yolov5", "yolo26", "moving_cells", "sort", "jpdaf", "gt_sort", "yolo26_sort"]


def _kaydet(ad, veri):
    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[ad] = veri
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"  -> {ad} kaydedildi")


def _temiz(o):
    import numpy as np
    if isinstance(o, dict):  return {str(k): _temiz(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_temiz(v) for v in o]
    if isinstance(o, np.integer):  return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.ndarray):  return o.tolist()
    return o


def _en_buyuk_yukle():
    """Belleğe sigan en buyuk klip uzunlugunu yukle.

    Tam klip 899 frame x 1280x1024x3 = 3.3 GB TEK PARCA bellek istiyor.
    Windows commit limiti yuzunden bu blok her zaman ayrilamiyor; sigana kadar
    kademeli kuculuyoruz. Kullanilan frame sayisi sonuca yazilir.
    """
    import pycasa as pc
    # DIKKAT: basarisiz bir deneme ayirdigi belleği hemen birakmiyor. Once 899'u
    # deneyip dusmek, sonraki denemelere yer birakmiyor. Bu yuzden makul bir
    # degerden basliyor ve her basarisizliktan sonra gc.collect() cagiriyoruz.
    hedef = os.environ.get("PYCASA_MAX_FRAMES")
    if hedef == "full":   sira = [None, 800, 700, 600, 500]   # tam klip hedefli
    elif hedef:           sira = [int(hedef)]
    else:                 sira = [600, 500, 400, 300, 200]
    for ff in sira:
        try:
            s = pc.io.load_default_data(final_frame=ff)
            print(f"  yuklenen frame: {s.get_video()['number_frame_used']}")
            return s
        except MemoryError:
            print(f"  {ff} frame sigmadi, kuculuyorum", flush=True)
            gc.collect()
    raise MemoryError("en kucuk deneme bile sigmadi")


def calistir(asama):
    s = _en_buyuk_yukle()
    N = s.get_video()["number_frame_used"]

    if asama in ("yolov5", "yolo26", "moving_cells"):
        if asama == "moving_cells":
            s.detection.detect_moving_cells()
        else:
            s.detection.yolo(yolo_model=asama)
        s.assessment.evaluate_detections()
        a = s.get_assessment()
        _kaydet(asama, {"frames_loaded": N, "detection": _temiz(a["detection"]),
                        "frames": a["last_detection"]["frame_summary"]})

    elif asama in ("sort", "jpdaf"):
        getattr(s.tracking, asama)()                       # detection yok -> sadece GT
        tr = s.get_tracks()[asama]["groundtruth"]
        n = len(tr)
        _kaydet(asama, {"frames_loaded": N, "tracks": n,
                        "avg_track_length": round(sum(len(t) for t in tr.values()) / n, 2)})

    elif asama == "gt_sort":
        s.tracking.sort()
        s.motility.kinematic_parameters()
        s.motility.casa_parameters()
        m = s.get_motility()
        _kaydet("gt_sort", {"frames_loaded": N, "casa": _temiz(m["casa_parameters"]["groundtruth"]),
                            "kinematik": _ozet(m["kinematic_parameters"]["groundtruth"])})

    elif asama == "yolo26_sort":
        s.detection.yolo(yolo_model="yolo26")
        s.tracking.sort(skip_gt=True)
        s.motility.kinematic_parameters()
        s.motility.casa_parameters()
        m = s.get_motility()
        _kaydet("yolo26_sort", {"frames_loaded": N, "casa": _temiz(m["casa_parameters"]["yolo26"]),
                                "kinematik": _ozet(m["kinematic_parameters"]["yolo26"])})
    del s
    gc.collect()


def _ozet(kin):
    """Track basina pencere degerlerini tek ortalama/std'ye indir."""
    import numpy as np
    out = {}
    for p in ("VCL", "VSL", "VAP", "LIN", "ALH", "WOB", "STR", "MAD"):
        v = [x for t in kin.values() for x in t.get(p, [])]
        out[p] = [round(float(np.mean(v)), 2), round(float(np.std(v)), 2)] if v else None
    out["track_sayisi"] = len(kin)
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1:
        calistir(sys.argv[1])
    else:
        if os.path.exists(OUT):
            os.remove(OUT)
        for a in ASAMALAR:
            print(f"\n{'='*25} {a} {'='*25}", flush=True)
            p = subprocess.run([sys.executable, __file__, a],
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            for satir in (p.stdout or "").splitlines():
                if any(k in satir for k in ("yuklenen", "summary", "assessment results",
                                            "tracks=", "%rapid", "concentration", "-> ",
                                            "VCL=", "Error", "MemoryError")):
                    print("  " + satir.strip())
            if p.returncode != 0:
                print(f"  !! {a} basarisiz:", (p.stderr or "")[-300:])
        print("\nSonuclar ->", os.path.abspath(OUT))
