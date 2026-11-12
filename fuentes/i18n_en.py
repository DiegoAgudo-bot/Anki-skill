# -*- coding: utf-8 -*-
"""Traducción al inglés de la interfaz. Clave: el texto en español tal cual
aparece dentro de tr("…") en el código."""

EN = {
    # --- menú
    "Primeros pasos…": "Getting started…",
    "Gestionar fuentes…": "Manage sources…",
    "Editar glosario…": "Edit glossary…",
    "Activar en tipos de nota…": "Enable on note types…",
    "Exportar datos para el móvil ahora": "Export mobile data now",
    # --- core
    "Fuentes: error al exportar los datos para el móvil: %s": "Fuentes: error exporting the mobile data: %s",
    "Fuentes: %d términos exportados (%s)": "Fuentes: %d terms exported (%s)",
    "Fuentes: los datos para el móvil ocupan %s. Considera reducir el glosario o los fragmentos por fuente.":
        "Fuentes: the mobile data takes up %s. Consider trimming the glossary or the excerpts per source.",
    # --- importador
    "El PDF está protegido con contraseña.": "The PDF is password-protected.",
    "El PDF está cifrado y no se puede leer sin librerías extra.":
        "The PDF is encrypted and cannot be read without extra libraries.",
    "No se puede leer el PDF: %s": "Cannot read the PDF: %s",
    "Este PDF ya está importado como \"%s\".": "This PDF is already imported as \"%s\".",
    "Añadir PDFs a Fuentes": "Add PDFs to Fuentes",
    "PDF (*.pdf)": "PDF (*.pdf)",
    "leyendo texto": "reading text,",
    "indexando texto": "indexing text,",
    "%s%s página %d de %d": "%s%s page %d of %d",
    "Importando %d de %d: %s\n": "Importing %d of %d: %s\n",
    "Importando PDF…": "Importing PDF…",
    "Cancelado.": "Cancelled.",
    "Fuentes: error al importar: %s": "Fuentes: import error: %s",
    "✓ %s: %d páginas, %d fragmentos.": "✓ %s: %d pages, %d excerpts.",
    " Aviso: %d páginas sin texto (¿imágenes o escaneadas?).":
        " Note: %d pages without text (images or scanned?).",
    "✗ %s: parece un PDF escaneado (sin texto que se pueda extraer). Necesitaría OCR, que esta versión todavía no incluye. Si tienes una versión del PDF con texto, impórtala en su lugar.":
        "✗ %s: this looks like a scanned PDF (no extractable text). It would need OCR, which this version "
        "does not include yet. If you have a version of the PDF with text, import that one instead.",
    "Reindexando: %s página %d de %d": "Reindexing: %s page %d of %d",
    "Reindexando…": "Reindexing…",
    "Reindexado: %d páginas, %d fragmentos.": "Reindexed: %d pages, %d excerpts.",
    "Reindexado cancelado. La fuente queda incompleta: vuelve a reindexarla.":
        "Reindexing cancelled. The source is incomplete: reindex it again.",
    "Fuentes: error al reindexar: %s": "Fuentes: reindex error: %s",
    # --- términos propuestos
    "Fuentes: términos propuestos": "Fuentes: suggested terms",
    "Estos términos salen de los marcadores (índice) del PDF.\nMarca los que quieras añadir al glosario. Podrás editarlos después.":
        "These terms come from the PDF's bookmarks (outline).\nTick the ones you want to add to the glossary. "
        "You can edit them later.",
    "Marcar todos": "Select all",
    "Desmarcar todos": "Select none",
    "Añadir los marcados": "Add selected",
    "No añadir ninguno": "Add none",
    # --- visor
    "Abrir con el visor del sistema": "Open with the system viewer",
    "%s — página %d": "%s — page %d",
    "Fuentes: %s": "Fuentes: %s",
    "Este Anki no puede mostrar el PDF dentro; se abre con el visor del sistema.":
        "This Anki cannot display the PDF inside; opening it with the system viewer.",
    "No se encuentra el PDF de esta fuente. Elimínala y vuelve a importarla.":
        "The PDF for this source is missing. Delete the source and import it again.",
    "Fuentes: visor integrado no disponible (%s); uso el del sistema.":
        "Fuentes: built-in viewer unavailable (%s); using the system viewer.",
    # --- gestor
    "Fuentes: gestionar fuentes": "Fuentes: manage sources",
    "Importa solo material que tengas derecho a usar. Todo se procesa y se guarda en este ordenador; al móvil solo llega a través de tu propia sincronización con AnkiWeb.":
        "Only import material you have the right to use. Everything is processed and stored on this computer; "
        "it only reaches your phone through your own AnkiWeb sync.",
    "Activa": "Active",
    "Nombre": "Name",
    "Páginas": "Pages",
    "Fragmentos": "Excerpts",
    "Importada": "Imported",
    "Estado": "Status",
    "Añadir PDF…": "Add PDF…",
    "Renombrar…": "Rename…",
    "Abrir PDF": "Open PDF",
    "Reindexar": "Reindex",
    "Eliminar…": "Delete…",
    "Exportar para el móvil": "Export for mobile",
    "Cerrar": "Close",
    "Lista": "Ready",
    "Incompleta: reindexa": "Incomplete: reindex",
    "%d fuentes · %d términos en el glosario · Datos para el móvil: %s":
        "%d sources · %d glossary terms · Mobile data: %s",
    "  ⚠ más de %d MB: la sincronización con el móvil será lenta": "  ⚠ over %d MB: syncing to mobile will be slow",
    "Aún no hay fuentes. Pulsa «Añadir PDF…» para importar la primera.":
        "No sources yet. Click “Add PDF…” to import your first one.",
    "Selecciona primero una fuente.": "Select a source first.",
    "Renombrar fuente": "Rename source",
    "Nombre que verás en el popup:": "Name shown in the popup:",
    "¿Eliminar la fuente «%s»?\n\nSe borrarán su índice y la copia del PDF guardada por el add-on (tu archivo original no se toca).":
        "Delete the source “%s”?\n\nIts index and the PDF copy kept by the add-on will be removed "
        "(your original file is not touched).",
    "Eliminar fuente": "Delete source",
    "Fuente eliminada.": "Source deleted.",
    # --- editor de glosario
    "Fuentes: editar glosario": "Fuentes: edit glossary",
    "Cada término se subraya en tus tarjetas (sin distinguir mayúsculas ni tildes). Escribe los sinónimos separados por punto y coma.":
        "Each term is underlined on your cards (ignoring case and accents). Separate synonyms with semicolons.",
    "Filtrar:": "Filter:",
    "p. ej. arteria": "e.g. artery",
    "Activo": "Active",
    "Término": "Term",
    "Sinónimos": "Synonyms",
    "Añadir término": "Add term",
    "Eliminar seleccionados": "Delete selected",
    "Importar…": "Import…",
    "Exportar…": "Export…",
    "Cancelar": "Cancel",
    "Guardar": "Save",
    "%d términos": "%d terms",
    " (%d visibles)": " (%d shown)",
    "Selecciona primero los términos.": "Select the terms first.",
    "Importar glosario": "Import glossary",
    "Glosario (*.json *.txt *.csv *.tsv)": "Glossary (*.json *.txt *.csv *.tsv)",
    "No se pudo leer el archivo: %s": "Could not read the file: %s",
    "%d términos nuevos.": "%d new terms.",
    "Exportar glosario": "Export glossary",
    "JSON (*.json)": "JSON (*.json)",
    "Glosario exportado.": "Glossary exported.",
    "Glosario guardado: %d términos con fragmentos en tus fuentes.":
        "Glossary saved: %d terms with excerpts in your sources.",
    "\n\n%d términos no aparecen en ninguna fuente activa y no se subrayarán:\n%s":
        "\n\n%d terms do not appear in any active source and will not be underlined:\n%s",
    "¿Salir sin guardar los cambios del glosario?": "Close without saving your glossary changes?",
    # --- tipos de nota
    "Fuentes: activar en tipos de nota": "Fuentes: enable on note types",
    "Marca los tipos de nota en los que quieres el subrayado en el <b>móvil</b> (AnkiDroid, AnkiMobile, AnkiWeb). Se añade al final de sus plantillas un pequeño bloque que carga <code>_fuentes.js</code>; al desmarcar se quita sin tocar nada más.<br><br>En el escritorio no hace falta: allí el add-on lo carga solo.":
        "Tick the note types where you want underlining on <b>mobile</b> (AnkiDroid, AnkiMobile, AnkiWeb). "
        "A small block that loads <code>_fuentes.js</code> is added at the end of their templates; unticking "
        "removes it without touching anything else.<br><br>On desktop this is not needed: the add-on loads it by itself.",
    "  (parcial)": "  (partial)",
    "Aplicar": "Apply",
    "Plantillas actualizadas en %d tipos de nota.\n\nPara usarlo en el móvil: sincroniza aquí y después en el móvil (los datos viajan como medios).":
        "Templates updated on %d note types.\n\nTo use it on mobile: sync here, then sync on your phone "
        "(the data travels as media).",
    # --- asistente de primeros pasos
    "Fuentes: primeros pasos": "Fuentes: getting started",
    "<b>Fuentes</b> subraya los términos de tus tarjetas y te muestra qué dicen sobre ellos <b>tus propios PDFs</b>, con su página. Todo se procesa en este ordenador.<br><br>Importa solo material que tengas derecho a usar.":
        "<b>Fuentes</b> underlines the terms on your cards and shows what <b>your own PDFs</b> say about them, "
        "with page numbers. Everything is processed on this computer.<br><br>"
        "Only import material you have the right to use.",
    "<b>1. Añade un PDF</b><br>Un libro o tus apuntes, con texto (no escaneado).":
        "<b>1. Add a PDF</b><br>A book or your notes, with real text (not scanned).",
    "<b>2. Crea tu glosario</b><br>Los términos que quieres ver subrayados, con sus sinónimos.":
        "<b>2. Build your glossary</b><br>The terms you want underlined, with their synonyms.",
    "<b>3. Actívalo en el móvil</b> (opcional)<br>Elige los tipos de nota y sincroniza.":
        "<b>3. Enable it on mobile</b> (optional)<br>Pick your note types, then sync.",
    "¡Listo! Repasa una tarjeta que contenga alguno de tus términos y pasa el ratón por encima. Encontrarás todo en Herramientas → Fuentes.":
        "All set! Review a card containing one of your terms and hover over it. "
        "You will find everything under Tools → Fuentes.",
    "Ya tienes fuentes. Ahora añade los términos que quieres subrayar.":
        "You have sources. Now add the terms you want underlined.",
    "Empieza por el paso 1.": "Start with step 1.",
}
