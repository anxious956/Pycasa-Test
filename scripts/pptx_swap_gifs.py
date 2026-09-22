"""Sunumdaki durgun goruntuleri animasyonlu GIF'lerle degistir.

PowerPoint animasyonlu GIF'i slayt gosterisinde kendiliginden oynatir. Yapilan is:
  1) GIF'leri ppt/media/ icine ekle
  2) [Content_Types].xml'e gif uzantisini tanit
  3) ilgili slaydin _rels dosyasinda hedefi png yerine gif'e cevir
  4) artik kullanilmayan png'leri at

Slayttaki cerceve boyutu (a:ext) degismiyor; GIF ayni kutuya oturuyor.

    python scripts/pptx_swap_gifs.py <girdi.pptx> <cikti.pptx>
"""
import os, re, shutil, sys, zipfile

# slayt numarasi -> (degistirilecek medya dosyasi, yerine konacak GIF)
DEGISIM = {
    8: ("image2.png", "outputs/report/02_gt_vs_yolo26.gif"),
    9: ("image3.png", "outputs/report/09_sort_vs_jpdaf.gif"),
}


def main(girdi, cikti):
    z = zipfile.ZipFile(girdi)
    icerik = {n: z.read(n) for n in z.namelist()}
    z.close()

    yeni_medya, eskiler = {}, []
    for slayt, (eski_png, gif_yolu) in DEGISIM.items():
        rels_yol = f"ppt/slides/_rels/slide{slayt}.xml.rels"
        rels = icerik[rels_yol].decode("utf-8")
        if f"media/{eski_png}" not in rels:
            print(f"  ! slayt {slayt}: {eski_png} bulunamadi, atlaniyor")
            continue
        gif_ad = f"image_anim{slayt}.gif"
        yeni_medya[f"ppt/media/{gif_ad}"] = open(gif_yolu, "rb").read()
        icerik[rels_yol] = rels.replace(f"media/{eski_png}", f"media/{gif_ad}").encode("utf-8")
        eskiler.append(f"ppt/media/{eski_png}")
        mb = os.path.getsize(gif_yolu) / 1e6
        print(f"  slayt {slayt}: {eski_png} -> {gif_ad}  ({mb:.1f} MB)")

    # gif uzantisini tanit
    ct_yol = "[Content_Types].xml"
    ct = icerik[ct_yol].decode("utf-8")
    if 'Extension="gif"' not in ct:
        ct = ct.replace("<Default", '<Default Extension="gif" ContentType="image/gif"/><Default', 1)
        icerik[ct_yol] = ct.encode("utf-8")
        print("  [Content_Types].xml: gif tanitildi")

    # baska slaytta kullanilmayan eski png'leri at
    for eski in eskiler:
        ad = eski.split("/")[-1]
        hala = any(ad in v.decode("utf-8", "ignore")
                   for k, v in icerik.items() if k.endswith(".rels"))
        if not hala:
            icerik.pop(eski, None)
            print(f"  atildi: {eski}")

    icerik.update(yeni_medya)
    with zipfile.ZipFile(cikti, "w", zipfile.ZIP_DEFLATED) as out:
        for ad, veri in icerik.items():
            out.writestr(ad, veri)
    print(f"\n  yazildi: {cikti}  ({os.path.getsize(cikti)/1e6:.1f} MB)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
