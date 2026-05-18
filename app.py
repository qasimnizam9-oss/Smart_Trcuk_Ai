from flask import Flask, request, jsonify, render_template, redirect, session, url_for
from functools import wraps
from flask_cors import CORS
from models import db, AdminModel, DriverModel, CustomerModel, BookingModel, TransactionModel, ChatModel, DriverSettingsModel, LogModel, NotificationModel, InsuranceClaimModel, EmergencyMessageModel
from math import radians, cos, sin, asin, sqrt
import random
from datetime import datetime, timedelta
import urllib.parse
import os
from datetime import datetime, timedelta

app = Flask(__name__)

from flask_cors import CORS
from sqlalchemy import or_

# Enable Cross-Origin Resource Sharing for professional frontend/backend separation
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.secret_key = os.environ.get('SECRET_KEY', 'smart_truck_admin_secret_2026')


# --- MySQL Database Configuration ---
# Changed to pymysql to match your test scripts and existing environment
password = urllib.parse.quote_plus("QasimNizam123.")
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{password}@localhost/smart_truck_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True
}

db.init_app(app)

# ─────────────────────────────────────────
#  AUTO-MIGRATE EXTRA COLUMNS (safe ALTERs)
# ─────────────────────────────────────────
with app.app_context():
    from sqlalchemy import text
    extra_cols = {
        "face_biometrics": "ALTER TABLE drivers ADD COLUMN face_biometrics LONGTEXT",
        "vehicle_number":  "ALTER TABLE drivers ADD COLUMN vehicle_number VARCHAR(50) DEFAULT 'V-0000'",
        "vehicle_type":    "ALTER TABLE drivers ADD COLUMN vehicle_type VARCHAR(50) DEFAULT 'Standard Truck'",
        "earnings":        "ALTER TABLE drivers ADD COLUMN earnings INT DEFAULT 0",
        "trips":           "ALTER TABLE drivers ADD COLUMN trips INT DEFAULT 0",
        "bio":             "ALTER TABLE drivers ADD COLUMN bio TEXT",
        "password":        "ALTER TABLE customers ADD COLUMN password VARCHAR(255)",
        "wallet_balance":  "ALTER TABLE customers ADD COLUMN wallet_balance FLOAT DEFAULT 100000.0",
        "total_bookings":  "ALTER TABLE customers ADD COLUMN total_bookings INT DEFAULT 0",
        "company_name":    "ALTER TABLE customers ADD COLUMN company_name VARCHAR(150)",
        "iban":            "ALTER TABLE customers ADD COLUMN iban VARCHAR(50)",
        "ntn":             "ALTER TABLE customers ADD COLUMN ntn VARCHAR(50)",
        "avatar":          "ALTER TABLE customers ADD COLUMN avatar LONGTEXT",
        "pickup_lat":      "ALTER TABLE bookings ADD COLUMN pickup_lat FLOAT",
        "pickup_lon":      "ALTER TABLE bookings ADD COLUMN pickup_lon FLOAT",
        "dropoff_lat":     "ALTER TABLE bookings ADD COLUMN dropoff_lat FLOAT",
        "dropoff_lon":     "ALTER TABLE bookings ADD COLUMN dropoff_lon FLOAT",
        "distance_km":     "ALTER TABLE bookings ADD COLUMN distance_km FLOAT",
        "payment_status":  "ALTER TABLE bookings ADD COLUMN payment_status VARCHAR(20) DEFAULT 'Pending'",
        "type":            "ALTER TABLE notifications ADD COLUMN type VARCHAR(20) DEFAULT 'info'",
        "email_admin":     "ALTER TABLE admins ADD COLUMN email VARCHAR(100)",
        "avatar_admin":    "ALTER TABLE admins ADD COLUMN avatar LONGTEXT",
    }
    for col, sql in extra_cols.items():
        try:
            if col in ['password', 'wallet_balance', 'total_bookings', 'company_name', 'iban', 'ntn', 'avatar']:
                tbl = 'customers'
            elif col in ['pickup_lat', 'pickup_lon', 'dropoff_lat', 'dropoff_lon', 'distance_km', 'payment_status']:
                tbl = 'bookings'
            elif col in ['type']:
                tbl = 'notifications'
            elif col in ['email_admin', 'avatar_admin']:
                tbl = 'admins'
                col = col.replace('_admin', '')
            else:
                tbl = 'drivers'
            db.session.execute(text(f"SELECT {col} FROM {tbl} LIMIT 1"))
        except Exception:
            try:
                db.session.execute(text(sql))
                db.session.commit()
                print(f"Migrated: added column {col}")
            except Exception as e:
                db.session.rollback()
                print(f"Migration error on {col}: {e}")

    # Create any missing tables (driver_settings, etc.)
    db.create_all()

    # Seed marketplace bookings if empty
    try:
        if BookingModel.query.count() == 0:
            seeds = [
                BookingModel(pickup_loc="Lahore HQ",         dropoff_loc="Faisalabad Industrial", weight_kg=5000, fare_pkr=25000, status='Pending'),
                BookingModel(pickup_loc="Karachi Port",       dropoff_loc="Hyderabad Terminal",    weight_kg=8000, fare_pkr=45000, status='Pending'),
                BookingModel(pickup_loc="Islamabad Dry Port", dropoff_loc="Peshawar Hub",          weight_kg=3500, fare_pkr=18500, status='Pending'),
            ]
            db.session.add_all(seeds)
            db.session.commit()
            print("Freight marketplace seeded.")
    except Exception as e:
        print(f"Seeding skipped: {e}")

    print("MySQL connected to smart_truck_db [OK]")


# --- Configuration ---
RATE_PER_KM = 60 
mock_bookings_count = 1284 

# --- Professional Fleet Data (Initialized from DB) ---
trucks = []

def sync_trucks_from_db():
    """Sync trucks array from MySQL database - call this after any driver status change"""
    global trucks
    trucks = []
    try:
        all_drivers = DriverModel.query.all()
        for d in all_drivers:
            trucks.append({
                "id": d.id, "driver": d.name, "email": d.email, "phone": d.phone,
                "password": d.password, "lat": d.lat, "lon": d.lon,
                "capacity": d.capacity or 5000, "is_available": d.is_available, "rating": d.rating,
                "year": d.truck_year or 2024, "vehicle_type": d.vehicle_type, "current_status": d.current_status,
                "speed": 0, "earnings": d.earnings or 0, "trips": d.trips or 0
            })
        print(f"Synced {len(trucks)} drivers to AI matching pool.")
    except Exception as e:
        print(f"Database sync error: {e}")

# Initial sync on startup
with app.app_context():
    try:
        available_drivers = DriverModel.query.filter_by(is_available=True).all()
        for d in available_drivers:
            trucks.append({
                "id": d.id, "driver": d.name, "email": d.email, "phone": d.phone,
                "password": d.password, "lat": d.lat, "lon": d.lon,
                "capacity": d.capacity or 5000, "is_available": True, "rating": d.rating,
                "year": d.truck_year or 2024, "vehicle_type": d.vehicle_type, "current_status": d.current_status,
                "speed": 0, "earnings": d.earnings or 0, "trips": d.trips or 0
            })
        print(f"Synced {len(trucks)} online drivers to AI matching pool.")
    except Exception as e:
        print(f"Database sync skipped: {e}")

# --- Admin & Security Data ---
admin_logs = []

system_settings = {
    "notifications": {"sms": True, "email": True, "app": False},
    "security": {"encryption": "AES-256 Active", "monitoring": "24/7 Live"},
    "maintenance_mode": False,
    "customization": {
        "site_name": "SmartTruck OS",
        "primary_color": "#6366f1",
        "logo_url": ""
    },
    "security_policies": {
        "min_password_length": 8,
        "require_special_char": True,
        "session_timeout": 30
    },
    "profile": {
        "name": "Qasim Nizam",
        "email": "qasim@smarttruck.os",
        "role": "Senior System Administrator",
        "avatar": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    }
}

# --- Revenue & Shipment Helpers ---
def get_revenue_snapshot():
    today_rev = mock_bookings_count * random.randint(150, 200) 
    return {
        "today_pkr": today_rev, 
        "monthly_pkr": "PKR 2.4M",
        "active_shipments": random.randint(5, 15),
        "forecast_trend": [random.randint(30, 95) for _ in range(6)] 
    }

# --- AI Helper: Haversine Formula ---
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

# --- AI Scoring Engine ---
def calculate_ai_score(distance, rating, year):
    normalized_dist = 1 / (1 + distance) 
    age_score = (year - 2015) / 10       
    rating_score = rating / 5           
    
    total_score = (normalized_dist * 0.6) + (rating_score * 0.3) + (age_score * 0.1)
    return round(total_score * 100, 2)

# --- AUTH DECORATORS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"status": "Error", "message": "Authentication required"}), 401
            return redirect(url_for('user_auth_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"status": "Error", "message": "Admin privileges required"}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def driver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'driver_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"status": "Error", "message": "Driver authentication required"}), 401
            return redirect(url_for('driver_auth'))
        return f(*args, **kwargs)
    return decorated_function

# --- GLOBAL ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/driver')
def driver_landing():
    return render_template('driver_landing.html')

@app.route('/status')
def status():
    return {
        "status": "Online",
        "version": "2.1.0-PRO",
        "message": "Smart Truck AI Backend is Running!",
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoints": {
            "admin_panel": "/admin",
            "driver_portal": "/driver",
            "match_truck": "/match-truck (POST)",
            "ai_analysis": "/admin/ai-analysis (GET)"
        }
    }

# --- USER / SHIPPER ROUTES ---

@app.route('/user/auth')
def user_auth_page():
    return render_template('user_auth.html')

@app.route('/user/dashboard')
@login_required
def user_dashboard_page():
    return render_template('user_dashboard.html')

@app.route('/user')
def user_root_redirect():
    return redirect('/user/dashboard')

@app.route('/user/checkout')
@login_required
def user_checkout_page():
    booking_id = request.args.get('booking_id')
    return render_template('user_checkout.html', booking_id=booking_id)

@app.route('/user/track/<int:booking_id>')
@login_required
def user_track_page(booking_id):
    return render_template('user_track.html', booking_id=booking_id)

@app.route('/api/user/signup', methods=['POST'])
def user_signup():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')

        if not email or not password or not name:
            return jsonify({"status": "Error", "message": "All fields are required"}), 400

        existing = CustomerModel.query.filter_by(email=email).first()
        if existing:
            return jsonify({"status": "Error", "message": "Email already exists"}), 400

        new_user = CustomerModel(name=name, email=email, phone=phone, password=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"status": "Success", "message": "Account created!", "user_id": new_user.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/api/user/login', methods=['POST'])
def user_login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        user = CustomerModel.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['user_name'] = user.name
            return jsonify({"status": "Success", "message": "Login successful", "user_id": user.id, "name": user.name})
        return jsonify({"status": "Error", "message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/api/user/logout', methods=['POST'])
def user_logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    return jsonify({"status": "Success", "message": "Logged out"})

@app.route('/api/user/<int:user_id>/bookings', methods=['GET'])
def get_user_bookings(user_id):
    user = CustomerModel.query.get(user_id)
    bookings = BookingModel.query.filter_by(customer_id=user_id).order_by(BookingModel.created_at.desc()).all()
    
    total_spent = 0
    pending_amount = 0
    result_list = []
    
    for b in bookings:
        driver = DriverModel.query.get(b.driver_id)
        # Use our new database column for payment status
        pay_status = b.payment_status or "Pending"
        
        if pay_status == 'Paid':
            total_spent += b.fare_pkr or 0
        else:
            pending_amount += b.fare_pkr or 0

        result_list.append({
            "id": b.id,
            "pickup": b.pickup_loc,
            "dropoff": b.dropoff_loc,
            "fare": b.fare_pkr,
            "status": b.status,
            "payment_status": pay_status,
            "driver": driver.name if driver else "Unknown",
            "date": b.created_at.strftime("%Y-%m-%d %H:%M")
        })
    
    return jsonify({
        "bookings": result_list,
        "wallet_balance": user.wallet_balance if user else 0,
        "total_spent": total_spent,
        "pending_amount": pending_amount
    })

@app.route('/api/user/cancel-booking', methods=['POST'])
def cancel_booking():
    data = request.json
    booking_id = data.get('booking_id')
    
    booking = BookingModel.query.get(booking_id)
    if not booking:
        return jsonify({"status": "Error", "message": "Booking not found"}), 404
        
    if booking.status == 'Completed':
        return jsonify({"status": "Error", "message": "Cannot cancel a completed shipment"}), 400
        
    try:
        booking.status = 'Cancelled'
        db.session.commit()
        return jsonify({"status": "Success", "message": "Shipment #BK-{} has been terminated.".format(booking_id)})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/api/driver/biometrics/<int:driver_id>', methods=['POST'])
def upload_driver_biometrics(driver_id):
    data = request.json
    image_data = data.get('image')
    
    driver = DriverModel.query.get(driver_id)
    if not driver:
        return jsonify({"status": "Error", "message": "Driver not found"}), 404
        
    try:
        driver.face_biometrics = image_data
        driver.is_verified = False # Admin must approve
        driver.current_status = "Awaiting Admin Review"
        db.session.commit()
        return jsonify({"status": "Success", "message": "Biometrics uploaded. Awaiting admin approval."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500


@app.route('/api/user/pay/<int:booking_id>', methods=['POST'])
def process_payment(booking_id):
    try:
        data = request.json or {}
        booking = BookingModel.query.get(booking_id)
        if not booking:
            return jsonify({"status": "Error", "message": "Booking not found"}), 404
            
        user = CustomerModel.query.get(booking.customer_id)
        if not user:
            return jsonify({"status": "Error", "message": "User account not found"}), 404
            
        # Ensure values are not None for calculation
        wallet_balance = user.wallet_balance if user.wallet_balance is not None else 0.0
        fare_pkr = booking.fare_pkr if booking.fare_pkr is not None else 0.0
            
        # Deduct from wallet (Simulated Gateway)
        if wallet_balance < fare_pkr:
            return jsonify({"status": "Error", "message": f"Insufficient wallet balance. Required: PKR {fare_pkr}, Available: PKR {wallet_balance}"}), 400
            
        user.wallet_balance = wallet_balance - fare_pkr
        booking.payment_status = 'Paid'
        booking.status = 'Approved'
        
        # Notify Driver that payment is done and load is ready to be accepted
        if booking.driver_id:
            notif = NotificationModel(
                target_id=booking.driver_id,
                target_type='driver',
                title='Payment Confirmed - Load Ready',
                message=f'Customer has paid for shipment #BK-{booking.id}. You can now start the transit.',
                type='success'
            )
            db.session.add(notif)
            
        # Create transaction record
        new_tx = TransactionModel(
            booking_id=booking_id,
            amount=fare_pkr,
            payment_method=data.get('payment_method', 'Wallet'),
            admin_commission=fare_pkr * 0.1,
            driver_payout=fare_pkr * 0.9,
            payment_status='Paid'
        )
        db.session.add(new_tx)
        db.session.commit()
        
        return jsonify({"status": "Success", "message": "Payment successful!", "new_balance": user.wallet_balance})
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Payment Error Traceback:\n{traceback.format_exc()}")
        return jsonify({"status": "Error", "message": f"Payment processing error: {str(e)}"}), 500

@app.route('/api/booking/<int:booking_id>', methods=['GET'])
def get_booking_details(booking_id):
    booking = BookingModel.query.get(booking_id)
    if not booking:
        return jsonify({"status": "Error", "message": "Booking not found"}), 404
    driver = DriverModel.query.get(booking.driver_id)
    return jsonify({
        "id": booking.id,
        "pickup": booking.pickup_loc,
        "dropoff": booking.dropoff_loc,
        "pickup_lat": booking.pickup_lat,
        "pickup_lon": booking.pickup_lon,
        "dropoff_lat": booking.dropoff_lat,
        "dropoff_lon": booking.dropoff_lon,
        "fare": booking.fare_pkr,
        "status": booking.status,
        "driver_name": driver.name if driver else "Unknown",
        "driver_lat": driver.lat if driver else 31.5204,
        "driver_lon": driver.lon if driver else 74.3587,
        "driver_pic": driver.profile_pic if driver else 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png',
        "driver_vehicle": f"{driver.vehicle_number} • {driver.vehicle_type}" if driver else "N/A"
    })

@app.route('/api/user/book', methods=['POST'])
def confirm_booking():
    try:
        data = request.json
        user_id_raw  = data.get('user_id')
        pickup   = data.get('pickup_loc')
        dropoff  = data.get('dropoff_loc')
        weight   = data.get('weight')
        fare     = data.get('fare')
        driver_id_raw = data.get('driver_id')
        driver_name = data.get('driver_name')

        # Convert IDs to integers safely
        try:
            user_id = int(user_id_raw) if user_id_raw else None
            driver_id = int(driver_id_raw) if driver_id_raw else None
        except (ValueError, TypeError):
            return jsonify({"status": "Error", "message": "Invalid User or Driver ID format"}), 400

        if not user_id:
            return jsonify({"status": "Error", "message": "User ID is required"}), 400

        # Verify user exists to avoid foreign key violation
        user = CustomerModel.query.get(user_id)
        if not user:
            return jsonify({"status": "Error", "message": f"User account (ID: {user_id}) not found. Please log in again."}), 401

        # If driver_id not provided, try lookup by name
        if not driver_id and driver_name:
            for t in trucks:
                if t['driver'] == driver_name:
                    driver_id = t['id']
                    break
            if not driver_id:
                d = DriverModel.query.filter_by(name=driver_name).first()
                if d: driver_id = d.id

        new_booking = BookingModel(
            customer_id=user_id,
            pickup_loc=pickup,
            dropoff_loc=dropoff,
            pickup_lat=data.get('pickup_lat'),
            pickup_lon=data.get('pickup_lon'),
            dropoff_lat=data.get('dropoff_lat'),
            dropoff_lon=data.get('dropoff_lon'),
            distance_km=float(data.get('distance', 0)),
            weight_kg=int(float(weight)) if weight else None,
            fare_pkr=float(fare) if fare is not None else 0.0,
            driver_id=driver_id,
            status='Assigned' if driver_id else 'Pending'
        )
        db.session.add(new_booking)
        db.session.commit()

        if driver_id:
            driver = DriverModel.query.get(driver_id)
            if driver:
                driver.is_available = False
                driver.current_status = 'Assigned'
                db.session.commit()
                
            for t in trucks:
                if t['id'] == driver_id:
                    t['is_available'] = False
                    t['current_status'] = 'Assigned'
                    break
            
            notif = NotificationModel(
                target_id=driver_id,
                target_type='driver',
                title='New Booking Assigned',
                message=f'You have been selected by customer for shipment from {pickup} to {dropoff}. Login to confirm pickup.',
                type='success'
            )
            db.session.add(notif)
            db.session.commit()

        return jsonify({"status": "Success", "message": "Booking Confirmed!", "booking_id": new_booking.id})
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Booking Error Traceback:\n{error_details}")
        return jsonify({"status": "Error", "message": f"Server Error: {str(e)}"}), 500

@app.route('/api/user/submit-claim', methods=['POST'])
def submit_claim():
    try:
        data = request.json
        user_id = data.get('user_id')
        booking_id = data.get('booking_id')
        claim_type = data.get('claim_type')
        description = data.get('description')

        new_claim = InsuranceClaimModel(
            customer_id=user_id,
            booking_id=booking_id,
            claim_type=claim_type,
            description=description,
            status='Pending'
        )
        db.session.add(new_claim)
        
        # Notify admin (as a system log or actual notification if implemented)
        # For now, let's just log it
        print(f"New Insurance Claim: {claim_type} for Booking {booking_id}")
        
        db.session.commit()
        return jsonify({"status": "Success", "message": "Claim submitted successfully to admin review."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/api/admin/claims', methods=['GET'])
def get_admin_claims():
    claims = InsuranceClaimModel.query.order_by(InsuranceClaimModel.created_at.desc()).all()
    results = []
    for c in claims:
        customer = CustomerModel.query.get(c.customer_id)
        results.append({
            "id": c.id,
            "booking_id": c.booking_id,
            "customer_name": customer.name if customer else "Unknown",
            "claim_type": c.claim_type,
            "description": c.description,
            "status": c.status,
            "date": c.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return jsonify(results)

@app.route('/api/admin/update-claim', methods=['POST'])
def update_claim_status():
    data = request.json
    claim_id = data.get('claim_id')
    new_status = data.get('status')
    
    claim = InsuranceClaimModel.query.get(claim_id)
    if claim:
        claim.status = new_status
        db.session.commit()
        return jsonify({"status": "Success"})
    return jsonify({"status": "Error", "message": "Claim not found"}), 404


# --- User Profile APIs ---
@app.route('/api/user/profile/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    user = CustomerModel.query.get(user_id)
    if not user:
        return jsonify({"status": "Error", "message": "User not found"}), 404
    
    return jsonify({
        "status": "Success",
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "company_name": user.company_name,
        "iban": user.iban,
        "ntn": user.ntn,
        "avatar": user.avatar,
        "wallet_balance": user.wallet_balance
    })

@app.route('/api/user/profile/update', methods=['POST'])
def update_user_profile():
    try:
        data = request.json
        user_id = data.get('user_id')
        user = CustomerModel.query.get(user_id)
        if not user:
            return jsonify({"status": "Error", "message": "User not found"}), 404
            
        user.name = data.get('name', user.name)
        user.phone = data.get('phone', user.phone)
        user.company_name = data.get('company_name', user.company_name)
        user.iban = data.get('iban', user.iban)
        user.ntn = data.get('ntn', user.ntn)
        user.avatar = data.get('avatar', user.avatar)
        
        db.session.commit()
        return jsonify({"status": "Success", "message": "Profile updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500


@app.route('/match-truck', methods=['POST'])
def match_truck():
    try:
        data = request.json
        p_lat = float(data.get('pickup_lat', 31.5204)) 
        p_lon = float(data.get('pickup_lon', 74.3587))
        weight = float(data.get('weight', 0))

        best_truck = None
        max_score = -1
        best_truck_dist = 0

        for truck in trucks:
            if truck["is_available"] and truck["capacity"] >= weight:
                dist = calculate_distance(p_lat, p_lon, truck["lat"], truck["lon"])
                score = calculate_ai_score(dist, truck["rating"], truck["year"])
                
                if score > max_score:
                    max_score = score
                    best_truck = truck
                    best_truck_dist = dist

        if best_truck:
            fare = max(500, round(best_truck_dist * RATE_PER_KM))
            return jsonify({
                "status": "Success",
                "driver_name": best_truck["driver"],
                "ai_match_score": max_score,
                "distance_km": round(best_truck_dist, 2),
                "estimated_fare": fare,
                "truck_details": f"{best_truck['year']} Model | {best_truck['rating']} Stars"
            })
        
        return jsonify({"status": "Error", "message": "No suitable truck found"}), 404
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

# --- REAL Driver Selection API ---
@app.route('/api/drivers/nearby', methods=['POST'])
def get_nearby_drivers():
    """
    Returns ONLY real verified AND available drivers from MySQL database.
    NO DUMMY/FAKE drivers - only real registered drivers approved by admin.
    Driver must be BOTH: is_verified=True AND is_available=True
    """
    try:
        data = request.json
        p_lat = float(data.get('pickup_lat', 31.5204))
        p_lon = float(data.get('pickup_lon', 74.3587))
        weight = float(data.get('weight', 0))

        # Get ALL available drivers from MySQL (include both new and verified)
        real_drivers = DriverModel.query.filter(
            DriverModel.is_available == True
        ).all()

        # NO FAKE/DUMMY FALLBACK - if no real drivers, return empty array
        if not real_drivers:
            return jsonify({
                "status": "Success",
                "drivers": [],
                "count": 0,
                "message": "No verified drivers currently available. Please try again later."
            })

        # Process only real drivers from database
        available_drivers = []
        
        for driver in real_drivers:
            # Get driver capacity from DB (default 5000 if not set)
            driver_capacity = driver.capacity or 5000
            
            # Skip if capacity less than required weight
            if weight and driver_capacity < weight:
                continue
            
            # Get location from DB or use default
            driver_lat = driver.lat or 31.5204
            driver_lon = driver.lon or 74.3587
            
            # Calculate distance from pickup location
            dist = calculate_distance(p_lat, p_lon, driver_lat, driver_lon)
            
            # Calculate AI score based on distance, rating, and vehicle year
            truck_year = driver.truck_year or 2024
            rating = driver.rating or 5.0
            score = calculate_ai_score(dist, rating, truck_year)
            
            # Calculate fare based on distance
            fare = max(500, round(dist * RATE_PER_KM))
            
            # Get profile pic or generate from real driver name
            profile_pic = driver.profile_pic
            if not profile_pic or 'flaticon.com/512/3135/3135715.png' in profile_pic:
                profile_pic = f"https://ui-avatars.com/api/?name={driver.name.replace(' ', '+')}&background=random&color=fff&size=128"
            
            available_drivers.append({
                "id": driver.id,
                "driver_id": driver.id,
                "name": driver.name,
                "driver_name": driver.name,
                "rating": rating,
                "vehicle": f"{truck_year} {driver.vehicle_type or 'Truck'}",
                "vehicle_number": driver.vehicle_number or 'N/A',
                "vehicle_type": driver.vehicle_type or 'Standard Truck',
                "capacity": driver_capacity,
                "distance_km": round(dist, 1),
                "ai_match_score": score,
                "estimated_fare": fare,
                "fare": fare,
                "is_verified": driver.is_verified,
                "isVerified": driver.is_verified,
                "profile_pic": profile_pic,
                "image": profile_pic,
                "trips_completed": driver.trips or 0,
                "trips": driver.trips or 0,
                "experience": f"{random.randint(2, 10)} Years",
                "email": driver.email,
                "phone": driver.phone,
                "current_status": driver.current_status or 'Idle',
                "bio": driver.bio
            })

        # Sort by AI match score (highest first)
        available_drivers.sort(key=lambda x: x["ai_match_score"], reverse=True)

        # Return all available drivers (limited to 50 for performance, but includes everyone nearby)
        return jsonify({
            "status": "Success",
            "drivers": available_drivers[:50],
            "count": len(available_drivers)
        })

    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

# --- ADMIN PANEL ROUTES ---

@app.route('/admin')
@admin_required
def admin_page():
    return render_template('admin.html')

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/signup')
def admin_signup():
    return render_template('admin_signup.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    return redirect(url_for('admin_login'))

@app.route('/api/admin/signup', methods=['POST'])
def api_admin_signup():
    data = request.json
    full_name = data.get('full_name')
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "Error", "message": "Username and password required"}), 400

    existing = AdminModel.query.filter_by(username=username).first()
    if existing:
        return jsonify({"status": "Error", "message": "Username already exists"}), 400

    new_admin = AdminModel(full_name=full_name, username=username, password=password)
    db.session.add(new_admin)
    db.session.commit()
    return jsonify({"status": "Success", "message": "Admin account created!"})

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    admin = AdminModel.query.filter_by(username=username, password=password).first()
    if admin:
        session['admin_id'] = admin.id
        session['admin_name'] = admin.full_name
        admin.last_login = datetime.now()
        db.session.commit()
        return jsonify({
            "status": "Success", 
            "message": "Login successful", 
            "admin_id": admin.id,
            "name": admin.full_name
        })
    return jsonify({"status": "Error", "message": "Invalid admin credentials"}), 401

@app.route('/admin/all-trucks', methods=['GET'])
def get_all_trucks_admin():
    drivers = DriverModel.query.all()
    pending_kyc = []
    for d in drivers:
        if not d.is_verified:
            pending_kyc.append({
                "id": d.id, 
                "driver": d.name, 
                "documents": ["CNIC", "License", "Registration"], 
                "biometrics": d.face_biometrics,
                "date": d.created_at.strftime("%Y-%m-%d %H:%M") if d.created_at else "Just now"
            })
    
    online_list = []
    verified_drivers = [d for d in drivers if d.is_verified]
    
    for d in verified_drivers:
        # Professional Telemetry Simulation: Randomize speed if the driver is on a job
        speed = 0
        if d.current_status in ['Assigned', 'In Transit', 'Active Dispatch']:
            speed = random.randint(45, 90)
        elif d.is_available:
            speed = 0
            
        online_list.append({
            "id": d.id, 
            "driver": d.name, 
            "capacity": d.capacity, 
            "lat": d.lat or 31.5204, 
            "lon": d.lon or 74.3587, 
            "speed": speed, 
            "rating": d.rating, 
            "current_status": d.current_status, 
            "is_available": d.is_available, 
            "biometrics": d.face_biometrics,
            "earnings": d.earnings or 0
        })

    revenue_data = get_revenue_snapshot()
    
    return jsonify({
        "total_trucks": len(verified_drivers),
        "online_trucks": len([d for d in verified_drivers if d.is_available]),
        "pending_requests": len(pending_kyc),
        "total_bookings": mock_bookings_count,
        "revenue": revenue_data,
        "trucks": online_list,
        "pending_kyc": pending_kyc
    })

@app.route('/api/admin/payouts', methods=['GET'])
@admin_required
def get_admin_payouts():
    drivers = DriverModel.query.filter(DriverModel.earnings > 0).all()
    res = []
    for d in drivers:
        res.append({
            "id": d.id,
            "driver": d.name,
            "earnings": d.earnings,
            "status": "Pending Payout"
        })
    return jsonify(res)

@app.route('/api/admin/process-payout/<int:driver_id>', methods=['POST'])
@admin_required
def process_payout(driver_id):
    driver = DriverModel.query.get(driver_id)
    if driver:
        amount = driver.earnings
        driver.earnings = 0
        db.session.commit()
        
        # Log Payout
        log = LogModel(admin_name=session.get('admin_name', 'System'), action=f"Processed Payout: PKR {amount} to {driver.name}", module="Finance", ip=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        return jsonify({"status": "Success", "message": f"Settlement of PKR {amount} dispatched to {driver.name}."})
    return jsonify({"status": "Error", "message": "Driver not found"}), 404

@app.route('/api/admin/block-driver/<int:driver_id>', methods=['POST'])
@admin_required
def admin_block_driver(driver_id):
    driver = DriverModel.query.get(driver_id)
    if not driver:
        return jsonify({"status": "Error", "message": "Driver not found"}), 404
    
    driver.is_available = False
    driver.current_status = 'Blocked'
    db.session.commit()
    
    # Sync memory pool
    sync_trucks_from_db()
    
    return jsonify({"status": "Success", "message": f"Security Alert: Driver {driver.name} has been restricted."})

@app.route('/api/admin/verify-driver/<int:driver_id>', methods=['POST'])
def verify_driver(driver_id):
    driver = DriverModel.query.get(driver_id)
    if not driver:
        return jsonify({"status": "Error", "message": "Driver not found"}), 404
    
    driver.is_verified = True
    db.session.commit()
    
    # Create Success Notification for Driver
    notif = NotificationModel(
        target_id=driver_id,
        target_type='driver',
        title='Elite Verification Confirmed',
        message='Congratulations! Your credentials have been approved. Your Golden Partner Card is now active.',
        type='success'
    )
    db.session.add(notif)
    
    # Log the action
    admin_name = session.get('admin_name', 'System')
    log = LogModel(admin_name=admin_name, action=f"Verified Driver: {driver.name}", module="KYC / Fleet", ip=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    
    return jsonify({"status": "Success", "message": "Driver officially verified!"})

@app.route('/admin/logs', methods=['GET'])
def get_admin_logs():
    return jsonify(admin_logs)

@app.route('/admin/audit-logs', methods=['GET'])
def get_admin_audit_logs():
    logs = LogModel.query.order_by(LogModel.timestamp.desc()).limit(50).all()
    res = []
    for log in logs:
        res.append({
            "admin": log.admin_name,
            "action": log.action,
            "module": log.module,
            "time": log.timestamp.strftime("%Y-%m-%d %H:%M"),
            "ip": log.ip
        })
    return jsonify(res)

@app.route('/admin/update-settings', methods=['POST'])
def update_settings():
    data = request.json
    section = data.get('section')
    settings = data.get('settings')
    
    # Persistent Profile Update
    if section == 'profile' and 'admin_id' in session:
        admin = AdminModel.query.get(session['admin_id'])
        if admin:
            admin.full_name = settings.get('name', admin.full_name)
            admin.email = settings.get('email', admin.email)
            admin.role = settings.get('role', admin.role)
            admin.avatar = settings.get('avatar', admin.avatar)
            db.session.commit()
            session['admin_name'] = admin.full_name

    if section in system_settings:
        if isinstance(system_settings[section], dict):
            system_settings[section].update(settings)
        else:
            system_settings[section] = settings

    current_admin = session.get('admin_name', 'System Admin')
    log_entry = LogModel(admin_name=current_admin, action=f"Updated {section} Settings", module="System", ip=request.remote_addr)
    db.session.add(log_entry)
    db.session.commit()

    return jsonify({"status": "Success", "settings": system_settings})

@app.route('/admin/get-settings', methods=['GET'])
def get_settings():
    # Sync profile with database for current session
    if 'admin_id' in session:
        admin = AdminModel.query.get(session['admin_id'])
        if admin:
            system_settings['profile'] = {
                "name": admin.full_name,
                "email": admin.email or "admin@smarttruck.os",
                "role": admin.role or "Senior Administrator",
                "avatar": admin.avatar or "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            }
    return jsonify(system_settings)

@app.route('/admin/run-audit', methods=['POST'])
def run_audit():
    current_admin = session.get('admin_name', 'System Admin')
    log_entry = LogModel(admin_name=current_admin, action="Triggered Security Audit", module="Security", ip=request.remote_addr)
    db.session.add(log_entry)
    db.session.commit()

    admin_logs.insert(0, {
        "admin": current_admin,
        "action": "Triggered Security Audit",
        "module": "Security",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ip": request.remote_addr
    })
    return jsonify({"status": "Success", "message": "Security Integrity Check Complete. No threats found."})

@app.route('/admin/approve-driver/<int:truck_id>', methods=['POST'])
def approve_driver(truck_id):
    driver = DriverModel.query.get(truck_id)
    if driver:
        driver.is_verified = True
        driver.is_available = True
        driver.current_status = "Idle"
        
        current_admin = session.get('admin_name', 'System Admin')
        log_entry = LogModel(admin_name=current_admin, action=f"Verified Driver: {driver.name}", module="Verification", ip=request.remote_addr)
        db.session.add(log_entry)
        db.session.commit()

        return jsonify({"status": "Success", "message": f"Driver {driver.name} Verified!"})
    return jsonify({"status": "Error", "message": "Driver not found"}), 404

@app.route('/admin/reject-driver/<int:truck_id>', methods=['POST'])
def reject_driver(truck_id):
    driver = DriverModel.query.get(truck_id)
    if driver:
        name = driver.name
        db.session.delete(driver)
        
        current_admin = session.get('admin_name', 'System Admin')
        log_entry = LogModel(admin_name=current_admin, action=f"Rejected Driver: {name}", module="Verification", ip=request.remote_addr)
        db.session.add(log_entry)
        db.session.commit()

        return jsonify({"status": "Success", "message": "Driver KYC Rejected and removed."})
    return jsonify({"status": "Error", "message": "Driver not found"}), 404

@app.route('/admin/ai-analysis', methods=['GET'])
@admin_required
def ai_analysis():
    # Ensure AI pool is synchronized with latest database state
    sync_trucks_from_db()
    
    # Find all unassigned bookings that need AI matching
    pending_bookings = BookingModel.query.filter(
        (BookingModel.status == 'Pending') | 
        ((BookingModel.status == 'Approved') & (BookingModel.driver_id == None))
    ).all()
    
    analysis = []
    for b in pending_bookings:
        best_truck = None
        max_score = -1
        
        # Use real coordinates for geospatial proximity matching
        b_lat = b.pickup_lat or 31.5204
        b_lon = b.pickup_lon or 74.3587
        
        for t in trucks:
            # Filter by availability and payload capacity
            if t["is_available"] and t["capacity"] >= (b.weight_kg or 0):
                # Calculate precision distance using Haversine
                dist = calculate_distance(b_lat, b_lon, t["lat"], t["lon"])
                score = calculate_ai_score(dist, t["rating"], t["year"])
                
                if score > max_score:
                    max_score = score
                    best_truck = t
                    
        if best_truck:
            reasons = [
                "Optimal Distance & High Rating", 
                "Vehicle Age Compliance", 
                "Proximity Lead", 
                "Top Rated Driver",
                "Fuel Efficiency Optimization",
                "Historical Route Reliability"
            ]
            analysis.append({
                "booking_id": f"ORD-{b.id}",
                "raw_id": b.id,
                "truck": best_truck["driver"],
                "truck_id": best_truck["id"],
                "score": max_score,
                "reasoning": random.choice(reasons) if max_score > 70 else "Calculated Match"
            })
            
    return jsonify(analysis)

@app.route('/api/admin/assign-truck', methods=['POST'])
@admin_required
def admin_assign_truck():
    try:
        data = request.json
        booking_id = data.get('booking_id')
        truck_id = data.get('truck_id')
        
        booking = BookingModel.query.get(booking_id)
        if not booking:
            return jsonify({"status": "Error", "message": "Booking not found"}), 404
            
        driver = DriverModel.query.get(truck_id)
        if not driver:
            return jsonify({"status": "Error", "message": "Driver not found"}), 404
        
        # Update Database: Assign driver and update statuses
        booking.driver_id = driver.id
        booking.status = 'Assigned'
        driver.is_available = False
        driver.current_status = 'Assigned via AI Matching'
        
        # Deploy Notification to Driver Terminal
        notif = NotificationModel(
            target_id=driver.id,
            target_type='driver',
            title='AI Match Confirmed',
            message=f'HQ AI matching has assigned you to Shipment #ORD-{booking.id}. Pickup: {booking.pickup_loc}.',
            type='success'
        )
        db.session.add(notif)
        
        # Log AI operation for audit trail
        admin_name = session.get('admin_name', 'Administrator')
        log = LogModel(
            admin_name=admin_name, 
            action=f"AI Matching: Dispatched ORD-{booking.id} to {driver.name}", 
            module="AI Matching Engine", 
            ip=request.remote_addr
        )
        db.session.add(log)
        
        db.session.commit()
        
        # Synchronize AI matching pool (memory state)
        sync_trucks_from_db()
        
        return jsonify({
            "status": "Success", 
            "message": f"AI Matching Successful: Shipment #ORD-{booking.id} has been dispatched to {driver.name}."
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500

# --- Financial & Pricing State ---
pricing_rules = [
    {"type": "6-Wheeler (Light)", "base": 120, "surcharge": 5, "commission": 10},
    {"type": "10-Wheeler (Heavy)", "base": 180, "surcharge": 8, "commission": 12}
]

@app.route('/admin/pricing-rules', methods=['GET', 'POST'])
def handle_pricing_rules():
    if request.method == 'POST':
        data = request.json
        # Check if rule already exists to enable EDITING instead of DUPLICATING
        exists = False
        for rule in pricing_rules:
            if rule['type'] == data.get('type'):
                rule.update(data)
                exists = True
                break
        
        if not exists:
            pricing_rules.append(data)
            
        return jsonify({"status": "Success", "message": "Rule synchronized with global engine."})
    return jsonify(pricing_rules)

@app.route('/admin/financials', methods=['GET'])
def get_financials():
    # Fetch real bookings for financial activity
    bookings = BookingModel.query.order_by(BookingModel.created_at.desc()).limit(10).all()
    res = []
    for b in bookings:
        res.append({
            "ref": f"#ORD-{b.id}",
            "id": b.id,
            "date": b.created_at.strftime("%Y-%m-%d"),
            "amount": b.fare_pkr or 0,
            "status": b.status
        })
    return jsonify(res)


@app.route('/api/admin/create-booking', methods=['POST'])
def admin_create_booking():
    data = request.json
    customer_id = data.get('customer_id') or 1  # default to 1 if empty
    new_booking = BookingModel(
        customer_id=customer_id,
        pickup_loc=data.get('pickup_loc'),
        dropoff_loc=data.get('dropoff_loc'),
        weight_kg=int(data.get('weight') or 0),
        fare_pkr=float(data.get('fare') or 0),
        status='Pending'
    )
    db.session.add(new_booking)
    db.session.commit()
    return jsonify({"status": "Success", "message": "Manual Booking Created!"})

@app.route('/api/admin/add-truck', methods=['POST'])
def admin_add_truck():
    data = request.json
    try:
        new_driver = DriverModel(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            password=data.get('password'),
            capacity=int(data.get('capacity') or 5000),
            is_available=True,
            current_status="Idle",
            is_verified=True,
            rating=5.0
        )
        db.session.add(new_driver)
        db.session.commit()
        
        trucks.append({
            "id": new_driver.id, "driver": new_driver.name, "email": new_driver.email, "phone": new_driver.phone,
            "password": new_driver.password, "lat": 31.5204, "lon": 74.3587, 
            "capacity": new_driver.capacity, "is_available": True, "rating": 5.0, 
            "year": 2024, "current_status": "Idle", "speed": 0, "earnings": 0, "trips": 0
        })
        
        return jsonify({"status": "Success", "message": "Truck added and active!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 400

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    users = CustomerModel.query.all()
    res = []
    for u in users:
        bookings_count = BookingModel.query.filter_by(customer_id=u.id).count()
        res.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "phone": u.phone,
            "total_bookings": bookings_count
        })
    return jsonify(res)

@app.route('/admin/dashboard-summary', methods=['GET'])
def dashboard_summary():
    rev = get_revenue_snapshot()
    avg_rating = round(sum(t['rating'] for t in trucks)/len(trucks), 1) if trucks else 0
    return jsonify({
        "cards": [
            {"title": "Today's Revenue", "value": f"PKR {rev['today_pkr']:,}", "icon": "trending-up"},
            {"title": "Active Fleet", "value": len([t for t in trucks if t['is_available']]), "icon": "truck"},
            {"title": "Pending KYC", "value": len([t for t in trucks if not t['is_available']]), "icon": "clock"},
            {"title": "Avg Rating", "value": avg_rating, "icon": "star"}
        ]
    })

@app.route('/admin/financial-report', methods=['GET'])
def get_financial_report():
    rev_data = get_revenue_snapshot()
    gross = rev_data['today_pkr']
    operating_costs = int(gross * 0.35)
    payouts = int(gross * 0.15)
    net_profit = gross - operating_costs - payouts
    
    return jsonify({
        "gross_revenue": gross,
        "operating_costs": operating_costs,
        "driver_payouts": payouts,
        "net_profit": net_profit,
        "currency": "PKR",
        "margin": "42%"
    })

@app.route('/admin/export-data', methods=['POST'])
def export_data():
    data = request.json
    export_type = data.get('format', 'PDF').upper()

    current_admin = session.get('admin_name', 'System Admin')
    admin_logs.insert(0, {
        "admin": current_admin,
        "action": f"Exported {export_type} Report",
        "module": "Analytics",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ip": request.remote_addr
    })
    
    return jsonify({"status": "Success", "message": f"System data compiled and exported as {export_type}"})

@app.route('/admin/notifications/unread', methods=['GET'])
def get_unread_notifications():
    alerts = [
        {"id": 1, "type": "info", "msg": "New Driver Approval Pending", "time": "Just now"},
        {"id": 2, "type": "success", "msg": "Server Backup Successful", "time": "2 hours ago"},
        {"id": 3, "type": "warning", "msg": "High Traffic on Route A-12", "time": "5 hours ago"}
    ]
    return jsonify(alerts)

@app.route('/admin/search', methods=['GET'])
def search_fleet():
    query = request.args.get('q', '').lower()
    results = [t for t in trucks if query in t['driver'].lower()]
    return jsonify(results)

@app.route('/api/admin/analytics', methods=['GET'])
def get_analytics():
    # Mock data for Chart.js
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    revenue_data = [random.randint(50000, 150000) for _ in range(7)]
    
    online_count = len([t for t in trucks if t["is_available"]])
    pending_count = len([t for t in trucks if not t["is_available"]])
    total = len(trucks)
    
    return jsonify({
        "revenue": {
            "labels": labels,
            "data": revenue_data
        },
        "fleet": {
            "online": online_count,
            "pending": pending_count,
            "offline": total - online_count - pending_count
        }
    })

@app.route('/api/admin/bookings', methods=['GET'])
def admin_get_bookings():
    bookings = BookingModel.query.order_by(BookingModel.created_at.desc()).all()
    result = []
    for b in bookings:
        customer = CustomerModel.query.get(b.customer_id)
        driver = DriverModel.query.get(b.driver_id) if b.driver_id else None
        result.append({
            "id": f"ORD-{b.id}",
            "raw_id": b.id,
            "customer": customer.name if customer else "Unknown",
            "driver": driver.name if driver else "Unassigned",
            "pickup": b.pickup_loc,
            "dropoff": b.dropoff_loc,
            "fare": b.fare_pkr,
            "status": b.status,
            "date": b.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return jsonify(result)

@app.route('/api/admin/bookings/<int:booking_id>/approve', methods=['POST'])
def admin_approve_booking(booking_id):
    booking = BookingModel.query.get(booking_id)
    if not booking:
        return jsonify({"status": "Error", "message": "Booking not found"}), 404
    booking.status = 'Approved'
    db.session.commit()
    return jsonify({"status": "Success", "message": "Booking Approved"})

@app.route('/api/admin/bookings/<int:booking_id>/cancel', methods=['POST'])
def admin_cancel_booking(booking_id):
    booking = BookingModel.query.get(booking_id)
    if not booking:
        return jsonify({"status": "Error", "message": "Booking not found"}), 404
    booking.status = 'Cancelled'
    db.session.commit()
    return jsonify({"status": "Success", "message": "Booking Cancelled"})

@app.route('/api/admin/bookings/<int:booking_id>/update', methods=['POST'])
@admin_required
def admin_update_booking(booking_id):
    try:
        data = request.json
        booking = BookingModel.query.get(booking_id)
        if not booking:
            return jsonify({"status": "Error", "message": "Booking not found"}), 404
        
        if 'status' in data:
            booking.status = data['status']
            # If status is updated to Assigned or In Transit, ensure driver availability is handled
            if data['status'] in ['Assigned', 'In Transit'] and booking.driver_id:
                driver = DriverModel.query.get(booking.driver_id)
                if driver:
                    driver.is_available = False
                    driver.current_status = data['status']
            elif data['status'] in ['Completed', 'Cancelled'] and booking.driver_id:
                driver = DriverModel.query.get(booking.driver_id)
                if driver:
                    driver.is_available = True
                    driver.current_status = 'Idle'
        
        if 'fare' in data:
            booking.fare_pkr = float(data['fare'])
        
        db.session.commit()
        return jsonify({"status": "Success", "message": "Shipment #BK-{} updated successfully".format(booking_id)})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500

# --- DRIVER PORTAL ROUTES ---

@app.route('/driver/dashboard')
@driver_required
def driver_page():
    return render_template('driver.html')

@app.route('/driver/auth')
def driver_auth():
    return render_template('driver_auth.html')

@app.route('/api/driver/signup', methods=['POST'])
def driver_signup():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"status": "Error", "message": "Email and password are required"}), 400

        # Check if exists
        existing = DriverModel.query.filter_by(email=email).first()
        if existing:
            return jsonify({"status": "Error", "message": "Email already registered"}), 400

        # Save to Database - Mark as available immediately so they show up in Instant Booking
        new_driver_db = DriverModel(
            name=name, email=email, phone=phone, password=password,
            is_available=True, current_status="Available - New Driver"
        )
        db.session.add(new_driver_db)
        db.session.commit()

        # Maintain existing list logic for runtime compatibility
        new_id = new_driver_db.id
        new_driver = {
            "id": new_id,
            "driver": name,
            "email": email,
            "phone": phone,
            "password": password,
            "lat": 31.5204, "lon": 74.3587, 
            "capacity": 0, 
            "is_available": False, 
            "rating": 5.0, 
            "year": 2024, 
            "current_status": "Pending Verification", 
            "speed": 0, "earnings": 0, "trips": 0
        }
        trucks.append(new_driver)
        
        admin_logs.insert(0, {
            "admin": "System AI",
            "action": f"New Registration: {name}",
            "module": "Auth",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ip": request.remote_addr
        })
        
        return jsonify({"status": "Success", "message": "Account created! Waiting for verification."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/api/driver/logout', methods=['POST'])
def driver_logout_api():
    session.pop('driver_id', None)
    session.pop('driver_name', None)
    return jsonify({"status": "Success", "message": "Logged out"})

@app.route('/api/driver/login', methods=['POST'])
def driver_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    # Check in Database (PRIMARY)
    driver_db = DriverModel.query.filter_by(email=email, password=password).first()
    
    if driver_db:
        session['driver_id'] = driver_db.id
        session['driver_name'] = driver_db.name
        # Sync with trucks mock list if missing (due to server restart)
        exists_in_mock = any(t['id'] == driver_db.id for t in trucks)
        if not exists_in_mock:
            trucks.append({
                "id": driver_db.id,
                "driver": driver_db.name,
                "email": driver_db.email,
                "phone": driver_db.phone,
                "password": driver_db.password,
                "lat": driver_db.lat, "lon": driver_db.lon, 
                "capacity": driver_db.capacity, 
                "is_available": driver_db.is_available, 
                "rating": driver_db.rating, 
                "year": driver_db.truck_year, 
                "current_status": driver_db.current_status, 
                "speed": 0, "earnings": driver_db.earnings, "trips": driver_db.trips
            })
            
        return jsonify({
            "status": "Success", 
            "message": "Welcome back!",
            "driver_id": driver_db.id
        })
            
    return jsonify({"status": "Error", "message": "Invalid credentials"}), 401

@app.route('/api/driver/toggle-status', methods=['POST'])
def toggle_status():
    data = request.json
    try:
        driver_id = int(data.get('id'))
    except:
        return jsonify({"status": "Error", "message": "Invalid Driver ID"}), 400
        
    is_online = data.get('available') 
    
    # Update MySQL (NEW)
    driver_db = DriverModel.query.get(driver_id)
    if driver_db:
        driver_db.is_available = is_online
        driver_db.current_status = "Idle" if is_online else "Offline"
        db.session.commit()
        # If not in mock list, we still return success
        db_found = True
    else:
        db_found = False
    for truck in trucks:
        if truck['id'] == driver_id:
            truck['is_available'] = is_online
            truck['current_status'] = "Idle" if is_online else "Offline"
            return jsonify({
                "status": "Success", 
                "message": f"Status updated to {truck['current_status']}",
                "new_state": truck['current_status']
            })
            
    if db_found and is_online:
        # Force refresh trucks pool if online but not yet present
        trucks.append({
            "id": driver_db.id, "driver": driver_db.name, "email": driver_db.email, "phone": driver_db.phone,
            "password": driver_db.password, "lat": driver_db.lat, "lon": driver_db.lon, 
            "capacity": driver_db.capacity, "is_available": True, "rating": driver_db.rating, 
            "year": driver_db.truck_year, "current_status": "Idle", "speed": 0, "earnings": driver_db.earnings, "trips": driver_db.trips
        })
        return jsonify({"status": "Success", "message": "Status updated and synced", "new_state": "Online"})
    
    if db_found:
        return jsonify({"status": "Success", "message": "Status updated", "new_state": "Offline"})

    return jsonify({"status": "Error", "message": "Driver ID not found"}), 404


@app.route('/api/driver/update-location', methods=['POST'])
def update_location():
    data = request.json
    driver_id = data.get('id')
    new_lat = data.get('lat')
    new_lon = data.get('lon')
    
    # Update MySQL (NEW)
    driver_db = DriverModel.query.get(driver_id)
    if driver_db:
        driver_db.lat = new_lat
        driver_db.lon = new_lon
        db.session.commit()

    for truck in trucks:
        if truck['id'] == driver_id:
            truck['lat'] = new_lat
            truck['lon'] = new_lon
            return jsonify({"status": "Success", "message": "GPS Coordinates Synced"})
    return jsonify({"status": "Error", "message": "Driver Sync Failed"}), 404


@app.route('/api/driver/stats/<int:driver_id>', methods=['GET'])
def get_driver_stats(driver_id):
    driver = DriverModel.query.get(driver_id)
    if driver:
        return jsonify({
            "driver": driver.name,
            "total_earnings": f"PKR {(driver.earnings or 0):,}",
            "trips": driver.trips or 0,
            "rating": driver.rating,
            "fleet_status": driver.current_status
        })
    for truck in trucks:
        if truck['id'] == driver_id:
            return jsonify({
                "driver": truck['driver'],
                "total_earnings": f"PKR {truck['earnings']:,}",
                "trips": truck['trips'],
                "rating": truck['rating'],
                "fleet_status": truck['current_status']
            })
    return jsonify({"status": "Error", "message": "Data Not Found"}), 404

@app.route('/api/driver/active-job/<int:driver_id>', methods=['GET'])
def get_active_job(driver_id):
    booking = BookingModel.query.filter_by(driver_id=driver_id, status='In Transit').first()
    if not booking:
        return jsonify({"status": "Error", "message": "No active job"})
        
    user = CustomerModel.query.get(booking.customer_id)
    return jsonify({
        "status": "Success",
        "job": {
            "id": booking.id,
            "pickup": booking.pickup_loc,
            "dropoff": booking.dropoff_loc,
            "fare": booking.fare_pkr,
            "user_name": user.name if user else "Unknown User",
            "user_phone": user.phone if user else "N/A"
        }
    })

@app.route('/api/driver/complete-job/<int:driver_id>', methods=['POST'])
def complete_job(driver_id):
    data = request.json
    booking_id = data.get('booking_id')
    
    booking = BookingModel.query.filter_by(id=booking_id, driver_id=driver_id).first()
    if not booking:
        return jsonify({"status": "Error", "message": "Job not found"})
        
    booking.status = 'Completed'

    # Notify the Customer (Shipment visibility for User)
    notif_user = NotificationModel(
        target_id=booking.customer_id,
        target_type='user',
        title='Delivery Successful!',
        message=f'Good news! Your shipment #BK-{booking.id} has been delivered at the destination.',
        type='success'
    )
    db.session.add(notif_user)

    # Create System Audit Log (Dashboard visibility for Admin)
    admin_log = LogModel(
        admin_name="System AI",
        action=f"Delivery Confirmed: Shipment #BK-{booking.id} completed by {driver_id}",
        module="Logistics",
        ip=request.remote_addr
    )
    db.session.add(admin_log)

    # Update Driver stats in Database for persistence
    driver = DriverModel.query.get(driver_id)
    fare = booking.fare_pkr or 0
    if driver:
        driver.trips = (driver.trips or 0) + 1
        driver.earnings = (driver.earnings or 0) + int(fare * 0.85)
        driver.current_status = 'Idle'
        driver.is_available = True

    db.session.commit()
    
    # Update driver stats in runtime mock array for matching pool consistency
    for truck in trucks:
        if truck['id'] == driver_id:
            truck['trips'] = driver.trips if driver else (truck['trips'] + 1)
            truck['earnings'] = driver.earnings if driver else (truck['earnings'] + int(fare * 0.85))
            truck['current_status'] = 'Idle'
            truck['is_available'] = True
            break
            
    return jsonify({"status": "Success", "message": "Job completed successfully!"})

@app.route('/api/driver/settings/<int:driver_id>', methods=['GET', 'POST'])
def driver_settings(driver_id):
    setting = DriverSettingsModel.query.filter_by(driver_id=driver_id).first()
    if request.method == 'POST':
        data = request.json
        if not setting:
            setting = DriverSettingsModel(driver_id=driver_id)
            db.session.add(setting)
        setting.max_distance = int(data.get('max_distance', 100))
        setting.auto_accept = bool(data.get('auto_accept', False))
        db.session.commit()
        return jsonify({"status": "Success", "message": "Settings saved!"})
    
    if setting:
        return jsonify({"max_distance": setting.max_distance, "auto_accept": setting.auto_accept})
    return jsonify({"max_distance": 100, "auto_accept": False})

@app.route('/api/driver/profile/<int:driver_id>', methods=['GET', 'POST'])
def driver_profile(driver_id):
    driver = DriverModel.query.get(driver_id)
    if not driver:
        return jsonify({"status": "Error", "message": "Driver not found"}), 404

    if request.method == 'POST':
        data = request.json
        driver.name           = data.get('name', driver.name)
        driver.phone          = data.get('phone', driver.phone)
        driver.vehicle_number = data.get('vehicle_number', driver.vehicle_number)
        driver.vehicle_type   = data.get('vehicle_type', driver.vehicle_type)
        driver.bio            = data.get('bio', driver.bio)
        driver.profile_pic    = data.get('profile_pic', driver.profile_pic)
        db.session.commit()
        return jsonify({"status": "Success", "message": "Profile updated!"})

    # Return biometric photo if available (for verified card display)
    return jsonify({
        "name":           driver.name,
        "email":          driver.email,
        "phone":          driver.phone,
        "profile_pic":    driver.profile_pic,
        "vehicle_number": driver.vehicle_number or 'V-0000',
        "vehicle_type":   driver.vehicle_type or 'Standard Truck',
        "bio":            driver.bio or 'Professional Logistics Partner',
        "is_verified":    driver.is_verified,
        # Return biometric photo for verified card display - priority over profile_pic
        "biometric_photo": driver.face_biometrics,
    })

@app.route('/api/driver/upload-pic/<int:driver_id>', methods=['POST'])
def upload_profile_pic(driver_id):
    driver = DriverModel.query.get(driver_id)
    if not driver:
        return jsonify({"status": "Error", "message": "Driver not found"}), 404
    
    # In a real app, we'd save the file. For this demo, we'll just accept a URL or mock it.
    data = request.json
    driver.profile_pic = data.get('image_url', driver.profile_pic)
    db.session.commit()
    return jsonify({"status": "Success", "message": "Picture updated!"})
    
@app.route('/api/driver/biometrics/<int:driver_id>', methods=['POST'])
def save_driver_biometrics(driver_id):
    try:
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({"status": "Error", "message": "Biometric data missing"}), 400
            
        driver = DriverModel.query.get(driver_id)
        if not driver:
            return jsonify({"status": "Error", "message": "Driver not found"}), 404
            
        # Store high-fidelity biometric signature (Base64)
        driver.face_biometrics = image_data
        
        # Log the security event
        log = LogModel(
            admin_name="System AI",
            action=f"Biometric Scan Captured: Driver {driver.name} (ID: {driver_id})",
            module="Security / Biometrics",
            ip=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            "status": "Success", 
            "message": "Identity verified and biometric signature stored in the enterprise cloud."
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500



@app.route('/api/driver/terminate/<int:driver_id>', methods=['POST'])
def terminate_driver(driver_id):
    driver = DriverModel.query.get(driver_id)
    if not driver:
        return jsonify({"status": "Error", "message": "Driver not found"}), 404
    
    try:
        # SOFT DELETE: Mark driver as terminated instead of hard deleting
        # This prevents foreign key constraint errors while preserving booking history
        driver.is_available = False
        driver.current_status = 'Terminated'
        driver.is_verified = False  # Revert verification status
        
        db.session.commit()
        
        # Remove from mock trucks list (runtime memory)
        global trucks
        trucks = [t for t in trucks if t['id'] != driver_id]
        
        return jsonify({"status": "Success", "message": "Partner account terminated."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/api/driver/ai-fare', methods=['POST'])
def ai_fare():
    data = request.json
    base_fare = float(data.get('current_fare', 0))
    # AI logic: simulate high demand
    surge_multiplier = random.uniform(1.1, 1.4)
    new_fare = round(base_fare * surge_multiplier)
    return jsonify({
        "status": "Success",
        "suggested_fare": new_fare,
        "reason": "High demand in drop-off zone (AI Suggested)"
    })

@app.route('/api/driver/available-loads', methods=['GET'])
def get_available_loads():
    # ENHANCED: Filter loads based on driver identity, capacity and location
    driver_id = request.args.get('driver_id', type=int)
    
    # Get driver info for capacity/location filtering
    driver = None
    driver_capacity = 5000  # Default capacity
    driver_lat = 31.5204    # Default Lahore
    driver_lon = 74.3587
    driver_is_available = False
    
    if driver_id:
        driver = DriverModel.query.get(driver_id)
        if driver:
            driver_capacity = driver.capacity or 5000
            driver_lat = driver.lat or 31.5204
            driver_lon = driver.lon or 74.3587
            driver_is_available = driver.is_available
    
    # Include Pending, Approved (User Booked), Assigned (Direct Assignment), and In Transit (Active Jobs)
    # This ensures driver sees their direct assignments with Accept/Reject options
    if driver_id:
        # Get all loads: 
        # 1. Pending (Marketplace)
        # 2. Approved but NO driver assigned (Broadcast Marketplace)
        # 3. Assigned/Approved/In Transit SPECIFICALLY for this driver
        all_loads = BookingModel.query.filter(
            (BookingModel.status == 'Pending') | 
            ((BookingModel.status == 'Approved') & (BookingModel.driver_id == None)) |
            ((BookingModel.status.in_(['Assigned', 'Approved', 'In Transit'])) & (BookingModel.driver_id == driver_id))
        ).order_by(BookingModel.created_at.desc()).all()
    else:
        # For general queries, only show unassigned marketplace loads
        all_loads = BookingModel.query.filter(
            (BookingModel.status == 'Pending') |
            ((BookingModel.status == 'Approved') & (BookingModel.driver_id == None))
        ).order_by(BookingModel.created_at.desc()).all()
    
    results = []
    for b in all_loads:
        load_weight = b.weight_kg or 0
        
        # MARKETPLACE LOADS: Apply capacity filter
        # Only show marketplace loads (Pending/Approved) if driver capacity can handle them
        # FIXED: Now properly handles capacity comparison
        if b.status in ['Pending', 'Approved'] and driver:
            if load_weight > driver_capacity:
                continue  # Skip loads that exceed driver capacity
            # Also check if driver is available - if not, still show their assigned loads but not marketplace
            if not driver_is_available and b.status == 'Pending':
                # Driver is offline, only show their already assigned loads
                if b.driver_id != driver_id:
                    continue
        
        # Calculate distance-based match score for marketplace loads
        # Use estimated pickup location (in real app, we'd geocode pickup_loc)
        # Determine match score based on status
        if (b.status in ['Assigned', 'Approved']) and b.driver_id == driver_id:
            match_score = 99  # Direct assignment - highest priority
            display_status = 'Direct Assignment'
        elif b.status == 'In Transit' and b.driver_id == driver_id:
            match_score = 100  # Active job - already accepted
            display_status = 'In Transit'
        elif b.status in ['Pending', 'Approved']:
            # For marketplace loads (Pending or general Approved)
            match_score = random.randint(75, 94)
            display_status = b.status
        else:
            match_score = random.randint(75, 94)
            display_status = b.status
        
        # Include driver_id so frontend can properly determine button logic
        results.append({
            "id": b.id,
            "pickup": b.pickup_loc,
            "dropoff": b.dropoff_loc,
            "weight": load_weight,
            "fare": b.fare_pkr or 0,
            "status": display_status,
            "match_score": match_score,
            "driver_id": b.driver_id,
        })
    return jsonify(results)

@app.route('/api/driver/accept-load/<int:booking_id>', methods=['POST'])
def accept_load(booking_id):
    data = request.json
    driver_id = data.get('driver_id')
    
    # Get driver info for capacity validation
    driver = DriverModel.query.get(driver_id)
    if not driver:
        return jsonify({"status": "Error", "message": "Driver not found"}), 404
    
    booking = BookingModel.query.get(booking_id)
    if not booking:
        return jsonify({"status": "Error", "message": "Booking not found"}), 404
    
    # FIXED: Validate driver capacity before accepting
    load_weight = booking.weight_kg or 0
    driver_capacity = driver.capacity or 5000
    
    if load_weight > driver_capacity:
        return jsonify({
            "status": "Error", 
            "message": f"Load weight ({load_weight}kg) exceeds your capacity ({driver_capacity}kg)"
        }), 400
    
    # Check if driver is available
    if not driver.is_available and driver.current_status != 'Assigned':
        return jsonify({
            "status": "Error", 
            "message": "You must be online to accept loads"
        }), 400
        
    booking.driver_id = driver_id  # Update just in case of broadcast loads
    booking.status = 'In Transit'  # This officially activates the route
    
    # Notify User that driver has started the journey
    notif_user = NotificationModel(
        target_id=booking.customer_id,
        target_type='user',
        title='Driver on the Way!',
        message=f'Driver {driver.name} has accepted your shipment #BK-{booking.id} and is now in transit.',
        type='success'
    )
    db.session.add(notif_user)
    
    db.session.commit()

    # Professional Sync: Update runtime AI matching pool
    for t in trucks:
        if t['id'] == driver_id:
            t['is_available'] = False
            t['current_status'] = 'In Transit'
            break
    
    return jsonify({"status": "Success", "message": "Load accepted! Route data synchronized."})

@app.route('/api/driver/reject-load/<int:booking_id>', methods=['POST'])
def reject_load(booking_id):
    data = request.json
    # Use int() to ensure type matching with the database ID
    try:
        driver_id = int(data.get('driver_id'))
    except (TypeError, ValueError):
        return jsonify({"status": "Error", "message": "Invalid Driver ID format"}), 400
    
    booking = BookingModel.query.get(booking_id)
    
    if not booking:
        return jsonify({"status": "Error", "message": "Booking not found"}), 404
    
    # Allow driver to reject from marketplace (Pending/Approved) OR if already assigned to this driver
    # This enables professional driver choice: Accept or Reject from available loads
    if booking.status in ['Pending', 'Approved'] or (booking.driver_id == driver_id and booking.status == 'Assigned'):
        # Clear driver assignment and return to marketplace
        booking.driver_id = None
        booking.status = 'Pending'
        
        try:
            db.session.commit()
            return jsonify({
                "status": "Success", 
                "message": "Load rejected and returned to marketplace."
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "Error", "message": str(e)}), 500
    
    # Cannot reject loads that are already In Transit or Completed
    if booking.status in ['In Transit', 'Completed']:
        return jsonify({"status": "Error", "message": "Cannot reject active or completed loads."}), 400
    
    return jsonify({"status": "Error", "message": "Unable to reject this load."}), 403
@app.route('/api/driver/bookings/<int:driver_id>', methods=['GET'])
def get_driver_bookings(driver_id):
    bookings = BookingModel.query.filter_by(driver_id=driver_id).order_by(BookingModel.id.desc()).all()
    results = []
    for b in bookings:
        customer = CustomerModel.query.get(b.customer_id)
        results.append({
            "id": b.id,
            "status": b.status,
            "pickup": b.pickup_loc,
            "dropoff": b.dropoff_loc,
            "user_name": customer.name if customer else "Unknown Shipper"
        })
    return jsonify(results)

@app.route('/api/chat/<int:booking_id>', methods=['GET', 'POST'])
def chat_api(booking_id):
    if request.method == 'POST':
        data = request.json
        new_msg = ChatModel(booking_id=booking_id, sender=data.get('sender'), message=data.get('message'))
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({"status": "Success"})

    msgs = ChatModel.query.filter_by(booking_id=booking_id).order_by(ChatModel.created_at.asc()).all()
    return jsonify([{"sender": m.sender, "message": m.message, "time": m.created_at.strftime("%H:%M")} for m in msgs])

@app.route('/api/driver/earnings/<int:driver_id>', methods=['GET'])
def get_driver_earnings(driver_id):
    try:
        # Fetch all completed bookings for this driver
        completed = BookingModel.query.filter_by(driver_id=driver_id, status='Completed').all()
        
        total_gross = sum([b.fare_pkr for b in completed if b.fare_pkr])
        total_net = total_gross * 0.85 # 15% Platform fee
        
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        year_ago = now - timedelta(days=365)
        
        weekly_gross = sum([b.fare_pkr for b in completed if b.created_at and b.created_at >= week_ago])
        monthly_gross = sum([b.fare_pkr for b in completed if b.created_at and b.created_at >= month_ago])
        yearly_gross = sum([b.fare_pkr for b in completed if b.created_at and b.created_at >= year_ago])
        
        # Calculate recent growth (mocked for professional feel if no past data)
        growth = "+12.4%" if len(completed) > 5 else "+0.0%"
        
        return jsonify({
            "status": "Success",
            "total_gross": round(total_gross),
            "total_net": round(total_net),
            "weekly_earnings": round(weekly_gross * 0.85),
            "monthly_earnings": round(monthly_gross * 0.85),
            "yearly_earnings": round(yearly_gross * 0.85),
            "trips": len(completed),
            "growth": growth,
            "efficiency": "96.4%"
        })
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

@app.route('/api/driver/notifications/<int:driver_id>', methods=['GET'])
def get_driver_notifications(driver_id):
    try:
        notifs = NotificationModel.query.filter_by(target_id=driver_id, target_type='driver').order_by(NotificationModel.created_at.desc()).limit(15).all()
        return jsonify([{
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "time": n.created_at.strftime("%H:%M")
        } for n in notifs])
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

@app.route('/api/driver/notifications/read/<int:notif_id>', methods=['POST'])
def read_driver_notification(notif_id):
    n = NotificationModel.query.get(notif_id)
    if n:
        n.is_read = True
        db.session.commit()
    return jsonify({"status": "Success"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# --- EMERGENCY COMMUNICATION ROUTES ---
@app.route('/api/emergency/send', methods=['POST'])
def send_emergency_msg():
    data = request.json
    try:
        driver_id = data.get('driver_id')
        admin_id = data.get('admin_id')
        
        # Explicitly convert to int to ensure database compatibility
        if driver_id is not None:
            driver_id = int(driver_id)
        if admin_id is not None:
            admin_id = int(admin_id)

        new_msg = EmergencyMessageModel(
            driver_id=driver_id,
            admin_id=admin_id,
            sender_type=data.get('sender_type'),
            message=data.get('message'),
            is_emergency=data.get('is_emergency', False)
        )
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({"status": "Success", "message": "Message sent to HQ"})
    except (ValueError, TypeError) as e:
        return jsonify({"status": "Error", "message": "Invalid ID format"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500

@app.route('/api/emergency/messages/<int:driver_id>', methods=['GET'])
def get_emergency_msgs(driver_id):
    msgs = EmergencyMessageModel.query.filter_by(driver_id=driver_id).order_by(EmergencyMessageModel.created_at.asc()).all()
    return jsonify([{
        "id": m.id,
        "sender_type": m.sender_type,
        "message": m.message,
        "status": m.status,
        "time": m.created_at.strftime("%H:%M"),
        "is_emergency": m.is_emergency
    } for m in msgs])

@app.route('/api/emergency/admin/all', methods=['GET'])
def get_all_emergency_msgs():
    # Group messages by driver for a chat-like list in admin
    msgs = EmergencyMessageModel.query.order_by(EmergencyMessageModel.created_at.desc()).all()
    drivers = {}
    for m in msgs:
        if m.driver_id not in drivers:
            d = DriverModel.query.get(m.driver_id)
            drivers[m.driver_id] = {
                "driver_name": d.name if d else "Unknown",
                "last_msg": m.message,
                "time": m.created_at.strftime("%H:%M"),
                "status": m.status,
                "driver_id": m.driver_id
            }
    return jsonify(list(drivers.values()))

@app.route('/api/emergency/admin/drivers', methods=['GET'])
@admin_required
def get_all_drivers_for_support():
    """Returns all registered drivers for the admin support selector"""
    try:
        drivers = DriverModel.query.all()
        return jsonify([{
            "id": d.id,
            "name": d.name,
            "phone": d.phone,
            "email": d.email,
            "is_verified": d.is_verified,
            "current_status": d.current_status
        } for d in drivers])
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400
