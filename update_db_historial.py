import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Crear tabla de historial
c.execute('''
CREATE TABLE IF NOT EXISTS historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tramite_id INTEGER,
    usuario TEXT,
    accion TEXT,
    valor_anterior TEXT,
    valor_nuevo TEXT,
    fecha TEXT,
    FOREIGN KEY (tramite_id) REFERENCES tramites (id)
)
''')

conn.commit()
conn.close()
print("Tabla 'historial' creada correctamente.")