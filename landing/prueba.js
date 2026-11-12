// Prueba de la landing con Chromium (Playwright):  node landing/prueba.js
// Comprueba que carga sin errores ni desbordes, que la demo subraya y abre el
// popup, y los estados de la lista de espera (sin conectar, fallo y éxito).
'use strict';
const { execFileSync } = require('child_process');
const os = require('os');
const path = require('path');
const { chromium } = require('playwright');

let fallos = 0;
const ok = (c, t) => { console.log((c ? '  ✓ ' : '  ✗ ') + t); if (!c) fallos++; };

(async () => {
  // Copia de prueba con la lista conectada a un servicio ficticio.
  const conLista = path.join(os.tmpdir(), 'fuentes-landing-con-lista.html');
  execFileSync('python3', [path.join(__dirname, 'build.py'), conLista, 'https://formularios.test/f/abc'], { stdio: 'ignore' });
  const b = await chromium.launch();

  for (const [w, h, nombre] of [[1280, 900, 'escritorio'], [390, 800, 'móvil']]) {
    console.log('\n' + nombre);
    const p = await b.newPage({ viewport: { width: w, height: h } });
    const errores = []; p.on('pageerror', (e) => errores.push(e.message));
    await p.goto('file://' + path.join(__dirname, 'index.html'));
    await p.waitForTimeout(1200);
    ok(errores.length === 0, 'sin errores de JavaScript ' + errores.join('; '));
    ok(await p.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), 'sin desbordes horizontales');
    ok((await p.$$('#escena .t')).length === 3, 'la tarjeta de la portada subraya 3 términos');
    ok(await p.$eval('.fx-pop', (e) => !e.hidden && /p\. \d+/.test(e.textContent)), 'popup abierto con fragmento y página');
    await p.fill('#prueba-a', 'el CIATICO y la a. femoral');
    ok(JSON.stringify(await p.$$eval('#salida-a .t', (e) => e.map((x) => x.textContent))) === '["CIATICO","a. femoral"]', 'la zona de pruebas subraya lo que escribes');
    await p.click('#ejemplos button');
    ok((await p.$$('#salida-a .t')).length >= 2, 'las frases de ejemplo rellenan la zona de pruebas');
    ok(await p.$$eval('nav a[href^="#"]', (as) => as.every((a) => document.querySelector(a.getAttribute('href')))), 'todos los enlaces del menú llevan a una sección');
    // Lista sin conectar: no finge.
    await p.fill('#correo-a', 'no-es-un-correo'); await p.click('#lista-a button');
    ok(/correo válido/.test(await p.textContent('#lista-a .fx-estado')), 'correo inválido: pide corregirlo');
    await p.fill('#correo-a', 'ana@correo.es'); await p.click('#lista-a button');
    ok(/todavía no está abierta/.test(await p.textContent('#lista-a .fx-estado')), 'sin servicio configurado: avisa, no finge');
    await p.close();
  }

  console.log('\nlista de espera conectada');
  const p = await b.newPage();
  let recibido = null, responder = 500;
  await p.route('https://formularios.test/**', (r) => {
    recibido = r.request().postDataJSON();
    r.fulfill({ status: responder, contentType: 'application/json', body: '{}' });
  });
  await p.goto('file://' + conLista);
  await p.fill('#correo-final', 'ana@correo.es'); await p.click('#lista-final button');
  await p.waitForFunction(() => /No se pudo/.test(document.querySelector('#lista-final .fx-estado').textContent));
  ok(true, 'si el servicio falla: lo dice y deja reintentar');
  responder = 200;
  await p.click('#lista-final button');
  await p.waitForFunction(() => /Apuntado a la lista/.test(document.querySelector('#lista-final .fx-estado').textContent));
  ok(recibido && recibido.email === 'ana@correo.es', 'envía el correo al servicio y confirma');

  await b.close();
  console.log(fallos ? '\n' + fallos + ' comprobaciones fallidas' : '\nTodo correcto.');
  process.exit(fallos ? 1 : 0);
})();
