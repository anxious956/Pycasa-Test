"""Visuals for the beginner-level presentation.

Three assets that explain the pipeline to someone with no background:

  10_raw_video.gif      the microscope video with nothing drawn on it -- "what we start with"
  11_one_cell.gif       one sperm cell, zoomed in, with its path drawn as it swims
  12_speed_explained.png  the same cell's full path, with the curvy path and the
                        straight line drawn on top -- shows what "speed" means

    python scripts/make_explainer_visuals.py
"""
import os
import numpy as np
import cv2
import imageio.v2 as imageio
import pycasa as pc

OUT = "outputs/report"
FRAMES = 100
ORANGE = (40, 165, 255)     # BGR
WHITE = (255, 255, 255)
CYAN = (255, 220, 80)


def raw_video(video):
    """The unannotated clip, downscaled, every second frame."""
    frames = []
    for i in range(0, len(video), 3):
        img = cv2.resize(video[i], (480, 384), interpolation=cv2.INTER_AREA)
        frames.append(img)
    path = f"{OUT}/10_raw_video.gif"
    imageio.mimsave(path, frames, duration=1 / 10, loop=0, subrectangles=True)
    cv2.imwrite(path.replace(".gif", ".png"), cv2.cvtColor(frames[len(frames) // 2], cv2.COLOR_RGB2BGR))
    print(f"  {path}  ({os.path.getsize(path) / 1e6:.1f} MB)")


def pick_cell(tracks):
    """A cell that clearly swims FORWARD while wiggling.

    For a beginner the picture has to read at a glance: the path should start at
    one end and finish at the other, never doubling back behind its start point.
    Among those, prefer the curviest path, so the gap between "path speed" and
    "straight-line speed" is easy to see.
    """
    best, best_score = None, -1
    for tid, pts in tracks.items():
        fs = sorted(int(f) for f in pts)
        if len(fs) < 70 or fs[-1] - fs[0] > len(fs) + 5:      # long and unbroken
            continue
        xy = np.array([pts[str(f)] if str(f) in pts else pts[f] for f in fs], float)
        net_vec = xy[-1] - xy[0]
        net = np.linalg.norm(net_vec)
        if net < 90:
            continue
        # forward progress: project every point on the start->end direction
        t = (xy - xy[0]) @ (net_vec / net)
        if t.min() < -0.05 * net or t.max() > 1.08 * net:
            continue
        path_len = np.sum(np.linalg.norm(np.diff(xy, axis=0), axis=1))
        ratio = path_len / net
        if ratio < 1.6:                                          # needs visible wiggle
            continue
        score = net * min(ratio, 4.0)
        if score > best_score:
            best, best_score = (tid, fs, xy), score
    return best


def one_cell(video, cell):
    """Crop around one cell and animate its path growing."""
    tid, fs, xy = cell
    H, W = video.shape[1:3]
    x0, y0 = xy.min(axis=0) - 45
    x1, y1 = xy.max(axis=0) + 45
    side = int(max(x1 - x0, y1 - y0))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0 = int(np.clip(cx - side / 2, 0, W - side))
    y0 = int(np.clip(cy - side / 2, 0, H - side))
    zoom = 460 / side

    frames = []
    for k, f in enumerate(fs):
        if k % 2 and k != len(fs) - 1:          # every second frame keeps the GIF small
            continue
        img = cv2.cvtColor(video[f], cv2.COLOR_RGB2BGR)[y0:y0 + side, x0:x0 + side].copy()
        img = cv2.resize(img, (460, 460), interpolation=cv2.INTER_CUBIC)
        pts = ((xy[:k + 1] - [x0, y0]) * zoom).astype(int)
        if len(pts) > 1:
            cv2.polylines(img, [pts], False, ORANGE, 3, cv2.LINE_AA)
        cv2.circle(img, tuple(pts[-1]), 16, CYAN, 3, cv2.LINE_AA)
        frames.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    path = f"{OUT}/11_one_cell.gif"
    durations = [1 / 8] * (len(frames) - 1) + [2.5]
    imageio.mimsave(path, frames, duration=durations, loop=0, subrectangles=True)
    print(f"  {path}  ({os.path.getsize(path) / 1e6:.1f} MB, track {tid}, {len(fs)} frames)")
    return x0, y0, side, zoom


def speed_explained(video, cell, crop, um_per_px, fps):
    """The full path of the cell, with the curvy path and the straight line."""
    tid, fs, xy = cell
    x0, y0, side, zoom = crop
    img = cv2.cvtColor(video[fs[-1]], cv2.COLOR_RGB2BGR)[y0:y0 + side, x0:x0 + side].copy()
    img = cv2.resize(img, (460, 460), interpolation=cv2.INTER_CUBIC)
    img = (img * 0.7).astype(np.uint8)
    pts = ((xy - [x0, y0]) * zoom).astype(int)

    cv2.polylines(img, [pts], False, ORANGE, 4, cv2.LINE_AA)            # the real path
    a, b = tuple(pts[0]), tuple(pts[-1])
    n = 22                                                              # dashed straight line
    for i in range(n):
        if i % 2 == 0:
            p = (int(a[0] + (b[0] - a[0]) * i / n), int(a[1] + (b[1] - a[1]) * i / n))
            q = (int(a[0] + (b[0] - a[0]) * (i + 1) / n), int(a[1] + (b[1] - a[1]) * (i + 1) / n))
            cv2.line(img, p, q, WHITE, 3, cv2.LINE_AA)
    cv2.circle(img, a, 9, WHITE, -1, cv2.LINE_AA)
    cv2.circle(img, b, 9, CYAN, -1, cv2.LINE_AA)

    path_len = np.sum(np.linalg.norm(np.diff(xy, axis=0), axis=1)) * um_per_px
    net = np.linalg.norm(xy[-1] - xy[0]) * um_per_px
    secs = (fs[-1] - fs[0]) / fps
    path = f"{OUT}/12_speed_explained.png"
    cv2.imwrite(path, img)
    print(f"  {path}")
    print(f"     path speed     (VCL) = {path_len / secs:5.1f} um/s")
    print(f"     straight speed (VSL) = {net / secs:5.1f} um/s")
    return round(path_len / secs, 1), round(net / secs, 1)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    s = pc.io.load_default_data(final_frame=FRAMES, verbose=False)
    video = np.asarray(s.get_video()["original_video"])
    meta = s.get_meta()
    raw_video(video)
    s.tracking.sort(show_progress=False, verbose=False)
    tracks = s.get_tracks()["sort"]["groundtruth"]
    cell = pick_cell(tracks)
    crop = one_cell(video, cell)
    vcl, vsl = speed_explained(video, cell, crop, meta["um_per_px"], meta["sampling_rate"])
    with open(f"{OUT}/12_speed_explained.txt", "w") as f:
        f.write(f"{vcl}\n{vsl}\n")
