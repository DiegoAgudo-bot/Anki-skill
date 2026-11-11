// Utilidades para cargar fuentes.js en un DOM simulado (jsdom) desde Node.
'use strict';
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const RAIZ = path.join(__dirname, '..', '..');
const CODIGO = fs.readFileSync(path.join(RAIZ, 'fuentes', 'web', 'fuentes.js'), 'utf8');
const CASOS = JSON.parse(fs.readFileSync(path.join(RAIZ, 'tests', 'casos_matching.json'), 'utf8'));

// Glosario y datos de ejemplo (texto inventado).
const GLOSARIO = {
  version: 1,
  ajustes: { subrayado: true, fragmentos: 3, soloPrimera: true },
  terminos: [
    { t: 'arteria femoral', s: ['a. femoral'], f: '_fuentes_t_arteria-femoral.json' },
    { t: 'arteria femoral profunda', s: [], f: '_fuentes_t_arteria-femoral-profunda.json' },
    { t: 'nervio ciático', s: ['ciático'], f: '_fuentes_t_nervio-ciatico.json' },
    { t: 'aorta', s: [], f: '_fuentes_t_aorta.json' },
    { t: 'vena cava', s: [], f: '_fuentes_t_vena-cava.json' }
  ]
};
const TERMINO = {
  t: 'arteria femoral',
  fuentes: [
    { id: 1, nombre: 'Apuntes', fragmentos: [
      { p: 3, x: 'La arteria femoral pasa bajo el ligamento <inguinal>.' },
      { p: 4, e: 'xii', x: 'Otra mención de la A. FEMORAL.' },
      { p: 5, x: 'Tercera.' }, { p: 6, x: 'Cuarta (no debe salir).' }
    ] },
    { id: 2, nombre: 'Resumen', fragmentos: [{ p: 1, x: 'Resumen de la arteria femoral.' }] }
  ]
};

/**
 * Crea un DOM con el HTML de la tarjeta, carga el script y espera a que
 * subraye. `datos` mapea nombre de archivo -> JSON (null = error de carga).
 */
function montar(html, opciones) {
  opciones = opciones || {};
  const dom = new JSDOM('<!doctype html><html><body>' + html + '</body></html>', {
    runScripts: 'outside-only', pretendToBeVisual: true
  });
  const w = dom.window;
  const datos = Object.assign({ '_fuentes_glosario.json': GLOSARIO,
    '_fuentes_t_arteria-femoral.json': TERMINO }, opciones.datos || {});
  w.__peticiones = [];
  if (opciones.pycmd) w.pycmd = opciones.pycmd;
  // Proveedor de datos en memoria (en Anki se usa fetch/XHR).
  w.eval('window.Fuentes = { };');
  w.__datos = datos;
  w.eval(CODIGO);
  w.Fuentes.dataProvider = function (nombre, cb) {
    w.__peticiones.push(nombre);
    const d = w.__datos[nombre];
    setTimeout(function () { d ? cb(null, d) : cb(new Error('no existe')); }, 0);
  };
  return new Promise((resolve) => setTimeout(() => {
    w.Fuentes.run();
    setTimeout(() => resolve(w), 20);
  }, 0));
}

function subrayados(w) {
  return Array.from(w.document.querySelectorAll('.fuentes-term')).map((e) => e.textContent);
}

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

module.exports = { CODIGO, CASOS, GLOSARIO, TERMINO, montar, subrayados, esperar, JSDOM };
