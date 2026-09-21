"""Helper: timelapse ciktisini dosyaya kaydet (GT / detection / track overlay).
pycasa'nin timelapse'i interaktif pencere acar; repo'ya koymak icin
ayni overlay'leri Agg backend ile GIF + PNG olarak render ediyoruz."""
import sys, numpy as np, cv2, imageio.v2 as imageio

def _boxes(frame_rows, W, H):
    out = []
    for r in frame_rows or []:
        vals = [float(x) for x in np.asarray(r).ravel()]
        if len(vals) == 5: _, cx, cy, w, h = vals
        elif len(vals) >= 6: _, cx, cy, w, h = vals[:5]
        else: continue
        if max(cx, cy, w, h) <= 1.5:  # normalized
            cx, cy, w, h = cx*W, cy*H, w*W, h*H
        out.append((int(cx-w/2), int(cy-h/2), int(cx+w/2), int(cy+h/2)))
    return out

def render(session, out_path, show_gt=True, det_source=None, track_source=None,
           scale=0.5, stride=1, max_frames=None, title=""):
    video = np.asarray(session.get_video()["original_video"])
    N, H, W = video.shape[:3]
    gt = session.get_groundtruth() if show_gt else {}
    det = session.get_detections() if det_source else {}
    # tracks: session.get_tracks()[backend][source][track_id] = {frame_index: [x, y]}
    trails = {}
    if track_source:
        backend, source = track_source
        tracks = session.get_tracks().get(backend, {}).get(source, {})
        for tid, pts in tracks.items():
            for f, xy in pts.items():
                x, y = float(xy[0]), float(xy[1])
                if max(x, y) <= 1.5: x, y = x*W, y*H
                trails.setdefault(int(f), []).append((tid, x, y))
    frames_out = []
    idx = range(0, N if max_frames is None else min(N, max_frames), stride)
    for i in idx:
        img = video[i].copy()
        for b in _boxes(gt.get(str(i)), W, H):
            cv2.rectangle(img, b[:2], b[2:], (0, 255, 0), 2)      # lime = GT
        for b in _boxes(det.get(str(i)), W, H):
            cv2.rectangle(img, b[:2], b[2:], (255, 77, 77), 2)    # red = detection
        if trails:
            # draw trajectory tails for last 30 frames
            colors = {}
            for f in range(max(0, i-30), i+1):  # son 30 frame'lik iz
                for tid, x, y in trails.get(f, []):
                    c = colors.setdefault(tid, tuple(int(v) for v in np.random.RandomState(hash(str(tid)) % 2**31).randint(60, 255, 3)))
                    cv2.circle(img, (int(x), int(y)), 3, c, -1)
        cv2.putText(img, f"{title} frame {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        if scale != 1: img = cv2.resize(img, (int(W*scale), int(H*scale)))
        frames_out.append(img)
    if out_path.endswith(".gif"):
        imageio.mimsave(out_path, frames_out, duration=1/30, loop=0)
        cv2.imwrite(out_path.rsplit(".", 1)[0] + "_frame0.png", cv2.cvtColor(frames_out[0], cv2.COLOR_RGB2BGR))
    else:
        cv2.imwrite(out_path, cv2.cvtColor(frames_out[0], cv2.COLOR_RGB2BGR))
    print("saved", out_path, len(frames_out), "frames")

if __name__ == "__main__":
    import pycasa as pc
    s = pc.io.load_default_data()
    render(s, "outputs/step2_timelapse_gt_only.gif", show_gt=True, title="GT only", scale=0.4, stride=2)
