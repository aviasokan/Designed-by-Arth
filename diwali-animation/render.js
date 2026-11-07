// Renders the animation frame-by-frame with Playwright, then encodes with ffmpeg.
const { chromium } = require('playwright');
const { spawnSync, spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const dir = __dirname, FPS = 30, T = 10, OUT_W = 1080, OUT_H = 1350;
const out = process.argv[2] || path.join(dir, 'diwali-animation.mp4');
const only = process.argv[3] ? +process.argv[3] : null;   // optional: single-frame preview at time t

(async () => {
  const srv = http.createServer((q, r) => { try { const f = path.join(dir, decodeURIComponent(q.url.split('?')[0]).replace(/^\//, '') || 'index.html');
    r.end(fs.readFileSync(fs.existsSync(f) && fs.statSync(f).isFile() ? f : path.join(dir, 'index.html'))); } catch (e) { r.statusCode = 404; r.end(); } }).listen(0);
  const port = srv.address().port;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 2000 }, deviceScaleFactor: OUT_W / 1600 });
  await page.addInitScript(() => { window.__capture = true; });
  await page.goto(`http://localhost:${port}/index.html`);
  await page.waitForFunction('window.ready');
  const cv = await page.$('#c');
  if (only !== null) { await page.evaluate(t => render(t), only); await cv.screenshot({ path: out }); await browser.close(); srv.close(); return; }
  const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-crf', '16', '-preset', 'slow', '-movflags', '+faststart', '-vf', `scale=${OUT_W}:${OUT_H}:flags=lanczos`, out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < FPS * T; f++) {
    await page.evaluate(t => render(t), f / FPS);
    const png = await cv.screenshot({ type: 'png' });
    if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  await browser.close(); srv.close();
})();
