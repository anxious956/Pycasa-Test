"""Rapor icin durgun grafikleri (PNG) uretir: katman paneli, radar, yogunluk dagilimi.

pycasa'nin gorsellestirme fonksiyonlari pencere aciyor. Burada matplotlib'i Agg
arka ucuna sabitleyip plt.show'u yakaliyoruz, boylece pencere acilmadan dosyaya yaziliyor.

Not: her Casa session'i videoyu RAM'de tutuyor. Dort katmanli panel icin ayri ve
kucuk bir session kullaniyoruz, yoksa matplotlib cizim sirasinda MemoryError veriyor.

    python scripts/make_report_figs.py
"""
import os, gc
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib
import matplotlib.pyplot as plt

OUT = "outputs/report"
os.makedirs(OUT, exist_ok=True)

_ad = ["fig"]
def _kaydet(*a, **k):
    for num in plt.get_fignums():
        plt.figure(num).savefig(f"{OUT}/{_ad[0]}.png", dpi=100,
                                bbox_inches="tight", facecolor="white")
        print(f"  {OUT}/{_ad[0]}.png")
    plt.close("all")
    gc.collect()

plt.switch_backend("Agg")          # arka ucu once baslat, yoksa FigureCanvas None kalir
plt.switch_backend = lambda *a, **k: None
plt.show = _kaydet
matplotlib.rcParams["figure.figsize"] = (13, 7.5)

import pycasa as pc

# --- 1) Radar ve yogunluk: GT ve yolo26 kaynaklari (goruntu cizimi yok, bellek rahat)
for etiket, yolo in [("gt", False), ("yolo26", True)]:
    s = pc.io.load_default_data(final_frame=60, verbose=False)
    if yolo:
        s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
        s.tracking.sort(skip_gt=True, show_progress=False, verbose=False)
    else:
        s.tracking.sort(show_progress=False, verbose=False)
    s.motility.kinematic_parameters(show_progress=False, verbose=False)
    s.motility.casa_parameters(verbose=False)
    _ad[0] = f"06_radar_{etiket}";     s.visualization.motility_radar()
    _ad[0] = f"07_yogunluk_{etiket}";  s.visualization.motility_density_scatter()
    del s; gc.collect()

# --- 2) Dort katmanli panel: kucuk session, yoksa cizim sirasinda bellek yetmiyor
p = pc.io.load_default_data(final_frame=8, verbose=False)
p.preprocessing.grayscale(show_progress=False, verbose=False)
p.preprocessing.binarization.otsu(show_progress=False, verbose=False)
p.preprocessing.normalization.clahe(show_progress=False, verbose=False)
p.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
_ad[0] = "08_katmanlar"
p.visualization.plot_frame(["original", "grayscale", "binarized", "normalized"], frame_index=5)
print("\nBitti ->", os.path.abspath(OUT))
