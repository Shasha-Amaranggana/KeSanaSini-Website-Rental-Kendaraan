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
from sqlalchemy.orm import synonym

# Catatan enkapsulasi: kolom dipetakan ke penyimpanan internal; getter/setter dan
# synonym mempertahankan API publik agar query SQLAlchemy dan route lama tetap kompatibel.
# Penyimpanan protected dipakai untuk data bersama pada pewarisan/akses antarmodel.
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
# [OOP - ABSTRAKSI]: class abstrak (ABC) dengan @abstractmethod yang mendefinisikan kontrak perhitungan harga.
class AbstractRentalPricing(ABC):

    @abstractmethod
    def calculate_total(self, rental):
        # Setiap class turunannya harus menyediakan cara menghitung total.
        raise NotImplementedError


# Menghitung total biaya berdasarkan aturan harga yang digunakan website.
# [OOP - PEWARISAN & OVERRIDING]: mewarisi AbstractRentalPricing dan mengimplementasikan calculate_total().
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


    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA DIRI USER]
    # ──────────────────────────────────────────────────────────────────────────

    _id              = db.Column("id", db.Integer, primary_key=True)
    # Getter dan setter untuk atribut privat id.
    def get_id(self):
        return self._id
    def set_id(self, value):
        self._id = value
    id = synonym("_id", descriptor=property(get_id, set_id))

    _name            = db.Column("name", db.String(100), nullable=False)
    # Getter dan setter untuk atribut privat name.
    def get_name(self):
        return self._name
    def set_name(self, value):
        self._name = value
    name = synonym("_name", descriptor=property(get_name, set_name))

    _birth_date      = db.Column("birth_date", db.Date, nullable=False)
    # Getter dan setter untuk atribut privat birth_date.
    def get_birth_date(self):
        return self._birth_date
    def set_birth_date(self, value):
        self._birth_date = value
    birth_date = synonym("_birth_date", descriptor=property(get_birth_date, set_birth_date))

    _gender          = db.Column("gender", db.String(20), nullable=False)
    # Getter dan setter untuk atribut privat gender.
    def get_gender(self):
        return self._gender
    def set_gender(self, value):
        self._gender = value
    gender = synonym("_gender", descriptor=property(get_gender, set_gender))

    _email           = db.Column("email", db.String(120), unique=True, nullable=False)
    # Getter dan setter untuk atribut privat email.
    def get_email(self):
        return self._email
    def set_email(self, value):
        self._email = value
    email = synonym("_email", descriptor=property(get_email, set_email))

    _phone           = db.Column("phone", db.String(20), nullable=False)
    # Getter dan setter untuk atribut privat phone.
    def get_phone(self):
        return self._phone
    def set_phone(self, value):
        self._phone = value
    phone = synonym("_phone", descriptor=property(get_phone, set_phone))

    _emergency_phone = db.Column("emergency_phone", db.String(20), nullable=False)
    # Getter dan setter untuk atribut privat emergency_phone.
    def get_emergency_phone(self):
        return self._emergency_phone
    def set_emergency_phone(self, value):
        self._emergency_phone = value
    emergency_phone = synonym("_emergency_phone", descriptor=property(get_emergency_phone, set_emergency_phone))

    __password_hash   = db.Column("password_hash", db.String(128), nullable=False)
    # Getter dan setter untuk atribut privat password_hash.
    def get_password_hash(self):
        return self.__password_hash
    def set_password_hash(self, value):
        self.__password_hash = value
    password_hash = synonym("_User__password_hash", descriptor=property(get_password_hash, set_password_hash))

    __ktp_file        = db.Column("ktp_file", db.String(255), nullable=True)
    # Getter dan setter untuk atribut privat ktp_file.
    def get_ktp_file(self):
        return self.__ktp_file
    def set_ktp_file(self, value):
        self.__ktp_file = value
    ktp_file = synonym("_User__ktp_file", descriptor=property(get_ktp_file, set_ktp_file))

    __sim_file        = db.Column("sim_file", db.String(255), nullable=True)
    # Getter dan setter untuk atribut privat sim_file.
    def get_sim_file(self):
        return self.__sim_file
    def set_sim_file(self, value):
        self.__sim_file = value
    sim_file = synonym("_User__sim_file", descriptor=property(get_sim_file, set_sim_file))


    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA DIRI - Membedakan "ADMIN" & "USER" & "SUPERADMIN"]
    # ──────────────────────────────────────────────────────────────────────────

    __role            = db.Column("role", db.String(20), nullable=False, default='user')
    # Getter dan setter untuk atribut privat role.
    def get_role(self):
        return self.__role
    def set_role(self, value):
        self.__role = value
    role = synonym("_User__role", descriptor=property(get_role, set_role))


    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA TAMBAHAN - Fitur kelola pelanggan dan admin]
    # ──────────────────────────────────────────────────────────────────────────

    _is_active       = db.Column("is_active", db.Boolean, nullable=False, default=True)
    # Getter dan setter untuk atribut privat is_active.
    def get_is_active(self):
        return self._is_active
    def set_is_active(self, value):
        self._is_active = value
    is_active = synonym("_is_active", descriptor=property(get_is_active, set_is_active))

    _profile_photo   = db.Column("profile_photo", db.String(255), nullable=True)
    # Getter dan setter untuk atribut privat profile_photo.
    def get_profile_photo(self):
        return self._profile_photo
    def set_profile_photo(self, value):
        self._profile_photo = value
    profile_photo = synonym("_profile_photo", descriptor=property(get_profile_photo, set_profile_photo))

    __ktp_number      = db.Column("ktp_number", db.String(20), nullable=True)
    # Getter dan setter untuk atribut privat ktp_number.
    def get_ktp_number(self):
        return self.__ktp_number
    def set_ktp_number(self, value):
        self.__ktp_number = value
    ktp_number = synonym("_User__ktp_number", descriptor=property(get_ktp_number, set_ktp_number))

    __sim_number      = db.Column("sim_number", db.String(20), nullable=True)
    # Getter dan setter untuk atribut privat sim_number.
    def get_sim_number(self):
        return self.__sim_number
    def set_sim_number(self, value):
        self.__sim_number = value
    sim_number = synonym("_User__sim_number", descriptor=property(get_sim_number, set_sim_number))

    # SQLAlchemy menggunakan kolom role untuk menentukan jenis kelas objek User saat data dibaca dari database.
    __mapper_args__ = {'polymorphic_on': '_User__role'}         


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
    

    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA VEHICLE]
    # ──────────────────────────────────────────────────────────────────────────

    __id              = db.Column("id", db.Integer, primary_key =True)
    # Getter dan setter untuk atribut privat id.
    def get_id(self):
        return self.__id
    def set_id(self, value):
        self.__id = value
    id = synonym("_Vehicle__id", descriptor=property(get_id, set_id))

    __photo           = db.Column("photo", db.String(255), nullable=False)
    # Getter dan setter untuk atribut privat photo.
    def get_photo(self):
        return self.__photo
    def set_photo(self, value):
        self.__photo = value
    photo = synonym("_Vehicle__photo", descriptor=property(get_photo, set_photo))
    
    __brand           = db.Column("brand", db.String(50), nullable =False)
    # Getter dan setter untuk atribut privat brand.
    def get_brand(self):
        return self.__brand
    def set_brand(self, value):
        self.__brand = value
    brand = synonym("_Vehicle__brand", descriptor=property(get_brand, set_brand))
    
    __model           = db.Column("model", db.String(100), nullable=False)
    # Getter dan setter untuk atribut privat model.
    def get_model(self):
        return self.__model
    def set_model(self, value):
        self.__model = value
    model = synonym("_Vehicle__model", descriptor=property(get_model, set_model))
    
    __gallery         = db.Column("gallery", db.Text, nullable=True)  
    # Getter dan setter untuk atribut privat gallery.
    def get_gallery(self):
        return self.__gallery
    def set_gallery(self, value):
        self.__gallery = value
    gallery = synonym("_Vehicle__gallery", descriptor=property(get_gallery, set_gallery))
    
    __vehicle_number  = db.Column("vehicle_number", db.String(20), unique=True, nullable=False)
    # Getter dan setter untuk atribut privat vehicle_number.
    def get_vehicle_number(self):
        return self.__vehicle_number
    def set_vehicle_number(self, value):
        self.__vehicle_number = value
    vehicle_number = synonym("_Vehicle__vehicle_number", descriptor=property(get_vehicle_number, set_vehicle_number))
    
    __year            = db.Column("year", db.Integer, nullable=False)
    # Getter dan setter untuk atribut privat year.
    def get_year(self):
        return self.__year
    def set_year(self, value):
        self.__year = value
    year = synonym("_Vehicle__year", descriptor=property(get_year, set_year))
    
    __vehicle_type    = db.Column("vehicle_type", db.String(20), nullable=False)
    # Getter dan setter untuk atribut privat vehicle_type.
    def get_vehicle_type(self):
        return self.__vehicle_type
    def set_vehicle_type(self, value):
        self.__vehicle_type = value
    vehicle_type = synonym("_Vehicle__vehicle_type", descriptor=property(get_vehicle_type, set_vehicle_type))
    
    __seats           = db.Column("seats", db.Integer, nullable    =False)
    # Getter dan setter untuk atribut privat seats.
    def get_seats(self):
        return self.__seats
    def set_seats(self, value):
        self.__seats = value
    seats = synonym("_Vehicle__seats", descriptor=property(get_seats, set_seats))
    
    __luggage         = db.Column("luggage", db.Integer, nullable    =False, default     =0)
    # Getter dan setter untuk atribut privat luggage.
    def get_luggage(self):
        return self.__luggage
    def set_luggage(self, value):
        self.__luggage = value
    luggage = synonym("_Vehicle__luggage", descriptor=property(get_luggage, set_luggage))
    
    __price_per_day   = db.Column("price_per_day", db.Integer, nullable=False)
    # Getter dan setter untuk atribut privat price_per_day.
    def get_price_per_day(self):
        return self.__price_per_day
    def set_price_per_day(self, value):
        self.__price_per_day = value
    price_per_day = synonym("_Vehicle__price_per_day", descriptor=property(get_price_per_day, set_price_per_day))
    
    __rental_type     = db.Column("rental_type", db.String(30), nullable=False)
    # Getter dan setter untuk atribut privat rental_type.
    def get_rental_type(self):
        return self.__rental_type
    def set_rental_type(self, value):
        self.__rental_type = value
    rental_type = synonym("_Vehicle__rental_type", descriptor=property(get_rental_type, set_rental_type))
    
    
    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA TAMBAHAN - Fitur kelola kendaraan]
    # ──────────────────────────────────────────────────────────────────────────

    __color           = db.Column("color", db.String(30), nullable=True)
    # Getter dan setter untuk atribut privat color.
    def get_color(self):
        return self.__color
    def set_color(self, value):
        self.__color = value
    color = synonym("_Vehicle__color", descriptor=property(get_color, set_color))
    
    __chassis_number  = db.Column("chassis_number", db.String(50), unique=True, nullable=True)
    # Getter dan setter untuk atribut privat chassis_number.
    def get_chassis_number(self):
        return self.__chassis_number
    def set_chassis_number(self, value):
        self.__chassis_number = value
    chassis_number = synonym("_Vehicle__chassis_number", descriptor=property(get_chassis_number, set_chassis_number))
    
    __engine_number   = db.Column("engine_number", db.String(50), unique=True, nullable=True)
    # Getter dan setter untuk atribut privat engine_number.
    def get_engine_number(self):
        return self.__engine_number
    def set_engine_number(self, value):
        self.__engine_number = value
    engine_number = synonym("_Vehicle__engine_number", descriptor=property(get_engine_number, set_engine_number))
    
    __fuel            = db.Column("fuel", db.String(20), nullable=True, default='Bensin')
    # Getter dan setter untuk atribut privat fuel.
    def get_fuel(self):
        return self.__fuel
    def set_fuel(self, value):
        self.__fuel = value
    fuel = synonym("_Vehicle__fuel", descriptor=property(get_fuel, set_fuel))
    
    __transmission    = db.Column("transmission", db.String(20), nullable=True, default='Manual')
    # Getter dan setter untuk atribut privat transmission.
    def get_transmission(self):
        return self.__transmission
    def set_transmission(self, value):
        self.__transmission = value
    transmission = synonym("_Vehicle__transmission", descriptor=property(get_transmission, set_transmission))
    
    __engine_cc       = db.Column("engine_cc", db.Integer, nullable=True)
    # Getter dan setter untuk atribut privat engine_cc.
    def get_engine_cc(self):
        return self.__engine_cc
    def set_engine_cc(self, value):
        self.__engine_cc = value
    engine_cc = synonym("_Vehicle__engine_cc", descriptor=property(get_engine_cc, set_engine_cc))
    
    __facilities      = db.Column("facilities", db.Text, nullable=True)   
    # Getter dan setter untuk atribut privat facilities.
    def get_facilities(self):
        return self.__facilities
    def set_facilities(self, value):
        self.__facilities = value
    facilities = synonym("_Vehicle__facilities", descriptor=property(get_facilities, set_facilities))
    
    __notes           = db.Column("notes", db.Text, nullable=True)
    # Getter dan setter untuk atribut privat notes.
    def get_notes(self):
        return self.__notes
    def set_notes(self, value):
        self.__notes = value
    notes = synonym("_Vehicle__notes", descriptor=property(get_notes, set_notes))
    
    __is_active       = db.Column("is_active", db.Boolean, nullable=False, default=True)
    # Getter dan setter untuk atribut privat is_active.
    def get_is_active(self):
        return self.__is_active
    def set_is_active(self, value):
        self.__is_active = value
    is_active = synonym("_Vehicle__is_active", descriptor=property(get_is_active, set_is_active))
    
    # Koordinat kendaraan saat fitur tracking digunakan.
    _current_lat     = db.Column("current_lat", db.Float, nullable=True)
    # Getter dan setter untuk atribut privat current_lat.
    def get_current_lat(self):
        return self._current_lat
    def set_current_lat(self, value):
        self._current_lat = value
    current_lat = synonym("_current_lat", descriptor=property(get_current_lat, set_current_lat))
    
    _current_lng     = db.Column("current_lng", db.Float, nullable=True)
    # Getter dan setter untuk atribut privat current_lng.
    def get_current_lng(self):
        return self._current_lng
    def set_current_lng(self, value):
        self._current_lng = value
    current_lng = synonym("_current_lng", descriptor=property(get_current_lng, set_current_lng))



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

# [OOP - PEWARISAN / INHERITANCE]:
#   Driver mewarisi db.Model sehingga dapat dipetakan ke tabel sopir.
# [OOP - ENKAPSULASI / ENCAPSULATION]:
#   Atribut disimpan sebagai atribut privat (diawali __) dan diakses lewat
#   getter/setter serta @property, sehingga data sopir tidak diubah langsung dari luar class.
# [OOP - ABSTRAKSI / ABSTRACTION]:
#   Cara menentukan status sopir (Tersedia / Menunggu Konfirmasi / Berjalan)
#   disembunyikan di property status_label. Route dan template cukup memanggil d.status_label.
# [OOP - ASOSIASI OBJEK]:
#   Driver terhubung dengan Rental lewat relasi (driver.rentals dan rental.driver).
class Driver(db.Model):
    

    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT DRIVER]
    # ═════════════════════════════════════════════════════════════════════════


    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA DRIVER]
    # ──────────────────────────────────────────────────────────────────────────

    __id              = db.Column("id", db.Integer, primary_key=True)
    # Getter dan setter untuk atribut privat id.
    def get_id(self):
        return self.__id
    def set_id(self, value):
        self.__id = value
    id = synonym("_Driver__id", descriptor=property(get_id, set_id))

    __name            = db.Column("name", db.String(100), nullable=False)
    # Getter dan setter untuk atribut privat name.
    def get_name(self):
        return self.__name
    def set_name(self, value):
        self.__name = value
    name = synonym("_Driver__name", descriptor=property(get_name, set_name))
    
    __phone           = db.Column("phone", db.String(20), nullable=False)
    # Getter dan setter untuk atribut privat phone.
    def get_phone(self):
        return self.__phone
    def set_phone(self, value):
        self.__phone = value
    phone = synonym("_Driver__phone", descriptor=property(get_phone, set_phone))
    
    __is_available    = db.Column("is_available", db.Boolean, nullable=False, default=True)
    # Getter dan setter untuk atribut privat is_available.
    def get_is_available(self):
        return self.__is_available
    def set_is_available(self, value):
        self.__is_available = value
    is_available = synonym("_Driver__is_available", descriptor=property(get_is_available, set_is_available))
    
    __photo           = db.Column("photo", db.String(255), nullable=True, default='default_driver.png')
    # Getter dan setter untuk atribut privat photo.
    def get_photo(self):
        return self.__photo
    def set_photo(self, value):
        self.__photo = value
    photo = synonym("_Driver__photo", descriptor=property(get_photo, set_photo))
    
    __created_at      = db.Column("created_at", db.DateTime, nullable=False, default=datetime.now)
    # Getter dan setter untuk atribut privat created_at.
    def get_created_at(self):
        return self.__created_at
    def set_created_at(self, value):
        self.__created_at = value
    created_at = synonym("_Driver__created_at", descriptor=property(get_created_at, set_created_at))


    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA TAMBAHAN - Fitur kelola sopir]
    # ──────────────────────────────────────────────────────────────────────────

    __address         = db.Column("address", db.String(255), nullable=True)
    # Getter dan setter untuk atribut privat address.
    def get_address(self):
        return self.__address
    def set_address(self, value):
        self.__address = value
    address = synonym("_Driver__address", descriptor=property(get_address, set_address))

    __description     = db.Column("description", db.Text, nullable=True)
    # Getter dan setter untuk atribut privat description.
    def get_description(self):
        return self.__description
    def set_description(self, value):
        self.__description = value
    description = synonym("_Driver__description", descriptor=property(get_description, set_description))
    
    __sim_photo       = db.Column("sim_photo", db.String(255), nullable=True)
    # Getter dan setter untuk atribut privat sim_photo.
    def get_sim_photo(self):
        return self.__sim_photo
    def set_sim_photo(self, value):
        self.__sim_photo = value
    sim_photo = synonym("_Driver__sim_photo", descriptor=property(get_sim_photo, set_sim_photo))



    # ═════════════════════════════════════════════════════════════════════════
    #                           [METHOD DRIVER]
    # ═════════════════════════════════════════════════════════════════════════

    @property
    def code(self):
        # Membuat kode sopir dari ID-nya.
        return f"SP{self.id:03d}"

# [OOP - ENKAPSULASI]: query penyewaan aktif dibungkus di dalam objek sopir.
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

# [OOP - ABSTRAKSI]: menyembunyikan aturan penentuan status dari pemanggil.
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

# [OOP - ENKAPSULASI]: agregasi rating dihitung di dalam class.
    @property
    def avg_rating(self):
        # Menghitung rata-rata ulasan dari kendaraan pada pesanan yang selesai.
        pasangan = {(r.user_id, r.vehicle_id) for r in self.rentals
                    if r.status == Rental.STATUS_SELESAI}
        nilai = [rv.rating for (u, v) in pasangan
                 for rv in Review.query.filter_by(user_id=u, vehicle_id=v)]
        return round(sum(nilai) / len(nilai), 2) if nilai else 0

# [OOP - ENKAPSULASI]: agregasi rating dihitung di dalam class.
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
    

    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [STATUS PESANAN]
    # ──────────────────────────────────────────────────────────────────────────

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
        'kursi_bayi'    :  ('Kursi Bayi (Baby Car Seat)', 15000),
        'phone_holder'  :  ('Phone holder', 5000),
        'bantal'        :  ('Bantal', 5000),
        'selimut'       :  ('Selimut', 10000),
        'helm_tambahan' :  ('Helm tambahan', 10000),
        'jas_hujan'     :  ('Jas hujan', 5000),
        'box_belakang'  :  ('Box belakang', 15000),
    }

    # Menentukan jenis kendaraan yang bisa menggunakan setiap aksesori.
    ACCESSORY_TYPES = {
        'kursi_bayi'    :   ['mobil'],
        'phone_holder'  :   ['mobil', 'motor'],
        'bantal'        :   ['mobil'],
        'selimut'       :   ['mobil'],
        'helm_tambahan' :   ['motor'],
        'jas_hujan'     :   ['motor'],
        'box_belakang'  :   ['motor'],
    }

    # Pilihan asuransi beserta biayanya.
    INSURANCES = {                          
        'dasar'     :   ('Dasar', 0),
        'lengkap'   :   ('Lengkap', 50000),
    }


    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA PESANAN]
    # ──────────────────────────────────────────────────────────────────────────

    __id                  = db.Column("id", db.Integer, primary_key=True)
    # Getter dan setter untuk atribut privat id.
    def get_id(self):
        return self.__id
    def set_id(self, value):
        self.__id = value
    id = synonym("_Rental__id", descriptor=property(get_id, set_id))
    
    __booking_code        = db.Column("booking_code", db.String(20), unique=True, nullable=False)
    # Getter dan setter untuk atribut privat booking_code.
    def get_booking_code(self):
        return self.__booking_code
    def set_booking_code(self, value):
        self.__booking_code = value
    booking_code = synonym("_Rental__booking_code", descriptor=property(get_booking_code, set_booking_code))

    __user_id             = db.Column("user_id", db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Getter dan setter untuk atribut privat user_id.
    def get_user_id(self):
        return self.__user_id
    def set_user_id(self, value):
        self.__user_id = value
    user_id = synonym("_Rental__user_id", descriptor=property(get_user_id, set_user_id))
    
    __vehicle_id          = db.Column("vehicle_id", db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    # Getter dan setter untuk atribut privat vehicle_id.
    def get_vehicle_id(self):
        return self.__vehicle_id
    def set_vehicle_id(self, value):
        self.__vehicle_id = value
    vehicle_id = synonym("_Rental__vehicle_id", descriptor=property(get_vehicle_id, set_vehicle_id))
    
    __driver_id           = db.Column("driver_id", db.Integer, db.ForeignKey('driver.id'), nullable=True) # Tambahan Relasi Sopir
    # Getter dan setter untuk atribut privat driver_id.
    def get_driver_id(self):
        return self.__driver_id
    def set_driver_id(self, value):
        self.__driver_id = value
    driver_id = synonym("_Rental__driver_id", descriptor=property(get_driver_id, set_driver_id))

    __start_date          = db.Column("start_date", db.Date, nullable=False)
    # Getter dan setter untuk atribut privat start_date.
    def get_start_date(self):
        return self.__start_date
    def set_start_date(self, value):
        self.__start_date = value
    start_date = synonym("_Rental__start_date", descriptor=property(get_start_date, set_start_date))
    
    __end_date            = db.Column("end_date", db.Date, nullable=False)
    # Getter dan setter untuk atribut privat end_date.
    def get_end_date(self):
        return self.__end_date
    def set_end_date(self, value):
        self.__end_date = value
    end_date = synonym("_Rental__end_date", descriptor=property(get_end_date, set_end_date))


    # Tanggal dan jam disimpan terpisah.

    __pickup_time         = db.Column("pickup_time", db.String(5), nullable=False, default='10:00')
    # Getter dan setter untuk atribut privat pickup_time.
    def get_pickup_time(self):
        return self.__pickup_time
    def set_pickup_time(self, value):
        self.__pickup_time = value
    pickup_time = synonym("_Rental__pickup_time", descriptor=property(get_pickup_time, set_pickup_time))
    
    __return_time         = db.Column("return_time", db.String(5), nullable=False, default='10:00')
    # Getter dan setter untuk atribut privat return_time.
    def get_return_time(self):
        return self.__return_time
    def set_return_time(self, value):
        self.__return_time = value
    return_time = synonym("_Rental__return_time", descriptor=property(get_return_time, set_return_time))

    
    __status              = db.Column("status", db.String(50), nullable=False, default=STATUS_MENUNGGU_BAYAR)
    # Getter dan setter untuk atribut privat status.
    def get_status(self):
        return self.__status
    def set_status(self, value):
        self.__status = value
    status = synonym("_Rental__status", descriptor=property(get_status, set_status))
    
    __created_at          = db.Column("created_at", db.DateTime, nullable=False, default=datetime.now)
    # Getter dan setter untuk atribut privat created_at.
    def get_created_at(self):
        return self.__created_at
    def set_created_at(self, value):
        self.__created_at = value
    created_at = synonym("_Rental__created_at", descriptor=property(get_created_at, set_created_at))


    # Informasi pembayaran dan pembatalan.


# [OOP - ENKAPSULASI]: data pembayaran bersifat privat dan hanya diakses lewat getter/setter.
    __payment_method      = db.Column("payment_method", db.String(50), nullable=True)
    # Getter dan setter untuk atribut privat payment_method.
    def get_payment_method(self):
        return self.__payment_method
    def set_payment_method(self, value):
        self.__payment_method = value
    payment_method = synonym("_Rental__payment_method", descriptor=property(get_payment_method, set_payment_method))

# [OOP - ENKAPSULASI]: data pembayaran bersifat privat dan hanya diakses lewat getter/setter.
    __payment_status      = db.Column("payment_status", db.String(20), nullable=False, default='Belum Lunas') # 'Lunas' / 'Belum Lunas'
    # Getter dan setter untuk atribut privat payment_status.
    def get_payment_status(self):
        return self.__payment_status
    def set_payment_status(self, value):
        self.__payment_status = value
    payment_status = synonym("_Rental__payment_status", descriptor=property(get_payment_status, set_payment_status))
    
    __cancellation_reason = db.Column("cancellation_reason", db.String(500), nullable=True)
    # Getter dan setter untuk atribut privat cancellation_reason.
    def get_cancellation_reason(self):
        return self.__cancellation_reason
    def set_cancellation_reason(self, value):
        self.__cancellation_reason = value
    cancellation_reason = synonym("_Rental__cancellation_reason", descriptor=property(get_cancellation_reason, set_cancellation_reason))

    
    # Pilihan layanan tambahan saat menyewa.

    __with_driver         = db.Column("with_driver", db.Boolean, nullable=False, default=False)
    # Getter dan setter untuk atribut privat with_driver.
    def get_with_driver(self):
        return self.__with_driver
    def set_with_driver(self, value):
        self.__with_driver = value
    with_driver = synonym("_Rental__with_driver", descriptor=property(get_with_driver, set_with_driver))
    
    __accessories         = db.Column("accessories", db.String(200), nullable=True, default='')  
    # Getter dan setter untuk atribut privat accessories.
    def get_accessories(self):
        return self.__accessories
    def set_accessories(self, value):
        self.__accessories = value
    accessories = synonym("_Rental__accessories", descriptor=property(get_accessories, set_accessories))
    
    __insurance           = db.Column("insurance", db.String(20), nullable=False, default='dasar')
    # Getter dan setter untuk atribut privat insurance.
    def get_insurance(self):
        return self.__insurance
    def set_insurance(self, value):
        self.__insurance = value
    insurance = synonym("_Rental__insurance", descriptor=property(get_insurance, set_insurance))
    
    __purpose             = db.Column("purpose", db.String(50), nullable=True)
    # Getter dan setter untuk atribut privat purpose.
    def get_purpose(self):
        return self.__purpose
    def set_purpose(self, value):
        self.__purpose = value
    purpose = synonym("_Rental__purpose", descriptor=property(get_purpose, set_purpose))
    
    __region              = db.Column("region", db.String(30), nullable=True)
    # Getter dan setter untuk atribut privat region.
    def get_region(self):
        return self.__region
    def set_region(self, value):
        self.__region = value
    region = synonym("_Rental__region", descriptor=property(get_region, set_region))
    
    __destination_city    = db.Column("destination_city", db.String(100), nullable=True)
    # Getter dan setter untuk atribut privat destination_city.
    def get_destination_city(self):
        return self.__destination_city
    def set_destination_city(self, value):
        self.__destination_city = value
    destination_city = synonym("_Rental__destination_city", descriptor=property(get_destination_city, set_destination_city))
    
    __pickup_location     = db.Column("pickup_location", db.String(100), nullable=True)
    # Getter dan setter untuk atribut privat pickup_location.
    def get_pickup_location(self):
        return self.__pickup_location
    def set_pickup_location(self, value):
        self.__pickup_location = value
    pickup_location = synonym("_Rental__pickup_location", descriptor=property(get_pickup_location, set_pickup_location))
    
    __return_location     = db.Column("return_location", db.String(100), nullable=True)
    # Getter dan setter untuk atribut privat return_location.
    def get_return_location(self):
        return self.__return_location
    def set_return_location(self, value):
        self.__return_location = value
    return_location = synonym("_Rental__return_location", descriptor=property(get_return_location, set_return_location))
    
    __special_request     = db.Column("special_request", db.Text, nullable=True)
    # Getter dan setter untuk atribut privat special_request.
    def get_special_request(self):
        return self.__special_request
    def set_special_request(self, value):
        self.__special_request = value
    special_request = synonym("_Rental__special_request", descriptor=property(get_special_request, set_special_request))


    # Dokumen yang diperlukan untuk penyewaan.

    __ktp_file            = db.Column("ktp_file", db.String(255), nullable=True)
    # Getter dan setter untuk atribut privat ktp_file.
    def get_ktp_file(self):
        return self.__ktp_file
    def set_ktp_file(self, value):
        self.__ktp_file = value
    ktp_file = synonym("_Rental__ktp_file", descriptor=property(get_ktp_file, set_ktp_file))
    
    __sim_file            = db.Column("sim_file", db.String(255), nullable=True)
    # Getter dan setter untuk atribut privat sim_file.
    def get_sim_file(self):
        return self.__sim_file
    def set_sim_file(self, value):
        self.__sim_file = value
    sim_file = synonym("_Rental__sim_file", descriptor=property(get_sim_file, set_sim_file))


    # ---- Denda keterlambatan ----
    # Selama kendaraan masih dipakai, denda dihitung LIVE (berjalan).
    # Saat kendaraan dikembalikan, nilainya DIKUNCI ke kolom di bawah ini
    # supaya tidak terus bertambah setelah mobil masuk garasi.

    __fine_days           = db.Column("fine_days", db.Integer, nullable=False, default=0)
    # Getter dan setter untuk atribut privat fine_days.
    def get_fine_days(self):
        return self.__fine_days
    def set_fine_days(self, value):
        self.__fine_days = value
    fine_days = synonym("_Rental__fine_days", descriptor=property(get_fine_days, set_fine_days))
    
    __fine_amount         = db.Column("fine_amount", db.Integer, nullable=False, default=0)
    # Getter dan setter untuk atribut privat fine_amount.
    def get_fine_amount(self):
        return self.__fine_amount
    def set_fine_amount(self, value):
        self.__fine_amount = value
    fine_amount = synonym("_Rental__fine_amount", descriptor=property(get_fine_amount, set_fine_amount))
    
    __fine_paid           = db.Column("fine_paid", db.Boolean, nullable=False, default=False)
    # Getter dan setter untuk atribut privat fine_paid.
    def get_fine_paid(self):
        return self.__fine_paid
    def set_fine_paid(self, value):
        self.__fine_paid = value
    fine_paid = synonym("_Rental__fine_paid", descriptor=property(get_fine_paid, set_fine_paid))



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

    
    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [BATAS WAKTU PENYEWAAN ATURAN]
    # ──────────────────────────────────────────────────────────────────────────

#[OOP - ENKAPSULASI]: aturan "dibayar tapi tidak diambil" dibungkus di model, bukan di route.
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

# [OOP - ENKAPSULASI & STATE TRANSITION]: perubahan status dan efek sampingnya (termasuk status pembayaran) lewat satu pintu.
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

    # [OOP - ENKAPSULASI & ASOSIASI OBJEK (OBJECT ASSOCIATION)]
    # Properti terenkapsulasi untuk mengambil objek RentalCancellation terbaru
    # dari relasi one-to-many (cancellations) tanpa mengekspos logika pengurutan
    # secara berulang di layer controller maupun template.
    @property
    def latest_cancellation(self):
        if not self.cancellations:
            return None
        return max(self.cancellations, key=lambda c: c.id or 0)

    # [OOP - ENKAPSULASI & ABSTRAKSI STATUS PEMBATALAN]
    # Menyembunyikan detail pengecekan state permohonan pembatalan pelanggan
    # yang masih menunggu keputusan (persetujuan/penolakan) dari Admin.
    @property
    def has_pending_cancellation(self):
        latest = self.latest_cancellation
        return (
            latest is not None
            and latest.initiated_by == 'customer'
            and latest.status == RentalCancellation.STATUS_DIAJUKAN
        )

    # [OOP - ENKAPSULASI & ABSTRAKSI STATUS REFUND]
    # Menentukan apakah pesanan yang telah dibatalkan masih membutuhkan
    # konfirmasi pengembalian dana (refund) dari pihak Admin.
    @property
    def needs_refund(self):
        latest = self.latest_cancellation
        return (
            self.status == self.STATUS_BATAL
            and latest is not None
            and latest.refund_amount is not None
            and latest.refunded_at is None
            and latest.status in (
                RentalCancellation.STATUS_DISETUJUI,
                RentalCancellation.STATUS_MENUNGGU_REFUND,
            )
        )

    # [OOP - ENKAPSULASI & ABSTRAKSI STATUS REFUND]
    # Memeriksa apakah proses pengembalian dana (refund) untuk pesanan ini
    # telah diselesaikan dan dikonfirmasi oleh Admin.
    @property
    def is_refunded(self):
        latest = self.latest_cancellation
        return (
            latest is not None
            and latest.refunded_at is not None
            and latest.status == RentalCancellation.STATUS_DANA_DIKEMBALIKAN
        )



# ═════════════════════════════════════════════════════════════
#   F.   |   HISTORY PESANAN MODEL (HISTORY MODEL)
# ═════════════════════════════════════════════════════════════

# Menyimpan catatan setiap perubahan status pesanan.
class RentalStatusHistory(db.Model):
    


    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT RENTAL]
    # ═════════════════════════════════════════════════════════════════════════


    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA HISTORY]
    # ──────────────────────────────────────────────────────────────────────────

    __tablename__   = 'rental_status_history'

    __id              = db.Column("id", db.Integer, primary_key=True)
    # Getter dan setter untuk atribut privat id.
    def get_id(self):
        return self.__id
    def set_id(self, value):
        self.__id = value
    id = synonym("_RentalStatusHistory__id", descriptor=property(get_id, set_id))

    __rental_id       = db.Column("rental_id", db.Integer, db.ForeignKey('rental.id'), nullable=False, index=True)
    # Getter dan setter untuk atribut privat rental_id.
    def get_rental_id(self):
        return self.__rental_id
    def set_rental_id(self, value):
        self.__rental_id = value
    rental_id = synonym("_RentalStatusHistory__rental_id", descriptor=property(get_rental_id, set_rental_id))

    __old_status      = db.Column("old_status", db.String(50), nullable=True)
    # Getter dan setter untuk atribut privat old_status.
    def get_old_status(self):
        return self.__old_status
    def set_old_status(self, value):
        self.__old_status = value
    old_status = synonym("_RentalStatusHistory__old_status", descriptor=property(get_old_status, set_old_status))
    
    __new_status      = db.Column("new_status", db.String(50), nullable=False)
    # Getter dan setter untuk atribut privat new_status.
    def get_new_status(self):
        return self.__new_status
    def set_new_status(self, value):
        self.__new_status = value
    new_status = synonym("_RentalStatusHistory__new_status", descriptor=property(get_new_status, set_new_status))

    __changed_at      = db.Column("changed_at", db.DateTime, nullable=False, default=datetime.now, index=True)
    # Getter dan setter untuk atribut privat changed_at.
    def get_changed_at(self):
        return self.__changed_at
    def set_changed_at(self, value):
        self.__changed_at = value
    changed_at = synonym("_RentalStatusHistory__changed_at", descriptor=property(get_changed_at, set_changed_at))

    # Menghubungkan riwayat dengan pesanan yang berubah status.
    rental = db.relationship('Rental', back_populates='status_history')



# ═════════════════════════════════════════════════════════════
#   H.   |   RENTAL CANCELLATION MODEL
# ═════════════════════════════════════════════════════════════

# Menyimpan pengajuan pembatalan dan proses pengembalian dana.
class RentalCancellation(db.Model):



    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT RENTAL CANCELLATION]
    # ═════════════════════════════════════════════════════════════════════════
    

    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA RENTAL CANCELLATION]
    # ──────────────────────────────────────────────────────────────────────────

    __tablename__               = 'rental_cancellation'

    # Status yang digunakan selama proses pembatalan.
    STATUS_DIAJUKAN             = 'Pembatalan Diajukan'
    STATUS_DISETUJUI            = 'Pembatalan Disetujui'
    STATUS_DITOLAK              = 'Pembatalan Ditolak'
    STATUS_MENUNGGU_REFUND      = 'Menunggu Pengembalian Dana'
    STATUS_DANA_DIKEMBALIKAN    = 'Dana Dikembalikan'

    __id = db.Column("id", db.Integer, primary_key=True)
    # Getter dan setter untuk atribut privat id.
    def get_id(self):
        return self.__id
    def set_id(self, value):
        self.__id = value
    id = synonym("_RentalCancellation__id", descriptor=property(get_id, set_id))

    __rental_id = db.Column("rental_id", db.Integer, db.ForeignKey('rental.id'), nullable=False, index=True)
    # Getter dan setter untuk atribut privat rental_id.
    def get_rental_id(self):
        return self.__rental_id
    def set_rental_id(self, value):
        self.__rental_id = value
    rental_id = synonym("_RentalCancellation__rental_id", descriptor=property(get_rental_id, set_rental_id))

    # Alasan pembatalan yang disampaikan oleh pihak pengaju.
    __reason = db.Column("reason", db.String(500), nullable=False )
    # Getter dan setter untuk atribut privat reason.
    def get_reason(self):
        return self.__reason
    def set_reason(self, value):
        self.__reason = value
    reason = synonym("_RentalCancellation__reason", descriptor=property(get_reason, set_reason))

    # Menandai pihak yang mengajukan pembatalan.
    __initiated_by = db.Column("initiated_by", db.String(20), nullable=False)
    # Getter dan setter untuk atribut privat initiated_by.
    def get_initiated_by(self):
        return self.__initiated_by
    def set_initiated_by(self, value):
        self.__initiated_by = value
    initiated_by = synonym("_RentalCancellation__initiated_by", descriptor=property(get_initiated_by, set_initiated_by))

    __status = db.Column("status", db.String(50), nullable=False, default=STATUS_DIAJUKAN)
    # Getter dan setter untuk atribut privat status.
    def get_status(self):
        return self.__status
    def set_status(self, value):
        self.__status = value
    status = synonym("_RentalCancellation__status", descriptor=property(get_status, set_status))


    # Waktu pengajuan dan keputusan pembatalan:

    __requested_at = db.Column("requested_at", db.DateTime, nullable=True)
    # Getter dan setter untuk atribut privat requested_at.
    def get_requested_at(self):
        return self.__requested_at
    def set_requested_at(self, value):
        self.__requested_at = value
    requested_at = synonym("_RentalCancellation__requested_at", descriptor=property(get_requested_at, set_requested_at))
    
    __approved_at = db.Column("approved_at", db.DateTime, nullable=True)
    # Getter dan setter untuk atribut privat approved_at.
    def get_approved_at(self):
        return self.__approved_at
    def set_approved_at(self, value):
        self.__approved_at = value
    approved_at = synonym("_RentalCancellation__approved_at", descriptor=property(get_approved_at, set_approved_at))
    
    __rejected_at = db.Column("rejected_at", db.DateTime, nullable=True)
    # Getter dan setter untuk atribut privat rejected_at.
    def get_rejected_at(self):
        return self.__rejected_at
    def set_rejected_at(self, value):
        self.__rejected_at = value
    rejected_at = synonym("_RentalCancellation__rejected_at", descriptor=property(get_rejected_at, set_rejected_at))
    
    __cancelled_at = db.Column("cancelled_at", db.DateTime,nullable=True)
    # Getter dan setter untuk atribut privat cancelled_at.
    def get_cancelled_at(self):
        return self.__cancelled_at
    def set_cancelled_at(self, value):
        self.__cancelled_at = value
    cancelled_at = synonym("_RentalCancellation__cancelled_at", descriptor=property(get_cancelled_at, set_cancelled_at))


    # Waktu dana dikembalikan kepada pelanggan:

    __refunded_at = db.Column("refunded_at", db.DateTime, nullable=True)
    # Getter dan setter untuk atribut privat refunded_at.
    def get_refunded_at(self):
        return self.__refunded_at
    def set_refunded_at(self, value):
        self.__refunded_at = value
    refunded_at = synonym("_RentalCancellation__refunded_at", descriptor=property(get_refunded_at, set_refunded_at))


    # Jumlah dana yang perlu atau sudah dikembalikan:

    __refund_amount = db.Column("refund_amount", db.Integer, nullable=True)
    # Getter dan setter untuk atribut privat refund_amount.
    def get_refund_amount(self):
        return self.__refund_amount
    def set_refund_amount(self, value):
        self.__refund_amount = value
    refund_amount = synonym("_RentalCancellation__refund_amount", descriptor=property(get_refund_amount, set_refund_amount))

    # Catatan tambahan dari admin.
    __admin_note = db.Column("admin_note", db.Text, nullable=True)
    # Getter dan setter untuk atribut privat admin_note.
    def get_admin_note(self):
        return self.__admin_note
    def set_admin_note(self, value):
        self.__admin_note = value
    admin_note = synonym("_RentalCancellation__admin_note", descriptor=property(get_admin_note, set_admin_note))

    # Menghubungkan data pembatalan dengan pesanan terkait.
    rental = db.relationship('Rental', back_populates='cancellations')

    # ═════════════════════════════════════════════════════════════════════════
    #                [METHOD & PROPERTI OOP RENTAL CANCELLATION]
    # ═════════════════════════════════════════════════════════════════════════

    # [OOP - ENKAPSULASI STATE]
    # Properti terenkapsulasi untuk memeriksa apakah permohonan pembatalan
    # dari pelanggan masih menunggu persetujuan Admin.
    @property
    def is_pending(self):
        return (
            self.initiated_by == 'customer'
            and self.status == self.STATUS_DIAJUKAN
        )

    # [OOP - ENKAPSULASI STATE]
    # Properti terenkapsulasi untuk memeriksa apakah permohonan pembatalan
    # pelanggan telah ditolak oleh Admin.
    @property
    def is_rejected(self):
        return self.status == self.STATUS_DITOLAK

    # [OOP - ENKAPSULASI STATE REFUND]
    # Memeriksa apakah objek pembatalan ini membutuhkan konfirmasi
    # pengembalian dana oleh Admin.
    @property
    def needs_refund(self):
        return (
            self.refund_amount is not None
            and self.refunded_at is None
            and self.status in (
                self.STATUS_DISETUJUI,
                self.STATUS_MENUNGGU_REFUND,
            )
        )

    # [OOP - ENKAPSULASI STATE REFUND]
    # Memeriksa apakah dana refund pada pembatalan ini sudah dikembalikan.
    @property
    def is_refunded(self):
        return (
            self.refunded_at is not None
            and self.status == self.STATUS_DANA_DIKEMBALIKAN
        )

    # [OOP - ENKAPSULASI & STATE TRANSITION (BEHAVIOR METHOD)]
    # Mengenkapsulasi perubahan state saat Admin menyetujui permohonan
    # pembatalan yang diajukan oleh pelanggan.
    def approve(self, refund_amount=None, timestamp=None):
        waktu = timestamp or datetime.now()
        self.approved_at = waktu
        self.cancelled_at = waktu
        self.refund_amount = refund_amount
        self.status = (
            self.STATUS_MENUNGGU_REFUND
            if refund_amount is not None
            else self.STATUS_DISETUJUI
        )

    # [OOP - ENKAPSULASI & STATE TRANSITION (BEHAVIOR METHOD)]
    # Mengenkapsulasi perubahan state saat Admin menolak permohonan
    # pembatalan pelanggan beserta catatan alasan penolakan (admin_note).
    def reject(self, admin_note=None, timestamp=None):
        waktu = timestamp or datetime.now()
        self.rejected_at = waktu
        self.status = self.STATUS_DITOLAK
        self.admin_note = (admin_note or '').strip() or None

    # [OOP - ENKAPSULASI & STATE TRANSITION (BEHAVIOR METHOD)]
    # Mengenkapsulasi perubahan state saat Admin mengonfirmasi bahwa dana
    # refund telah dikembalikan kepada pelanggan.
    def mark_refunded(self, nominal=None, timestamp=None):
        waktu = timestamp or datetime.now()
        if nominal is not None:
            self.refund_amount = int(nominal)
        self.refunded_at = waktu
        self.status = self.STATUS_DANA_DIKEMBALIKAN

    # [OOP - ABSTRAKSI & POLIMORFISME DATA TIMELINE]
    # Menghasilkan tahapan timeline pembatalan secara dinamis berdasarkan
    # aktor pengaju (customer vs admin) dan kondisi pembayaran (refund vs non-refund).
    @property
    def timeline_steps(self):
        """Menyusun timeline berdasarkan aktor, keputusan, dan status refund."""
        if self.is_rejected:
            return [
                ('fa-file-circle-plus', 'Pembatalan Diajukan', self.requested_at),
                ('fa-circle-xmark', 'Pembatalan Ditolak', self.rejected_at),
            ]

        steps = [
            ('fa-file-circle-plus', 'Pembatalan Diajukan',
             self.requested_at or self.cancelled_at),
        ]

        if self.initiated_by == 'customer':
            # Pengajuan pelanggan harus menampilkan keputusan admin.
            if self.approved_at:
                label_keputusan = (
                    'Menunggu Pengembalian Dana'
                    if self.refund_amount is not None
                    else 'Pembatalan Disetujui'
                )
                steps.append(('fa-circle-check', label_keputusan, self.approved_at))
            elif self.status == self.STATUS_MENUNGGU_REFUND:
                steps.append(('fa-wallet', 'Menunggu Pengembalian Dana', self.cancelled_at))
        elif self.initiated_by in ('admin', 'system'):
            # Pembatalan langsung admin/sistem tidak melewati tahap persetujuan.
            if self.refund_amount is not None:
                steps.append(('fa-wallet', 'Menunggu Pengembalian Dana', self.cancelled_at))
            else:
                steps[0] = (
                    'fa-ban',
                    'Pembatalan Diajukan',
                    self.requested_at or self.cancelled_at
                )

        if self.refund_amount is not None:
            steps.append((
                'fa-wallet',
                'Dana Dikembalikan',
                self.refunded_at
            ))

        return steps

    # [OOP - ABSTRAKSI PERHITUNGAN STATE TIMELINE]
    # Menghitung jumlah tahapan timeline pembatalan yang sudah selesai (memiliki timestamp).
    @property
    def completed_steps_count(self):
        return sum(1 for _, _, waktu in self.timeline_steps if waktu is not None)



# ═════════════════════════════════════════════════════════════
#   I.   |   REVIEW MODEL
# ═════════════════════════════════════════════════════════════

# Menyimpan ulasan pelanggan terhadap kendaraan.
class Review(db.Model):



    # ═════════════════════════════════════════════════════════════════════════
    #                           [ATRIBUT REVIEW]
    # ═════════════════════════════════════════════════════════════════════════
    
    
    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA REVIEW]
    # ──────────────────────────────────────────────────────────────────────────

    __id          = db.Column("id", db.Integer, primary_key=True)
    # Getter dan setter untuk atribut privat id.
    def get_id(self):
        return self.__id
    def set_id(self, value):
        self.__id = value
    id = synonym("_Review__id", descriptor=property(get_id, set_id))
    
    __user_id     = db.Column("user_id", db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Getter dan setter untuk atribut privat user_id.
    def get_user_id(self):
        return self.__user_id
    def set_user_id(self, value):
        self.__user_id = value
    user_id = synonym("_Review__user_id", descriptor=property(get_user_id, set_user_id))
    
    __vehicle_id  = db.Column("vehicle_id", db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    # Getter dan setter untuk atribut privat vehicle_id.
    def get_vehicle_id(self):
        return self.__vehicle_id
    def set_vehicle_id(self, value):
        self.__vehicle_id = value
    vehicle_id = synonym("_Review__vehicle_id", descriptor=property(get_vehicle_id, set_vehicle_id))


    # Nilai ulasan menggunakan skala 1 sampai 5:

    __rating      = db.Column("rating", db.Integer, nullable=False)   # 1 sampai 5
    # Getter dan setter untuk atribut privat rating.
    def get_rating(self):
        return self.__rating
    def set_rating(self, value):
        self.__rating = value
    rating = synonym("_Review__rating", descriptor=property(get_rating, set_rating))
    
    __comment     = db.Column("comment", db.Text, nullable=True)
    # Getter dan setter untuk atribut privat comment.
    def get_comment(self):
        return self.__comment
    def set_comment(self, value):
        self.__comment = value
    comment = synonym("_Review__comment", descriptor=property(get_comment, set_comment))
    
    __created_at  = db.Column("created_at", db.DateTime, nullable=False, default=datetime.now)
    # Getter dan setter untuk atribut privat created_at.
    def get_created_at(self):
        return self.__created_at
    def set_created_at(self, value):
        self.__created_at = value
    created_at = synonym("_Review__created_at", descriptor=property(get_created_at, set_created_at))

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


    # ──────────────────────────────────────────────────────────────────────────
    # ↪  [DATA REVIEW]
    # ──────────────────────────────────────────────────────────────────────────

    __id          = db.Column("id", db.Integer, primary_key=True)
    # Getter dan setter untuk atribut privat id.
    def get_id(self):
        return self.__id
    def set_id(self, value):
        self.__id = value
    id = synonym("_Notification__id", descriptor=property(get_id, set_id))
    
    __user_id     = db.Column("user_id", db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Getter dan setter untuk atribut privat user_id.
    def get_user_id(self):
        return self.__user_id
    def set_user_id(self, value):
        self.__user_id = value
    user_id = synonym("_Notification__user_id", descriptor=property(get_user_id, set_user_id))
    
    __rental_id   = db.Column("rental_id", db.Integer, db.ForeignKey('rental.id'), nullable=False)
    # Getter dan setter untuk atribut privat rental_id.
    def get_rental_id(self):
        return self.__rental_id
    def set_rental_id(self, value):
        self.__rental_id = value
    rental_id = synonym("_Notification__rental_id", descriptor=property(get_rental_id, set_rental_id))
    
    __title       = db.Column("title", db.String(100), nullable=False)
    # Getter dan setter untuk atribut privat title.
    def get_title(self):
        return self.__title
    def set_title(self, value):
        self.__title = value
    title = synonym("_Notification__title", descriptor=property(get_title, set_title))
    
    __message     = db.Column("message", db.Text, nullable=False)
    # Getter dan setter untuk atribut privat message.
    def get_message(self):
        return self.__message
    def set_message(self, value):
        self.__message = value
    message = synonym("_Notification__message", descriptor=property(get_message, set_message))


    # Status sebelum dan sesudah perubahan:

    __old_status  = db.Column("old_status", db.String(50), nullable=True)
    # Getter dan setter untuk atribut privat old_status.
    def get_old_status(self):
        return self.__old_status
    def set_old_status(self, value):
        self.__old_status = value
    old_status = synonym("_Notification__old_status", descriptor=property(get_old_status, set_old_status))
    
    __new_status  = db.Column("new_status", db.String(50), nullable=False)
    # Getter dan setter untuk atribut privat new_status.
    def get_new_status(self):
        return self.__new_status
    def set_new_status(self, value):
        self.__new_status = value
    new_status = synonym("_Notification__new_status", descriptor=property(get_new_status, set_new_status))
    
    __is_read     = db.Column("is_read", db.Boolean, nullable=False, default=False)
    # Getter dan setter untuk atribut privat is_read.
    def get_is_read(self):
        return self.__is_read
    def set_is_read(self, value):
        self.__is_read = value
    is_read = synonym("_Notification__is_read", descriptor=property(get_is_read, set_is_read))

    __created_at  = db.Column("created_at", db.DateTime, nullable=False, default=datetime.now )
    # Getter dan setter untuk atribut privat created_at.
    def get_created_at(self):
        return self.__created_at
    def set_created_at(self, value):
        self.__created_at = value
    created_at = synonym("_Notification__created_at", descriptor=property(get_created_at, set_created_at))

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

    __category    = db.Column("category", db.String(20), nullable=False, default=CATEGORY_STATUS )
    # Getter dan setter untuk atribut privat category.
    def get_category(self):
        return self.__category
    def set_category(self, value):
        self.__category = value
    category = synonym("_Notification__category", descriptor=property(get_category, set_category))

    # Menghubungkan notifikasi dengan akun dan pesanan.
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
    rental = db.relationship('Rental', backref=db.backref('notifications', lazy=True))


    # ──────────────────────────────────────────────────────────────────────────
    # ↪  PENGATURAN TAMPILAN NOTIFIKASI
    # ──────────────────────────────────────────────────────────────────────────
    
    # Ikon dan warna teks untuk setiap jenis notifikasi.
    __STYLE = {
        CATEGORY_STATUS             : ('fa-solid fa-bell', 'tone-info'),
        CATEGORY_REMINDER           : ('fa-solid fa-clock', 'tone-warning'),
        CATEGORY_OVERDUE            : ('fa-solid fa-triangle-exclamation', 'tone-danger'),
        CATEGORY_FINE               : ('fa-solid fa-file-invoice-dollar', 'tone-danger'),
        CATEGORY_PAYMENT_1H         : ('fa-solid fa-credit-card', 'tone-warning'),
        CATEGORY_PAYMENT_30M        : ('fa-solid fa-hourglass-half', 'tone-warning'),
        CATEGORY_PAYMENT_CANCELLED  : ('fa-solid fa-ban', 'tone-danger'),
        CATEGORY_PICKUP_EXPIRED     : ('fa-solid fa-ban', 'tone-danger'),
        CATEGORY_RETURN_24H         : ('fa-solid fa-car-side', 'tone-info'),
        CATEGORY_RETURN_3H          : ('fa-solid fa-clock', 'tone-warning'),
    }

    # Class CSS untuk latar kartu notifikasi.
    __CARD_STYLE = {
        CATEGORY_STATUS             : 'card-status',
        CATEGORY_REMINDER           : 'card-rental',
        CATEGORY_OVERDUE            : 'card-rental',
        CATEGORY_FINE               : 'card-rental',
        CATEGORY_PAYMENT_1H         : 'card-payment',
        CATEGORY_PAYMENT_30M        : 'card-payment',
        CATEGORY_PAYMENT_CANCELLED  : 'card-payment',
        CATEGORY_PICKUP_EXPIRED     : 'card-rental',
        CATEGORY_RETURN_24H         : 'card-rental',
        CATEGORY_RETURN_3H          : 'card-rental',
    }

    # Label dan warna badge untuk setiap jenis notifikasi.
    __BADGE_STYLE = {
        CATEGORY_STATUS             : ('Status Pesanan', 'info'),
        CATEGORY_REMINDER           : ('Pengingat', 'warning'),
        CATEGORY_OVERDUE            : ('Denda', 'danger'),
        CATEGORY_FINE               : ('Denda', 'danger'),
        CATEGORY_PAYMENT_1H         : ('Pengingat Pembayaran', 'warning'),
        CATEGORY_PAYMENT_30M        : ('Segera Bayar', 'warning'),
        CATEGORY_PAYMENT_CANCELLED  : ('Dibatalkan', 'danger'),
        CATEGORY_PICKUP_EXPIRED     : ('Dibatalkan', 'danger'),
        CATEGORY_RETURN_24H         : ('Pengingat Pengembalian', 'info'),
        CATEGORY_RETURN_3H          : ('Segera Dikembalikan', 'warning'),
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

# [OOP - FACTORY METHOD & ENKAPSULASI NOTIFIKASI]
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

    @classmethod
    def fine_issued(cls, rental):
        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=cls.CATEGORY_FINE,
            title='Tagihan Denda Keterlambatan',
            message=(
                f'Kendaraan pesanan {rental.booking_code} dikembalikan '
                f'terlambat {rental.fine_days} hari. Total denda: '
                f'{cls._rp(rental.fine_amount)}. Silakan selesaikan '
                f'pembayaran denda kepada admin.'
            ),
            old_status=rental.status,
            new_status=rental.status,
        )

# [OOP - FACTORY METHOD & ENKAPSULASI NOTIFIKASI]
    @classmethod
    def payment_cancelled(cls, rental, old_status=None):
        """Membuat notifikasi pembatalan otomatis akibat pembayaran kedaluwarsa."""
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

# [OOP - FACTORY METHOD & ENKAPSULASI NOTIFIKASI]
    @classmethod
    def pickup_expired(cls, rental, old_status=None):
        """Membuat notifikasi pembatalan otomatis karena kendaraan tidak diambil."""
        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=cls.CATEGORY_PICKUP_EXPIRED,
            title='Pesanan Dibatalkan karena Kendaraan Tidak Diambil',
            message=(
                f'Pesanan {rental.booking_code} dibatalkan otomatis karena '
                'kendaraan tidak diambil hingga masa sewa berakhir. '
                'Silakan hubungi admin untuk informasi lebih lanjut.'
            ),
            old_status=old_status or rental.status,
            new_status=Rental.STATUS_BATAL,
        )

    # [OOP - FACTORY METHOD & ENKAPSULASI NOTIFIKASI]
    # Membuat objek Notification saat permohonan pembatalan pelanggan ditolak Admin.
    @classmethod
    def cancellation_rejected(cls, rental, cancellation):
        catatan = (
            f' Catatan admin: {cancellation.admin_note}'
            if cancellation and cancellation.admin_note
            else ''
        )
        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=cls.CATEGORY_STATUS,
            title='Permohonan Pembatalan Ditolak',
            message=(
                f'Permohonan pembatalan untuk pesanan {rental.booking_code} '
                f'ditolak oleh admin. Status pesanan tetap "{rental.status}".'
                f'{catatan}'
            ),
            old_status=rental.status,
            new_status=rental.status,
        )

    # [OOP - FACTORY METHOD & ENKAPSULASI NOTIFIKASI]
    # Membuat objek Notification saat Admin mengonfirmasi pengembalian dana (refund).
    @classmethod
    def refund_completed(cls, rental, cancellation):
        nominal_rp = cls._rp(cancellation.refund_amount or 0)
        return cls(
            user_id=rental.user_id,
            rental_id=rental.id,
            category=cls.CATEGORY_STATUS,
            title='Pengembalian Dana Selesai',
            message=(
                f'Pengembalian dana sebesar {nominal_rp} untuk pesanan '
                f'{rental.booking_code} telah selesai diproses oleh admin.'
            ),
            old_status=Rental.STATUS_BATAL,
            new_status=RentalCancellation.STATUS_DANA_DIKEMBALIKAN,
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