**Pagewise — configuración**

- `subrayado`: activa o desactiva el subrayado de términos (escritorio y móvil, tras sincronizar).
- `fragmentos_por_fuente`: cuántos fragmentos de cada fuente se muestran en el popup (máximo recomendado: 3).
- `max_caracteres_fragmento`: longitud de cada fragmento. Más largo = más espacio en los medios sincronizados.
- `solo_primera_aparicion`: subraya solo la primera vez que aparece cada término en la tarjeta.
- `fuentes_inactivas`: lista de IDs de fuentes que NO se usan (todas las demás están activas). Es más cómodo cambiarlo desde *Herramientas → Pagewise → Gestionar fuentes*.
- `aviso_tamano_mb`: avisa si los datos exportados para el móvil superan este tamaño.
- `inyectar_en_escritorio`: en escritorio, carga el script automáticamente aunque la plantilla no tenga el snippet.
- `visor_pdf`: con qué se abre el PDF al hacer clic en un fragmento. `pdfjs` (por defecto) abre la página y resalta el texto, y aguanta PDFs de varios GB; `chromium` usa el visor integrado de Anki, sin resaltado; `sistema` abre tu lector de PDF habitual. Es más cómodo cambiarlo en *Herramientas → Pagewise → Ajustes*.
- `explicar_modelo`: modelo de Claude que usa el botón «Explicar» (por defecto `claude-opus-5-5`).
- `explicar_esfuerzo`: cuánto piensa Claude antes de explicar: `low` (por defecto, más rápido), `medium`, `high`, `xhigh` o `max`. La clave de API se pone en *Ajustes*, no aquí.
- `asistente_visto`: ponlo en `false` para volver a ver el asistente de primeros pasos al abrir Anki.

Al guardar, los datos del móvil se vuelven a exportar.
