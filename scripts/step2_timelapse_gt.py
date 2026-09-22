import pycasa as pc

# Step 2: visualise the default dataset as a timelapse showing only the GT detections
# (no detection/tracking was run; the default dataset has GT detections but no GT tracks)
self = pc.io.load_default_data()

self.visualization.timelapse(
    video_type="original",
    show_detections=False,   # no predicted detections
    show_tracks=False,       # no tracks
    show_groundtruth=True,   # GT bounding boxes only (lime)
)
