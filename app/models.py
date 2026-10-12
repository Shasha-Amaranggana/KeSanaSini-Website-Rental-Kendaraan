from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta


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

    # Relasi antar objek (OOP)
    user = db.relationship('User', backref=db.backref('rentals', lazy=True))
    vehicle = db.relationship('Vehicle', backref=db.backref('rentals', lazy=True))
    driver = db.relationship('Driver', backref=db.backref('rentals', lazy=True))

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

    user = db.relationship(
        'User',
        backref=db.backref('notifications', lazy=True)
    )

    rental = db.relationship(
        'Rental',
        backref=db.backref('notifications', lazy=True)
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
