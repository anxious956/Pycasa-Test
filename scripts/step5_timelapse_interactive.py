import pycasa as pc
# Interactive timelapse: SORT first; closing the window opens the JPDAF one.
self = pc.io.load_default_data()
self.tracking.sort()
self.visualization.timelapse(video_type="original", show_detections=False, show_groundtruth=True, show_tracks=True)
self.tracking.jpdaf()
self.visualization.timelapse(video_type="original", show_detections=False, show_groundtruth=True, show_tracks=True)
