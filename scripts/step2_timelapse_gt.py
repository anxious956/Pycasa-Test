import pycasa as pc

# Adim 2: default datayi sadece GT detectionlarla timelapse ile gorsellestir
# (hicbir detection/tracking calistirilmadi; default datada GT track yok, sadece GT detection var)
self = pc.io.load_default_data()

self.visualization.timelapse(
    video_type="original",
    show_detections=False,   # predicted detection yok
    show_tracks=False,       # track yok
    show_groundtruth=True,   # sadece GT bounding box'lar (lime)
)
