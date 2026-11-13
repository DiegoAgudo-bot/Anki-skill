# Landing de Pagewise

Una página (`index.html`, más la carpeta `video/`) con la demo en vivo y la lista de espera.
No necesita servidor propio: vale cualquier alojamiento de páginas estáticas.

- `src/pagina.html`: contenido y estilos.
- `src/demo.js`: la demo (subrayado, popup, zona de pruebas) y el envío de la lista.
- `config.json`: ajustes.
- `build.py`: genera `index.html`.
- `prueba.js`: comprobaciones con Chromium.
- `video/`: el vídeo de 30 segundos (MP4 y WebM) y su carátula. Hay que publicarla junto a `index.html`.

Los textos de ejemplo de la demo son apuntes inventados.

## Cambiar algo

Edita `src/` o `config.json` y regenera la página:

```bash
python3 landing/build.py
```

```bash
node landing/prueba.js
```

## Conectar la lista de espera

1. Crea un formulario en un servicio que acepte envíos en JSON y devuelva una dirección de envío (por ejemplo Formspree, plan gratuito).
2. Pon esa dirección en `config.json`, en `lista_endpoint`.
3. Regenera la página.

Mientras `lista_endpoint` esté vacío, el formulario avisa de que la lista aún no está abierta: nunca dice «apuntado» sin haber guardado el correo.

Al recoger correos tratas datos personales: necesitas una política de privacidad enlazada desde la página y una forma de darse de baja.

## Publicar

Con GitHub Pages: en el repositorio, *Settings → Pages*, elige publicar desde una rama y la carpeta de la landing, o sube `index.html` a cualquier alojamiento estático. Después pon la dirección final en `url_publica` y regenera.

Antes de publicar revisa en `config.json` que `descarga_url` apunta a un sitio que los visitantes puedan abrir (un repositorio privado no sirve).

## Regenerar el vídeo

El vídeo se monta con capturas reales del add-on en Anki (PDFs de prueba con texto inventado):

1. `python dev/capturas_anki.py carpeta/cap` (con un Python que tenga `aqt`) saca las capturas y las posiciones del cursor.
2. Copia `dev/video/player.html` y `dev/video/render.js` a `carpeta/` y ejecuta `node render.js 30`: dibuja los 900 fotogramas.
3. Únelos con ffmpeg: `ffmpeg -framerate 30 -i frames/%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart pagewise-30s.mp4`.

El guion (textos y tiempos) está en `dev/video/player.html`.
