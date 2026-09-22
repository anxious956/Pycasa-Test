"""Generates the GIFs and PNGs for the report.

pycasa's timelapse opens an interactive window and never writes to disk. This
script draws the same overlays (GT boxes, detection boxes, track trajectories,
legend) and writes them under outputs/report/ as GIF + cover PNG.

Usage:
    python scripts/make_report_gifs.py              # generate everything
    python scripts/make_report_gifs.py full         # just one of them

Each figure is written in two formats:
  .mp4  H.264 video - for PowerPoint. Small file, full resolution, sharp image.
  .gif  for GitHub/markdown (PowerPoint plays GIFs too, but the file is large).
  .png  the middle frame; use it wherever animation is not an option.

Generated:
    01_gt_only          GT boxes (step 2)
    02_gt_vs_yolo26     GT + YOLO26 boxes side by side (step 3)
    03_sort_gt          SORT trajectories over GT (step 5)
    04_jpdaf_gt         JPDAF trajectories over GT (step 5)
    05_full             GT + YOLO26 boxes + both track sets (the full timelapse)
"""
import os, sys, gc
import numpy as np
import cv2
import imageio.v2 as imageio
import pycasa as pc

OUT = "outputs/report"
os.makedirs(OUT, exist_ok=True)

FRAMES = 60          # 61 frames
GIF_SCALE = 0.45     # 1280x1024 -> 576x460, kept small for the GIF
MP4_SCALE = 0.70     # 896x716, more than sharp enough on a PowerPoint slide
GIF_STRIDE = 2       # 31 frames in the GIF (to keep the file size down)
MP4_STRIDE = 1       # 61 frames in the MP4 (free, since H.264 compresses it)
FPS = 12
TRAIL = 25           # how many frames back the trajectory tail extends

# BGR (cv2) colors
GREEN  = (0, 255, 0)         # groundtruth boxes
RED    = (60, 60, 255)       # detection boxes
BLUE   = (255, 200, 80)      # tracks over GT
ORANGE = (40, 160, 255)      # tracks over detections


def _boxes(rows, W, H):
    """Convert YOLO rows (cls cx cy w h, normalized) to pixel boxes."""
    out = []
    for r in rows or []:
        v = [float(x) for x in np.asarray(r).ravel()[:5]]
        if len(v) < 5:
            continue
        _, cx, cy, w, h = v
        if max(cx, cy, w, h) <= 1.5:
            cx, cy, w, h = cx * W, cy * H, w * W, h * H
        out.append((int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2)))
    return out


def _trails(tracks, W, H):
    """{track_id: {frame: [x, y]}} -> {frame: [(x, y), ...]}"""
    per_frame = {}
    for pts in (tracks or {}).values():
        for f, xy in pts.items():
            x, y = float(xy[0]), float(xy[1])
            if max(x, y) <= 1.5:
                x, y = x * W, y * H
            per_frame.setdefault(int(f), []).append((x, y))
    return per_frame


def _legend(img, legendItems, y0=42, scale=1.0):
    """Color key; y0 starts just below the title bar."""
    pad, rowH, width = int(8 * scale), int(20 * scale), int(250 * scale)
    height = pad * 2 + rowH * len(legendItems)
    x0 = img.shape[1] - width - int(10 * scale)
    cover = img[y0:y0 + height, x0:x0 + width].copy()
    cv2.rectangle(img, (x0, y0), (x0 + width, y0 + height), (25, 25, 25), -1)
    cv2.addWeighted(cover, 0.25, img[y0:y0 + height, x0:x0 + width], 0.75, 0,
                    img[y0:y0 + height, x0:x0 + width])
    for i, (label, colour, kind) in enumerate(legendItems):
        y = y0 + pad + rowH * i + int(13 * scale)
        k = max(2, int(2 * scale))
        if kind == "box":
            cv2.rectangle(img, (x0 + pad, y - int(9 * scale)),
                          (x0 + pad + int(14 * scale), y + int(3 * scale)), colour, k)
        else:
            cv2.line(img, (x0 + pad, y - int(3 * scale)),
                     (x0 + pad + int(14 * scale), y - int(3 * scale)), colour, k)
        cv2.putText(img, label, (x0 + pad + int(22 * scale), y + int(2 * scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42 * scale, (245, 245, 245),
                    max(1, int(scale)), cv2.LINE_AA)


def render(session, name, title, *, gt=True, det=False, gt_track=None, det_track=None,
           det_label="yolo26", stride=None):
    """Generate a single GIF plus its cover PNG."""
    video = np.asarray(session.get_video()["original_video"])
    N, H, W = video.shape[:3]
    gt_box = session.get_groundtruth() if gt else {}
    det_box = session.get_detections() if det else {}
    gt_trails = _trails(gt_track, W, H)
    det_trails = _trails(det_track, W, H)

    legendItems = []
    if gt:        legendItems.append(("groundtruth", GREEN, "box"))
    if det:       legendItems.append((f"detections ({det_label})", RED, "box"))
    if gt_track:  legendItems.append(("tracks (groundtruth)", BLUE, "line"))
    if det_track: legendItems.append((f"tracks ({det_label})", ORANGE, "line"))

    def _draw(i, scale):
        img = cv2.cvtColor(video[i], cv2.COLOR_RGB2BGR).copy()
        for f in range(max(0, i - TRAIL), i + 1):
            thickness = 2 if f < i - 6 else 3
            for x, y in gt_trails.get(f, []):
                cv2.circle(img, (int(x), int(y)), thickness, BLUE, -1)
            for x, y in det_trails.get(f, []):
                cv2.circle(img, (int(x), int(y)), thickness, ORANGE, -1)
        for b in _boxes(det_box.get(str(i)), W, H):
            cv2.rectangle(img, b[:2], b[2:], RED, 2)
        for b in _boxes(gt_box.get(str(i)), W, H):
            cv2.rectangle(img, b[:2], b[2:], GREEN, 2)
        # H.264 requires even dimensions, hence // 2 * 2
        img = cv2.resize(img, (int(W * scale) // 2 * 2, int(H * scale) // 2 * 2),
                         interpolation=cv2.INTER_AREA)
        ui_scale = img.shape[1] / 576.0          # scale text and legend with the resolution
        cv2.rectangle(img, (0, 0), (img.shape[1], int(34 * ui_scale)), (20, 20, 20), -1)
        cv2.putText(img, f"{title}  |  frame {i}", (int(10 * ui_scale), int(23 * ui_scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6 * ui_scale, (80, 230, 255),
                    max(1, int(ui_scale)), cv2.LINE_AA)
        if legendItems:
            _legend(img, legendItems, y0=int(42 * ui_scale), scale=ui_scale)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # MP4 (for PowerPoint): full resolution, every frame.
    # We do not accumulate frames in a list; 61 frames of 1152x920 fill RAM and
    # kill the ffmpeg process (BrokenPipe). We stream them out one by one.
    mp4 = f"{OUT}/{name}.mp4"
    idx = list(range(0, N, stride or MP4_STRIDE))
    middle = idx[len(idx) // 2]
    with imageio.get_writer(mp4, fps=FPS, codec="libx264", quality=6,
                            macro_block_size=1) as writer:
        for i in idx:
            frame = _draw(i, MP4_SCALE)
            writer.append_data(frame)
            if i == middle:
                cv2.imwrite(f"{OUT}/{name}.png", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            del frame
    gc.collect()

    # GIF (for GitHub/markdown): small scale, every 2nd frame.
    # The GIF palette needs all the frames, but at this scale the list stays small.
    gif_frames = [_draw(i, GIF_SCALE) for i in range(0, N, stride or GIF_STRIDE)]
    gif = f"{OUT}/{name}.gif"
    imageio.mimsave(gif, gif_frames, duration=1 / FPS, loop=0, subrectangles=True)
    del gif_frames
    gc.collect()
    png = f"{OUT}/{name}.png"

    print(f"  {mp4}  ({os.path.getsize(mp4)/1e6:.1f} MB)   "
          f"{gif}  ({os.path.getsize(gif)/1e6:.1f} MB)   {png}")


def _fresh_session():
    return pc.io.load_default_data(final_frame=FRAMES, verbose=False)


def make_gt_only():
    print("01_gt_only: groundtruth boxes only")
    render(_fresh_session(), "01_gt_only", "Groundtruth detections")


def make_gt_vs_yolo26():
    print("02_gt_vs_yolo26: GT + YOLO26 boxes")
    s = _fresh_session(); s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    render(s, "02_gt_vs_yolo26", "GT (green) vs YOLO26 (red)", det=True)


def make_sort_gt():
    print("03_sort_gt: SORT over GT")
    s = _fresh_session(); s.tracking.sort(show_progress=False, verbose=False)
    render(s, "03_sort_gt", "SORT on groundtruth",
           gt_track=s.get_tracks()["sort"]["groundtruth"])


def make_jpdaf_gt():
    print("04_jpdaf_gt: JPDAF over GT")
    s = _fresh_session(); s.tracking.jpdaf(show_progress=False, verbose=False)
    render(s, "04_jpdaf_gt", "JPDAF on groundtruth",
           gt_track=s.get_tracks()["jpdaf"]["groundtruth"])


def make_full():
    print("05_full: GT + YOLO26 boxes + both track sets")
    s = _fresh_session()
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.tracking.sort(show_progress=False, verbose=False)
    tr = s.get_tracks()["sort"]
    render(s, "05_full", "GT + YOLO26 + SORT tracks", det=True,
           gt_track=tr.get("groundtruth"), det_track=tr.get("yolo26"))


ALL_FIGURES = {"gt": make_gt_only, "det": make_gt_vs_yolo26, "sort": make_sort_gt,
               "jpdaf": make_jpdaf_gt, "full": make_full}

if __name__ == "__main__":
    selection = sys.argv[1:] or list(ALL_FIGURES)
    for name in selection:
        ALL_FIGURES[name]()
    print("\nDone ->", os.path.abspath(OUT))
