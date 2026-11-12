/*
 * Fuentes — subrayado de términos y popup con fragmentos de tus fuentes.
 *
 * UN ÚNICO script para Anki escritorio, AnkiDroid, AnkiMobile y AnkiWeb.
 * - Escrito en ES5, sin dependencias ni APIs modernas sin comprobar
 *   (los WebViews de móvil pueden ser antiguos).
 * - Lee sus datos de la carpeta de medios de Anki:
 *     _fuentes_glosario.json   términos, sinónimos y archivo de cada término
 *     _fuentes_t_*.json        fragmentos de cada término
 * - Si existe pycmd (Anki escritorio) lo usa SOLO para extras: abrir el PDF,
 *   buscar más / texto libre en el índice SQLite.
 *
 * El algoritmo de normalización y matching es el mismo que en
 * textutil.py; ambos se prueban con tests/casos_matching.json.
 */
(function () {
  'use strict';
  var W = window;
  var D = document;

  // Si el script ya está cargado (AnkiMobile y Anki escritorio reutilizan la
  // página entre tarjetas, o la plantilla y el add-on lo cargan a la vez),
  // solo volvemos a aplicar el subrayado a la tarjeta nueva.
  if (W.Fuentes && W.Fuentes.__cargado) {
    W.Fuentes.run();
    return;
  }

  var F = (W.Fuentes = W.Fuentes || {});
  F.__cargado = true;
  F.version = '1.0.0';

  /* ------------------------------------------------------------------ *
   * Normalización (minúsculas, sin tildes, conserva la ñ)               *
   * ------------------------------------------------------------------ */

  // Tabla de respaldo si String.prototype.normalize no existe.
  var PLEGADO = {
    'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a', 'ã': 'a', 'å': 'a', 'ā': 'a',
    'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e', 'ē': 'e',
    'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i', 'ī': 'i',
    'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o', 'õ': 'o', 'ō': 'o',
    'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u', 'ū': 'u',
    'ç': 'c', 'ý': 'y', 'ÿ': 'y'
  };
  var ESPACIOS = ' \t\n\r\f\v     ';
  var MARCAS = /[̀-ͯ]/g;
  var tieneNormalize = typeof ''.normalize === 'function';
  var cacheCar = {};

  function normCar(c) {
    var r = cacheCar[c];
    if (r !== undefined) return r;
    var b = c.toLowerCase();
    if (b === 'ñ') r = 'ñ';
    else if (tieneNormalize) r = b.normalize('NFD').replace(MARCAS, '');
    else r = (PLEGADO[b] || b).replace(MARCAS, '');
    cacheCar[c] = r;
    return r;
  }

  function esPalabra(c) {
    return (c >= '0' && c <= '9') || c.toLowerCase() !== c.toUpperCase();
  }

  /** Devuelve {s: texto normalizado, m: mapa a índices del original}. */
  function normalizar(texto) {
    var s = [];
    var m = [];
    var enEspacio = false;
    for (var i = 0; i < texto.length; i++) {
      var c = texto.charAt(i);
      if (ESPACIOS.indexOf(c) !== -1) {
        if (!enEspacio) { s.push(' '); m.push(i); }
        enEspacio = true;
        continue;
      }
      enEspacio = false;
      var n = normCar(c);
      for (var k = 0; k < n.length; k++) { s.push(n.charAt(k)); m.push(i); }
    }
    return { s: s.join(''), m: m };
  }

  function clave(texto) {
    return normalizar(String(texto).replace(/^\s+|\s+$/g, '')).s.replace(/^ +| +$/g, '');
  }

  // Zonas que nunca se subrayan: [sound:…], {{c1::…}}, \( … \), \[ … \].
  var PROTEGIDO = /\[sound:[^\]]*\]|\{\{c\d+::[\s\S]*?\}\}|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]/g;

  /* ------------------------------------------------------------------ *
   * Matcher: trie de caracteres, gana la frase más larga                *
   * ------------------------------------------------------------------ */

  var FIN = '\u0000';

  /** variantes: [[texto, id], ...] */
  function Matcher(variantes) {
    this.raiz = {};
    for (var i = 0; i < variantes.length; i++) {
      var k = clave(variantes[i][0]);
      if (!k) continue;
      var nodo = this.raiz;
      for (var j = 0; j < k.length; j++) {
        var c = k.charAt(j);
        if (!nodo.hasOwnProperty(c)) nodo[c] = {};
        nodo = nodo[c];
      }
      if (!nodo.hasOwnProperty(FIN)) nodo[FIN] = variantes[i][1];
    }
  }

  /** Devuelve [[inicio, fin, id], ...] sobre el texto ORIGINAL. */
  Matcher.prototype.buscar = function (texto) {
    var nm = normalizar(texto);
    var s = nm.s;
    var mapa = nm.m;
    var protegidos = [];
    var r;
    PROTEGIDO.lastIndex = 0;
    while ((r = PROTEGIDO.exec(texto)) !== null) {
      protegidos.push([r.index, r.index + r[0].length]);
      if (r[0].length === 0) PROTEGIDO.lastIndex++;
    }
    var res = [];
    var n = s.length;
    var k = 0;
    while (k < n) {
      if ((k > 0 && esPalabra(s.charAt(k - 1))) || !esPalabra(s.charAt(k))) { k++; continue; }
      var nodo = this.raiz;
      var j = k;
      var mejorFin = -1;
      var mejorId = null;
      while (j < n && nodo.hasOwnProperty(s.charAt(j))) {
        nodo = nodo[s.charAt(j)];
        j++;
        if (nodo.hasOwnProperty(FIN) && (j === n || !esPalabra(s.charAt(j)))) {
          mejorFin = j;
          mejorId = nodo[FIN];
        }
      }
      if (mejorFin < 0) { k++; continue; }
      var ini = mapa[k];
      var fin = mapa[mejorFin - 1] + 1;
      var libre = true;
      for (var p = 0; p < protegidos.length; p++) {
        if (protegidos[p][0] < fin && ini < protegidos[p][1]) { libre = false; break; }
      }
      if (libre) res.push([ini, fin, mejorId]);
      k = mejorFin;
    }
    return res;
  };

  F.normalizar = normalizar;
  F.clave = clave;
  F.Matcher = Matcher;

  /* ------------------------------------------------------------------ *
   * Carga de datos (fetch → XMLHttpRequest → pycmd)                     *
   * ------------------------------------------------------------------ */

  F.base = typeof W.FUENTES_BASE === 'string' ? W.FUENTES_BASE : '';
  F.dataProvider = null; // función(nombre, cb(err, datos)) para tests y demo
  var cacheDatos = {};
  var pendientes = {};

  function tienePy() { return typeof W.pycmd === 'function'; }
  F.tienePy = tienePy;

  function porXHR(url, cb) {
    try {
      var x = new XMLHttpRequest();
      x.open('GET', url, true);
      x.onreadystatechange = function () {
        if (x.readyState !== 4) return;
        // En file:// el estado es 0 aunque haya ido bien.
        if ((x.status === 200 || x.status === 0) && x.responseText) {
          try { cb(null, JSON.parse(x.responseText)); } catch (e) { cb(e); }
        } else cb(new Error('XHR ' + x.status));
      };
      x.send();
    } catch (e) { cb(e); }
  }

  function porPy(nombre, cb) {
    if (!tienePy()) { cb(new Error('sin pycmd')); return; }
    F.py({ cmd: 'archivo', nombre: nombre }, function (r) {
      if (r && r.ok) cb(null, r.datos); else cb(new Error('pycmd'));
    });
  }

  function cargar(nombre, cb) {
    if (cacheDatos.hasOwnProperty(nombre)) { cb(null, cacheDatos[nombre]); return; }
    if (pendientes[nombre]) { pendientes[nombre].push(cb); return; }
    pendientes[nombre] = [cb];
    var terminar = function (err, datos) {
      if (!err) cacheDatos[nombre] = datos;
      var cbs = pendientes[nombre];
      delete pendientes[nombre];
      for (var i = 0; i < cbs.length; i++) cbs[i](err, datos);
    };
    if (F.dataProvider) { F.dataProvider(nombre, terminar); return; }
    var url = F.base + encodeURIComponent(nombre);
    var conXHR = function () {
      porXHR(url, function (err, datos) {
        if (!err) terminar(null, datos); else porPy(nombre, terminar);
      });
    };
    if (typeof W.fetch === 'function') {
      try {
        W.fetch(url).then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        }).then(function (d) { terminar(null, d); }, conXHR);
      } catch (e) { conXHR(); }
    } else conXHR();
  }
  F.cargar = cargar;
  F.limpiarCache = function () { cacheDatos = {}; glosario = null; };

  /** Llamada a Python (solo escritorio). Mensajes: "fuentes:" + JSON. */
  F.py = function (msg, cb) {
    if (!tienePy()) return false;
    W.pycmd('fuentes:' + JSON.stringify(msg), cb || function () {});
    return true;
  };

  /* ------------------------------------------------------------------ *
   * Glosario y ajustes                                                  *
   * ------------------------------------------------------------------ */

  var AJUSTES_DEF = { subrayado: true, fragmentos: 3, soloPrimera: true, idioma: '' };

  // Textos de la interfaz. El idioma llega en los ajustes exportados desde
  // el escritorio (el de tu Anki); si no, se usa el del navegador.
  var TEXTOS = {
    es: {
      vacio: 'No hay fragmentos para este término.',
      cargando: 'Cargando…',
      errorCarga: 'No se pudieron cargar los fragmentos. Sincroniza los medios con AnkiWeb y vuelve a intentarlo.',
      abrirPdf: 'Abrir el PDF en esta página',
      mas: 'Más en mis fuentes',
      buscando: 'Buscando…',
      errorBuscar: 'No se pudo buscar en las fuentes.',
      buscar: 'Buscar en fuentes',
      pagina: 'p. '
    },
    en: {
      vacio: 'No excerpts for this term.',
      cargando: 'Loading…',
      errorCarga: 'Could not load the excerpts. Sync your media with AnkiWeb and try again.',
      abrirPdf: 'Open the PDF at this page',
      mas: 'More from my sources',
      buscando: 'Searching…',
      errorBuscar: 'Could not search your sources.',
      buscar: 'Search sources',
      pagina: 'p. '
    }
  };

  function idioma() {
    var i = (glosario && glosario.ajustes.idioma) || (W.FUENTES_CONFIG && W.FUENTES_CONFIG.idioma) ||
      (W.navigator && (W.navigator.language || W.navigator.userLanguage)) || 'es';
    return String(i).toLowerCase().indexOf('es') === 0 ? 'es' : 'en';
  }

  function T(k) {
    return TEXTOS[idioma()][k] || TEXTOS.es[k] || k;
  }
  F.idioma = idioma;
  var glosario = null; // {terminos: [...], matcher, ajustes}
  var esperandoGlosario = [];

  function prepararGlosario(datos) {
    var ajustes = {};
    var k;
    for (k in AJUSTES_DEF) if (AJUSTES_DEF.hasOwnProperty(k)) ajustes[k] = AJUSTES_DEF[k];
    var a = (datos && datos.ajustes) || {};
    for (k in a) if (a.hasOwnProperty(k)) ajustes[k] = a[k];
    var c = W.FUENTES_CONFIG || {};
    for (k in c) if (c.hasOwnProperty(k)) ajustes[k] = c[k];
    var terminos = (datos && datos.terminos) || [];
    var variantes = [];
    for (var i = 0; i < terminos.length; i++) {
      var t = terminos[i];
      variantes.push([t.t, i]);
      var sin = t.s || [];
      for (var j = 0; j < sin.length; j++) variantes.push([sin[j], i]);
    }
    return { terminos: terminos, matcher: new Matcher(variantes), ajustes: ajustes };
  }

  function conGlosario(cb) {
    if (glosario) { cb(glosario); return; }
    esperandoGlosario.push(cb);
    if (esperandoGlosario.length > 1) return;
    cargar('_fuentes_glosario.json', function (err, datos) {
      if (err) {
        // Sin datos (p. ej. el móvil aún no ha sincronizado los medios):
        // no hacemos nada y la tarjeta se ve como siempre.
        if (W.console) W.console.log('[Fuentes] glosario no disponible: ' + err);
      }
      var g = prepararGlosario(err ? null : datos);
      // Si falló no lo guardamos: se reintentará con la siguiente tarjeta
      // (por ejemplo, después de sincronizar).
      if (!err) glosario = g;
      var cbs = esperandoGlosario;
      esperandoGlosario = [];
      for (var i = 0; i < cbs.length; i++) cbs[i](g);
    });
  }

  /* ------------------------------------------------------------------ *
   * Subrayado en el DOM                                                 *
   * ------------------------------------------------------------------ */

  // Elementos en los que nunca se entra.
  var SALTAR = {
    SCRIPT: 1, STYLE: 1, TEXTAREA: 1, INPUT: 1, SELECT: 1, OPTION: 1, BUTTON: 1,
    A: 1, CODE: 1, PRE: 1, SVG: 1, MATH: 1, IMG: 1, AUDIO: 1, VIDEO: 1, OBJECT: 1,
    IFRAME: 1, NOSCRIPT: 1, TEMPLATE: 1, 'MJX-CONTAINER': 1
  };

  function tieneClase(el, c) {
    var cn = el.className;
    if (typeof cn !== 'string') cn = el.getAttribute ? (el.getAttribute('class') || '') : '';
    return (' ' + cn + ' ').indexOf(' ' + c + ' ') !== -1;
  }

  function cercano(el, pred, tope) {
    while (el && el !== tope && el.nodeType === 1) {
      if (pred(el)) return el;
      el = el.parentNode;
    }
    return null;
  }

  function debeSaltar(el, esReverso) {
    if (SALTAR[el.nodeName.toUpperCase()]) return true;
    if (el.getAttribute && (el.getAttribute('data-fuentes-skip') !== null ||
        el.getAttribute('contenteditable') === 'true')) return true;
    if (tieneClase(el, 'fuentes-term') || tieneClase(el, 'fuentes-popup') ||
        tieneClase(el, 'fuentes-buscar') || tieneClase(el, 'MathJax') ||
        tieneClase(el, 'MathJax_Display') || tieneClase(el, 'MathJax_Preview')) return true;
    // En el anverso no tocamos el hueco del cloze ([...] o la pista).
    if (!esReverso && tieneClase(el, 'cloze')) return true;
    return false;
  }

  // Etiquetas de formato "en línea": un término puede estar repartido entre
  // ellas (p. ej. arteria <b>femoral</b>). Cualquier otra etiqueta corta.
  var EN_LINEA = {
    B: 1, I: 1, U: 1, EM: 1, STRONG: 1, SPAN: 1, FONT: 1, MARK: 1, SMALL: 1, BIG: 1,
    S: 1, SUB: 1, SUP: 1, INS: 1, DEL: 1, ABBR: 1, CITE: 1, Q: 1
  };

  /**
   * Agrupa los nodos de texto en "tramos": listas de nodos consecutivos
   * separados solo por etiquetas de formato en línea. El matching se hace
   * sobre el texto unido de cada tramo.
   */
  function tramos(raiz, esReverso) {
    var res = [];
    var actual = [];
    function cortar() {
      if (actual.length) { res.push(actual); actual = []; }
    }
    (function recorrer(n) {
      for (var c = n.firstChild; c; c = c.nextSibling) {
        if (c.nodeType === 3) {
          actual.push(c);
        } else if (c.nodeType === 1) {
          if (debeSaltar(c, esReverso)) { cortar(); continue; }
          var enLinea = EN_LINEA[c.nodeName.toUpperCase()] === 1;
          if (!enLinea) cortar();
          recorrer(c);
          if (!enLinea) cortar();
        }
      }
    })(raiz);
    cortar();
    return res;
  }

  function contenedor() {
    return D.getElementById('qa') || D.body;
  }

  /** Envuelve en <span class="fuentes-term"> los trozos [a, b, id] de un nodo de texto. */
  function envolver(nodo, trozos) {
    var texto = nodo.nodeValue;
    var frag = D.createDocumentFragment();
    var pos = 0;
    for (var j = 0; j < trozos.length; j++) {
      if (trozos[j][0] > pos) frag.appendChild(D.createTextNode(texto.slice(pos, trozos[j][0])));
      var span = D.createElement('span');
      span.className = 'fuentes-term';
      span.setAttribute('data-fuentes-t', String(trozos[j][2]));
      span.setAttribute('role', 'button');
      span.appendChild(D.createTextNode(texto.slice(trozos[j][0], trozos[j][1])));
      frag.appendChild(span);
      pos = trozos[j][1];
    }
    if (pos < texto.length) frag.appendChild(D.createTextNode(texto.slice(pos)));
    nodo.parentNode.replaceChild(frag, nodo);
  }

  /** Subraya los términos dentro de `raiz`. Devuelve los índices encontrados. */
  function subrayar(raiz, g, esReverso) {
    var ts = tramos(raiz, esReverso);
    var vistos = {};
    var encontrados = [];
    // Si ya hay subrayados (segunda pasada sobre la misma tarjeta), cuentan.
    var previos = raiz.getElementsByTagName ? raiz.getElementsByTagName('span') : [];
    for (var p = 0; p < previos.length; p++) {
      if (tieneClase(previos[p], 'fuentes-term')) vistos[previos[p].getAttribute('data-fuentes-t')] = 1;
    }
    for (var i = 0; i < ts.length; i++) {
      var nodos = ts[i];
      var texto = '';
      var inicios = [];
      var k;
      for (k = 0; k < nodos.length; k++) { inicios.push(texto.length); texto += nodos[k].nodeValue; }
      if (!/\S/.test(texto)) continue;
      var ms = g.matcher.buscar(texto);
      if (!ms.length) continue;
      var porNodo = [];
      for (var j = 0; j < ms.length; j++) {
        var id = ms[j][2];
        if (g.ajustes.soloPrimera && vistos[id]) continue;
        if (!g.terminos[id] || !g.terminos[id].f) continue;
        vistos[id] = 1;
        encontrados.push(id);
        // Un término puede caer en varios nodos: un trozo subrayado en cada uno.
        for (k = 0; k < nodos.length; k++) {
          var a = Math.max(ms[j][0], inicios[k]);
          var b = Math.min(ms[j][1], inicios[k] + nodos[k].nodeValue.length);
          if (a < b) (porNodo[k] = porNodo[k] || []).push([a - inicios[k], b - inicios[k], id]);
        }
      }
      for (k = 0; k < nodos.length; k++) if (porNodo[k]) envolver(nodos[k], porNodo[k]);
    }
    return encontrados;
  }
  F.subrayar = subrayar;

  /* ------------------------------------------------------------------ *
   * Popup                                                               *
   * ------------------------------------------------------------------ */

  var popup = null;
  var popupTermino = null; // elemento .fuentes-term activo
  var temporAbrir = null;
  var temporCerrar = null;
  var ultimoToque = 0;
  var forzarTactil = false;
  var acciones = [];

  F.forceTouch = function (v) { forzarTactil = !!v; };

  function esTactil() {
    return forzarTactil || (new Date().getTime() - ultimoToque < 1200);
  }

  function escapar(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /** Escapa el fragmento y resalta las variantes del término con <mark>. */
  function resaltar(texto, termino) {
    var m = termino.__matcher;
    if (!m || typeof m.buscar !== 'function') {
      var vs = [[termino.t, 0]];
      var sin = termino.s || [];
      for (var i = 0; i < sin.length; i++) vs.push([sin[i], 0]);
      m = termino.__matcher = new Matcher(vs);
    }
    var ms = m.buscar(texto);
    var out = '';
    var pos = 0;
    for (var j = 0; j < ms.length; j++) {
      out += escapar(texto.slice(pos, ms[j][0])) + '<mark>' + escapar(texto.slice(ms[j][0], ms[j][1])) + '</mark>';
      pos = ms[j][1];
    }
    return out + escapar(texto.slice(pos));
  }
  F.resaltar = resaltar;

  function etiquetaPagina(fr) {
    return T('pagina') + (fr.e || fr.p);
  }

  /** HTML del popup a partir de los datos de un término. */
  function htmlFragmentos(datos, termino, max) {
    var fuentes = (datos && datos.fuentes) || [];
    if (!fuentes.length) return '<div class="fuentes-vacio">' + escapar(T('vacio')) + '</div>';
    var py = tienePy();
    var h = '';
    for (var i = 0; i < fuentes.length; i++) {
      var f = fuentes[i];
      var frs = (f.fragmentos || []).slice(0, max);
      if (!frs.length) continue;
      h += '<div class="fuentes-fuente"><div class="fuentes-nombre">' + escapar(f.nombre) + '</div>';
      for (var j = 0; j < frs.length; j++) {
        var fr = frs[j];
        var donde = escapar(f.nombre) + ', ' + escapar(etiquetaPagina(fr));
        h += '<div class="fuentes-frag' + (py ? ' fuentes-abrible' : '') + '" data-s="' + escapar(f.id) +
          '" data-p="' + escapar(fr.p) + '"' + (py ? ' title="' + escapar(T('abrirPdf')) + '"' : '') + '>' +
          '<div class="fuentes-texto">' + resaltar(fr.x, termino) + '</div>' +
          '<div class="fuentes-donde">' + donde + (py ? ' <span class="fuentes-ir">↗</span>' : '') +
          '</div></div>';
      }
      h += '</div>';
    }
    return h;
  }

  function contexto(id) {
    var t = glosario && glosario.terminos[id];
    return {
      id: id,
      termino: t,
      variantes: t ? [t.t].concat(t.s || []) : [],
      tienePy: tienePy(),
      datos: t && cacheDatos[t.f]
    };
  }

  /**
   * Registro de acciones del popup (p. ej. un futuro botón "Explicar" con
   * búsqueda semántica o LLM). Una acción es:
   *   {id, etiqueta (texto o función que lo devuelve), disponible: function(ctx) -> bool,
   *    ejecutar: function(ctx, mostrar(html))}
   */
  F.registrarAccion = function (accion) {
    for (var i = 0; i < acciones.length; i++) {
      if (acciones[i].id === accion.id) { acciones[i] = accion; return; }
    }
    acciones.push(accion);
  };

  function htmlAcciones(ctx) {
    var h = '';
    for (var i = 0; i < acciones.length; i++) {
      var a = acciones[i];
      if (a.disponible && !a.disponible(ctx)) continue;
      h += '<button type="button" class="fuentes-accion" data-accion="' + escapar(a.id) + '">' +
        escapar(typeof a.etiqueta === 'function' ? a.etiqueta() : a.etiqueta) + '</button>';
    }
    return h ? '<div class="fuentes-acciones">' + h + '</div>' : '';
  }

  function crearPopup() {
    if (popup && popup.parentNode) return popup;
    popup = D.createElement('div');
    popup.className = 'fuentes-popup';
    popup.setAttribute('role', 'dialog');
    popup.style.display = 'none';
    D.body.appendChild(popup);
    return popup;
  }

  function colocar(anclaRect) {
    var vw = W.innerWidth || D.documentElement.clientWidth;
    var vh = W.innerHeight || D.documentElement.clientHeight;
    var sx = W.pageXOffset || D.documentElement.scrollLeft || 0;
    var sy = W.pageYOffset || D.documentElement.scrollTop || 0;
    var margen = 8;
    var ancho = Math.min(440, vw - 2 * margen);
    popup.style.width = ancho + 'px';
    var abajo = vh - anclaRect.bottom - margen;
    var arriba = anclaRect.top - margen;
    var ponerAbajo = abajo >= 160 || abajo >= arriba;
    // En táctil (pantalla pequeña) ocupa menos para no tapar la tarjeta.
    var disponible = Math.max(100, Math.min((ponerAbajo ? abajo : arriba) - 6, vh * (esTactil() ? 0.4 : 0.5)));
    popup.style.maxHeight = Math.floor(disponible) + 'px';
    var izq = anclaRect.left + sx;
    if (izq + ancho > sx + vw - margen) izq = sx + vw - margen - ancho;
    if (izq < sx + margen) izq = sx + margen;
    popup.style.left = Math.round(izq) + 'px';
    if (ponerAbajo) {
      popup.style.top = Math.round(anclaRect.bottom + sy + 6) + 'px';
    } else {
      var alto = Math.min(popup.offsetHeight || disponible, disponible);
      popup.style.top = Math.round(anclaRect.top + sy - 6 - alto) + 'px';
    }
  }

  function mostrarEn(anclaRect, html) {
    crearPopup();
    popup.innerHTML = html;
    popup.style.display = 'block';
    popup.scrollTop = 0;
    colocar(anclaRect);
  }

  function abrir(el) {
    if (!glosario) return;
    var id = parseInt(el.getAttribute('data-fuentes-t'), 10);
    var t = glosario.terminos[id];
    if (!t) return;
    popupTermino = el;
    var max = glosario.ajustes.fragmentos || 3;
    var pintar = function (cuerpo) {
      if (popupTermino !== el) return; // el usuario ya se fue a otro término
      var ctx = contexto(id);
      mostrarEn(el.getBoundingClientRect(),
        '<div class="fuentes-cab">' + escapar(t.t) + '</div>' +
        '<div class="fuentes-cuerpo">' + cuerpo + '</div>' + htmlAcciones(ctx));
      popup.setAttribute('data-fuentes-t', String(id));
    };
    if (cacheDatos.hasOwnProperty(t.f)) {
      pintar(htmlFragmentos(cacheDatos[t.f], t, max));
      return;
    }
    pintar('<div class="fuentes-vacio">' + escapar(T('cargando')) + '</div>');
    cargar(t.f, function (err, datos) {
      pintar(err
        ? '<div class="fuentes-vacio">' + escapar(T('errorCarga')) + '</div>'
        : htmlFragmentos(datos, t, max));
    });
  }
  F.abrir = abrir;

  function cerrar() {
    if (temporAbrir) { clearTimeout(temporAbrir); temporAbrir = null; }
    if (temporCerrar) { clearTimeout(temporCerrar); temporCerrar = null; }
    if (popup) { popup.style.display = 'none'; popup.innerHTML = ''; }
    popupTermino = null;
  }
  F.cerrar = cerrar;

  function abierto() { return !!(popup && popup.style.display === 'block'); }
  F.abierto = abierto;

  function esTermino(el) { return el.nodeType === 1 && tieneClase(el, 'fuentes-term'); }
  function esPopup(el) { return el.nodeType === 1 && tieneClase(el, 'fuentes-popup'); }

  /* ------------------------------------------------------------------ *
   * Búsqueda de texto libre (solo escritorio, vía pycmd)                *
   * ------------------------------------------------------------------ */

  var botonBuscar = null;

  function ocultarBotonBuscar() {
    if (botonBuscar) botonBuscar.style.display = 'none';
  }

  function mostrarResultadosPy(rect, titulo, res) {
    var max = 10;
    var tFalso = { t: titulo, s: (res && res.resaltar) || [] };
    var cuerpo = res && res.ok ? htmlFragmentos(res, tFalso, max)
      : '<div class="fuentes-vacio">' + escapar(T('errorBuscar')) + '</div>';
    popupTermino = null;
    mostrarEn(rect, '<div class="fuentes-cab">' + escapar(titulo) + '</div>' +
      '<div class="fuentes-cuerpo">' + cuerpo + '</div>');
  }

  function textoSeleccionado() {
    var sel = W.getSelection ? W.getSelection() : null;
    if (!sel || sel.rangeCount === 0) return null;
    var t = String(sel.toString()).replace(/\s+/g, ' ').replace(/^ | $/g, '');
    if (t.length < 3 || t.length > 120) return null;
    return { texto: t, rect: sel.getRangeAt(0).getBoundingClientRect() };
  }

  function quizaMostrarBotonBuscar() {
    if (!tienePy() || esTactil()) return;
    var s = textoSeleccionado();
    if (!s) { ocultarBotonBuscar(); return; }
    if (!botonBuscar) {
      botonBuscar = D.createElement('button');
      botonBuscar.type = 'button';
      botonBuscar.className = 'fuentes-buscar';
      D.body.appendChild(botonBuscar);
    }
    botonBuscar.innerHTML = '';
    botonBuscar.appendChild(D.createTextNode(T('buscar')));
    var sx = W.pageXOffset || 0;
    var sy = W.pageYOffset || 0;
    botonBuscar.style.display = 'block';
    botonBuscar.style.left = Math.round(s.rect.left + sx) + 'px';
    botonBuscar.style.top = Math.round(s.rect.bottom + sy + 4) + 'px';
    botonBuscar.setAttribute('data-q', s.texto);
  }

  /* ------------------------------------------------------------------ *
   * Eventos (se registran una sola vez, por delegación)                 *
   * ------------------------------------------------------------------ */

  function onTouch() { ultimoToque = new Date().getTime(); }

  function onOver(e) {
    if (esTactil()) return;
    var el = cercano(e.target, esTermino);
    if (el) {
      if (temporCerrar) { clearTimeout(temporCerrar); temporCerrar = null; }
      if (popupTermino === el && abierto()) return;
      // Otro trozo del mismo término (partido por etiquetas): no reabrir.
      if (abierto() && popupTermino &&
          popupTermino.getAttribute('data-fuentes-t') === el.getAttribute('data-fuentes-t')) return;
      if (temporAbrir) clearTimeout(temporAbrir);
      temporAbrir = setTimeout(function () { temporAbrir = null; abrir(el); }, 120);
    } else if (cercano(e.target, esPopup)) {
      if (temporCerrar) { clearTimeout(temporCerrar); temporCerrar = null; }
    }
  }

  function onOut(e) {
    if (esTactil()) return;
    var desde = cercano(e.target, esTermino) || cercano(e.target, esPopup);
    if (!desde) return;
    var hacia = e.relatedTarget;
    if (hacia && (cercano(hacia, esTermino) === popupTermino && popupTermino || cercano(hacia, esPopup))) return;
    if (temporAbrir) { clearTimeout(temporAbrir); temporAbrir = null; }
    if (temporCerrar) clearTimeout(temporCerrar);
    temporCerrar = setTimeout(cerrar, 350);
  }

  function onClick(e) {
    var t = e.target;
    // Botón "Buscar en fuentes" sobre una selección (escritorio).
    if (botonBuscar && cercano(t, function (x) { return x === botonBuscar; })) {
      var q = botonBuscar.getAttribute('data-q');
      var rect = botonBuscar.getBoundingClientRect();
      ocultarBotonBuscar();
      F.py({ cmd: 'buscar', q: q }, function (res) { mostrarResultadosPy(rect, q, res); });
      e.preventDefault();
      return;
    }
    var enPopup = cercano(t, esPopup);
    if (enPopup) {
      var accion = cercano(t, function (x) { return x.getAttribute && x.getAttribute('data-accion') !== null; }, enPopup);
      if (accion) {
        ejecutarAccion(accion.getAttribute('data-accion'));
        e.preventDefault();
        return;
      }
      var frag = cercano(t, function (x) { return tieneClase(x, 'fuentes-abrible'); }, enPopup);
      if (frag) {
        F.py({ cmd: 'abrir', fuente: parseInt(frag.getAttribute('data-s'), 10),
          pagina: parseInt(frag.getAttribute('data-p'), 10) });
        e.preventDefault();
      }
      return; // los toques dentro del popup no lo cierran
    }
    var el = cercano(t, esTermino);
    if (el) {
      if (temporAbrir) { clearTimeout(temporAbrir); temporAbrir = null; }
      if (!(popupTermino === el && abierto())) abrir(el);
      e.preventDefault();
      if (e.stopPropagation) e.stopPropagation();
      return;
    }
    if (abierto()) cerrar(); // tocar fuera cierra
  }

  function ejecutarAccion(idAccion) {
    var id = popup ? parseInt(popup.getAttribute('data-fuentes-t'), 10) : NaN;
    var ctx = contexto(id);
    for (var i = 0; i < acciones.length; i++) {
      if (acciones[i].id !== idAccion) continue;
      acciones[i].ejecutar(ctx, function (html) {
        if (!popup) return;
        var zona = null;
        var divs = popup.getElementsByTagName('div');
        for (var j = 0; j < divs.length; j++) if (tieneClase(divs[j], 'fuentes-cuerpo')) zona = divs[j];
        if (zona) zona.innerHTML = html;
      });
    }
  }

  // Acción incluida: "Más en mis fuentes" (escritorio, consulta el índice SQLite).
  F.registrarAccion({
    id: 'mas',
    etiqueta: function () { return T('mas'); },
    disponible: function (ctx) { return ctx.tienePy && !!ctx.termino; },
    ejecutar: function (ctx, mostrar) {
      mostrar('<div class="fuentes-vacio">' + escapar(T('buscando')) + '</div>');
      F.py({ cmd: 'mas', variantes: ctx.variantes }, function (res) {
        mostrar(res && res.ok ? htmlFragmentos(res, ctx.termino, 10)
          : '<div class="fuentes-vacio">' + escapar(T('errorBuscar')) + '</div>');
      });
    }
  });

  var eventosListos = false;
  function registrarEventos() {
    if (eventosListos) return;
    eventosListos = true;
    var opc = false;
    try {
      // Comprobamos si el navegador admite {passive: true}.
      var o = Object.defineProperty({}, 'passive', { get: function () { opc = { passive: true }; return true; } });
      W.addEventListener('fuentes-test', null, o);
    } catch (e) { opc = false; }
    D.addEventListener('touchstart', onTouch, opc);
    D.addEventListener('mouseover', onOver, false);
    D.addEventListener('mouseout', onOut, false);
    D.addEventListener('click', onClick, true);
    D.addEventListener('mouseup', function () { setTimeout(quizaMostrarBotonBuscar, 0); }, false);
    D.addEventListener('keydown', function (e) {
      if (e.keyCode === 27 && abierto()) cerrar();
    }, false);
    W.addEventListener('resize', function () { if (abierto()) cerrar(); }, false);
  }

  /* ------------------------------------------------------------------ *
   * Arranque                                                            *
   * ------------------------------------------------------------------ */

  function precargar(ids) {
    // Precargamos los fragmentos de los términos de esta tarjeta para que el
    // popup abra al instante (son archivos locales y pequeños).
    if (ids.length > 40) ids = ids.slice(0, 40);
    for (var i = 0; i < ids.length; i++) {
      var t = glosario.terminos[ids[i]];
      if (t && t.f) cargar(t.f, function () {});
    }
  }

  /** Aplica el subrayado a la tarjeta actual. Se puede llamar las veces que haga falta. */
  F.run = function () {
    cerrar();
    ocultarBotonBuscar();
    if (!D.body) return;
    registrarEventos();
    conGlosario(function (g) {
      if (!g.ajustes.subrayado || !g.terminos.length) return;
      var raiz = contenedor();
      var esReverso = !!D.getElementById('answer');
      var ids = subrayar(raiz, g, esReverso);
      F.ultimos = ids;
      setTimeout(function () { precargar(ids); }, 30);
    });
  };

  // Anki escritorio: volver a aplicar cuando se muestra cada tarjeta.
  if (W.onShownHook && W.onShownHook.push && !W.__fuentesHook) {
    W.__fuentesHook = true;
    W.onShownHook.push(function () { F.run(); });
  }

  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', F.run, false);
  else setTimeout(F.run, 0);
})();
