# ═════════════════════════════════════════════════════════════
#     ROUTES DAN LOGIKA WEBSITE KeSanaSini (routes.py)
#
#     ⤷ Mengatur URL atau halaman yang dapat diakses pengguna.
#     ⤷ Menghubungkan halaman HTML dengan data dari models.py.
#     ⤷ Memproses formulir, memvalidasi input, dan mengelola session.
#     ⤷ Menjalankan proses pemesanan, pembayaran, pembatalan, pengelolaan akun, serta notifikasi.
#     ⤷ Menggunakan Flask Blueprint untuk mengelompokkan route.
# ═════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════
#   IMPORT LIBRARY DAN MODEL
# ═════════════════════════════════════════════════════════════
# Mengimpor fungsi Flask untuk membuat halaman, membaca input,
# mengatur pengalihan halaman, session, dan respons JSON.
from flask import jsonify, Blueprint, render_template, request, redirect, url_for, flash, session, current_app
# Mengimpor model database yang digunakan dalam proses website.
from app.models import (
    User, Vehicle, Rental, RentalCancellation, Review, Driver, Notification)
# Mengimpor fungsi untuk pencarian dengan beberapa kondisi.
from sqlalchemy import or_
# Mengimpor fungsi pengelolaan tanggal dan waktu.
from datetime import datetime, date, timedelta
# Mengamankan nama file yang diunggah pengguna.
from werkzeug.utils import secure_filename
# Mengelola data formulir dalam bentuk MultiDict.
from werkzeug.datastructures import MultiDict
# Mengimpor wraps untuk mempertahankan informasi fungsi decorator.
from functools import wraps
# Mengimpor database dan OAuth dari aplikasi.
from app import db, oauth
# Mengelola token bertanda tangan dan memeriksa masa berlakunya.
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
# Mengelola operasi file dan folder.
import os
import shutil
# Membuat ID unik dan menangani pengiriman email.
import uuid
import smtplib
import ssl
from email.message import EmailMessage
# Mengamankan teks HTML dari karakter yang berpotensi berbahaya.
from html import escape



# ═════════════════════════════════════════════════════════════
#   MEMBUAT BLUEPRINT
# ═════════════════════════════════════════════════════════════
# Blueprint digunakan untuk mengelompokkan route utama website.
bp = Blueprint('main', __name__)



# ═════════════════════════════════════════════════════════════
#   PEMERIKSAAN NOTIFIKASI OTOMATIS
# ═════════════════════════════════════════════════════════════
# Decorator ini menjalankan pemeriksaan sebelum request diproses.
@bp.before_app_request
def periksa_notifikasi_otomatis():
    """Memeriksa notifikasi otomatis pada setiap request non-statis."""
    if request.endpoint == 'static' or (
        request.endpoint and request.endpoint.endswith('.static')
    ):
        return

    try:
        # Memeriksa pengingat dan denda secara otomatis.
        periksa_pengingat_dan_denda()
    except Exception:
        # Membatalkan perubahan database jika terjadi kesalahan
        # dan mencatat detail kesalahan ke log aplikasi.
        db.session.rollback()
        current_app.logger.exception(
            'Gagal memproses notifikasi otomatis KeSanaSini.'
        )



# ═════════════════════════════════════════════════════════════
#   KONSTANTA DAN FUNGSI PENGATURAN WAKTU
# ═════════════════════════════════════════════════════════════
# Daftar nama bulan untuk menampilkan tanggal dalam Bahasa Indonesia.
BULAN_ID = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli',
            'Agustus', 'September', 'Oktober', 'November', 'Desember']

# Minimal waktu antara pemesanan dan pengambilan kendaraan adalah 25 jam.
MINIMUM_JAM_SEBELUM_PENGAMBILAN = 25

# Menghasilkan waktu paling awal kendaraan boleh diambil.
def waktu_minimum_pengambilan():
    """Waktu paling awal kendaraan boleh diambil."""
    return datetime.now() + timedelta(
        hours=MINIMUM_JAM_SEBELUM_PENGAMBILAN
    )

# Membulatkan waktu ke menit berikutnya jika masih memiliki detik.
def bulatkan_ke_menit_berikutnya(waktu):
    """Bulatkan ke menit berikutnya untuk input tanggal dan jam."""
    if waktu.second or waktu.microsecond:
        waktu = waktu.replace(
            second=0,
            microsecond=0
        ) + timedelta(minutes=1)

    return waktu.replace(second=0, microsecond=0)

# Menentukan jadwal pengambilan default untuk formulir.
def waktu_default_pengambilan():
    """Jadwal bawaan agar pengguna punya waktu mengisi formulir."""
    return bulatkan_ke_menit_berikutnya(
        datetime.now() + timedelta(hours=26)
    )

# Menggabungkan tanggal dan jam dari input menjadi objek datetime.
# Jika format tidak valid, fungsi mengembalikan None.
def parse_waktu_pengambilan(tanggal, jam):
    """Gabungkan tanggal dan jam pilihan menjadi satu datetime."""
    try:
        return datetime.strptime(
            f'{tanggal} {jam}',
            '%Y-%m-%d %H:%M'
        )
    except (TypeError, ValueError):
        return None



# ═════════════════════════════════════════════════════════════
#   FILTER TEMPLATE
# ═════════════════════════════════════════════════════════════

# Mendaftarkan filter rupiah agar dapat digunakan pada template HTML.
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




# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#
#                                                   PENGATURAN USER
#
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


# ═════════════════════════════════════════════════════════════
#   HALAMAN OPENING
# ═════════════════════════════════════════════════════════════
# Route untuk menampilkan halaman pembuka website.
@bp.route('/')
def welcome():
    return render_template('welcome.html')



# ═════════════════════════════════════════════════════════════
#   HALAMAN UTAMA USER
# ═════════════════════════════════════════════════════════════
# Menampilkan halaman utama setelah pengguna berhasil login.
@bp.route('/home')
def index():

    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    # Mengambil data pengguna yang sedang login dari database.
    user = User.query.get(session['user_id'])

    vehicles = Vehicle.query.all()

    now = waktu_default_pengambilan()

    current_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M')


    return render_template(
        'user/halUtamaUser.html',
        vehicles=vehicles,
        user=user,
        current_date=current_date,
        current_time=current_time
    )



# ═════════════════════════════════════════════════════════════
#   HALAMAN PENCARIAN KENDARAAN
# ═════════════════════════════════════════════════════════════
# Memproses pencarian kendaraan berdasarkan jadwal, jenis, dan harga.
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

    minimum_pickup = waktu_minimum_pengambilan()

    # Jika pencarian dibuka tanpa tanggal dan jam,
    # gunakan waktu minimum.
    if not pickup_date_str and not pickup_time:
        selected_pickup = waktu_default_pengambilan()
    else:
        selected_pickup = parse_waktu_pengambilan(
            pickup_date_str,
            pickup_time
        )

        if selected_pickup is None:
            flash(
                'Tanggal dan jam pengambilan tidak valid.',
                'error'
            )
            return redirect(url_for('main.index'))

        if selected_pickup < minimum_pickup:
            flash(
                'Pengambilan kendaraan harus dijadwalkan '
                'minimal 25 jam dari waktu pemesanan.',
                'error'
            )
            return redirect(
                request.referrer or url_for('main.index')
            )

    start_date = selected_pickup.date()
    pickup_time = selected_pickup.strftime('%H:%M')

    # Tentukan tanggal pengembalian.
    end_date = start_date + timedelta(days=duration)

    # Format tanggal untuk ditampilkan.
    pickup_date = start_date.strftime('%d %B %Y')
    return_date = end_date.strftime('%d %B %Y')
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



# ═════════════════════════════════════════════════════════════
#   DETAIL KENDARAAN DAN ULASAN
# ═════════════════════════════════════════════════════════════
# Menampilkan detail kendaraan, jadwal sewa, harga, dan ulasan.
@bp.route('/detail-kendaraan/<int:vehicle_id>')
def detail_kendaraan(vehicle_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    from_page = request.args.get('from_page', 'search')

    if from_page not in ('home', 'search'):
        from_page = 'search'

    # Data pencarian dibawa dari halaman sebelumnya lewat URL
    date_str = request.args.get('date')
    time_str = request.args.get('time')
    duration = request.args.get('duration', type=int) or 1
    duration = max(1, min(duration, 7))

    # Jika dibuka tanpa jadwal, gunakan waktu minimum yang baru.
    if not date_str:
        selected_pickup = waktu_default_pengambilan()
    else:
        selected_pickup = parse_waktu_pengambilan(
            date_str,
            time_str or '10:00'
        )

        if selected_pickup is None:
            flash('Tanggal dan jam pengambilan tidak valid.', 'error')
            return redirect(url_for('main.index'))

    pickup_date = selected_pickup.date()
    pickup_time = selected_pickup.strftime('%H:%M')

    end_date = pickup_date + timedelta(days=duration)
    total = vehicle.price_per_day * duration

    try:
        pickup_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pickup_date = date.today()

    end_date = pickup_date + timedelta(days=duration)
    total = vehicle.price_per_day * duration

    # Cek ketersediaan kendaraan pada tanggal yang dipilih.
    # Semua status aktif yang belum selesai atau batal
    # harus memblokir kendaraan jika jadwalnya bertabrakan.
    bentrok = Rental.query.filter(
        Rental.vehicle_id == vehicle.id,
        Rental.status.in_([
            Rental.STATUS_MENUNGGU_BAYAR,
            Rental.STATUS_MENUNGGU_KONFIRMASI,
            Rental.STATUS_PENGAMBILAN,
            Rental.STATUS_DIPAKAI,
            Rental.STATUS_PENGEMBALIAN,
        ]),
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
        reviews=reviews,
        from_page=from_page
    )

@bp.route('/kendaraan/<int:vehicle_id>/ulasan')
def semua_ulasan(vehicle_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    vehicle = Vehicle.query.get_or_404(vehicle_id)
    star = request.args.get('star', type=int)

    return redirect(url_for('main.detail_kendaraan', vehicle_id=vehicle.id, ulasan=1, star=star))



# ═════════════════════════════════════════════════════════════
#   KONSTANTA FORMULIR PENYEWAAN
# ═════════════════════════════════════════════════════════════
# Pilihan tujuan penggunaan kendaraan.
PURPOSES = ['Liburan', 'Dinas / Bisnis', 'Acara keluarga', 'Pernikahan', 'Lainnya']
REGIONS = ['Dalam kota', 'Luar kota']
LOCATIONS = ['Kantor rental', 'Bandara SAMS Sepinggan']
ALLOWED_DOC_EXT = {'jpg', 'jpeg', 'png', 'pdf'}
ALASAN_PEMBATALAN_USER = [
    'Ingin mengubah rincian dan membuat pesanan baru',
    'Kendaraan memiliki ulasan yang kurang baik (Detail kendaraan kurang sesuai, pengalaman pelanggan berbeda, dan lainnya).',
    'Menemukan alternatif rental lain.',
    'Pesanan dibuat secara tidak sengaja.',
    'Alasan lainnya (Berubah pikiran, rencana perjalanan berubah atau dibatalkan, dan lainnya).'
]



# ═════════════════════════════════════════════════════════════
#   FUNGSI BANTUAN PEMBATALAN DAN DOKUMEN
# ═════════════════════════════════════════════════════════════
# [OOP - ABSTRAKSI & INSPEKSI RIWAYAT OBJEK]
# Memeriksa apakah objek Rental sudah dibayar berdasarkan atribut payment_status,
# status pesanan aktif, maupun koleksi objek riwayat status (status_history).
def _rental_sudah_dibayar(rental, status_sebelum=None):
    """
    Menentukan apakah pesanan sudah dibayar.
    Status lama ikut diperiksa untuk membantu data lama yang
    payment_status-nya belum konsisten.
    """
    status = status_sebelum or rental.status

    status_yang_menandakan_pembayaran = [
        Rental.STATUS_MENUNGGU_KONFIRMASI,
        Rental.STATUS_PENGAMBILAN,
        Rental.STATUS_DIPAKAI,
        Rental.STATUS_PENGEMBALIAN,
        Rental.STATUS_SELESAI
    ]

    riwayat_pernah_bayar = any(
        (h.old_status in status_yang_menandakan_pembayaran)
        or (h.new_status in status_yang_menandakan_pembayaran)
        for h in (rental.status_history or [])
    )

    return (
        rental.payment_status == 'Lunas'
        or status in status_yang_menandakan_pembayaran
        or riwayat_pernah_bayar
    )


# [OOP - ENKAPSULASI QUERY OBJEK]
# Mengambil pengajuan pembatalan pelanggan yang masih menunggu keputusan admin.
def _permohonan_pembatalan_pending(rental_id):
    """Mengambil permohonan pelanggan yang masih menunggu keputusan admin."""
    return (
        RentalCancellation.query
        .filter_by(
            rental_id=rental_id,
            initiated_by='customer',
            status=RentalCancellation.STATUS_DIAJUKAN
        )
        .order_by(RentalCancellation.id.desc())
        .first()
    )


# [OOP - INSTANSIASI OBJEK & RELASI ASOSIASI]
# Membuat catatan pembatalan dan pengembalian dana (objek RentalCancellation)
# untuk pesanan yang sudah dibayar lalu dibatalkan langsung oleh admin.
def _catat_pembatalan_admin_berbayar(
    rental,
    reason,
    waktu_batal
):
    """
    Membuat catatan refund saat admin langsung membatalkan
    pesanan yang sudah dibayar.
    """
    existing = rental.latest_cancellation
    if existing and existing.needs_refund:
        existing.reason = reason or existing.reason or 'Dibatalkan oleh Admin.'
        return existing

    pembatalan = RentalCancellation(
        rental_id=rental.id,
        reason=reason or 'Dibatalkan oleh Admin.',
        initiated_by='admin',
        status=RentalCancellation.STATUS_MENUNGGU_REFUND,
        requested_at=None,
        cancelled_at=waktu_batal,
        refund_amount=rental.total_price
    )

    db.session.add(pembatalan)
    return pembatalan


# [OOP - ENKAPSULASI]
# Membatalkan pesanan langsung oleh admin, termasuk pembatalan pesanan yang sudah dibayar.
# Jika pesanan sudah dibayar, catatan refund akan dibuat agar admin dapat memproses pengembalian dana.
def _batalkan_oleh_admin(rental, reason):
    """Satu-satunya pintu pembatalan langsung oleh admin."""
    reason = (reason or '').strip()[:500]
    rental.cancellation_reason = (
        reason or rental.cancellation_reason or 'Dibatalkan oleh Admin.'
    )
    sudah_dibayar = _rental_sudah_dibayar(rental, rental.status)

    old_status = rental.change_status(Rental.STATUS_BATAL)
    if not old_status:
        return False

    waktu_batal = (
        rental.status_history[-1].changed_at
        if rental.status_history else datetime.now()
    )
    db.session.add(
        Notification.status_changed(rental, old_status, cancelled_by='admin')
    )

    if sudah_dibayar:
        _catat_pembatalan_admin_berbayar(
            rental, rental.cancellation_reason, waktu_batal
        )
    elif not rental.latest_cancellation:
        db.session.add(RentalCancellation(
            rental_id=rental.id,
            reason=rental.cancellation_reason,
            initiated_by='admin',
            status=RentalCancellation.STATUS_DIAJUKAN,
            requested_at=waktu_batal,
            cancelled_at=waktu_batal,
            refund_amount=None
        ))
    return True


# Memvalidasi dan menyimpan dokumen KTP atau SIM ke folder dokumen.
# Nama file diamankan sebelum digunakan untuk penyimpanan.
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


# Menghubungkan KTP/SIM dari Kelola Akun ke Form Sewa
ACCOUNT_DOC_FOLDER = os.path.join('static', 'uploads', 'dokumen_akun')


def _account_doc_exists(filename):
    """True kalau user punya dokumen di Kelola Akun dan file-nya benar-benar ada."""
    if not filename:
        return False
    path = os.path.join(current_app.root_path, ACCOUNT_DOC_FOLDER, filename)
    return os.path.exists(path)


def _copy_account_document(account_file, booking_code, kind):
    """Salin KTP/SIM dari Kelola Akun ke dokumen pesanan. Return nama file baru."""
    if not _account_doc_exists(account_file):
        return None
    src = os.path.join(current_app.root_path, ACCOUNT_DOC_FOLDER, account_file)
    ext = account_file.rsplit('.', 1)[-1].lower()

    folder = os.path.join(current_app.root_path, 'static', 'uploads', 'dokumen')
    os.makedirs(folder, exist_ok=True)

    filename = secure_filename(f"{booking_code}_{kind}.{ext}")
    shutil.copyfile(src, os.path.join(folder, filename))
    return filename



# ═════════════════════════════════════════════════════════════
#   FORM DAN PROSES PEMESANAN KENDARAAN
# ═════════════════════════════════════════════════════════════
# Menampilkan formulir sewa dan memproses data ketika formulir dikirim.
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
    tipe = vehicle.vehicle_type.lower()
    accessories_avail = {k: v for k, v in Rental.ACCESSORIES.items()
                        if tipe in Rental.ACCESSORY_TYPES.get(k, [])}

    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    if not user:
        return redirect(url_for('main.login'))

    has_ktp = _account_doc_exists(user.ktp_file)
    has_sim = _account_doc_exists(user.sim_file)
    
    # Ambil data tanggal dan jam pengambilan.
    tanggal_str = request.args.get('date')
    jam_str = request.args.get('time')

    if not tanggal_str and not jam_str:
        selected_pickup = waktu_default_pengambilan()
    else:
        selected_pickup = parse_waktu_pengambilan(
            tanggal_str,
            jam_str
        )

        if selected_pickup is None:
            flash(
                'Tanggal dan jam pengambilan tidak valid.',
                'error'
            )
            return redirect(url_for('main.index'))

    pickup_date = selected_pickup.date()
    pickup_time = selected_pickup.strftime('%H:%M')

    duration = request.args.get('duration', type=int) or 1
    duration = max(1, min(duration, 7))

    end_date = pickup_date + timedelta(days=duration)
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
            has_ktp=has_ktp,
            has_sim=has_sim,
            driver_fee=Rental.DRIVER_FEE,
            accessories=accessories_avail,
            insurances=Rental.INSURANCES,
            purposes=PURPOSES,
            regions=REGIONS,
            locations=LOCATIONS,
            form=form,
        )

    if request.method == 'GET':
        return render_form(MultiDict())

    # Validasi ulang saat formulir sewa dikirim.
    # Batas dihitung dari waktu pengiriman pesanan,
    # bukan hanya saat pengguna membuka halaman pencarian.
    if selected_pickup < waktu_minimum_pengambilan():
        flash(
            'Jadwal pengambilan harus minimal 25 jam '
            'dari sekarang. Silakan pilih ulang tanggal '
            'dan jam pengambilan.',
            'error'
        )
        return redirect(url_for('main.index'))

    # ---------- POST: validasi lalu simpan ----------
    f = request.form
    with_driver = can_driver and f.get('rental_type') == 'sopir'
    accessories = [a for a in f.getlist('accessories') if a in accessories_avail]
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
        # KTP wajib untuk semua, SIM hanya untuk lepas kunci.
    # Boleh dari Kelola Akun (sudah tersimpan) atau diunggah langsung di form.
    docs = [('ktp', 'KTP', has_ktp)]
    if not with_driver:
        docs.append(('sim', 'SIM', has_sim))

    for field, label, saved in docs:
        up = request.files.get(field)
        if up and up.filename:
            if up.filename.rsplit('.', 1)[-1].lower() not in ALLOWED_DOC_EXT:
                errors.append(f'Format {label} harus JPG, PNG, atau PDF.')
        elif not saved:
            errors.append(f'{label} wajib diunggah.')
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

    rental.ktp_file = (
        _save_document(request.files.get('ktp'), booking_code, 'ktp')
        or _copy_account_document(user.ktp_file, booking_code, 'ktp')
    )
    if not with_driver:
        rental.sim_file = (
            _save_document(request.files.get('sim'), booking_code, 'sim')
            or _copy_account_document(user.sim_file, booking_code, 'sim')
        )

    db.session.add(rental)
    db.session.commit()

    return redirect(url_for('main.pembayaran', rental_id=rental.id))



# ═════════════════════════════════════════════════════════════
#   PEMBATALAN OTOMATIS PESANAN
# ═════════════════════════════════════════════════════════════
# Membatalkan pesanan yang belum dibayar setelah melewati batas 24 jam.
def batalkan_pesanan_kedaluwarsa(rental, commit=True):
    """Membatalkan pesanan lewat tenggat pembayaran 24 jam."""
    if rental.status != Rental.STATUS_MENUNGGU_BAYAR:
        return False

    # Jangan bentrokkan pembatalan otomatis dengan permohonan
    # pelanggan yang masih menunggu keputusan admin.
    if _permohonan_pembatalan_pending(rental.id):
        return False

    deadline = rental.created_at + timedelta(hours=24)

    if datetime.now() < deadline or rental.payment_status == 'Lunas':
        return False

    status_lama = rental.status

    if not rental.cancellation_reason:
        rental.cancellation_reason = (
            'Dibatalkan otomatis karena pembayaran melewati batas waktu 24 jam.'
        )

    old_status = rental.change_status(Rental.STATUS_BATAL)

    # Simpan timeline pembatalan otomatis agar Detail Pesanan menampilkan
    # Pembatalan Diajukan beserta waktu kejadian, meskipun belum ada refund.
    existing_cancellation = rental.latest_cancellation
    if not existing_cancellation:
        db.session.add(RentalCancellation(
            rental_id=rental.id,
            reason=rental.cancellation_reason,
            initiated_by='system',
            status=RentalCancellation.STATUS_DIAJUKAN,
            requested_at=datetime.now(),
            cancelled_at=datetime.now(),
            refund_amount=None
        ))

    # Pastikan notifikasi pembatalan tidak dibuat berulang.
    sudah_ada = Notification.query.filter_by(
        rental_id=rental.id,
        category=Notification.CATEGORY_PAYMENT_CANCELLED,
    ).first()

    if not sudah_ada:
        db.session.add(
            Notification.payment_cancelled(
                rental,
                status_lama
            )
        )

    if commit:
        db.session.commit()

    return True



# ═════════════════════════════════════════════════════════════
#   HALAMAN PEMBAYARAN
# ═════════════════════════════════════════════════════════════
# Membatalkan pesanan yang sudah dibayar tetapi kendaraan tidak diambil
def batalkan_pesanan_tidak_diambil(rental, commit=True):
    """Batalkan pesanan yang sudah dibayar tapi kendaraan tidak diambil."""
    if not rental.is_pickup_expired:
        return False
    if _permohonan_pembatalan_pending(rental.id):
        return False

    status_lama = rental.status

    if not rental.cancellation_reason:
        rental.cancellation_reason = (
            'Dibatalkan otomatis karena kendaraan tidak diambil '
            'hingga masa sewa berakhir.'
        )

    old_status = rental.change_status(Rental.STATUS_BATAL)

    # Pesanan sudah dibayar: pembatalan otomatis tetap memerlukan refund.
    # Catat aktor system agar timeline tidak salah menyebut Admin sebagai pengaju.
    existing_cancellation = rental.latest_cancellation
    if not existing_cancellation or not existing_cancellation.needs_refund:
        db.session.add(RentalCancellation(
            rental_id=rental.id,
            reason=rental.cancellation_reason,
            initiated_by='system',
            status=RentalCancellation.STATUS_MENUNGGU_REFUND,
            requested_at=datetime.now(),
            cancelled_at=datetime.now(),
            refund_amount=rental.total_price
        ))

    # Cegah notifikasi ganda.
    sudah_ada = Notification.query.filter_by(
        rental_id=rental.id,
        category=Notification.CATEGORY_PICKUP_EXPIRED,
    ).first()

    if not sudah_ada:
        db.session.add(Notification.pickup_expired(rental, status_lama))

    if commit:
        db.session.commit()

    return True

# Menampilkan halaman pembayaran untuk pesanan tertentu.
@bp.route('/pembayaran/<int:rental_id>')
def pembayaran(rental_id):
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

    if _permohonan_pembatalan_pending(rental.id):
        flash(
            'Pembayaran tidak dapat dilanjutkan karena '
            'pesanan sedang menunggu persetujuan pembatalan.',
            'error'
        )
        return redirect(
            url_for('main.detail_pesanan', rental_id=rental.id)
        )

    if rental.payment_status == 'Lunas':
        return redirect(
            url_for('main.pembayaran_sukses', rental_id=rental.id)
        )

    # Batalkan pesanan dan buat notifikasi jika batas pembayaran habis.
    if batalkan_pesanan_kedaluwarsa(rental):
        flash('Waktu pembayaran habis, pesanan dibatalkan.')
        return redirect(url_for('main.index'))

    if rental.status == Rental.STATUS_BATAL:
        flash('Pesanan ini sudah dibatalkan.')
        return redirect(url_for('main.index'))

    deadline = rental.created_at + timedelta(hours=24)

    return render_template(
        'user/pembayaran.html',
        rental=rental,
        user=user,
        total=rental.total_price,
        deadline=deadline
    )

# Mengembalikan status pembayaran dalam format JSON.
# Route ini dapat dipanggil oleh JavaScript untuk memeriksa status terbaru.
@bp.route('/pembayaran/<int:rental_id>/status')
def status_pembayaran(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    return jsonify(paid=(rental.payment_status == 'Lunas'))



# ═════════════════════════════════════════════════════════════
#   KONFIRMASI PEMBAYARAN BERHASIL
# ═════════════════════════════════════════════════════════════
# Menampilkan halaman sukses setelah status pembayaran diperbarui.
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

    # Pastikan pesanan belum dibatalkan dan pembayaran belum kedaluwarsa.
    if batalkan_pesanan_kedaluwarsa(rental):
        flash('Waktu pembayaran habis, pesanan dibatalkan.')
        return redirect(url_for('main.index'))

    if rental.status == Rental.STATUS_BATAL:
        flash('Pesanan ini sudah dibatalkan.')
        return redirect(url_for('main.index'))

    # Ubah status jika pembayaran masih menunggu dan belum kedaluwarsa.
    # Catat pembayaran saat pelanggan menyelesaikan pembayaran.
    if rental.status == Rental.STATUS_MENUNGGU_BAYAR:
        # Pelanggan telah menyelesaikan pembayaran, tetapi Admin belum
        # memverifikasi bukti/transaksi. Status baru Lunas setelah dikonfirmasi.
        rental.payment_status = 'Menunggu Konfirmasi'
        rental.change_status(Rental.STATUS_MENUNGGU_KONFIRMASI)
        db.session.commit()

    return render_template(
        'user/pembayaran_sukses.html',
        rental=rental,
        user=user
    )



# ═════════════════════════════════════════════════════════════
#   KELOLA AKUN PENGGUNA
# ═════════════════════════════════════════════════════════════
# Menampilkan dan memperbarui data profil pengguna.
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

            if not re.fullmatch(r'\+?\d{10,15}', phone) or \
                not re.fullmatch(r'\+?\d{10,15}', emergency_phone):
                flash('Nomor telepon harus berupa angka 10-15 digit.', 'error')
                return redirect(url_for('main.kelola_akun'))

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



# ═════════════════════════════════════════════════════════════
#   KELOLA PESANAN PENGGUNA
# ═════════════════════════════════════════════════════════════
# Menampilkan seluruh riwayat pesanan milik pengguna yang login.
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



# ═════════════════════════════════════════════════════════════
#   PENGAJUAN PEMBATALAN PESANAN OLEH PENGGUNA
# ═════════════════════════════════════════════════════════════
# Route POST digunakan untuk menerima permohonan pembatalan pesanan.
@bp.route(
    '/detail-pesanan/<int:rental_id>/batalkan',
    methods=['POST'])
def batalkan_pesanan_user(rental_id):
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

    status_boleh_batal = [
        Rental.STATUS_MENUNGGU_BAYAR,
        Rental.STATUS_MENUNGGU_KONFIRMASI,
        Rental.STATUS_PENGAMBILAN
    ]

    if rental.status not in status_boleh_batal:
        flash(
            'Pesanan tidak dapat dibatalkan karena '
            'sudah memasuki tahap penggunaan atau sudah berakhir.',
            'error'
        )
        return redirect(
            url_for('main.detail_pesanan', rental_id=rental.id)
        )

    # Pastikan pengajuan sebelumnya tidak masih menunggu admin.
    if _permohonan_pembatalan_pending(rental.id):
        flash(
            'Permohonan pembatalan pesanan ini sedang menunggu '
            'persetujuan admin.',
            'error'
        )
        return redirect(
            url_for('main.detail_pesanan', rental_id=rental.id)
        )

    # Alasan harus cocok dengan salah satu pilihan dropdown.
    reason = request.form.get(
        'cancellation_reason', ''
    ).strip()

    if reason not in ALASAN_PEMBATALAN_USER:
        flash(
            'Silakan pilih alasan pembatalan yang tersedia.',
            'error'
        )
        return redirect(
            url_for('main.detail_pesanan', rental_id=rental.id)
        )

    # Tentukan apakah pengajuan membutuhkan proses refund.
    perlu_refund = _rental_sudah_dibayar(rental)

    pembatalan = RentalCancellation(
        rental_id=rental.id,
        reason=reason,
        initiated_by='customer',
        status=RentalCancellation.STATUS_DIAJUKAN,
        requested_at=datetime.now(),
        refund_amount=(
            rental.total_price if perlu_refund else None
        )
    )

    # Pesanan belum langsung menjadi Batal.
    # Status baru berubah setelah admin menyetujui.
    db.session.add(pembatalan)
    db.session.commit()

    flash(
        'Permohonan pembatalan berhasil diajukan. '
        'Pesanan menunggu persetujuan admin.',
        'success'
    )

    return redirect(
        url_for('main.detail_pesanan', rental_id=rental.id)
    )



# ═════════════════════════════════════════════════════════════
#   REVIEW PESANAN YANG SUDAH SELESAI
# ═════════════════════════════════════════════════════════════
@bp.route('/detail-pesanan/<int:rental_id>/review', methods=['POST'])
def kirim_review_pesanan(rental_id):
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

    # Review hanya dapat diberikan setelah pesanan selesai.
    if rental.status != Rental.STATUS_SELESAI:
        flash(
            'Review hanya dapat diberikan setelah pesanan selesai.',
            'error'
        )
        return redirect(
            url_for('main.detail_pesanan', rental_id=rental.id)
        )

    # Ambil review sebelumnya untuk menentukan apakah membuat
    # review baru atau memperbarui review yang sudah ada.
    existing_review = Review.query.filter_by(
        rental_id=rental.id,
        user_id=user.id
    ).first()

    # Validasi rating kendaraan.
    try:
        rating = int(request.form.get('rating', '0'))
    except (TypeError, ValueError):
        rating = 0

    if rating not in (1, 2, 3, 4, 5):
        flash('Pilih rating kendaraan antara 1 sampai 5 bintang.', 'error')
        return redirect(
            url_for('main.detail_pesanan', rental_id=rental.id)
        )

    # Rating sopir hanya diperlukan jika pesanan menggunakan sopir.
    rating_driver = None

    if rental.driver_id is not None:
        try:
            rating_driver = int(
                request.form.get('rating_driver', '0')
            )
        except (TypeError, ValueError):
            rating_driver = 0

        if rating_driver not in (1, 2, 3, 4, 5):
            flash('Pilih rating sopir antara 1 sampai 5 bintang.', 'error')
            return redirect(
                url_for('main.detail_pesanan', rental_id=rental.id)
            )

    # Komentar hanya untuk kendaraan.
    comment = (request.form.get('comment') or '').strip()

    if existing_review:
        # Perbarui review yang sudah ada.
        existing_review.rating = rating
        existing_review.rating_driver = rating_driver
        existing_review.comment = comment or None

        pesan_review = 'Review berhasil diperbarui.'
    else:
        # Buat review baru jika belum pernah mengisi.
        review = Review(
            user_id=user.id,
            vehicle_id=rental.vehicle_id,
            rental_id=rental.id,
            rating=rating,
            rating_driver=rating_driver,
            comment=comment or None
        )

        db.session.add(review)
        pesan_review = 'Terima kasih, review berhasil dikirim.'

    db.session.commit()

    flash(pesan_review, 'success')

    return redirect(
        url_for('main.detail_pesanan', rental_id=rental.id)
    )


# ═════════════════════════════════════════════════════════════
#   HALAMAN DETAIL PESANAN
# ═════════════════════════════════════════════════════════════
@bp.route('/detail-pesanan/<int:rental_id>')
def detail_pesanan(rental_id):
    # Membuat route untuk menampilkan detail pesanan berdasarkan ID rental.
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

    # Ambil ulasan yang sudah dikirim untuk pesanan ini.
    review_existing = Review.query.filter_by(
        rental_id=rental.id,
        user_id=user.id
    ).first()

    # [OOP - PEMANFAATAN PROPERTI ENKAPSULASI & ABSTRAKSI MODEL]
    # Mengambil objek RentalCancellation terbaru melalui properti enkapsulasi
    # serta menyinkronkan data lama jika pesanan berbayar sudah berstatus Batal.
    cancellation = rental.latest_cancellation
    if (
        rental.status == Rental.STATUS_BATAL
        and cancellation is None
        and _rental_sudah_dibayar(rental)
    ):
        waktu_batal = (
            rental.status_history[-1].changed_at
            if rental.status_history
            else datetime.now()
        )
        cancellation = _catat_pembatalan_admin_berbayar(
            rental,
            rental.cancellation_reason,
            waktu_batal
        )
        db.session.commit()

    cancellation_is_pending = (
        cancellation.is_pending if cancellation else False
    )
    cancellation_is_rejected = (
        cancellation.is_rejected if cancellation else False
    )

    # Keterangan pembatalan langsung tanpa proses refund.
    alasan_lama = (rental.cancellation_reason or '').lower()

    dibatalkan_otomatis = (
        'otomatis' in alasan_lama
        or 'melewati batas waktu pembayaran' in alasan_lama
    )

    # Memeriksa pembatalan otomatis karena kendaraan tidak diambil.
    dibatalkan_otomatis_tidak_diambil = (
        rental.status == Rental.STATUS_BATAL
        and (
            'kendaraan tidak diambil' in alasan_lama
            or 'kendaraan tidak segera diambil' in alasan_lama
        )
    )

    # Memeriksa pembatalan otomatis karena pembayaran melewati tenggat.
    dibatalkan_otomatis_batas_pembayaran = (
        rental.status == Rental.STATUS_BATAL
        and (
            'pembayaran melewati batas waktu' in alasan_lama
            or 'melewati batas waktu pembayaran' in alasan_lama
            or 'pembayaran melewati batas waktu 24 jam' in alasan_lama
        )
    )
    

    # Mengambil status pesanan sebelum pembatalan terakhir oleh admin.
    status_sebelum_batal = next(
        (
            riwayat.old_status
            for riwayat in reversed(rental.status_history)
            if riwayat.new_status == Rental.STATUS_BATAL
        ),
        None
    )

    # =====================================================
    # TIMELINE STATUS PEMBATALAN PESANAN
    # Menampilkan pengajuan, persetujuan, dan pengembalian dana.
    # =====================================================
    cancellation_steps = []
    cancellation_completed_steps = 0

    if cancellation and cancellation.initiated_by == 'customer':

        # TAHAP 1: PELANGGAN MENGAJUKAN PEMBATALAN.
        cancellation_steps.append((
            'fa-file-circle-plus',
            'Pembatalan Diajukan',
            cancellation.requested_at
        ))

        # PERMOHONAN PEMBATALAN DITOLAK ADMIN.
        if cancellation.status == RentalCancellation.STATUS_DITOLAK:

            cancellation_steps.append((
                'fa-circle-xmark',
                'Pembatalan Ditolak',
                cancellation.rejected_at
            ))

            cancellation_completed_steps = 2

        else:

            # TAHAP 2: PERSETUJUAN PEMBATALAN.
            if cancellation.status == RentalCancellation.STATUS_DIAJUKAN:

                cancellation_steps.append((
                    'fa-clock',
                    'Menunggu Persetujuan',
                    None
                ))

                cancellation_completed_steps = 1

            else:

                cancellation_steps.append((
                    'fa-circle-check',
                    'Pembatalan Disetujui',
                    cancellation.approved_at
                ))

                cancellation_completed_steps = 2

            # Memeriksa apakah pesanan membutuhkan refund.
            perlu_refund = (
                cancellation.refund_amount is not None
                or rental.payment_status == 'Lunas'
                or _rental_sudah_dibayar(rental)
            )

            # TAHAP 3: DANA DIKEMBALIKAN.
            # Tetap tampil meskipun pembatalan masih diajukan.
            if perlu_refund:

                waktu_pengembalian = (
                    cancellation.refunded_at
                    if cancellation.status
                    == RentalCancellation.STATUS_DANA_DIKEMBALIKAN
                    else None
                )

                cancellation_steps.append((
                    'fa-money-bill-transfer',
                    'Dana Dikembalikan',
                    waktu_pengembalian
                ))

                # Tahap refund selesai hanya setelah dana dikembalikan.
                if (
                    cancellation.status
                    == RentalCancellation.STATUS_DANA_DIKEMBALIKAN
                ):
                    cancellation_completed_steps = 3

    elif (
        rental.status == Rental.STATUS_BATAL
        and (rental.payment_status or 'Belum Lunas') == 'Belum Lunas'
        and not dibatalkan_otomatis
        and (
            cancellation is None
            or (
                cancellation.initiated_by == 'admin'
                and cancellation.refund_amount is None
            )
        )
    ):

        # TIMELINE PEMBATALAN LANGSUNG OLEH ADMIN TANPA REFUND.
        waktu_batal = next(
            (
                riwayat.changed_at
                for riwayat in reversed(rental.status_history)
                if riwayat.new_status == Rental.STATUS_BATAL
            ),
            None
        )

        cancellation_steps = [(
            'fa-file-circle-plus',
            'Pembatalan Diajukan',
            waktu_batal
        )]

        cancellation_completed_steps = 1

    elif (
        cancellation
        and cancellation.initiated_by == 'admin'
        and rental.status == Rental.STATUS_BATAL
        and status_sebelum_batal in [
            Rental.STATUS_MENUNGGU_KONFIRMASI,
            Rental.STATUS_PENGAMBILAN
        ]
        and rental.payment_status in [
            'Menunggu Konfirmasi',
            'Lunas'
        ]
        and cancellation.refund_amount is not None
    ):

        # TIMELINE PEMBATALAN LANGSUNG OLEH ADMIN
        # UNTUK PESANAN DENGAN PEMBAYARAN YANG PERLU DIREFUND.

        waktu_batal = (
            cancellation.cancelled_at
            or next(
                (
                    riwayat.changed_at
                    for riwayat in reversed(rental.status_history)
                    if riwayat.new_status == Rental.STATUS_BATAL
                ),
                None
            )
        )

        cancellation_steps = [
            (
                'fa-file-circle-plus',
                'Pembatalan Diajukan',
                waktu_batal
            ),
            (
                'fa-money-bill-transfer',
                'Dana Dikembalikan',
                cancellation.refunded_at
            )
        ]

        # Tahap pertama selesai ketika admin membatalkan pesanan.
        # Tahap kedua selesai setelah dana benar-benar dikembalikan.
        if (
            cancellation.status
            == RentalCancellation.STATUS_DANA_DIKEMBALIKAN
            or cancellation.refunded_at is not None
        ):
            cancellation_completed_steps = 2
        else:
            cancellation_completed_steps = 1

    else:

        # Mempertahankan timeline pembatalan lainnya.
        cancellation_steps = (
            cancellation.timeline_steps if cancellation else []
        )

        cancellation_completed_steps = (
            cancellation.completed_steps_count if cancellation else 0
        )

    # =====================================================
    #   WAKTU PERUBAHAN STATUS PESANAN
    # =====================================================
    status_waktu = {}

    # Ambil waktu terakhir setiap status dari riwayat.
    for riwayat in rental.status_history:
        status_waktu[riwayat.new_status] = riwayat.changed_at

    # Fallback untuk status lama yang tercatat melalui notifikasi.
    notifikasi_status = (
        Notification.query
        .filter_by(
            rental_id=rental.id,
            category=Notification.CATEGORY_STATUS
        )
        .order_by(Notification.created_at.asc())
        .all()
    )

    for notifikasi in notifikasi_status:
        status_waktu.setdefault(
            notifikasi.new_status,
            notifikasi.created_at
        )

    timeline_times = {
        'created': rental.created_at,
        'payment': status_waktu.get(
            Rental.STATUS_MENUNGGU_KONFIRMASI
        ),
        'pickup': status_waktu.get(
            Rental.STATUS_PENGAMBILAN
        ),
        'in_use': status_waktu.get(
            Rental.STATUS_DIPAKAI
        ),
        'completed': status_waktu.get(
            Rental.STATUS_SELESAI
        ),
        'cancelled': status_waktu.get(
            Rental.STATUS_BATAL
        )
    }

    return render_template(
        'user/halDetailPesanan.html',
        user=user,
        rental=rental,
        cancellation=cancellation,
        review_existing=review_existing,
        cancellation_steps=cancellation_steps,
        cancellation_completed_steps=cancellation_completed_steps,
        cancellation_is_pending=cancellation_is_pending,
        cancellation_is_rejected=cancellation_is_rejected,
        timeline_times=timeline_times,
        dibatalkan_otomatis=dibatalkan_otomatis,
        dibatalkan_otomatis_tidak_diambil=dibatalkan_otomatis_tidak_diambil,
        dibatalkan_otomatis_batas_pembayaran=dibatalkan_otomatis_batas_pembayaran,
        alasan_pembatalan=ALASAN_PEMBATALAN_USER,
        current_step={
            Rental.STATUS_MENUNGGU_BAYAR: 0,
            Rental.STATUS_MENUNGGU_KONFIRMASI: 1,
            Rental.STATUS_PENGAMBILAN: 2,
            Rental.STATUS_DIPAKAI: 3,
            Rental.STATUS_PENGEMBALIAN: 3,
            Rental.STATUS_SELESAI: 4,
            Rental.STATUS_BATAL: -1
        }.get(rental.status, 0)
    )


# ═════════════════════════════════════════════════════════════
#   HALAMAN RIWAYAT PESANAN
# ═════════════════════════════════════════════════════════════
@bp.route('/riwayat-pesanan')
def riwayat_pesanan():
    if 'user_id' not in session:
        # Memeriksa apakah pengguna sudah login.
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    
    # Mengambil data pengguna dari database.
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
# ═════════════════════════════════════════════════════════════
#   MEMERIKSA NOTIFIKASI YANG SUDAH ADA
# ═════════════════════════════════════════════════════════════
def _notifikasi_sudah_ada(rental, category):
    """Memeriksa apakah kategori notifikasi sudah dibuat untuk pesanan."""
    return Notification.query.filter_by(
        user_id=rental.user_id,
        rental_id=rental.id,
        category=category,
    ).first() is not None


# ═════════════════════════════════════════════════════════════
#   MEMERIKSA PENGINGAT DAN DENDA
# ═════════════════════════════════════════════════════════════
def periksa_pengingat_dan_denda(user_id=None):
    """
    Memeriksa pengingat pembayaran, pengembalian, dan denda.
    Pengingat H-3 hari yang sudah ada tetap dipertahankan.
    """
    now = datetime.now()
    today_start = datetime(
        now.year,
        now.month,
        now.day
    )

    jumlah_baru = 0

    # =====================================================
    # 1. PEMBAYARAN
    #    H-1 jam, H-30 menit, dan pembatalan otomatis
    # =====================================================
    pembayaran_query = Rental.query.filter(
        Rental.status == Rental.STATUS_MENUNGGU_BAYAR,
        Rental.payment_status != 'Lunas',
    )

    if user_id is not None:
        pembayaran_query = pembayaran_query.filter(
            Rental.user_id == user_id
        )

    for rental in pembayaran_query.all():
        deadline = rental.created_at + timedelta(hours=24)

        # Batalkan pesanan yang sudah melewati tenggat.
        if now >= deadline:
            if batalkan_pesanan_kedaluwarsa(
                rental,
                commit=False
            ):
                jumlah_baru += 1

            continue

        sisa = deadline - now
        kategori = None

        # Pengingat dalam rentang 1 jam hingga 30 menit.
        if timedelta(minutes=30) < sisa <= timedelta(hours=1):
            kategori = Notification.CATEGORY_PAYMENT_1H

        # Pengingat saat tersisa maksimal 30 menit.
        elif timedelta(0) < sisa <= timedelta(minutes=30):
            kategori = Notification.CATEGORY_PAYMENT_30M

        if (
            kategori
            and not _notifikasi_sudah_ada(rental, kategori)
        ):
            db.session.add(
                Notification.payment_reminder(
                    rental,
                    kategori
                )
            )
            jumlah_baru += 1

    # =====================================================
    # 2. PENGEMBALIAN KENDARAAN
    #    H-24 jam dan H-3 jam
    # =====================================================
    pemakaian_query = Rental.query.filter_by(
        status=Rental.STATUS_DIPAKAI
    )

    if user_id is not None:
        pemakaian_query = pemakaian_query.filter(
            Rental.user_id == user_id
        )

    for rental in pemakaian_query.all():
        sisa = rental.return_deadline - now

        if sisa > timedelta(0):
            kategori = None

            # Pengingat dalam rentang 24 jam hingga 3 jam.
            if timedelta(hours=3) < sisa <= timedelta(hours=24):
                kategori = Notification.CATEGORY_RETURN_24H

            # Pengingat saat tersisa maksimal 3 jam.
            elif timedelta(0) < sisa <= timedelta(hours=3):
                kategori = Notification.CATEGORY_RETURN_3H

            if (
                kategori
                and not _notifikasi_sudah_ada(rental, kategori)
            ):
                db.session.add(
                    Notification.return_deadline_reminder(
                        rental,
                        kategori
                    )
                )
                jumlah_baru += 1

            # Pengingat lama H-3 hari tetap berjalan.
            if (
                rental.is_due_soon
                and not _notifikasi_sudah_ada(
                    rental,
                    Notification.CATEGORY_REMINDER
                )
            ):
                db.session.add(
                    Notification.return_reminder(rental)
                )
                jumlah_baru += 1

        # Kendaraan belum dikembalikan setelah tenggat.
        elif rental.is_overdue:
            sudah_ada_hari_ini = Notification.query.filter(
                Notification.user_id == rental.user_id,
                Notification.rental_id == rental.id,
                Notification.category == Notification.CATEGORY_OVERDUE,
                Notification.created_at >= today_start,
            ).first()

            # Pertahankan aturan lama: maksimal satu peringatan per hari.
            if not sudah_ada_hari_ini:
                db.session.add(
                    Notification.overdue_warning(rental)
                )
                jumlah_baru += 1

    # =====================================================
    # 3. PESANAN SUDAH DIBAYAR TAPI TIDAK DIAMBIL
    # =====================================================
    belum_diambil_query = Rental.query.filter(
        Rental.status.in_([
            Rental.STATUS_MENUNGGU_KONFIRMASI,
            Rental.STATUS_PENGAMBILAN,
        ]),
        Rental.end_date <= now.date(),
    )

    if user_id is not None:
        belum_diambil_query = belum_diambil_query.filter(
            Rental.user_id == user_id
        )

    for rental in belum_diambil_query.all():
        if batalkan_pesanan_tidak_diambil(rental, commit=False):
            jumlah_baru += 1

    if jumlah_baru:
        db.session.commit()


# ═════════════════════════════════════════════════════════════
# MEMBUKA NOTIFIKASI DAN MENANDAINYA SUDAH DIBACA
# ═════════════════════════════════════════════════════════════
@bp.route('/notifikasi')
def notifikasi():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    # Mengambil data pengguna yang sedang login.
    if not user:
        # Memeriksa apakah data akun masih tersedia.
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


# ═════════════════════════════════════════════════════════════
# MENANDAI NOTIFIKASI SUDAH DIBACA SAAT DIBUKA
# ═════════════════════════════════════════════════════════════
@bp.route('/notifikasi/<int:notification_id>/lihat-pesanan')
def buka_notifikasi(notification_id):
    # Pastikan pengguna sudah login.
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if not user:
        session.clear()
        return redirect(url_for('main.login'))

    # Ambil notifikasi milik pengguna yang sedang login.
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user.id
    ).first_or_404()

    # Tandai notifikasi sebagai sudah dibaca.
    if not notification.is_read:
        # Mengubah status notifikasi menjadi sudah dibaca.
        notification.is_read = True
        # Menyimpan perubahan ke database.
        db.session.commit()

    # Buka halaman detail pesanan terkait.
    return redirect(
        url_for(
            'main.detail_pesanan',
            rental_id=notification.rental_id
        )
    )


# ═════════════════════════════════════════════════════════════
# MENGGANTI PASSWORD
# ═════════════════════════════════════════════════════════════
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




# ═════════════════════════════════════════════════════════════
#   HALAMAN LOGIN | REGISTER | LOGOUT
# ═════════════════════════════════════════════════════════════
@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Hapus pesan validasi jadwal dari antrean flash
    # agar tidak ikut tampil di halaman login.
    flash_lama = session.get('_flashes', [])

    pesan_jadwal = (
        'Pengambilan kendaraan harus dijadwalkan',
        'Jadwal pengambilan harus minimal 25 jam',
    )

    flash_lama = [
        item for item in flash_lama
        if not any(teks in item[1] for teks in pesan_jadwal)
    ]

    if flash_lama:
        session['_flashes'] = flash_lama
    else:
        session.pop('_flashes', None)
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):

            # Tolak login jika akun dinonaktifkan admin
            if not user.is_active:
                flash('Akun Anda telah dinonaktifkan. Silakan hubungi admin.')
                return redirect(url_for('main.login'))

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


@bp.route('/login/google')
def google_login():
    # Cegah error jika kredensial Google belum disiapkan.
    if (
        not current_app.config.get('GOOGLE_CLIENT_ID')
        or not current_app.config.get('GOOGLE_CLIENT_SECRET')
    ):
        flash('Login Google belum dikonfigurasi.', 'error')
        return redirect(url_for('main.login'))

    redirect_uri = url_for(
        'main.google_callback',
        _external=True
    )

    return oauth.google.authorize_redirect(
        redirect_uri,
        prompt='select_account'
    )


@bp.route('/login/google/callback')
def google_callback():
    # Ambil dan verifikasi hasil autentikasi dari Google.
    try:
        token = oauth.google.authorize_access_token()
        google_user = token.get('userinfo')
    except Exception:
        current_app.logger.exception(
            'Proses login Google gagal.'
        )
        flash(
            'Login Google gagal. Silakan coba lagi.',
            'error'
        )
        return redirect(url_for('main.login'))

    if not google_user:
        flash(
            'Data akun Google tidak berhasil diperoleh.',
            'error'
        )
        return redirect(url_for('main.login'))

    # Hanya terima alamat email yang telah diverifikasi Google.
    email = (google_user.get('email') or '').strip()

    if not email or google_user.get('email_verified') is not True:
        flash(
            'Email Google tidak dapat diverifikasi.',
            'error'
        )
        return redirect(url_for('main.login'))

    # OPSI B: cari akun yang sudah ada, tanpa membuat akun baru.
    user = User.query.filter(
        db.func.lower(User.email) == email.lower()
    ).first()

    if not user:
        flash(
            'Email Google belum terdaftar. '
            'Silakan registrasi terlebih dahulu.',
            'error'
        )
        return redirect(url_for('main.register'))

    # Akun yang dinonaktifkan tidak boleh login dengan Google.
    if not user.is_active:
        flash(
            'Akun Anda sedang dinonaktifkan. Hubungi admin.',
            'error'
        )
        return redirect(url_for('main.login'))

    # Buat session aplikasi setelah identitas berhasil diperiksa.
    session.clear()
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['user_email'] = user.email
    session['user_role'] = user.role

    # Pertahankan pemisahan halaman berdasarkan role.
    if user.role in ('admin', 'superadmin'):
        return redirect(url_for('main.admin_dashboard'))

    return redirect(url_for('main.index'))


def kirim_email_reset_password(email_tujuan, reset_url):
    """Kirim tautan reset password melalui Gmail SMTP."""

    email_pengirim = os.getenv('SMTP_EMAIL')
    app_password = os.getenv('SMTP_APP_PASSWORD')
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))

    if not email_pengirim or not app_password:
        raise RuntimeError(
            'SMTP_EMAIL dan SMTP_APP_PASSWORD belum dikonfigurasi.'
        )

    pesan = EmailMessage()
    pesan['Subject'] = 'Reset Password KeSanaSini'
    pesan['From'] = f'KeSanaSini <{email_pengirim}>'
    pesan['To'] = email_tujuan

    # Versi teks biasa jika aplikasi email tidak mendukung HTML.
    pesan.set_content(
        f'''Halo,

Kami menerima permintaan untuk mengatur ulang password
akun KeSanaSini Anda.

Klik tautan berikut untuk membuat password baru:
{reset_url}

Tautan ini berlaku selama 15 menit.

Jika Anda tidak meminta reset password, abaikan email ini.

Salam,
Tim KeSanaSini
'''
    )

    # Versi HTML agar link mudah diklik.
    url_aman = escape(reset_url, quote=True)

    pesan.add_alternative(
        f'''\
<html>
<body>
    <h2>Reset Password KeSanaSini</h2>
    <p>Kami menerima permintaan untuk mengatur ulang
    password akun KeSanaSini Anda.</p>

    <p>
        <a href="{url_aman}">Reset Password</a>
    </p>

    <p>Link berlaku selama 15 menit.</p>

    <p>Jika Anda tidak meminta reset password,
    abaikan email ini.</p>

    <p>Salam,<br>Tim KeSanaSini</p>
</body>
</html>
''',
        subtype='html'
    )

    # App Password Google dapat ditampilkan dengan spasi.
    app_password = app_password.strip().replace(' ', '')

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=20
    ) as server:
        server.ehlo()
        server.starttls(
            context=ssl.create_default_context()
        )
        server.ehlo()
        server.login(email_pengirim, app_password)
        server.send_message(pesan)


@bp.route('/lupa-password', methods=['GET', 'POST'])
def lupa_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()

        user = User.query.filter(
            db.func.lower(User.email) == email.lower()
        ).first()

        # Pesan tetap sama agar tidak membocorkan
        # apakah email terdaftar.
        flash(
            'Jika email terdaftar, tautan reset akan dikirim. '
            'Periksa kotak masuk dan folder spam.',
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

            try:
                kirim_email_reset_password(
                    user.email,
                    reset_url
                )
            except Exception:
                current_app.logger.exception(
                    'Gagal mengirim email reset password.'
                )

        return redirect(
            url_for('main.lupa_password')
        )

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




# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#
#                                                   PENGATURAN ADMIN
#
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
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
    # [OOP - QUERY OBJECT & AGREGASI KONTEKS ADMIN]
    # Mengambil koleksi objek Rental yang menunggu konfirmasi serta objek
    # RentalCancellation yang membutuhkan tindakan persetujuan/refund dari Admin.
    pending = (Rental.query
               .filter_by(status=Rental.STATUS_MENUNGGU)
               .order_by(Rental.created_at.desc())
               .all())
    pending_cancellations = (
        RentalCancellation.query
        .join(Rental)
        .filter(
            or_(
                RentalCancellation.status == RentalCancellation.STATUS_DIAJUKAN,
                db.and_(
                    Rental.status == Rental.STATUS_BATAL,
                    RentalCancellation.status.in_([
                        RentalCancellation.STATUS_DISETUJUI,
                        RentalCancellation.STATUS_MENUNGGU_REFUND
                    ]),
                    RentalCancellation.refund_amount.isnot(None),
                    RentalCancellation.refunded_at.is_(None)
                )
            )
        )
        .order_by(RentalCancellation.id.desc())
        .all()
    )
    return {
        'admin': User.query.get(session['user_id']),
        'pending_rentals': pending,
        'pending_cancellations': pending_cancellations,
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


@bp.route(
    '/admin/penyewaan/<int:rental_id>/pembatalan/'
    '<int:cancellation_id>/proses',
    methods=['POST']
)
@admin_required
def admin_proses_pembatalan(rental_id, cancellation_id):
    rental = Rental.query.get_or_404(rental_id)

    pembatalan = RentalCancellation.query.filter_by(
        id=cancellation_id,
        rental_id=rental.id
    ).first_or_404()

    action = request.form.get('action')
    sekarang = datetime.now()

    # =====================================================
    # 1. ADMIN MENYETUJUI PERMOHONAN PELANGGAN
    # =====================================================
    if action == 'approve':
        if (
            pembatalan.initiated_by != 'customer'
            or pembatalan.status != RentalCancellation.STATUS_DIAJUKAN
        ):
            flash(
                'Permohonan ini tidak lagi menunggu persetujuan.',
                'error'
            )
            return redirect(
                url_for('main.admin_penyewaan_edit', id=rental.id)
            )

        status_boleh_batal = [
            Rental.STATUS_MENUNGGU_BAYAR,
            Rental.STATUS_MENUNGGU_KONFIRMASI,
            Rental.STATUS_PENGAMBILAN
        ]

        if rental.status not in status_boleh_batal:
            flash(
                'Pesanan sudah memasuki tahap yang tidak '
                'dapat dibatalkan melalui alur ini.',
                'error'
            )
            return redirect(
                url_for('main.admin_penyewaan_edit', id=rental.id)
            )

        perlu_refund = _rental_sudah_dibayar(rental)

        # Simpan alasan pada kolom lama agar tetap kompatibel
        # dengan template dan proses admin yang sudah ada.
        rental.cancellation_reason = pembatalan.reason

        old_status = rental.change_status(Rental.STATUS_BATAL)

        if not old_status:
            flash('Status pesanan tidak berubah.', 'error')
            return redirect(
                url_for('main.admin_penyewaan_edit', id=rental.id)
            )

        # [OOP - ENKAPSULASI & STATE TRANSITION]
        # Memanggil method behavior approve() pada objek RentalCancellation
        # serta Factory Method Notification.status_changed().
        pembatalan.approve(
            refund_amount=rental.total_price if perlu_refund else None,
            timestamp=sekarang
        )

        db.session.add(
            Notification.status_changed(
                rental,
                old_status,
                cancelled_by='user'
            )
        )
        db.session.commit()

        flash(
            'Pembatalan disetujui. '
            + (
                'Pengembalian dana masih perlu diproses.'
                if perlu_refund
                else 'Pesanan dibatalkan tanpa proses refund.'
            ),
            'success'
        )

    # =====================================================
    # 2. ADMIN MENOLAK PERMOHONAN PELANGGAN
    # =====================================================
    elif action == 'reject':
        if (
            pembatalan.initiated_by != 'customer'
            or pembatalan.status != RentalCancellation.STATUS_DIAJUKAN
        ):
            flash(
                'Permohonan ini tidak lagi dapat ditolak.',
                'error'
            )
            return redirect(
                url_for('main.admin_penyewaan_edit', id=rental.id)
            )

        # [OOP - ENKAPSULASI & FACTORY METHOD]
        # Memanggil method behavior reject() pada objek RentalCancellation
        # dan mengirim notifikasi penolakan ke pelanggan.
        pembatalan.reject(
            admin_note=request.form.get('admin_note', ''),
            timestamp=sekarang
        )
        db.session.add(
            Notification.cancellation_rejected(rental, pembatalan)
        )

        # Status pesanan tidak diubah ketika permohonan ditolak.
        db.session.commit()

        flash(
            'Permohonan pembatalan ditolak. '
            'Status pesanan tetap seperti sebelumnya.',
            'success'
        )

    # =====================================================
    # 3. ADMIN MENCATAT DANA SUDAH DIKEMBALIKAN
    # =====================================================
    elif action == 'refund':
        status_refund_boleh = [
            RentalCancellation.STATUS_DISETUJUI,
            RentalCancellation.STATUS_MENUNGGU_REFUND
        ]

        if (
            pembatalan.status not in status_refund_boleh
            or pembatalan.refund_amount is None
            or rental.status != Rental.STATUS_BATAL
        ):
            flash('Pembatalan ini belum memenuhi syarat refund.', 'error')
            return redirect(url_for('main.admin_penyewaan_edit', id=rental.id))

        # [OOP - ENKAPSULASI]
        # Memanggil method behavior mark_refunded().
        # Refund selalu penuh: nominal sudah tercatat saat pembatalan disetujui.
        pembatalan.mark_refunded(
            nominal=pembatalan.refund_amount,
            timestamp=sekarang
        )
        db.session.add(Notification.refund_completed(rental, pembatalan))
        db.session.commit()

        flash('Pengembalian dana berhasil dicatat.', 'success')

    else:
        flash('Aksi pembatalan tidak valid.', 'error')

    return redirect(
        url_for('main.admin_penyewaan_edit', id=rental.id)
    )


@bp.route('/admin/penyewaan/<int:rental_id>/status', methods=['POST'])
@admin_required
def admin_update_rental_status(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    new_status = request.form.get('status')
    balik = request.referrer or url_for('main.admin_dashboard')

    if new_status not in Rental.ALL_STATUS:
        flash('Status tidak valid.', 'error')
        return redirect(balik)

    if new_status == rental.status:
        flash('Status pesanan tidak mengalami perubahan.')
        return redirect(balik)

    # Jangan membatalkan langsung pesanan yang memiliki pengajuan
    # pelanggan. Gunakan tombol Setujui/Tolak Permohonan.
    if new_status == Rental.STATUS_BATAL and _permohonan_pembatalan_pending(rental.id):
        flash(
            'Ada permohonan pembatalan dari pelanggan. '
            'Silakan proses permohonan tersebut terlebih dahulu.', 'error'
        )
        return redirect(url_for('main.admin_penyewaan_edit', id=rental.id))

    if not rental.can_admin_change_to(new_status):
        flash(
            f'Status tidak bisa diubah dari "{rental.status}" '
            f'ke "{new_status}".', 'error'
        )
        return redirect(balik)

    # Validasi pembatalan langsung oleh admin.
    if new_status == Rental.STATUS_BATAL:
        _batalkan_oleh_admin(rental, request.form.get('cancellation_reason'))
    else:
        old_status = rental.change_status(new_status)
        if old_status:
            db.session.add(Notification.status_changed(rental, old_status))
            # Notifikasi denda tetap dipertahankan.
            if (
                rental.fine_amount > 0
                and new_status in [Rental.STATUS_PENGEMBALIAN, Rental.STATUS_SELESAI]
            ):
                db.session.add(Notification.fine_issued(rental))

    db.session.commit()
    flash(f'Status {rental.booking_code} diubah menjadi "{new_status}".')
    return redirect(balik)



# ═════════════════════════════════════════════════════════════
#   HALAMAN ADMIN: DAFTAR KENDARAAN
# ═════════════════════════════════════════════════════════════
@bp.route('/admin/kendaraan')
@admin_required
def admin_kendaraan():
    # ---------- KARTU STATISTIK ----------
    # Semua angka dihitung ulang dari database di setiap request.
    total_vehicles = Vehicle.query.count()
    # ID unit yang punya penyewaan berstatus "berjalan". Memakai set
    # agar tiap ID hanya dihitung sekali.
    rented_vehicle_ids = {r.vehicle_id for r in
                          Rental.query.filter_by(status=Rental.STATUS_BERJALAN).all()}
    # Unit yang dinonaktifkan admin (is_active = False).
    inactive_vehicles = Vehicle.query.filter_by(is_active=False).count()
    # Tersedia = aktif DAN tidak sedang disewa.
    available_vehicles = Vehicle.query.filter(
        Vehicle.is_active.is_(True),
        ~Vehicle.id.in_(list(rented_vehicle_ids))
    ).count()

    # q    : kata kunci pencarian (merek, tipe, atau plat).
    # page : nomor halaman, default 1.
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    # Pencarian memakai ilike (tidak membedakan huruf besar/kecil),
    # dengan pola %kata% sehingga cocok di bagian mana pun teks.
    query = Vehicle.query
    if q:
        pattern = f'%{q}%'
        query = query.filter(or_(
            Vehicle.brand.ilike(pattern),
            Vehicle.model.ilike(pattern),
            Vehicle.vehicle_number.ilike(pattern),
        ))

    # Urut dari data terbaru, 5 unit per halaman. error_out=False:
    # halaman di luar jangkauan menghasilkan daftar kosong, bukan 404.
    pagination = query.order_by(Vehicle.id.desc()).paginate(
        page=page, per_page=5, error_out=False)
    
    return render_template(
        'admin/kendaraan_list.html',
        active_menu='kendaraan',
        total_vehicles=total_vehicles,
        rented_vehicle_ids=rented_vehicle_ids,
        inactive_vehicles=inactive_vehicles,
        available_vehicles=available_vehicles,
        pagination=pagination,
        q=q,
        search=q,
        **admin_context()
    )



# ═════════════════════════════════════════════════════════════
#   HELPER FUNCTIONS UNTUK HALAMAN TAMBAH / EDIT KENDARAAN
# ═════════════════════════════════════════════════════════════
# Batas unggah foto. Aturan ini diperiksa ulang di server karena
# validasi di browser (accept dan 2 MB) mudah dilewati.
ALLOWED_IMAGE_EXT = {'jpg', 'jpeg', 'png', 'webp'}
MAX_IMAGE_BYTES = 2 * 1024 * 1024

# Pilihan dropdown yang sah. Harus sama dengan <option> di kendaraan_tambah.html dan kendaraan_edit.html.
VEHICLE_TYPES = ('SUV', 'MPV', 'Sedan', 'Motor')
TRANSMISSIONS = ('Otomatis', 'Manual')
FUELS = ('Bensin', 'Solar', 'Listrik')
RENTAL_TYPES = ('Sopir & Tanpa Sopir', 'Tanpa Sopir', 'Dengan Sopir')


# PEMBERSIH & PENGUBAH NILAI
# ---------------------------------------------------------
def _to_int(value, default=None):
    """'12' -> 12, '' / None / 'abc' -> default."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _clean(value):
    """Teks kosong menjadi None. Wajib untuk kolom unik: dua '' dianggap duplikat."""
    value = (value or '').strip()
    return value or None


def _allowed(options, current, attr):
    """Opsi standar + nilai lama milik unit ini (mis. 'Mobil', 'Automatic').
    Tanpa ini, menyimpan unit dari data seed akan ditolak atau memaksa nilainya berubah."""
    old = getattr(current, attr, None) if current is not None else None
    return tuple(options) + ((old,) if old else ())


# PEMBACAAN & VALIDASI FORM
# ---------------------------------------------------------
# Kunci form berbahasa Indonesia (merek, tipe, ...) dipetakan ke
# nama kolom model (brand, model, ...). Mengembalikan (data, error);
# error berisi None bila seluruh validasi lolos.
def _read_vehicle_form(form, current=None):
    """Ambil dan bersihkan isi form. `current` = unit yang sedang diubah (None saat tambah).
    Return (data, pesan_error)."""
    # Plat: huruf besar dan spasi ganda dirapikan menjadi satu spasi.
    # No. mesin & rangka: huruf besar, atau None bila kosong.
    # Bagasi default 0 karena kolom tidak boleh NULL.
    data = {
        'brand': (form.get('merek') or '').strip(),
        'model': (form.get('tipe') or '').strip(),
        'year': _to_int(form.get('tahun')),
        'color': _clean(form.get('warna')),
        'vehicle_number': ' '.join((form.get('plat_nomor') or '').upper().split()),
        'vehicle_type': form.get('kategori'),
        'transmission': form.get('transmisi'),
        'fuel': form.get('bahan_bakar'),
        'engine_cc': _to_int(form.get('cc_mesin')),
        'engine_number': (_clean(form.get('no_mesin')) or '').upper() or None,
        'chassis_number': (_clean(form.get('no_rangka')) or '').upper() or None,
        'price_per_day': _to_int(form.get('harga_sewa')),
        'rental_type': form.get('jenis_penyewaan'),
        'seats': _to_int(form.get('jumlah_penumpang')),
        'luggage': _to_int(form.get('jumlah_bagasi'), 0),  # kolom NOT NULL, default 0
        'facilities': _clean(form.get('fasilitas')),
        'notes': _clean(form.get('catatan_kondisi')),
    }

    # Validasi berurutan; berhenti di kesalahan pertama.
    if not data['brand'] or not data['model']:
        return data, 'Merek dan tipe wajib diisi.'
    if not data['vehicle_number']:
        return data, 'Plat nomor wajib diisi.'
    if data['year'] is None or not (1980 <= data['year'] <= datetime.now().year + 1):
        return data, 'Tahun tidak valid.'
    if data['vehicle_type'] not in _allowed(VEHICLE_TYPES, current, 'vehicle_type'):
        return data, 'Pilih kategori kendaraan.'
    if (data['transmission'] not in _allowed(TRANSMISSIONS, current, 'transmission')
            or data['fuel'] not in _allowed(FUELS, current, 'fuel')):
        return data, 'Transmisi atau bahan bakar tidak valid.'
    if data['rental_type'] not in _allowed(RENTAL_TYPES, current, 'rental_type'):
        return data, 'Jenis penyewaan tidak valid.'
    if data['price_per_day'] is None or data['price_per_day'] <= 0:
        return data, 'Harga sewa harus lebih dari 0.'
    if data['seats'] is None or data['seats'] < 1:
        return data, 'Jumlah penumpang minimal 1.'
    if data['luggage'] < 0 or (data['engine_cc'] is not None and data['engine_cc'] < 0):
        return data, 'Bagasi dan CC mesin tidak boleh negatif.'
    return data, None


# DATA AWAL FORM UBAH
# ---------------------------------------------------------
def _vehicle_to_form(v):
    """Nilai awal form ubah, dari database. Kuncinya = atribut name di form."""
    s = lambda x: '' if x is None else str(x)
    return {
        'merek': s(v.brand), 'tipe': s(v.model), 'tahun': s(v.year), 'warna': s(v.color),
        'kategori': s(v.vehicle_type), 'plat_nomor': s(v.vehicle_number),
        'transmisi': s(v.transmission), 'bahan_bakar': s(v.fuel),
        'cc_mesin': s(v.engine_cc), 'no_mesin': s(v.engine_number), 'no_rangka': s(v.chassis_number),
        'harga_sewa': s(v.price_per_day), 'jenis_penyewaan': s(v.rental_type),
        'jumlah_penumpang': s(v.seats), 'jumlah_bagasi': s(v.luggage),
        'fasilitas': s(v.facilities), 'catatan_kondisi': s(v.notes),
        'is_active': '1' if v.is_active else '',
    }


# PENCEGAHAN DUPLIKAT
# ---------------------------------------------------------
# exclude_id diisi saat mengubah, supaya unit tidak dianggap
# duplikat dirinya sendiri.
def _find_duplicate(data, exclude_id=None):
    """Cek plat / no. rangka / no. mesin yang sudah dipakai unit lain. Return pesan atau None."""
    for field, label in (('vehicle_number', 'Plat nomor'),
                         ('chassis_number', 'No. rangka'),
                         ('engine_number', 'No. mesin')):
        value = data[field]
        if not value:
            continue
        q = Vehicle.query.filter(getattr(Vehicle, field) == value)
        if exclude_id:
            q = q.filter(Vehicle.id != exclude_id)
        if q.first():
            return f'{label} "{value}" sudah terdaftar.'
    return None


# PENGELOLAAN FILE FOTO
# ---------------------------------------------------------
def _images_dir():
    # root_path = folder paket app/, jadi tidak bergantung pada folder tempat server dijalankan
    return os.path.join(current_app.root_path, 'static', 'images')


def _save_vehicle_photo(file_storage):
    """Validasi lalu simpan foto dengan nama unik. Return nama file; raise ValueError bila ditolak."""
    ext = os.path.splitext(file_storage.filename or '')[1].lower().lstrip('.')
    if ext not in ALLOWED_IMAGE_EXT:
        raise ValueError('Format foto harus JPG, PNG, atau WebP.')

    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_IMAGE_BYTES:
        raise ValueError('Ukuran foto maksimal 2 MB.')

    # Nama acak (UUID) mencegah foto unit lain tertimpa.
    # Ukuran dicek dengan seek ke akhir stream, tanpa membaca file.
    filename = f'{uuid.uuid4().hex}.{ext}'
    os.makedirs(_images_dir(), exist_ok=True)
    file_storage.save(os.path.join(_images_dir(), filename))
    return filename


def _delete_vehicle_photo(filename):
    """Hanya dipakai untuk membatalkan foto BARU yang gagal disimpan. Foto lama tidak pernah dihapus
    otomatis: bisa jadi masih dirujuk unit lain atau kolom gallery."""
    if not filename:
        return
    try:
        os.remove(os.path.join(_images_dir(), filename))
    except OSError:
        pass



# ═════════════════════════════════════════════════════════════
#   HALAMAN ADMIN: TAMBAH KENDARAAN
# ═════════════════════════════════════════════════════════════
@bp.route('/admin/kendaraan/tambah', methods=['GET', 'POST'])
@admin_required
def tambah_kendaraan():
    error = None

    # POST: tiap tahap hanya dijalankan bila tahap sebelumnya tidak menghasilkan error.
    if request.method == 'POST':
        data, error = _read_vehicle_form(request.form)

        if not error:
            error = _find_duplicate(data)

        # Foto wajib saat menambah unit baru.
        photo_name = None
        if not error:
            foto = request.files.get('photo')
            if not foto or not foto.filename:
                error = 'Foto kendaraan wajib diunggah.'
            else:
                try:
                    photo_name = _save_vehicle_photo(foto)
                except ValueError as e:
                    error = str(e)

        if not error:
            # Simpan data. Foto sudah tertulis di disk, jadi bila commit gagal, file itu harus dihapus agar tidak jadi sampah.
            db.session.add(Vehicle(
                photo=photo_name,
                is_active=bool(request.form.get('is_active')),
                **data
            ))
            try:
                db.session.commit()
            # Race condition: admin lain menyimpan plat yang sama di antara pengecekan dan commit. Dijaga oleh constraint unik.
            except IntegrityError:
                db.session.rollback()
                _delete_vehicle_photo(photo_name)
                error = 'Plat nomor, no. rangka, atau no. mesin sudah dipakai unit lain.'
            else:
                flash('Kendaraan berhasil ditambahkan.')
                return redirect(url_for('main.admin_kendaraan'))

    # GET, atau POST yang gagal: tampilkan form. Isian lama dikirim kembali lewat `form` agar tidak perlu mengetik ulang.
    return render_template(
        'admin/kendaraan_tambah.html',
        active_menu='kendaraan',
        form=request.form if request.method == 'POST' else None,
        error=error,
        **admin_context()
    )



# ═════════════════════════════════════════════════════════════
#   HALAMAN ADMIN: UBAH KENDARAAN
# ═════════════════════════════════════════════════════════════
@bp.route('/admin/kendaraan/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_kendaraan(id):
    vehicle = Vehicle.query.get_or_404(id)
    # Unit yang sedang disewa dikunci statusnya (tidak boleh dinonaktifkan).
    unit_out = vehicle.current_status == 'Disewa'
    error = None
    form = _vehicle_to_form(vehicle)

    # Checkbox yang disabled tidak ikut terkirim oleh browser. Karena itu, bila unit sedang disewa, status aktif TIDAK dibaca dari form dan tetap memakai nilai di database. Ini juga menjadi pengaman sebenarnya, sebab atribut disabled bisa dibuang lewat DevTools.
    if request.method == 'POST':
        form = request.form.to_dict()
        # Saat unit disewa, saklar status dikunci di tampilan (checkbox disabled tidak ikut terkirim).
        # Jadi status tidak boleh dibaca dari form, tetap pakai nilai di database.
        if unit_out:
            form['is_active'] = '1' if vehicle.is_active else ''
            wants_active = vehicle.is_active
        else:
            wants_active = bool(request.form.get('is_active'))

        # current=vehicle: nilai lama unit (mis. data seed) tetap dianggap sah.
        data, error = _read_vehicle_form(request.form, current=vehicle)

        if not error:
            error = _find_duplicate(data, exclude_id=vehicle.id)

        # Foto: bila ada file baru -> simpan. Bila tidak ada -> pastikan foto lama masih ada di disk.
        new_photo = None
        if not error:
            foto = request.files.get('photo')
            if foto and foto.filename:
                try:
                    new_photo = _save_vehicle_photo(foto)
                except ValueError as e:
                    error = str(e)
            elif not vehicle.photo or not os.path.exists(os.path.join(_images_dir(), vehicle.photo)):
                error = 'File foto lama tidak ditemukan. Unggah foto baru.'

        if not error:
            # Terapkan seluruh perubahan ke objek, lalu commit.
            for key, value in data.items():
                setattr(vehicle, key, value)
            vehicle.is_active = wants_active
            if new_photo:
                vehicle.photo = new_photo
            try:
                db.session.commit()
            # Foto baru dibatalkan; foto lama sengaja tidak pernah dihapus otomatis karena bisa dirujuk unit lain.
            except IntegrityError:
                db.session.rollback()
                _delete_vehicle_photo(new_photo)
                error = 'Plat nomor, no. rangka, atau no. mesin sudah dipakai unit lain.'
            else:
                flash('Data kendaraan berhasil diperbarui.')
                return redirect(url_for('main.admin_kendaraan'))

    return render_template(
        'admin/kendaraan_edit.html',
        active_menu='kendaraan',
        vehicle=vehicle,
        form=form,
        error=error,
        vehicle_out=unit_out,
        **admin_context()
    )


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
        reason = request.form.get('cancellation_reason', '').strip()[:500]
        ingin_batal = (
            'btn_tolak' in request.form
            or request.form.get('status') == Rental.STATUS_BATAL
        )

        if ingin_batal and _permohonan_pembatalan_pending(rental.id):
            flash(
                'Pesanan memiliki pengajuan pembatalan pelanggan. '
                'Gunakan tombol proses permohonan pembatalan.', 'error'
            )
            return redirect(url_for('main.admin_penyewaan_edit', id=rental.id))

        # Tombol Tolak
        if 'btn_tolak' in request.form:
            if not rental.can_cancel():
                flash('Pesanan di tahap ini tidak bisa dibatalkan.', 'error')
                return redirect(url_for('main.admin_penyewaan_edit', id=rental.id))
            _batalkan_oleh_admin(rental, reason)
            db.session.commit()
            flash('Penyewaan berhasil ditolak/dibatalkan.')
            return redirect(url_for('main.admin_penyewaan'))

        # Tombol Simpan
        # Select yang disabled tidak ikut terkirim, makanya ada fallback.
        new_status = request.form.get('status') or rental.status
        driver_id = request.form.get('driver_id')

        if new_status != rental.status:
            if not rental.can_admin_change_to(new_status):
                flash(
                    f'Status tidak bisa diubah dari "{rental.status}" '
                    f'ke "{new_status}".', 'error'
                )
                return redirect(url_for('main.admin_penyewaan_edit', id=rental.id))

            if new_status == Rental.STATUS_BATAL:
                _batalkan_oleh_admin(rental, reason)
            else:
                old_status = rental.change_status(new_status)
                if old_status:
                    db.session.add(Notification.status_changed(rental, old_status))
                    if (
                        rental.fine_amount > 0
                        and new_status in [Rental.STATUS_PENGEMBALIAN, Rental.STATUS_SELESAI]
                    ):
                        db.session.add(Notification.fine_issued(rental))

        if rental.with_driver and driver_id:
            rental.driver_id = None if driver_id == 'none' else int(driver_id)

        # Opsi pelunasan denda oleh admin
        if 'fine_paid' in request.form:
            rental.fine_paid = (request.form.get('fine_paid') == '1')

        db.session.commit()
        flash('Data penyewaan berhasil diperbarui.')
        return redirect(url_for('main.admin_penyewaan'))

    # ---- GET: tidak berubah dari kode lamamu ----
    cancellation = rental.latest_cancellation
    if (
        rental.status == Rental.STATUS_BATAL
        and cancellation is None
        and _rental_sudah_dibayar(rental)
    ):
        waktu_batal = (
            rental.status_history[-1].changed_at
            if rental.status_history
            else datetime.now()
        )
        cancellation = _catat_pembatalan_admin_berbayar(
            rental,
            rental.cancellation_reason,
            waktu_batal
        )
        db.session.commit()

    cancellation_steps = (
        cancellation.timeline_steps if cancellation else []
    )
    cancellation_completed_steps = (
        cancellation.completed_steps_count if cancellation else 0
    )

    return render_template(
        'admin/penyewaan_edit.html',
        active_menu='penyewaan',
        rental=rental,
        statuses=Rental.ALL_STATUS,
        drivers=drivers,
        cancellation=cancellation,
        cancellation_steps=cancellation_steps,
        cancellation_completed_steps=cancellation_completed_steps,
        perlu_refund=_rental_sudah_dibayar(rental),
        **admin_context()
    )


@bp.route('/admin/pelanggan')
@admin_required
def admin_pelanggan():
    return render_template('admin/placeholder.html', active_menu='pelanggan',
                           title='Pelanggan', icon='fa-users', **admin_context())

ALLOWED_IMG_EXT = {'jpg', 'jpeg', 'png', 'webp'}



# ═════════════════════════════════════════════════════════════
#   KELOLA PELANGGAN (admin_bp)  &  KELOLA ADMIN (superadmin_bp)
# ═════════════════════════════════════════════════════════════
import re
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from app.models import Customer, Admin, RentalStatusHistory

admin_bp = Blueprint('kelola_pelanggan', __name__, url_prefix='/admin/kelola-pelanggan')
superadmin_bp = Blueprint('kelola_admin', __name__, url_prefix='/superadmin/kelola-admin')



# ═════════════════════════════════════════════════════════════
#   PENJAGA AKSES
# ═════════════════════════════════════════════════════════════
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

    def _filtered(self, keyword):
        """Query dengan filter pencarian (nama / email / no. HP / kode ID seperti PLG001)."""
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
        return query

    def search(self, keyword, page):
        """Hasil pencarian dengan pagination."""
        return self._filtered(keyword).order_by(self.model.id).paginate(
            page=page, per_page=self.PER_PAGE, error_out=False)

    def search_all(self, keyword):
        """Semua hasil pencarian tanpa pagination (daftar dibuat bisa di-scroll)."""
        return self._filtered(keyword).order_by(self.model.id).all()

    def count(self, active_only=False):
        """Jumlah akun; active_only=True hanya yang berstatus aktif."""
        query = self.base_query()
        if active_only:
            query = query.filter(self.model.is_active.is_(True))
        return query.count()

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

    def rental_summary(self, rentals):
        """Total penyewaan & total transaksi (hanya pesanan Selesai) untuk kartu ringkasan."""
        total_spent = sum(r.total_price for r in rentals if r.status == Rental.STATUS_SELESAI)
        return len(rentals), total_spent

    @staticmethod
    def rental_group(rental):
        """Kelompok filter riwayat: selesai / batal / jalan (Berlangsung)."""
        if rental.status == Rental.STATUS_SELESAI:
            return 'selesai'
        if rental.status == Rental.STATUS_BATAL:
            return 'batal'
        return 'jalan'


# [OOP - PEWARISAN & ENKAPSULASI LOGIKA BISNIS]:
# Mewarisi BaseUserService dan mengarahkan 'model' ke class Admin,
# sekaligus mengenkapsulasi validasi pendaftaran dan upload foto admin.
class AdminService(BaseUserService):
    model = Admin

    EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    PHONE_RE = re.compile(r'^\+?\d{10,15}$')
    MIN_PASSWORD = 8
    ALLOWED_PHOTO_EXT = {'jpg', 'jpeg', 'png', 'webp'}

    def base_query(self):
        """Daftar administrator mencakup role 'admin' dan 'superadmin'."""
        return self.model.query.filter(self.model.role.in_(['admin', 'superadmin']))

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

    # Penyimpanan foto profil
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

    # [ Polimorfisme - class PelangganListView & AdminListView ]
    # Nama method sama, implementasi/perilaku berbeda sesuai kebutuhan kelas
    def get(self):
        keyword = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        selected = self.service.find(request.args.get('id', type=int))
        rentals = self.service.rental_history(selected) if selected else []
        total_rentals, total_spent = self.service.rental_summary(rentals)

        return render_template(
            'admin/pelanggan.html',
            active_menu='pelanggan',
            pagination=self.service.search(keyword, page),   # dipakai form status (halaman asal)
            customers=self.service.search_all(keyword),      # daftar scroll
            total_customers=self.service.count(),
            active_customers=self.service.count(active_only=True),
            selected=selected,
            rentals=rentals,
            rental_group=self.service.rental_group,
            total_rentals=total_rentals,
            total_spent=total_spent,
            keyword=keyword,
            **admin_context()
        )


# [OOP - PEWARISAN (MethodView)]: Menangani HTTP POST status pelanggan
class PelangganStatusView(MethodView):
    """Simpan perubahan status akun pelanggan (aktif / nonaktif)."""
    decorators = [admin_required]
    service = CustomerService()

    # [ Polimorfisme - class PelangganStatusView & AdminStatusView ]
    # Nama method sama, implementasi/perilaku berbeda sesuai kebutuhan kelas
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

    # [ Polimorfisme - class PelangganListView & AdminListView ]
    # Nama method sama, implementasi/perilaku berbeda sesuai kebutuhan kelas
    def get(self):
        keyword = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)

        # Aktivitas terbaru: diambil dari riwayat perubahan status pesanan
        activities = []
        for h in (RentalStatusHistory.query
                  .order_by(RentalStatusHistory.changed_at.desc()).limit(20).all()):
            rental = db.session.get(Rental, h.rental_id)
            activities.append({
                'booking_code': rental.booking_code if rental else '-',
                'old': h.old_status, 'new': h.new_status, 'time': h.changed_at,
            })

        return render_template(
            'admin/admin_list.html',
            active_menu='admin',
            pagination=self.service.search(keyword, page),   # dipakai form status (halaman asal)
            admins=self.service.search_all(keyword),         # daftar scroll
            total_admins=self.service.count(),
            active_admins=self.service.count(active_only=True),
            selected=self.service.find(request.args.get('id', type=int)),
            activities=activities,
            keyword=keyword,
            **admin_context()
        )


# [OOP - PEWARISAN (MethodView)]: Menangani mutasi status admin via HTTP POST
class AdminStatusView(MethodView):
    """Simpan perubahan status akun admin (aktif / nonaktif)."""
    decorators = [superadmin_required]
    service = AdminService()

    # [ Polimorfisme - class PelangganStatusView & AdminStatusView ]
    # Nama method sama, implementasi/perilaku berbeda sesuai kebutuhan kelas
    def post(self, user_id):
        target = self.service.get_or_404(user_id)
        active = request.form.get('is_active') == '1'
        if target.id == session.get('user_id') and not active:
            flash('Anda tidak dapat menonaktifkan akun Anda sendiri.')
            return redirect(url_for('kelola_admin.daftar', id=target.id))
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



# ═════════════════════════════════════════════════════════════
#   DAFTAR SOPIR 
# ═════════════════════════════════════════════════════════════
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



# ═════════════════════════════════════════════════════════════
#   TAMBAH SOPIR
# ═════════════════════════════════════════════════════════════
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
            ktp_photo=_save_driver_file(request.files.get('foto_ktp'), 'ktp'),
        )
        db.session.add(sopir)
        db.session.commit()
        flash(f'Sopir {nama} berhasil ditambahkan.')
        return redirect(url_for('main.admin_sopir'))

    return render_template('admin/sopir_tambah.html', active_menu='sopir', f={}, **admin_context())



# ═════════════════════════════════════════════════════════════
#   PROFIL + STATUS SOPIR
# ═════════════════════════════════════════════════════════════
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



# ═════════════════════════════════════════════════════════════
#   EDIT SOPIR
# ═════════════════════════════════════════════════════════════
@bp.route('/admin/sopir/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_sopir(id):
    sopir = Driver.query.get_or_404(id)

    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        telepon = request.form.get('telepon', '').strip()

        if not nama or not telepon:
            flash('Nama dan No. Handphone wajib diisi.')
            return render_template('admin/sopir_edit.html', active_menu='sopir',
                                   driver=sopir, **admin_context())

        # Simpan file baru (jika ada). Kolom yang tidak diunggah ulang tidak diubah.
        daftar = [
            ('foto_sopir', 'photo',     'foto'),
            ('foto_sim',   'sim_photo', 'sim'),
            ('foto_ktp',   'ktp_photo', 'ktp'),
        ]
        file_baru = {}
        for field, atribut, prefix in daftar:
            upload = request.files.get(field)
            if upload and upload.filename:
                nama_file = _save_driver_file(upload, prefix)
                if not nama_file:
                    # Format salah: hapus file baru yang sudah sempat tersimpan.
                    for f in file_baru.values():
                        _delete_driver_file(f)
                    flash('Format foto harus JPG, PNG, atau WebP.')
                    return render_template('admin/sopir_edit.html', active_menu='sopir',
                                           driver=sopir, **admin_context())
                file_baru[atribut] = nama_file

        # Catat file lama untuk dihapus setelah commit berhasil.
        file_lama = [getattr(sopir, a) for a in file_baru]

        sopir.name = nama
        sopir.phone = telepon
        sopir.address = request.form.get('alamat', '').strip()
        sopir.description = request.form.get('deskripsi', '').strip()
        for atribut, nama_file in file_baru.items():
            setattr(sopir, atribut, nama_file)

        db.session.commit()

        for f in file_lama:
            _delete_driver_file(f)

        flash(f'Data sopir {nama} berhasil diperbarui.')
        return redirect(url_for('main.admin_sopir_detail', id=sopir.id))

    return render_template('admin/sopir_edit.html', active_menu='sopir',
                           driver=sopir, **admin_context())



# ═════════════════════════════════════════════════════════════
#   PECAT (HAPUS) SOPIR
# ═════════════════════════════════════════════════════════════
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
    _delete_driver_file(sopir.ktp_photo)
    db.session.delete(sopir)   # rental lama otomatis dilepas (driver_id jadi NULL)
    db.session.commit()
    flash(f'Sopir {nama} telah diberhentikan.')
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



# ═════════════════════════════════════════════════════════════
#   HALAMAN ADMIN: LIVE TRACKING
# ═════════════════════════════════════════════════════════════
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
                'vehicle_type': v.vehicle_type,
                'driver_name': r.driver.name if r.with_driver and r.driver else "Tanpa Sopir",
                'lat': v.current_lat,
                'lng': v.current_lng
            })
            
    # Simpan pergeseran kordinat ke database
    db.session.commit()
    return jsonify(data)