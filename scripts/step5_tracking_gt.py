import sys, json
import pycasa as pc
sys.path.insert(0, "scripts")
from render_gif import render

# Adim 5: sadece GT detectionlar ustunde SORT ve JPDAF tracking, timelapse ile gorsellestirme
# (interaktif pencere icin: scripts/step5_timelapse_interactive.py; burada GIF'e render ediyoruz)
self = pc.io.load_default_data()
summary = {}

self.tracking.sort()
tr = self.get_tracks()
print("get_tracks() backends:", list(tr.keys()), "| sources:", list(tr["sort"].keys()))
n = len(tr["sort"]["groundtruth"]); L = sum(len(v) for v in tr["sort"]["groundtruth"].values()) / n
summary["sort"] = {"tracks": n, "avg_track_length": round(L, 2)}
render(self, "outputs/step5_sort_gt_tracks.gif", show_gt=True, track_source=("sort", "groundtruth"),
       scale=0.4, stride=2, title="SORT on GT")

self.tracking.jpdaf()           # -> Warning: Previous tracking result overwritten (sort -> jpdaf)
tr = self.get_tracks()
print("get_tracks() backends after jpdaf:", list(tr.keys()))
n = len(tr["jpdaf"]["groundtruth"]); L = sum(len(v) for v in tr["jpdaf"]["groundtruth"].values()) / n
summary["jpdaf"] = {"tracks": n, "avg_track_length": round(L, 2)}
render(self, "outputs/step5_jpdaf_gt_tracks.gif", show_gt=True, track_source=("jpdaf", "groundtruth"),
       scale=0.4, stride=2, title="JPDAF on GT")
json.dump(summary, open("outputs/step5_tracking_summary.json", "w"), indent=2)
print(json.dumps(summary, indent=2))
