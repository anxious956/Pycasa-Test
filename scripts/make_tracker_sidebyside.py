"""Slayt 9 icin: SORT ve JPDAF yorungelerinin yan yana BIRIKEN animasyonu.

Mevcut statik figur tum track'leri birden gosteriyor. Animasyonlu hali
yorungelerin zamanla BIRIKMESINI gosterir; SORT'un track'lerinin kopup yeniden
basladigi, JPDAF'inkilerin ise surdugu boylece gozle gorulur.

Iki asama (bellek icin ayri):
  1) extract : tam klipte SORT + JPDAF calistir, track'leri ve bir arka plan
               karesini diske yaz (video bellekte tutulmaz)
  2) render  : diskteki track'lerden yan yana GIF uret

    python scripts/make_tracker_sidebyside.py extract
    python scripts/make_tracker_sidebyside.py render
    python scripts/make_tracker_sidebyside.py            # ikisi de
"""
import os, sys, json, gc

VERI = "outputs/report/tracks_fullclip.json"
ARKA = "outputs/report/tracks_background.png"
CIKTI = "outputs/report/09_sort_vs_jpdaf.gif"
KARE = 26           # GIF kare sayisi; her kare o ana kadarki tum izleri gosterir
PANEL_EN = 540      # her panelin genisligi (piksel); GIF boyutu icin olculu


def extract():
    """Tam klipte SORT + JPDAF calistir, track'leri diske yaz.

    Bellek hilesi: pycasa videoyu tek parca np.zeros ile aliyor (901 frame =
    3.3 GB) ve bu blok cogu zaman RAM'e sigmiyor. Tracking aslinda piksellere
    dokunmuyor, sadece detection'lari kullaniyor. Bu yuzden YUKLEME suresince
    np.zeros'u gecici olarak disk destekli np.memmap'e yonlendiriyoruz; video
    diskte duruyor, RAM'de degil.
    """
    import numpy as np, cv2, tempfile, pycasa as pc

    gecici = os.path.join(tempfile.gettempdir(), "pycasa_video.memmap")
    gercek_zeros = np.zeros

    def zeros_memmap(shape, dtype=float, order="C"):
        # sadece dev video dizisini yakala, digerlerini normal birak
        if isinstance(shape, tuple) and len(shape) == 4 and np.prod(shape) > 5e8:
            print(f"  video diske aliniyor: {shape} -> {gecici}", flush=True)
            mm = np.memmap(gecici, dtype=dtype, mode="w+", shape=shape)
            mm[:] = 0
            return mm
        return gercek_zeros(shape, dtype=dtype, order=order)

    np.zeros = zeros_memmap
    try:
        s = pc.io.load_default_data(final_frame=None)
    finally:
        np.zeros = gercek_zeros

    video = s.get_video()["original_video"]
    N, H, W = video.shape[:3]
    print(f"  yuklenen frame: {N}")
    cv2.imwrite(ARKA, cv2.cvtColor(np.ascontiguousarray(video[0]), cv2.COLOR_RGB2BGR))

    cikti = {"N": int(N), "W": int(W), "H": int(H)}
    for backend in ("sort", "jpdaf"):
        getattr(s.tracking, backend)()                              # detection yok -> GT
        tr = s.get_tracks()[backend]["groundtruth"]
        cikti[backend] = {tid: [[int(f), float(xy[0]), float(xy[1])]
                                for f, xy in pts.items()]
                          for tid, pts in tr.items()}
        print(f"  {backend}: {len(tr)} track")
    del video, s
    gc.collect()
    json.dump(cikti, open(VERI, "w"), separators=(",", ":"))
    print(f"  yazildi: {VERI} ({os.path.getsize(VERI)/1e6:.1f} MB), arka plan: {ARKA}")
    try:
        os.remove(gecici)
    except OSError:
        pass


def render():
    """Diskteki track'lerden yan yana biriken GIF uret.

    Noktalar yerine ardisik konumlari CIZGI ile baglıyoruz; statik figurun
    gorunumu boyle ve yorungeler ayirt edilebilir kaliyor. Noktayla cizilince
    900 frame'den sonra her sey tek bir kutleye donusuyor.
    """
    import numpy as np, cv2, imageio.v2 as imageio
    d = json.load(open(VERI))
    N, W, H = d["N"], d["W"], d["H"]
    olcek = PANEL_EN / W
    ph, pw = int(H * olcek), PANEL_EN
    arka = cv2.imread(ARKA)
    arka = cv2.resize(arka, (pw, ph), interpolation=cv2.INTER_AREA)
    arka = (arka * 0.42).astype(np.uint8)

    RENK = {"sort": (255, 130, 40), "jpdaf": (40, 165, 255)}       # BGR: mavi / turuncu

    # her backend icin: son karesi f olan cizgi parcalari -> {f: [((x1,y1),(x2,y2)), ...]}
    parcalar = {}
    for backend in ("sort", "jpdaf"):
        per = {}
        for pts in d[backend].values():
            pts = sorted(pts, key=lambda r: r[0])
            for (f1, x1, y1), (f2, x2, y2) in zip(pts, pts[1:]):
                if f2 - f1 > 3:                    # kopuk yerleri birlestirme
                    continue
                per.setdefault(int(f2), []).append(
                    ((int(x1 * olcek), int(y1 * olcek)), (int(x2 * olcek), int(y2 * olcek))))
        parcalar[backend] = per

    BASLIK = 46
    kareler = []
    sinirlar = [int(N * (i + 1) / KARE) for i in range(KARE)]
    tuval = {b: arka.copy() for b in ("sort", "jpdaf")}
    onceki = 0
    for adim, sinir in enumerate(sinirlar):
        for b in ("sort", "jpdaf"):
            for f in range(onceki, sinir):
                for p1, p2 in parcalar[b].get(f, []):
                    cv2.line(tuval[b], p1, p2, RENK[b], 1, cv2.LINE_AA)
        onceki = sinir

        panel = []
        for b, ad in (("sort", f"SORT on GT  -  {len(d['sort'])} tracks"),
                      ("jpdaf", f"JPDAF on GT  -  {len(d['jpdaf'])} tracks")):
            p = np.full((ph + BASLIK, pw, 3), 255, np.uint8)
            p[BASLIK:] = tuval[b]
            cv2.putText(p, ad, (10, 31), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (30, 30, 30), 2, cv2.LINE_AA)
            panel.append(p)
        ayirac = np.full((ph + BASLIK, 26, 3), 255, np.uint8)
        img = np.hstack([panel[0], ayirac, panel[1]])
        cv2.putText(img, f"frame {sinir} / {N}", (img.shape[1] - 205, 31),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (120, 120, 120), 1, cv2.LINE_AA)
        kareler.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if adim % 10 == 0:
            print(f"  kare {adim + 1}/{KARE}", flush=True)

    sure = [1 / 12] * (KARE - 1) + [2.5]                            # son karede bekle
    imageio.mimsave(CIKTI, kareler, duration=sure, loop=0, subrectangles=True)
    kapak = CIKTI.replace(".gif", ".png")
    cv2.imwrite(kapak, cv2.cvtColor(kareler[-1], cv2.COLOR_RGB2BGR))
    print(f"  yazildi: {CIKTI} ({os.path.getsize(CIKTI)/1e6:.1f} MB, "
          f"{kareler[0].shape[1]}x{kareler[0].shape[0]}, oran "
          f"{kareler[0].shape[1]/kareler[0].shape[0]:.2f})")


if __name__ == "__main__":
    ne = sys.argv[1] if len(sys.argv) > 1 else "hepsi"
    if ne in ("extract", "hepsi"):
        extract()
    if ne in ("render", "hepsi"):
        render()
