# Struktur folder proyek:
# spk_kucing_saw/
# ├── app.py
# ├── templates/
# │   ├── index.html
# │   ├── hasil.html
# │   ├── admin.html
# │   ├── tambah_kucing.html
# │   ├── edit_kucing.html
# │   ├── login.html
# │   ├── pengguna.html
# │   ├── ubah_password.html
# └── static/

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'rahasia_super_aman'

def get_db():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    conn = get_db()
    kriteria = conn.execute('SELECT * FROM kriteria').fetchall()
    return render_template('index.html', kriteria=kriteria)

@app.route('/hasil', methods=['POST'])
def hasil():
    conn = get_db()
    kriteria = conn.execute('SELECT * FROM kriteria').fetchall()
    bobot = {str(k['id']): float(request.form.get(f"bobot_{k['id']}")) for k in kriteria}

    ras = conn.execute('SELECT * FROM ras_kucing').fetchall()
    if not ras:
        flash("Data ras kucing masih kosong. Silakan tambahkan data terlebih dahulu.", "warning")
        return redirect(url_for("index"))

    data_nilai = {}
    for r in ras:
        nilai = conn.execute('SELECT id_kriteria, nilai FROM nilai_alternatif WHERE id_kucing = ?', (r['id'],)).fetchall()
        data_nilai[r['id']] = {n['id_kriteria']: n['nilai'] for n in nilai}

    normal = {}
    for k in kriteria:
        # Ambil nilai untuk kriteria k dari semua ras yang punya nilai
        nilai_k = [data_nilai[r['id']][k['id']] for r in ras if k['id'] in data_nilai[r['id']]]
        if not nilai_k:
            flash(f"Nilai untuk kriteria '{k['nama_kriteria']}' belum lengkap.", "warning")
            return redirect(url_for("index"))

        if k['sifat'] == 'benefit':
            max_v = max(nilai_k)
            for r in ras:
                if k['id'] in data_nilai[r['id']]:
                    normal.setdefault(r['id'], {})[k['id']] = data_nilai[r['id']][k['id']] / max_v
                else:
                    normal.setdefault(r['id'], {})[k['id']] = 0
        else:
            min_v = min(nilai_k)
            for r in ras:
                if k['id'] in data_nilai[r['id']]:
                    normal.setdefault(r['id'], {})[k['id']] = min_v / data_nilai[r['id']][k['id']]
                else:
                    normal.setdefault(r['id'], {})[k['id']] = 0

    hasil = []
    for r in ras:
        skor = sum(normal[r['id']][k['id']] * bobot[str(k['id'])] for k in kriteria)
        hasil.append({
            'nama': r['nama_ras'],
            'skor': skor,
            'deskripsi': r['deskripsi'],
            'foto_url': r['foto_url']  # pastikan ini ada
        })

    hasil.sort(key=lambda x: x['skor'], reverse=True)
    return render_template('hasil.html', hasil=hasil)

@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = get_db()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hash_password(password)
        user = conn.execute('SELECT * FROM pengguna WHERE username = ? AND password = ?', (username, password_hash)).fetchone()
        if user:
            session['admin'] = True
            session['username'] = username
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Username atau password salah!', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda berhasil logout.', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db()
    ras = conn.execute('SELECT * FROM ras_kucing').fetchall()
    return render_template('admin.html', ras=ras)

@app.route('/tambah', methods=['GET', 'POST'])
def tambah_kucing():
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        nama_ras = request.form['nama_ras']
        deskripsi = request.form['deskripsi']
        foto_url = request.form.get('foto_url', '')
        conn.execute('INSERT INTO ras_kucing (nama_ras, deskripsi, foto_url) VALUES (?, ?, ?)', (nama_ras, deskripsi, foto_url))
        conn.commit()
        id_kucing = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        kriteria = conn.execute('SELECT * FROM kriteria').fetchall()
        for k in kriteria:
            nilai = float(request.form.get(f"nilai_{k['id']}"))
            conn.execute('INSERT INTO nilai_alternatif (id_kucing, id_kriteria, nilai) VALUES (?, ?, ?)',
                         (id_kucing, k['id'], nilai))
        conn.commit()
        flash('Data kucing berhasil ditambahkan!', 'success')
        return redirect(url_for('admin'))

    kriteria = conn.execute('SELECT * FROM kriteria').fetchall()
    return render_template('tambah_kucing.html', kriteria=kriteria)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_kucing(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        nama_ras = request.form['nama_ras']
        deskripsi = request.form['deskripsi']
        foto_url = request.form.get('foto_url', '')
        conn.execute('UPDATE ras_kucing SET nama_ras = ?, deskripsi = ?, foto_url = ? WHERE id = ?', (nama_ras, deskripsi, foto_url, id))

        kriteria = conn.execute('SELECT * FROM kriteria').fetchall()
        for k in kriteria:
            nilai = float(request.form.get(f"nilai_{k['id']}"))
            conn.execute('UPDATE nilai_alternatif SET nilai = ? WHERE id_kucing = ? AND id_kriteria = ?',
                         (nilai, id, k['id']))
        conn.commit()
        flash('Data kucing berhasil diupdate!', 'success')
        return redirect(url_for('edit_kucing', id=id))

    kucing = conn.execute('SELECT * FROM ras_kucing WHERE id = ?', (id,)).fetchone()
    kriteria = conn.execute('SELECT * FROM kriteria').fetchall()
    nilai = conn.execute('SELECT * FROM nilai_alternatif WHERE id_kucing = ?', (id,)).fetchall()
    nilai_dict = {n['id_kriteria']: n['nilai'] for n in nilai}
    return render_template('edit_kucing.html', kucing=kucing, kriteria=kriteria, nilai=nilai_dict)


@app.route('/hapus/<int:id>')
def hapus_kucing(id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM nilai_alternatif WHERE id_kucing = ?', (id,))
    conn.execute('DELETE FROM ras_kucing WHERE id = ?', (id,))
    conn.commit()
    return redirect(url_for('admin'))

@app.route('/pengguna')
def pengguna():
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db()
    data = conn.execute('SELECT * FROM pengguna').fetchall()
    return render_template('pengguna.html', pengguna=data)

@app.route('/pengguna/tambah', methods=['POST'])
def tambah_pengguna():
    if not session.get('admin'):
        return redirect(url_for('login'))
    username = request.form['username']
    password = hash_password(request.form['password'])
    conn = get_db()
    conn.execute('INSERT INTO pengguna (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    return redirect(url_for('pengguna'))

@app.route('/pengguna/hapus/<username>')
def hapus_pengguna(username):
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM pengguna WHERE username = ?', (username,))
    conn.commit()
    return redirect(url_for('pengguna'))

@app.route('/ubah_password', methods=['GET', 'POST'])
def ubah_password():
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        old = hash_password(request.form['old_password'])
        new = hash_password(request.form['new_password'])
        user = conn.execute('SELECT * FROM pengguna WHERE username = ? AND password = ?', (session['username'], old)).fetchone()
        if user:
            conn.execute('UPDATE pengguna SET password = ? WHERE username = ?', (new, session['username']))
            conn.commit()
            return redirect(url_for('admin'))
        else:
            return render_template('ubah_password.html', error='Password lama salah')
    return render_template('ubah_password.html')

if __name__ == '__main__':
    app.run(debug=True)
