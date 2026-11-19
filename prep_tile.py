# Task 1361: tile TripoSplat's prepared cut-outs (on grey) with their alpha bboxes, to see what BiRefNet kept.
import sys
from PIL import Image, ImageDraw
d, out, names = sys.argv[1], sys.argv[2], sys.argv[3:]; S = 320
sheet = Image.new("RGB", (len(names) * S, S), (60, 60, 60))
for i, n in enumerate(names):
    im = Image.open(f"{d}/{n}-prepared.webp").convert("RGBA"); print(n, im.size, "alpha bbox", im.getchannel("A").getbbox())
    im = im.resize((S, S)); sheet.paste(im, (i * S, 0), im); ImageDraw.Draw(sheet).text((i * S + 6, 4), n, fill=(255, 255, 255))
sheet.save(out, quality=88)
