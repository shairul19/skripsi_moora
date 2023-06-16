from flask import Flask, render_template, request, redirect, session
import psycopg2
from psycopg2 import Error
import hashlib
import random
import string
import datetime

app = Flask(__name__)
app.secret_key = 'hdbkbe@!bdm0/wwd/ff/f'


# Fungsi untuk melakukan koneksi ke database PostgreSQL
def connect_db():
    try:
        conn = psycopg2.connect(
            user="shai",
            password="123",
            host="localhost",
            port="5432",
            database="db_seleksi"
        )
        return conn
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return None


# Fungsi untuk mengenkripsi password dengan SHA-256
def encrypt_password(password):
    sha_signature = hashlib.sha256(password.encode()).hexdigest()
    return sha_signature

# Fungsi untuk mendapatkan 4 digit akhir ID user
def get_last_4_digits(id_user):
    return id_user[-4:]

# Fungsi untuk memanggil password sementara
def generate_temp_password():
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(8))

# Halaman utama
@app.route('/')
def home():
    return render_template('index.html')

# Halaman registrasi
@app.route('/register2', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        nama_lengkap = request.form['nama_lengkap']
        tanggal_lahir = request.form['tanggal_lahir']
        posisi = request.form['posisi']
        role = 'user'  # Set role sebagai 'user' secara default

        # Generate ID User
        conn = connect_db()
        cur = conn.cursor()
        # Mendapatkan nilai terakhir yang digunakan
        cur.execute("SELECT last_sequence FROM tbl_user WHERE posisi = %s", (posisi,))
        last_sequence = cur.fetchone()

        if last_sequence is not None:
            sequence = last_sequence[0] + 1
        else:
            sequence = 1

        # Memperbarui nilai terakhir yang digunakan
        cur.execute("UPDATE tbl_user SET last_sequence = %s WHERE posisi = %s", (sequence, posisi))
        conn.commit()

        # Menggabungkan posisi dengan urutan daftar
        id_user = posisi + str(sequence).zfill(4)

        # Generate password dan lakukan enkripsi
        tanggal_lahir = datetime.datetime.strptime(tanggal_lahir, "%Y-%m-%d")  # Mengubah tanggal lahir menjadi objek datetime
        password = 'seleksi' + tanggal_lahir.strftime("%d%m")  # Mendapatkan tanggal dan bulan lahir dengan format ddmm
        encrypted_password = encrypt_password(password)
        
        if conn:
            try:
                cursor = conn.cursor()

                # Cek apakah username sudah digunakan
                cursor.execute("SELECT * FROM tbl_user WHERE username = %s", (username,))
                existing_user = cursor.fetchone()

                if existing_user:
                    return "Username sudah digunakan. Silakan gunakan username lain."

                # Tambahkan data pemain ke database
                cursor.execute("INSERT INTO tbl_user (id_user, username, nama_lengkap, tanggal_lahir, posisi, role, password, last_sequence) VALUES (%s,%s, %s, %s, %s, %s, %s, %s)",
                    (id_user, username, nama_lengkap, tanggal_lahir, posisi, role, encrypted_password, sequence)
                )

                conn.commit()
                cursor.close()

                return "Registrasi berhasil! Password sementara: " + password + "<br><br><a href='/'>Back to Index</a>"

            except (Exception, Error) as error:
                print("Error while inserting data", error)
                return "Terjadi kesalahan saat registrasi."

            finally:
                if conn:
                    conn.close()

    return render_template('register2.html')

# Halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()

                # Cek apakah username dan password cocok
                cursor.execute("SELECT * FROM tbl_user WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user:
                    encrypted_password = encrypt_password('seleksi' + user[3].strftime("%d%m"))  # Menggabungkan password dengan tanggal dan bulan lahir
                    if user[6] == encrypted_password:
                        session['id_user'] = user[0]
                        session['username'] = user[1]
                        session['role'] = user[6]
                        return redirect('/dashboard')
                    else:
                        return "Password yang dimasukkan salah."
                else:
                    return "Username tidak ditemukan."

            except (Exception, Error) as error:
                print("Error while querying data", error)
                return "Terjadi kesalahan saat login."

            finally:
                if conn:
                    conn.close()

    return render_template('login.html')


# Halaman dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return "Selamat datang, " + session['username'] + "!<br><br><a href='/logout'>Logout</a>"
    else:
        return redirect('/login')


# Halaman logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Halaman lihat peserta
@app.route('/lihat_peserta', methods=['GET', 'POST'])
def lihat_peserta():
    if request.method == 'POST':
        posisi = request.form['posisi']

        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()

                if posisi == 'all':
                    # Mendapatkan semua data peserta
                    cursor.execute("SELECT * FROM tbl_user")
                else:
                    # Mendapatkan data peserta berdasarkan posisi yang dipilih
                    cursor.execute("SELECT * FROM tbl_user WHERE posisi = %s", (posisi,))

                peserta = cursor.fetchall()

                return render_template('lihat_peserta.html', peserta=peserta)

            except (Exception, Error) as error:
                print("Error while querying data", error)
                return "Terjadi kesalahan saat mengambil data peserta."

            finally:
                if conn:
                    conn.close()

    return render_template('lihat_peserta.html')

if __name__ == '__main__':
    app.run(debug=True)