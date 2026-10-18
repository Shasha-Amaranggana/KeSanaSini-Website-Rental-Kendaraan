from app import create_app, db
from app.models import Vehicle, User, Rental, Review
from datetime import date, datetime, timedelta

def run_seed():
    """Fungsi pembangun isi awal database"""
    # 1. HANCURKAN DAN BANGUN ULANG DATABASE
    print("Mereset database...")
    db.drop_all()
    db.create_all()

    # 2. BUAT AKUN TESTER (USER & ADMIN)
    print("Membuat akun tester...")
    
    # Akun Pelanggan Biasa
    user_biasa = User(
        name="Sana Sini",
        birth_date=date(2000, 1, 1),
        gender="Laki-laki",
        email="sanasini@gmail.com",
        phone="081234567890",
        emergency_phone="080987654321",
        role="user"
    )
    user_biasa.set_password("admin123")
    
    # Akun Admin
    admin_web = User(
        name="Bos Admin",
        birth_date=date(1990, 5, 5),
        gender="Perempuan",
        email="admin@sanasini.com",
        phone="08111222333",
        emergency_phone="08333222111",
        role="admin"
    )
    admin_web.set_password("admin123")

    db.session.add(user_biasa)
    db.session.add(admin_web)

    # Akun Super Admin + beberapa admin contoh (modul Kelola Admin)
    super_admin = User(
        name="Super Admin", birth_date=date(1988, 3, 3), gender="Laki-laki",
        email="superadmin@sanasini.com", phone="08999000111", emergency_phone="08999000222",
        ktp_number="1234567890123456", sim_number="123456789012", role="superadmin"
    )
    super_admin.set_password("admin123")
    db.session.add(super_admin)

    for nama, email, aktif in [("Mimin Jakan", "mimin@sanasini.com", False),
                               ("Lamin Temet", "lamin@sanasini.com", True),
                               ("Fandi Santoso", "fandi@sanasini.com", True)]:
        staf = User(
            name=nama, birth_date=date(1995, 1, 1), gender="Laki-laki", email=email,
            phone="08777000111", emergency_phone="08777000222",
            ktp_number="1234567890123456", sim_number="123456789012",
            role="admin", is_active=aktif
        )
        staf.set_password("admin123")
        db.session.add(staf)

    # 3. BUAT DATA KENDARAAN
    print("Memasukkan data kendaraan...")
    vehicles = [
        Vehicle(
            photo="rush1.png",
            gallery="rush2.png, rush3.png",
            brand="Toyota",
            model="Rush",
            vehicle_number="KT 1234 XX",
            year=2024,
            vehicle_type="Mobil",
            seats=7,
            luggage=2,
            price_per_day=500000,
            rental_type="Sopir & Tanpa Sopir",
            color="Hitam",
            chassis_number="CH1234567890",
            engine_number="EN1234567890",
            fuel="Bensin",
            transmission="Manual",
            engine_cc=1500,
            facilities="AC dingin, Airbag, Kamera belakang, Audio bluetooth, Ban serep",
            notes="Servis terakhir 15 September 2026, Goresan kecil di bumper belakang kanan, Dilarang merokok di dalam mobil"
        ),
        Vehicle(
            photo="avanza1.png",
            gallery="avanza2.png, avanza3.png",
            brand="Toyota",
            model="Grand New Avanza",
            vehicle_number="KT 2345 XX",
            year=2024,
            vehicle_type="Mobil",
            seats=7,
            luggage=2,
            price_per_day=450000,
            rental_type="Sopir & Tanpa Sopir",
            color="Putih",
            chassis_number="CH0987654321",
            engine_number="EN0987654321",
            fuel="Bensin",
            transmission="Manual",
            engine_cc=1500,
            facilities="AC dingin, Airbag, Kamera belakang, Ban serep",
            notes="Servis terakhir 9 September 2026, Dilarang merokok di dalam mobil"
        ),
        Vehicle(
            photo="xenia1.png",
            gallery="xenia2.png, xenia3.png",
            brand="Daihatsu",
            model="Xenia",
            vehicle_number="KT 3456 XX",
            year=2023,
            vehicle_type="Mobil",
            seats=7,
            luggage=2,
            price_per_day=400000,
            rental_type="Sopir & Tanpa Sopir",
            color="Silver",
            chassis_number="CH5678901234",
            engine_number="EN5678901234",
            fuel="Bensin",
            transmission="Manual",
            engine_cc=1300,
            facilities="AC dingin, Airbag, Kamera belakang, Ban serep",
            notes="Servis terakhir 9 September 2026, Dilarang merokok di dalam mobil"
        ),
        Vehicle(
            photo="nmax1.png",
            gallery="nmax2.png, nmax3.png",
            brand="Yamaha",
            model="NMAX",
            vehicle_number="KT 4567 XX",
            year=2024,
            vehicle_type="Motor",
            seats=2,
            luggage=1,
            price_per_day=120000,
            rental_type="Tanpa Sopir",
            color="Hitam",
            chassis_number="CH1111111111",
            engine_number="EN1111111111",
            fuel="Bensin",
            transmission="Automatic",
            engine_cc=155,
            facilities="Ban tubeless, Lampu LED, Bagasi luas, pajak hidup",
            notes="Servis terakhir 15 Agustus 2026"
        ),
        Vehicle(
            photo="vario1.png",
            gallery="vario2.png, vario3.png",
            brand="Honda",
            model="Vario 110",
            vehicle_number="KT 5678 XX",
            year=2023,
            vehicle_type="Motor",
            seats=2,
            luggage=1,
            price_per_day=100000,
            rental_type="Tanpa Sopir",
            color="Hitam",
            chassis_number="CH6789012345",
            engine_number="EN6789012345",
            fuel="Bensin",
            transmission="Automatic",
            engine_cc=110,
            facilities="Ban tubeless, Lampu LED, pajak hidup",
            notes="Servis terakhir 25 September 2026, Goresan kecil di body kanan"
        )
    ]

    db.session.add_all(vehicles)
    db.session.flush()  # supaya vehicle.id sudah terisi

    # 4. BUAT SOPIR CONTOH
    from app.models import Driver
    print("Membuat sopir contoh...")
    drivers = [
        Driver(name="Ahmad Hidayat", phone="081999888771"),
        Driver(name="Reza Pahlevi", phone="081999888772"),
        Driver(name="Andi Saputra", phone="081999888773"),
    ]
    db.session.add_all(drivers)
    db.session.flush()
    ahmad, reza, andi = drivers

    # 5. BUAT PELANGGAN CONTOH
    print("Membuat pelanggan contoh...")
    customers = []
    for i, (nama, gender) in enumerate([
        ("Budi Santoso", "Laki-laki"),
        ("Udin Saputra", "Laki-laki"),
        ("Yanto Wijaya", "Laki-laki"),
        ("Adit Pratama", "Laki-laki"),
    ], start=1):
        c = User(
            name=nama,
            birth_date=date(1998, i, 10),
            gender=gender,
            email=f"{nama.split()[0].lower()}@gmail.com",
            phone=f"08120000000{i}",
            emergency_phone=f"08130000000{i}",
            role="user"
        )
        c.set_password("user123")
        customers.append(c)
    db.session.add_all(customers)
    db.session.flush()

    # 6. BUAT DATA PENYEWAAN CONTOH
    print("Membuat data penyewaan...")
    budi, udin, yanto, adit = customers
    rush, avanza, xenia, nmax, vario = vehicles
    now = datetime.now()

    rental_data = [
        # (pelanggan, kendaraan, tgl sewa, tgl kembali, status, hari lalu, metode bayar, status bayar, sopir)
        (budi,      rush,   date(2026, 10, 1),  date(2026, 10, 4),  Rental.STATUS_SELESAI,                7, "Transfer Bank", "Lunas", ahmad),
        (udin,      rush,   date(2026, 10, 3),  date(2026, 10, 7),  Rental.STATUS_PENGEMBALIAN,           6, "Transfer Bank", "Lunas", None),
        (yanto,     xenia,  date(2026, 10, 5),  date(2026, 10, 9),  Rental.STATUS_DIPAKAI,                5, "E-Wallet",      "Lunas", reza),
        (adit,      avanza, date(2026, 10, 7),  date(2026, 10, 15), Rental.STATUS_BATAL,                  4, "-",             "Belum Lunas", None),
        (budi,      nmax,   date(2026, 10, 7),  date(2026, 10, 10), Rental.STATUS_DIPAKAI,                3, "Cash",          "Lunas", None),
        (user_biasa, vario, date(2026, 10, 10), date(2026, 10, 12), Rental.STATUS_MENUNGGU_BAYAR,         1, "Transfer Bank", "Belum Lunas", None),
        (udin,      avanza, date(2026, 10, 11), date(2026, 10, 14), Rental.STATUS_MENUNGGU_KONFIRMASI,    0, "E-Wallet",      "Lunas", None),
        (yanto,     rush,   date(2026, 10, 12), date(2026, 10, 13), Rental.STATUS_PENGAMBILAN,            0, "Cash",          "Belum Lunas", None),
    ]

    rentals = []
    for idx, (cust, veh, start, end, status, days_ago, p_method, p_status, sopir) in enumerate(rental_data, start=1):
        
        # DEMO TRACKING: Set koordinat jika mobil sedang dipakai
        if status == Rental.STATUS_DIPAKAI:
            veh.current_lat = -0.502106 + (idx * 0.001)  # Sebarkan titik di Samarinda
            veh.current_lng = 117.153709 + (idx * 0.001)
            
        jam = ['08:00', '09:30', '10:00', '13:00', '15:30', '19:00'][idx % 6]
        rentals.append(Rental(
            booking_code=f"RMB{1000 + idx}",
            user_id=cust.id,
            vehicle_id=veh.id,
            start_date=start,
            end_date=end,
            pickup_time=jam,
            return_time=jam,
            status=status,
            payment_method=p_method,
            payment_status=p_status,
            cancellation_reason="Ada perubahan jadwal perjalanan mendadak." if status == Rental.STATUS_BATAL else None,
            driver_id=sopir.id if sopir else None,
            with_driver=True if sopir else False,
            accessories="bantal,selimut" if idx % 2 == 0 else "",
            insurance="lengkap" if idx % 3 == 0 else "dasar",
            destination_city="Samarinda" if idx % 2 == 0 else "Balikpapan",
            special_request="Mohon kendaraan sudah dicuci bersih dan bensin terisi penuh saat diambil." if idx % 2 == 1 else None,
            created_at=now - timedelta(days=days_ago, minutes=idx)
        ))
    db.session.add_all(rentals)

        # 5b. BUAT ULASAN CONTOH
    print("Membuat ulasan contoh...")
    review_data = [
        # (pelanggan, kendaraan, rating, komentar)
        (budi,       rush,   5, "Proses seruh terima satset, bensin awal juga penuh. Mantappp"),
        (udin,       rush,   5, "Mobil bersih, AC dingin"),
        (yanto,      rush,   4, "Mobil nyaman dipakai keluarga, adminnya ramah"),
        (adit,       rush,   4, "Kondisi mobil bagus, sesuai foto"),
        (user_biasa, rush,   5, "Sewa gampang, mobil terawat"),
        (budi,       rush,   3, "Mobil oke, tapi pengembalian sempat antre"),
        (udin,       avanza, 4, "Luas dan nyaman untuk perjalanan jauh"),
        (yanto,      xenia,  5, "Harga terjangkau, mobil bersih"),
        (budi,       nmax,   5, "Motor enak dipakai keliling kota"),
    ]
    for i, (cust, veh, rating, komentar) in enumerate(review_data):
        db.session.add(Review(
            user_id=cust.id,
            vehicle_id=veh.id,
            rating=rating,
            comment=komentar,
            created_at=now - timedelta(days=i + 1)
        ))
    
    # 6. SIMPAN SEMUA
    db.session.commit()
    print("Berhasil! Database baru siap digunakan.")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        run_seed()