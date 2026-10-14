from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the database object
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configure the SQLite database
    # The database file will be created in the 'instance' folder automatically
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rentals.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-for-session-management'

    # Link the app to the database
    db.init_app(app)

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
        
        # --- SISTEM AUTO-HEAL (PERBAIKAN OTOMATIS) ---
        # Mencegah error "no such column" ketika teman kelompok melakukan push
        try:
            from .models import User, Vehicle, Rental, Review, Driver, Notification
            # Lakukan query palsu untuk memaksa SQLAlchemy mencocokkan skema dengan .db lokal
            db.session.query(User).first()
            db.session.query(Vehicle).first()
            db.session.query(Rental).first()
            db.session.query(Review).first()
            db.session.query(Driver).first()
            db.session.query(Notification).first()
        except Exception as e:
            print("\n==================================================================")
            print("[AUTO-FIX] Mendeteksi perubahan kode database dari teman kelompok!")
            print("[AUTO-FIX] Menyelaraskan dan mengisi ulang database secara otomatis...")
            print("==================================================================")
            
            # Kita bersihkan session yang error
            db.session.rollback()
            
            # Panggil file seed secara ajaib
            import seed
            seed.run_seed()
            print("==================================================================\n")

    return app
