# ═════════════════════════════════════════════════════════════
#     MODEL DATA DAN LOGIKA BISNIS WEBSITE KeSanaSini (models.py)

#     ⤷ Mendefinisikan class yang merepresentasikan data utama website,
#       seperti User, Vehicle, Driver, Rental, RentalCancellation, Review, dan Notification.
#     ⤷ Mengatur struktur tabel database, atribut, serta relasi antar-model menggunakan SQLAlchemy ORM.
#     ⤷ Menyediakan method dan property untuk mengelola data serta menjalankan logika bisnis,
#       seperti perhitungan biaya sewa, pengelolaan status pesanan, dan denda.
#     ⤷ Menerapkan konsep OOP, seperti enkapsulasi, pewarisan, polimorfisme, dan asosiasi antarobjek.
#     ⤷ Menjadi penghubung antara objek Python dan database,
#       sehingga routes.py dapat mengakses serta mengelola data tanpa harus menulis query database secara manual.
# ═════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════
#   A.   |   IMPORT
# ═════════════════════════════════════════════════════════════
# ↓ Mengimpor objek database SQLAlchemy dari app.
from app import db
# ABC dan abstractmethod digunakan untuk mendefinisikan kontrak abstrak secara eksplisit.
from abc import ABC, abstractmethod
# ↓ Mengimpor fungsi untuk mengenkripsi password menjadi hash dan memeriksa password dengan hash yang tersimpan.
from werkzeug.security import generate_password_hash, check_password_hash
# ↓ Mengimpor datetime untuk mengelola tanggal dan waktu, serta timedelta untuk menghitung selisih atau durasi waktu.
from datetime import datetime, timedelta
# ↓ Mengimpor fungsi matematika, misalnya pembulatan ke atas menggunakan math.ceil().
import math



# ═════════════════════════════════════════════════════════════
#   B.   |   ABSTRAKSI PERHITUNGAN HARGA SEWA
# ═════════════════════════════════════════════════════════════


# Menentukan method yang harus dimiliki oleh class penghitung harga.
class AbstractRentalPricing(ABC):

    @abstractmethod
    def calculate_total(self, rental):
        # Setiap class turunannya harus menyediakan cara menghitung total.
        raise NotImplementedError


# Menghitung total biaya berdasarkan aturan harga yang digunakan website.
class StandardRentalPricing(AbstractRentalPricing):

    def calculate_total(self, rental):
        # Total berasal dari biaya kendaraan, sopir, aksesori, dan asuransi.
        return (
            rental.vehicle_cost
            + rental.driver_cost
            + rental.accessories_cost
            + rental.insurance_cost
        )


# Objek ini digunakan oleh Rental untuk menghitung total biaya.
_RENTAL_PRICING = StandardRentalPricing()



# ═════════════════════════════════════════════════════════════════════════════
#   C.   |   USER MODEL (CLASS USER)
# ═════════════════════════════════════════════════════════════════════════════
# User mewarisi db.Model agar dapat dipetakan ke tabel database.
class User(db.Model):


    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT USER]
    # ═════════════════════════════════════════════════════════════════════════

    # Awalan kode akun jika tidak menggunakan jenis akun khusus.
    CODE_PREFIX = 'USR'

    # Membuat kode akun dari awalan dan ID pengguna.
    def get_code(self):
        return f"{self.CODE_PREFIX}{self.id:03d}"

    # ↪  [DATA DIRI USER]
    # ─────────────────────────────────────
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(100), nullable=False)
    birth_date      = db.Column(db.Date, nullable=False)
    gender          = db.Column(db.String(20), nullable=False)
    email           = db.Column(db.String(120), unique=True, nullable=False)
    phone           = db.Column(db.String(20), nullable=False)
    emergency_phone = db.Column(db.String(20), nullable=False)
    password_hash   = db.Column(db.String(128), nullable=False)
    ktp_file        = db.Column(db.String(255), nullable=True)
    sim_file        = db.Column(db.String(255), nullable=True)
    
    # ↪  [DATA DIRI - Membedakan "ADMIN" & "USER" & "SUPERADMIN"]
    # ─────────────────────────────────────
    role            = db.Column(db.String(20), nullable=False, default='user')

    # ↪  [DATA TAMBAHAN - Fitur kelola pelanggan dan admin]
    # ─────────────────────────────────────
    is_active       = db.Column(db.Boolean, nullable=False, default=True)
    profile_photo   = db.Column(db.String(255), nullable=True)
    ktp_number      = db.Column(db.String(20), nullable=True)
    sim_number      = db.Column(db.String(20), nullable=True)

    # SQLAlchemy menggunakan kolom role untuk menentukan jenis kelas objek User saat data dibaca dari database.
    __mapper_args__ = {'polymorphic_on': role}               


    # ═════════════════════════════════════════════════════════════════════════
    #                           [METHOD USER]
    # ═════════════════════════════════════════════════════════════════════════

    # ENKAPSULASI:
    # Password diolah melalui method ini agar prosesnya terpusat.
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Memeriksa password yang dimasukkan dengan hash di database.
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



# ═════════════════════════════════════════════════════════════════════════════
#   D.   |   KENDARAAN MODEL (CLASS VEHICLE)
# ═════════════════════════════════════════════════════════════════════════════

# Menyimpan data kendaraan yang tersedia untuk disewa.
class Vehicle(db.Model):


    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT VEHICLE]
    # ═════════════════════════════════════════════════════════════════════════
    
    # ↪  [DATA VEHICLE]
    # ─────────────────────────────────────
    id              = db.Column(db.Integer, primary_key =True)
    photo           = db.Column(db.String(255), nullable=False)
    brand           = db.Column(db.String(50), nullable =False)
    model           = db.Column(db.String(100), nullable=False)
    gallery         = db.Column(db.Text, nullable       =True)  
    vehicle_number  = db.Column(
                        db.String(20),
                        unique  =True,
                        nullable=False
    )
    year            = db.Column(db.Integer, nullable    =False)
    vehicle_type    = db.Column(
                        db.String(20),
                        nullable=False
    )
    seats           = db.Column(db.Integer, nullable    =False)
    luggage         = db.Column(
                        db.Integer,
                        nullable    =False,
                        default     =0
    )
    price_per_day   = db.Column(
                        db.Integer,
                        nullable=False
    )
    rental_type     = db.Column(
                        db.String(30),
                        nullable=False
    )

    # ↪  [DATA TAMBAHAN - Fitur kelola kendaraan]
    # ─────────────────────────────────────
    color           = db.Column(db.String(30), nullable=True)
    chassis_number  = db.Column(db.String(50), unique=True, nullable=True)
    engine_number   = db.Column(db.String(50), unique=True, nullable=True)
    fuel            = db.Column(db.String(20), nullable=True, default='Bensin')
    transmission    = db.Column(db.String(20), nullable=True, default='Manual')
    engine_cc       = db.Column(db.Integer, nullable=True)
    facilities      = db.Column(db.Text, nullable=True)   
    notes           = db.Column(db.Text, nullable=True)
    is_active       = db.Column(db.Boolean, nullable=False, default=True)

    # Koordinat kendaraan saat fitur tracking digunakan.
    current_lat     = db.Column(db.Float, nullable=True)
    current_lng     = db.Column(db.Float, nullable=True)


    # ═════════════════════════════════════════════════════════════════════════
    #                   [METHOD VEHICLE - INFORMASI KENDARAAN]
    # ═════════════════════════════════════════════════════════════════════════
    @property
    def full_name(self):
        # Menggabungkan merek dan model kendaraan.
        return f"{self.brand} {self.model}"

    @property
    def facility_list(self):
        # Mengubah daftar fasilitas dari teks menjadi list.
        if not self.facilities:
            return []
        return [f.strip() for f in self.facilities.split(',')]

    @property
    def photo_list(self):
        # Menggabungkan foto utama dan foto tambahan.
        photos = [self.photo]
        if self.gallery:
            photos += [p.strip() for p in self.gallery.split(',')]
        return photos


    # ═════════════════════════════════════════════════════════════════════════
    #                   [METHOD VEHICLE - ULASAN DAN STATUS KENDARAAN]
    # ═════════════════════════════════════════════════════════════════════════
    @property
    def review_count(self):
        # Menghitung jumlah ulasan kendaraan.
        return len(self.reviews)

    @property
    def avg_rating(self):
        # Menghitung rata-rata nilai ulasan.
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    def rating_count(self, star):
        # Menghitung jumlah ulasan dengan nilai tertentu.
        return sum(1 for r in self.reviews if r.rating == star)

    def rating_percent(self, star):
        # Menghitung persentase ulasan untuk nilai tertentu.
        if not self.reviews:
            return 0
        return round(self.rating_count(star) / len(self.reviews) * 100)

    @property
    def latest_reviews(self):
        # Mengambil dua ulasan terbaru.
        return sorted(self.reviews, key=lambda r: r.created_at, reverse=True)[:2]
    
    @property
    def current_status(self):
        # Memeriksa apakah kendaraan sedang digunakan untuk menyewa.
        active_rental = Rental.query.filter_by(
                        vehicle_id=self.id,
                        status=Rental.STATUS_BERJALAN
        ).first()
        if active_rental:
            return "Disewa"
        return "Tersedia"



# ═════════════════════════════════════════════════════════════════════════════
#   E.   |   SOPIL MODEL (CLASS DRIVER)
# ═════════════════════════════════════════════════════════════════════════════

# Menyimpan informasi sopir dan pesanan yang ditanganinya.
class Driver(db.Model):
    

    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT DRIVER]
    # ═════════════════════════════════════════════════════════════════════════
    
    # ↪  [DATA DRIVER]
    # ─────────────────────────────────────
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(100), nullable=False)
    phone           = db.Column(db.String(20), nullable=False)
    is_available    = db.Column(db.Boolean, nullable=False, default=True)
    photo           = db.Column(db.String(255), nullable=True, default='default_driver.png')
    created_at      = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # ↪  [DATA TAMBAHAN - Fitur kelola sopir]
    # ─────────────────────────────────────
    address         = db.Column(db.String(255), nullable=True)
    description     = db.Column(db.Text, nullable=True)
    sim_photo       = db.Column(db.String(255), nullable=True)


    # ═════════════════════════════════════════════════════════════════════════
    #                           [METHOD DRIVER]
    # ═════════════════════════════════════════════════════════════════════════

    @property
    def code(self):
        # Membuat kode sopir dari ID-nya.
        return f"SP{self.id:03d}"

    @property
    def current_rental(self):
        # Mengambil pesanan aktif terbaru yang menggunakan sopir ini.
        aktif = [
            Rental.STATUS_MENUNGGU_KONFIRMASI,
            Rental.STATUS_PENGAMBILAN,
            Rental.STATUS_DIPAKAI,
            Rental.STATUS_PENGEMBALIAN]
        return (Rental.query
                .filter(Rental.driver_id == self.id, Rental.status.in_(aktif))
                .order_by(Rental.start_date.desc())
                .first())

    @property
    def status_label(self):
        # Menentukan status sopir berdasarkan pesanan aktifnya.
        r = self.current_rental
        if r is None:
            return 'Tersedia'
        if r.status == Rental.STATUS_MENUNGGU_KONFIRMASI:
            return 'Menunggu Konfirmasi'
        return 'Berjalan'

    @property
    def total_orders(self):
        # Menghitung pesanan yang tidak batal dalam setahun terakhir.
        batas = datetime.now() - timedelta(days=365)
        return (Rental.query
                .filter(Rental.driver_id == self.id,
                        Rental.status != Rental.STATUS_BATAL,
                        Rental.created_at >= batas)
                .count())

    @property
    def avg_rating(self):
        # Menghitung rata-rata ulasan dari kendaraan pada pesanan yang selesai.
        pasangan = {(r.user_id, r.vehicle_id) for r in self.rentals
                    if r.status == Rental.STATUS_SELESAI}
        nilai = [rv.rating for (u, v) in pasangan
                 for rv in Review.query.filter_by(user_id=u, vehicle_id=v)]
        return round(sum(nilai) / len(nilai), 2) if nilai else 0

    @property
    def rating_label(self):
        # Mengubah nilai rata-rata menjadi keterangan.
        n = self.avg_rating
        if n >= 4.5:
            return 'Sangat Baik'
        if n >= 3.5:
            return 'Baik'
        return 'Cukup' if n > 0 else 'Belum ada penilaian'



# ═════════════════════════════════════════════════════════════
#   F.   |   PESANAN MODEL (CLASS RENTAL)
# ═════════════════════════════════════════════════════════════

# Menyimpan pesanan sewa beserta biaya, status, dan denda.
class Rental(db.Model):
    

    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT RENTAL]
    # ═════════════════════════════════════════════════════════════════════════
    
    # ↪  [STATUS PESANAN]
    # ─────────────────────────────────────
    STATUS_MENUNGGU_BAYAR       = 'Menunggu Pembayaran'
    STATUS_MENUNGGU_KONFIRMASI  = 'Menunggu Konfirmasi'
    STATUS_PENGAMBILAN          = 'Kendaraan Dalam Pengambilan'
    STATUS_DIPAKAI              = 'Kendaraan Sedang Dipakai'
    STATUS_PENGEMBALIAN         = 'Dalam Proses Pengembalian'
    STATUS_SELESAI              = 'Selesai'
    STATUS_BATAL                = 'Batal'

    # Daftar status yang diperbolehkan dalam proses penyewaan.
    ALL_STATUS = [
        STATUS_MENUNGGU_BAYAR, STATUS_MENUNGGU_KONFIRMASI, 
        STATUS_PENGAMBILAN, STATUS_DIPAKAI, 
        STATUS_PENGEMBALIAN, STATUS_SELESAI, STATUS_BATAL
    ]

    # Nama status lama tetap dipakai agar kode yang sudah ada tidak rusak.
    STATUS_MENUNGGU = STATUS_MENUNGGU_KONFIRMASI
    STATUS_BERJALAN = STATUS_DIPAKAI

    # Biaya sopir per hari.
    DRIVER_FEE = 150000

    # Nama dan harga aksesori.                   
    ACCESSORIES = {
        'kursi_bayi':    ('Kursi Bayi (Baby Car Seat)', 15000),
        'phone_holder':  ('Phone holder', 5000),
        'bantal':        ('Bantal', 5000),
        'selimut':       ('Selimut', 10000),
        'helm_tambahan': ('Helm tambahan', 10000),
        'jas_hujan':     ('Jas hujan', 5000),
        'box_belakang':  ('Box belakang', 15000),
    }

    # Menentukan jenis kendaraan yang bisa menggunakan setiap aksesori.
    ACCESSORY_TYPES = {
        'kursi_bayi':    ['mobil'],
        'phone_holder':  ['mobil', 'motor'],
        'bantal':        ['mobil'],
        'selimut':       ['mobil'],
        'helm_tambahan': ['motor'],
        'jas_hujan':     ['motor'],
        'box_belakang':  ['motor'],
    }

    # Pilihan asuransi beserta biayanya.
    INSURANCES = {                          
        'dasar':   ('Dasar', 0),
        'lengkap': ('Lengkap', 50000),
    }

    # ↪  [DATA PESANAN]
    # ─────────────────────────────────────
    id                  = db.Column(db.Integer, primary_key=True)
    booking_code        = db.Column(db.String(20), unique=True, nullable=False)

    user_id             = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id          = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    driver_id           = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True) # Tambahan Relasi Sopir

    start_date          = db.Column(db.Date, nullable=False)
    end_date            = db.Column(db.Date, nullable=False)

    # Tanggal dan jam disimpan terpisah.
    pickup_time         = db.Column(db.String(5), nullable=False, default='10:00')
    return_time         = db.Column(db.String(5), nullable=False, default='10:00')
    status              = db.Column(db.String(50), nullable=False, default=STATUS_MENUNGGU_BAYAR)
    created_at          = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # Informasi pembayaran dan pembatalan.
    payment_method      = db.Column(db.String(50), nullable=True)
    payment_status      = db.Column(db.String(20), nullable=False, default='Belum Lunas') # 'Lunas' / 'Belum Lunas'
    cancellation_reason = db.Column(db.String(500), nullable=True)

    # Pilihan layanan tambahan saat menyewa.
    with_driver         = db.Column(db.Boolean, nullable=False, default=False)
    accessories         = db.Column(db.String(200), nullable=True, default='')  
    insurance           = db.Column(db.String(20), nullable=False, default='dasar')
    purpose             = db.Column(db.String(50), nullable=True)
    region              = db.Column(db.String(30), nullable=True)
    destination_city    = db.Column(db.String(100), nullable=True)
    pickup_location     = db.Column(db.String(100), nullable=True)
    return_location     = db.Column(db.String(100), nullable=True)
    special_request     = db.Column(db.Text, nullable=True)

    # Dokumen yang diperlukan untuk penyewaan.
    ktp_file            = db.Column(db.String(255), nullable=True)
    sim_file            = db.Column(db.String(255), nullable=True)

    # ---- Denda keterlambatan ----
    # Selama kendaraan masih dipakai, denda dihitung LIVE (berjalan).
    # Saat kendaraan dikembalikan, nilainya DIKUNCI ke kolom di bawah ini
    # supaya tidak terus bertambah setelah mobil masuk garasi.
    fine_days           = db.Column(db.Integer, nullable=False, default=0)
    fine_amount         = db.Column(db.Integer, nullable=False, default=0)
    fine_paid           = db.Column(db.Boolean, nullable=False, default=False)


    # ═════════════════════════════════════════════════════════════════════════
    #                           [RELASI ANTAR-MODEL]
    # ═════════════════════════════════════════════════════════════════════════

    # Menghubungkan pesanan dengan pelanggan, kendaraan, dan sopir.
    user            = db.relationship('User', backref=db.backref('rentals', lazy=True))
    vehicle         = db.relationship('Vehicle', backref=db.backref('rentals', lazy=True))
    driver          = db.relationship('Driver', backref=db.backref('rentals', lazy=True))

    # Menyimpan riwayat perubahan status pesanan.
    status_history = db.relationship(
        'RentalStatusHistory',
        back_populates='rental',
        cascade='all, delete-orphan',
        order_by='RentalStatusHistory.changed_at',
        lazy=True
    )

    # Menyimpan pengajuan pembatalan yang terkait dengan pesanan.
    cancellations = db.relationship(
        'RentalCancellation',
        back_populates='rental',
        cascade='all, delete-orphan',
        order_by='RentalCancellation.id',
        lazy=True
    )

    # Aturan bisnis pengingat & denda
    REMINDER_DAYS   = 3                         # pengingat mulai H-3 sebelum batas kembali
    FINE_ADMIN_FEE  = 50000                     # denda administrasi per hari keterlambatan
    TRACKING_START  = (-0.502106, 117.153709)   # titik awal tracking (Samarinda)


    # ═════════════════════════════════════════════════════════════════════════
    #                           [METHOD RENTAL]
    # ═════════════════════════════════════════════════════════════════════════
    @property
    def duration_days(self):
                # Durasi minimal dihitung satu hari.
        return max(1, (self.end_date - self.start_date).days)

    @property
    def accessory_keys(self):
        # Mengambil kode aksesori yang valid dari data pesanan.
        return [
            k for k in (self.accessories or '').split(',')
            if k in self.ACCESSORIES]

    @property
    def vehicle_cost(self):
        # Harga kendaraan dikalikan lama penyewaan.
        return self.duration_days * self.vehicle.price_per_day

    @property
    def driver_cost(self):
        # Biaya sopir hanya dihitung jika pelanggan memilih sopir.
        return self.duration_days * self.DRIVER_FEE if self.with_driver else 0

    @property
    def accessories_cost(self):
        # Menjumlahkan harga semua aksesori yang dipilih.
        return sum(self.ACCESSORIES[k][1] for k in self.accessory_keys)

    @property
    def insurance_cost(self):
        # Menghitung biaya asuransi sesuai pilihan dan durasi sewa.
        price = self.INSURANCES.get(self.insurance or 'dasar', ('', 0))[1]
        return price * self.duration_days

    # ABSTRAKSI:
    # Perhitungan total diserahkan kepada objek penghitung harga sewa.
    @property
    def total_price(self):
        return _RENTAL_PRICING.calculate_total(self)

    # ↪  [BATAS WAKTU PENYEWAAN ATURAN]
    # ─────────────────────────────────────
    @property
    def is_pickup_expired(self):
        # Memeriksa apakah batas waktu pengambilan sudah lewat.
        return (
            self.status in (
                self.STATUS_MENUNGGU_KONFIRMASI,
                self.STATUS_PENGAMBILAN
            )
            and datetime.now() > self.return_deadline
        )
    
    @property
    def return_deadline(self):
        # Menggabungkan tanggal dan jam pengembalian menjadi satu waktu.
        try:
            jam = datetime.strptime(self.return_time or '10:00', '%H:%M').time()
        except ValueError:
            jam = datetime.strptime('10:00', '%H:%M').time()
        return datetime.combine(self.end_date, jam)

    @property
    def is_in_use(self):
        # Memeriksa apakah kendaraan sedang digunakan.
        return self.status == self.STATUS_DIPAKAI

    @property
    def time_remaining(self):
        # Menghitung sisa waktu sampai batas pengembalian.
        return self.return_deadline - datetime.now()

    @property
    def is_overdue(self):
        # Bernilai True jika kendaraan masih digunakan setelah batas waktu.
        return self.is_in_use and self.time_remaining.total_seconds() < 0

    @property
    def is_due_soon(self):
        # Memeriksa apakah waktu pengembalian sudah masuk periode pengingat.
        sisa = self.time_remaining.total_seconds()

        return (
            self.is_in_use
            and 0 <= sisa <= self.REMINDER_DAYS * 86400
        )

    @property
    def remaining_label(self):
        # Mengubah sisa waktu menjadi teks yang ditampilkan di halaman.
        sisa = max(0, int(self.time_remaining.total_seconds()))
        hari, sisa = divmod(sisa, 86400)
        jam = sisa // 3600
        if hari and jam:
            return f'{hari} hari {jam} jam'
        if hari:
            return f'{hari} hari'
        return f'{jam} jam' if jam else 'kurang dari 1 jam'


    # ═════════════════════════════════════════════════════════════════════════
    #                    [METHOD RENTAL - PERHITUNGAN DENDA]
    # ═════════════════════════════════════════════════════════════════════════
    @property
    def fine_per_day(self):
        # Denda harian terdiri dari harga kendaraan dan biaya administrasi.
        return self.vehicle.price_per_day + self.FINE_ADMIN_FEE

    def _late_days_at(self, moment):
        # Keterlambatan sebagian hari tetap dihitung satu hari.
        telat = (moment - self.return_deadline).total_seconds()
        return math.ceil(telat / 86400) if telat > 0 else 0

    @property
    def late_days(self):
        # Saat kendaraan masih digunakan, hitung keterlambatan secara langsung.
        if self.is_in_use:
            return self._late_days_at(datetime.now())
        # Jika sudah tidak digunakan, ambil jumlah hari yang tersimpan.
        return self.fine_days or 0

    @property
    def active_fine(self):
        # Menghitung denda berjalan atau mengambil denda yang sudah disimpan.
        if self.is_in_use:
            return self.late_days * self.fine_per_day
        return self.fine_amount or 0

    @property
    def has_fine(self):
        # Memeriksa apakah pesanan memiliki denda.
        return self.active_fine > 0

    @property
    def final_total_price(self):
        # Total akhir terdiri dari biaya sewa dan denda.
        return self.total_price + self.active_fine

    def lock_fine(self):
        # Menyimpan jumlah hari dan total denda saat kendaraan dikembalikan.
        self.fine_days = self._late_days_at(datetime.now())
        self.fine_amount = self.fine_days * self.fine_per_day
        if self.fine_amount == 0:
            self.fine_paid = False


    # ═════════════════════════════════════════════════════════════════════════
    #                    [METHOD RENTAL - PERUBAHAN STATUS]
    # ═════════════════════════════════════════════════════════════════════════
    def change_status(self, new_status):
        # Mengubah status sekaligus menjalankan proses yang terkait.
        if new_status not in self.ALL_STATUS or new_status == self.status:
            return None

        old_status = self.status

        # Pembayaran dianggap lunas saat kendaraan masuk tahap pengambilan.
        if new_status == self.STATUS_PENGAMBILAN:
            self.payment_status = 'Lunas'
    
        # Saat kendaraan mulai digunakan, aktifkan lokasi awal dan reset denda.
        if new_status == self.STATUS_DIPAKAI:
            self.vehicle.current_lat, self.vehicle.current_lng = self.TRACKING_START
            self.fine_days, self.fine_amount, self.fine_paid = 0, 0, False
        elif old_status == self.STATUS_DIPAKAI:
            # Hentikan pelacakan saat kendaraan tidak lagi digunakan.
            self.vehicle.current_lat = None
            self.vehicle.current_lng = None
            
            if new_status == self.STATUS_BATAL:
                self.fine_days, self.fine_amount, self.fine_paid = 0, 0, False
            else:
                self.lock_fine()

        # Hapus alasan pembatalan jika pesanan diaktifkan kembali.
        if old_status == self.STATUS_BATAL and new_status != self.STATUS_BATAL:
            self.cancellation_reason = None

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



# ═════════════════════════════════════════════════════════════
#   F.   |   HISTORY PESANAN MODEL (HISTORY MODEL)
# ═════════════════════════════════════════════════════════════

# Menyimpan catatan setiap perubahan status pesanan.
class RentalStatusHistory(db.Model):
    

    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT RENTAL]
    # ═════════════════════════════════════════════════════════════════════════
    
    # ↪  [DATA HISTORY]
    # ─────────────────────────────────────
    __tablename__   = 'rental_status_history'

    id              = db.Column(db.Integer, primary_key=True)

    rental_id       = db.Column(
                        db.Integer,
                        db.ForeignKey('rental.id'),
                        nullable=False,
                        index=True
    )

    old_status      = db.Column(db.String(50), nullable=True)
    new_status      = db.Column(db.String(50), nullable=False)

    changed_at      = db.Column(
                        db.DateTime,
                        nullable=False,
                        default=datetime.now,
                        index=True
    )

    # Menghubungkan riwayat dengan pesanan yang berubah status.
    rental = db.relationship(
        'Rental',
        back_populates='status_history'
    )



# ═════════════════════════════════════════════════════════════
#   H.   |   RENTAL CANCELLATION MODEL
# ═════════════════════════════════════════════════════════════

# Menyimpan pengajuan pembatalan dan proses pengembalian dana.
class RentalCancellation(db.Model):


    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT RENTAL CANCELLATION]
    # ═════════════════════════════════════════════════════════════════════════
    
    # ↪  [DATA RENTAL CANCELLATION]
    # ─────────────────────────────────────
    __tablename__               = 'rental_cancellation'

    # Status yang digunakan selama proses pembatalan.
    STATUS_DIAJUKAN             = 'Pembatalan Diajukan'
    STATUS_DISETUJUI            = 'Pembatalan Disetujui'
    STATUS_DITOLAK              = 'Pembatalan Ditolak'
    STATUS_MENUNGGU_REFUND      = 'Menunggu Pengembalian Dana'
    STATUS_DANA_DIKEMBALIKAN    = 'Dana dikembalikan'

    id = db.Column(
            db.Integer,
            primary_key=True
    )

    rental_id = db.Column(
                    db.Integer,
                    db.ForeignKey('rental.id'),
                    nullable=False,
                    index=True
    )

    # Alasan pembatalan yang disampaikan oleh pihak pengaju.
    reason = db.Column(
                db.String(500),
                nullable=False
    )

    # Menandai pihak yang mengajukan pembatalan.
    initiated_by = db.Column(
        db.String(20),
        nullable=False
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default=STATUS_DIAJUKAN
    )

    # Waktu pengajuan dan keputusan pembatalan.
    requested_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True
    )
    rejected_at = db.Column(db.DateTime, nullable=True
    )
    cancelled_at = db.Column(db.DateTime,nullable=True
    )

    # Waktu dana dikembalikan kepada pelanggan.
    refunded_at = db.Column(
                    db.DateTime,
                    nullable=True
    )

    # Jumlah dana yang perlu atau sudah dikembalikan.
    refund_amount = db.Column(
                    db.Integer,
                    nullable=True
    )

    # Catatan tambahan dari admin.
    admin_note = db.Column(
        db.Text,
        nullable=True
    )

    # Menghubungkan data pembatalan dengan pesanan terkait.
    rental = db.relationship(
        'Rental',
        back_populates='cancellations'
    )



# ═════════════════════════════════════════════════════════════
#   I.   |   REVIEW MODEL
# ═════════════════════════════════════════════════════════════

# Menyimpan ulasan pelanggan terhadap kendaraan.
class Review(db.Model):


    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT REVIEW]
    # ═════════════════════════════════════════════════════════════════════════
    
    # ↪  [DATA REVIEW]
    # ─────────────────────────────────────
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id  = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)

    # Nilai ulasan menggunakan skala 1 sampai 5.
    rating      = db.Column(db.Integer, nullable=False)   # 1 sampai 5
    comment     = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # Menghubungkan ulasan dengan pelanggan dan kendaraan.
    user        = db.relationship('User', backref=db.backref('reviews', lazy=True))
    vehicle     = db.relationship('Vehicle', backref=db.backref('reviews', lazy=True))



# ═════════════════════════════════════════════════════════════
#   J.   |   NOTIFICATION MODEL
# ═════════════════════════════════════════════════════════════

# Menyimpan notifikasi dan informasi tampilannya di website.
class Notification(db.Model):


    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT REVIEW]
    # ═════════════════════════════════════════════════════════════════════════
    
    # ↪  [DATA REVIEW]
    # ─────────────────────────────────────
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(
                db.Integer,
                db.ForeignKey('user.id'),
                nullable=False
    )
    rental_id   = db.Column(
                db.Integer,
                db.ForeignKey('rental.id'),
                nullable=False
    )
    title       = db.Column(db.String(100), nullable=False)
    message     = db.Column(db.Text, nullable=False)

    # Status sebelum dan sesudah perubahan.
    old_status  = db.Column(db.String(50), nullable=True)
    new_status  = db.Column(db.String(50), nullable=False)

    is_read     = db.Column(db.Boolean, nullable=False, default=False)

    created_at  = db.Column(
                db.DateTime,
                nullable=False,
                default=datetime.now
    )

    # Jenis notifikasi untuk perubahan status dan pengingat.
    CATEGORY_STATUS     = 'status'
    CATEGORY_REMINDER   = 'reminder'
    CATEGORY_OVERDUE    = 'overdue'
    CATEGORY_FINE       = 'fine'

    # Jenis notifikasi pembayaran.
    CATEGORY_PAYMENT_1H         = 'payment_1h'
    CATEGORY_PAYMENT_30M        = 'payment_30m'
    CATEGORY_PAYMENT_CANCELLED  = 'payment_cancelled'
    CATEGORY_PICKUP_EXPIRED     = 'pickup_expired'

    # Jenis notifikasi pengembalian kendaraan.
    CATEGORY_RETURN_24H = 'return_24h'
    CATEGORY_RETURN_3H  = 'return_3h'

    category    = db.Column(
                db.String(20),
                nullable=False,
                default=CATEGORY_STATUS
    )

    # Menghubungkan notifikasi dengan akun dan pesanan.
    user = db.relationship(
        'User',
        backref=db.backref('notifications', lazy=True)
    )

    rental = db.relationship(
        'Rental',
        backref=db.backref('notifications', lazy=True)
    )

    # ─────────────────────────────────────────────────────────
    # PENGATURAN TAMPILAN NOTIFIKASI
    # ─────────────────────────────────────────────────────────
    # Ikon dan warna teks untuk setiap jenis notifikasi.
    __STYLE = {
        CATEGORY_STATUS: ('fa-solid fa-bell', 'tone-info'),
        CATEGORY_REMINDER: ('fa-solid fa-clock', 'tone-warning'),
        CATEGORY_OVERDUE: ('fa-solid fa-triangle-exclamation', 'tone-danger'),
        CATEGORY_FINE: ('fa-solid fa-file-invoice-dollar', 'tone-danger'),
        CATEGORY_PAYMENT_1H: ('fa-solid fa-credit-card', 'tone-warning'),
        CATEGORY_PAYMENT_30M: ('fa-solid fa-hourglass-half', 'tone-warning'),
        CATEGORY_PAYMENT_CANCELLED: ('fa-solid fa-ban', 'tone-danger'),
        CATEGORY_PICKUP_EXPIRED: ('fa-solid fa-ban', 'tone-danger'),
        CATEGORY_RETURN_24H: ('fa-solid fa-car-side', 'tone-info'),
        CATEGORY_RETURN_3H: ('fa-solid fa-clock', 'tone-warning'),
    }

    # Class CSS untuk latar kartu notifikasi.
    __CARD_STYLE = {
        CATEGORY_STATUS: 'card-status',
        CATEGORY_REMINDER: 'card-rental',
        CATEGORY_OVERDUE: 'card-rental',
        CATEGORY_FINE: 'card-rental',
        CATEGORY_PAYMENT_1H: 'card-payment',
        CATEGORY_PAYMENT_30M: 'card-payment',
        CATEGORY_PAYMENT_CANCELLED: 'card-payment',
        CATEGORY_PICKUP_EXPIRED: 'card-rental',
        CATEGORY_RETURN_24H: 'card-rental',
        CATEGORY_RETURN_3H: 'card-rental',
    }

    # Label dan warna badge untuk setiap jenis notifikasi.
    __BADGE_STYLE = {
        CATEGORY_STATUS: ('Status Pesanan', 'info'),
        CATEGORY_REMINDER: ('Pengingat', 'warning'),
        CATEGORY_OVERDUE: ('Denda', 'danger'),
        CATEGORY_FINE: ('Denda', 'danger'),
        CATEGORY_PAYMENT_1H: ('Pengingat Pembayaran', 'warning'),
        CATEGORY_PAYMENT_30M: ('Segera Bayar', 'warning'),
        CATEGORY_PAYMENT_CANCELLED: ('Dibatalkan', 'danger'),
        CATEGORY_PICKUP_EXPIRED: ('Dibatalkan', 'danger'),
        CATEGORY_RETURN_24H: ('Pengingat Pengembalian', 'info'),
        CATEGORY_RETURN_3H: ('Segera Dikembalikan', 'warning'),
    }


    # ═════════════════════════════════════════════════════════════════════════
    #                    [METHOD NOTIFIKASI]
    # ═════════════════════════════════════════════════════════════════════════
    @property
    def is_manual_cancellation(self):
        # Memeriksa notifikasi pembatalan yang dilakukan user atau admin.
        return (
            self.category == self.CATEGORY_STATUS
            and self.new_status == Rental.STATUS_BATAL
        )


    @property
    def icon(self):
        # Pembatalan menggunakan ikon larangan.
        if self.is_manual_cancellation:
            return 'fa-solid fa-ban'

        return self.__STYLE.get(
            self.category,
            self.__STYLE[self.CATEGORY_STATUS]
        )[0]

    @property
    def tone(self):
        # Pembatalan menggunakan warna peringatan.
        if self.is_manual_cancellation:
            return 'tone-danger'

        return self.__STYLE.get(
            self.category,
            self.__STYLE[self.CATEGORY_STATUS]
        )[1]


    @property
    def card_tone(self):
        # Mengambil class kartu sesuai jenis notifikasi.
        if self.is_manual_cancellation:
            return 'card-rental'

        return self.__CARD_STYLE.get(
            self.category,
            self.__CARD_STYLE[self.CATEGORY_STATUS]
        )


    @property
    def badge_label(self):
        # Mengambil teks badge yang sesuai.
        if self.is_manual_cancellation:
            return 'Dibatalkan'

        return self.__BADGE_STYLE.get(
            self.category,
            self.__BADGE_STYLE[self.CATEGORY_STATUS]
        )[0]


    @property
    def badge_tone(self):
        # Mengambil warna badge yang sesuai.
        if self.is_manual_cancellation:
            return 'danger'

        return self.__BADGE_STYLE.get(
            self.category,
            self.__BADGE_STYLE[self.CATEGORY_STATUS]
        )[1]

    @staticmethod
    def _rp(n):
        # Mengubah angka menjadi format rupiah.
        return 'Rp{:,.0f}'.format(n).replace(',', '.')


    @classmethod
    def status_changed(cls, rental, old_status, cancelled_by=None):
         # Membuat pesan khusus jika pesanan dibatalkan oleh user atau admin.
        if (
            rental.status == Rental.STATUS_BATAL
            and cancelled_by in ('user', 'admin')
        ):
            alasan = (
                rental.cancellation_reason or 'Tidak dicantumkan'
            ).strip()

            title = (
                f'Pesanan Dibatalkan oleh {cancelled_by.title()}'
            )

            message = (
                f'Pesanan {rental.booking_code} dibatalkan '
                f'oleh {cancelled_by} dengan alasan {alasan}. '
                'Untuk pengembalian dana, silakan hubungi admin '
                'melalui halaman detail pesanan.'
            )
        else:
            # Pesan umum untuk perubahan status pesanan.
            title = 'Status Pesanan Diperbarui'
            message = (
                f'Status pesanan {rental.booking_code} berubah dari '
                f'"{old_status}" menjadi "{rental.status}".'
            )

            if rental.status == Rental.STATUS_BATAL and rental.cancellation_reason:
                message += f' Alasan: {rental.cancellation_reason}'

        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=cls.CATEGORY_STATUS,
            title=title,
            message=message,
            old_status=old_status,
            new_status=rental.status,
        )


    @classmethod
    def overdue_warning(cls, rental):
        # Membuat notifikasi ketika kendaraan terlambat dikembalikan,
        # termasuk informasi jumlah hari keterlambatan dan total denda.
        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=cls.CATEGORY_OVERDUE,
            title='Pengembalian Kendaraan Terlambat',
            message=(
                f'Pesanan {rental.booking_code} telah melewati '
                f'batas waktu pengembalian. '
                f'Keterlambatan: {rental.late_days} hari. '
                f'Total denda saat ini: {cls._rp(rental.active_fine)}.'
            ),
            old_status=rental.status,
            new_status=rental.status,
        )

    @classmethod
    def return_reminder(cls, rental):
        # Membuat notifikasi pengingat pengembalian kendaraan
        # berdasarkan sisa waktu yang tersedia sebelum batas pengembalian.
        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=cls.CATEGORY_REMINDER,
            title='Pengingat Pengembalian Kendaraan',
            message=(
                f'Pesanan {rental.booking_code} akan segera '
                f'mencapai batas waktu pengembalian. '
                f'Sisa waktu: {rental.remaining_label}.'
            ),
            old_status=rental.status,
            new_status=rental.status,
        )

    @classmethod
    def payment_reminder(cls, rental, category):
        # Membuat notifikasi pengingat pembayaran berdasarkan kategori
        # waktu yang diberikan, yaitu 1 jam atau 30 menit sebelum batas.
        if category == cls.CATEGORY_PAYMENT_1H:
            title = 'Pengingat Pembayaran'
            waktu = '1 jam'
        elif category == cls.CATEGORY_PAYMENT_30M:
            title = 'Segera Lakukan Pembayaran'
            waktu = '30 menit'
        else:
            raise ValueError('Kategori pengingat pembayaran tidak valid.')

        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=category,
            title=title,
            message=(
                f'Pembayaran pesanan {rental.booking_code} '
                f'belum diselesaikan. Silakan lakukan pembayaran '
                f'dalam waktu {waktu} agar pesanan tidak dibatalkan.'
            ),
            old_status=rental.status,
            new_status=rental.status,
        )

    @classmethod
    def return_deadline_reminder(cls, rental, category):
        # Membuat notifikasi pengingat batas waktu pengembalian
        # sesuai kategori, yaitu 24 jam atau 3 jam sebelum tenggat.
        if category == cls.CATEGORY_RETURN_24H:
            title = 'Pengingat Pengembalian Kendaraan'
            waktu = '24 jam'
        elif category == cls.CATEGORY_RETURN_3H:
            title = 'Segera Kembalikan Kendaraan'
            waktu = '3 jam'
        else:
            raise ValueError('Kategori pengingat pengembalian tidak valid.')

        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=category,
            title=title,
            message=(
                f'Pesanan {rental.booking_code} mendekati '
                f'batas waktu pengembalian. Pastikan kendaraan '
                f'dikembalikan dalam batas waktu yang tersisa, '
                f'yaitu sekitar {waktu}.'
            ),
            old_status=rental.status,
            new_status=rental.status,
        )



# ═════════════════════════════════════════════════════════════
#   K.   |   FITUR PROFIL AKUN
# ═════════════════════════════════════════════════════════════
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
# ═════════════════════════════════════════════════════════════

# Fitur profil ini digunakan bersama oleh Customer dan Admin.
class ProfileMixin:

    # Mengambil lokasi foto profil jika tersedia.
    @property
    def avatar_path(self):
        if self.profile_photo:
            return f"uploads/profil/{self.profile_photo}"
        return None

    # Mencari dokumen akun, lalu memeriksa pesanan jika belum ditemukan.
    def _document(self, label, attr):
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
        # Menampilkan dokumen KTP dan SIM beserta lokasi filenya.
        return [
            self._document('KTP', 'ktp_file'),
            self._document('SIM', 'sim_file')
        ]



# ═════════════════════════════════════════════════════════════
#   L.   |   CUSTOMER MODEL
# ═════════════════════════════════════════════════════════════

# Customer mewarisi User dan menggunakan fitur profil dari ProfileMixin.
class Customer(ProfileMixin, User):
    

    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT CUSTOMER]
    # ═════════════════════════════════════════════════════════════════════════
    ROLE            = 'user'
    CODE_PREFIX     = 'PLG'
    __mapper_args__ = {'polymorphic_identity': ROLE}


    # ═════════════════════════════════════════════════════════════════════════
    #                           [METHOD CUSTOMER]
    # ═════════════════════════════════════════════════════════════════════════
    @property
    def code(self):
        # Kode akun pelanggan tetap tersedia untuk route dan template.
        return self.get_code()

    # POLIMORFISME:
    # Customer menggunakan awalan PLG untuk kode akunnya.
    def get_code(self):
        return f"{self.CODE_PREFIX}{self.id:03d}"

    @property
    def rental_history(self):
        # Mengambil seluruh pesanan pelanggan dari yang terbaru.
        return (Rental.query
                .filter_by(user_id=self.id)
                .order_by(Rental.created_at.desc())
                .all())



# ═════════════════════════════════════════════════════════════
#   M.   |   ADMIN MODEL
# ═════════════════════════════════════════════════════════════

# Admin mewarisi User dan memiliki fitur profil yang sama dengan Customer
class Admin(ProfileMixin, User):
    

    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT ADMIN]
    # ═════════════════════════════════════════════════════════════════════════
    ROLE            = 'admin'
    CODE_PREFIX     = 'ADM'
    is_super_admin  = False
    __mapper_args__ = {'polymorphic_identity': ROLE}


    # ═════════════════════════════════════════════════════════════════════════
    #                           [METHOD CUSTOMER]
    # ═════════════════════════════════════════════════════════════════════════
    @property
    def code(self):
        # Kode akun admin tetap bisa digunakan oleh route dan template.
        return self.get_code()

    # POLIMORFISME:
    # Admin menggunakan awalan ADM untuk kode akunnya.
    def get_code(self):
        return f"{self.CODE_PREFIX}{self.id:03d}"



# ═════════════════════════════════════════════════════════════
#   N.   |   SUPERADMIN MODEL
# ═════════════════════════════════════════════════════════════

# SuperAdmin mewarisi Admin dan memiliki penanda hak akses tertinggi.
class SuperAdmin(Admin):


    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT SUPERADMIN]
    # ═════════════════════════════════════════════════════════════════════════
    ROLE            = 'superadmin'
    CODE_PREFIX     = 'SA'
    is_super_admin  = True
    __mapper_args__ = {'polymorphic_identity': ROLE}


    # ═════════════════════════════════════════════════════════════════════════
    #                           [METHOD SUPERADMIN]
    # ═════════════════════════════════════════════════════════════════════════
    # POLIMORFISME:
    # SuperAdmin mengubah hasil get_code() agar memakai awalan SA.
    def get_code(self):
        return f"{self.CODE_PREFIX}{self.id:03d}"