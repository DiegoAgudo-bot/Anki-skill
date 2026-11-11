// Tests del matcher y del subrayado en el DOM. Ejecutar con:  npm test
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const acorn = require('acorn');
const { CODIGO, CASOS, montar, subrayados, esperar, JSDOM } = require('./helpers');

function fuentesSinDom() {
  const dom = new JSDOM('<!doctype html><body></body>', { runScripts: 'outside-only' });
  dom.window.eval('window.Fuentes = {}; window.Fuentes.dataProvider = function(n, cb){ cb(new Error("x")); };');
  dom.window.eval(CODIGO);
  return dom.window.Fuentes;
}

test('el script es ES5 válido (compatibilidad con WebViews antiguos)', () => {
  assert.doesNotThrow(() => acorn.parse(CODIGO, { ecmaVersion: 5 }));
});

test('casos compartidos con Python (tests/casos_matching.json)', async (t) => {
  const F = fuentesSinDom();
  const variantes = [];
  CASOS.glosario.forEach((term, i) => {
    [term.term].concat(term.synonyms).forEach((v) => variantes.push([v, i]));
  });
  const m = new F.Matcher(variantes);
  for (const caso of CASOS.casos) {
    await t.test(caso.nombre, () => {
      const obtenido = Array.from(m.buscar(caso.texto)).map(([a, b, i]) => ({
        termino: CASOS.glosario[i].term, texto: caso.texto.slice(a, b)
      }));
      assert.deepEqual(obtenido, caso.esperado);
    });
  }
});

test('subraya términos sin tocar etiquetas ni atributos', async () => {
  const html = '<div id="qa"><p class="aorta" title="arteria femoral">La <b>arteria femoral</b> y la ' +
    '<img src="aorta.png" alt="aorta"> <a href="#">aorta</a> aorta.</p></div>';
  const w = await montar(html);
  assert.deepEqual(subrayados(w), ['arteria femoral', 'aorta']);
  const p = w.document.querySelector('p');
  assert.equal(p.className, 'aorta');
  assert.equal(p.getAttribute('title'), 'arteria femoral');
  assert.equal(w.document.querySelector('img').getAttribute('alt'), 'aorta');
  assert.equal(w.document.querySelector('a').innerHTML, 'aorta', 'no se subraya dentro de enlaces');
  // El texto visible no cambia.
  assert.equal(p.textContent, 'La arteria femoral y la  aorta aorta.');
});

test('frase más larga, sinónimos, tildes y varias palabras con nbsp', async () => {
  const w = await montar('<div id="qa">ARTERIA&nbsp;FEMORAL PROFUNDA, el ciatico y la Vena  Cava</div>');
  assert.deepEqual(subrayados(w), ['ARTERIA FEMORAL PROFUNDA', 'ciatico', 'Vena  Cava']);
});

test('solo la primera aparición de cada término', async () => {
  const w = await montar('<div id="qa">aorta, aorta y <i>aorta</i></div>');
  assert.deepEqual(subrayados(w), ['aorta']);
});

test('no toca el cloze en el anverso pero sí en el reverso', async () => {
  const anverso = '<div id="qa">La <span class="cloze" data-cloze="aorta">[...]</span> sale del ' +
    'ventrículo; ver <span class="cloze">[aorta]</span> y la vena cava</div>';
  let w = await montar(anverso);
  assert.deepEqual(subrayados(w), ['vena cava']);
  assert.equal(w.document.querySelectorAll('.cloze')[1].innerHTML, '[aorta]');
  assert.equal(w.document.querySelector('.cloze').getAttribute('data-cloze'), 'aorta');

  const reverso = '<div id="qa">pregunta<hr id="answer">La <span class="cloze">aorta</span> sale.</div>';
  w = await montar(reverso);
  assert.deepEqual(subrayados(w), ['aorta']);
  assert.equal(w.document.querySelector('.cloze .fuentes-term').textContent, 'aorta');
});

test('no rompe audio, MathJax ni scripts', async () => {
  const html = '<div id="qa">[sound:aorta.mp3] <a class="replay-button">aorta</a> ' +
    '\\(aorta\\) <script>var aorta = 1;</script><span data-fuentes-skip>aorta</span> ' +
    '<code>aorta</code> fin</div>';
  const w = await montar(html);
  assert.deepEqual(subrayados(w), []);
  assert.match(w.document.getElementById('qa').innerHTML, /\[sound:aorta\.mp3\]/);
  assert.equal(w.document.querySelector('script').textContent, 'var aorta = 1;');
});

test('ejecutar dos veces no duplica (plantilla + add-on o AnkiMobile)', async () => {
  const w = await montar('<div id="qa">La aorta y la arteria femoral</div>');
  w.eval(CODIGO); // segunda carga del script = vuelve a aplicar
  w.Fuentes.run();
  await esperar(20);
  assert.deepEqual(subrayados(w), ['aorta', 'arteria femoral']);
  assert.equal(w.document.querySelectorAll('.fuentes-term .fuentes-term').length, 0);
});

test('términos sin archivo de datos no se subrayan', async () => {
  const datos = { '_fuentes_glosario.json': { terminos: [{ t: 'aorta', s: [] }] } };
  const w = await montar('<div id="qa">aorta</div>', { datos });
  assert.deepEqual(subrayados(w), []);
});

test('sin glosario (móvil sin sincronizar) la tarjeta queda igual y reintenta', async () => {
  const w = await montar('<div id="qa">aorta</div>', { datos: { '_fuentes_glosario.json': null } });
  assert.equal(w.document.getElementById('qa').innerHTML, 'aorta');
  // Llega el glosario (tras sincronizar) y la siguiente tarjeta ya subraya.
  w.__datos['_fuentes_glosario.json'] = require('./helpers').GLOSARIO;
  w.Fuentes.run();
  await esperar(20);
  assert.deepEqual(subrayados(w), ['aorta']);
});

test('subrayado desactivado en los ajustes', async () => {
  const g = JSON.parse(JSON.stringify(require('./helpers').GLOSARIO));
  g.ajustes.subrayado = false;
  const w = await montar('<div id="qa">aorta</div>', { datos: { '_fuentes_glosario.json': g } });
  assert.deepEqual(subrayados(w), []);
});
