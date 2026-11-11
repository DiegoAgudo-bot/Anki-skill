# -*- coding: utf-8 -*-
"""Índice local de fuentes: SQLite + FTS5.

Vive en user_files/index.sqlite3 (Anki no borra user_files al actualizar el
add-on). No depende de Anki.

Tablas:
  sources(id, nombre, archivo, ruta_original, fecha, paginas, sha1, estado)
  chunks(id, source_id, pagina, etiqueta, texto)
  chunks_fts: índice FTS5 sobre chunks.texto (contenido externo)

Si el SQLite no trae FTS5 (muy raro), se usa un plan B más lento con LIKE
sobre el texto normalizado.
"""
import datetime
import sqlite3

from .textutil import normalizar

_TOKENIZER_PREFERIDO = "unicode61 remove_diacritics 2"
_TOKENIZER_ANTIGUO = "unicode61 remove_diacritics 1"  # SQLite < 3.27

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    archivo TEXT NOT NULL,          -- nombre del PDF copiado en user_files/pdfs
    ruta_original TEXT,
    fecha TEXT NOT NULL,
    paginas INTEGER NOT NULL DEFAULT 0,
    sha1 TEXT,
    estado TEXT NOT NULL DEFAULT 'indexando'   -- 'indexando' | 'lista'
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    pagina INTEGER NOT NULL,        -- página física (1 = primera)
    etiqueta TEXT,                  -- número impreso si difiere (p. ej. 'xii')
    texto TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_source ON chunks(source_id);
CREATE TABLE IF NOT EXISTS meta (clave TEXT PRIMARY KEY, valor TEXT);
"""

_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    texto, content='chunks', content_rowid='id', tokenize='{tok}'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, texto) VALUES (new.id, new.texto);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, texto) VALUES ('delete', old.id, old.texto);
END;
"""


def _norm_sql(texto):
    return normalizar(texto or "")[0]


def consulta_fts(variantes):
    """Construye una consulta FTS5 segura: "frase 1" OR "frase 2"."""
    frases = []
    for v in variantes:
        v = " ".join(v.replace('"', " ").split())
        if v:
            frases.append('"%s"' % v)
    return " OR ".join(frases)


class Indice:
    def __init__(self, ruta, usar_fts=True):
        self.ruta = ruta
        self.db = sqlite3.connect(ruta, timeout=30, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        try:
            self.db.execute("PRAGMA journal_mode = WAL")
        except sqlite3.DatabaseError:
            pass
        self.db.create_function("fuentes_norm", 1, _norm_sql)
        self.db.executescript(_ESQUEMA)
        self.fts = usar_fts and self._preparar_fts()
        self.db.commit()

    def _preparar_fts(self):
        for tok in (_TOKENIZER_PREFERIDO, _TOKENIZER_ANTIGUO):
            try:
                self.db.executescript(_FTS.format(tok=tok))
                return True
            except sqlite3.OperationalError:
                continue
        return False

    def cerrar(self):
        self.db.close()

    # ------------------------------------------------------------------ fuentes

    def agregar_fuente(self, nombre, archivo, ruta_original, paginas, sha1):
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cur = self.db.execute(
            "INSERT INTO sources(nombre, archivo, ruta_original, fecha, paginas, sha1)"
            " VALUES (?,?,?,?,?,?)",
            (nombre, archivo, ruta_original, fecha, paginas, sha1),
        )
        self.db.commit()
        return cur.lastrowid

    def marcar_lista(self, source_id, paginas=None):
        if paginas is None:
            self.db.execute("UPDATE sources SET estado='lista' WHERE id=?", (source_id,))
        else:
            self.db.execute(
                "UPDATE sources SET estado='lista', paginas=? WHERE id=?", (paginas, source_id)
            )
        self.db.commit()

    def renombrar(self, source_id, nombre):
        self.db.execute("UPDATE sources SET nombre=? WHERE id=?", (nombre, source_id))
        self.db.commit()

    def borrar_fragmentos(self, source_id):
        self.db.execute("DELETE FROM chunks WHERE source_id=?", (source_id,))
        self.db.execute("UPDATE sources SET estado='indexando' WHERE id=?", (source_id,))
        self.db.commit()

    def eliminar_fuente(self, source_id):
        self.db.execute("DELETE FROM chunks WHERE source_id=?", (source_id,))
        self.db.execute("DELETE FROM sources WHERE id=?", (source_id,))
        self.db.commit()

    def fuente(self, source_id):
        fila = self.db.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
        return dict(fila) if fila else None

    def fuente_por_sha1(self, sha1):
        fila = self.db.execute("SELECT * FROM sources WHERE sha1=?", (sha1,)).fetchone()
        return dict(fila) if fila else None

    def fuentes(self):
        filas = self.db.execute(
            "SELECT s.*, (SELECT COUNT(*) FROM chunks c WHERE c.source_id=s.id) AS fragmentos"
            " FROM sources s ORDER BY s.nombre COLLATE NOCASE"
        ).fetchall()
        return [dict(f) for f in filas]

    # ------------------------------------------------------------------ fragmentos

    def agregar_fragmentos(self, source_id, filas):
        """filas: [(pagina, etiqueta, texto)]"""
        self.db.executemany(
            "INSERT INTO chunks(source_id, pagina, etiqueta, texto) VALUES (?,?,?,?)",
            [(source_id, p, e, t) for p, e, t in filas],
        )
        self.db.commit()

    def buscar(self, variantes, source_ids=None, limite=200, por_fuente=None):
        """Fragmentos que contienen alguna de las frases, del más al menos relevante.

        Con `por_fuente`, como mucho esos resultados de cada fuente (así una
        fuente muy grande no tapa a las demás).
        Devuelve [{source_id, pagina, etiqueta, texto}].
        """
        variantes = [v for v in variantes if v and v.strip()]
        if not variantes:
            return []
        filtro, params = "", []
        if source_ids is not None:
            if not source_ids:
                return []
            filtro = " AND c.source_id IN (%s)" % ",".join("?" * len(source_ids))
            params = list(source_ids)
        filtro += " AND s.estado='lista'"
        if self.fts:
            interna = (
                "SELECT c.source_id, c.pagina, c.etiqueta, c.texto, bm25(chunks_fts) AS rango"
                " FROM chunks_fts f JOIN chunks c ON c.id = f.rowid"
                " JOIN sources s ON s.id = c.source_id WHERE chunks_fts MATCH ?" + filtro
            )
            if por_fuente and self._ventanas():
                sql = (
                    "SELECT source_id, pagina, etiqueta, texto FROM ("
                    " SELECT x.*, ROW_NUMBER() OVER (PARTITION BY source_id ORDER BY rango) AS rn"
                    " FROM (" + interna + ") x) WHERE rn <= ? ORDER BY rango LIMIT ?"
                )
                args = [consulta_fts(variantes)] + params + [por_fuente, limite]
            else:
                sql = interna + " ORDER BY rango LIMIT ?"
                args = [consulta_fts(variantes)] + params + [limite]
            filas = self.db.execute(sql, args)
        else:
            # Plan B sin FTS5: LIKE sobre el texto normalizado (lento pero funciona).
            condiciones = " OR ".join(["fuentes_norm(c.texto) LIKE ?"] * len(variantes))
            sql = (
                "SELECT c.source_id, c.pagina, c.etiqueta, c.texto FROM chunks c"
                " JOIN sources s ON s.id = c.source_id WHERE (" + condiciones + ")"
                + filtro + " LIMIT ?"
            )
            likes = ["%" + _norm_sql(v).strip() + "%" for v in variantes]
            filas = self.db.execute(sql, likes + params + [limite])
        return [dict(f) for f in filas]

    def _ventanas(self):
        """¿Admite este SQLite funciones de ventana (3.25+)?"""
        return sqlite3.sqlite_version_info >= (3, 25, 0)

    def buscar_libre(self, texto, source_ids=None, limite=30):
        """Búsqueda de texto libre (todas las palabras, en cualquier orden)."""
        palabras = [p for p in _norm_sql(texto).replace('"', " ").split() if len(p) > 1]
        if not palabras:
            return []
        if not self.fts:
            return self._buscar_libre_sin_fts(palabras, source_ids, limite)
        consulta = " AND ".join('"%s"' % p for p in palabras[:12])
        filtro, params = " AND s.estado='lista'", []
        if source_ids is not None:
            if not source_ids:
                return []
            filtro += " AND c.source_id IN (%s)" % ",".join("?" * len(source_ids))
            params = list(source_ids)
        sql = (
            "SELECT c.source_id, c.pagina, c.etiqueta, c.texto FROM chunks_fts f"
            " JOIN chunks c ON c.id = f.rowid JOIN sources s ON s.id = c.source_id"
            " WHERE chunks_fts MATCH ?" + filtro + " ORDER BY bm25(chunks_fts) LIMIT ?"
        )
        return [dict(f) for f in self.db.execute(sql, [consulta] + params + [limite])]

    def _buscar_libre_sin_fts(self, palabras, source_ids, limite):
        condiciones = " AND ".join(["fuentes_norm(c.texto) LIKE ?"] * len(palabras))
        params = ["%" + p + "%" for p in palabras]
        filtro = " AND s.estado='lista'"
        if source_ids is not None:
            if not source_ids:
                return []
            filtro += " AND c.source_id IN (%s)" % ",".join("?" * len(source_ids))
            params += list(source_ids)
        sql = (
            "SELECT c.source_id, c.pagina, c.etiqueta, c.texto FROM chunks c"
            " JOIN sources s ON s.id = c.source_id WHERE " + condiciones + filtro + " LIMIT ?"
        )
        return [dict(f) for f in self.db.execute(sql, params + [limite])]

    # ------------------------------------------------------------------ meta

    def version(self):
        """Cambia cada vez que cambia el contenido (para saber si hay que reexportar)."""
        fila = self.db.execute(
            "SELECT COUNT(*), COALESCE(MAX(id),0) FROM chunks"
        ).fetchone()
        nombres = self.db.execute(
            "SELECT GROUP_CONCAT(id || ':' || nombre || ':' || estado, '|') FROM sources"
        ).fetchone()[0]
        return "%s-%s-%s" % (fila[0], fila[1], nombres or "")
