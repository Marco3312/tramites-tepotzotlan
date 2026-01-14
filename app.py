from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
import sqlite3
import bcrypt
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# === PROTECCIÓN DE RUTAS ===
def requiere_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or not session.get('user_type'):
            flash('Debes iniciar sesión para acceder a esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# === TUS HASHES (LOS QUE GENERASTE) ===
HASH_MIGUEL = "$2b$12$L8Olhn.ialIiOccjcn63CeAZ4FYg2dQ9nVNLLZNT3rFmknx9ambpi"
HASH_ULISES = "$2b$12$3ITwlK92/byktGK4w3kfBu4wLyVNgB8NxAO470aUEXlmUcbb0uake"
HASH_PASANTE = "$2b$12$FEquB9LL8UPC9P3Xti9vu.uV00fpfKg9/.fYOrenv0sZ9Oj4t8Ja."

@app.route('/requisitos')
def requisitos():
    return render_template('requisitos.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        if username == 'MIGUELANGEL' and bcrypt.checkpw(password, HASH_MIGUEL.encode('utf-8')):
            session['logged_in'] = True
            session['user_type'] = 'admin'
            session['username'] = username
            return redirect(url_for('seleccion_tramites'))
        elif username == 'Ulises Rangel' and bcrypt.checkpw(password, HASH_ULISES.encode('utf-8')):
            session['logged_in'] = True
            session['user_type'] = 'admin'
            session['username'] = username
            return redirect(url_for('seleccion_tramites'))
        elif username == 'pasante' and bcrypt.checkpw(password, HASH_PASANTE.encode('utf-8')):
            session['logged_in'] = True
            session['user_type'] = 'pasante'
            session['username'] = username
            return redirect(url_for('seleccion_tramites'))
        else:
            flash('Usuario o contraseña incorrectos.')
    return render_template('login.html')

@app.route('/seleccion_tramites')
@requiere_login
def seleccion_tramites():
    conn = get_db_connection()
    por_revision = conn.execute("SELECT COUNT(*) FROM tramites WHERE estatus = 'Por revisión'").fetchone()[0]
    conn.close()
    return render_template('seleccion_tramites.html', 
                         user_type=session.get('user_type'),
                         por_revision=por_revision)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/tramite/<tipo>', methods=['GET', 'POST'])
@requiere_login
def tramite(tipo):
    if session.get('user_type') != 'admin':
        flash('No tienes permisos para subir trámites.')
        return redirect(url_for('seleccion_tramites'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        notes = request.form.get('notes', '')

        if not nombre:
            flash('Debes poner un nombre para guardar.')
            return redirect(url_for('tramite', tipo=tipo))

        pdfs = []
        for field in request.files:
            file = request.files[field]
            if file and allowed_file(file.filename):
                if file.content_length > MAX_FILE_SIZE:
                    flash(f"El archivo '{file.filename}' es demasiado grande (máx 10MB).")
                    continue
                filename = file.filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                pdfs.append(filename)

        if not pdfs:
            flash('Debes subir al menos un archivo PDF.')
            return redirect(url_for('tramite', tipo=tipo))

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO tramites (nombre, tipo_tramite, pdfs, notes) VALUES (?, ?, ?, ?)',
                  (nombre, tipo, ','.join(pdfs), notes))
        conn.commit()
        conn.close()
        flash('Trámite guardado correctamente.')
        return redirect(url_for('ver_tramites_tipo', tipo=tipo))

    return render_template('tramite.html', tipo=tipo)

@app.route('/ver_tramites')
@requiere_login
def ver_tramites():
    if session.get('user_type') != 'admin':
        flash('No tienes permisos.')
        return redirect(url_for('seleccion_tramites'))
    conn = get_db_connection()
    tramites = conn.execute('SELECT * FROM tramites WHERE estatus != ?', ('Completado',)).fetchall()
    conn.close()
    return render_template('ver_tramites.html', tramites=tramites, tipo='Todos', user_type=session.get('user_type'))

@app.route('/ver_tramites/<tipo>')
@requiere_login
def ver_tramites_tipo(tipo):
    conn = get_db_connection()
    tramites = conn.execute('SELECT * FROM tramites WHERE tipo_tramite = ? AND estatus != ?', (tipo, 'Completado')).fetchall()
    conn.close()
    return render_template('ver_tramites.html', tramites=tramites, tipo=tipo, user_type=session.get('user_type'))

@app.route('/ver_tramites_completados')
@requiere_login
def ver_tramites_completados():
    conn = get_db_connection()
    tramites = conn.execute('SELECT * FROM tramites WHERE estatus = ?', ('Completado',)).fetchall()
    conn.close()
    return render_template('ver_tramites_completados.html', tramites=tramites, user_type=session.get('user_type'))

@app.route('/ver_tramite/<int:id>', methods=['GET', 'POST'])
@requiere_login
def ver_tramite(id):
    conn = get_db_connection()
    tramite = conn.execute('SELECT * FROM tramites WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        if session.get('user_type') != 'admin':
            flash('No tienes permisos para modificar trámites.')
            conn.close()
            return redirect(url_for('ver_tramite', id=id))

        usuario = session.get('username', 'Admin')
        fecha = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')
        c = conn.cursor()

        if 'estatus' in request.form:
            nuevo = request.form['estatus']
            anterior = tramite['estatus']
            if nuevo != anterior:
                c.execute('UPDATE tramites SET estatus = ? WHERE id = ?', (nuevo, id))
                c.execute('INSERT INTO historial (tramite_id, usuario, accion, valor_anterior, valor_nuevo, fecha) VALUES (?, ?, ?, ?, ?, ?)',
                          (id, usuario, 'Cambio de estatus', anterior, nuevo, fecha))
                conn.commit()
                flash('Estatus actualizado.')

        elif 'notes' in request.form:
            nuevo = request.form['notes']
            anterior = tramite['notes'] or ''
            if nuevo != anterior:
                c.execute('UPDATE tramites SET notes = ? WHERE id = ?', (nuevo, id))
                c.execute('INSERT INTO historial (tramite_id, usuario, accion, valor_anterior, valor_nuevo, fecha) VALUES (?, ?, ?, ?, ?, ?)',
                          (id, usuario, 'Edición de notas', anterior[:50] + ('...' if len(anterior) > 50 else ''), 
                           nuevo[:50] + ('...' if len(nuevo) > 50 else ''), fecha))
                conn.commit()
                flash('Notas actualizadas.')

        elif 'reemplazar' in request.files:
            new_pdf = request.files['reemplazar']
            if new_pdf and allowed_file(new_pdf.filename):
                if new_pdf.content_length > MAX_FILE_SIZE:
                    flash("El archivo nuevo excede 10MB.")
                else:
                    new_filename = new_pdf.filename
                    new_pdf.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    pdfs = tramite['pdfs'].split(',')
                    anterior_pdf = pdfs[0]
                    pdfs[0] = new_filename
                    c.execute('UPDATE tramites SET pdfs = ? WHERE id = ?', (','.join(pdfs), id))
                    c.execute('INSERT INTO historial (tramite_id, usuario, accion, valor_anterior, valor_nuevo, fecha) VALUES (?, ?, ?, ?, ?, ?)',
                              (id, usuario, 'Reemplazo de PDF', anterior_pdf, new_filename, fecha))
                    conn.commit()
                    flash('Archivo reemplazado.')

        elif 'eliminar' in request.form:
            pdf_to_delete = request.form['eliminar']
            pdfs = tramite['pdfs'].split(',')
            if pdf_to_delete in pdfs:
                c.execute('INSERT INTO historial (tramite_id, usuario, accion, valor_anterior, valor_nuevo, fecha) VALUES (?, ?, ?, ?, ?, ?)',
                          (id, usuario, 'Eliminación de PDF', pdf_to_delete, 'Eliminado', fecha))
                pdfs.remove(pdf_to_delete)
                c.execute('UPDATE tramites SET pdfs = ? WHERE id = ?', (','.join(pdfs), id))
                conn.commit()
                flash('Archivo eliminado.')

        conn.close()
        return redirect(url_for('ver_tramite', id=id))

    historial = conn.execute('SELECT * FROM historial WHERE tramite_id = ? ORDER BY fecha DESC', (id,)).fetchall()
    conn.close()

    return render_template('ver_tramite.html', tramite=tramite, user_type=session.get('user_type'), historial=historial)

@requiere_login
@app.route('/eliminar_tramite/<int:id>', methods=['POST'])
@requiere_login
def eliminar_tramite(id):
    if session.get('user_type') != 'admin':
        flash('No tienes permisos para eliminar trámites.')
        return redirect(url_for('ver_tramite', id=id))
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Borrar PDFs del disco si existen
    tramite = c.execute('SELECT pdfs FROM tramites WHERE id = ?', (id,)).fetchone()
    if tramite and tramite['pdfs']:
        pdfs = tramite['pdfs'].split(',')
        for pdf in pdfs:
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf.strip())
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    
    # Borrar historial relacionado
    c.execute('DELETE FROM historial WHERE tramite_id = ?', (id,))
    
    # Borrar el trámite
    c.execute('DELETE FROM tramites WHERE id = ?', (id,))
    
    conn.commit()
    conn.close()
    
    flash('Trámite eliminado completamente.')
    return redirect(url_for('seleccion_tramites'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':

    app.run(debug=True)




