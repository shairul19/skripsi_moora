from flask import Flask, render_template, request, redirect, session
import psycopg2
from psycopg2 import Error
import hashlib
import random
import string

app = Flask(__name__)
app.secret_key = 'secretkey'  # Ganti dengan kunci rahasia yang lebih aman


# Fungsi untuk mengenkripsi password dengan SHA-256
def encrypt_password(password):
    sha_signature = hashlib.sha256(password.encode()).hexdigest()
    return sha_signature


# Fungsi untuk mendapatkan 4 digit akhir ID pemain
def get_last_4_digits(nisn):
    return nisn[-4:]


# Fungsi untuk membangkitkan password sementara
def generate_temp_password():
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(8))


# Fungsi untuk melakukan koneksi ke database PostgreSQL
def connect_db():
    try:
        connection = psycopg2.connect(
            user="shai",
            password="123",
            host="localhost",
            port="5432",
            database="db_seleksi"
        )
        return connection
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return None


# Halaman utama
@app.route('/')
def home():
    return render_template('index.html')


# Halaman registrasi
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nisn = request.form['nisn']
        username = request.form['username']
        nama_pemain = request.form['nama_pemain']
        tgl_lahir_pemain = request.form['tgl_lahir_pemain']
        posisi_pemain = request.form['posisi_pemain']
        role = 'pemain'  # Set role sebagai 'pemain' secara default

        last_4_digits = get_last_4_digits(nisn)
        password = f"seleksi{last_4_digits}"  # Password sementara berdasarkan 4 digit akhir ID pemain

        encrypted_password = encrypt_password(password)

        connection = connect_db()
        if connection:
            try:
                cursor = connection.cursor()

                # Cek apakah username sudah digunakan
                cursor.execute("SELECT * FROM tbl_pemain WHERE username = %s", (username,))
                existing_user = cursor.fetchone()

                if existing_user:
                    return "Username sudah digunakan. Silakan gunakan username lain."

                # Tambahkan data pemain ke database
                cursor.execute(
                    "INSERT INTO tbl_pemain (id_pemain, nisn, username, nama_pemain, tgl_lahir_pemain, posisi_pemain, role, password) VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s)",
                    (nisn, username, nama_pemain, tgl_lahir_pemain, posisi_pemain, role, encrypted_password)
                )

                connection.commit()
                cursor.close()

                return "Registrasi berhasil! Password sementara: " + password

            except (Exception, Error) as error:
                print("Error while inserting data", error)
                return "Terjadi kesalahan saat registrasi."

            finally:
                if connection:
                    connection.close()

    return render_template('register.html')


# Halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = connect_db()
        if connection:
            try:
                cursor = connection.cursor()

                # Cek apakah username dan password valid
                cursor.execute("SELECT * FROM tbl_pemain WHERE username = %s", (username,))
                user = cursor.fetchone()

                if user:
                    stored_password = user[7]  # Ambil password yang tersimpan di database
                    entered_password = encrypt_password(password)

                    if entered_password == stored_password:
                        session['username'] = username
                        session['role'] = user[6]  # Ambil role pemain dari database
                        return redirect('/dashboard')

                return "Username atau password salah."

            except (Exception, Error) as error:
                print("Error while logging in", error)
                return "Terjadi kesalahan saat login."

            finally:
                if connection:
                    connection.close()

    return render_template('login.html')


# Halaman dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        role = session['role']
        if role == 'admin':
            return "Selamat datang, admin!"
        elif role == 'pemain':
            return "Selamat datang, pemain!"
    else:
        return redirect('/login')


# Fungsi untuk logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect('/login')


if __name__ == '__main__':
    app.run()
