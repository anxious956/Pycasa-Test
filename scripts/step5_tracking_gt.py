"""Step 5: SORT and JPDAF tracking on the ground-truth detections only.

No detector is active, so both trackers see identical input and any difference
between them is the association algorithm itself. Running jpdaf() after sort()
also demonstrates that pycasa keeps only one tracking result at a time.

For an interactive window use scripts/step5_timelapse_interactive.py.
For the figures and animations use scripts/make_report_gifs.py.

    python scripts/step5_tracking_gt.py
"""
import json
import pycasa as pc

self = pc.io.load_default_data()
summary = {}

self.tracking.sort()
tr = self.get_tracks()
print("get_tracks() backends:", list(tr.keys()), "| sources:", list(tr["sort"].keys()))
n = len(tr["sort"]["groundtruth"]); L = sum(len(v) for v in tr["sort"]["groundtruth"].values()) / n
summary["sort"] = {"tracks": n, "avg_track_length": round(L, 2)}

self.tracking.jpdaf()           # -> Warning: Previous tracking result overwritten (sort -> jpdaf)
tr = self.get_tracks()
print("get_tracks() backends after jpdaf:", list(tr.keys()))
n = len(tr["jpdaf"]["groundtruth"]); L = sum(len(v) for v in tr["jpdaf"]["groundtruth"].values()) / n
summary["jpdaf"] = {"tracks": n, "avg_track_length": round(L, 2)}

json.dump(summary, open("outputs/step5_tracking_summary.json", "w"), indent=2)
print(json.dumps(summary, indent=2))
