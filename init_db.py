import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Tabla para trámites (con columna notes)
c.execute('''
    CREATE TABLE IF NOT EXISTS tramites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo_tramite TEXT NOT NULL,
        estatus TEXT DEFAULT 'En trámite',  -- Opciones: En trámite, Pausado, Cancelado, Por revisión
        pdfs TEXT,
        notes TEXT DEFAULT ''  -- Columna para notas, por defecto vacía
    )
''')

conn.commit()
conn.close()
print("Base de datos creada correctamente.")