// Tests del popup (ratón y táctil). Ejecutar con:  npm test
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { montar, esperar } = require('./helpers');

function click(w, el) {
  el.dispatchEvent(new w.MouseEvent('click', { bubbles: true, cancelable: true }));
}
function hover(w, el) {
  el.dispatchEvent(new w.MouseEvent('mouseover', { bubbles: true }));
}
function out(w, el, hacia) {
  el.dispatchEvent(new w.MouseEvent('mouseout', { bubbles: true, relatedTarget: hacia || null }));
}
function popup(w) { return w.document.querySelector('.fuentes-popup'); }
function visible(w) { return !!popup(w) && popup(w).style.display === 'block'; }

const HTML = '<div id="qa">La arteria femoral y la aorta. <p id="fuera">texto</p></div>';

test('al pasar el ratón se abre con hasta 3 fragmentos por fuente, página y resaltado', async () => {
  const w = await montar(HTML);
  hover(w, w.document.querySelector('.fuentes-term'));
  await esperar(200);
  assert.ok(visible(w));
  const p = popup(w);
  assert.equal(p.querySelector('.fuentes-cab').textContent, 'arteria femoral');
  assert.deepEqual(Array.from(p.querySelectorAll('.fuentes-nombre')).map((e) => e.textContent),
    ['Apuntes', 'Resumen']);
  assert.equal(p.querySelectorAll('.fuentes-fuente')[0].querySelectorAll('.fuentes-frag').length, 3);
  const donde = Array.from(p.querySelectorAll('.fuentes-donde')).map((e) => e.textContent);
  assert.deepEqual(donde, ['Apuntes, p. 3', 'Apuntes, p. xii', 'Apuntes, p. 5', 'Resumen, p. 1']);
  // Término resaltado (también el sinónimo) y HTML del fragmento escapado.
  const marcas = Array.from(p.querySelectorAll('mark')).map((e) => e.textContent);
  assert.deepEqual(marcas, ['arteria femoral', 'A. FEMORAL', 'arteria femoral']);
  assert.match(p.innerHTML, /&lt;inguinal&gt;/);
  // Sin pycmd (móvil) no hay enlaces para abrir el PDF ni acciones extra.
  assert.equal(p.querySelectorAll('.fuentes-abrible').length, 0);
  assert.equal(p.querySelectorAll('.fuentes-accion').length, 0);
});

test('se cierra al salir el ratón, pero no al pasar al popup', async () => {
  const w = await montar(HTML);
  const term = w.document.querySelector('.fuentes-term');
  hover(w, term);
  await esperar(200);
  out(w, term, popup(w));
  await esperar(400);
  assert.ok(visible(w), 'sigue abierto al entrar en el popup');
  out(w, popup(w), w.document.getElementById('fuera'));
  await esperar(400);
  assert.ok(!visible(w));
});

test('táctil: tocar abre, tocar dentro no cierra, tocar fuera cierra', async () => {
  const w = await montar(HTML);
  w.Fuentes.forceTouch(true);
  const term = w.document.querySelector('.fuentes-term');
  hover(w, term); // en táctil el mouseover emulado se ignora
  await esperar(200);
  assert.ok(!visible(w));
  click(w, term);
  await esperar(10);
  assert.ok(visible(w));
  click(w, popup(w).querySelector('.fuentes-texto'));
  assert.ok(visible(w));
  click(w, w.document.getElementById('fuera'));
  assert.ok(!visible(w));
});

test('carga perezosa con "Cargando…" y error amable si falta el archivo', async () => {
  const w = await montar(HTML, { datos: { '_fuentes_t_aorta.json': null } });
  w.Fuentes.forceTouch(true);
  click(w, w.document.querySelectorAll('.fuentes-term')[1]);
  await esperar(20);
  assert.match(popup(w).textContent, /Sincroniza los medios/);
});

test('precarga los términos de la tarjeta (popup instantáneo)', async () => {
  const w = await montar(HTML);
  await esperar(60);
  assert.ok(w.__peticiones.includes('_fuentes_t_arteria-femoral.json'));
  w.Fuentes.forceTouch(true);
  const t0 = Date.now();
  click(w, w.document.querySelector('.fuentes-term'));
  assert.ok(visible(w), 'abre de forma síncrona desde la caché');
  assert.ok(Date.now() - t0 < 100);
});

test('escritorio con pycmd: clic en un fragmento abre el PDF en su página', async () => {
  const mensajes = [];
  const w = await montar(HTML, { pycmd: (m, cb) => { mensajes.push(m); if (cb) cb({ ok: true, fuentes: [] }); } });
  w.Fuentes.forceTouch(true);
  click(w, w.document.querySelector('.fuentes-term'));
  await esperar(10);
  const frag = popup(w).querySelectorAll('.fuentes-abrible')[1];
  click(w, frag);
  assert.deepEqual(JSON.parse(mensajes[0].replace(/^fuentes:/, '')), { cmd: 'abrir', fuente: 1, pagina: 4 });
  // Acción "Más en mis fuentes" disponible en escritorio.
  const boton = popup(w).querySelector('.fuentes-accion');
  assert.equal(boton.textContent, 'Más en mis fuentes');
  click(w, boton);
  assert.equal(JSON.parse(mensajes[1].replace(/^fuentes:/, '')).cmd, 'mas');
});

test('acciones registrables (preparado para un futuro "Explicar")', async () => {
  const w = await montar(HTML);
  w.Fuentes.registrarAccion({
    id: 'explicar', etiqueta: 'Explicar',
    disponible: () => true,
    ejecutar: (ctx, mostrar) => mostrar('<p id="exp">Explicación de ' + ctx.termino.t + '</p>')
  });
  w.Fuentes.forceTouch(true);
  click(w, w.document.querySelector('.fuentes-term'));
  await esperar(10);
  click(w, popup(w).querySelector('[data-accion="explicar"]'));
  assert.equal(w.document.getElementById('exp').textContent, 'Explicación de arteria femoral');
});

test('Escape cierra y una tarjeta nueva cierra el popup', async () => {
  const w = await montar(HTML);
  w.Fuentes.forceTouch(true);
  click(w, w.document.querySelector('.fuentes-term'));
  await esperar(10);
  w.document.dispatchEvent(new w.KeyboardEvent('keydown', { keyCode: 27 }));
  assert.ok(!visible(w));
  click(w, w.document.querySelector('.fuentes-term'));
  await esperar(10);
  w.Fuentes.run();
  assert.ok(!visible(w));
});

test('interfaz en inglés cuando el glosario exportado lo indica', async () => {
  const g = JSON.parse(JSON.stringify(require('./helpers').GLOSARIO));
  g.ajustes.idioma = 'en';
  const w = await montar(HTML, { datos: { '_fuentes_glosario.json': g, '_fuentes_t_aorta.json': null },
    pycmd: (m, cb) => cb && cb({ ok: false }) });
  assert.equal(w.Fuentes.idioma(), 'en');
  w.Fuentes.forceTouch(true);
  click(w, w.document.querySelector('.fuentes-term'));
  await esperar(10);
  assert.equal(popup(w).querySelector('.fuentes-accion').textContent, 'More from my sources');
  assert.equal(popup(w).querySelector('.fuentes-abrible').getAttribute('title'), 'Open the PDF at this page');
});
