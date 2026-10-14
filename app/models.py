from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import math


# =========================================================
# USER MODEL (Class User)
# =========================================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    emergency_phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    ktp_file = db.Column(db.String(255), nullable=True)
    sim_file = db.Column(db.String(255), nullable=True)
    
    # Kolom baru untuk membedakan Admin dan User
    role = db.Column(db.String(20), nullable=False, default='user')

    # ---- Tambahan modul Kelola Pelanggan & Admin ----       <-- mulai tambahan
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    ktp_number = db.Column(db.String(20), nullable=True)
    sim_number = db.Column(db.String(20), nullable=True)
    # Kolom role menjadi penentu kelas: Customer / Admin / SuperAdmin
    __mapper_args__ = {'polymorphic_on': role}               

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# =========================================================
# KENDARAAN MODEL (Class Vehicle)
# =========================================================
class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo = db.Column(db.String(255), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    gallery = db.Column(db.Text, nullable=True)  
    vehicle_number = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )
    year = db.Column(db.Integer, nullable=False)
    vehicle_type = db.Column(
        db.String(20),
        nullable=False
    )
    seats = db.Column(db.Integer, nullable=False)
    luggage = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )
    price_per_day = db.Column(
        db.Integer,
        nullable=False
    )
    rental_type = db.Column(
        db.String(30),
        nullable=False
    )

    color = db.Column(db.String(30), nullable=True)
    chassis_number = db.Column(db.String(50), unique=True, nullable=True)
    engine_number = db.Column(db.String(50), unique=True, nullable=True)
    fuel = db.Column(db.String(20), nullable=True, default='Bensin')
    transmission = db.Column(db.String(20), nullable=True, default='Manual')
    engine_cc = db.Column(db.Integer, nullable=True)
    facilities = db.Column(db.Text, nullable=True)   
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Koordinat Live Tracking
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)

    @property
    def full_name(self):
        return f"{self.brand} {self.model}"

    @property
    def facility_list(self):
        if not self.facilities:
            return []
        return [f.strip() for f in self.facilities.split(',')]

    @property
    def photo_list(self):
        photos = [self.photo]
        if self.gallery:
            photos += [p.strip() for p in self.gallery.split(',')]
        return photos

    @property
    def review_count(self):
        return len(self.reviews)

    @property
    def avg_rating(self):
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    def rating_count(self, star):
        return sum(1 for r in self.reviews if r.rating == star)

    def rating_percent(self, star):
        if not self.reviews:
            return 0
        return round(self.rating_count(star) / len(self.reviews) * 100)

    @property
    def latest_reviews(self):
        return sorted(self.reviews, key=lambda r: r.created_at, reverse=True)[:2]
    
    @property
    def current_status(self):
        """Cek status kendaraan di tabel Rental"""
        active_rental = Rental.query.filter_by(vehicle_id=self.id, status=Rental.STATUS_BERJALAN).first()
        if active_rental:
            return "Disewa"
        return "Tersedia"


# =========================================================
# DRIVER MODEL (Sopir)
# =========================================================
class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    photo = db.Column(db.String(255), nullable=True, default='default_driver.png')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # ----- KOLOM BARU (dari desain "Tambah Data Sopir") -----
    address = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    sim_photo = db.Column(db.String(255), nullable=True)

    @property
    def code(self):
        """ID tampilan, contoh: SP001"""
        return f"SP{self.id:03d}"

    @property
    def current_rental(self):
        """Penyewaan aktif terbaru milik sopir ini, atau None kalau sedang tidak bertugas."""
        aktif = [Rental.STATUS_MENUNGGU_KONFIRMASI, Rental.STATUS_PENGAMBILAN,
                 Rental.STATUS_DIPAKAI, Rental.STATUS_PENGEMBALIAN]
        return (Rental.query
                .filter(Rental.driver_id == self.id, Rental.status.in_(aktif))
                .order_by(Rental.start_date.desc())
                .first())

    @property
    def status_label(self):
        """Tersedia / Menunggu Konfirmasi / Berjalan (dihitung dari data Rental)."""
        r = self.current_rental
        if r is None:
            return 'Tersedia'
        if r.status == Rental.STATUS_MENUNGGU_KONFIRMASI:
            return 'Menunggu Konfirmasi'
        return 'Berjalan'

    @property
    def total_orders(self):
        """Jumlah pesanan (tidak batal) dalam setahun terakhir."""
        batas = datetime.now() - timedelta(days=365)
        return (Rental.query
                .filter(Rental.driver_id == self.id,
                        Rental.status != Rental.STATUS_BATAL,
                        Rental.created_at >= batas)
                .count())

    @property
    def avg_rating(self):
        """Rata-rata ulasan (skala 1-5) dari pelanggan yang sudah selesai menyewa bersama sopir ini."""
        pasangan = {(r.user_id, r.vehicle_id) for r in self.rentals
                    if r.status == Rental.STATUS_SELESAI}
        nilai = [rv.rating for (u, v) in pasangan
                 for rv in Review.query.filter_by(user_id=u, vehicle_id=v)]
        return round(sum(nilai) / len(nilai), 2) if nilai else 0

    @property
    def rating_label(self):
        n = self.avg_rating
        if n >= 4.5:
            return 'Sangat Baik'
        if n >= 3.5:
            return 'Baik'
        return 'Cukup' if n > 0 else 'Belum ada penilaian'


# =========================================================
# RENTAL MODEL (Data Penyewaan)
# =========================================================
class Rental(db.Model):
    # Alur Status Penyewaan Baru
    STATUS_MENUNGGU_BAYAR = 'Menunggu Pembayaran'
    STATUS_MENUNGGU_KONFIRMASI = 'Menunggu Konfirmasi'
    STATUS_PENGAMBILAN = 'Kendaraan Dalam Pengambilan'
    STATUS_DIPAKAI = 'Kendaraan Sedang Dipakai'
    STATUS_PENGEMBALIAN = 'Dalam Proses Pengembalian'
    STATUS_SELESAI = 'Selesai'
    STATUS_BATAL = 'Batal'
    ALL_STATUS = [
        STATUS_MENUNGGU_BAYAR, STATUS_MENUNGGU_KONFIRMASI, 
        STATUS_PENGAMBILAN, STATUS_DIPAKAI, 
        STATUS_PENGEMBALIAN, STATUS_SELESAI, STATUS_BATAL
    ]

    # Kompatibilitas dengan kode lama (fallback untuk property dashboard lama)
    STATUS_MENUNGGU = STATUS_MENUNGGU_KONFIRMASI
    STATUS_BERJALAN = STATUS_DIPAKAI

    DRIVER_FEE = 150000                       
    ACCESSORIES = {                           
        'kursi_bayi':   ('Kursi Bayi (Baby Car Seat)', 15000),
        'phone_holder': ('Phone holder', 5000),
        'bantal':       ('Bantal', 5000),
        'selimut':      ('Selimut', 10000),
    }
    INSURANCES = {                          
        'dasar':   ('Dasar', 0),
        'lengkap': ('Lengkap', 50000),
    }

    id = db.Column(db.Integer, primary_key=True)
    booking_code = db.Column(db.String(20), unique=True, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True) # Tambahan Relasi Sopir

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    # Jam pengambilan & pengembalian (format "HH:MM"), dipisah dari tanggal
    # supaya perhitungan durasi & cek bentrok berbasis tanggal tetap aman.
    pickup_time = db.Column(db.String(5), nullable=False, default='10:00')
    return_time = db.Column(db.String(5), nullable=False, default='10:00')
    status = db.Column(db.String(50), nullable=False, default=STATUS_MENUNGGU_BAYAR)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # Tambahan Data Pembayaran
    payment_method = db.Column(db.String(50), nullable=True)
    payment_status = db.Column(db.String(20), nullable=False, default='Belum Lunas') # 'Lunas' / 'Belum Lunas'

    with_driver = db.Column(db.Boolean, nullable=False, default=False)
    accessories = db.Column(db.String(200), nullable=True, default='')  
    insurance = db.Column(db.String(20), nullable=False, default='dasar')
    purpose = db.Column(db.String(50), nullable=True)
    region = db.Column(db.String(30), nullable=True)
    destination_city = db.Column(db.String(100), nullable=True)
    pickup_location = db.Column(db.String(100), nullable=True)
    return_location = db.Column(db.String(100), nullable=True)
    special_request = db.Column(db.Text, nullable=True)
    ktp_file = db.Column(db.String(255), nullable=True)
    sim_file = db.Column(db.String(255), nullable=True)

    # ---- Denda keterlambatan ----
    # Selama kendaraan masih dipakai, denda dihitung LIVE (berjalan).
    # Saat kendaraan dikembalikan, nilainya DIKUNCI ke kolom di bawah ini
    # supaya tidak terus bertambah setelah mobil masuk garasi.
    fine_days = db.Column(db.Integer, nullable=False, default=0)
    fine_amount = db.Column(db.Integer, nullable=False, default=0)
    fine_paid = db.Column(db.Boolean, nullable=False, default=False)

    # Relasi antar objek (OOP)
    user = db.relationship('User', backref=db.backref('rentals', lazy=True))
    vehicle = db.relationship('Vehicle', backref=db.backref('rentals', lazy=True))
    driver = db.relationship('Driver', backref=db.backref('rentals', lazy=True))

    # ---- Aturan bisnis pengingat & denda ----
    REMINDER_DAYS = 3                 # pengingat mulai H-3 sebelum batas kembali
    FINE_ADMIN_FEE = 50000            # denda administrasi per hari keterlambatan
    TRACKING_START = (-0.502106, 117.153709)   # titik awal tracking (Samarinda)

    @property
    def duration_days(self):
        return max(1, (self.end_date - self.start_date).days)

    @property
    def accessory_keys(self):
        return [k for k in (self.accessories or '').split(',') if k in self.ACCESSORIES]

    @property
    def vehicle_cost(self):
        return self.duration_days * self.vehicle.price_per_day

    @property
    def driver_cost(self):
        return self.duration_days * self.DRIVER_FEE if self.with_driver else 0

    @property
    def accessories_cost(self):
        return sum(self.ACCESSORIES[k][1] for k in self.accessory_keys)

    @property
    def insurance_cost(self):
        price = self.INSURANCES.get(self.insurance or 'dasar', ('', 0))[1]
        return price * self.duration_days

    @property
    def total_price(self):
        # Perbaikan kalkulasi total harga sesuai desain yang lengkap
        return self.vehicle_cost + self.driver_cost + self.accessories_cost + self.insurance_cost

    # ---------------------------------------------------------
    # BATAS WAKTU PENGEMBALIAN
    # ---------------------------------------------------------
    @property
    def return_deadline(self):
        """Tanggal + jam pengembalian digabung menjadi satu datetime."""
        try:
            jam = datetime.strptime(self.return_time or '10:00', '%H:%M').time()
        except ValueError:
            jam = datetime.strptime('10:00', '%H:%M').time()
        return datetime.combine(self.end_date, jam)

    @property
    def is_in_use(self):
        return self.status == self.STATUS_DIPAKAI

    @property
    def time_remaining(self):
        """Sisa waktu menuju batas kembali (negatif = sudah lewat)."""
        return self.return_deadline - datetime.now()

    @property
    def is_overdue(self):
        """Terlambat = kendaraan masih dipakai tetapi batas waktu sudah lewat."""
        return self.is_in_use and self.time_remaining.total_seconds() < 0

    @property
    def is_due_soon(self):
        """Masuk jendela pengingat H-3 (dan belum terlambat)."""
        sisa = self.time_remaining.total_seconds()
        return self.is_in_use and 0 <= sisa <= self.REMINDER_DAYS * 86400

    @property
    def remaining_label(self):
        """Teks sisa waktu yang mudah dibaca, contoh: '2 hari 5 jam'."""
        sisa = max(0, int(self.time_remaining.total_seconds()))
        hari, sisa = divmod(sisa, 86400)
        jam = sisa // 3600
        if hari and jam:
            return f'{hari} hari {jam} jam'
        if hari:
            return f'{hari} hari'
        return f'{jam} jam' if jam else 'kurang dari 1 jam'

    # ---------------------------------------------------------
    # DENDA KETERLAMBATAN
    # ---------------------------------------------------------
    @property
    def fine_per_day(self):
        """Denda per hari = tarif sewa harian kendaraan + biaya administrasi."""
        return self.vehicle.price_per_day + self.FINE_ADMIN_FEE

    def _late_days_at(self, moment):
        """Jumlah hari terlambat pada waktu tertentu (telat 1 jam = 1 hari)."""
        telat = (moment - self.return_deadline).total_seconds()
        return math.ceil(telat / 86400) if telat > 0 else 0

    @property
    def late_days(self):
        """Hari terlambat: live saat masih dipakai, nilai terkunci setelah kembali."""
        if self.is_in_use:
            return self._late_days_at(datetime.now())
        return self.fine_days or 0

    @property
    def active_fine(self):
        """Denda yang berlaku saat ini (live atau terkunci)."""
        if self.is_in_use:
            return self.late_days * self.fine_per_day
        return self.fine_amount or 0

    @property
    def has_fine(self):
        return self.active_fine > 0

    @property
    def final_total_price(self):
        """Total tagihan = biaya sewa + denda keterlambatan."""
        return self.total_price + self.active_fine

    def lock_fine(self):
        """Bekukan denda saat kendaraan dikembalikan."""
        self.fine_days = self._late_days_at(datetime.now())
        self.fine_amount = self.fine_days * self.fine_per_day
        if self.fine_amount == 0:
            self.fine_paid = False

    # ---------------------------------------------------------
    # TRANSISI STATUS (satu pintu untuk semua halaman admin)
    # ---------------------------------------------------------
    def change_status(self, new_status):
        """
        Ubah status penyewaan beserta efek sampingnya:
          - Pengambilan            -> pembayaran dianggap lunas
          - Sedang Dipakai         -> tracking GPS menyala, denda kembali live
          - Pengembalian / Selesai -> tracking mati, denda dikunci
          - Batal                  -> tracking mati, denda dihapus
        Mengembalikan status lama (None jika tidak ada perubahan).
        """
        if new_status not in self.ALL_STATUS or new_status == self.status:
            return None

        old_status = self.status

        if new_status == self.STATUS_PENGAMBILAN:
            self.payment_status = 'Lunas'

        if new_status == self.STATUS_DIPAKAI:
            self.vehicle.current_lat, self.vehicle.current_lng = self.TRACKING_START
            self.fine_days, self.fine_amount, self.fine_paid = 0, 0, False
        elif old_status == self.STATUS_DIPAKAI:
            # Kendaraan keluar dari status dipakai: matikan tracking.
            # (Hanya di sini, supaya perubahan status pesanan LAIN untuk mobil
            #  yang sama tidak ikut mematikan tracking yang sedang berjalan.)
            self.vehicle.current_lat = None
            self.vehicle.current_lng = None
            if new_status == self.STATUS_BATAL:
                self.fine_days, self.fine_amount, self.fine_paid = 0, 0, False
            else:
                self.lock_fine()

        self.status = new_status
        return old_status


# =========================================================
# REVIEW MODEL (Ulasan Pengguna)
# =========================================================
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)   # 1 sampai 5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    vehicle = db.relationship('Vehicle', backref=db.backref('reviews', lazy=True))


# =========================================================
# NOTIFICATION MODEL (Notifikasi Pengguna)
# =========================================================
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    rental_id = db.Column(
        db.Integer,
        db.ForeignKey('rental.id'),
        nullable=False
    )

    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)

    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    # Jenis notifikasi (dipakai untuk ikon/warna & mencegah notifikasi ganda)
    CATEGORY_STATUS = 'status'        # perubahan status oleh admin
    CATEGORY_REMINDER = 'reminder'    # pengingat H-3 pengembalian
    CATEGORY_OVERDUE = 'overdue'      # peringatan terlambat + denda berjalan
    CATEGORY_FINE = 'fine'            # denda final saat kendaraan dikembalikan
    category = db.Column(db.String(20), nullable=False, default=CATEGORY_STATUS)

    user = db.relationship(
        'User',
        backref=db.backref('notifications', lazy=True)
    )

    rental = db.relationship(
        'Rental',
        backref=db.backref('notifications', lazy=True)
    )

    # ---- Tampilan per kategori (ikon Font Awesome + kelas warna) ----
    _STYLE = {
        CATEGORY_STATUS:   ('fa-solid fa-bell', 'tone-info'),
        CATEGORY_REMINDER: ('fa-solid fa-clock', 'tone-warning'),
        CATEGORY_OVERDUE:  ('fa-solid fa-triangle-exclamation', 'tone-danger'),
        CATEGORY_FINE:     ('fa-solid fa-file-invoice-dollar', 'tone-danger'),
    }

    @property
    def icon(self):
        return self._STYLE.get(self.category, self._STYLE[self.CATEGORY_STATUS])[0]

    @property
    def tone(self):
        return self._STYLE.get(self.category, self._STYLE[self.CATEGORY_STATUS])[1]

    # ---- Factory method: satu tempat untuk membuat setiap jenis notifikasi ----
    @staticmethod
    def _rp(n):
        return 'Rp{:,.0f}'.format(n).replace(',', '.')

    @classmethod
    def status_changed(cls, rental, old_status):
        return cls(
            user_id=rental.user_id, rental_id=rental.id,
            category=cls.CATEGORY_STATUS,
            title='Status Pesanan Diperbarui',
            message=(f'Status pesanan {rental.booking_code} berubah dari '
                     f'"{old_status}" menjadi "{rental.status}".'),
            old_status=old_status, new_status=rental.status,
        )

    @classmethod
    def return_reminder(cls, rental):
        batas = rental.return_deadline.strftime('%d-%m-%Y pukul %H:%M')
        return cls(
            user_id=rental.user_id, rental_id=rental.id,
            category=cls.CATEGORY_REMINDER,
            title='Pengingat Pengembalian Kendaraan',
            message=(f'Masa sewa {rental.vehicle.full_name} '
                     f'({rental.vehicle.vehicle_number}) untuk pesanan '
                     f'{rental.booking_code} tersisa {rental.remaining_label}. '
                     f'Batas pengembalian: {batas}. Keterlambatan dikenakan denda '
                     f'{cls._rp(rental.fine_per_day)} per hari.'),
            old_status=rental.status, new_status=rental.status,
        )

    @classmethod
    def overdue_warning(cls, rental):
        batas = rental.return_deadline.strftime('%d-%m-%Y pukul %H:%M')
        return cls(
            user_id=rental.user_id, rental_id=rental.id,
            category=cls.CATEGORY_OVERDUE,
            title='Peringatan: Pengembalian Terlambat',
            message=(f'Pesanan {rental.booking_code} melewati batas pengembalian '
                     f'({batas}). Anda terlambat {rental.late_days} hari dengan '
                     f'denda berjalan {cls._rp(rental.active_fine)}. Segera '
                     f'kembalikan kendaraan agar denda tidak bertambah.'),
            old_status=rental.status, new_status=rental.status,
        )

    @classmethod
    def fine_issued(cls, rental):
        return cls(
            user_id=rental.user_id, rental_id=rental.id,
            category=cls.CATEGORY_FINE,
            title='Tagihan Denda Keterlambatan',
            message=(f'Kendaraan pesanan {rental.booking_code} dikembalikan '
                     f'terlambat {rental.fine_days} hari. Total denda: '
                     f'{cls._rp(rental.fine_amount)}. Silakan selesaikan '
                     f'pembayaran denda kepada admin.'),
            old_status=rental.status, new_status=rental.status,
        )



# =========================================================
# MODEL TURUNAN USER  (Kelola Pelanggan & Kelola Admin)
#
#   User (induk)
#    |-- Customer          role = 'user'
#    |-- Admin             role = 'admin'
#         |-- SuperAdmin   role = 'superadmin'
#
# Tidak ada tabel baru: semuanya tetap di tabel `user`,
# kolom `role` yang menentukan kelas objeknya.
# =========================================================
class ProfileMixin:
    """Perilaku bersama untuk semua jenis pengguna (foto profil & dokumen)."""

    @property
    def avatar_path(self):
        """Path foto profil relatif terhadap folder static, atau None."""
        if self.profile_photo:
            return f"uploads/profil/{self.profile_photo}"
        return None

    def _document(self, label, attr):
        """
        Cari dokumen (KTP/SIM). Urutan pencarian:
        1) file di akun user (halaman Kelola Akun), 2) file dari penyewaan terbaru.
        """
        own = getattr(self, attr)
        if own:
            path = f"uploads/dokumen_akun/{own}"
            filename = own
        else:
            column = getattr(Rental, attr)
            rental = (Rental.query
                      .filter(Rental.user_id == self.id, column.isnot(None), column != '')
                      .order_by(Rental.created_at.desc())
                      .first())
            if rental is None:
                return {'label': label, 'path': None, 'is_pdf': False}
            filename = getattr(rental, attr)
            path = f"uploads/dokumen/{filename}"
        return {'label': label, 'path': path, 'is_pdf': filename.lower().endswith('.pdf')}

    @property
    def documents(self):
        return [self._document('KTP', 'ktp_file'), self._document('SIM', 'sim_file')]


class Customer(ProfileMixin, User):
    """Pelanggan / penyewa kendaraan."""
    ROLE = 'user'
    CODE_PREFIX = 'PLG'
    __mapper_args__ = {'polymorphic_identity': ROLE}

    @property
    def code(self):
        return f"{self.CODE_PREFIX}{self.id:03d}"      # contoh: PLG001

    @property
    def rental_history(self):
        return (Rental.query
                .filter_by(user_id=self.id)
                .order_by(Rental.created_at.desc())
                .all())


class Admin(ProfileMixin, User):
    """Admin biasa."""
    ROLE = 'admin'
    CODE_PREFIX = 'ADM'
    is_super_admin = False
    __mapper_args__ = {'polymorphic_identity': ROLE}

    @property
    def code(self):
        return f"{self.CODE_PREFIX}{self.id:03d}"      # contoh: ADM002


class SuperAdmin(Admin):
    """Super Admin = Admin + hak mengelola akun admin lain."""
    ROLE = 'superadmin'
    CODE_PREFIX = 'SA'
    is_super_admin = True
    __mapper_args__ = {'polymorphic_identity': ROLE}
