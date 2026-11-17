# Pagewise: tus PDFs dentro de tus tarjetas de Anki

Add-on para Anki que subraya los términos de tus tarjetas y, al pasar el ratón (escritorio) o tocarlos (móvil), muestra los fragmentos más relevantes de **tus propias fuentes** (los PDFs que importas tú) con su número de página. En el escritorio, un clic abre el PDF en esa página sin salir de Anki.

- Funciona en **Anki escritorio 2.1.66 o posterior** (Qt6). Probado en 2.1.66 y 25.09.
- Interfaz en **español e inglés**: sigue el idioma de tu Anki (español, o inglés para el resto). *English summary [below](#english).*
- Funciona en **AnkiDroid, AnkiMobile y AnkiWeb** sin conexión, gracias a datos precalculados que viajan con tu sincronización de medios.
- **Todo es local.** Los PDFs se procesan en tu ordenador. No hay servidores ni se comparte nada entre usuarios. Los datos solo llegan a tu móvil a través de tu propia sincronización con AnkiWeb. La única excepción es el botón opcional **Explicar** (Pro), que solo se conecta cuando lo pulsas (ver [Privacidad](#privacidad)).

> **Nota legal.** El add-on se distribuye vacío: sin libros, sin índices y sin glosarios. Importa solo material que tengas derecho a usar (apuntes propios, libros que hayas comprado para uso personal y cuya licencia lo permita, documentos con licencia abierta…). Tú eres responsable del contenido que cargas. Ten en cuenta que los fragmentos exportados para el móvil se guardan en tu colección y se sincronizan con tu cuenta de AnkiWeb.

> **¿Vienes de «Fuentes»?** Es el nombre anterior de este add-on. Instala Pagewise sin borrar antes el antiguo: al arrancar copia tus PDFs, tu índice y tu glosario, actualiza tus plantillas y desactiva «Fuentes». Reinicia Anki y, cuando compruebes que todo está, elimina el complemento antiguo.

## Instalación

1. Descarga o genera `pagewise-<versión>.ankiaddon` (ver [Desarrollo](#desarrollo)).
2. En Anki: **Herramientas → Complementos → Instalar desde archivo…** y elige el `.ankiaddon`.
3. Reinicia Anki. Aparecerá el menú **Herramientas → Pagewise** y, la primera vez, el asistente de **primeros pasos**, que te guía por lo básico y marca lo que ya has hecho. Puedes volver a abrirlo desde el menú.

## Uso en el escritorio

1. **Herramientas → Pagewise → Gestionar fuentes… → Añadir PDF…**
   - La importación va en segundo plano con una barra de progreso (se puede cancelar cerrándola). Un libro de 1000 páginas tarda de uno a varios minutos.
   - Admite PDFs grandes (probado con 2 GB): ni la importación ni el visor cargan el archivo entero en memoria. Hace falta espacio en disco para la copia.
   - El PDF **se copia** dentro del add-on (`user_files/pdfs/`), así que puedes mover o borrar el original.
   - Si el PDF es escaneado (sin texto), el add-on te avisa: haría falta OCR, que esta versión aún no incluye.
   - Si el PDF tiene marcadores (índice), el add-on te propone términos para el glosario. Tú eliges cuáles añadir.
2. **Herramientas → Pagewise → Editar glosario…** Añade los términos que quieres subrayar y sus sinónimos, separados por `;`. También puedes importar una lista (`.txt`/`.csv` con una línea por término, `término; sinónimo; sinónimo`, o `.json`).
   - El subrayado no distingue mayúsculas ni tildes (`ciático` = `CIATICO`), pero sí la ñ (`año` ≠ `ano`).
   - Si un término está dentro de otro, gana el más largo («arteria femoral profunda» antes que «arteria femoral»).
   - Un término en singular también se reconoce en plural: «arteria» subraya «arterias», «nervio ciático» subraya «nervios ciáticos» y «agujero de conjunción» subraya «agujeros de conjunción». Lo mismo al buscar en tus fuentes y con **Buscar en fuentes** sobre un texto seleccionado.
3. Repasa como siempre:
   - Pasa el ratón por un término subrayado para ver los fragmentos (hasta 3 por fuente).
   - Haz clic en un fragmento para abrir el PDF en esa página, con el término **resaltado** en el texto (como al buscarlo con Ctrl+F).
   - **Más en mis fuentes** busca más resultados en el índice completo.
   - **Explicar** (Pro, escritorio): Claude, la IA de Anthropic, te explica el término a partir de los fragmentos de tus fuentes y cita la página. Necesita tu clave de la API de Anthropic (ver [Explicar](#explicar)).
   - Si seleccionas un texto cualquiera de la tarjeta, aparece **Buscar en fuentes** para hacer una búsqueda libre.

En el gestor puedes activar o desactivar fuentes, y también renombrarlas, reindexarlas o eliminarlas. Además, ves cuánto ocupan los datos exportados para el móvil.

## Activar el móvil (AnkiDroid, AnkiMobile, AnkiWeb)

1. En el escritorio: **Herramientas → Pagewise → Activar en tipos de nota…** y marca los tipos de nota que uses.
   - El add-on añade al final de sus plantillas un pequeño bloque entre `<!-- PAGEWISE:INICIO -->` y `<!-- PAGEWISE:FIN -->` que carga `_pagewise.js` y `_pagewise.css`.
   - Al desmarcarlo, se quita sin tocar nada más.
2. **Sincroniza en el escritorio** y luego **en el móvil**. Los datos (`_pagewise_glosario.json`, un `_pagewise_t_*.json` por término, `_pagewise.js` y `_pagewise.css`) viajan como archivos de medios.
   - Empiezan por `_`, así que «Comprobar medios» no los borra.
   - No van en una subcarpeta porque Anki no sincroniza subcarpetas de medios.
3. En el móvil, toca un término subrayado para ver el popup. Toca fuera para cerrarlo. En el móvil no hay visor de PDF: verás «Fuente, p. N».

Cada vez que importas, reindexas, editas el glosario o cambias la configuración, los datos se vuelven a exportar. Solo se reescribe lo que ha cambiado, para no resincronizar de más.

**Tamaño.** Cada término ocupa de 1 a 4 KB por fuente. 2000 términos con 3 fuentes rondan los 10 MB. El gestor muestra el total y avisa al superar `aviso_tamano_mb`.

**Si en el móvil no aparece el subrayado**, prueba esto:
- Comprueba que has sincronizado los medios en los dos lados.
- En AnkiDroid, si un toque en el término pasa la tarjeta, revisa los gestos de toque en *Ajustes → Controles*.
- AnkiWeb ejecuta el JavaScript de las plantillas de forma limitada: allí el soporte es «lo mejor posible».

## Versión gratuita y Pagewise Pro

- **Gratuita:** todo lo descrito arriba, con hasta **2 fuentes** (PDFs).
- **Pro:** fuentes ilimitadas y el botón «Explicar». El OCR para PDFs escaneados está en desarrollo.

Para activar Pro en la versión gratuita, pega tu licencia en **Herramientas → Pagewise → Pagewise Pro…**. Se comprueba en tu ordenador, sin conexión. Si una licencia caduca no pierdes nada: tus fuentes siguen funcionando y solo se bloquea añadir más de dos.

Cómo se emiten las licencias: `herramientas/README.md`.

**Edición Pro empaquetada.** `./build.sh --pro` genera `build/pagewise-pro-<versión>.ankiaddon`: el mismo add-on con una marca (`EDICION_PRO`) que quita el límite de fuentes sin pedir licencia, y que en Anki aparece como «Pagewise Pro». Se instala encima de la gratuita sin perder fuentes ni glosario. Cualquiera que tenga ese archivo tiene Pro: repártelo solo a quien haya pagado.

## Explicar

1. Consigue una clave de la API de Anthropic en [console.anthropic.com](https://console.anthropic.com/settings/keys). Cada explicación se cobra en tu cuenta de Anthropic (unos céntimos).
2. **Herramientas → Pagewise → Ajustes…**, pega la clave y pulsa **Comprobar la clave** (no gasta nada) y **Guardar**.
3. En el repaso, abre el popup de un término y pulsa **Explicar**. Tarda unos segundos. Cada término se explica una sola vez por sesión de Anki; las siguientes salen al instante.

Claude recibe el término, el texto de la tarjeta y hasta 12 fragmentos de tus fuentes sobre él, con su fuente y página. Se le pide que se apoye en ellos, que cite «(Fuente, p. N)» y que avise cuando algo no venga de tus fuentes. Puede equivocarse: compruébalo en el PDF.

Por defecto usa `claude-opus-5-5` con esfuerzo `low` (rápido). Se puede cambiar en la configuración (`explicar_modelo`, `explicar_esfuerzo`). Si no pones clave en Ajustes, se usa la variable de entorno `ANTHROPIC_API_KEY`, si existe.

## Ajustes

**Herramientas → Pagewise → Ajustes…** reúne lo que más se cambia:

- **Con qué se abre el PDF** al hacer clic en un fragmento: el visor de Pagewise (abre la página y resalta el término) o el visor de PDF del ordenador (abre el archivo; Pagewise te dice en qué página está, porque no se le puede pasar).
- **La clave de la API de Anthropic** para «Explicar».

## Configuración

El resto se cambia en **Herramientas → Complementos → Pagewise → Configuración** (ver `config.md`):

| Opción | Por defecto | Qué hace |
| --- | --- | --- |
| `subrayado` | `true` | Activa o desactiva el subrayado (en el móvil, tras sincronizar). |
| `fragmentos_por_fuente` | `3` | Fragmentos por fuente en el popup. |
| `max_caracteres_fragmento` | `300` | Longitud de cada fragmento. |
| `solo_primera_aparicion` | `true` | Subraya solo la primera vez que aparece cada término en una tarjeta. |
| `fuentes_inactivas` | `[]` | IDs de las fuentes que no se usan (mejor desde el gestor). |
| `aviso_tamano_mb` | `50` | Umbral del aviso de tamaño de los datos para el móvil. |
| `inyectar_en_escritorio` | `true` | En el escritorio, carga el script aunque la plantilla no tenga el bloque. |
| `visor_pdf` | `pdfjs` | Visor al hacer clic en un fragmento: `pdfjs` (resalta el término y aguanta PDFs de varios GB), `chromium` (el integrado de Anki, sin resaltado) o `sistema` (tu lector de PDF). Mejor desde Ajustes. |
| `explicar_modelo` | `claude-opus-5-5` | Modelo de Claude para «Explicar». |
| `explicar_esfuerzo` | `low` | Cuánto piensa Claude antes de explicar: `low`, `medium`, `high`, `xhigh` o `max`. Más esfuerzo, más espera y más coste. |

## Limitaciones conocidas

- El resaltado en el PDF depende del texto que pdf.js lee de la página: si el PDF lo guarda de forma rara (ligaduras, columnas partidas) puede abrirse la página sin marcar nada.
- En PDFs de más de 200 MB el visor solo prepara el resaltado de las páginas cercanas a la que miras, para no cargar el libro entero en memoria. Si buscas tú con la lupa del visor (Ctrl+F) sí recorre todo el libro, y entonces el consumo de memoria puede acercarse al tamaño del archivo.
- Sin OCR: los PDFs escaneados no se pueden indexar todavía.
- Un término repartido entre etiquetas de formato (`arteria <b>femoral</b>`) sí se detecta. No se detecta si lo corta un salto de línea, un párrafo, un enlace o una celda de tabla.
- En el anverso no se subraya dentro del hueco del cloze, para no revelar nada. En el reverso sí.
- No se subraya dentro de enlaces, botones de audio, código ni fórmulas MathJax.
- El índice (`user_files/`) es común a todos los perfiles de Anki del ordenador. Los datos del móvil se exportan a la colección del perfil abierto.
- Clientes muy antiguos que cargan las tarjetas desde `file://` y bloquean `fetch` y `XMLHttpRequest` no pueden leer los datos. Las versiones actuales de AnkiDroid y AnkiMobile no tienen este problema.

## Privacidad

- Sin «Explicar» no hay ninguna conexión de red. El visor de PDF lee tus PDFs a través del servidor local que Anki ya usa para mostrar las tarjetas (solo escucha en tu propio ordenador, `127.0.0.1`).
- El índice SQLite, el glosario y las copias de los PDFs se quedan en la carpeta `user_files/` del add-on, que sobrevive a las actualizaciones.
- Al móvil solo llegan los fragmentos exportados, por tu propia sincronización de AnkiWeb.
- **Explicar** (opcional, Pro) es lo único que sale de tu ordenador, y solo cuando lo pulsas: se envían a la API de Anthropic (`api.anthropic.com`) el término, el texto de la tarjeta y los fragmentos de tus fuentes sobre ese término. Nunca los PDFs completos. Tu clave se guarda en `user_files/clave_anthropic.txt`, fuera de la configuración de Anki.

## Desarrollo

```
pagewise/              ← el add-on (lo que va dentro del .ankiaddon)
  __init__.py         solo registra hooks y menús
  importer.py         PDF → páginas limpias → fragmentos (pypdf)
  index.py            SQLite + FTS5 (unicode61 remove_diacritics 2)
  textutil.py         normalización y matcher (gemelo del JS)
  providers.py        interfaz «fragmentos de un término» (hoy FTS; mañana semántica/LLM)
  exporter.py         JSON para el móvil en la carpeta de medios
  glossary.py         glosario (cargar, limpiar, importar, nombres de archivo)
  templates.py        insertar/quitar el bloque en las plantillas
  reviewer.py         card_will_show + mensajes pycmd
  core.py             rutas, configuración, exportación en segundo plano
  explicar.py         botón «Explicar»: petición a la API de Claude (urllib) y lectura de la respuesta
  licencia.py         licencias Pro: formato, verificación sin conexión y límite de la versión gratuita
  ed25519.py          firmas Ed25519 en Python puro (RFC 8032)
  migracion.py        migración de datos, medios y plantillas del nombre anterior («Fuentes»)
  i18n.py, i18n_en.py textos de la interfaz: español en el código, inglés en el diccionario
  ui/                 asistente, gestor, editor de glosario, tipos de nota, visor de PDF, importación
  web/pagewise.js/.css un único JS (ES5) para escritorio y móvil
  web/pdfjs/          visor de PDF: pdf.js 4.10 (Apache 2.0) con ajustes mínimos (ver LEEME-PAGEWISE.md)
  vendor/             pypdf 6.21 (BSD-3) y typing_extensions (PSF), Python puro
tests/                pytest (fuera de Anki) + tests/js (node:test + jsdom)
dev/                  demo, generadores de PDFs de prueba, e2e con Anki real, prueba móvil
herramientas/         emisión de licencias (para el vendedor; no va en el add-on)
build.sh              genera build/pagewise-<versión>.ankiaddon
```

**¿Por qué pypdf y no PyMuPDF?** pypdf es Python puro y cabe en un único `.ankiaddon` para Windows, macOS y Linux. PyMuPDF es más rápido, pero obliga a empaquetar binarios para cada plataforma y su licencia (AGPL) no encaja con un producto de pago sin licencia comercial.

**Acciones del popup.**
- En el JS, registra una acción con `Pagewise.registrarAccion({id, etiqueta, disponible, ejecutar})`. «Más en mis fuentes» y «Explicar» son ejemplos.
- «Explicar» (`explicar.py`) llama a la API de Mensajes con `urllib`, sin el SDK `anthropic`: el SDK necesita librerías compiladas que no caben en un único `.ankiaddon` para todos los sistemas. Responde en segundo plano y devuelve el resultado al popup con `Pagewise.__explicado(n, resultado)`.
- Los mensajes a Python van como `pycmd("pagewise:" + JSON)` y se atienden en `reviewer.COMANDOS`.

**Formatos de los datos** (en la carpeta de medios):
- `_pagewise_glosario.json`: `{"version":1, "ajustes":{"subrayado","fragmentos","soloPrimera"}, "terminos":[{"t","s":[sinónimos],"f":archivo}]}`
- `_pagewise_t_<slug>_<hash>.json`: `{"t":término, "fuentes":[{"id","nombre","fragmentos":[{"p":página, "e":etiqueta impresa opcional, "x":texto}]}]}`

### Probar

```bash
python3 -m pip install pytest reportlab
```

```bash
npm install
```

```bash
python3 -m pytest              # importer, index, exporter, glosario, plantillas, matcher
```

```bash
python3 -m pytest --lentos -s  # incluye un PDF de 1200 páginas
```

```bash
npm test                       # matcher y popup en JS (mismos casos que Python) + sintaxis ES5
```

La demo del popup en el navegador (con modo móvil, modo noche y `pycmd` simulado):

```bash
python3 -m http.server 8000
```

Abre `http://localhost:8000/dev/demo.html`.

La prueba «como en el móvil» con Chromium (emulación de Android e iPhone, WebView antiguo y modo noche) deja capturas en `dev/capturas/`:

```bash
node dev/prueba_movil.js
```

La prueba de extremo a extremo con un Anki real sin pantalla (necesita `pip install "aqt[qt6]==2.1.66" "reportlab<4.3"` en un Python 3.9):

```bash
python dev/e2e_anki.py --plantillas --paquete=build/pagewise-1.6.0.ankiaddon
```

Para generar el paquete:

```bash
./build.sh
```

Añade `--ingles` para probar la interfaz en inglés y `--migracion` para probar la migración desde el nombre anterior. Estos mismos tests se ejecutan solos en GitHub con cada cambio (`.github/workflows/tests.yml`).

**Traducciones.** Los textos van en español dentro de `tr("…")` y su traducción en `pagewise/i18n_en.py`; un test falla si falta alguna. Los textos del popup están en `TEXTOS`, en `web/pagewise.js`.

Todos los PDFs de prueba se generan con `dev/generar_pdfs.py` y contienen **texto inventado** escrito para este proyecto.

## English

**Pagewise** is an Anki add-on that underlines the terms on your cards and, on hover (desktop) or tap (mobile), shows the most relevant excerpts from **your own sources** (PDFs you import yourself) with their page number. On desktop, one click opens the PDF at that page inside Anki.

- Works on Anki desktop 2.1.66+ and, offline, on AnkiDroid, AnkiMobile and AnkiWeb (precomputed data travels with your own media sync).
- Everything is processed locally. No servers, nothing shared between users.
- The interface is in English whenever Anki is not set to Spanish.

**Install:** Tools → Add-ons → Install from file… → pick the `.ankiaddon`, then restart Anki. A *Getting started* window walks you through adding a PDF, building your glossary and enabling mobile.

**Legal note.** The add-on ships empty. Only import material you have the right to use; you are responsible for the content you load.
