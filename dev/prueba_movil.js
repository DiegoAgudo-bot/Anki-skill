// Prueba "como en el móvil" con Chromium sin pantalla (Playwright).
//
//   node dev/prueba_movil.js
//
// Simula lo que hacen AnkiDroid y AnkiMobile: la tarjeta se renderiza con la
// plantilla que lleva el snippet de Pagewise y se sirve desde la carpeta de
// medios (aquí, una carpeta temporal generada con el exportador REAL).
// Comprueba: toque, cierre al tocar fuera, "Fuente, p. N", tiempo de apertura,
// WebView antiguo (sin fetch ni String.normalize), modo noche y cambio de
// tarjeta sin recargar la página (AnkiMobile). Guarda capturas en
// dev/capturas/ para revisarlas.
'use strict';
const { execFileSync } = require('child_process');
const fs = require('fs');
const http = require('http');
const os = require('os');
const path = require('path');
const { chromium, devices } = require('playwright');

const RAIZ = path.join(__dirname, '..');
const CAPTURAS = path.join(__dirname, 'capturas');
const SNIPPET = '\n<!-- PAGEWISE:INICIO -->\n<link rel="stylesheet" href="_pagewise.css">\n' +
  '<script src="_pagewise.js"></script>\n<!-- PAGEWISE:FIN -->';

// Tarjetas tal y como quedarían tras renderizar la plantilla (con el snippet).
const ANVERSO = '<style>.card{font-family:arial;font-size:20px;text-align:center}</style>' +
  '<div class="card">¿Qué vaso nace del <b>ventrículo izquierdo</b>? Pista: no es la arteria femoral.' +
  '<br><span class="cloze" data-cloze="aorta">[...]</span></div>' + SNIPPET;
const REVERSO = ANVERSO.replace('</div>', '<hr id="answer">La <span class="cloze">aorta</span>; ' +
  'el nervio ciatico va por detrás del muslo.</div>');
const OTRA = '<div class="card">El bíceps braquial flexiona el codo; el cuadriceps extiende la rodilla.</div>' + SNIPPET;

function pagina(qa, claseBody, antes) {
  return '<!doctype html><html><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1">' + (antes || '') +
    '</head><body class="' + (claseBody || '') + '"><div id="qa">' + qa + '</div></body></html>';
}

function servir(dir) {
  const tipos = { '.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json' };
  const srv = http.createServer((req, res) => {
    const f = path.join(dir, decodeURIComponent(req.url.split('?')[0]));
    if (!f.startsWith(dir) || !fs.existsSync(f)) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': tipos[path.extname(f)] || 'application/octet-stream' });
    res.end(fs.readFileSync(f));
  });
  return new Promise((r) => srv.listen(0, '127.0.0.1', () => r(srv)));
}

let fallos = 0;
function comprobar(cond, texto) {
  console.log((cond ? '  ✓ ' : '  ✗ ') + texto);
  if (!cond) fallos++;
}

async function abrirTarjeta(ctx, base, archivo, html) {
  fs.writeFileSync(path.join(base.dir, archivo), html);
  const p = await ctx.newPage();
  const errores = [];
  p.on('pageerror', (e) => errores.push(e.message));
  await p.goto(base.url + archivo);
  await p.waitForTimeout(300);
  return { p, errores };
}

const terminos = (p) => p.$$eval('.pagewise-term', (es) => es.map((e) => e.textContent));
const popupVisible = (p) => p.$eval('.pagewise-popup', (e) => e.style.display === 'block').catch(() => false);

(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'pagewise-medios-'));
  execFileSync('python3', [path.join(RAIZ, 'dev', 'generar_demo.py'), dir], { stdio: 'inherit' });
  fs.mkdirSync(CAPTURAS, { recursive: true });
  const srv = await servir(dir);
  const base = { dir, url: 'http://127.0.0.1:' + srv.address().port + '/' };
  const navegador = await chromium.launch();

  for (const [nombre, disp] of [['Android (AnkiDroid)', devices['Pixel 7']], ['iPhone (AnkiMobile)', devices['iPhone 13']]]) {
    console.log('\n' + nombre);
    const ctx = await navegador.newContext({ ...disp });
    let { p, errores } = await abrirTarjeta(ctx, base, 'anverso.html', pagina(ANVERSO));
    comprobar(JSON.stringify(await terminos(p)) === JSON.stringify(['ventrículo izquierdo', 'arteria femoral']),
      'anverso subrayado sin tocar el cloze: ' + (await terminos(p)).join(', '));
    comprobar(await p.$eval('.cloze', (e) => e.innerHTML === '[...]'), 'el hueco del cloze queda intacto');
    // Medimos dentro de la página: del toque a que el popup tiene contenido.
    await p.waitForTimeout(150); // deja terminar la precarga
    const ms = await p.evaluate(() => {
      const t0 = performance.now();
      const t = document.querySelector('.pagewise-term');
      t.dispatchEvent(new TouchEvent('touchstart', { bubbles: true }));
      t.click();
      const pop = document.querySelector('.pagewise-popup');
      return pop && pop.querySelector('.pagewise-frag') ? performance.now() - t0 : -1;
    });
    comprobar(ms >= 0 && ms < 100, 'popup con fragmentos en ' + ms.toFixed(1) + ' ms (< 100 ms)');
    await p.touchscreen.tap(20, disp.viewport.height - 20); // cerrar (el popup tapa la línea de abajo)
    await p.tap('.pagewise-term >> nth=1');
    await p.waitForTimeout(200);
    const donde = await p.$$eval('.pagewise-donde', (es) => es.map((e) => e.textContent));
    comprobar(donde.length > 0 && donde.every((d) => /, p\. \d+$/.test(d)), 'muestra "Fuente, p. N": ' + donde[0]);
    comprobar((await p.$$('.pagewise-abrible')).length === 0, 'sin enlaces al PDF (no hay visor en el móvil)');
    const caja = await p.$eval('.pagewise-popup', (e) => { const r = e.getBoundingClientRect(); return [r.left, r.right, innerWidth]; });
    comprobar(caja[0] >= 0 && caja[1] <= caja[2], 'el popup cabe en la pantalla');
    await p.waitForTimeout(200);
    await p.screenshot({ path: path.join(CAPTURAS, nombre.split(' ')[0].toLowerCase() + '-popup.png') });
    await p.tap('.pagewise-popup .pagewise-texto');
    comprobar(await popupVisible(p), 'tocar dentro del popup no lo cierra');
    await p.touchscreen.tap(20, disp.viewport.height - 20);
    await p.waitForTimeout(50);
    comprobar(!(await popupVisible(p)), 'tocar fuera lo cierra');
    comprobar(errores.length === 0, 'sin errores de JavaScript ' + (errores.join('; ') || ''));

    // Reverso y cambio de tarjeta sin recargar (AnkiMobile reutiliza la página).
    ({ p, errores } = await abrirTarjeta(ctx, base, 'reverso.html', pagina(REVERSO)));
    comprobar((await terminos(p)).includes('aorta') && (await terminos(p)).includes('nervio ciatico'),
      'reverso: subraya el cloze revelado y "ciatico" sin tilde');
    await p.evaluate((html) => {
      const qa = document.getElementById('qa');
      qa.innerHTML = html;
      // Como hacen los clientes: volver a ejecutar los <script> de la tarjeta.
      qa.querySelectorAll('script').forEach((s) => {
        const n = document.createElement('script');
        n.src = s.getAttribute('src');
        s.parentNode.replaceChild(n, s);
      });
    }, OTRA);
    await p.waitForTimeout(300);
    comprobar(JSON.stringify(await terminos(p)) === JSON.stringify(['bíceps braquial', 'cuadriceps']),
      'tarjeta siguiente en la misma página: ' + (await terminos(p)).join(', '));
    comprobar(await p.evaluate(() => document.querySelectorAll('.pagewise-popup').length <= 1), 'un solo popup en la página');
    await ctx.close();
  }

  console.log('\nWebView antiguo (sin fetch ni String.prototype.normalize) + modo noche de AnkiDroid');
  const ctx = await navegador.newContext({ ...devices['Galaxy S9+'] });
  const viejo = '<script>delete window.fetch; window.fetch = undefined; String.prototype.normalize = undefined;</script>';
  const { p, errores } = await abrirTarjeta(ctx, base, 'viejo.html', pagina(REVERSO, 'night_mode', viejo));
  comprobar((await terminos(p)).includes('ventrículo izquierdo'), 'carga por XMLHttpRequest y normaliza con la tabla propia');
  await p.tap('.pagewise-term');
  await p.waitForTimeout(200);
  comprobar(await p.$eval('.pagewise-popup', (e) => getComputedStyle(e).backgroundColor === 'rgb(36, 41, 47)'), 'popup en modo noche');
  await p.screenshot({ path: path.join(CAPTURAS, 'android-noche.png') });
  comprobar(errores.length === 0, 'sin errores de JavaScript ' + (errores.join('; ') || ''));

  console.log('\nSin datos (el móvil aún no ha sincronizado los medios)');
  fs.renameSync(path.join(dir, '_pagewise_glosario.json'), path.join(dir, 'x.json'));
  const r = await abrirTarjeta(ctx, base, 'sin.html', pagina(ANVERSO));
  comprobar((await terminos(r.p)).length === 0 && r.errores.length === 0, 'la tarjeta se ve normal, sin errores');

  await navegador.close();
  srv.close();
  fs.rmSync(dir, { recursive: true, force: true });
  console.log(fallos ? '\n' + fallos + ' comprobaciones fallidas' : '\nTodo correcto. Capturas en dev/capturas/');
  process.exit(fallos ? 1 : 0);
})();
