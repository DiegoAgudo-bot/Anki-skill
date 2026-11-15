#!/usr/bin/env bash
# Genera build/pagewise-<versión>.ankiaddon (un .zip con el CONTENIDO de pagewise/).
#
#   ./build.sh              pasa los tests y empaqueta
#   ./build.sh --sin-tests  solo empaqueta
#
# El paquete se distribuye VACÍO: sin PDFs, índices ni glosarios. El script
# lo comprueba y falla si encuentra datos de usuario dentro.
set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" != "--sin-tests" ]]; then
  echo "== Tests de Python"
  python3 -m pytest -q
  echo "== Tests de JavaScript"
  npm test --silent
fi

VERSION=$(python3 -c "import json;print(json.load(open('pagewise/manifest.json'))['human_version'])")
mkdir -p build
SALIDA="build/pagewise-${VERSION}.ankiaddon"
rm -f "$SALIDA"

# Si hay archivos nuevos sin añadir a git se quedarían fuera sin avisar.
SIN_SEGUIR=$(git status --porcelain -- pagewise | grep '^??' || true)
if [[ -n "$SIN_SEGUIR" ]]; then
  echo "Hay archivos en pagewise/ sin añadir a git (git add) y no entrarían en el paquete:"
  echo "$SIN_SEGUIR"
  exit 1
fi

# Solo se empaqueta lo que está bajo control de versiones (así nunca se
# cuelan user_files/, meta.json ni cachés). user_files/ va con su README.
(cd pagewise && git ls-files -z . | xargs -0 zip -q -X "../$SALIDA")

echo "== Comprobando el contenido"
python3 - "$SALIDA" <<'EOF'
import sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
nombres = z.namelist()
prohibido = [n for n in nombres if n.endswith((".pdf", ".sqlite3", ".pyc", ".clave-privada", "licencia.txt")) or n == "meta.json"
             or (n.startswith("user_files/") and n != "user_files/README.txt")
             or n.endswith("glosario.json")]
assert not prohibido, "datos de usuario dentro del paquete: %s" % prohibido
for necesario in ("__init__.py", "manifest.json", "config.json", "web/pagewise.js", "i18n_en.py",
                  "ui/asistente.py", "licencia.py", "ed25519.py", "ui/pro.py",
                  "web/pagewise.css", "vendor/pypdf/__init__.py", "user_files/README.txt",
                  "web/pdfjs/LICENSE", "web/pdfjs/web/viewer.html", "web/pdfjs/web/viewer.mjs",
                  "web/pdfjs/web/pagewise-visor.js", "web/pdfjs/build/pdf.mjs", "web/pdfjs/build/pdf.worker.mjs"):
    assert necesario in nombres, "falta " + necesario
assert not any(n.startswith("pagewise/") for n in nombres), "el zip no debe llevar la carpeta raíz"
print("%d archivos, %.0f KB" % (len(nombres), sum(i.compress_size for i in z.infolist()) / 1024))
EOF
echo "Listo: $SALIDA"
