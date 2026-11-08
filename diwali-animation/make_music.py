"""Original synthesised soundtrack, timed to the film's events. Writes diwali-music.wav (16 s, stereo)."""
import wave
import numpy as np
SR, DUR = 44100, 16.0
N = int(SR * DUR); rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)

def put(sig, t0, gain=1.0, pan=0.0):          # pan -1..1
    i = int(t0 * SR); 
    if i >= N: return
    s = sig[: N - i] if i >= 0 else sig[-i:]
    i = max(i, 0)
    gl, gr = gain * np.sqrt((1 - pan) / 2), gain * np.sqrt((1 + pan) / 2)
    L[i:i + len(s)] += s * gl; R[i:i + len(s)] += s * gr

def tt(d): return np.arange(int(SR * d)) / SR
def midi(n): return 440 * 2 ** ((n - 69) / 12)
NOTE = {'D2': 38, 'E2': 40, 'G2': 43, 'A2': 45, 'B2': 47, 'D3': 50, 'D4': 62, 'E4': 64, 'F#4': 66, 'G4': 67, 'A4': 69, 'B4': 71,
        'D5': 74, 'E5': 76, 'F#5': 78, 'G5': 79, 'A5': 81, 'B5': 83, 'D6': 86, 'E6': 88}

def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); m = np.ones_like(f)
    if lo: m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi: m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x))

def pluck(f, d=1.2, bright=1.0):              # sitar-ish: harmonic stack, fast decay, slight buzz
    t = tt(d); y = np.zeros_like(t)
    for h in range(1, 10):
        y += (1 / h ** 1.15) * np.exp(-t * (4 + 2.2 * h / bright)) * np.sin(2 * np.pi * f * h * t * (1 + 0.0009 * h * h))
    y *= (1 + 0.25 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t * 18))
    return y * np.minimum(1, t * 600) * 0.5
def bell(f, d=2.4):
    t = tt(d); y = np.zeros_like(t)
    for r, a, dc in ((1, 1, 1.6), (2.76, .5, 2.4), (5.4, .3, 3.4), (8.93, .15, 5)):
        y += a * np.exp(-t * dc) * np.sin(2 * np.pi * f * r * t)
    return y * np.minimum(1, t * 800) * 0.45
def pad(f, d, a=0.6):
    t = tt(d); env = np.minimum(1, t / a) * np.minimum(1, (d - t) / 0.5)
    y = sum(np.sin(2 * np.pi * f * k * t + p) / k for k, p in ((1, 0), (2, 1.1), (3, 2.0))) * 0.5
    y += 0.4 * np.sin(2 * np.pi * f * 1.004 * t)
    return y * env * 0.35
def kick():
    t = tt(0.45); f = 48 + 130 * np.exp(-t * 28); ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t * 9) + 0.5 * rng.standard_normal(len(t)) * np.exp(-t * 90)) * 0.9
def dhol(): 
    t = tt(0.3); f = 90 + 90 * np.exp(-t * 35); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) * 0.8
def tabla(f=420, d=0.22):
    t = tt(d); fr = f * (1 + 0.18 * np.exp(-t * 30)); y = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 22)
    return (y + 0.3 * np.sin(2 * np.pi * fr * 2.3 * t) * np.exp(-t * 40)) * 0.55
def shaker(d=0.07):
    t = tt(d); return fft_filter(rng.standard_normal(len(t)), lo=5000) * np.exp(-t * 55) * 0.35
def clap():
    t = tt(0.2); n = fft_filter(rng.standard_normal(len(t)), lo=900, hi=6000)
    return n * (np.exp(-t * 28) + 0.6 * np.exp(-((t - 0.015) * 90) ** 2)) * 0.7
def whoosh(d=0.6, lo=500, hi=5000, peak=0.5):
    t = tt(d); n = fft_filter(rng.standard_normal(len(t)), lo=lo, hi=hi); e = np.sin(np.pi * np.clip(t / d, 0, 1) ** peak) ** 2
    return n * e * 0.5
def riser(d, f0=180, f1=2200):
    t = tt(d); k = (t / d); f = f0 * (f1 / f0) ** k; ph = 2 * np.pi * np.cumsum(f) / SR
    n = fft_filter(rng.standard_normal(len(t)), lo=1500) * k ** 2
    return (np.sin(ph) * 0.35 + n * 0.7) * k ** 1.6
def boom(d=1.6, f=55):
    t = tt(d); fr = f * (1 + 1.2 * np.exp(-t * 9)); y = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 2.2)
    n = fft_filter(rng.standard_normal(len(t)), hi=900) * np.exp(-t * 3.5) * 0.9
    return (y + n) * 0.9
def crackle(d=1.0):
    t = tt(d); n = fft_filter(rng.standard_normal(len(t)), lo=2500); pops = (rng.random(len(t)) > 0.9992).astype(float)
    env = np.exp(-t * 3); return (n * (np.convolve(pops, np.exp(-np.arange(900) / 120.0), 'same') * 3)) * env * 0.6
def whistle(d=0.85):
    t = tt(d); k = t / d; f = 700 + 1900 * k ** 1.5; return np.sin(2 * np.pi * np.cumsum(f) / SR) * (k ** 1.2) * np.exp(-((k - 1) * 3) ** 2) * 0.16
def click():
    t = tt(0.08); return fft_filter(rng.standard_normal(len(t)), lo=1800) * np.exp(-t * 90) * 0.9 + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 60) * 0.6

# ---------------- timeline (matches index.html) ----------------
BEAT, OFF = 0.5, 0.05                         # beat grid; beat 7 lands on the switch flip (3.55 s)
# intro drone + shutters
for f, a in ((midi(38), 0.45), (midi(45), 0.3)):
    t = tt(4.4); put(np.sin(2 * np.pi * f * t) * np.minimum(1, t / 1.5) * np.minimum(1, (4.4 - t) / 0.6) * a, 0, 1.0)
put(pad(midi(50), 3.9, 1.5), 0, 0.6, -0.3); put(pad(midi(57), 3.9, 1.5), 0.1, 0.5, 0.3)
for k in range(10):
    t0 = 0.7 + k * 0.16; put(whoosh(0.5, 700, 4500), t0 - 0.05, 0.35, -0.7 + 1.4 * (k / 9)); put(tabla(300 + 20 * k, 0.12), t0 + 0.55, 0.35, -0.7 + 1.4 * (k / 9))
for t0, n in ((0.9, 'A4'), (1.4, 'D5'), (1.9, 'F#5'), (2.4, 'E5')): put(bell(midi(NOTE[n]), 2.0), t0, 0.35, 0.3 * (1 if t0 > 1.5 else -1))
# switch: appear, riser, flip
put(whoosh(0.5, 300, 3000), 2.55, 0.5); put(riser(1.0), 2.55, 0.8); put(tabla(520, 0.1), 2.62, 0.5)
put(click(), 3.55, 1.0); put(boom(2.0, 48), 3.55, 1.0); put(bell(midi(74), 3.0), 3.55, 0.6, -0.2); put(bell(midi(81), 3.0), 3.55, 0.5, 0.2); put(bell(midi(86), 3.0), 3.55, 0.35)
# ignition sparkle run (matches the left-to-right wave)
run = ['D5', 'E5', 'F#5', 'A5', 'B5', 'D6', 'E6', 'D6', 'B5', 'A5', 'F#5', 'A5', 'B5', 'D6', 'E6', 'D6']
for i, n in enumerate(run): put(bell(midi(NOTE[n]), 1.4), 3.65 + i * 0.115, 0.28, -0.8 + 1.6 * (i / 15))
put(whoosh(1.6, 800, 7000, 0.7), 3.6, 0.45)
put(bell(midi(86), 2.0), 4.55, 0.4)                          # logo pop
# chords + bass
CH = [('D', [50, 54, 57], 38), ('A', [52, 57, 61], 45), ('Bm', [50, 54, 59], 47), ('G', [50, 55, 59], 43), ('D', [50, 54, 57], 38), ('A', [52, 57, 61], 45)]
for bar, (name, tri, root) in enumerate(CH):
    t0 = 3.55 + bar * 2.0
    for m in tri: put(pad(midi(m), 2.1, 0.35), t0, 0.5, ((m % 3) - 1) * 0.5)
    for b in (0, 2, 2.5, 3.5):
        put(pluck(midi(root), 0.6, 0.7) * 1.2, t0 + b * BEAT, 0.55 if b in (0, 2) else 0.3, 0)
# drums
for k in range(0, 17):
    t0 = 3.55 + k * BEAT
    if t0 > 15.3: break
    put(kick(), t0, 0.85 if k % 2 == 0 else (0.5 if t0 > 7.5 else 0.0))
    put(tabla(430 + 30 * (k % 3)), t0 + BEAT / 2, 0.45, 0.3)
    if t0 >= 5.5: put(shaker(), t0, 0.5, -0.4); put(shaker(), t0 + BEAT / 2, 0.35, 0.4)
    if t0 >= 9.5 and k % 2 == 1: put(clap(), t0, 0.55)
    if t0 >= 7.5 and k % 4 == 3: put(dhol(), t0 + BEAT / 2, 0.55)
for k in range(8): put(clap(), 13.05 + k * 0.0625 * 4, 0.12 + 0.07 * k)        # snare-ish roll into the finale
# melody (sitar pluck + doubled bell) timed to the title build
MEL = [(5.55, ['A4', 'B4', 'D5', 'E5', 'F#5', 'E5', 'D5', 'B4']), (7.55, ['E5', 'F#5', 'A5', 'F#5', 'E5', 'D5', 'E5', 'A4']),
       (9.55, ['D5', 'E5', 'F#5', 'A5', 'B5', 'A5', 'F#5', 'E5']), (11.55, ['B4', 'D5', 'E5', 'G5', 'F#5', 'E5', 'D5', 'B4']),
       (13.55, ['F#5', 'A5', 'B5', 'D6', 'B5', 'A5', 'F#5', 'D5'])]
for t0, notes in MEL:
    for i, n in enumerate(notes):
        ts = t0 + i * 0.25; put(pluck(midi(NOTE[n]), 1.0), ts, 0.55, 0.15 * (1 if i % 2 else -1))
        if i % 4 == 0: put(bell(midi(NOTE[n]) * 2, 1.6), ts, 0.16, 0.3)
put(pad(midi(62), 2.2, 0.3), 13.55, 0.6); put(pad(midi(69), 2.2, 0.3), 13.55, 0.5); put(pad(midi(74), 2.2, 0.3), 13.55, 0.45)
# title: HAPPY slide-ins, Diwali letter landings, tagline wipes, footer
for i in range(5): put(whoosh(0.35, 1500, 8000), 5.1 + i * 0.09, 0.22, -0.6 + 0.3 * i)
for i in range(6):
    tl = 5.6 + 0.12 * i + 0.285; put(dhol(), tl, 0.7, -0.4 + 0.16 * i); put(bell(midi(NOTE[['D5', 'E5', 'F#5', 'A5', 'B5', 'D6'][i]]), 1.6), tl, 0.3, -0.4 + 0.16 * i)
put(whoosh(0.9, 800, 6000), 6.55, 0.35); put(whoosh(0.9, 800, 6000), 6.9, 0.3); put(whoosh(0.5, 400, 3000), 6.75, 0.25)
# fireworks: rocket whistle, boom, crackle (same schedule as SHOWS)
for st in [2.2, 2.9, 3.8, 4.6, 5.5, 6.3, 7.2, 8.0, 8.8, 9.5, 10.3, 11.0, 11.8, 12.5, 12.9, 13.3, 13.6]:
    t0 = 6.0 + (st - 2.2) * 0.6; pan = -0.5 if int(st * 10) % 2 else 0.5
    put(whistle(), t0 - 0.85, 0.5, pan); put(boom(1.2, 62 + 12 * (int(st * 7) % 4)), t0, 0.5, pan); put(crackle(1.2), t0 + 0.05, 0.45, -pan)
# finale + tail
put(boom(2.4, 45), 13.55, 0.95); put(whoosh(2.0, 2500, 12000, 0.5), 13.5, 0.5); put(crackle(1.6), 13.6, 0.6); put(bell(midi(86), 3.0), 13.6, 0.4); put(bell(midi(74), 3.0), 13.6, 0.4)
put(riser(0.9, 250, 3000), 12.65, 0.45)

# ---------------- master ----------------
t = np.arange(N) / SR
fade = np.minimum(1, t / 0.4) * np.clip((DUR - t) / 0.8, 0, 1)
for ch in (L, R): ch *= fade
st = np.stack([L, R], 1)
st = np.tanh(st * 1.15) / np.tanh(1.15); st *= 0.89 / np.abs(st).max()
with wave.open('diwali-music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print('peak', np.abs(st).max().round(3), 'rms', np.sqrt((st ** 2).mean()).round(3))
