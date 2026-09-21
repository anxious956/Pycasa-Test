"""Rapor icin GIF ve PNG uretir.

pycasa'nin timelapse'i interaktif pencere aciyor, dosyaya kaydetmiyor.
Bu script ayni overlay'leri (GT kutulari, detection kutulari, track yorungeleri,
legend) cizip outputs/report/ altina GIF + kapak PNG olarak yazar.

Kullanim:
    python scripts/make_report_gifs.py              # hepsini uret
    python scripts/make_report_gifs.py full         # sadece bir tanesi

Uretilenler:
    01_gt_only          GT kutulari (adim 2)
    02_gt_vs_yolo26     GT + YOLO26 kutulari yan yana (adim 3)
    03_sort_gt          GT uzerinde SORT yorungeleri (adim 5)
    04_jpdaf_gt         GT uzerinde JPDAF yorungeleri (adim 5)
    05_full             GT + YOLO26 kutulari + iki track seti (timelapse'in tam hali)
"""
import os, sys
import numpy as np
import cv2
import imageio.v2 as imageio
import pycasa as pc

OUT = "outputs/report"
os.makedirs(OUT, exist_ok=True)

FRAMES = 60          # 61 frame
SCALE = 0.45         # 1280x1024 -> 576x460
STRIDE = 2           # her 2. frame -> 31 kare, GIF boyutu yarilanir
TRAIL = 25           # yorunge kuyrugunun kac frame geriye uzandigi

# BGR (cv2) renkleri
YESIL   = (0, 255, 0)        # groundtruth kutulari
KIRMIZI = (60, 60, 255)      # detection kutulari
MAVI    = (255, 200, 80)     # GT uzerinde track
TURUNCU = (40, 160, 255)     # detection uzerinde track


def _kutular(satirlar, W, H):
    """YOLO satirlarini (cls cx cy w h, normalize) piksel kutusuna cevir."""
    out = []
    for r in satirlar or []:
        v = [float(x) for x in np.asarray(r).ravel()[:5]]
        if len(v) < 5:
            continue
        _, cx, cy, w, h = v
        if max(cx, cy, w, h) <= 1.5:
            cx, cy, w, h = cx * W, cy * H, w * W, h * H
        out.append((int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2)))
    return out


def _izler(tracks, W, H):
    """{track_id: {frame: [x, y]}} -> {frame: [(x, y), ...]}"""
    per_frame = {}
    for pts in (tracks or {}).values():
        for f, xy in pts.items():
            x, y = float(xy[0]), float(xy[1])
            if max(x, y) <= 1.5:
                x, y = x * W, y * H
            per_frame.setdefault(int(f), []).append((x, y))
    return per_frame


def _legend(img, girdiler, y0=42):
    """Renk aciklamasi; y0 baslik cubugunun altindan basliyor."""
    pad, sat, gen = 8, 20, 250
    yuk = pad * 2 + sat * len(girdiler)
    x0 = img.shape[1] - gen - 10
    kapak = img[y0:y0 + yuk, x0:x0 + gen].copy()
    cv2.rectangle(img, (x0, y0), (x0 + gen, y0 + yuk), (25, 25, 25), -1)
    cv2.addWeighted(kapak, 0.25, img[y0:y0 + yuk, x0:x0 + gen], 0.75, 0,
                    img[y0:y0 + yuk, x0:x0 + gen])
    for i, (etiket, renk, tip) in enumerate(girdiler):
        y = y0 + pad + sat * i + 13
        if tip == "kutu":
            cv2.rectangle(img, (x0 + pad, y - 9), (x0 + pad + 14, y + 3), renk, 2)
        else:
            cv2.line(img, (x0 + pad, y - 3), (x0 + pad + 14, y - 3), renk, 2)
        cv2.putText(img, etiket, (x0 + pad + 22, y + 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (245, 245, 245), 1, cv2.LINE_AA)


def render(session, ad, baslik, *, gt=True, det=False, gt_track=None, det_track=None,
           det_label="yolo26", stride=None):
    """Tek bir GIF + kapak PNG uret."""
    video = np.asarray(session.get_video()["original_video"])
    N, H, W = video.shape[:3]
    gt_box = session.get_groundtruth() if gt else {}
    det_box = session.get_detections() if det else {}
    gt_iz = _izler(gt_track, W, H)
    det_iz = _izler(det_track, W, H)

    girdiler = []
    if gt:        girdiler.append(("groundtruth", YESIL, "kutu"))
    if det:       girdiler.append((f"detections ({det_label})", KIRMIZI, "kutu"))
    if gt_track:  girdiler.append(("tracks (groundtruth)", MAVI, "cizgi"))
    if det_track: girdiler.append((f"tracks ({det_label})", TURUNCU, "cizgi"))

    kareler = []
    for i in range(0, N, stride or STRIDE):
        img = cv2.cvtColor(video[i], cv2.COLOR_RGB2BGR).copy()
        for f in range(max(0, i - TRAIL), i + 1):
            kalinlik = 2 if f < i - 6 else 3
            for x, y in gt_iz.get(f, []):
                cv2.circle(img, (int(x), int(y)), kalinlik, MAVI, -1)
            for x, y in det_iz.get(f, []):
                cv2.circle(img, (int(x), int(y)), kalinlik, TURUNCU, -1)
        for b in _kutular(det_box.get(str(i)), W, H):
            cv2.rectangle(img, b[:2], b[2:], KIRMIZI, 2)
        for b in _kutular(gt_box.get(str(i)), W, H):
            cv2.rectangle(img, b[:2], b[2:], YESIL, 2)
        img = cv2.resize(img, (int(W * SCALE), int(H * SCALE)), interpolation=cv2.INTER_AREA)
        cv2.rectangle(img, (0, 0), (img.shape[1], 34), (20, 20, 20), -1)
        cv2.putText(img, f"{baslik}  |  frame {i}", (10, 23),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 230, 255), 1, cv2.LINE_AA)
        if girdiler:
            _legend(img, girdiler)
        kareler.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    gif = f"{OUT}/{ad}.gif"
    imageio.mimsave(gif, kareler, duration=1 / 12, loop=0, subrectangles=True)
    png = f"{OUT}/{ad}.png"
    cv2.imwrite(png, cv2.cvtColor(kareler[len(kareler) // 2], cv2.COLOR_RGB2BGR))
    mb = os.path.getsize(gif) / 1e6
    print(f"  {gif}  ({len(kareler)} kare, {mb:.1f} MB)")
    print(f"  {png}")


def _yeni():
    return pc.io.load_default_data(final_frame=FRAMES, verbose=False)


def yap_gt_only():
    print("01_gt_only: sadece GT kutulari")
    render(_yeni(), "01_gt_only", "Groundtruth detections")


def yap_gt_vs_yolo26():
    print("02_gt_vs_yolo26: GT + YOLO26 kutulari")
    s = _yeni(); s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    render(s, "02_gt_vs_yolo26", "GT (green) vs YOLO26 (red)", det=True)


def yap_sort_gt():
    print("03_sort_gt: GT uzerinde SORT")
    s = _yeni(); s.tracking.sort(show_progress=False, verbose=False)
    render(s, "03_sort_gt", "SORT on groundtruth",
           gt_track=s.get_tracks()["sort"]["groundtruth"])


def yap_jpdaf_gt():
    print("04_jpdaf_gt: GT uzerinde JPDAF")
    s = _yeni(); s.tracking.jpdaf(show_progress=False, verbose=False)
    render(s, "04_jpdaf_gt", "JPDAF on groundtruth",
           gt_track=s.get_tracks()["jpdaf"]["groundtruth"])


def yap_full():
    print("05_full: GT + YOLO26 kutulari + iki track seti")
    s = _yeni()
    s.detection.yolo(yolo_model="yolo26", show_progress=False, verbose=False)
    s.tracking.sort(show_progress=False, verbose=False)
    tr = s.get_tracks()["sort"]
    render(s, "05_full", "GT + YOLO26 + SORT tracks", det=True,
           gt_track=tr.get("groundtruth"), det_track=tr.get("yolo26"))


HEPSI = {"gt": yap_gt_only, "det": yap_gt_vs_yolo26, "sort": yap_sort_gt,
         "jpdaf": yap_jpdaf_gt, "full": yap_full}

if __name__ == "__main__":
    secim = sys.argv[1:] or list(HEPSI)
    for ad in secim:
        HEPSI[ad]()
    print("\nBitti ->", os.path.abspath(OUT))
