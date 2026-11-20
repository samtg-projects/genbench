import sys, cv2, numpy as np
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
S = 256; rows = (len(files) + cols - 1) // cols
im = np.zeros((rows * (S + 22), cols * S, 3), np.uint8)
for i, f in enumerate(files):
    a = cv2.imread(f); a = cv2.resize(a, (S, S), interpolation=cv2.INTER_AREA)
    r, c = divmod(i, cols); im[r * (S + 22): r * (S + 22) + S, c * S:(c + 1) * S] = a
    cv2.putText(im, f.split("/")[-1].split("_seed")[0], (c * S + 6, r * (S + 22) + S + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
cv2.imwrite(out, im, [cv2.IMWRITE_JPEG_QUALITY, 85]); print(out, im.shape)
