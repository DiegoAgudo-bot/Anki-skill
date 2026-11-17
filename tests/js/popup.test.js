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
function popup(w) { return w.document.querySelector('.pagewise-popup'); }
function visible(w) { return !!popup(w) && popup(w).style.display === 'block'; }

const HTML = '<div id="qa">La arteria femoral y la aorta. <p id="fuera">texto</p></div>';

test('al pasar el ratón se abre con hasta 3 fragmentos por fuente, página y resaltado', async () => {
  const w = await montar(HTML);
  hover(w, w.document.querySelector('.pagewise-term'));
  await esperar(200);
  assert.ok(visible(w));
  const p = popup(w);
  assert.equal(p.querySelector('.pagewise-cab').textContent, 'arteria femoral');
  assert.deepEqual(Array.from(p.querySelectorAll('.pagewise-nombre')).map((e) => e.textContent),
    ['Apuntes', 'Resumen']);
  assert.equal(p.querySelectorAll('.pagewise-fuente')[0].querySelectorAll('.pagewise-frag').length, 3);
  const donde = Array.from(p.querySelectorAll('.pagewise-donde')).map((e) => e.textContent);
  assert.deepEqual(donde, ['Apuntes, p. 3', 'Apuntes, p. xii', 'Apuntes, p. 5', 'Resumen, p. 1']);
  // Término resaltado (también el sinónimo) y HTML del fragmento escapado.
  const marcas = Array.from(p.querySelectorAll('mark')).map((e) => e.textContent);
  assert.deepEqual(marcas, ['arteria femoral', 'A. FEMORAL', 'arteria femoral']);
  assert.match(p.innerHTML, /&lt;inguinal&gt;/);
  // Sin pycmd (móvil) no hay enlaces para abrir el PDF ni acciones extra.
  assert.equal(p.querySelectorAll('.pagewise-abrible').length, 0);
  assert.equal(p.querySelectorAll('.pagewise-accion').length, 0);
});

test('se cierra al salir el ratón, pero no al pasar al popup', async () => {
  const w = await montar(HTML);
  const term = w.document.querySelector('.pagewise-term');
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
  w.Pagewise.forceTouch(true);
  const term = w.document.querySelector('.pagewise-term');
  hover(w, term); // en táctil el mouseover emulado se ignora
  await esperar(200);
  assert.ok(!visible(w));
  click(w, term);
  await esperar(10);
  assert.ok(visible(w));
  click(w, popup(w).querySelector('.pagewise-texto'));
  assert.ok(visible(w));
  click(w, w.document.getElementById('fuera'));
  assert.ok(!visible(w));
});

test('carga perezosa con "Cargando…" y error amable si falta el archivo', async () => {
  const w = await montar(HTML, { datos: { '_pagewise_t_aorta.json': null } });
  w.Pagewise.forceTouch(true);
  click(w, w.document.querySelectorAll('.pagewise-term')[1]);
  await esperar(20);
  assert.match(popup(w).textContent, /Sincroniza los medios/);
});

test('precarga los términos de la tarjeta (popup instantáneo)', async () => {
  const w = await montar(HTML);
  await esperar(60);
  assert.ok(w.__peticiones.includes('_pagewise_t_arteria-femoral.json'));
  w.Pagewise.forceTouch(true);
  const t0 = Date.now();
  click(w, w.document.querySelector('.pagewise-term'));
  assert.ok(visible(w), 'abre de forma síncrona desde la caché');
  assert.ok(Date.now() - t0 < 100);
});

test('escritorio con pycmd: clic en un fragmento abre el PDF en su página', async () => {
  const mensajes = [];
  const w = await montar(HTML, { pycmd: (m, cb) => { mensajes.push(m); if (cb) cb({ ok: true, fuentes: [] }); } });
  w.Pagewise.forceTouch(true);
  click(w, w.document.querySelector('.pagewise-term'));
  await esperar(10);
  const frag = popup(w).querySelectorAll('.pagewise-abrible')[1];
  click(w, frag);
  // Además de la página, manda el texto resaltado en ese fragmento para que
  // el visor lo marque también en el PDF.
  const msg = JSON.parse(mensajes[0].replace(/^pagewise:/, ''));
  assert.equal(msg.cmd, 'abrir');
  assert.equal(msg.fuente, 1);
  assert.equal(msg.pagina, 4);
  assert.equal(msg.q, frag.querySelector('mark').textContent);
  assert.equal(msg.frase, true);
  // Acción "Más en mis fuentes" disponible en escritorio.
  const boton = popup(w).querySelector('.pagewise-accion');
  assert.equal(boton.textContent, 'Más en mis fuentes');
  click(w, boton);
  assert.equal(JSON.parse(mensajes[1].replace(/^pagewise:/, '')).cmd, 'mas');
});

test('acciones registrables (preparado para un futuro "Explicar")', async () => {
  const w = await montar(HTML);
  w.Pagewise.registrarAccion({
    id: 'explicar', etiqueta: 'Explicar',
    disponible: () => true,
    ejecutar: (ctx, mostrar) => mostrar('<p id="exp">Explicación de ' + ctx.termino.t + '</p>')
  });
  w.Pagewise.forceTouch(true);
  click(w, w.document.querySelector('.pagewise-term'));
  await esperar(10);
  click(w, popup(w).querySelector('[data-accion="explicar"]'));
  assert.equal(w.document.getElementById('exp').textContent, 'Explicación de arteria femoral');
});

test('Escape cierra y una tarjeta nueva cierra el popup', async () => {
  const w = await montar(HTML);
  w.Pagewise.forceTouch(true);
  click(w, w.document.querySelector('.pagewise-term'));
  await esperar(10);
  w.document.dispatchEvent(new w.KeyboardEvent('keydown', { keyCode: 27 }));
  assert.ok(!visible(w));
  click(w, w.document.querySelector('.pagewise-term'));
  await esperar(10);
  w.Pagewise.run();
  assert.ok(!visible(w));
});

test('interfaz en inglés cuando el glosario exportado lo indica', async () => {
  const g = JSON.parse(JSON.stringify(require('./helpers').GLOSARIO));
  g.ajustes.idioma = 'en';
  const w = await montar(HTML, { datos: { '_pagewise_glosario.json': g, '_pagewise_t_aorta.json': null },
    pycmd: (m, cb) => cb && cb({ ok: false }) });
  assert.equal(w.Pagewise.idioma(), 'en');
  w.Pagewise.forceTouch(true);
  click(w, w.document.querySelector('.pagewise-term'));
  await esperar(10);
  assert.equal(popup(w).querySelector('.pagewise-accion').textContent, 'More from my sources');
  assert.equal(popup(w).querySelector('.pagewise-abrible').getAttribute('title'), 'Open the PDF at this page');
});

test('textoResaltado: una expresión se busca como frase; varias palabras, sueltas', async () => {
  const w = await montar(HTML);
  const d = w.document.createElement('div');
  d.innerHTML = 'La <mark>Arteria  femoral</mark> y otra vez la <mark>arteria femoral</mark>.';
  assert.deepEqual({ ...w.Pagewise.textoResaltado(d) }, { q: 'Arteria femoral', frase: true });
  d.innerHTML = 'El <mark>nervio</mark> y el <mark>muslo</mark> y el <mark>Nervio</mark>.';
  assert.deepEqual({ ...w.Pagewise.textoResaltado(d) }, { q: 'nervio muslo', frase: false });
  d.innerHTML = 'Sin nada resaltado.';
  assert.deepEqual({ ...w.Pagewise.textoResaltado(d) }, { q: '', frase: true });
});

test('Explicar: pide a Python con el término y la tarjeta, y pinta la respuesta al llegar', async () => {
  const mensajes = [];
  const w = await montar(HTML, { pycmd: (m, cb) => {
    mensajes.push(JSON.parse(m.replace(/^pagewise:/, '')));
    if (cb) cb(mensajes[mensajes.length - 1].cmd === 'explicar' ? { ok: true, pendiente: 7 } : { ok: true, fuentes: [] });
  } });
  w.Pagewise.forceTouch(true);
  click(w, w.document.querySelector('.pagewise-term'));
  await esperar(10);
  const boton = Array.from(popup(w).querySelectorAll('.pagewise-accion')).find((b) => b.textContent === 'Explicar');
  assert.ok(boton, 'botón Explicar en escritorio');
  click(w, boton);
  const msg = mensajes.find((m) => m.cmd === 'explicar');
  assert.equal(msg.termino, 'arteria femoral');
  assert.ok(msg.variantes.includes('arteria femoral'));
  assert.equal(typeof msg.tarjeta, 'string');
  assert.match(popup(w).textContent, /Leyendo tus fuentes/);
  w.Pagewise.__explicado(7, { ok: true, autor: 'ChatGPT', texto: 'Primer <b>párrafo</b>.\n\nSegundo (Libro, p. 4).' });
  const ps = popup(w).querySelectorAll('.pagewise-explicacion p');
  assert.equal(ps.length, 2);
  assert.equal(ps[0].textContent, 'Primer <b>párrafo</b>.');   // escapado, no HTML
  assert.match(popup(w).textContent, /Explicación de ChatGPT a partir de tus fuentes\. Puede equivocarse/);
});

test('Explicar: sin Pro o sin clave, mensaje claro', async () => {
  let respuesta = { ok: false, motivo: 'pro' };
  const w = await montar(HTML, { pycmd: (m, cb) => { if (cb) cb(m.indexOf('"explicar"') > 0 ? respuesta : { ok: true, fuentes: [] }); } });
  w.Pagewise.forceTouch(true);
  click(w, w.document.querySelector('.pagewise-term'));
  await esperar(10);
  const boton = () => Array.from(popup(w).querySelectorAll('.pagewise-accion')).find((b) => b.textContent === 'Explicar');
  click(w, boton());
  assert.match(popup(w).textContent, /Pagewise Pro/);
  respuesta = { ok: false, motivo: 'clave' };
  click(w, w.document.body);
  click(w, w.document.querySelector('.pagewise-term'));
  await esperar(10);
  click(w, boton());
  assert.match(popup(w).textContent, /clave de la API/);
});

test('Explicar no aparece en el móvil (sin pycmd)', async () => {
  const w = await montar(HTML);
  w.Pagewise.forceTouch(true);
  click(w, w.document.querySelector('.pagewise-term'));
  await esperar(10);
  assert.ok(!Array.from(popup(w).querySelectorAll('.pagewise-accion')).some((b) => b.textContent === 'Explicar'));
});
