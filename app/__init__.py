
# ═════════════════════════════════════════════════════════════
#     INISIALISASI DAN KONFIGURASI APLIKASI WEBSITE KeSanaSini (__init__.py)
#
#     ⤷ Membuat dan mengonfigurasi aplikasi Flask menggunakan pola Application Factory
#       melalui fungsi create_app() agar aplikasi dapat diinisialisasi secara terstruktur.
#     ⤷ Mengatur konfigurasi utama aplikasi, seperti koneksi database SQLite,
#       SECRET_KEY, serta kredensial Google OAuth melalui environment variable.
#     ⤷ Menginisialisasi SQLAlchemy dan OAuth sebagai komponen utama aplikasi
#       untuk mengelola database serta mendukung autentikasi menggunakan akun Google.
#     ⤷ Mengimpor dan mendaftarkan blueprint dari routes.py untuk menghubungkan
#       endpoint pengguna, admin, dan superadmin ke dalam aplikasi Flask.
#     ⤷ Membuat tabel database yang belum tersedia serta menjalankan migrasi skema
#       sederhana untuk menambahkan kolom yang belum ada tanpa menghapus data lama.
#     ⤷ Menjadi pusat inisialisasi aplikasi yang menghubungkan konfigurasi,
#       autentikasi, routing, dan database sebelum aplikasi dijalankan oleh server.
# ═════════════════════════════════════════════════════════════




# ═════════════════════════════════════════════════════════════
#   A.   |   IMPORT
# ═════════════════════════════════════════════════════════════

# Mengimpor Flask untuk membuat dan mengatur aplikasi web.
from flask import Flask

# Mengimpor SQLAlchemy untuk menghubungkan aplikasi Flask dengan database dan melakukan operasi CRUD.
from flask_sqlalchemy import SQLAlchemy

# Mengimpor OAuth untuk mengintegrasikan login menggunakan layanan pihak ketiga, seperti Google.
from authlib.integrations.flask_client import OAuth

# Mengimpor fungsi untuk membaca variabel konfigurasi dari file .env.
from dotenv import load_dotenv

# Mengimpor modul os untuk mengakses environment variables dan fungsi sistem operasi.
import os

# Membaca variabel konfigurasi dari file .env agar dapat diakses menggunakan os.getenv().
load_dotenv()



# ═════════════════════════════════════════════════════════════
#   B.   |   INISIALISASI OBJEK GLOBAL
# ═════════════════════════════════════════════════════════════

# Membuat objek SQLAlchemy yang akan digunakan untuk mengelola database aplikasi.
db = SQLAlchemy()

# Membuat objek OAuth untuk menangani autentikasi menggunakan layanan eksternal.
oauth = OAuth()



# ═════════════════════════════════════════════════════════════
#   C.   |   FUNGSI FACTORY UNTUK MEMBUAT APLIKASI FLASK
# ═════════════════════════════════════════════════════════════

# Membuat dan mengonfigurasi instance aplikasi Flask.
def create_app():

    # Membuat objek aplikasi Flask.
    # __name__ membantu Flask menentukan lokasi sumber daya aplikasi, seperti template dan folder static.
    app = Flask(__name__)


    
    # ═════════════════════════════════════════════════════════════
    #   C.1.   |   KONFIGURASI APLIKASI DAN DATABASE
    # ═════════════════════════════════════════════════════════════

    # Mengatur koneksi database menggunakan SQLite.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rentals.db'

    # Menonaktifkan pelacakan perubahan objek SQLAlchemy yang tidak diperlukan oleh aplikasi ini.
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mengambil SECRET_KEY dari environment variable.
    # Jika tidak tersedia, aplikasi menggunakan nilai default.
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-only-change-this-secret')

    # Mengambil Client ID untuk autentikasi Google OAuth.
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')

    # Mengambil Client Secret untuk autentikasi Google OAuth.
    app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')


    # ═════════════════════════════════════════════════════════════
    #   C.2.   |   MENGHUBUNGKAN DATABASE DAN OAUTH KE APLIKASI
    # ═════════════════════════════════════════════════════════════

    # Menghubungkan objek SQLAlchemy ke aplikasi Flask yang baru dibuat agar model dapat mengakses database.
    db.init_app(app)

    # Menghubungkan objek OAuth ke aplikasi Flask.
    oauth.init_app(app)


    # ═════════════════════════════════════════════════════════════
    #   C.3.   |   REGISTRASI GOOGLE OAUTH
    # ═════════════════════════════════════════════════════════════
    oauth.register(
        name='google',                                                              # Memberikan nama "google" pada konfigurasi OAuth ini.
        client_id=app.config.get('GOOGLE_CLIENT_ID'),                               # Mengambil Client ID Google dari konfigurasi aplikasi.
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),                       # Mengambil Client Secret Google dari konfigurasi.
        server_metadata_url=(
            'https://accounts.google.com/.well-known/openid-configuration'),        # Mengambil metadata OpenID Connect milik Google, termasuk endpoint autentikasi dan token.
        client_kwargs={
            'scope': 'openid email profile'}                                        # Meminta izin identitas dasar, alamat email, dan informasi profil pengguna dari Google.
    )


    # ═════════════════════════════════════════════════════════════
    #   C.4.   |   IMPORT ROUTES DAN MODELS
    # ═════════════════════════════════════════════════════════════

    # Import dilakukan di dalam create_app() untuk membantu menghindari circular import.
    from . import routes        # Mengimpor definisi route atau endpoint aplikasi.
    from . import models        # Mengimpor model database, seperti User, Vehicle, Driver, Rental, Review, dan model lainnya.


    # ═════════════════════════════════════════════════════════════
    #   C.5.   |   REGISTRASI BLUEPRINT
    # ═════════════════════════════════════════════════════════════
    app.register_blueprint(routes.bp)              # Mendaftarkan blueprint utama untuk fitur pengguna.
    app.register_blueprint(routes.admin_bp)        # Mendaftarkan blueprint untuk fitur pengelolaan oleh admin.
    app.register_blueprint(routes.superadmin_bp)   # Mendaftarkan blueprint untuk fitur superadmin.

    # [OOP - ENKAPSULASI]: Foto profil akun yang sedang login (user, admin, super admin)
    # disediakan ke semua template sebagai `nav_avatar_url`; `avatar_url(user)` untuk akun lain.
    class AvatarResolver:
        FOLDER = 'uploads/profil'
        FOLDERS = ('uploads/profil', 'uploads/foto_profil')   # folder lama sebagai cadangan

        @classmethod
        def url_for_user(cls, user):
            from flask import url_for
            filename = getattr(user, 'profile_photo', None) if user else None
            if not filename:
                return None
            for folder in cls.FOLDERS:
                path = os.path.join(app.root_path, 'static', folder, filename)
                if os.path.exists(path):
                    return url_for('static', filename=f'{folder}/{filename}', v=int(os.path.getmtime(path)))
            return None
        
        @classmethod
        def current(cls):
            from flask import session
            user_id = session.get('user_id')
            return cls.url_for_user(db.session.get(models.User, user_id)) if user_id else None

    @app.context_processor
    def inject_avatar():
        return {'nav_avatar_url': AvatarResolver.current(),
                'avatar_url': AvatarResolver.url_for_user}


    # ═════════════════════════════════════════════════════════════
    #   C.6.   |   PEMBUATAN TABEL DAN MIGRASI DATABASE
    # ═════════════════════════════════════════════════════════════

    # Mengaktifkan konteks aplikasi agar operasi database dapat dijalankan menggunakan konfigurasi Flask.
    with app.app_context():

        # Membuat tabel yang belum tersedia berdasarkan model.
        # Tidak menghapus tabel atau data yang sudah ada.
        db.create_all()

        
        # ═════════════════════════════════════════════════════════════
        #   C.6.1.   |   SISTEM AUTO-HEAL: MIGRASI SKEMA NON-DESTRUKTIF
        # ═════════════════════════════════════════════════════════════

        # Mengimpor inspect untuk memeriksa struktur database dan text untuk menjalankan perintah SQL secara eksplisit.
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)                  # Membuat objek pemeriksa struktur database.
        existing_tables = inspector.get_table_names()   # Mengambil daftar nama tabel yang sudah ada di database.

        # Menentukan tabel, nama kolom, dan tipe data yang perlu ditambahkan apabila kolom tersebut belum tersedia.
        migrations = {
            'rental': [
                ('cancellation_reason', 'VARCHAR(500)'),
                ('fine_days', 'INTEGER NOT NULL DEFAULT 0'),
                ('fine_amount', 'INTEGER NOT NULL DEFAULT 0'),
                ('fine_paid', 'BOOLEAN NOT NULL DEFAULT 0'),
                ('pickup_time', "VARCHAR(5) NOT NULL DEFAULT '10:00'"),
                ('return_time', "VARCHAR(5) NOT NULL DEFAULT '10:00'"),
            ],
            'user': [
                ('is_active', 'BOOLEAN NOT NULL DEFAULT 1'),
                ('profile_photo', 'VARCHAR(255)'),
                ('ktp_number', 'VARCHAR(20)'),
                ('sim_number', 'VARCHAR(20)'),
                ('total_transaction', 'BIGINT NOT NULL DEFAULT 0'),
            ],
            'vehicle': [
                ('current_lat', 'FLOAT'),
                ('current_lng', 'FLOAT'),
                ('is_active', 'BOOLEAN NOT NULL DEFAULT 1'),
            ],
            'driver': [
                ('address', 'VARCHAR(255)'),
                ('description', 'TEXT'),
                ('sim_photo', 'VARCHAR(255)'),
            ],
        }

        # Memeriksa setiap tabel yang tercantum dalam konfigurasi migrasi dan melewati tabel yang belum tersedia.
        for table_name, columns in migrations.items():
            if table_name in existing_tables:

                # Mengambil nama semua kolom yang sudah ada pada tabel yang sedang diperiksa.
                existing_cols = {
                    c['name'] for c in inspector.get_columns(table_name)}

                # Memeriksa satu per satu kolom yang dibutuhkan.
                for col_name, col_def in columns:

                    # Jika kolom belum ada, tambahkan kolom baru tanpa menghapus tabel atau data lama.
                    if col_name not in existing_cols:
                        db.session.execute(
                            text(f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}')
                        )

                        # Menampilkan informasi kolom yang berhasil ditambahkan ke terminal.
                        print(f"[AUTO-MIGRATE] Kolom '{col_name}' berhasil ditambahkan ke tabel '{table_name}'.")
        
        # Menyimpan perubahan migrasi ke database.
        db.session.commit()

        # Isi ulang total transaksi semua pelanggan dari data pesanan yang sudah ada.
        try:
            models.TransactionTotalService.recalculate_all()
        except Exception as error:
            db.session.rollback()
            print(f"[TOTAL TRANSAKSI] Gagal menghitung ulang: {error}")

    # Mengembalikan objek aplikasi Flask yang sudah selesai dikonfigurasi agar dapat dijalankan oleh server.
    return app