#!/usr/bin/env bash
# Genera build/pagewise-<versión>.ankiaddon (un .zip con el CONTENIDO de pagewise/).
#
#   ./build.sh              pasa los tests y empaqueta la versión gratuita
#   ./build.sh --sin-tests  solo empaqueta
#   ./build.sh --pro        edición Pro: sin límite de fuentes y sin licencia
#                           (se puede combinar con --sin-tests)
#
# El paquete se distribuye VACÍO: sin PDFs, índices ni glosarios. El script
# lo comprueba y falla si encuentra datos de usuario dentro.
set -euo pipefail
cd "$(dirname "$0")"

PRO=0
TESTS=1
for arg in "$@"; do
  case "$arg" in
    --pro) PRO=1 ;;
    --sin-tests) TESTS=0 ;;
    *) echo "Opción desconocida: $arg"; exit 1 ;;
  esac
done

if [[ $TESTS == 1 ]]; then
  echo "== Tests de Python"
  python3 -m pytest -q
  echo "== Tests de JavaScript"
  npm test --silent
fi

VERSION=$(python3 -c "import json;print(json.load(open('pagewise/manifest.json'))['human_version'])")
mkdir -p build
if [[ $PRO == 1 ]]; then
  SALIDA="build/pagewise-pro-${VERSION}.ankiaddon"
else
  SALIDA="build/pagewise-${VERSION}.ankiaddon"
fi
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

if [[ $PRO == 1 ]]; then
  # Edición Pro: la marca EDICION_PRO en la raíz quita el límite de fuentes, y
  # el nombre visible en Anki lo dice. El paquete sigue siendo "pagewise", así
  # que se instala encima de la versión gratuita sin perder datos.
  TMP=$(mktemp -d)
  trap 'rm -rf "$TMP"' EXIT
  printf 'Pagewise Pro: edición completa, sin límite de fuentes.\n' > "$TMP/EDICION_PRO"
  python3 - pagewise/manifest.json "$TMP/manifest.json" <<'EOF2'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
m["name"] = m["name"].replace("Pagewise", "Pagewise Pro", 1)
json.dump(m, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=4)
EOF2
  zip -q -d "$SALIDA" manifest.json
  ABS="$(pwd)/$SALIDA"
  (cd "$TMP" && zip -q -X "$ABS" EDICION_PRO manifest.json)
fi

echo "== Comprobando el contenido"
python3 - "$SALIDA" "$PRO" <<'EOF'
import json, sys, zipfile
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
pro = sys.argv[2] == "1"
assert ("EDICION_PRO" in nombres) == pro, "marca de edición Pro donde no toca"
nombre = json.loads(z.read("manifest.json"))["name"]
assert nombre.startswith("Pagewise Pro") == pro, nombre
print("Edición:", "Pro (sin límite de fuentes)" if pro else "gratuita (%s)" % nombre)
print("%d archivos, %.0f KB" % (len(nombres), sum(i.compress_size for i in z.infolist()) / 1024))
EOF
echo "Listo: $SALIDA"
