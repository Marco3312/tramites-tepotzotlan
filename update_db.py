import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Añadir columna 'notes' si no existe
c.execute('''
    ALTER TABLE tramites ADD COLUMN notes TEXT DEFAULT ''
''')

conn.commit()
conn.close()
print("Base de datos actualizada: columna 'notes' añadida.")