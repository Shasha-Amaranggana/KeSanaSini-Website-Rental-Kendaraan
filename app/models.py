from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import math


# =========================================================
# USER MODEL (Class User)
# ---------------------------------------------------------
# [OOP - PEWARISAN / INHERITANCE]:
#   Kelas User mewarisi 'db.Model' dari SQLAlchemy ORM untuk
#   mendapatkan kemampuan pemetaan basis data relasional.
# [OOP - POLIMORFISME / POLYMORPHISM]:
#   '__mapper_args__ = {"polymorphic_on": role}' mengaktifkan Single-Table
#   Inheritance sehingga class turunan (Customer, Admin, SuperAdmin)
#   dapat diinstansiasi secara polimorfik sesuai nilai kolom 'role'.
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
    # [OOP - POLIMORFISME]: Kolom role menjadi diskriminator penentu kelas polimorfik
    __mapper_args__ = {'polymorphic_on': role}               

    # [OOP - ENKAPSULASI / ENCAPSULATION]:
    # Mengenkapsulasi hashing & verifikasi password sehingga keamanan terpusat di objek.
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# =========================================================
# KENDARAAN MODEL (Class Vehicle)
# ---------------------------------------------------------
# [OOP - PEWARISAN / INHERITANCE]:
#   Mewarisi 'db.Model' dari SQLAlchemy untuk pemetaan tabel kendaraan.
# [OOP - ENKAPSULASI / ENCAPSULATION]:
#   Membungkus atribut data kendaraan dan menyembunyikan komputasi internal
#   melalui @property (contoh: full_name, facility_list, avg_rating,
#   serta kalkulasi status ketersediaan sewa di current_status).
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
# ---------------------------------------------------------
# [OOP - PEWARISAN / INHERITANCE]:
#   Mewarisi 'db.Model' dari SQLAlchemy untuk tabel sopir/driver.
# [OOP - ENKAPSULASI / ENCAPSULATION]:
#   Membungkus data dan komputasi dinamis sopir melalui getter (@property)
#   seperti format kode (code -> SP001), status tugas live (status_label),
#   perhitungan jumlah order, dan agregasi rating performa sopir.
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
# ---------------------------------------------------------
# [OOP - PEWARISAN / INHERITANCE]:
#   Mewarisi 'db.Model' dari SQLAlchemy untuk tabel transaksi penyewaan.
# [OOP - ASOSIASI & RELASI OBJEK / OBJECT RELATIONSHIPS]:
#   Menghubungkan entitas Rental dengan objek User, Vehicle, dan Driver
#   melalui db.relationship, memungkinkan navigasi antar-objek secara langsung.
# [OOP - ENKAPSULASI / ENCAPSULATION]:
#   1. Mengenkapsulasi kalkulasi biaya total (durasi, unit, sopir, aksesoris, asuransi).
#   2. Mengenkapsulasi logika batas waktu, pengingat H-3, dan denda keterlambatan.
#   3. State Machine (change_status) mengenkapsulasi transisi status dan efek sampingnya
#      (koordinat live GPS tracking, penguncian denda, status pembayaran).
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
        'kursi_bayi':    ('Kursi Bayi (Baby Car Seat)', 15000),
        'phone_holder':  ('Phone holder', 5000),
        'bantal':        ('Bantal', 5000),
        'selimut':       ('Selimut', 10000),
        'helm_tambahan': ('Helm tambahan', 10000),
        'jas_hujan':     ('Jas hujan', 5000),
        'box_belakang':  ('Box belakang', 15000),
    }
    # Aksesoris cocok untuk jenis kendaraan apa (huruf kecil)
    ACCESSORY_TYPES = {
        'kursi_bayi':    ['mobil'],
        'phone_holder':  ['mobil', 'motor'],
        'bantal':        ['mobil'],
        'selimut':       ['mobil'],
        'helm_tambahan': ['motor'],
        'jas_hujan':     ['motor'],
        'box_belakang':  ['motor'],
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
    cancellation_reason = db.Column(db.String(500), nullable=True)

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

    # [OOP - ASOSIASI / OBJECT RELATIONSHIP]:
    # Menghubungkan objek Rental dengan objek User, Vehicle, dan Driver
    # sehingga data terkait dapat diakses secara relasional (e.g., rental.vehicle.price_per_day).
    user = db.relationship('User', backref=db.backref('rentals', lazy=True))
    vehicle = db.relationship('Vehicle', backref=db.backref('rentals', lazy=True))
    driver = db.relationship('Driver', backref=db.backref('rentals', lazy=True))
    # Riwayat perubahan status penyewaan.
    status_history = db.relationship(
        'RentalStatusHistory',
        back_populates='rental',
        cascade='all, delete-orphan',
        order_by='RentalStatusHistory.changed_at',
        lazy=True
    )

    # ---- Aturan bisnis pengingat & denda ----
    REMINDER_DAYS = 3                 # pengingat mulai H-3 sebelum batas kembali
    FINE_ADMIN_FEE = 50000            # denda administrasi per hari keterlambatan
    TRACKING_START = (-0.502106, 117.153709)   # titik awal tracking (Samarinda)

    # ---------------------------------------------------------
    # [OOP - ENKAPSULASI: KALKULASI FINANSIAL & DURASI]
    # Mengenkapsulasi rumus perhitungan tarif sewa, driver, asuransi,
    # dan aksesoris agar logika tidak tercecer di file route/template.
    # ---------------------------------------------------------
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
    # [OOP - ENKAPSULASI: LOGIKA WAKTU & DEADLINE PENGEMBALIAN]
    # Membungkus komputasi deadline (tanggal + jam), selisih waktu sewa,
    # pengingat H-3 (is_due_soon), dan status keterlambatan (is_overdue).
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
    # [OOP - ENKAPSULASI: LOGIKA PERHITUNGAN DENDA KETERLAMBATAN]
    # Membungkus perhitungan denda per hari, hari terlambat live/terkunci,
    # akumulasi denda, serta metode lock_fine() saat kendaraan dikembalikan.
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
    # [OOP - ENKAPSULASI: STATE TRANSITION & DATA INTEGRITY]
    # Menjamin transisi status hanya lewat satu pintu dengan efek samping
    # konsisten (aktivasi GPS, penguncian denda, pembaruan status pembayaran).
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

        # Simpan status terbaru.
        self.status = new_status

        # Catat waktu perubahan status.
        self.status_history.append(
            RentalStatusHistory(
                old_status=old_status,
                new_status=new_status,
                changed_at=datetime.now()
            )
        )

        return old_status


# =========================================================
# RENTAL STATUS HISTORY
# Riwayat setiap perubahan status penyewaan.
# =========================================================
class RentalStatusHistory(db.Model):
    __tablename__ = 'rental_status_history'

    id = db.Column(db.Integer, primary_key=True)

    rental_id = db.Column(
        db.Integer,
        db.ForeignKey('rental.id'),
        nullable=False,
        index=True
    )

    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)

    changed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        index=True
    )

    rental = db.relationship(
        'Rental',
        back_populates='status_history'
    )

# =========================================================
# REVIEW MODEL (Ulasan Pengguna)
# ---------------------------------------------------------
# [OOP - PEWARISAN & ASOSIASI]:
#   Mewarisi 'db.Model'. Menjadi entitas asosiatif yang menghubungkan
#   objek User (pemberi ulasan) dan Vehicle (kendaraan yang diulas).
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
# ---------------------------------------------------------
# [OOP - PEWARISAN / INHERITANCE]:
#   Mewarisi 'db.Model' dari SQLAlchemy untuk tabel notifikasi pengguna.
# [OOP - ENKAPSULASI / ENCAPSULATION]:
#   Membungkus metadata tampilan notifikasi (ikon Font Awesome & kelas CSS tone)
#   secara terisolasi di dalam kelas melalui dictionary _STYLE dan getter property.
# [OOP - ABSTRAKSI & FACTORY METHOD PATTERN]:
#   Menyediakan kumpulan classmethod (@classmethod: status_changed, return_reminder,
#   overdue_warning, fine_issued) sebagai pabrik pembuatan objek notifikasi.
#   Pemanggil (caller) tidak perlu menyusun judul, pesan, dan kategori manual,
#   cukup mengoper objek Rental.
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

    # Notifikasi pembayaran
    CATEGORY_PAYMENT_1H = 'payment_1h'
    CATEGORY_PAYMENT_30M = 'payment_30m'
    CATEGORY_PAYMENT_CANCELLED = 'payment_cancelled'

    # Notifikasi pengembalian kendaraan
    CATEGORY_RETURN_24H = 'return_24h'
    CATEGORY_RETURN_3H = 'return_3h'

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
        CATEGORY_STATUS: (
            'fa-solid fa-bell',
            'tone-info'
        ),
        CATEGORY_REMINDER: (
            'fa-solid fa-clock',
            'tone-warning'
        ),
        CATEGORY_OVERDUE: (
            'fa-solid fa-triangle-exclamation',
            'tone-danger'
        ),
        CATEGORY_FINE: (
            'fa-solid fa-file-invoice-dollar',
            'tone-danger'
        ),
        CATEGORY_PAYMENT_1H: (
            'fa-solid fa-credit-card',
            'tone-warning'
        ),
        CATEGORY_PAYMENT_30M: (
            'fa-solid fa-hourglass-half',
            'tone-warning'
        ),
        CATEGORY_PAYMENT_CANCELLED: (
            'fa-solid fa-ban',
            'tone-danger'
        ),
        CATEGORY_RETURN_24H: (
            'fa-solid fa-car-side',
            'tone-info'
        ),
        CATEGORY_RETURN_3H: (
            'fa-solid fa-clock',
            'tone-warning'
        ),
    }

    # Warna kartu berdasarkan jenis urusan.
    _CARD_STYLE = {
        CATEGORY_STATUS: 'card-status',
        CATEGORY_REMINDER: 'card-rental',
        CATEGORY_OVERDUE: 'card-rental',
        CATEGORY_FINE: 'card-rental',
        CATEGORY_PAYMENT_1H: 'card-payment',
        CATEGORY_PAYMENT_30M: 'card-payment',
        CATEGORY_PAYMENT_CANCELLED: 'card-payment',
        CATEGORY_RETURN_24H: 'card-rental',
        CATEGORY_RETURN_3H: 'card-rental',
    }

    # Teks dan warna badge berdasarkan jenis notifikasi.
    _BADGE_STYLE = {
        CATEGORY_STATUS: ('Status Pesanan', 'info'),
        CATEGORY_REMINDER: ('Pengingat', 'warning'),
        CATEGORY_OVERDUE: ('Denda', 'danger'),
        CATEGORY_FINE: ('Denda', 'danger'),
        CATEGORY_PAYMENT_1H: ('Pengingat Pembayaran', 'warning'),
        CATEGORY_PAYMENT_30M: ('Segera Bayar', 'warning'),
        CATEGORY_PAYMENT_CANCELLED: ('Dibatalkan', 'danger'),
        CATEGORY_RETURN_24H: ('Pengingat Pengembalian', 'info'),
        CATEGORY_RETURN_3H: ('Segera Dikembalikan', 'warning'),
    }

    # [OOP - ENKAPSULASI (Property)]: Menentukan ikon visual berdasarkan kategori
    @property
    def icon(self):
        return self._STYLE.get(
            self.category, self._STYLE[self.CATEGORY_STATUS])[0]

    # [OOP - ENKAPSULASI (Property)]: Menentukan tone warna badge berdasarkan kategori
    @property
    def tone(self):
        return self._STYLE.get(
            self.category, self._STYLE[self.CATEGORY_STATUS])[1]

    @property
    def card_tone(self):
        return self._CARD_STYLE.get(
            self.category,
            self._CARD_STYLE[self.CATEGORY_STATUS]
        )

    @property
    def badge_label(self):
        return self._BADGE_STYLE.get(
            self.category,
            self._BADGE_STYLE[self.CATEGORY_STATUS]
        )[0]

    @property
    def badge_tone(self):
        return self._BADGE_STYLE.get(
            self.category,
            self._BADGE_STYLE[self.CATEGORY_STATUS]
        )[1]

    # ---------------------------------------------------------
    # [OOP - ABSTRAKSI & FACTORY PATTERN]
    # Classmethod berikut bertindak sebagai Factory Method untuk
    # menghasilkan instance Notification dengan format pesan terstandar.
    # ---------------------------------------------------------
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
    def payment_reminder(cls, rental, category):
        """Membuat pengingat pembayaran H-1 jam atau H-30 menit."""
        deadline = rental.created_at + timedelta(hours=24)
        batas = deadline.strftime('%d-%m-%Y pukul %H:%M')

        if category == cls.CATEGORY_PAYMENT_1H:
            title = 'Pembayaran Akan Berakhir dalam 1 Jam'
            detail_waktu = 'Batas pembayaran tinggal sekitar 1 jam lagi.'
        else:
            title = 'Pembayaran Berakhir dalam 30 Menit'
            detail_waktu = 'Batas pembayaran tinggal sekitar 30 menit lagi.'

        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=category,
            title=title,
            message=(
                f'{detail_waktu} Segera selesaikan pembayaran untuk pesanan '
                f'{rental.booking_code}. Batas pembayaran: {batas}. '
                'Jika sampai batas waktu belum dibayar, '
                'pesanan akan dibatalkan otomatis.'
            ),
            old_status=rental.status,
            new_status=rental.status,
        )

    @classmethod
    def payment_cancelled(cls, rental, old_status=None):
        """Membuat notifikasi pembatalan otomatis akibat pembayaran."""
        deadline = rental.created_at + timedelta(hours=24)
        batas = deadline.strftime('%d-%m-%Y pukul %H:%M')

        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=cls.CATEGORY_PAYMENT_CANCELLED,
            title='Pesanan Dibatalkan karena Belum Dibayar',
            message=(
                f'Pesanan {rental.booking_code} dibatalkan otomatis karena '
                'pembayaran tidak diselesaikan dalam 24 jam sejak pemesanan. '
                f'Batas pembayaran: {batas}.'
            ),
            old_status=old_status or Rental.STATUS_MENUNGGU_BAYAR,
            new_status=Rental.STATUS_BATAL,
        )

    @classmethod
    def return_deadline_reminder(cls, rental, category):
        """Membuat pengingat menjelang batas pengembalian kendaraan."""
        batas = rental.return_deadline.strftime('%d-%m-%Y pukul %H:%M')

        if category == cls.CATEGORY_RETURN_24H:
            title = 'Pengingat Pengembalian Kendaraan dalam 24 Jam'
            keterangan = (
                'Waktu pengembalian sudah memasuki 24 jam terakhir.'
            )
        else:
            title = 'Pengingat: 3 Jam Menuju Pengembalian Kendaraan'
            keterangan = (
                'Waktu pengembalian tinggal sekitar 3 jam lagi.'
            )

        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=category,
            title=title,
            message=(
                f'{keterangan} Mohon kembalikan kendaraan untuk pesanan '
                f'{rental.booking_code} tepat waktu. '
                f'Batas pengembalian: {batas}. '
                f'Keterlambatan dikenakan denda '
                f'{cls._rp(rental.fine_per_day)} per hari.'
            ),
            old_status=rental.status,
            new_status=rental.status,
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
        batas = rental.return_deadline.strftime(
            '%d-%m-%Y pukul %H:%M'
        )

        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=cls.CATEGORY_OVERDUE,
            title='Pesanan Dikenakan Denda karena Belum Dikembalikan',
            message=(
                f'Kendaraan untuk pesanan {rental.booking_code} belum '
                f'dikembalikan melewati batas pengembalian ({batas}). '
                f'Saat ini keterlambatan dihitung {rental.late_days} hari '
                f'dengan denda berjalan '
                f'{cls._rp(rental.active_fine)}. '
                'Segera kembalikan kendaraan agar denda tidak bertambah.'
            ),
            old_status=rental.status,
            new_status=rental.status,
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
# MODEL TURUNAN USER (Kelola Pelanggan & Kelola Admin)
#
#   [OOP - DIAGRAM HIERARKI PEWARISAN (INHERITANCE)]:
#
#              db.Model
#                 |
#                User <-----+
#               /    \      |  ProfileMixin (Abstraksi / Mixin)
#              /      \     +--------+
#             v        v             |
#         Customer    Admin <--------+
#                       |
#                       v
#                   SuperAdmin
#
# ---------------------------------------------------------
# [OOP - PEWARISAN (INHERITANCE) & MULTIPLE INHERITANCE]:
#   - Customer mewarisi User & ProfileMixin (Multiple Inheritance).
#   - Admin mewarisi User & ProfileMixin (Multiple Inheritance).
#   - SuperAdmin mewarisi Admin (Pewarisan Bertingkat / Multilevel Inheritance).
#
# [OOP - POLIMORFISME / POLYMORPHISM]:
#   Menerapkan Single-Table Polymorphism (SQLAlchemy ORM).
#   Semua kelas turunan disimpan di tabel 'user', namun saat di-query:
#   - Objek otomatis di-instansiasi sebagai Customer, Admin, atau SuperAdmin.
#   - Property '.code' bersifat polimorfik: menghasilkan 'PLG001', 'ADM001', atau 'SA001'.
#   - Attribute 'is_super_admin' bernilai False untuk Admin dan True untuk SuperAdmin.
# =========================================================
class ProfileMixin:
    """
    [OOP - ABSTRAKSI & MIXIN]:
    Kelas bantuan abstrak penyedia perilaku bersama (foto profil & dokumen akun)
    untuk diwariskan ke Customer dan Admin tanpa membuat tabel terpisah di database.
    """

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
    """
    [OOP - MULTIPLE INHERITANCE & POLIMORFISME]:
    Mewarisi sifat ProfileMixin & User.
    Menggunakan polymorphic_identity = 'user'.
    """
    ROLE = 'user'
    CODE_PREFIX = 'PLG'
    __mapper_args__ = {'polymorphic_identity': ROLE}

    # [OOP - POLIMORFISME]: Format kode ID khusus pelanggan (contoh: PLG001)
    @property
    def code(self):
        return f"{self.CODE_PREFIX}{self.id:03d}"

    # [OOP - ENKAPSULASI]: Mengenkapsulasi query histori penyewaan milik customer ini
    @property
    def rental_history(self):
        return (Rental.query
                .filter_by(user_id=self.id)
                .order_by(Rental.created_at.desc())
                .all())


class Admin(ProfileMixin, User):
    """
    [OOP - MULTIPLE INHERITANCE & POLIMORFISME]:
    Mewarisi sifat ProfileMixin & User.
    Menggunakan polymorphic_identity = 'admin'.
    """
    ROLE = 'admin'
    CODE_PREFIX = 'ADM'
    is_super_admin = False
    __mapper_args__ = {'polymorphic_identity': ROLE}

    # [OOP - POLIMORFISME]: Format kode ID khusus admin (contoh: ADM001)
    @property
    def code(self):
        return f"{self.CODE_PREFIX}{self.id:03d}"


class SuperAdmin(Admin):
    """
    [OOP - PEWARISAN BERTINGKAT / MULTILEVEL INHERITANCE & POLIMORFISME]:
    Mewarisi class Admin -> User.
    Meng-override atribut is_super_admin menjadi True dan prefix menjadi 'SA'.
    """
    ROLE = 'superadmin'
    CODE_PREFIX = 'SA'
    is_super_admin = True
    __mapper_args__ = {'polymorphic_identity': ROLE}
