"""Fix the two text problems on slide 5.

1) Incorrect claim: "two of us compared numbers independently" -- the finding
   came out of a single-person study, because the API test suite runs each module
   group in its own process. The run on the second machine came later and
   confirmed it.
2) Ambiguous labels: three rows say "Our own run", so the audience cannot tell
   who ran what. They are clarified as Machine 1 / Machine 2.

    python scripts/pptx_fix_slide5.py <input.pptx> <output.pptx>
"""
import os, sys, zipfile

REPLACEMENTS = [
    # (old text, new text)
    ("This was only caught because two of us compared numbers independently — a single run would never reveal it",
     "This surfaced because our API test suite runs each module group in its own process — the isolated YOLO26 number did not match the one in our own report. A second machine then confirmed it with a third value."),
    ("Isolated process (clean)",
     "Machine 1 — isolated process (clean)"),
    ("After YOLOv5, same process",
     "Machine 1 — after YOLOv5, same process"),
    ("Our own run — after YOLOv5, same process",
     "Machine 2 — after YOLOv5, same process"),
]


def main(src, dst):
    z = zipfile.ZipFile(src)
    parts = {n: z.read(n) for n in z.namelist()}
    z.close()

    path = "ppt/slides/slide5.xml"
    x = parts[path].decode("utf-8")
    for old, new in REPLACEMENTS:
        # longer labels first: "Our own run — after YOLOv5..." does not contain
        # "After YOLOv5, same process", but the order still matters
        n = x.count(old)
        if n == 0:
            print(f"  ! not found: {old[:55]!r}")
            continue
        x = x.replace(old, new)
        print(f"  replaced {n}x: {old[:48]!r}")
    parts[path] = x.encode("utf-8")

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in parts.items():
            out.writestr(name, data)
    print(f"\n  written: {dst}  ({os.path.getsize(dst)/1e6:.1f} MB)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
