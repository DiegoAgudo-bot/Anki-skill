/* Motor de la demo de la landing.
   Reproduce en pequeño lo que hace el add-on: subraya términos (sin
   distinguir mayúsculas ni tildes, gana la frase más larga) y abre un popup
   con fragmentos y página. Los textos son apuntes INVENTADOS de ejemplo. */
var Fx = (function () {
  var A = 'Apuntes de Anatomía', R = 'Resumen de repaso';
  var G = [
    { t: 'arteria femoral', s: ['a. femoral'], f: [
      [A, 12, 'La arteria femoral continúa a la arteria ilíaca externa por debajo del ligamento inguinal. En el triángulo femoral se palpa el pulso con facilidad.'],
      [R, 3, 'Recuerda que el nervio ciático no acompaña a la arteria femoral, sino que va por detrás del muslo.']] },
    { t: 'nervio ciático', s: ['ciático'], f: [
      [A, 47, 'El nervio ciático es el nervio más grueso del organismo. Sale de la pelvis por el agujero ciático mayor y desciende por la región posterior del muslo.']] },
    { t: 'ligamento inguinal', s: [], f: [
      [A, 11, 'El ligamento inguinal se extiende desde la espina ilíaca anterosuperior hasta el tubérculo del pubis.']] },
    { t: 'ventrículo izquierdo', s: [], f: [
      [A, 5, 'El ventrículo izquierdo tiene la pared más gruesa porque debe vencer la resistencia de toda la circulación sistémica.']] },
    { t: 'aorta', s: [], f: [
      [A, 6, 'La aorta nace del ventrículo izquierdo y describe un arco antes de descender por el tórax.'],
      [R, 4, 'La aorta torácica da arterias intercostales; la abdominal, el tronco celíaco y las renales.']] },
    { t: 'vena safena mayor', s: ['safena mayor'], f: [
      [A, 14, 'La vena safena mayor es la vena más larga del cuerpo y asciende por la cara medial del miembro inferior.']] }
  ];

  function norm(s) {
    return s.toLowerCase().replace(/ñ/g, '\u0001').normalize('NFD')
      .replace(/[̀-ͯ]/g, '').replace(/\u0001/g, 'ñ').replace(/ /g, ' ');
  }
  function letra(c) { return !!c && /[a-z0-9ñ]/.test(c); }
  var V = [];
  G.forEach(function (g, i) {
    [g.t].concat(g.s).forEach(function (v) { V.push({ k: norm(v), i: i }); });
  });
  V.sort(function (a, b) { return b.k.length - a.k.length; });

  /* Coincidencias [inicio, fin, término] en un texto; opcionalmente solo de un término. */
  function buscar(texto, solo) {
    var n = norm(texto.normalize('NFC')), res = [], p = 0;
    while (p < n.length) {
      var hit = null;
      if (letra(n[p]) && !letra(n[p - 1])) {
        for (var j = 0; j < V.length; j++) {
          var v = V[j];
          if ((solo === undefined || v.i === solo) && n.startsWith(v.k, p) && !letra(n[p + v.k.length])) { hit = v; break; }
        }
      }
      if (hit) { res.push([p, p + hit.k.length, hit.i]); p += hit.k.length; } else p++;
    }
    return res;
  }
  function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

  /* Subraya los términos dentro de un elemento. */
  function subrayar(raiz) {
    var w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT), nodos = [], n;
    while ((n = w.nextNode())) if (!n.parentNode.closest('.t,button,input,a')) nodos.push(n);
    nodos.forEach(function (nodo) {
      var tx = nodo.nodeValue.normalize('NFC'), ms = buscar(tx);
      if (!ms.length) return;
      var fr = document.createDocumentFragment(), pos = 0;
      ms.forEach(function (m) {
        fr.appendChild(document.createTextNode(tx.slice(pos, m[0])));
        var sp = document.createElement('span');
        sp.className = 't'; sp.dataset.i = m[2]; sp.tabIndex = 0; sp.setAttribute('role', 'button');
        sp.textContent = tx.slice(m[0], m[1]);
        fr.appendChild(sp); pos = m[1];
      });
      fr.appendChild(document.createTextNode(tx.slice(pos)));
      nodo.parentNode.replaceChild(fr, nodo);
    });
  }
  function resaltar(tx, i) {
    var out = '', pos = 0;
    buscar(tx, i).forEach(function (m) {
      out += esc(tx.slice(pos, m[0])) + '<mark>' + esc(tx.slice(m[0], m[1])) + '</mark>'; pos = m[1];
    });
    return out + esc(tx.slice(pos));
  }

  var pop = null, actual = null, tCerrar = null, api = { onOpen: null, onClose: null, colocar: null, dx: 0, dy: 8 };
  function htmlPop(i) {
    var g = G[i], h = '<p class="fx-term">' + esc(g.t) + '</p>', ult = '';
    g.f.forEach(function (f) {
      if (f[0] !== ult) { h += '<p class="fx-src">' + f[0] + '</p>'; ult = f[0]; }
      h += '<div class="fx-frag"><p>' + resaltar(f[2], i) + '</p><p class="fx-where">' + f[0] + ', p. ' + f[1] + '</p></div>';
    });
    return h;
  }
  function abrir(el) {
    clearTimeout(tCerrar);
    if (actual === el) return;
    if (!pop) { pop = document.createElement('div'); pop.className = 'fx-pop'; pop.setAttribute('role', 'dialog'); document.body.appendChild(pop); }
    if (actual) actual.classList.remove('on');
    actual = el; el.classList.add('on');
    pop.innerHTML = htmlPop(+el.dataset.i);
    pop.hidden = false;
    var r = el.getBoundingClientRect(), vw = document.documentElement.clientWidth;
    var ancho = Math.min(380, vw - 24);
    pop.style.width = ancho + 'px';
    var x = Math.max(12, Math.min(r.left + api.dx, vw - ancho - 12));
    var y = r.bottom + api.dy;
    // Cada diseño puede decidir dónde va el popup (p. ej. al lado de la escena).
    var c = api.colocar ? api.colocar(el, r, ancho, vw) : null;
    if (c) { x = c[0]; y = c[1]; }
    pop.style.left = (x + window.scrollX) + 'px';
    pop.style.top = (y + window.scrollY) + 'px';
    pop.classList.remove('in'); void pop.offsetWidth; pop.classList.add('in');
    if (api.onOpen) api.onOpen(el, pop);
  }
  function cerrar() {
    if (!actual) return;
    actual.classList.remove('on'); actual = null;
    if (pop) pop.hidden = true;
    if (api.onClose) api.onClose();
  }
  var auto = null;
  function parar() { if (auto) { clearInterval(auto.id); if (auto.cur) auto.cur.hidden = true; auto = null; } }

  document.addEventListener('mouseover', function (e) {
    var t = e.target.closest && e.target.closest('.t');
    if (t && !t.closest('[data-touch]')) { parar(); abrir(t); }
    else if (e.target.closest && e.target.closest('.fx-pop')) clearTimeout(tCerrar);
  });
  document.addEventListener('mouseout', function (e) {
    if (auto) return;
    var de = e.target.closest && (e.target.closest('.t') || e.target.closest('.fx-pop'));
    if (de && !(de.closest && de.closest('[data-touch]'))) { clearTimeout(tCerrar); tCerrar = setTimeout(cerrar, 300); }
  });
  document.addEventListener('click', function (e) {
    var t = e.target.closest('.t');
    if (t) { parar(); if (actual === t && t.closest('[data-touch]')) cerrar(); else { actual = actual === t ? null : actual; abrir(t); } return; }
    if (!e.target.closest('.fx-pop')) { if (actual) parar(); cerrar(); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { parar(); cerrar(); }
    if ((e.key === 'Enter' || e.key === ' ') && e.target.classList && e.target.classList.contains('t')) { e.preventDefault(); parar(); abrir(e.target); }
  });
  window.addEventListener('resize', function () { if (!auto) cerrar(); });

  /* Demostración automática: un cursor recorre los términos del escenario.
     La página arranca con el popup ya abierto (estado completo en reposo). */
  function autoplay(escena, cursor) {
    var ts = escena.querySelectorAll('.t'); if (!ts.length) return;
    var k = 0;
    function ir() {
      var t = ts[k % ts.length]; k++;
      if (cursor) {
        var r = t.getBoundingClientRect(), b = escena.getBoundingClientRect();
        cursor.hidden = false;
        cursor.style.transform = 'translate(' + (r.left - b.left + r.width * 0.6) + 'px,' + (r.top - b.top + r.height * 0.55) + 'px)';
      }
      setTimeout(function () { if (auto) abrir(t); }, cursor ? 650 : 0);
    }
    abrir(ts[0]); k = 1;
    // Recolocar cuando terminen de cargar las tipografías (cambian el tamaño del texto).
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () {
      if (actual) { var t = actual; actual = null; abrir(t); }
    });
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    auto = { cur: cursor, id: setInterval(function () {
      var b = escena.getBoundingClientRect();
      if (b.bottom < 0 || b.top > window.innerHeight) return; // fuera de pantalla: no molestar
      ir();
    }, 4200) };
  }

  /* Zona de pruebas: lo que escribe el visitante se subraya en vivo. */
  function probar(input, salida) {
    function pintar() { salida.textContent = input.value || ' '; subrayar(salida); }
    input.addEventListener('input', function () { parar(); cerrar(); pintar(); });
    pintar();
  }

  /* Lista de espera. Envía el correo al servicio de formularios configurado
     en landing/config.json (compatible con Formspree y similares: POST JSON).
     Sin servicio configurado NO finge: avisa de que la lista aún no está abierta. */
  function lista(form, destino) {
    var campo = form.querySelector('input[type=email]'), estado = form.querySelector('.fx-estado');
    var boton = form.querySelector('button');
    function decir(texto, clase) { estado.textContent = texto; estado.className = 'fx-estado ' + clase; }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var v = campo.value.trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) {
        decir('Escribe un correo válido, por ejemplo ana@correo.es', 'mal'); campo.focus(); return;
      }
      if (!destino) { decir('La lista de espera todavía no está abierta. Vuelve en unos días.', 'mal'); return; }
      boton.disabled = true; decir('Apuntándote…', '');
      fetch(destino, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ email: v, origen: 'landing' }) })
        .then(function (r) { if (!r.ok) throw new Error(r.status); })
        .then(function () { decir('Apuntado a la lista. Te escribiremos cuando salga la versión Pro.', 'bien'); form.classList.add('hecho'); })
        .catch(function () { boton.disabled = false; decir('No se pudo apuntar tu correo. Comprueba tu conexión e inténtalo otra vez.', 'mal'); });
    });
  }
  api.subrayar = subrayar; api.autoplay = autoplay; api.probar = probar; api.lista = lista;
  api.abrir = abrir; api.cerrar = cerrar;
  return api;
})();
