import pycasa as pc
# Interaktif timelapse: once SORT, pencereyi kapatinca JPDAF acilir.
self = pc.io.load_default_data()
self.tracking.sort()
self.visualization.timelapse(video_type="original", show_detections=False, show_groundtruth=True, show_tracks=True)
self.tracking.jpdaf()
self.visualization.timelapse(video_type="original", show_detections=False, show_groundtruth=True, show_tracks=True)
