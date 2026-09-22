import pycasa as pc

# Step 1: load the default dataset
self = pc.io.load_default_data()

print("\n=== META ===")
meta = self.get_meta()
for k in ("um_per_px", "volume_ml", "chamber_depth_um", "dilution_factor", "fps", "frame_rate"):
    if k in meta:
        print(f"{k}: {meta[k]}")
print("\nAll meta keys:", sorted(meta.keys()))

video = self.get_video()
print("\n=== VIDEO ===")
print("video keys:", list(video.keys()))
gt = self.get_groundtruth()
print("\n=== GROUNDTRUTH ===")
print("gt keys:", list(gt.keys())[:10])
tr = self.get_tracks()
print("\n=== TRACKS ===")
print("tracks:", tr)
