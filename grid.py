# grid.py sheet.jpg rows col cols out.jpg : take column `col` of each row of a preview sheet and lay them out in a grid
import sys
from PIL import Image
src, rows, col, ncols, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
im = Image.open(src); W, H = im.size; rh = H // rows; cw = W // 5
g = Image.new("RGB", (ncols * cw, -(-rows // ncols) * rh))
for i in range(rows):
    g.paste(im.crop((col * cw, i * rh, (col + 1) * cw, (i + 1) * rh)), ((i % ncols) * cw, (i // ncols) * rh))
g.save(out, quality=88); print(g.size)
