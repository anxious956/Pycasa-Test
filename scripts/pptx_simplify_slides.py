"""Sunumu anlatan kisinin slaytlarini sadelestir (5, 6, 9, 10, 13, 14).

Ilke: slayt konusmanin yerini almaz, ona destek olur. Tablolar kaliyor (kanit
onlar), uzun duz yazi cumleleri kisaltiliyor. Paragraf SILINMIYOR, sadece metin
kisaltiliyor; boylece yerlesim bozulmuyor, kutularda daha cok bosluk kaliyor.

Ayrica iki icerik duzeltmesi:
  - slayt 14, 1. satir: "fixed by 8.4+" abartili; dallanma 8.4'te de duruyor,
    sadece her seferinde ayni tarafa gidiyor.

    python scripts/pptx_simplify_slides.py <girdi.pptx> <cikti.pptx>
"""
import os, sys, zipfile

DEGISIM = {
 5: [
  ("running YOLOv5 earlier in the same Python process changes YOLO26's low-confidence detections — even with identical weights, data, and settings. (Root cause confirmed two slides later.)",
   "same weights, same data, same settings — only the process history differs. Root cause two slides later."),
  ("Recall is essentially identical across every run — only the false-positive tail moves, and with it, precision and F1",
   "Recall never moves. Only false positives do — precision and F1 follow."),
  ("F1 for the same model on the same data ranges from 77% to 85% across five runs depending purely on what ran earlier in the process",
   "Same model, same data: F1 ranges 77% to 85% across five runs."),
  ("This surfaced because our API test suite runs each module group in its own process — the isolated YOLO26 number did not match the one in our own report. A second machine then confirmed it with a third value.",
   "Found because our API tests run each module in its own process. A second machine later gave a third value."),
 ],
 6: [
  ("A controlled 2x2 — varying the YOLOv5 import and OpenCV thread count independently, each condition in its own process.",
   "A 2x2: import and thread count varied independently, each in its own process."),
  ("A = B and C = D: thread count changes nothing. Holding it fixed, importing YOLOv5 alone still shifts 387 detections.",
   "Thread count: no effect. Import alone: 387 detections."),
 ],
 9: [
  ("Both trackers ran on identical ground-truth detections — no detector needed. JPDAF is the group's own 2017 algorithm, adapted from radar tracking to survive collisions.",
   "Identical input to both. JPDAF is the group's 2017 algorithm, adapted from radar tracking."),
  ("On 101 frames the difference looks like noise (+12% track length). Over the full clip it's unmistakable: JPDAF holds each cell ~2x longer and needs 35% fewer tracks — SORT is losing identities through collisions and restarting them as “new” cells.",
   "101 frames: looks like noise, +12%. Full clip: JPDAF holds each cell 2x longer with 35% fewer tracks. SORT loses identities in collisions and restarts them."),
  ("Every SORT track (left, n=401) vs. every JPDAF track (right, n=262) — full 899-frame clip.",
   "Tracks accumulating over the full 899-frame clip. SORT left (401), JPDAF right (262)."),
 ],
 10: [
  ("Population motility grades, concentration and total count, compared against HSTLI's own commercial Sperm Class Analyzer report for this donor.",
   "Compared against the real Sperm Class Analyzer report for this donor."),
  ("GT+SORT tracks motility grades reasonably well but concentration runs ~14% low",
   "GT+SORT: grades close, concentration 14% low."),
  ("YOLO26+SORT overshoots concentration by 20-24% both times — false-positive detections become short, static tracks, inflating both the cell count and the immotile fraction",
   "YOLO26+SORT: concentration 20-24% high. False positives become short static tracks, inflating count and immotile share."),
  ("101 frames is only 3.4 of ~30 seconds — is this a detector problem, or a duration problem? Full-clip rerun on the next slide answers it",
   "101 frames is 3.4 of 30 seconds. Detector problem, or duration? Next slide."),
 ],
 13: [
  ("Every public function in pycasa was exercised at least once — 140 test cases including parameter variants and deliberately invalid inputs, each module group run in its own process to bound memory and isolate the YOLOv5 contamination.",
   "Every public function run at least once. 140 cases, including deliberately invalid inputs. Each module in its own process."),
  (" — the 6 failures are genuine defects (next slide), not test artefacts. Everything documented works correctly, and error handling is clear in almost every case.",
   " — the 6 failures are genuine defects (next slide), not test artefacts."),
 ],
 14: [
  ("In ultralytics==8.3.197, YOLO26's NMS silently swaps algorithms if torchvision happens to be imported (Slides 5-7) — highest priority, fixed by 8.4+",
   "NMS algorithm depends on whether torchvision is imported (slides 5-7). Highest priority. No longer varies in 8.4+."),
  ("get_assessment()/get_motility() hand back session objects — deep-copy before comparing",
   "Returns the session's own objects, not copies. Deep-copy before comparing."),
  ("Full-clip loading needs one large allocation — bounded by largest free memory block, not total memory",
   "Needs one large allocation — bounded by the largest free block, not total memory."),
 ],
}


def main(girdi, cikti):
    z = zipfile.ZipFile(girdi)
    icerik = {n: z.read(n) for n in z.namelist()}
    z.close()

    toplam = eksik = 0
    for slayt, ciftler in DEGISIM.items():
        yol = f"ppt/slides/slide{slayt}.xml"
        x = icerik[yol].decode("utf-8")
        for eski, yeni in ciftler:
            # XML'de & ve < kacisli duruyor olabilir
            for a, b in ((eski, yeni),
                         (eski.replace("&", "&amp;"), yeni.replace("&", "&amp;"))):
                if a in x:
                    x = x.replace(a, b)
                    toplam += 1
                    print(f"  slayt {slayt:2d}: {len(eski):3d} -> {len(yeni):3d} karakter  {eski[:46]!r}")
                    break
            else:
                eksik += 1
                print(f"  ! slayt {slayt:2d}: BULUNAMADI  {eski[:60]!r}")
        icerik[yol] = x.encode("utf-8")

    with zipfile.ZipFile(cikti, "w", zipfile.ZIP_DEFLATED) as out:
        for ad, veri in icerik.items():
            out.writestr(ad, veri)
    print(f"\n  {toplam} degisiklik, {eksik} bulunamadi")
    print(f"  yazildi: {cikti}  ({os.path.getsize(cikti)/1e6:.1f} MB)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
