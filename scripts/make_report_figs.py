"""Generates the static figures (PNG) for the report: layer panel, radar, density scatter.

pycasa's visualization functions open a window. Here we pin matplotlib to the Agg
backend and intercept plt.show, so the figures go straight to disk with no window.

Note: every Casa session keeps the video in RAM. The four-layer panel uses its own
small session, otherwise matplotlib raises MemoryError while drawing.

    python scripts/make_report_figs.py
"""
import os, gc
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib
import matplotlib.pyplot as plt

OUT = "outputs/report"
os.makedirs(OUT, exist_ok=True)

_name_holder = ["fig"]
def _save(*a, **k):
    for num in plt.get_fignums():
        plt.figure(num).savefig(f"{OUT}/{_name_holder[0]}.png", dpi=100,
                                bbox_inches="tight", facecolor="white")
        print(f"  {OUT}/{_name_holder[0]}.png")
    plt.close("all")
    gc.collect()

plt.switch_backend("Agg")          # start the backend first, or FigureCanvas stays None
plt.switch_backend = lambda *a, **k: None
plt.show = _save
matplotlib.rcParams["figure.figsize"] = (13, 7.5)

import pycasa as pc

# --- 1) Radar and density: GT and yolo26 sources (no image rendering, memory is fine)
for label, yolo in [("gt", False), ("yolo26", True)]:
    s = pc.io.load_default_data(final_frame=60, verbose=False)
    if yolo:
        s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
        s.tracking.sort(skip_gt=True, show_progress=False, verbose=False)
    else:
        s.tracking.sort(show_progress=False, verbose=False)
    s.motility.kinematic_parameters(show_progress=False, verbose=False)
    s.motility.casa_parameters(verbose=False)
    _name_holder[0] = f"06_radar_{label}";     s.visualization.motility_radar()
    _name_holder[0] = f"07_yogunluk_{label}";  s.visualization.motility_density_scatter()
    del s; gc.collect()

# --- 2) Four-layer panel: a small session, otherwise drawing runs out of memory
p = pc.io.load_default_data(final_frame=8, verbose=False)
p.preprocessing.grayscale(show_progress=False, verbose=False)
p.preprocessing.binarization.otsu(show_progress=False, verbose=False)
p.preprocessing.normalization.clahe(show_progress=False, verbose=False)
p.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
_name_holder[0] = "08_katmanlar"
p.visualization.plot_frame(["original", "grayscale", "binarized", "normalized"], frame_index=5)
print("\nDone ->", os.path.abspath(OUT))
