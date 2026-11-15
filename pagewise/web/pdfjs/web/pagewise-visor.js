/* Pagewise: ajustes del visor pdf.js. El resto de esta carpeta es pdf.js 4.10.38
 * (versión «legacy») tal cual, salvo la etiqueta que carga este archivo en
 * viewer.html y el método #extractText de viewer.mjs (marcado con PAGEWISE).
 *
 * - El PDF se pide POR TROZOS al servidor local de Anki: solo se leen las
 *   páginas que se miran, así que un libro de 1-2 GB no se carga en memoria.
 * - Sin scripts del PDF, sin historial y sin botones que no tienen sentido
 *   dentro de Anki (abrir otro archivo, descargar, imprimir, editar).
 * - pagewiseIr(pagina, buscar, frase): salta a una página y resalta el texto,
 *   como Ctrl+F, empezando por la coincidencia de esa página.
 */
(function () {
  'use strict';

  function poner(opciones, nombre, valor) {
    try { opciones.set(nombre, valor); } catch (e) { /* opción que esta versión no tiene */ }
  }

  document.addEventListener('webviewerloaded', function () {
    var o = window.PDFViewerApplicationOptions;
    if (!o) return;
    poner(o, 'defaultUrl', '');
    poner(o, 'disablePreferences', true);
    poner(o, 'disableAutoFetch', true);   // no descargar el resto del PDF por detrás
    poner(o, 'disableStream', true);      // pedir solo los trozos necesarios
    poner(o, 'disableHistory', true);
    poner(o, 'viewOnLoad', 1);            // no recordar la posición anterior: manda la página pedida
    poner(o, 'enableScripting', false);
    poner(o, 'isEvalSupported', false);
    poner(o, 'externalLinkTarget', 2);    // los enlaces del PDF no sustituyen al visor
    poner(o, 'annotationEditorMode', -1);
    poner(o, 'enableSignatureEditor', false);
    var idioma = /[?&]lang=([A-Za-z-]+)/.exec(location.search);
    if (idioma) poner(o, 'localeProperties', { lang: idioma[1] });
  });

  /* ---------------------------------------------------------------------
   * Orden de lectura del texto para la búsqueda.
   *
   * Para resaltar, pdf.js necesita el texto de la página. De serie lee el
   * libro entero empezando por la página 1; aquí se empieza por la página
   * que se está mirando y se sigue hacia fuera (N, N+1, N-1, N+2…), así el
   * resaltado aparece enseguida aunque sea la página 900.
   *
   * En PDFs enormes (?grande=1, lo decide Python por el tamaño del archivo)
   * leer el texto de todo el libro obliga a traer casi todo el archivo a la
   * memoria. Ahí solo se leen las páginas cercanas a la visible, y se sigue
   * a medida que el usuario pasa páginas. Si el usuario busca él mismo con
   * la lupa (Ctrl+F), se lee el libro completo: lo ha pedido.
   * ------------------------------------------------------------------- */
  var VENTANA = 2;                       // páginas a cada lado, en modo «grande»
  var limitar = /[?&]grande=1(&|$)/.test(location.search);
  var reanudar = function () {};

  window.pagewisePlanExtraccion = function (total, extraer, paginaActual) {
    var hecha = new Uint8Array(total);
    var quedan = total;
    var activo = false;

    function centro() { return Math.max(0, Math.min(total - 1, paginaActual() || 0)); }

    function siguiente(c) {
      for (var d = 0; d < total; d++) {
        if (c + d < total && !hecha[c + d]) return c + d;
        if (c - d >= 0 && !hecha[c - d]) return c - d;
      }
      return -1;
    }

    function paso() {
      var c = centro();
      var i = quedan ? siguiente(c) : -1;
      if (i < 0 || (limitar && Math.abs(i - c) > VENTANA)) { activo = false; return; }
      activo = true;
      hecha[i] = 1;
      quedan--;
      extraer(i).then(paso, paso);
    }

    reanudar = function () { if (!activo) paso(); };
    paso();
  };

  function conectar() {
    var app = window.PDFViewerApplication;
    if (!app || !app.initializedPromise) return;
    app.initializedPromise.then(function () {
      var bus = app.eventBus;
      if (!bus) return;
      bus._on('pagechanging', function () { reanudar(); });
      bus._on('find', function (evt) {
        // Búsqueda hecha por el usuario en la barra del visor: todo el libro.
        if (evt && app.findBar && evt.source === app.findBar) limitar = false;
        reanudar();
      });
    });
  }
  document.addEventListener('webviewerloaded', conectar);

  var estilo = document.createElement('style');
  estilo.textContent =
    '#secondaryOpenFile, #downloadButton, #secondaryDownload, #printButton, #secondaryPrint,' +
    '#editorModeButtons, #editorModeSeparator, #viewBookmark, #viewBookmarkSeparator,' +
    '#presentationMode { display: none !important; }';
  document.documentElement.appendChild(estilo);

  function hash(pagina, buscar, frase) {
    var h = 'page=' + (parseInt(pagina, 10) || 1);
    if (buscar) h += '&search=' + encodeURIComponent(buscar) + '&phrase=' + (frase ? 'true' : 'false');
    return h;
  }

  window.pagewiseIr = function (pagina, buscar, frase) {
    var app = window.PDFViewerApplication;
    if (!app || !app.pdfDocument || !app.pdfLinkService) return false;
    // Primero la página: la búsqueda empieza por la página visible.
    app.page = parseInt(pagina, 10) || 1;
    reanudar();
    if (buscar) {
      app.pdfLinkService.setHash(hash(pagina, buscar, frase));
    } else if (app.eventBus) {
      app.eventBus.dispatch('findbarclose', { source: window });
    }
    return true;
  };

  /* Estado para las pruebas y para que Python sepa si el visor arrancó. */
  window.pagewiseEstado = function () {
    var app = window.PDFViewerApplication;
    if (!app || !app.pdfDocument) return { listo: false };
    var fc = app.findController;
    return {
      listo: true,
      pagina: app.page,
      paginas: app.pagesCount,
      coincidencias: fc ? fc._matchesCountTotal : 0,
      paginaCoincidencia: fc && fc._selected ? fc._selected.pageIdx + 1 : 0,
      resaltadas: document.querySelectorAll('.textLayer .highlight').length,
      limitado: limitar
    };
  };
})();
