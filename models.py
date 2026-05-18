from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class AdminModel(db.Model):
    __tablename__ = 'admins'
    id         = db.Column(db.Integer, primary_key=True)
    full_name  = db.Column(db.String(100))
    username   = db.Column(db.String(50), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(20), default='Super Admin')
    email      = db.Column(db.String(100))
    avatar     = db.Column(db.Text, default='https://cdn-icons-png.flaticon.com/512/3135/3135715.png')
    last_login = db.Column(db.DateTime)

class DriverModel(db.Model):
    __tablename__  = 'drivers'
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    email          = db.Column(db.String(100), unique=True, nullable=False)
    phone          = db.Column(db.String(20))
    password       = db.Column(db.String(255), nullable=False)
    vehicle_type   = db.Column(db.String(50))
    truck_year     = db.Column(db.Integer)
    capacity       = db.Column(db.Integer, default=5000)
    bio            = db.Column(db.Text)
    profile_pic    = db.Column(db.Text, default='https://cdn-icons-png.flaticon.com/512/3135/3135715.png')
    is_verified    = db.Column(db.Boolean, default=False)
    is_available   = db.Column(db.Boolean, default=False)
    current_status = db.Column(db.String(50), default='Pending')
    rating         = db.Column(db.Float, default=5.0)
    lat            = db.Column(db.Float, default=31.5204)
    lon            = db.Column(db.Float, default=74.3587)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    face_biometrics = db.Column(db.Text)
    vehicle_number  = db.Column(db.String(50), default='V-0000')
    earnings        = db.Column(db.Integer, default=0)
    trips           = db.Column(db.Integer, default=0)

class CustomerModel(db.Model):
    __tablename__    = 'customers'
    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(100), nullable=False)
    email            = db.Column(db.String(100), unique=True, nullable=False)
    phone            = db.Column(db.String(20))
    total_bookings   = db.Column(db.Integer, default=0)
    password         = db.Column(db.String(255))
    wallet_balance   = db.Column(db.Float, default=100000.0) # PKR Credits
    company_name     = db.Column(db.String(150))
    iban             = db.Column(db.String(50))
    ntn              = db.Column(db.String(50))
    avatar           = db.Column(db.Text)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

class BookingModel(db.Model):
    __tablename__ = 'bookings'
    id            = db.Column(db.Integer, primary_key=True)
    customer_id   = db.Column(db.Integer, db.ForeignKey('customers.id'))
    driver_id     = db.Column(db.Integer, db.ForeignKey('drivers.id'))
    pickup_loc    = db.Column(db.String(255))
    dropoff_loc   = db.Column(db.String(255))
    distance_km   = db.Column(db.Float)
    weight_kg     = db.Column(db.Integer)
    fare_pkr      = db.Column(db.Float)
    status        = db.Column(db.String(50), default='Pending')
    pickup_lat    = db.Column(db.Float)
    pickup_lon    = db.Column(db.Float)
    dropoff_lat   = db.Column(db.Float)
    dropoff_lon   = db.Column(db.Float)
    payment_status = db.Column(db.String(20), default='Pending') # 'Pending', 'Paid'
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

class TransactionModel(db.Model):
    __tablename__      = 'transactions'
    id                 = db.Column(db.Integer, primary_key=True)
    booking_id         = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    amount             = db.Column(db.Float)
    payment_method     = db.Column(db.String(50))
    admin_commission   = db.Column(db.Float)
    driver_payout      = db.Column(db.Float)
    payment_status     = db.Column(db.String(20), default='Unpaid')
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

class ChatModel(db.Model):
    __tablename__ = 'messages'
    id            = db.Column(db.Integer, primary_key=True)
    booking_id    = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    sender        = db.Column(db.String(20))
    message       = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

class DriverSettingsModel(db.Model):
    __tablename__  = 'driver_settings'
    id             = db.Column(db.Integer, primary_key=True)
    driver_id      = db.Column(db.Integer, db.ForeignKey('drivers.id'), unique=True)
    max_distance   = db.Column(db.Integer, default=100)
    auto_accept    = db.Column(db.Boolean, default=False)

class LogModel(db.Model):
    __tablename__ = 'admin_audit_logs'
    id          = db.Column(db.Integer, primary_key=True)
    admin_name  = db.Column(db.String(100))
    action      = db.Column(db.String(255))
    module      = db.Column(db.String(50))
    ip          = db.Column(db.String(45))
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)

class NotificationModel(db.Model):
    __tablename__ = 'notifications'
    id          = db.Column(db.Integer, primary_key=True)
    target_id   = db.Column(db.Integer) 
    target_type = db.Column(db.String(20)) # 'driver' or 'user'
    title       = db.Column(db.String(100))
    message     = db.Column(db.Text)
    is_read     = db.Column(db.Boolean, default=False)
    type        = db.Column(db.String(20), default='info') 
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class InsuranceClaimModel(db.Model):
    __tablename__ = 'insurance_claims'
    id            = db.Column(db.Integer, primary_key=True)
    booking_id    = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    customer_id   = db.Column(db.Integer, db.ForeignKey('customers.id'))
    claim_type    = db.Column(db.String(50)) # 'Cargo Damage', 'Excessive Delay'
    description   = db.Column(db.Text)
    status        = db.Column(db.String(20), default='Pending') # 'Pending', 'In Review', 'Resolved', 'Rejected'
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

class EmergencyMessageModel(db.Model):
    __tablename__ = 'emergency_messages'
    id            = db.Column(db.Integer, primary_key=True)
    driver_id     = db.Column(db.Integer, db.ForeignKey('drivers.id'))
    admin_id      = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    sender_type   = db.Column(db.String(20)) # 'driver' or 'admin'
    message       = db.Column(db.Text)
    is_emergency  = db.Column(db.Boolean, default=True)
    status        = db.Column(db.String(20), default='Open') # 'Open', 'Resolved'
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)