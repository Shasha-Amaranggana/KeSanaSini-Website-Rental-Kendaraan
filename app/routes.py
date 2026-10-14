from flask import jsonify, Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.models import (
    User, Vehicle, Rental, Review, Driver, Notification)
from sqlalchemy import or_
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from werkzeug.datastructures import MultiDict
from functools import wraps
from app import db
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os

bp = Blueprint('main', __name__)

BULAN_ID = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli',
            'Agustus', 'September', 'Oktober', 'November', 'Desember']

@bp.app_template_filter('rupiah')
def rupiah(value):
    """15000 -> 15.000"""
    return f"{int(value or 0):,}".replace(',', '.')

@bp.app_template_filter('tanggal_id')
def tanggal_id(value):
    """Format tanggal ke Bahasa Indonesia, contoh: 01 Oktober 2026"""
    if not value:
        return '-'
    return f"{value.day:02d} {BULAN_ID[value.month - 1]} {value.year}"

# =========================================================
# HALAMAN OPENING
# =========================================================
@bp.route('/')
def welcome():
    return render_template('welcome.html')


# =========================================================
# HALAMAN UTAMA USER
# =========================================================
@bp.route('/home')
def index():

    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    vehicles = Vehicle.query.all()

    now = datetime.now()

    current_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M')

    return render_template(
        'user/halUtamaUser.html',
        vehicles=vehicles,
        user=user,
        current_date=current_date,
        current_time=current_time
    )


# =========================================================
# HALAMAN PENCARIAN USER
# =========================================================
@bp.route('/hasil-pencarian')
def hasil_pencarian():
    # Ambil data dari form pencarian
    pickup_date_str = request.args.get('date')
    pickup_time = request.args.get('time')
    duration = request.args.get('duration', 1, type=int) or 1

    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    vehicle_type = request.args.get('vehicle_type', 'mobil')

    # Validasi durasi
    duration = max(1, min(duration, 7))

    # Tentukan tanggal pengambilan
    try:
        start_date = datetime.strptime(
            pickup_date_str, '%Y-%m-%d'
        ).date()
    except (ValueError, TypeError):
        start_date = date.today()
        pickup_date_str = start_date.strftime('%Y-%m-%d')

    # Tentukan tanggal pengembalian
    end_date = start_date + timedelta(days=duration)

    # Format tanggal untuk ditampilkan
    pickup_date = start_date.strftime('%d %B %Y')
    return_date = end_date.strftime('%d %B %Y')
    pickup_time = pickup_time or datetime.now().strftime('%H:%M')
    return_time = pickup_time

    # Query kendaraan
    query = Vehicle.query.filter(
        Vehicle.is_active.is_(True)
    )

    # Filter jenis kendaraan
    if vehicle_type:
        query = query.filter(
            Vehicle.vehicle_type.ilike(vehicle_type)
        )

    # Filter harga per hari
    if min_price is not None:
        query = query.filter(
            Vehicle.price_per_day >= min_price
        )

    if max_price is not None:
        query = query.filter(
            Vehicle.price_per_day <= max_price
        )

    # Status yang tidak lagi memblokir kendaraan:
    # selesai dan batal.
    status_selesai = [
        Rental.STATUS_SELESAI,
        Rental.STATUS_BATAL
    ]

    # Cari kendaraan yang memiliki penyewaan bentrok.
    kendaraan_dipesan = (
        db.session.query(Rental.vehicle_id)
        .filter(
            ~Rental.status.in_(status_selesai),
            Rental.start_date <= end_date,
            Rental.end_date >= start_date
        )
        .distinct()
        .subquery()
    )

    # Tampilkan kendaraan yang TIDAK memiliki
    # penyewaan bentrok pada tanggal yang dipilih.
    query = query.filter(
        ~Vehicle.id.in_(kendaraan_dipesan)
    )

    vehicles = query.all()

    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    return render_template(
        'user/halPencarianUser.html',
        vehicles=vehicles,
        user=user,
        pickup_date=pickup_date,
        pickup_time=pickup_time,
        return_date=return_date,
        return_time=return_time,
        duration=duration,
        min_price=min_price,
        max_price=max_price,
        vehicle_type=vehicle_type
    )


@bp.route('/detail-kendaraan/<int:vehicle_id>')
def detail_kendaraan(vehicle_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    # Data pencarian dibawa dari halaman sebelumnya lewat URL
    date_str = request.args.get('date')
    duration = request.args.get('duration', type=int) or 1
    pickup_time = request.args.get('time') or '10:00'

    try:
        pickup_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pickup_date = date.today()

    end_date = pickup_date + timedelta(days=duration)
    total = vehicle.price_per_day * duration

    # Cek ketersediaan di tanggal tsb
    bentrok = Rental.query.filter(
        Rental.vehicle_id == vehicle.id,
        Rental.status.in_([Rental.STATUS_MENUNGGU, Rental.STATUS_BERJALAN]),
        Rental.start_date <= end_date,
        Rental.end_date >= pickup_date
    ).first()

    foto = request.args.get('foto', 0, type=int)
    photos = vehicle.photo_list
    if foto < 0 or foto >= len(photos):
        foto = 0

    show_reviews = request.args.get('ulasan') == '1'
    star = request.args.get('star', type=int)

    reviews = sorted(vehicle.reviews, key=lambda r: r.created_at, reverse=True)
    if star in (1, 2, 3, 4, 5):
        reviews = [r for r in reviews if r.rating == star]
    else:
        star = None

    return render_template(
        'user/haldetailkendaraanUser.html',
        user=user,
        vehicle=vehicle,
        pickup_date=pickup_date,
        pickup_time=pickup_time,
        end_date=end_date,
        duration=duration,
        total=total,
        tersedia=(bentrok is None),
        foto=foto,
        show_reviews=show_reviews,
        star=star,
        reviews=reviews
    )

@bp.route('/kendaraan/<int:vehicle_id>/ulasan')
def semua_ulasan(vehicle_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    vehicle = Vehicle.query.get_or_404(vehicle_id)
    star = request.args.get('star', type=int)

    return redirect(url_for('main.detail_kendaraan', vehicle_id=vehicle.id, ulasan=1, star=star))

PURPOSES = ['Liburan', 'Dinas / Bisnis', 'Acara keluarga', 'Pernikahan', 'Lainnya']
REGIONS = ['Dalam kota', 'Luar kota']
LOCATIONS = ['Kantor rental', 'Bandara SAMS Sepinggan']
ALLOWED_DOC_EXT = {'jpg', 'jpeg', 'png', 'pdf'}

def _save_document(file_storage, booking_code, kind):
    """Simpan KTP/SIM ke static/uploads/dokumen. Return nama file, atau None."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_DOC_EXT:
        return None

    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'dokumen')
    os.makedirs(folder, exist_ok=True)

    filename = secure_filename(f"{booking_code}_{kind}.{ext}")
    file_storage.save(os.path.join(folder, filename))
    return filename

@bp.route('/pesanan', methods=['GET', 'POST'])
def pesanan():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    vehicle_id = request.args.get('vehicle_id', type=int)

    if not vehicle_id:
        flash('Kendaraan belum dipilih.')
        return redirect(url_for('main.index'))

    vehicle = Vehicle.query.get_or_404(vehicle_id)
    can_driver = vehicle.rental_type.startswith('Sopir')

    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    if not user:
        return redirect(url_for('main.login'))

    # Ambil data pencarian sebelumnya
    pickup_date = request.args.get('date')
    duration = request.args.get('duration', type=int)

    if not pickup_date:
        pickup_date = datetime.now().date()
    else:
        pickup_date = datetime.strptime(
            pickup_date,
            '%Y-%m-%d'
        ).date()

    if not duration:
        duration = 1

    end_date = pickup_date + timedelta(days=duration)

    # Jam pengambilan dari halaman pencarian (format HH:MM). Jam kembali = jam ambil.
    pickup_time = request.args.get('time') or '10:00'
    try:
        pickup_time = datetime.strptime(pickup_time, '%H:%M').strftime('%H:%M')
    except ValueError:
        pickup_time = '10:00'
    return_time = pickup_time

    def render_form(form):
        return render_template(
            'user/formsewaUser.html',
            user=user,
            vehicle=vehicle,
            pickup_date=pickup_date,
            end_date=end_date,
            pickup_time=pickup_time,
            return_time=return_time,
            duration=duration,
            can_driver=can_driver,
            driver_fee=Rental.DRIVER_FEE,
            accessories=Rental.ACCESSORIES,
            insurances=Rental.INSURANCES,
            purposes=PURPOSES,
            regions=REGIONS,
            locations=LOCATIONS,
            form=form,
        )

    if request.method == 'GET':
        return render_form(MultiDict())

    # ---------- POST: validasi lalu simpan ----------
    f = request.form
    with_driver = can_driver and f.get('rental_type') == 'sopir'
    accessories = [a for a in f.getlist('accessories') if a in Rental.ACCESSORIES]
    insurance = f.get('insurance') if f.get('insurance') in Rental.INSURANCES else 'dasar'
    region = f.get('region')
    luar_kota = region == 'Luar kota'
    destination = (f.get('destination_city') or '').strip()

    errors = []
    if not f.get('agree'):
        errors.append('Anda harus menyetujui syarat dan ketentuan.')
    if luar_kota and not destination:
        errors.append('Kota tujuan wajib diisi untuk perjalanan luar kota.')

    # KTP wajib untuk semua. SIM hanya wajib kalau lepas kunci.
    docs = [('ktp', 'KTP')] + ([] if with_driver else [('sim', 'SIM')])
    for field, label in docs:
        up = request.files.get(field)
        if not up or not up.filename:
            errors.append(f'{label} wajib diunggah.')
        elif up.filename.rsplit('.', 1)[-1].lower() not in ALLOWED_DOC_EXT:
            errors.append(f'Format {label} harus JPG, PNG, atau PDF.')

    # Cek ulang ketersediaan (bisa saja sudah dipesan orang lain)
    bentrok = Rental.query.filter(
        Rental.vehicle_id == vehicle.id,
        Rental.status.in_([
            Rental.STATUS_MENUNGGU_BAYAR, Rental.STATUS_MENUNGGU_KONFIRMASI,
            Rental.STATUS_PENGAMBILAN, Rental.STATUS_DIPAKAI,
            Rental.STATUS_PENGEMBALIAN,
        ]),
        Rental.start_date <= end_date,
        Rental.end_date >= pickup_date
    ).first()
    if bentrok:
        errors.append('Maaf, kendaraan sudah dipesan pada tanggal tersebut.')

    if errors:
        for e in errors:
            flash(e)
        return render_form(f)

    # Kode booking: RMB + (1000 + nomor urut)
    last = Rental.query.order_by(Rental.id.desc()).first()
    booking_code = f"RMB{1000 + (last.id if last else 0) + 1}"

    rental = Rental(
        booking_code=booking_code,
        user_id=user.id,
        vehicle_id=vehicle.id,
        start_date=pickup_date,
        end_date=end_date,
        pickup_time=pickup_time,
        return_time=return_time,
        status=Rental.STATUS_MENUNGGU_BAYAR,
        with_driver=with_driver,
        accessories=','.join(accessories),
        insurance=insurance,
        purpose=f.get('purpose'),
        region=region,
        destination_city=destination if luar_kota else None,
        pickup_location=f.get('pickup_location'),
        return_location=f.get('return_location'),
        special_request=(f.get('special_request') or '').strip() or None,
    )

    rental.ktp_file = _save_document(request.files.get('ktp'), booking_code, 'ktp')
    if not with_driver:
        rental.sim_file = _save_document(request.files.get('sim'), booking_code, 'sim')

    db.session.add(rental)
    db.session.commit()

    return redirect(url_for('main.pembayaran', rental_id=rental.id))

@bp.route('/pembayaran/<int:rental_id>')
def pembayaran(rental_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get(session['user_id'])
    rental = Rental.query.filter_by(id=rental_id, user_id=user.id).first_or_404()

    if rental.payment_status == 'Lunas':
        return redirect(url_for('main.pembayaran_sukses', rental_id=rental.id))

    deadline = rental.created_at + timedelta(hours=24)
    if rental.status == Rental.STATUS_BATAL or datetime.now() > deadline:
        if rental.status == Rental.STATUS_MENUNGGU_BAYAR:
            rental.status = Rental.STATUS_BATAL
            db.session.commit()
        flash('Waktu pembayaran habis, pesanan dibatalkan.')
        return redirect(url_for('main.index'))

    return render_template('user/pembayaran.html', rental=rental, user=user,
                           total=rental.total_price, deadline=deadline)


@bp.route('/pembayaran/<int:rental_id>/status')
def status_pembayaran(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    return jsonify(paid=(rental.payment_status == 'Lunas'))



@bp.route('/pembayaran/<int:rental_id>/sukses')
def pembayaran_sukses(rental_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.login'))

    rental = Rental.query.filter_by(
        id=rental_id,
        user_id=user.id
    ).first_or_404()

    # Pastikan pesanan belum dibatalkan
    # dan masih menunggu pembayaran.
    if rental.status == Rental.STATUS_MENUNGGU_BAYAR:
        deadline = rental.created_at + timedelta(hours=24)

        if datetime.now() > deadline:
            rental.status = Rental.STATUS_BATAL
            db.session.commit()

            flash('Waktu pembayaran habis, pesanan dibatalkan.')
            return redirect(url_for('main.index'))

        rental.status = Rental.STATUS_MENUNGGU_KONFIRMASI
        db.session.commit()

    return render_template(
        'user/pembayaran_sukses.html',
        rental=rental,
        user=user
    )




# =========================================================
# HALAMAN KELOLA AKUN USER
# =========================================================

@bp.route('/kelola-akun', methods=['GET', 'POST'])
def kelola_akun():
    # Cek login menggunakan session yang sudah ada
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if not user:
        session.clear()
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        emergency_phone = request.form.get(
            'emergency_phone', ''
        ).strip()
        gender = request.form.get('gender', '').strip()

        try:
            # Validasi data wajib
            if not name:
                raise ValueError('Nama lengkap wajib diisi.')

            if not phone or not emergency_phone:
                raise ValueError('Nomor telepon wajib diisi.')

            if gender not in ['Laki-laki', 'Perempuan']:
                raise ValueError('Jenis kelamin tidak valid.')

            # Tanggal lahir dikirim dari tiga dropdown
            day = int(request.form.get('birth_day', ''))
            month = int(request.form.get('birth_month', ''))
            year = int(request.form.get('birth_year', ''))

            birth_date = date(year, month, day)

            # Perbarui data pengguna
            user.name = name
            user.birth_date = birth_date
            user.gender = gender
            user.phone = phone
            user.emergency_phone = emergency_phone

            # Proses upload KTP dan SIM
            upload_folder = os.path.join(
                current_app.root_path,
                'static',
                'uploads',
                'dokumen_akun'
            )
            os.makedirs(upload_folder, exist_ok=True)

            for field, column in [
                ('ktp', 'ktp_file'),
                ('sim', 'sim_file')
            ]:
                uploaded_file = request.files.get(field)

                if uploaded_file and uploaded_file.filename:
                    original_name = secure_filename(
                        uploaded_file.filename
                    )

                    if '.' not in original_name:
                        raise ValueError(
                            'Format dokumen tidak valid.'
                        )

                    extension = original_name.rsplit(
                        '.', 1
                    )[1].lower()

                    if extension not in ALLOWED_DOC_EXT:
                        raise ValueError(
                            'Dokumen harus JPG, JPEG, PNG, atau PDF.'
                        )

                    filename = (
                        f"{field}_{user.id}_"
                        f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}."
                        f"{extension}"
                    )

                    uploaded_file.save(
                        os.path.join(upload_folder, filename)
                    )

                    setattr(user, column, filename)

            db.session.commit()

            # Perbarui nama yang disimpan dalam session
            session['user_name'] = user.name
            session['user_email'] = user.email

            flash('Data akun berhasil disimpan.', 'success')
            return redirect(url_for('main.kelola_akun'))

        except (ValueError, TypeError):
            db.session.rollback()
            flash(
                'Data tidak valid. Periksa kembali isian formulir.',
                'error'
            )

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                'Gagal menyimpan perubahan akun'
            )
            flash(
                'Terjadi kesalahan saat menyimpan data akun.',
                'error'
            )

    return render_template(
        'user/halKelolaAkun.html',
        user=user
    )


@bp.route('/kelola-pesanan', methods=['GET', 'POST'])
def kelola_pesanan():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if not user:
        session.clear()
        return redirect(url_for('main.login'))

    periksa_pengingat_dan_denda(user.id)

    pesanan = (
        Rental.query
        .filter_by(user_id=user.id)
        .order_by(Rental.created_at.desc())
        .all()
    )

    return render_template(
        'user/halKelolaPesanan.html',
        user=user,
        pesanan=pesanan
    )


@bp.route('/detail-pesanan/<int:rental_id>')
def detail_pesanan(rental_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if not user:
        session.clear()
        return redirect(url_for('main.login'))

    periksa_pengingat_dan_denda(user.id)

    rental = Rental.query.filter_by(
        id=rental_id,
        user_id=user.id
    ).first_or_404()

    # Tahap timeline untuk setiap status penyewaan
    status_steps = {
        Rental.STATUS_MENUNGGU_BAYAR: 0,
        Rental.STATUS_MENUNGGU_KONFIRMASI: 1,
        Rental.STATUS_PENGAMBILAN: 2,
        Rental.STATUS_DIPAKAI: 3,
        Rental.STATUS_PENGEMBALIAN: 4,
        Rental.STATUS_SELESAI: 4,
        Rental.STATUS_BATAL: -1,
    }

    current_step = status_steps.get(rental.status, 0)

    return render_template(
        'user/halDetailPesanan.html',
        user=user,
        rental=rental,
        current_step=current_step
    )

@bp.route('/riwayat-pesanan')
def riwayat_pesanan():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if not user:
        session.clear()
        return redirect(url_for('main.login'))

    pesanan = (
        Rental.query
        .filter_by(user_id=user.id, status='Selesai')
        .order_by(Rental.created_at.desc())
        .all()
    )

    return render_template(
        'user/halKelolaPesanan.html',
        user=user,
        pesanan=pesanan,
        halaman='riwayat'
    )


# ---------------------------------------------------------
# [OOP - SERVICE FUNCTION & INTERAKSI ANTAR-OBJEK]
# Fungsi layanan ini memanfaatkan prinsip OOP:
# 1. Enkapsulasi: Mengakses property objek 'rental.is_overdue' dan
#    'rental.is_due_soon' tanpa perlu kalkulasi manual detik/jam di sini.
# 2. Abstraksi & Factory Pattern: Menggunakan method kelas Notification
#    (Notification.overdue_warning & Notification.return_reminder) untuk
#    membuat objek notifikasi tanpa menyusun string pesan secara manual.
# ---------------------------------------------------------
def periksa_pengingat_dan_denda(user_id):
    """
    Sistem Pengingat H-3 & Peringatan Denda Keterlambatan Otomatis (OOP Service).
      1. Jika kendaraan sedang dipakai dan sisa waktu <= 3 hari -> Buat Notifikasi H-3 (1x).
      2. Jika kendaraan melewati batas waktu -> Buat Notifikasi Denda (maks 1x per hari).
    """
    rentals = Rental.query.filter_by(
        user_id=user_id,
        status=Rental.STATUS_DIPAKAI
    ).all()

    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    jumlah_baru = 0

    for rental in rentals:
        # [OOP - ENKAPSULASI]: rental.is_overdue mengevaluasi keterlambatan secara otomatis
        if rental.is_overdue:
            # Cek apakah hari ini sudah pernah dikirimkan peringatan denda
            sudah_ada = Notification.query.filter(
                Notification.user_id == user_id,
                Notification.rental_id == rental.id,
                Notification.category == Notification.CATEGORY_OVERDUE,
                Notification.created_at >= today_start
            ).first()

            if not sudah_ada:
                # [OOP - FACTORY PATTERN]: Memanggil factory method untuk instansiasi notifikasi
                db.session.add(Notification.overdue_warning(rental))
                jumlah_baru += 1

        # [OOP - ENKAPSULASI]: rental.is_due_soon mengevaluasi jendela pengingat H-3
        elif rental.is_due_soon:
            sudah_ada = Notification.query.filter_by(
                user_id=user_id,
                rental_id=rental.id,
                category=Notification.CATEGORY_REMINDER
            ).first()

            if not sudah_ada:
                # [OOP - FACTORY PATTERN]: Memanggil factory method untuk instansiasi pengingat H-3
                db.session.add(Notification.return_reminder(rental))
                jumlah_baru += 1

    if jumlah_baru:
        db.session.commit()


@bp.route('/notifikasi')
def notifikasi():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if not user:
        session.clear()
        return redirect(url_for('main.login'))
    
    periksa_pengingat_dan_denda(user.id)
    
    notifications = (
        Notification.query
        .filter_by(user_id=user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    unread_count = Notification.query.filter_by(
        user_id=user.id,
        is_read=False
    ).count()

    return render_template(
        'user/halKelolaNotifikasi.html',
        user=user,
        notifications=notifications,
        unread_count=unread_count
    )


@bp.route('/ganti-password', methods=['POST'])
def ganti_password():
    # Pastikan user sudah login
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.', 'error')
        return redirect(url_for('main.login'))

    user = db.session.get(User, session['user_id'])

    if not user:
        session.clear()
        flash('Akun tidak ditemukan. Silakan login kembali.', 'error')
        return redirect(url_for('main.login'))

    # Ambil data dari form
    password_lama = request.form.get('current_password', '')
    password_baru = request.form.get('new_password', '')
    konfirmasi_password = request.form.get('confirm_password', '')

    # 1. Periksa password lama
    if not user.check_password(password_lama):
        flash('Password lama yang Anda masukkan salah.', 'error')
        return redirect(url_for('main.kelola_akun'))

    # 2. Validasi password baru
    if (
        len(password_baru) < 8
        or not any(char.isalpha() for char in password_baru)
        or not any(char.isdigit() for char in password_baru)
    ):
        flash(
            'Password baru minimal 8 karakter dan harus mengandung '
            'huruf serta angka.',
            'error'
        )
        return redirect(url_for('main.kelola_akun'))

    # 3. Periksa konfirmasi password
    if password_baru != konfirmasi_password:
        flash('Konfirmasi password baru tidak cocok.', 'error')
        return redirect(url_for('main.kelola_akun'))

    # 4. Password baru harus berbeda dari password lama
    if user.check_password(password_baru):
        flash('Password baru harus berbeda dari password lama.', 'error')
        return redirect(url_for('main.kelola_akun'))

    # 5. Simpan password baru dalam bentuk hash
    user.set_password(password_baru)
    db.session.commit()

    flash('Password berhasil diperbarui.', 'success')
    return redirect(url_for('main.kelola_akun'))




# =========================================================
# HALAMAN LOGIN | REGISTER | LOGOUT
# =========================================================
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_role'] = user.role  # Simpan jabatan di session
            
            # POLISI LALU LINTAS (If-Else Role)
            if user.role in ('admin', 'superadmin'):
                return redirect(url_for('main.admin_dashboard'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('Email atau kata sandi salah. Silakan coba lagi.')
            return redirect(url_for('main.login'))
            
    return render_template('loginRegister.html', mode='login')


@bp.route('/lupa-password', methods=['GET', 'POST'])
def lupa_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()

        user = User.query.filter(
            db.func.lower(User.email) == email.lower()
        ).first()

        # Pesan dibuat sama agar tidak membocorkan
        # apakah sebuah email terdaftar.
        flash(
            'Jika email terdaftar, tautan reset akan dibuat.',
            'info'
        )

        if user:
            serializer = URLSafeTimedSerializer(
                current_app.config['SECRET_KEY'],
                salt='kesanasini-password-reset'
            )

            token = serializer.dumps({
                'user_id': user.id,
                'password_hash': user.password_hash
            })

            reset_url = url_for(
                'main.reset_password',
                token=token,
                _external=True
            )

            # Hanya untuk pengujian lokal.
            current_app.logger.warning(
                '[DEV ONLY] Tautan reset password: %s',
                reset_url
            )

        return redirect(url_for('main.lupa_password'))

    return render_template(
    'loginRegister.html',
    mode='forgot_password'
)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    serializer = URLSafeTimedSerializer(
        current_app.config['SECRET_KEY'],
        salt='kesanasini-password-reset'
    )

    try:
        data = serializer.loads(token, max_age=900)
    except SignatureExpired:
        flash('Tautan reset sudah kedaluwarsa. Silakan minta tautan baru.', 'error')
        return redirect(url_for('main.lupa_password'))
    except BadSignature:
        flash('Tautan reset tidak valid.', 'error')
        return redirect(url_for('main.lupa_password'))

    user = db.session.get(User, data.get('user_id'))

    # Token tidak berlaku lagi jika password sudah berubah.
    if not user or user.password_hash != data.get('password_hash'):
        flash('Tautan reset tidak valid atau sudah digunakan.', 'error')
        return redirect(url_for('main.lupa_password'))

    if request.method == 'POST':
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        if len(password) < 8 or not any(c.isalpha() for c in password) \
                or not any(c.isdigit() for c in password):
            flash(
                'Password minimal 8 karakter dan harus mengandung huruf serta angka.',
                'error'
            )
        elif password != confirm_password:
            flash('Konfirmasi password tidak cocok.', 'error')
        elif user.check_password(password):
            flash('Gunakan password yang berbeda dari password lama.', 'error')
        else:
            user.set_password(password)
            db.session.commit()

            flash('Password berhasil diubah. Silakan login.', 'success')
            return redirect(url_for('main.login'))

    return render_template(
    'loginRegister.html',
    mode='reset_password',
    token=token
)


# =========================================================
# HALAMAN ADMIN
# =========================================================
def admin_required(view_func):
    """Decorator: hanya user dengan role 'admin' yang boleh masuk."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') not in ('admin', 'superadmin'):
            flash('Anda tidak memiliki akses ke halaman ini!')
            return redirect(url_for('main.login'))
        return view_func(*args, **kwargs)
    return wrapper


def admin_context():
    """Data yang dipakai bersama oleh semua halaman admin (navbar & notifikasi)."""
    pending = (Rental.query
               .filter_by(status=Rental.STATUS_MENUNGGU)
               .order_by(Rental.created_at.desc())
               .all())
    return {
        'admin': User.query.get(session['user_id']),
        'pending_rentals': pending,
    }


@bp.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    today = date.today()

    # ---------- KARTU STATISTIK ----------
    total_vehicles = Vehicle.query.count()
    rented_vehicle_ids = {r.vehicle_id for r in
                          Rental.query.filter_by(status=Rental.STATUS_BERJALAN).all()}
    available_vehicles = total_vehicles - len(rented_vehicle_ids)

    running = Rental.query.filter_by(status=Rental.STATUS_BERJALAN).count()
    waiting = Rental.query.filter_by(status=Rental.STATUS_MENUNGGU).count()
    active_total = running + waiting

    new_today = (Rental.query
                 .filter(Rental.status == Rental.STATUS_MENUNGGU,
                         db.func.date(Rental.created_at) == today.isoformat())
                 .count())

    # ---------- TABEL PENYEWAAN TERBARU (search + pagination) ----------
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Rental.query.join(User).join(Vehicle)
    if q:
        pattern = f'%{q}%'
        query = query.filter(or_(
            Rental.booking_code.ilike(pattern),
            User.name.ilike(pattern),
            Vehicle.brand.ilike(pattern),
            Vehicle.model.ilike(pattern),
        ))

    pagination = query.order_by(Rental.created_at.desc()).paginate(
        page=page, per_page=5, error_out=False)

    return render_template(
        'admin/dashboard.html',
        active_menu='dashboard',
        total_vehicles=total_vehicles,
        available_vehicles=available_vehicles,
        active_total=active_total,
        running=running,
        waiting=waiting,
        new_today=new_today,
        pagination=pagination,
        q=q,
        statuses=Rental.ALL_STATUS,
        **admin_context()
    )




@bp.route('/admin/penyewaan/<int:rental_id>/status', methods=['POST'])
@admin_required
def admin_update_rental_status(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    new_status = request.form.get('status')

    if new_status not in Rental.ALL_STATUS:
        flash('Status tidak valid.')
        return redirect(
            request.referrer or url_for('main.admin_dashboard')
        )

    old_status = rental.change_status(new_status)

    if old_status:
        db.session.add(Notification.status_changed(rental, old_status))

        # Terbitkan notifikasi denda jika kendaraan dikembalikan terlambat
        if rental.fine_amount > 0 and new_status in [Rental.STATUS_PENGEMBALIAN, Rental.STATUS_SELESAI]:
            db.session.add(Notification.fine_issued(rental))

        db.session.commit()
        flash(f'Status {rental.booking_code} diubah menjadi "{new_status}".')
    else:
        flash('Status pesanan tidak mengalami perubahan.')

    return redirect(
        request.referrer or url_for('main.admin_dashboard')
    )



# =========================================================
# HALAMAN ADMIN: DAFTAR KENDARAAN
# =========================================================
@bp.route('/admin/kendaraan')
@admin_required
def admin_kendaraan():
    # ---------- KARTU STATISTIK ----------
    total_vehicles = Vehicle.query.count()
    rented_vehicle_ids = {r.vehicle_id for r in
                          Rental.query.filter_by(status=Rental.STATUS_BERJALAN).all()}

    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Vehicle.query
    if q:
        pattern = f'%{q}%'
        query = query.filter(or_(
            Vehicle.brand.ilike(pattern),
            Vehicle.model.ilike(pattern),
        ))

    pagination = query.order_by(Vehicle.id.desc()).paginate(
        page=page, per_page=5, error_out=False)
    
    return render_template(
        'admin/kendaraan_list.html',
        active_menu='kendaraan',
        total_vehicles=total_vehicles,
        rented_vehicle_ids=rented_vehicle_ids,
        pagination=pagination,
        q=q,
        statuses=Rental.ALL_STATUS,
        **admin_context()
    )

# =========================================================
# HALAMAN ADMIN: TAMBAH KENDARAAN
# =========================================================
@bp.route('/admin/kendaraan/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_kendaraan():
    if request.method == 'POST':
        foto = request.files.get('photo')
        filename = "default.png"
        if foto and foto.filename != '':
            filename = secure_filename(foto.filename)
            foto.save(os.path.join('app', 'static', 'images', filename))

        new_vehicle = Vehicle(
            photo=filename,
            brand=request.form.get('merek'),
            model=request.form.get('tipe'),
            year=request.form.get('tahun'),
            color=request.form.get('warna'),
            vehicle_number=request.form.get('plat_nomor'),
            rental_type=request.form.get('jenis_penyewaan'),
            fuel=request.form.get('bahan_bakar'),
            transmission=request.form.get('transmisi'),
            vehicle_type=request.form.get('kategori'),
            price_per_day=request.form.get('harga_sewa'),
            seats=request.form.get('jumlah_penumpang'),
            luggage=request.form.get('jumlah_bagasi'),
            chassis_number=request.form.get('no_rangka'),
            engine_number=request.form.get('no_mesin'),
            engine_cc=request.form.get('cc_mesin'),
            facilities=request.form.get('fasilitas'),
            is_active=True # Default aktif
        )
        db.session.add(new_vehicle)
        try:
            db.session.commit()
            flash('Kendaraan berhasil ditambahkan.')
            return redirect(url_for('main.admin_kendaraan'))
        except Exception as e:
            db.session.rollback()
            flash('Gagal menambahkan kendaraan. Pastikan Plat/Rangka/Mesin tidak duplikat.')
            
    return render_template('admin/kendaraan_tambah.html', active_menu='kendaraan', **admin_context())

# =========================================================
# HALAMAN ADMIN: EDIT KENDARAAN
# =========================================================
@bp.route('/admin/kendaraan/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_kendaraan(id):
    vehicle = Vehicle.query.get_or_404(id)
    
    if request.method == 'POST':
        foto = request.files.get('photo')
        if foto and foto.filename != '':
            filename = secure_filename(foto.filename)
            foto.save(os.path.join('app', 'static', 'images', filename))
            vehicle.photo = filename

        vehicle.brand = request.form.get('merek')
        vehicle.model = request.form.get('tipe')
        vehicle.year = request.form.get('tahun')
        vehicle.color = request.form.get('warna')
        vehicle.vehicle_number = request.form.get('plat_nomor')
        vehicle.rental_type = request.form.get('jenis_penyewaan')
        vehicle.fuel = request.form.get('bahan_bakar')
        vehicle.transmission = request.form.get('transmisi')
        vehicle.vehicle_type = request.form.get('kategori')
        vehicle.price_per_day = request.form.get('harga_sewa')
        vehicle.seats = request.form.get('jumlah_penumpang')
        vehicle.luggage = request.form.get('jumlah_bagasi')
        vehicle.chassis_number = request.form.get('no_rangka')
        vehicle.engine_number = request.form.get('no_mesin')
        vehicle.notes = request.form.get('catatan_kondisi')
        vehicle.engine_cc = request.form.get('cc_mesin')
        vehicle.facilities = request.form.get('fasilitas')
        
        # Checkbox aktif
        vehicle.is_active = True if request.form.get('is_active') else False

        try:
            db.session.commit()
            flash('Data kendaraan berhasil diperbarui.')
            return redirect(url_for('main.admin_kendaraan'))
        except Exception as e:
            db.session.rollback()
            flash('Gagal mengedit kendaraan. Data duplikat.')

    return render_template('admin/kendaraan_edit.html', active_menu='kendaraan', vehicle=vehicle, **admin_context())


@bp.route('/admin/penyewaan')
@admin_required
def admin_penyewaan():
    # Filter parameter
    status_filter = request.args.get('status', '')
    date_filter = request.args.get('tanggal', '')
    type_filter = request.args.get('tipe_kendaraan', '')
    page = request.args.get('page', 1, type=int)

    query = Rental.query.join(Vehicle)

    if status_filter:
        query = query.filter(Rental.status == status_filter)
    
    if type_filter:
        query = query.filter(Vehicle.vehicle_type == type_filter)
        
    if date_filter and ' - ' in date_filter:
        try:
            start_str, end_str = date_filter.split(' - ')
            start_date = datetime.strptime(start_str, '%d-%m-%Y').date()
            end_date = datetime.strptime(end_str, '%d-%m-%Y').date()
            query = query.filter(Rental.start_date >= start_date, Rental.start_date <= end_date)
        except ValueError:
            pass # Abaikan jika format salah

    pagination = query.order_by(Rental.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)

    return render_template(
        'admin/penyewaan_list.html',
        active_menu='penyewaan',
        pagination=pagination,
        status_filter=status_filter,
        date_filter=date_filter,
        type_filter=type_filter,
        statuses=Rental.ALL_STATUS,
        **admin_context()
    )


@bp.route('/admin/penyewaan/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def admin_penyewaan_edit(id):
    from app.models import Driver
    rental = Rental.query.get_or_404(id)
    drivers = Driver.query.filter_by(is_available=True).all()
    
    # Jika rental sudah punya sopir, pastikan sopirnya masuk ke list walaupun tidak available
    if rental.driver and rental.driver not in drivers:
        drivers.append(rental.driver)

    if request.method == 'POST':
        # Proses Tolak
        if 'btn_tolak' in request.form:
            old_status = rental.change_status(Rental.STATUS_BATAL)
            if old_status:
                db.session.add(Notification.status_changed(rental, old_status))
            db.session.commit()
            flash('Penyewaan berhasil ditolak/dibatalkan.')
            return redirect(url_for('main.admin_penyewaan'))
            
        # Proses Simpan
        new_status = request.form.get('status')
        driver_id = request.form.get('driver_id')

        old_status = rental.change_status(new_status)

        if old_status:
            db.session.add(Notification.status_changed(rental, old_status))

            # Terbitkan notifikasi denda jika kendaraan dikembalikan terlambat
            if rental.fine_amount > 0 and new_status in [Rental.STATUS_PENGEMBALIAN, Rental.STATUS_SELESAI]:
                db.session.add(Notification.fine_issued(rental))

        if rental.with_driver and driver_id:
            if driver_id == 'none':
                rental.driver_id = None
            else:
                rental.driver_id = int(driver_id)

        # Opsi pelunasan denda oleh admin
        if 'fine_paid' in request.form:
            rental.fine_paid = (request.form.get('fine_paid') == '1')
                
        db.session.commit()
        flash('Data penyewaan berhasil diperbarui.')
        return redirect(url_for('main.admin_penyewaan'))

    return render_template(
        'admin/penyewaan_edit.html',
        active_menu='penyewaan',
        rental=rental,
        statuses=Rental.ALL_STATUS,
        drivers=drivers,
        **admin_context()
    )


@bp.route('/admin/pelanggan')
@admin_required
def admin_pelanggan():
    return render_template('admin/placeholder.html', active_menu='pelanggan',
                           title='Pelanggan', icon='fa-users', **admin_context())

ALLOWED_IMG_EXT = {'jpg', 'jpeg', 'png', 'webp'}

# =========================================================
# KELOLA PELANGGAN (admin_bp)  &  KELOLA ADMIN (superadmin_bp)
# =========================================================
import re
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from app.models import Customer, Admin

admin_bp = Blueprint('kelola_pelanggan', __name__, url_prefix='/admin/kelola-pelanggan')
superadmin_bp = Blueprint('kelola_admin', __name__, url_prefix='/superadmin/kelola-admin')


# ---------- PENJAGA AKSES ----------
def superadmin_required(view_func):
    """Decorator: hanya role 'superadmin'. (Untuk Admin biasa & Super Admin pakai admin_required.)"""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'superadmin':
            flash('Anda tidak memiliki akses ke halaman ini!')
            return redirect(url_for('main.login'))
        return view_func(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------
# [OOP - ABSTRAKSI & ENKAPSULASI: GUARD / INTERCEPTOR PATTERN]
# Mengenkapsulasi aturan validasi status akun aktif/nonaktif pada level
# middleware/request interceptor tanpa mengotori setiap fungsi view.
# ---------------------------------------------------------
class AccountStatusGuard:
    """
    Menegakkan status akun (aktif / nonaktif) di SETIAP request:
      - Admin / Super Admin nonaktif -> otomatis dikeluarkan (logout).
      - Pelanggan nonaktif           -> tidak boleh membuka halaman penyewaan.
    """
    STAFF_ROLES = ('admin', 'superadmin')
    EXEMPT_ENDPOINTS = ('static', 'main.login', 'main.logout')
    RENTAL_ENDPOINTS = ('main.pesanan',)

    @classmethod
    def check(cls):
        user_id = session.get('user_id')
        if not user_id or request.endpoint is None or request.endpoint in cls.EXEMPT_ENDPOINTS:
            return None

        user = db.session.get(User, user_id)
        if user is None or user.is_active:
            return None

        if user.role in cls.STAFF_ROLES:
            session.clear()
            flash('Akun admin Anda dinonaktifkan. Hubungi Super Admin.')
            return redirect(url_for('main.login'))

        if request.endpoint in cls.RENTAL_ENDPOINTS:
            flash('Akun Anda dinonaktifkan sehingga tidak dapat menyewa kendaraan. Hubungi admin.')
            return redirect(url_for('main.index'))
        return None


# Dijalankan di setiap request setelah admin_bp terdaftar
admin_bp.before_app_request(AccountStatusGuard.check)


# ---------- SERVICE (logika bisnis, berbasis class) ----------

# [OOP - PEWARISAN / INHERITANCE: CUSTOM EXCEPTION]
# Mewarisi kelas Exception bawaan Python untuk menangani kegagalan validasi form.
class ValidationError(Exception):
    """Dilempar saat input form tidak valid. `messages` berisi daftar pesan."""
    def __init__(self, messages):
        super().__init__('; '.join(messages))
        self.messages = messages


# [OOP - ABSTRAKSI: TEMPLATE DESIGN PATTERN & BASE SERVICE]
# Kelas abstrak layanan yang menyediakan operasi standar (search, paginate, find,
# get_or_404, set_active). Atribut 'model' diisi secara dinamis oleh kelas turunan.
class BaseUserService:
    """Logika umum: daftar -> cari -> pilih -> ubah status."""
    model = None            # diisi oleh kelas turunan
    PER_PAGE = 8

    def base_query(self):
        return self.model.query.filter(self.model.role == self.model.ROLE)

    def search(self, keyword, page):
        """Pencarian (nama / email / no. HP / kode ID seperti PLG001) + pagination."""
        query = self.base_query()
        keyword = (keyword or '').strip()
        if keyword:
            pattern = f'%{keyword}%'
            conditions = [
                self.model.name.ilike(pattern),
                self.model.email.ilike(pattern),
                self.model.phone.ilike(pattern),
            ]
            digits = ''.join(ch for ch in keyword if ch.isdigit())
            if digits and keyword.upper().startswith(self.model.CODE_PREFIX):
                conditions.append(self.model.id == int(digits))
            query = query.filter(or_(*conditions))
        return query.order_by(self.model.id).paginate(
            page=page, per_page=self.PER_PAGE, error_out=False)

    def find(self, user_id):
        """Ambil satu data, atau None kalau tidak ada / id kosong."""
        if not user_id:
            return None
        return self.base_query().filter(self.model.id == user_id).first()

    def get_or_404(self, user_id):
        return self.base_query().filter(self.model.id == user_id).first_or_404()

    def set_active(self, user, active):
        user.is_active = bool(active)
        db.session.commit()
        return user


# [OOP - PEWARISAN / INHERITANCE]:
# Mewarisi BaseUserService dan mengarahkan 'model' ke class Customer.
class CustomerService(BaseUserService):
    model = Customer

    # Menambahkan method spesifik untuk riwayat sewa pelanggan
    def rental_history(self, customer):
        return customer.rental_history


# [OOP - PEWARISAN & ENKAPSULASI LOGIKA BISNIS]:
# Mewarisi BaseUserService dan mengarahkan 'model' ke class Admin,
# sekaligus mengenkapsulasi validasi pendaftaran dan upload foto admin.
class AdminService(BaseUserService):
    model = Admin

    EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    PHONE_RE = re.compile(r'^\+?\d{10,15}$')
    MIN_PASSWORD = 8
    ALLOWED_PHOTO_EXT = {'jpg', 'jpeg', 'png', 'webp'}

    # Kolom wajib (NOT NULL) milik User yang tidak ada di form "Tambah Admin"
    DEFAULT_BIRTH_DATE = date(2000, 1, 1)
    DEFAULT_GENDER = '-'

    def create(self, form, photo=None):
        """Validasi form lalu buat akun admin baru. Return objek Admin."""
        name = (form.get('name') or '').strip()
        email = (form.get('email') or '').strip()
        phone = (form.get('phone') or '').strip()
        password = form.get('password') or ''
        confirm = form.get('confirm_password') or ''

        errors = []
        if not name:
            errors.append('Nama lengkap wajib diisi.')
        if not self.EMAIL_RE.match(email):
            errors.append('Email tidak valid (contoh: nama@domain.com).')
        elif User.query.filter(db.func.lower(User.email) == email.lower()).first():
            errors.append('Email sudah terdaftar.')
        if not self.PHONE_RE.match(phone):
            errors.append('Nomor HP harus berupa angka 10-15 digit.')
        if len(password) < self.MIN_PASSWORD:
            errors.append(f'Password minimal {self.MIN_PASSWORD} karakter.')
        elif password != confirm:
            errors.append('Konfirmasi password tidak cocok.')

        photo_ext = None
        if photo and photo.filename:
            photo_ext = photo.filename.rsplit('.', 1)[-1].lower() if '.' in photo.filename else ''
            if photo_ext not in self.ALLOWED_PHOTO_EXT:
                errors.append('Foto profil harus berformat JPG, JPEG, PNG, atau WEBP.')

        if errors:
            raise ValidationError(errors)

        filename = self._save_photo(photo, photo_ext) if photo_ext else None
        new_admin = Admin(
            name=name, email=email, phone=phone, emergency_phone=phone,
            birth_date=self.DEFAULT_BIRTH_DATE, gender=self.DEFAULT_GENDER,
            role=Admin.ROLE, is_active=True, profile_photo=filename,
        )
        new_admin.set_password(password)

        try:
            db.session.add(new_admin)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            self._delete_photo(filename)
            raise ValidationError(['Email sudah terdaftar.'])
        return new_admin

    # ---------- penyimpanan foto profil ----------
    @staticmethod
    def _photo_folder():
        return os.path.join(current_app.root_path, 'static', 'uploads', 'profil')

    def _save_photo(self, file_storage, ext):
        folder = self._photo_folder()
        os.makedirs(folder, exist_ok=True)
        filename = secure_filename(f"admin_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{ext}")
        file_storage.save(os.path.join(folder, filename))
        return filename

    def _delete_photo(self, filename):
        if filename:
            path = os.path.join(self._photo_folder(), filename)
            if os.path.exists(path):
                os.remove(path)


# ---------- CONTROLLER ADMIN: halaman Pelanggan (admin_bp) ----------

# [OOP - PEWARISAN & CLASS-BASED VIEWS (MethodView)]:
# Mewarisi MethodView dari Flask untuk menstrukturkan handler HTTP (GET)
# ke dalam method objek.
# [OOP - ASOSIASI / KOMPOSISI]: Menggunakan objek CustomerService() untuk delegasi bisnis logic.
class PelangganListView(MethodView):
    """Daftar pelanggan + (jika dipilih) detail, dokumen, dan riwayat penyewaan."""
    decorators = [admin_required]
    service = CustomerService()

    def get(self):
        keyword = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        selected = self.service.find(request.args.get('id', type=int))

        return render_template(
            'admin/pelanggan.html',
            active_menu='pelanggan',
            pagination=self.service.search(keyword, page),
            selected=selected,
            rentals=self.service.rental_history(selected) if selected else [],
            keyword=keyword,
            **admin_context()
        )


# [OOP - PEWARISAN (MethodView)]: Menangani HTTP POST status pelanggan
class PelangganStatusView(MethodView):
    """Simpan perubahan status akun pelanggan (aktif / nonaktif)."""
    decorators = [admin_required]
    service = CustomerService()

    def post(self, user_id):
        customer = self.service.get_or_404(user_id)
        active = request.form.get('is_active') == '1'
        self.service.set_active(customer, active)
        flash(f"Status akun {customer.name} diubah menjadi "
              f"{'Aktif' if active else 'Tidak Aktif'}.")
        return redirect(url_for(
            'kelola_pelanggan.daftar',
            id=customer.id,
            page=request.form.get('page', 1, type=int),
            q=request.form.get('q') or None,
        ))


admin_bp.add_url_rule('/', view_func=PelangganListView.as_view('daftar'))
admin_bp.add_url_rule('/<int:user_id>/status',
                      view_func=PelangganStatusView.as_view('ubah_status'),
                      methods=['POST'])


# ---------- CONTROLLER SUPER ADMIN: halaman Admin (superadmin_bp) ----------

# [OOP - PEWARISAN & KOMPOSISI (MethodView + AdminService)]:
# Menangani halaman daftar admin dengan delegasi query ke AdminService()
class AdminListView(MethodView):
    """Daftar admin + detail admin yang dipilih."""
    decorators = [superadmin_required]
    service = AdminService()

    def get(self):
        keyword = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)

        return render_template(
            'admin/admin_list.html',
            active_menu='admin',
            pagination=self.service.search(keyword, page),
            selected=self.service.find(request.args.get('id', type=int)),
            keyword=keyword,
            **admin_context()
        )


# [OOP - PEWARISAN (MethodView)]: Menangani mutasi status admin via HTTP POST
class AdminStatusView(MethodView):
    """Simpan perubahan status akun admin (aktif / nonaktif)."""
    decorators = [superadmin_required]
    service = AdminService()

    def post(self, user_id):
        target = self.service.get_or_404(user_id)
        active = request.form.get('is_active') == '1'
        self.service.set_active(target, active)
        flash(f"Status akun {target.name} diubah menjadi "
              f"{'Aktif' if active else 'Tidak Aktif'}.")
        return redirect(url_for(
            'kelola_admin.daftar',
            id=target.id,
            page=request.form.get('page', 1, type=int),
            q=request.form.get('q') or None,
        ))


# [OOP - PEWARISAN (MethodView)]: Form Tambah Admin dengan method GET dan POST terpisah
class AdminCreateView(MethodView):
    """Form Tambah Admin Baru."""
    decorators = [superadmin_required]
    service = AdminService()

    def _render(self, errors=None):
        return render_template(
            'admin/admin_tambah.html',
            active_menu='admin',
            errors=errors or [],
            form=request.form,
            **admin_context()
        )

    def get(self):
        return self._render()

    def post(self):
        try:
            new_admin = self.service.create(request.form, request.files.get('foto_profil'))
        except ValidationError as error:
            return self._render(error.messages)
        flash(f'Akun admin {new_admin.name} berhasil ditambahkan.')
        return redirect(url_for('kelola_admin.daftar', id=new_admin.id))


superadmin_bp.add_url_rule('/', view_func=AdminListView.as_view('daftar'))
superadmin_bp.add_url_rule('/<int:user_id>/status',
                           view_func=AdminStatusView.as_view('ubah_status'),
                           methods=['POST'])
superadmin_bp.add_url_rule('/tambah', view_func=AdminCreateView.as_view('tambah'),
                           methods=['GET', 'POST'])




def _save_driver_file(file_storage, prefix):
    """Simpan foto sopir / SIM ke static/uploads/sopir. Return nama file, atau None."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMG_EXT:
        return None
    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'sopir')
    os.makedirs(folder, exist_ok=True)
    filename = secure_filename(f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.{ext}")
    file_storage.save(os.path.join(folder, filename))
    return filename


def _delete_driver_file(filename):
    if filename and filename != 'default_driver.png':
        path = os.path.join(current_app.root_path, 'static', 'uploads', 'sopir', filename)
        if os.path.exists(path):
            os.remove(path)


# ---------- DAFTAR SOPIR ----------
@bp.route('/admin/sopir')
@admin_required
def admin_sopir():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Driver.query
    if q:
        pola = f'%{q}%'
        query = query.filter(or_(Driver.name.ilike(pola), Driver.phone.ilike(pola)))
    pagination = query.order_by(Driver.id).paginate(page=page, per_page=5, error_out=False)

    semua = Driver.query.all()
    hitung = lambda label: sum(1 for d in semua if d.status_label == label)

    return render_template(
        'admin/sopir_list.html',
        active_menu='sopir',
        pagination=pagination,
        q=q,
        total_tersedia=hitung('Tersedia'),
        total_berjalan=hitung('Berjalan'),
        total_menunggu=hitung('Menunggu Konfirmasi'),
        **admin_context()
    )


# ---------- TAMBAH SOPIR ----------
@bp.route('/admin/sopir/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_sopir():
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        telepon = request.form.get('telepon', '').strip()
        if not nama or not telepon:
            flash('Nama dan No. Handphone wajib diisi.')
            return render_template('admin/sopir_tambah.html', active_menu='sopir',
                                   f=request.form, **admin_context())

        sopir = Driver(
            name=nama,
            phone=telepon,
            address=request.form.get('alamat', '').strip(),
            description=request.form.get('deskripsi', '').strip(),
            photo=_save_driver_file(request.files.get('foto_sopir'), 'foto') or 'default_driver.png',
            sim_photo=_save_driver_file(request.files.get('foto_sim'), 'sim'),
        )
        db.session.add(sopir)
        db.session.commit()
        flash(f'Sopir {nama} berhasil ditambahkan.')
        return redirect(url_for('main.admin_sopir'))

    return render_template('admin/sopir_tambah.html', active_menu='sopir', f={}, **admin_context())


# ---------- PROFIL + STATUS SOPIR ----------
@bp.route('/admin/sopir/<int:id>')
@admin_required
def admin_sopir_detail(id):
    sopir = Driver.query.get_or_404(id)
    rentals = (Rental.query.filter_by(driver_id=id)
               .order_by(Rental.created_at.desc()).all())
    return render_template(
        'admin/sopir_detail.html',
        active_menu='sopir',
        driver=sopir,
        rentals=rentals,
        status_menunggu=Rental.STATUS_MENUNGGU_KONFIRMASI,
        status_verifikasi=Rental.STATUS_PENGAMBILAN,   # status tujuan setelah tombol Verifikasi
        status_batal=Rental.STATUS_BATAL,
        **admin_context()
    )


# ---------- PECAT (HAPUS) SOPIR ----------
@bp.route('/admin/sopir/<int:id>/pecat', methods=['POST'])
@admin_required
def pecat_sopir(id):
    sopir = Driver.query.get_or_404(id)
    if sopir.current_rental:
        flash('Sopir masih memiliki penyewaan aktif, selesaikan atau ganti sopirnya dulu.')
        return redirect(url_for('main.admin_sopir_detail', id=id))

    nama = sopir.name
    _delete_driver_file(sopir.photo)
    _delete_driver_file(sopir.sim_photo)
    db.session.delete(sopir)   # rental lama otomatis dilepas (driver_id jadi NULL)
    db.session.commit()
    flash(f'Sopir {nama} telah dipecat.')
    return redirect(url_for('main.admin_sopir'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date = request.form.get('birth_date')
        gender = request.form.get('gender')
        email = request.form.get('email')
        phone = request.form.get('phone')
        emergency_phone = request.form.get('emergency_phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Konfirmasi password tidak cocok.')
            return redirect(url_for('main.register'))

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Email sudah terdaftar.')
            return redirect(url_for('main.register'))

        user = User(
            name=name,
            birth_date=datetime.strptime(birth_date, '%Y-%m-%d').date(),
            gender=gender,
            email=email,
            phone=phone,
            emergency_phone=emergency_phone
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Registrasi berhasil. Silakan login.')
        return redirect(url_for('main.login'))

    return render_template('loginRegister.html', mode='register')

@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('user_role', None)
    flash('Kamu berhasil logout.', 'success')
    return redirect(url_for('main.login'))







# =========================================================
# HALAMAN ADMIN: LIVE TRACKING
# =========================================================
@bp.route('/admin/tracking')
@admin_required
def admin_tracking():
    focus_vehicle = request.args.get('vehicle_id', type=int)
    return render_template(
        'admin/tracking.html',
        active_menu='tracking',
        focus_vehicle=focus_vehicle,
        **admin_context()
    )

import random
from flask import jsonify

@bp.route('/api/live-tracking')
@admin_required
def api_live_tracking():
    # Ambil semua rental yang sedang dipakai
    active_rentals = Rental.query.filter_by(status=Rental.STATUS_DIPAKAI).all()
    
    data = []
    for r in active_rentals:
        v = r.vehicle
        if v.current_lat is not None and v.current_lng is not None:
            # Sihir Simulasi: Geser posisi mobil sedikit secara acak
            # 0.0001 derajat = sekitar 11 meter di dunia nyata
            v.current_lat += random.uniform(-0.0001, 0.0001)
            v.current_lng += random.uniform(-0.0001, 0.0001)
            
            data.append({
                'rental_id': r.id,
                'vehicle_id': v.id,
                'booking_code': r.booking_code,
                'customer_name': r.user.name,
                'vehicle_name': f"{v.brand} {v.model} ({v.vehicle_number})",
                'driver_name': r.driver.name if r.with_driver and r.driver else "Tanpa Sopir",
                'lat': v.current_lat,
                'lng': v.current_lng
            })
            
    # Simpan pergeseran kordinat ke database
    db.session.commit()
    return jsonify(data)
