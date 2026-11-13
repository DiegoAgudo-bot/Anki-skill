// Captura el vídeo fotograma a fotograma:  node render.js [fps] [solo-muestras]
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const fps = +(process.argv[2] || 30);
  const muestras = process.argv[3] === 'muestras';
  const dir = __dirname;
  const pos = fs.readFileSync(path.join(dir, 'cap', 'posiciones.json'), 'utf8');
  const html = fs.readFileSync(path.join(dir, 'player.html'), 'utf8').replace('/*__POS__*/{}', pos);
  fs.writeFileSync(path.join(dir, 'player.build.html'), html);
  const out = path.join(dir, muestras ? 'muestras' : 'frames');
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  const errores = []; p.on('pageerror', (e) => errores.push(e.message));
  await p.goto('file://' + path.join(dir, 'player.build.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(500);
  const dur = await p.evaluate(() => window.DURACION);
  const tiempos = muestras ? [0.2, 2, 6, 10, 13.5, 16, 20.5, 23.6, 25.5, 29]
    : Array.from({ length: Math.round(dur * fps) }, (_, i) => i / fps);
  let n = 0;
  for (const t of tiempos) {
    await p.evaluate((x) => window.pintar(x), t);
    await p.screenshot({ path: path.join(out, (muestras ? 't' + t : String(n).padStart(4, '0')) + '.png') });
    n++;
  }
  await b.close();
  console.log(n + ' fotogramas; errores: ' + (errores.join('; ') || 'ninguno'));
})();
