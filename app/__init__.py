from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
load_dotenv()

# Initialize the database object
db = SQLAlchemy()
oauth = OAuth()

def create_app():
    app = Flask(__name__)
    
    # Configure the SQLite database
    # The database file will be created in the 'instance' folder automatically
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rentals.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-only-change-this-secret')
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

    # Link the app to the database
    db.init_app(app)

    oauth.init_app(app)

    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url=(
            'https://accounts.google.com/.well-known/openid-configuration'
        ),
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

    # Import routes and models inside the function to avoid circular imports
    from . import routes
    from . import models

    # Register the routes with the app
    app.register_blueprint(routes.bp)
    app.register_blueprint(routes.admin_bp)        # Kelola Pelanggan (Admin)
    app.register_blueprint(routes.superadmin_bp)   # Kelola Admin (Super Admin)
    
    # Create the database tables if they don't exist
    with app.app_context():
        db.create_all()
        
        # --- SISTEM AUTO-HEAL (MIGRASI SKEMA NON-DESTRUKTIF) ---
        # Menambahkan kolom baru secara otomatis (ALTER TABLE) tanpa menghapus
        # data akun/pesanan yang sudah ada ketika anggota tim melakukan git pull.
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

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

        for table_name, columns in migrations.items():
            if table_name in existing_tables:
                existing_cols = {c['name'] for c in inspector.get_columns(table_name)}
                for col_name, col_def in columns:
                    if col_name not in existing_cols:
                        db.session.execute(
                            text(f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}')
                        )
                        print(f"[AUTO-MIGRATE] Kolom '{col_name}' berhasil ditambahkan ke tabel '{table_name}'.")
        db.session.commit()

    return app

