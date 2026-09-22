"""Replace the static images in the presentation with animated GIFs.

PowerPoint plays an animated GIF by itself during a slide show. The steps are:
  1) add the GIFs to ppt/media/
  2) register the gif extension in [Content_Types].xml
  3) in the slide's _rels file, point the target at the gif instead of the png
  4) drop the png files that are no longer referenced

The frame size on the slide (a:ext) is untouched; the GIF fits the same box.

    python scripts/pptx_swap_gifs.py <input.pptx> <output.pptx>
"""
import os, re, shutil, sys, zipfile

# slide number -> (media file to replace, GIF to put in its place)
REPLACEMENTS = {
    8: ("image2.png", "outputs/report/02_gt_vs_yolo26.gif"),
    9: ("image3.png", "outputs/report/09_sort_vs_jpdaf.gif"),
}


def main(src, dst):
    z = zipfile.ZipFile(src)
    parts = {n: z.read(n) for n in z.namelist()}
    z.close()

    new_media, old_media = {}, []
    for slide, (old_png, gif_path) in REPLACEMENTS.items():
        rels_path = f"ppt/slides/_rels/slide{slide}.xml.rels"
        rels = parts[rels_path].decode("utf-8")
        if f"media/{old_png}" not in rels:
            print(f"  ! slide {slide}: {old_png} not found, skipping")
            continue
        gif_name = f"image_anim{slide}.gif"
        new_media[f"ppt/media/{gif_name}"] = open(gif_path, "rb").read()
        parts[rels_path] = rels.replace(f"media/{old_png}", f"media/{gif_name}").encode("utf-8")
        old_media.append(f"ppt/media/{old_png}")
        mb = os.path.getsize(gif_path) / 1e6
        print(f"  slide {slide}: {old_png} -> {gif_name}  ({mb:.1f} MB)")

    # register the gif extension
    ct_path = "[Content_Types].xml"
    ct = parts[ct_path].decode("utf-8")
    if 'Extension="gif"' not in ct:
        ct = ct.replace("<Default", '<Default Extension="gif" ContentType="image/gif"/><Default', 1)
        parts[ct_path] = ct.encode("utf-8")
        print("  [Content_Types].xml: gif registered")

    # drop old png files that no other slide still references
    for old in old_media:
        name = old.split("/")[-1]
        still_used = any(name in v.decode("utf-8", "ignore")
                         for k, v in parts.items() if k.endswith(".rels"))
        if not still_used:
            parts.pop(old, None)
            print(f"  dropped: {old}")

    parts.update(new_media)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in parts.items():
            out.writestr(name, data)
    print(f"\n  written: {dst}  ({os.path.getsize(dst)/1e6:.1f} MB)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
