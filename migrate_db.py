from app import db, app, DriverModel
from sqlalchemy import text

with app.app_context():
    try:
        # Check if columns exist
        db.session.execute(text("SELECT wallet_balance FROM customers LIMIT 1"))
        db.session.execute(text("SELECT payment_status FROM bookings LIMIT 1"))
        print("Financial columns already exist.")
    except Exception as e:
        print("Missing financial columns. Adding them...")
        try:
            db.session.execute(text("ALTER TABLE customers ADD COLUMN wallet_balance FLOAT DEFAULT 100000.0"))
            db.session.execute(text("ALTER TABLE bookings ADD COLUMN payment_status VARCHAR(20) DEFAULT 'Pending'"))
            db.session.commit()
            print("Financial migration successful.")
        except Exception as ex:
            print(f"Financial migration failed: {ex}")

    try:
        # Check if drivers columns exist
        db.session.execute(text("SELECT profile_pic, vehicle_number, vehicle_type, bio FROM drivers LIMIT 1"))
        print("Driver columns already exist.")
    except Exception as e:
        print("Missing driver columns. Adding them...")
        try:
            db.session.execute(text("ALTER TABLE drivers ADD COLUMN profile_pic VARCHAR(255) DEFAULT 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'"))
            db.session.execute(text("ALTER TABLE drivers ADD COLUMN vehicle_number VARCHAR(50) DEFAULT 'V-0000'"))
            db.session.execute(text("ALTER TABLE drivers ADD COLUMN vehicle_type VARCHAR(50) DEFAULT 'Standard Truck'"))
            db.session.execute(text("ALTER TABLE drivers ADD COLUMN bio TEXT DEFAULT 'Professional Logistics Partner'"))
            db.session.commit()
            print("Driver migration successful.")
        except Exception as ex:
            print(f"Driver migration failed: {ex}")
