"""Lift the logo / title / tagline off the poster as transparent sprites and build a text-free background.
Outputs: poster_clean.jpg, layers/*.png, layers.json  (all in 1600x2000 poster coordinates)."""
import json, os
import numpy as np
from PIL import Image, ImageFilter

os.makedirs('layers', exist_ok=True)
im = Image.open('poster.jpg').convert('RGB'); A = np.asarray(im).astype(np.float32)
H, W = A.shape[:2]
REG = {'logo': (430, 15, 1170, 262), 'title': (455, 318, 1150, 585), 'tag': (390, 580, 1210, 700)}

def blur(a, s):            # separable gaussian blur on float arrays (H,W) or (H,W,C)
    r = int(3 * s); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum()
    out = a.astype(np.float32)
    for ax in (0, 1):
        pad = [(0, 0)] * out.ndim; pad[ax] = (r, r)
        p = np.pad(out, pad, mode='edge'); acc = np.zeros_like(out)
        for i, w in enumerate(k):
            sl = [slice(None)] * out.ndim; sl[ax] = slice(i, i + out.shape[ax]); acc += w * p[tuple(sl)]
        out = acc
    return out

def dilate(m, r):          # binary dilation using max filter
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * r + 1))) > 0

clean = A.copy(); layers = {}
for name, (x0, y0, x1, y1) in REG.items():
    sub = A[y0:y1, x0:x1]
    lum = sub.mean(-1)
    m0 = (lum > 105) | (sub[..., 0] > 150)                          # obvious text pixels
    m = dilate(m0, 4)
    valid = (~m).astype(np.float32)
    bgv = blur(sub * valid[..., None], 14) / np.maximum(blur(valid, 14), 1e-3)[..., None]
    bgv = np.where(valid[..., None] > 0, sub, bgv)                  # keep real bg where it is bg
    # foreground colour: nearest strongly-foreground pixel colour
    dist = np.linalg.norm(sub - bgv, axis=-1)
    solid = (dist > 120).astype(np.float32)
    fg = blur(sub * solid[..., None], 3) / np.maximum(blur(solid, 3), 1e-3)[..., None]
    fg = np.where(solid[..., None] > 0, sub, fg)
    nofg = blur(solid, 3) < 1e-3; fg[nofg] = sub[nofg]
    d = fg - bgv
    alpha = np.clip(((sub - bgv) * d).sum(-1) / np.maximum((d * d).sum(-1), 1.0), 0, 1)
    alpha[~m] = 0
    alpha[alpha < 0.04] = 0
    # sprite colour = foreground colour (not the blended pixel) so edges composite cleanly
    spr = np.dstack([np.clip(fg, 0, 255), alpha * 255]).astype(np.uint8)
    layers[name] = (spr, (x0, y0))
    cmask = dilate(alpha > 0.02, 3)
    clean[y0:y1, x0:x1][cmask] = bgv[cmask]
Image.fromarray(np.clip(clean, 0, 255).astype(np.uint8)).save('poster_clean.jpg', quality=94)

def save(name, spr, ox, oy, box):
    x0, y0, x1, y1 = box
    Image.fromarray(spr[y0:y1, x0:x1]).save(f'layers/{name}.png')
    return {'name': name, 'x': ox + x0, 'y': oy + y0, 'w': x1 - x0, 'h': y1 - y0}

def bbox(a, thr=8):
    ys, xs = np.nonzero(a > thr)
    return tuple(int(v) for v in (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))

def segments(alpha, gap=2):                                         # split by empty columns
    cols = (alpha > 8).any(0); segs = []; s = None
    for i, c in enumerate(cols):
        if c and s is None: s = i
        if not c and s is not None: segs.append([s, i]); s = None
    if s is not None: segs.append([s, len(cols)])
    out = []
    for a in segs:
        if out and a[0] - out[-1][1] <= gap: out[-1][1] = a[1]
        else: out.append(a)
    return out

meta = {'logo': [], 'happy': [], 'diwali': [], 'tag': []}
# ---- logo: mark (top) and company name (bottom)
spr, (ox, oy) = layers['logo']; al = spr[..., 3]
rows = (al > 8).any(1); ys = np.nonzero(rows)[0]
gap_y = None
for y in range(ys.min(), ys.max()):
    if not rows[y] and rows[y + 1:].any() and rows[:y].any(): gap_y = y; break
meta['logo'].append(save('logo_mark', spr[:gap_y], ox, oy, bbox(al[:gap_y])))
nm = spr.copy(); nm[:gap_y + 1] = 0
meta['logo'].append(save('logo_name', nm, ox, oy, bbox(nm[..., 3])))
# ---- title: white HAPPY vs orange Diwali
spr, (ox, oy) = layers['title']; rgb = spr[..., :3].astype(int); al = spr[..., 3]
white = (rgb.min(-1) > 170)
for key, sel in (('happy', white), ('diwali', ~white)):
    part = spr.copy(); part[..., 3] = np.where(sel, al, 0)
    segs = segments(part[..., 3])
    print(key, 'segments:', [(a, b) for a, b in segs])
    for i, (a, b) in enumerate(segs):
        sub = part.copy(); sub[:, :a, 3] = 0; sub[:, b:, 3] = 0
        meta[key].append(save(f'{key}_{i}', sub, ox, oy, bbox(sub[..., 3])))
# ---- tagline: two lines
spr, (ox, oy) = layers['tag']; al = spr[..., 3]
rows = (al > 8).any(1); ys = np.nonzero(rows)[0]
split = None
for y in range(ys.min() + 5, ys.max() - 5):
    if not rows[y] and rows[y - 3] is not None and not rows[y:y + 3].any() and rows[:y].any() and rows[y + 3:].any(): split = y; break
if split is None: split = (ys.min() + ys.max()) // 2
for i, (a, b) in enumerate(((0, split), (split, spr.shape[0]))):
    sub = spr.copy(); sub[:a] = 0; sub[b:] = 0
    meta['tag'].append(save(f'tag_{i}', sub, ox, oy, bbox(sub[..., 3])))
json.dump(meta, open('layers.json', 'w'))
print({k: len(v) for k, v in meta.items()})
