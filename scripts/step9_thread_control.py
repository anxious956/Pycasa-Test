"""Adim 9: YOLO26 sira bagimliligi icin kontrollu deney.

Soru: YOLOv5 import'undan sonra YOLO26'nin farkli sonuc vermesinin sebebi
OpenCV thread sayisinin degismesi mi, yoksa import'un biraktigi baska bir
global durum mu?

Yanlis test: "iki calistirmada cv2.getNumThreads() farkli okunuyor" demek.
Bu sadece degisken degisti demek, o degiskenin SONUCU degistirdigini gostermez.

Dogru test: thread sayisini bagimsiz degisken olarak ele alip 2x2 tasarim kurmak.
  A  import yok,  thread varsayilan
  B  import yok,  thread 1'e zorlanmis
  C  import var,  thread 1 (import'un birakti hal)
  D  import var,  thread varsayilana geri alinmis

Beklentiler:
  Sebep thread ise      -> A != B  ve  D ~ A  (thread'i geri alinca fark kapanir)
  Sebep import ise      -> A ~ B   ve  C ~ D  (thread ne olursa olsun fark surer)

Her kosul AYRI process'te calisir; ayni process'te import geri alinamaz.

    python scripts/step9_thread_control.py           # dortunu de calistir
    python scripts/step9_thread_control.py A         # tek kosul
"""
import os, sys, json, subprocess

OUT = "outputs/step9_thread_control.json"
FRAMES = 40
KOSULLAR = {
    "A": ("import yok", "thread varsayilan"),
    "B": ("import yok", "thread 1'e zorlanmis"),
    "C": ("import VAR", "thread 1 (import sonrasi hal)"),
    "D": ("import VAR", "thread varsayilana geri alinmis"),
}


def calistir(kod):
    import cv2
    import pycasa as pc

    varsayilan_cv2 = cv2.getNumThreads()
    import_edildi = False

    if kod in ("C", "D"):
        from pycasa.detection._yolo import _temporary_sys_path, _ensure_yolov5_pkg
        with _temporary_sys_path(str(_ensure_yolov5_pkg())):
            from models.common import AutoShape, DetectMultiBackend   # noqa: F401
        import_edildi = True

    if kod == "B":
        cv2.setNumThreads(1)
    elif kod == "D":
        cv2.setNumThreads(varsayilan_cv2)      # import'un dusurdugu degeri geri al

    import torch
    olculen = {
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

    sonuc = {"kosul": kod, "aciklama": KOSULLAR[kod], "yolov5_import": import_edildi,
             "cv2_varsayilan": varsayilan_cv2, "ortam": olculen,
             "detections": n, "tp": a["tp"], "fp": a["fp"], "fn": a["fn"],
             "precision": a["precision"], "recall": a["recall"], "F1": a["F1"]}

    d = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    d[kod] = sonuc
    json.dump(d, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"  {kod}: detections={n} tp={a['tp']} fp={a['fp']} F1={a['F1']} "
          f"| cv2_threads={olculen['cv2_threads']} torch_threads={olculen['torch_threads']}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        calistir(sys.argv[1])
    else:
        if os.path.exists(OUT):
            os.remove(OUT)
        for k, (imp, thr) in KOSULLAR.items():
            print(f"\n=== {k}: {imp}, {thr} ===", flush=True)
            p = subprocess.run([sys.executable, __file__, k],
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            for satir in (p.stdout or "").splitlines():
                if satir.strip().startswith(k + ":"):
                    print(" ", satir.strip())
            if p.returncode != 0:
                print("  !! hata:", (p.stderr or "")[-250:])

        d = json.load(open(OUT, encoding="utf-8"))
        print("\n" + "=" * 78)
        print(f"{'Kosul':6s} {'yolov5':8s} {'cv2thr':7s} {'detections':11s} {'FP':8s} {'F1':7s}")
        print("-" * 78)
        for k in KOSULLAR:
            if k in d:
                r = d[k]
                print(f"{k:6s} {str(r['yolov5_import']):8s} {r['ortam']['cv2_threads']:<7d} "
                      f"{r['detections']:<11d} {r['fp']:<8d} {r['F1']:<7.2f}")
        # yorum
        if all(k in d for k in "ABCD"):
            A, B, C, D = (d[k]["detections"] for k in "ABCD")
            print("-" * 78)
            print(f"A vs B (sadece thread degisti, import yok) : {A} vs {B} -> "
                  f"{'FARK YOK' if A == B else 'FARKLI'}")
            print(f"C vs D (sadece thread degisti, import var) : {C} vs {D} -> "
                  f"{'FARK YOK' if C == D else 'FARKLI'}")
            print(f"A vs C (sadece import degisti)             : {A} vs {C} -> "
                  f"{'FARK YOK' if A == C else 'FARKLI'}")
            print(f"B vs D (thread esit, sadece import degisti): {B} vs {D} -> "
                  f"{'FARK YOK' if B == D else 'FARKLI'}")
            if A == B and C == D and A != C:
                print("\nSONUC: thread sayisi sonucu degistirmiyor; degisken import.")
            elif A != B:
                print("\nSONUC: thread sayisi tek basina sonucu degistiriyor; iddia geri cekilmeli.")
            else:
                print("\nSONUC: tablo belirsiz, daha fazla kontrol gerekiyor.")
        print("\nSonuclar ->", os.path.abspath(OUT))
