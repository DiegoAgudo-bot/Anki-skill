# pdf.js dentro de Pagewise

Visor de PDF del add-on: [pdf.js](https://github.com/mozilla/pdf.js) 4.10.38, versión
«legacy» (`pdfjs-4.10.38-legacy-dist.zip`), licencia Apache 2.0 (`LICENSE`).

Se usa la 4.10 legacy porque funciona con el Chromium 108 de Anki 2.1.66 (Qt 6.5).

## Qué se ha quitado

Mapas de código (`*.map`), `pdf.sandbox.mjs` (scripts dentro del PDF, desactivados),
el depurador, el PDF de ejemplo y todos los idiomas salvo `en-US` y `es-ES`
(`web/locale/locale.json` reducido a esos dos).

## Qué se ha cambiado

1. `web/viewer.html`: título y una etiqueta `<script src="pagewise-visor.js">`.
2. `web/viewer.mjs`: el método `#extractText` (marcado con `PAGEWISE`) deja que
   `pagewise-visor.js` decida en qué orden se lee el texto de las páginas.
3. `web/viewer.css`: es el original pasado por lightningcss para Chromium 108
   (que no entiende CSS anidado): `npx lightningcss --targets 'chrome 108' viewer.css -o viewer.css`.
4. `web/pagewise-visor.js`: nuevo. Ajustes, salto a página con resaltado y modo «PDF grande».

## Para actualizar pdf.js

Repite los pasos de arriba sobre la nueva versión y pasa `dev/e2e_anki.py` con
Anki 2.1.66 + PyQt 6.5 y con el Anki actual, también con `--pdf-grande=`.
