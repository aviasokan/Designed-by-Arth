"""Extend the 4:5 poster to a 9:16 Stories canvas (1600x2844): sky above, navy below the URL bar."""
import numpy as np
from PIL import Image, ImageFilter
OY, W, H = 372, 1600, 2844
p = Image.open('poster_clean.jpg').convert('RGB'); a = np.asarray(p).astype(float)
top = np.asarray(Image.fromarray(a[:10].mean(axis=0, keepdims=True).astype('uint8').repeat(8, 0)).filter(ImageFilter.GaussianBlur(40)))[4].astype(float)
out = np.zeros((H, W, 3))
y = np.arange(OY)[:, None, None] / OY                                   # 0 at very top -> 1 at the seam
dark = np.array([5, 7, 34.])
out[:OY] = dark + (top[None] - dark) * (y ** 0.8)
out[OY:OY + 2000] = a
# soften the seam: blend first 36 poster rows into the extension colour
for i in range(36):
    k = 1 - i / 36; out[OY + i] = out[OY + i] * (1 - 0.7 * k) + top * 0.7 * k
yb = np.arange(H - OY - 2000)[:, None, None] / (H - OY - 2000)
out[OY + 2000:] = np.array([12, 15, 62.]) + (np.array([4, 6, 28.]) - np.array([12, 15, 62.])) * yb
rng = np.random.default_rng(3); out += rng.normal(0, 1.2, out.shape)       # dither, avoids banding in video
Image.fromarray(np.clip(out, 0, 255).astype('uint8')).save('poster916.jpg', quality=94)
print('ok')
