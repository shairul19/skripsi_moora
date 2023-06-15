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
        current_year = datetime.datetime.now().year
        cur.execute("SELECT COUNT(*) FROM tbl_user")
        count = cur.fetchone()[0] + 1
        id_user = str(current_year) + str(count).zfill(4)

        # Generate password dan lakukan enkripsi
        password = 'seleksi#' + id_user[-4:]
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
                cursor.execute("INSERT INTO tbl_user (id_user, username, nama_lengkap, tanggal_lahir, posisi, role, password) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (id_user, username, nama_lengkap, tanggal_lahir, posisi, role, encrypted_password)
                )

                conn.commit()
                cursor.close()

                return "Registrasi berhasil! Password sementara: " + password

            except (Exception, Error) as error:
                print("Error while inserting data", error)
                return "Terjadi kesalahan saat registrasi."

            finally:
                if conn:
                    conn.close()

    return render_template('register2.html')

if __name__ == '__main__':
    app.run(debug=True)