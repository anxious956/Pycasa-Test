"""Slayt 5'teki iki metin sorununu duzelt.

1) Yanlis iddia: "two of us compared numbers independently" -- bulgu tek kisilik
   bir calismada, API test paketi her modul grubunu ayri process'te calistirdigi
   icin ortaya cikti. Ikinci makinedeki calistirma sonradan geldi ve dogruladi.
2) Belirsiz etiket: uc satir "Our own run" diyor, dinleyici kimin calistirdigini
   ayirt edemiyor. Makine 1 / Makine 2 olarak netlestiriliyor.

    python scripts/pptx_fix_slide5.py <girdi.pptx> <cikti.pptx>
"""
import os, sys, zipfile

DEGISIM = [
    # (eski metin, yeni metin)
    ("This was only caught because two of us compared numbers independently — a single run would never reveal it",
     "This surfaced because our API test suite runs each module group in its own process — the isolated YOLO26 number did not match the one in our own report. A second machine then confirmed it with a third value."),
    ("Isolated process (clean)",
     "Machine 1 — isolated process (clean)"),
    ("After YOLOv5, same process",
     "Machine 1 — after YOLOv5, same process"),
    ("Our own run — after YOLOv5, same process",
     "Machine 2 — after YOLOv5, same process"),
]


def main(girdi, cikti):
    z = zipfile.ZipFile(girdi)
    icerik = {n: z.read(n) for n in z.namelist()}
    z.close()

    yol = "ppt/slides/slide5.xml"
    x = icerik[yol].decode("utf-8")
    for eski, yeni in DEGISIM:
        # uzun etiketler once: "Our own run — after YOLOv5..." icinde
        # "After YOLOv5, same process" gecmiyor, yine de sira onemli
        n = x.count(eski)
        if n == 0:
            print(f"  ! bulunamadi: {eski[:55]!r}")
            continue
        x = x.replace(eski, yeni)
        print(f"  {n}x degisti: {eski[:48]!r}")
    icerik[yol] = x.encode("utf-8")

    with zipfile.ZipFile(cikti, "w", zipfile.ZIP_DEFLATED) as out:
        for ad, veri in icerik.items():
            out.writestr(ad, veri)
    print(f"\n  yazildi: {cikti}  ({os.path.getsize(cikti)/1e6:.1f} MB)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
