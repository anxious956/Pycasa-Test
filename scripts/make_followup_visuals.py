"""Visuals and numbers for the follow-up presentation.

Two questions from the professor:

  1) How do the two YOLO versions compare?
       14_yolov5_vs_yolo26.gif / .png   same frames, YOLOv5 on the left, YOLO26 on the right,
                                        green = hand-marked cell, red = software box
  2) What happens to the tracks when two cells collide?  SORT vs JPDAF.
       13_collision_sort_vs_jpdaf.gif   zoomed crop around one collision, both trackers side by side
       13_collision_strip.png           before / during / after, SORT top row, JPDAF bottom row
       13_collision.json                the chosen event + counts over EVERY collision in the clip

Stages (kept separate; `find` needs no video):

    python scripts/make_followup_visuals.py find      # list collision events, write the JSON
    python scripts/make_followup_visuals.py render    # draw the chosen collision (loads ~100 frames)
    python scripts/make_followup_visuals.py detectors # all five detectors on frames 0-99 + the overlays
    python scripts/make_followup_visuals.py full      # Urbano + digital washing on all 899 frames (slow)

The collision detector works on the hand-marked boxes only, so it treats both
trackers the same way. Track positions come from outputs/report/tracks_fullclip.json,
written by make_tracker_sidebyside.py extract (SORT and JPDAF on the full clip).
"""
import os, sys, json, glob
import numpy as np

OUT = "outputs/report"
TRACKS_JSON = f"{OUT}/tracks_fullclip.json"
GT_DIR = glob.glob(os.path.join(os.environ.get("PYCASA_DATA", "pycasa_data"),
                                "sys-casa", "rawdata", "sub-HC004", "ses-01", "*_gt"))
CLOSE_PX = 14        # two hand-marked centres this close = the cells touch (a box is ~40 px)
INVOLVED_PX = 16     # a track passing this close to the collision point is part of the event
PAD = 40             # frames shown before and after the event
HIGHLIGHT_PX = 30    # tracks this close to the collision point are coloured in the pictures


# ----------------------------------------------------------------- ground truth
def load_gt():
    """{frame: (n,2) array of box centres in pixels}."""
    d = json.load(open(TRACKS_JSON))
    W, H = d["W"], d["H"]
    gt = {}
    for f in glob.glob(os.path.join(GT_DIR[0], "*_frame-*.txt")):
        fr = int(f.rsplit("-", 1)[1].split(".")[0])
        rows = np.loadtxt(f, ndmin=2)
        gt[fr] = rows[:, 1:3] * [W, H] if len(rows) else np.zeros((0, 2))
    return gt, d


def find_events(gt):
    """Group 'two centres are close' moments into events: (f0, f1, x, y)."""
    moments = []                                   # (frame, x, y) of every close pair
    for fr in sorted(gt):
        p = gt[fr]
        if len(p) < 2:
            continue
        dist = np.linalg.norm(p[:, None] - p[None], axis=2)
        np.fill_diagonal(dist, 1e9)
        for i, j in zip(*np.where(np.triu(dist < CLOSE_PX))):
            moments.append((fr, *(p[i] + p[j]) / 2))
    events = []                                    # merge moments that are consecutive in time and place
    for fr, x, y in moments:
        for ev in events:
            if fr - ev["f1"] <= 3 and np.hypot(x - ev["x"], y - ev["y"]) < 25:
                ev["f1"] = fr
                ev["x"], ev["y"] = (ev["x"] + x) / 2, (ev["y"] + y) / 2
                break
        else:
            events.append({"f0": fr, "f1": fr, "x": x, "y": y})
    return events


# ----------------------------------------------------------------- what each tracker did
def track_arrays(d, backend):
    out = {}
    for tid, pts in d[backend].items():
        a = np.array(sorted(pts), float)           # columns: frame, x, y
        out[tid] = a
    return out


def outcome(tracks, ev, N):
    """Which tracks took part, and did any of them start or stop at the collision?"""
    f0, f1, x, y = ev["f0"], ev["f1"], ev["x"], ev["y"]
    involved = []
    for tid, a in tracks.items():
        m = (a[:, 0] >= f0 - 2) & (a[:, 0] <= f1 + 2)
        if m.any() and np.min(np.hypot(a[m, 1] - x, a[m, 2] - y)) < INVOLVED_PX:
            involved.append(tid)
    if len(involved) < 2:
        return None                                # tracker never had two cells here
    broke = []
    for tid in involved:
        a = tracks[tid]
        first, last = a[0, 0], a[-1, 0]
        if first >= f0 - 5 or (last <= f1 + 5 and last < N - 1):
            broke.append(tid)
    return {"ids": involved, "broke": broke, "kept": not broke}


def find(write=True):
    gt, d = load_gt()
    N = d["N"]
    tr = {b: track_arrays(d, b) for b in ("sort", "jpdaf")}
    events = find_events(gt)
    rows, stats = [], {b: {"kept": 0, "broke": 0, "n": 0} for b in tr}
    for ev in events:
        if ev["f0"] < PAD or ev["f1"] > N - 1 - PAD:
            continue                               # need room to show before and after
        res = {b: outcome(tr[b], ev, N) for b in tr}
        if any(r is None for r in res.values()):
            continue
        for b, r in res.items():
            stats[b]["n"] += 1
            stats[b]["kept" if r["kept"] else "broke"] += 1
        rows.append({**{k: (round(v, 1) if isinstance(v, float) else v) for k, v in ev.items()}, **res})
    print(f"collision events with two tracked cells: {len(rows)}")
    for b in tr:
        s = stats[b]
        print(f"  {b:6s} kept both tracks through the collision: {s['kept']}/{s['n']}  "
              f"({100 * s['kept'] / max(s['n'], 1):.0f}%)")
    # demo event: JPDAF kept, SORT broke, both cells moving, nothing else nearby, not at the border
    def clean(r):
        if not (r["jpdaf"]["kept"] and not r["sort"]["kept"]):
            return -1
        if not (120 < r["x"] < d["W"] - 120 and 120 < r["y"] < d["H"] - 120):
            return -1
        moves = []
        for tid in r["jpdaf"]["ids"]:
            a = tr["jpdaf"][tid]
            m = (a[:, 0] >= r["f0"] - PAD) & (a[:, 0] <= r["f1"] + PAD)
            if m.sum() < 2 * PAD:
                return -1
            moves.append(np.linalg.norm(a[m][-1, 1:] - a[m][0, 1:]))
        if min(moves) < 35 or len(r["jpdaf"]["ids"]) != 2:
            return -1
        others = 0                                  # third cell within 60 px during the window?
        for fr in range(r["f0"] - PAD, r["f1"] + PAD + 1):
            p = gt.get(fr)
            if p is not None and len(p):
                others = max(others, int((np.hypot(p[:, 0] - r["x"], p[:, 1] - r["y"]) < 60).sum()))
        return -1 if others > 2 else min(moves) - 2 * (r["f1"] - r["f0"])
    def restart(r):
        """SORT: one track ends and another starts at the collision; JPDAF: two tracks, both kept."""
        if not (r["jpdaf"]["kept"] and len(r["jpdaf"]["ids"]) == 2 and not r["sort"]["kept"]):
            return -1
        if not (120 < r["x"] < d["W"] - 120 and 120 < r["y"] < d["H"] - 120):
            return -1
        ends = starts = 0
        for tid in r["sort"]["ids"]:
            a = tr["sort"][tid]
            ends += a[-1, 0] <= r["f1"] + 5 and a[-1, 0] < N - 1
            starts += a[0, 0] >= r["f0"] - 5
        if not (ends and starts):
            return -1
        moves = []
        for tid in r["jpdaf"]["ids"]:
            a = tr["jpdaf"][tid]
            m = (a[:, 0] >= r["f0"] - PAD) & (a[:, 0] <= r["f1"] + PAD)
            moves.append(np.linalg.norm(a[m][-1, 1:] - a[m][0, 1:]) if m.sum() > 1 else 0)
        return min(moves)
    for r in sorted(rows, key=restart, reverse=True)[:8]:
        if restart(r) > 0:
            print(f"  restart candidate f0={r['f0']} at ({r['x']:.0f},{r['y']:.0f}) "
                  f"sort ids {r['sort']['ids']} broke {r['sort']['broke']}  jpdaf {r['jpdaf']['ids']}  min move {restart(r):.0f}px")
    ranked = sorted(rows, key=clean, reverse=True)
    demo = ranked[0] if ranked and clean(ranked[0]) > 0 else None
    print("demo event:", demo)
    if write:
        json.dump({"close_px": CLOSE_PX, "events": rows, "stats": stats, "demo": demo},
                  open(f"{OUT}/13_collision.json", "w"), indent=1)
    return demo, d


# ----------------------------------------------------------------- drawing helpers
PALETTE = [(40, 165, 255), (255, 220, 80), (200, 80, 255), (80, 255, 120),   # BGR: orange, cyan,
           (60, 60, 255), (255, 120, 40), (0, 230, 230), (255, 255, 255)]     # violet, green, red, ...
CROP_HALF = 120      # pixels around the collision point
PANEL = 480          # rendered panel size
TITLE_H = 46


def _load_frames(first, last):
    """Frames first..last of the clip (inclusive) as an RGB array."""
    import pycasa as pc
    s = pc.io.load_default_data(initial_frame=first, final_frame=last, verbose=False)
    video = np.asarray(s.get_video()["original_video"])
    assert len(video) == last - first + 1, (len(video), first, last)
    return s, video


def _crop_box(ev, W, H):
    x0 = int(np.clip(ev["x"] - CROP_HALF, 0, W - 2 * CROP_HALF))
    y0 = int(np.clip(ev["y"] - CROP_HALF, 0, H - 2 * CROP_HALF))
    return x0, y0


def _draw_tracks(img, tracks, colours, f_start, f_now, x0, y0, zoom):
    """Trails of every track from f_start up to f_now, one colour per track ID."""
    import cv2
    for tid, a in tracks.items():
        m = (a[:, 0] >= f_start) & (a[:, 0] <= f_now)
        if not m.any():
            continue
        pts = ((a[m, 1:] - [x0, y0]) * zoom).astype(int)
        if not ((pts >= 0) & (pts < PANEL)).all(axis=1).any():
            continue
        col = colours.get(tid)
        if col is None:                                       # a bystander: thin grey, no label
            if len(pts) > 1:
                cv2.polylines(img, [pts], False, (150, 150, 150), 1, cv2.LINE_AA)
            continue
        if len(pts) > 1:
            cv2.polylines(img, [pts], False, col, 3, cv2.LINE_AA)
        if a[m][-1, 0] == f_now:                              # the track is alive right now
            cx, cy = pts[-1]
            cv2.circle(img, (cx, cy), 12, col, 2, cv2.LINE_AA)
            cv2.putText(img, "ID " + tid.lstrip("t"), (cx + 15, cy - 11), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, col, 2, cv2.LINE_AA)


def _panel(video, fi, tracks, colours, f_start, f_now, x0, y0, title):
    import cv2
    zoom = PANEL / (2 * CROP_HALF)
    img = cv2.cvtColor(video[fi], cv2.COLOR_RGB2BGR)[y0:y0 + 2 * CROP_HALF, x0:x0 + 2 * CROP_HALF]
    img = cv2.resize(img, (PANEL, PANEL), interpolation=cv2.INTER_CUBIC)
    _draw_tracks(img, tracks, colours, f_start, f_now, x0, y0, zoom)
    p = np.full((PANEL + TITLE_H, PANEL, 3), 255, np.uint8)
    p[TITLE_H:] = img
    cv2.putText(p, title, (10, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (30, 30, 30), 2, cv2.LINE_AA)
    return p


def render(ev, d, out_dir=OUT, tag="13_collision"):
    """Side-by-side GIF and before/during/after strip for one collision event."""
    import cv2, imageio.v2 as imageio
    f_start, f_end = ev["f0"] - PAD, ev["f1"] + PAD
    s, video = _load_frames(f_start, f_end)
    x0, y0 = _crop_box(ev, d["W"], d["H"])
    tr = {b: track_arrays(d, b) for b in ("sort", "jpdaf")}
    # colour every track that comes near the collision (a wider net than the statistics use,
    # so the passing cell is coloured too); order of appearance decides the colour
    colours = {b: {} for b in tr}
    for b in tr:
        near = []
        for tid, a in tr[b].items():
            m = (a[:, 0] >= ev["f0"] - 2) & (a[:, 0] <= ev["f1"] + 2)
            if m.any() and np.min(np.hypot(a[m, 1] - ev["x"], a[m, 2] - ev["y"])) < HIGHLIGHT_PX:
                near.append((a[0, 0], tid))
        for _, tid in sorted(near):
            colours[b][tid] = PALETTE[len(colours[b]) % len(PALETTE)]

    def both(f_now):
        panels = [_panel(video, f_now - f_start, tr[b], colours[b], f_start, f_now, x0, y0, name)
                  for b, name in (("sort", "SORT"), ("jpdaf", "JPDAF"))]
        gap = np.full((PANEL + TITLE_H, 26, 3), 255, np.uint8)
        return np.hstack([panels[0], gap, panels[1]])

    frames = []
    for f_now in range(f_start, f_end + 1, 2):
        img = both(f_now)
        bar = np.full((16, img.shape[1], 3), 255, np.uint8)
        cv2.rectangle(bar, (0, 5), (img.shape[1] - 1, 11), (225, 225, 225), -1)
        cv2.rectangle(bar, (0, 5), (int((img.shape[1] - 1) * (f_now - f_start) / (f_end - f_start)), 11),
                      (36, 138, 240), -1)
        frames.append(cv2.cvtColor(np.vstack([img, bar]), cv2.COLOR_BGR2RGB))
    gif = f"{out_dir}/{tag}_sort_vs_jpdaf.gif"
    imageio.mimsave(gif, frames, duration=[1 / 10] * (len(frames) - 1) + [2.5], loop=0, subrectangles=True)
    cv2.imwrite(gif.replace(".gif", ".png"), cv2.cvtColor(frames[-1], cv2.COLOR_RGB2BGR))

    # strip: before / during / after, SORT on top, JPDAF below
    mid = (ev["f0"] + ev["f1"]) // 2
    cols = [(f_start + 10, "before"), (mid, "touching"), (f_end, "after")]
    rows = []
    for b, name in (("sort", "SORT"), ("jpdaf", "JPDAF")):
        row = []
        for f_now, label in cols:
            p = _panel(video, f_now - f_start, tr[b], colours[b], f_start, f_now, x0, y0,
                       f"{name}  -  {label}  (frame {f_now})")
            row.append(p)
            row.append(np.full((PANEL + TITLE_H, 20, 3), 255, np.uint8))
        rows.append(np.hstack(row[:-1]))
        rows.append(np.full((20, rows[-1].shape[1], 3), 255, np.uint8))
    strip = np.vstack(rows[:-1])
    strip = cv2.resize(strip, None, fx=0.8, fy=0.8, interpolation=cv2.INTER_AREA)
    cv2.imwrite(f"{out_dir}/{tag}_strip.png", strip)
    print(f"  written: {gif} ({os.path.getsize(gif) / 1e6:.1f} MB, {len(frames)} frames), {tag}_strip.png")


# ----------------------------------------------------------------- detectors on the same 100 frames
DETECTORS = {
    "yolov5": ("casa.detection.yolo(yolo_model='yolov5')", lambda s: s.detection.yolo(yolo_model="yolov5", show_progress=False, verbose=False)),
    "yolo26": ("casa.detection.yolo(yolo_model='yolo26')", lambda s: s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)),
    "moving_cells": ("casa.detection.detect_moving_cells()", lambda s: s.detection.detect_moving_cells(show_progress=False, verbose=False)),
    "digital_washing": ("casa.detection.digital_washing()", lambda s: s.detection.digital_washing(show_progress=False, verbose=False)),
    "urbano": ("casa.detection.urbano_detection()", lambda s: s.detection.urbano_detection(show_progress=False, verbose=False)),
}
DET_FRAMES = 99            # frames 0..99
VIS_FIRST, VIS_LAST = 20, 79   # the motion-based detectors need 20 warm-up frames


def _rows_px(rows, W, H):
    out = []
    for r in rows or []:
        v = [float(x) for x in np.asarray(r).ravel()[1:5]]      # column 0 is the class label
        if len(v) == 4:
            out.append([v[0] * W, v[1] * H, v[2] * W, v[3] * H] if max(v) <= 1.5 else v)
    return out


def detect(name):
    """One detector in a fresh process: score on frames 0..99, keep boxes of frames 20..79."""
    import pycasa as pc, time
    s = pc.io.load_default_data(final_frame=DET_FRAMES, verbose=False)
    W, H = s.get_video()["original_video"].shape[2], s.get_video()["original_video"].shape[1]
    t = time.time()
    DETECTORS[name][1](s)
    secs = time.time() - t
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    det = s.get_detections()
    det = det[next(iter(det))] if isinstance(next(iter(det.values())), dict) else det
    boxes = {f: _rows_px(det.get(str(f), det.get(f)), W, H) for f in range(VIS_FIRST, VIS_LAST + 1)}
    gt = {f: _rows_px(s.get_groundtruth().get(str(f)), W, H) for f in range(VIS_FIRST, VIS_LAST + 1)}
    json.dump({"name": name, "call": DETECTORS[name][0], "seconds": round(secs, 1),
               "assessment": {k: a[k] for k in ("tp", "fp", "fn", "precision", "recall", "F1", "evaluated_frames")},
               "boxes": boxes, "gt": gt},
              open(f"{OUT}/14_det_{name}.json", "w"))
    print(f"  {name:16s} F1={a['F1']:.2f}  P={a['precision']:.1f}  R={a['recall']:.1f}  "
          f"frames={a['evaluated_frames']}  {secs:.0f}s")


def detectors():
    """Run every detector (each in its own process), then draw the comparison."""
    import subprocess, cv2, imageio.v2 as imageio
    for name in DETECTORS:
        if not os.path.exists(f"{OUT}/14_det_{name}.json"):
            print(f"running {name} ...", flush=True)
            subprocess.run([sys.executable, __file__, "detect", name], check=True)
    res = {n: json.load(open(f"{OUT}/14_det_{n}.json")) for n in DETECTORS}
    json.dump({n: {k: v for k, v in r.items() if k not in ("boxes", "gt")} for n, r in res.items()},
              open(f"{OUT}/14_detectors.json", "w"), indent=1)

    s, video = _load_frames(VIS_FIRST, VIS_LAST)
    RX, RY, RW, RH = 330, 300, 560, 420            # a busy region of the frame
    SCALE = 540 / RW
    GREEN, RED = (0, 200, 0), (40, 40, 255)

    def panel(name, f, title):
        img = cv2.cvtColor(video[f - VIS_FIRST], cv2.COLOR_RGB2BGR)[RY:RY + RH, RX:RX + RW]
        img = cv2.resize(img, (int(RW * SCALE), int(RH * SCALE)), interpolation=cv2.INTER_CUBIC)
        for rows, col in ((res[name]["gt"][str(f)], GREEN), (res[name]["boxes"][str(f)], RED)):
            for cx, cy, w, h in rows:
                p1 = (int((cx - w / 2 - RX) * SCALE), int((cy - h / 2 - RY) * SCALE))
                p2 = (int((cx + w / 2 - RX) * SCALE), int((cy + h / 2 - RY) * SCALE))
                cv2.rectangle(img, p1, p2, col, 2)
        p = np.full((img.shape[0] + TITLE_H, img.shape[1], 3), 255, np.uint8)
        p[TITLE_H:] = img
        cv2.putText(p, title, (10, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (30, 30, 30), 2, cv2.LINE_AA)
        return p

    labels = {"yolov5": "YOLOv5", "yolo26": "YOLO26", "moving_cells": "Moving cells",
              "digital_washing": "Digital washing", "urbano": "Urbano"}
    frames = []
    for f in range(VIS_FIRST, VIS_LAST + 1, 2):
        gap = np.full((int(RH * SCALE) + TITLE_H, 26, 3), 255, np.uint8)
        frames.append(cv2.cvtColor(np.hstack([panel("yolov5", f, "YOLOv5"), gap, panel("yolo26", f, "YOLO26")]),
                                   cv2.COLOR_BGR2RGB))
    gif = f"{OUT}/14_yolov5_vs_yolo26.gif"
    imageio.mimsave(gif, frames, duration=[1 / 8] * (len(frames) - 1) + [2.0], loop=0, subrectangles=True)
    cv2.imwrite(gif.replace(".gif", ".png"), cv2.cvtColor(frames[len(frames) // 2], cv2.COLOR_RGB2BGR))

    # all five detectors, animated, 3 x 2 grid (last tile is the legend)
    gap_v = np.full((int(RH * SCALE) + TITLE_H, 20, 3), 255, np.uint8)
    legend = np.full_like(panel("yolov5", VIS_FIRST, ""), 255)
    cv2.rectangle(legend, (30, 90), (60, 120), GREEN, 2)
    cv2.putText(legend, "marked by a person", (75, 113), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2, cv2.LINE_AA)
    cv2.rectangle(legend, (30, 150), (60, 180), RED, 2)
    cv2.putText(legend, "found by the software", (75, 173), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2, cv2.LINE_AA)
    grid_frames = []
    for f in range(VIS_FIRST, VIS_LAST + 1, 3):
        tiles = [panel(n, f, labels[n]) for n in DETECTORS]
        row1 = np.hstack([tiles[0], gap_v, tiles[1], gap_v, tiles[2]])
        row2 = np.hstack([tiles[3], gap_v, tiles[4], gap_v, legend])
        grid = np.vstack([row1, np.full((20, row1.shape[1], 3), 255, np.uint8), row2])
        grid = cv2.resize(grid, None, fx=0.7, fy=0.7, interpolation=cv2.INTER_AREA)
        grid_frames.append(cv2.cvtColor(grid, cv2.COLOR_BGR2RGB))
    gif2 = f"{OUT}/14_all_detectors.gif"
    imageio.mimsave(gif2, grid_frames, duration=[1 / 6] * (len(grid_frames) - 1) + [2.0], loop=0, subrectangles=True)
    cv2.imwrite(gif2.replace(".gif", ".png"), cv2.cvtColor(grid_frames[len(grid_frames) // 2], cv2.COLOR_RGB2BGR))
    print(f"  written: {gif} ({os.path.getsize(gif) / 1e6:.1f} MB), {gif2} ({os.path.getsize(gif2) / 1e6:.1f} MB), 14_detectors.json")


# ----------------------------------------------------------------- the same detectors on the whole clip
STEP8 = "outputs/step8_full_clip.json"     # YOLOv5, YOLO26 and moving cells were already run on all 899 frames


def detect_full(name):
    """Urbano / digital washing on the full clip, one per process.

    Same memory trick as make_tracker_sidebyside.extract: the 3.3 GB video block
    is redirected to a disk-backed memmap while it is loaded, because it does not
    fit in RAM as one piece. Detection reads frames one at a time, so this is slow
    but works.
    """
    import pycasa as pc, tempfile, time
    tmp_path = os.path.join(tempfile.gettempdir(), f"pycasa_video_{name}.memmap")
    real_zeros = np.zeros

    def zeros_memmap(shape, dtype=float, order="C"):
        if isinstance(shape, tuple) and len(shape) == 4 and np.prod(shape) > 5e8:
            mm = np.memmap(tmp_path, dtype=dtype, mode="w+", shape=shape)
            mm[:] = 0
            return mm
        return real_zeros(shape, dtype=dtype, order=order)

    np.zeros = zeros_memmap
    try:
        s = pc.io.load_default_data(final_frame=None, verbose=False)
    finally:
        np.zeros = real_zeros
    n = s.get_video()["number_frame_used"]
    t = time.time()
    DETECTORS[name][1](s)
    secs = time.time() - t
    s.assessment.evaluate_detections()
    a = s.get_assessment()["detection"]
    json.dump({"name": name, "call": DETECTORS[name][0], "seconds": round(secs, 1), "frames_loaded": int(n),
               "assessment": {k: a[k] for k in ("tp", "fp", "fn", "precision", "recall", "F1", "evaluated_frames")}},
              open(f"{OUT}/14_detfull_{name}.json", "w"))
    print(f"  {name:16s} full clip: F1={a['F1']:.2f}  P={a['precision']:.1f}  R={a['recall']:.1f}  "
          f"frames={a['evaluated_frames']}  {secs:.0f}s", flush=True)
    try:
        os.remove(tmp_path)
    except OSError:
        pass


def full():
    """Collect the full-clip scores of all five detectors into 14_detectors_full.json."""
    import subprocess
    out = {}
    step8 = json.load(open(STEP8))
    for name in ("yolov5", "yolo26", "moving_cells"):
        out[name] = {"name": name, "call": DETECTORS[name][0], "source": "step8_full_clip.py",
                     "frames_loaded": step8[name]["frames_loaded"], "assessment": step8[name]["detection"]}
    for name in ("urbano", "digital_washing"):
        f = f"{OUT}/14_detfull_{name}.json"
        if not os.path.exists(f):
            print(f"running {name} on the full clip ...", flush=True)
            subprocess.run([sys.executable, __file__, "detect_full", name], check=True)
        out[name] = json.load(open(f))
    json.dump(out, open(f"{OUT}/14_detectors_full.json", "w"), indent=1)
    for n, r in out.items():
        a = r["assessment"]
        print(f"  {n:16s} F1={a['F1']:.2f}  P={a['precision']:.1f}  R={a['recall']:.1f}  frames={a['evaluated_frames']}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "find"
    if mode == "find":
        find()
    elif mode == "review":                        # strips for several candidates, to pick one by eye
        demo, d = find(write=False)
        J = json.load(open(f"{OUT}/13_collision.json"))
        out_dir = sys.argv[2]
        for f0 in map(int, sys.argv[3:]):
            ev = next(e for e in J["events"] if e["f0"] == f0)
            render(ev, d, out_dir=out_dir, tag=f"cand_{f0}")
    elif mode == "render":                        # the chosen event: by f0, else the auto-picked demo
        J = json.load(open(f"{OUT}/13_collision.json"))
        d = json.load(open(TRACKS_JSON))
        ev = next(e for e in J["events"] if e["f0"] == int(sys.argv[2])) if len(sys.argv) > 2 else J["demo"]
        tag = sys.argv[3] if len(sys.argv) > 3 else "13_collision"
        J["demo" if tag == "13_collision" else tag] = ev
        json.dump(J, open(f"{OUT}/13_collision.json", "w"), indent=1)
        render(ev, d, tag=tag)
    elif mode == "detect":
        detect(sys.argv[2])
    elif mode == "detectors":
        detectors()
    elif mode == "detect_full":
        detect_full(sys.argv[2])
    elif mode == "full":
        full()
