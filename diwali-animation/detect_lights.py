"""Find the individual string-light bulbs on the house so they can be animated."""
import json, sys
import numpy as np
from PIL import Image, ImageFilter

src, out_img, out_json = sys.argv[1:4]
im = Image.open(src).convert("RGB").resize((1600, 2000), Image.LANCZOS)
im.save(out_img, quality=93)

gray = im.convert("L")
blur = gray.filter(ImageFilter.GaussianBlur(7))
mx = gray.filter(ImageFilter.MaxFilter(9))
g, b, m = (np.asarray(x).astype(int) for x in (gray, blur, mx))
rgb = np.asarray(im).astype(int)
warm = (rgb[..., 0] - rgb[..., 2]) > 25          # bulbs are warm yellow/white
mask = (g == m) & (g > 205) & ((g - b) > 42) & warm
mask[:720] = False; mask[1250:] = False
ys, xs = np.nonzero(mask)
pts = sorted(zip(xs.tolist(), ys.tolist()))
# drop near-duplicates
keep = []
for x, y in pts:
    if all((x - a) ** 2 + (y - c) ** 2 > 36 for a, c in keep):
        keep.append((x, y))
json.dump(keep, open(out_json, "w"))
print(len(keep), "lights")

# debug image
from PIL import ImageDraw
d = im.copy(); dr = ImageDraw.Draw(d)
for x, y in keep: dr.ellipse((x-6, y-6, x+6, y+6), outline=(0, 255, 0), width=2)
d.crop((0, 700, 1600, 1300)).save("/tmp/claude-0/-home-user-Designed-by-Arth/eb64797a-1052-5576-85d7-a30f4763377a/scratchpad/lights_debug.jpg")
