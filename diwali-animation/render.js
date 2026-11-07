// Deterministic frame renderer: Playwright (several workers) -> PNG frames -> ffmpeg.
//   node render.js out.mp4                 full video
//   node render.js out.png --at 4.5,9      preview stills (out-4.5.png ...)
const { chromium } = require('playwright');
const { spawnSync } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path'), os = require('os');
const dir = __dirname, FPS = 30, T = 15, OUT_W = 1080;
const args = process.argv.slice(2), out = args[0] || path.join(dir, 'diwali-animation.mp4');
const at = args.includes('--at') ? args[args.indexOf('--at') + 1].split(',').map(Number) : null;
const WORKERS = Math.max(1, Math.min(os.cpus().length, 6));

(async () => {
  const srv = http.createServer((q, r) => { try { const f = path.join(dir, decodeURIComponent(q.url.split('?')[0]).replace(/^\//, '') || 'index.html');
    r.end(fs.readFileSync(fs.statSync(f).isFile() ? f : path.join(dir, 'index.html'))); } catch (e) { r.statusCode = 404; r.end(); } }).listen(0);
  const url = `http://localhost:${srv.address().port}/index.html`;
  const browser = await chromium.launch();
  const open = async () => { const p = await browser.newPage({ viewport: { width: 1600, height: 2000 }, deviceScaleFactor: OUT_W / 1600 });
    await p.addInitScript(() => { window.__capture = true; }); await p.goto(url); await p.waitForFunction('window.ready'); return p; };
  if (at) {
    const p = await open();
    for (const t of at) { await p.evaluate(t => render(t), t); await (await p.$('#c')).screenshot({ path: out.replace(/(\.\w+)$/, `-${t}$1`) }); }
    await browser.close(); srv.close(); return;
  }
  const fdir = fs.mkdtempSync(path.join(os.tmpdir(), 'frames-')), N = FPS * T;
  let next = 0;
  await Promise.all(Array.from({ length: WORKERS }, async () => {
    const p = await open(), cv = await p.$('#c');
    for (;;) { const f = next++; if (f >= N) break;
      await p.evaluate(t => render(t), f / FPS);
      await cv.screenshot({ path: path.join(fdir, String(f).padStart(4, '0') + '.png') }); }
  }));
  await browser.close(); srv.close();
  const r = spawnSync('ffmpeg', ['-y', '-v', 'error', '-framerate', String(FPS), '-i', path.join(fdir, '%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-crf', '16', '-preset', 'slow', '-movflags', '+faststart', '-vf', 'scale=1080:1350:flags=lanczos', out], { stdio: 'inherit' });
  fs.rmSync(fdir, { recursive: true, force: true }); process.exit(r.status);
})();
