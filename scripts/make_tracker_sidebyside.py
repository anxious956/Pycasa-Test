"""For slide 9: a side-by-side animation of SORT and JPDAF trajectories ACCUMULATING.

The existing static figure shows all tracks at once. The animated version shows
the trajectories building up over time, which makes it visible that SORT's tracks
break and restart while JPDAF's keep going.

Two stages (kept separate for memory reasons):
  1) extract : run SORT + JPDAF on the full clip, write the tracks and one
               background frame to disk (the video is not kept in memory)
  2) render  : build the side-by-side GIF from the tracks on disk

    python scripts/make_tracker_sidebyside.py extract
    python scripts/make_tracker_sidebyside.py render
    python scripts/make_tracker_sidebyside.py            # both
"""
import os, sys, json, gc

TRACKS_JSON = "outputs/report/tracks_fullclip.json"
BG_PNG = "outputs/report/tracks_background.png"
OUT_GIF = "outputs/report/09_sort_vs_jpdaf.gif"
FRAME_COUNT = 26    # number of GIF frames; each one shows every track up to that point
PANEL_W = 540       # width of each panel (pixels); kept modest for the GIF size


def extract():
    """Run SORT + JPDAF on the full clip and write the tracks to disk.

    Memory trick: pycasa allocates the video as a single np.zeros block (901
    frames = 3.3 GB) which usually does not fit in RAM. Tracking never touches
    the pixels, it only uses the detections. So for the duration of the LOAD we
    redirect np.zeros to a disk-backed np.memmap; the video lives on disk rather
    than in RAM.
    """
    import numpy as np, cv2, tempfile, pycasa as pc

    tmp_path = os.path.join(tempfile.gettempdir(), "pycasa_video.memmap")
    real_zeros = np.zeros

    def zeros_memmap(shape, dtype=float, order="C"):
        # only intercept the huge video array, leave every other allocation alone
        if isinstance(shape, tuple) and len(shape) == 4 and np.prod(shape) > 5e8:
            print(f"  moving video to disk: {shape} -> {tmp_path}", flush=True)
            mm = np.memmap(tmp_path, dtype=dtype, mode="w+", shape=shape)
            mm[:] = 0
            return mm
        return real_zeros(shape, dtype=dtype, order=order)

    np.zeros = zeros_memmap
    try:
        s = pc.io.load_default_data(final_frame=None)
    finally:
        np.zeros = real_zeros

    video = s.get_video()["original_video"]
    N, H, W = video.shape[:3]
    print(f"  frames loaded: {N}")
    cv2.imwrite(BG_PNG, cv2.cvtColor(np.ascontiguousarray(video[0]), cv2.COLOR_RGB2BGR))

    out_data = {"N": int(N), "W": int(W), "H": int(H)}
    for backend in ("sort", "jpdaf"):
        getattr(s.tracking, backend)()                              # no detections -> GT
        tr = s.get_tracks()[backend]["groundtruth"]
        out_data[backend] = {tid: [[int(f), float(xy[0]), float(xy[1])]
                                   for f, xy in pts.items()]
                             for tid, pts in tr.items()}
        print(f"  {backend}: {len(tr)} tracks")
    del video, s
    gc.collect()
    json.dump(out_data, open(TRACKS_JSON, "w"), separators=(",", ":"))
    print(f"  written: {TRACKS_JSON} ({os.path.getsize(TRACKS_JSON)/1e6:.1f} MB), background: {BG_PNG}")
    try:
        os.remove(tmp_path)
    except OSError:
        pass


def render():
    """Build the accumulating side-by-side GIF from the tracks on disk.

    Instead of plotting points we connect consecutive positions with LINES; that
    matches the look of the static figure and keeps the trajectories
    distinguishable. Drawn as points, after 900 frames everything merges into a
    single blob.
    """
    import numpy as np, cv2, imageio.v2 as imageio
    d = json.load(open(TRACKS_JSON))
    N, W, H = d["N"], d["W"], d["H"]
    scale = PANEL_W / W
    panelH, panelW = int(H * scale), PANEL_W
    bg = cv2.imread(BG_PNG)
    bg = cv2.resize(bg, (panelW, panelH), interpolation=cv2.INTER_AREA)
    bg = (bg * 0.42).astype(np.uint8)

    COLOURS = {"sort": (255, 130, 40), "jpdaf": (40, 165, 255)}       # BGR: blue / orange

    # per backend: line segments ending at frame f -> {f: [((x1,y1),(x2,y2)), ...]}
    segments = {}
    for backend in ("sort", "jpdaf"):
        per = {}
        for pts in d[backend].values():
            pts = sorted(pts, key=lambda r: r[0])
            for (f1, x1, y1), (f2, x2, y2) in zip(pts, pts[1:]):
                if f2 - f1 > 3:                    # do not bridge across gaps
                    continue
                per.setdefault(int(f2), []).append(
                    ((int(x1 * scale), int(y1 * scale)), (int(x2 * scale), int(y2 * scale))))
        segments[backend] = per

    TITLE_H = 46
    frames = []
    cutoffs = [int(N * (i + 1) / FRAME_COUNT) for i in range(FRAME_COUNT)]
    canvas = {b: bg.copy() for b in ("sort", "jpdaf")}
    before = 0
    for step, cutoff in enumerate(cutoffs):
        for b in ("sort", "jpdaf"):
            for f in range(before, cutoff):
                for p1, p2 in segments[b].get(f, []):
                    cv2.line(canvas[b], p1, p2, COLOURS[b], 1, cv2.LINE_AA)
        before = cutoff

        panel = []
        for b, name in (("sort", f"SORT on GT  -  {len(d['sort'])} tracks"),
                        ("jpdaf", f"JPDAF on GT  -  {len(d['jpdaf'])} tracks")):
            p = np.full((panelH + TITLE_H, panelW, 3), 255, np.uint8)
            p[TITLE_H:] = canvas[b]
            cv2.putText(p, name, (10, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (30, 30, 30), 2, cv2.LINE_AA)
            panel.append(p)
        gap = np.full((panelH + TITLE_H, 26, 3), 255, np.uint8)
        img = np.hstack([panel[0], gap, panel[1]])
        cv2.putText(img, f"frame {cutoff} / {N}", (img.shape[1] - 205, 31),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (120, 120, 120), 1, cv2.LINE_AA)
        frames.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if step % 10 == 0:
            print(f"  frame {step + 1}/{FRAME_COUNT}", flush=True)

    durations = [1 / 12] * (FRAME_COUNT - 1) + [2.5]                 # hold on the last frame
    imageio.mimsave(OUT_GIF, frames, duration=durations, loop=0, subrectangles=True)
    cover = OUT_GIF.replace(".gif", ".png")
    cv2.imwrite(cover, cv2.cvtColor(frames[-1], cv2.COLOR_RGB2BGR))
    print(f"  written: {OUT_GIF} ({os.path.getsize(OUT_GIF)/1e6:.1f} MB, "
          f"{frames[0].shape[1]}x{frames[0].shape[0]}, ratio "
          f"{frames[0].shape[1]/frames[0].shape[0]:.2f})")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "hepsi"
    if mode in ("extract", "hepsi"):
        extract()
    if mode in ("render", "hepsi"):
        render()
