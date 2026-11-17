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
    "Pagewise: error al exportar los datos para el móvil: %s": "Pagewise: error exporting the mobile data: %s",
    "Pagewise: %d términos exportados (%s)": "Pagewise: %d terms exported (%s)",
    "Pagewise: los datos para el móvil ocupan %s. Considera reducir el glosario o los fragmentos por fuente.":
        "Pagewise: the mobile data takes up %s. Consider trimming the glossary or the excerpts per source.",
    # --- importador
    "El PDF está protegido con contraseña.": "The PDF is password-protected.",
    "El PDF está cifrado y no se puede leer sin librerías extra.":
        "The PDF is encrypted and cannot be read without extra libraries.",
    "No se puede leer el PDF: %s": "Cannot read the PDF: %s",
    "Este PDF ya está importado como \"%s\".": "This PDF is already imported as \"%s\".",
    "Añadir PDFs a Pagewise": "Add PDFs to Pagewise",
    "PDF (*.pdf)": "PDF (*.pdf)",
    "leyendo texto": "reading text,",
    "%scopiando el PDF: %d de %d MB": "%scopying the PDF: %d of %d MB",
    "No hay espacio suficiente en el disco: el PDF ocupa %d MB y quedan %d MB libres.":
        "Not enough disk space: the PDF takes %d MB and only %d MB are free.",
    "indexando texto": "indexing text,",
    "%s%s página %d de %d": "%s%s page %d of %d",
    "Importando %d de %d: %s\n": "Importing %d of %d: %s\n",
    "Importando PDF…": "Importing PDF…",
    "Cancelado.": "Cancelled.",
    "Pagewise: error al importar: %s": "Pagewise: import error: %s",
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
    "Pagewise: error al reindexar: %s": "Pagewise: reindex error: %s",
    # --- términos propuestos
    "Pagewise: términos propuestos": "Pagewise: suggested terms",
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
    "Pagewise: %s": "Pagewise: %s",
    "Este Anki no puede mostrar el PDF dentro; se abre con el visor del sistema.":
        "This Anki cannot display the PDF inside; opening it with the system viewer.",
    "No se encuentra el PDF de esta fuente. Elimínala y vuelve a importarla.":
        "The PDF for this source is missing. Delete the source and import it again.",
    "Pagewise: visor integrado no disponible (%s); uso el del sistema.":
        "Pagewise: built-in viewer unavailable (%s); using the system viewer.",
    # --- gestor
    "Pagewise: gestionar fuentes": "Pagewise: manage sources",
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
    "Pagewise: editar glosario": "Pagewise: edit glossary",
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
    "Pagewise: activar en tipos de nota": "Pagewise: enable on note types",
    "Marca los tipos de nota en los que quieres el subrayado en el <b>móvil</b> (AnkiDroid, AnkiMobile, AnkiWeb). Se añade al final de sus plantillas un pequeño bloque que carga <code>_pagewise.js</code>; al desmarcar se quita sin tocar nada más.<br><br>En el escritorio no hace falta: allí el add-on lo carga solo.":
        "Tick the note types where you want underlining on <b>mobile</b> (AnkiDroid, AnkiMobile, AnkiWeb). "
        "A small block that loads <code>_pagewise.js</code> is added at the end of their templates; unticking "
        "removes it without touching anything else.<br><br>On desktop this is not needed: the add-on loads it by itself.",
    "  (parcial)": "  (partial)",
    "Aplicar": "Apply",
    "Plantillas actualizadas en %d tipos de nota.\n\nPara usarlo en el móvil: sincroniza aquí y después en el móvil (los datos viajan como medios).":
        "Templates updated on %d note types.\n\nTo use it on mobile: sync here, then sync on your phone "
        "(the data travels as media).",
    # --- asistente de primeros pasos
    "Pagewise: primeros pasos": "Pagewise: getting started",
    "<b>Pagewise</b> subraya los términos de tus tarjetas y te muestra qué dicen sobre ellos <b>tus propios PDFs</b>, con su página. Todo se procesa en este ordenador.<br><br>Importa solo material que tengas derecho a usar.":
        "<b>Pagewise</b> underlines the terms on your cards and shows what <b>your own PDFs</b> say about them, "
        "with page numbers. Everything is processed on this computer.<br><br>"
        "Only import material you have the right to use.",
    "<b>1. Añade un PDF</b><br>Un libro o tus apuntes, con texto (no escaneado).":
        "<b>1. Add a PDF</b><br>A book or your notes, with real text (not scanned).",
    "<b>2. Crea tu glosario</b><br>Los términos que quieres ver subrayados, con sus sinónimos.":
        "<b>2. Build your glossary</b><br>The terms you want underlined, with their synonyms.",
    "<b>3. Actívalo en el móvil</b> (opcional)<br>Elige los tipos de nota y sincroniza.":
        "<b>3. Enable it on mobile</b> (optional)<br>Pick your note types, then sync.",
    "¡Listo! Repasa una tarjeta que contenga alguno de tus términos y pasa el ratón por encima. Encontrarás todo en Herramientas → Pagewise.":
        "All set! Review a card containing one of your terms and hover over it. "
        "You will find everything under Tools → Pagewise.",
    "Ya tienes fuentes. Ahora añade los términos que quieres subrayar.":
        "You have sources. Now add the terms you want underlined.",
    "Empieza por el paso 1.": "Start with step 1.",
    # --- migración desde el nombre anterior
    "Fuentes ahora se llama Pagewise.\n\nTus PDFs, tu índice y tu glosario se han copiado a Pagewise y el complemento antiguo ha quedado desactivado.\n\nReinicia Anki. Después puedes eliminar «Fuentes» en Herramientas → Complementos.":
        "Fuentes is now called Pagewise.\n\nYour PDFs, index and glossary have been copied to Pagewise and the old "
        "add-on has been disabled.\n\nRestart Anki. Afterwards you can delete “Fuentes” under Tools → Add-ons.",
    # --- Pagewise Pro
    "Pagewise Pro…": "Pagewise Pro…",
    "Pagewise Pro": "Pagewise Pro",
    "Versión gratuita: hasta %d fuentes.": "Free version: up to %d sources.",
    "Pagewise Pro activo. Licencia de %s, válida hasta el %s.": "Pagewise Pro is active. Licensed to %s, valid until %s.",
    "Pagewise Pro activo. Licencia de %s, sin caducidad.": "Pagewise Pro is active. Licensed to %s, never expires.",
    "<b>Has llegado al límite de la versión gratuita: %d fuentes.</b><br>Para añadir más, activa Pagewise Pro o elimina una fuente.":
        "<b>You have reached the free version limit: %d sources.</b><br>To add more, activate Pagewise Pro or delete a source.",
    "Pagewise Pro incluye:<ul><li>Fuentes ilimitadas</li><li>PDFs escaneados con OCR <i>(en desarrollo)</i></li><li>Botón «Explicar»: Claude o ChatGPT te explican el término a partir de tus fuentes (con tu clave de su API)</li></ul>":
        "Pagewise Pro includes:<ul><li>Unlimited sources</li><li>Scanned PDFs with OCR <i>(in development)</i></li>"
        "<li>“Explain” button: Claude or ChatGPT explain the term from your sources (with your API key)</li></ul>",
    "Ajustes…": "Settings…",
    "Pagewise: ajustes": "Pagewise: settings",
    "Al hacer clic en un fragmento, abrir el PDF con": "When you click an excerpt, open the PDF with",
    "El visor de Pagewise: abre la página y resalta el término":
        "The Pagewise viewer: opens the page and highlights the term",
    "El visor de PDF del ordenador: abre el archivo y tú vas a la página":
        "Your computer's PDF viewer: opens the file and you go to the page",
    "Con el visor del ordenador no se puede saltar a la página ni resaltar: Pagewise te dice en qué página está.":
        "Your computer's viewer cannot jump to the page or highlight: Pagewise tells you which page it is.",
    "Botón «Explicar» (Pagewise Pro)": "“Explain” button (Pagewise Pro)",
    "«Explicar» pide a una IA que te explique el término a partir de los fragmentos de tus fuentes, citando la página. Elige Claude (Anthropic) o ChatGPT (OpenAI) y pon tu propia clave de su API: cada explicación cuesta unos céntimos en tu cuenta.<br><br><b>Privacidad:</b> es lo único de Pagewise que se conecta a internet, y solo cuando pulsas «Explicar». Se envían a la empresa que elijas el término, el texto de la tarjeta y los fragmentos de tus fuentes sobre ese término. Nunca se envían los PDFs completos.":
        "“Explain” asks an AI to explain the term from the excerpts of your sources, citing the page. "
        "Choose Claude (Anthropic) or ChatGPT (OpenAI) and add your own API key for it: each explanation "
        "costs a few cents on your account.<br><br><b>Privacy:</b> this is the only part of Pagewise that "
        "goes online, and only when you press “Explain”. The company you choose receives the term, the card "
        "text and the excerpts of your sources about that term. Whole PDFs are never sent.",
    "Usar:": "Use:",
    "Claude (Anthropic)": "Claude (Anthropic)",
    "ChatGPT (OpenAI)": "ChatGPT (OpenAI)",
    "Clave de la API de OpenAI:": "OpenAI API key:",
    "Clave de la API de Anthropic:": "Anthropic API key:",
    "Mostrar": "Show",
    "Comprobar la clave": "Check the key",
    "Conseguir una clave": "Get a key",
    "Necesitas Pagewise Pro para usar «Explicar». Puedes guardar la clave igualmente.":
        "You need Pagewise Pro to use “Explain”. You can save the key anyway.",
    "Para usar «Explicar», pega aquí la clave de la API que hayas elegido.":
        "To use “Explain”, paste the API key for the AI you chose here.",
    "Escribe primero la clave.": "Type the key first.",
    "Comprobando…": "Checking…",
    "✓ La clave funciona.": "✓ The key works.",
    "Ajustes guardados.": "Settings saved.",
    "%s: ve a la página %d.": "%s: go to page %d.",
    "Pega aquí tu licencia:": "Paste your license here:",
    "Pagewise Pro (edición completa): fuentes ilimitadas, sin licencia que activar.":
        "Pagewise Pro (full edition): unlimited sources, no license to activate.",
    "Activar licencia": "Activate license",
    "Conseguir Pagewise Pro": "Get Pagewise Pro",
    "Quitar la licencia de este ordenador": "Remove the license from this computer",
    "La licencia se comprueba en tu ordenador: Pagewise no se conecta a ningún servidor.":
        "The license is checked on your computer: Pagewise does not connect to any server.",
    "Ese texto no parece una licencia de Pagewise. Cópiala entera, desde «PW1.» hasta el final.":
        "That text does not look like a Pagewise license. Copy all of it, from “PW1.” to the end.",
    "La licencia no es válida. Comprueba que la has copiado entera y sin cambios.":
        "The license is not valid. Check that you copied all of it, unchanged.",
    "Esta licencia ha caducado. Tus fuentes siguen funcionando; renuévala para añadir más.":
        "This license has expired. Your sources keep working; renew it to add more.",
    "Pagewise Pro activado. Gracias, %s.": "Pagewise Pro activated. Thank you, %s.",
    "Licencia quitada de este ordenador.": "License removed from this computer.",
    "La versión gratuita admite %d fuentes: se importarán solo los primeros %d PDF de los %d elegidos.":
        "The free version allows %d sources: only the first %d of the %d PDFs you picked will be imported.",
}
