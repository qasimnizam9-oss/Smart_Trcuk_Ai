-- Smart Truck System MySQL Schema (Production Grade)
-- Version: 2.5.0
-- Compatible with MySQL 8.0+

CREATE DATABASE IF NOT EXISTS smart_truck_db;
USE smart_truck_db;

-- 1. Admins Table (Enhanced with Profile Persistence)
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'Super Admin',
    email VARCHAR(100),
    avatar LONGTEXT,
    last_login DATETIME
) ENGINE=InnoDB;

-- 2. Drivers Table (Fleet & AI Match Enabled)
CREATE TABLE IF NOT EXISTS drivers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password VARCHAR(255) NOT NULL,
    vehicle_type VARCHAR(50) DEFAULT 'Standard Truck',
    truck_year INT,
    capacity INT DEFAULT 5000,
    bio TEXT,
    profile_pic TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT FALSE,
    current_status VARCHAR(50) DEFAULT 'Pending',
    rating FLOAT DEFAULT 5.0,
    lat FLOAT DEFAULT 31.5204,
    lon FLOAT DEFAULT 74.3587,
    face_biometrics TEXT,
    vehicle_number VARCHAR(50) DEFAULT 'V-0000',
    earnings INT DEFAULT 0,
    trips INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. Customers (Shippers) Table
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password VARCHAR(255),
    wallet_balance FLOAT DEFAULT 100000.0,
    total_bookings INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. Bookings Table (Logistics Core)
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    driver_id INT,
    pickup_loc VARCHAR(255),
    dropoff_loc VARCHAR(255),
    pickup_lat FLOAT,
    pickup_lon FLOAT,
    dropoff_lat FLOAT,
    dropoff_lon FLOAT,
    distance_km FLOAT,
    weight_kg INT,
    fare_pkr FLOAT,
    status VARCHAR(50) DEFAULT 'Pending',
    payment_status VARCHAR(20) DEFAULT 'Pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 5. Transactions Table (Finance Hub)
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT,
    amount FLOAT,
    payment_method VARCHAR(50),
    admin_commission FLOAT,
    driver_payout FLOAT,
    payment_status VARCHAR(20) DEFAULT 'Unpaid',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. Messages (Communication Engine)
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT,
    sender VARCHAR(20),
    message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. Driver Settings (Custom Preferences)
CREATE TABLE IF NOT EXISTS driver_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    driver_id INT UNIQUE,
    max_distance INT DEFAULT 100,
    auto_accept BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. Audit Logs (System Security)
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_name VARCHAR(100),
    action VARCHAR(255),
    module VARCHAR(50),
    ip VARCHAR(45),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 9. Notifications (Real-time Alerts)
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    target_id INT,
    target_type VARCHAR(20), -- 'driver' or 'user'
    title VARCHAR(100),
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    type VARCHAR(20) DEFAULT 'info',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 10. Insurance Claims (Risk Management)
CREATE TABLE IF NOT EXISTS insurance_claims (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT,
    customer_id INT,
    claim_type VARCHAR(50),
    description TEXT,
    status VARCHAR(20) DEFAULT 'Pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 11. Emergency Messages (Incident Response)
CREATE TABLE IF NOT EXISTS emergency_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    driver_id INT,
    admin_id INT NULL,
    sender_type VARCHAR(20), -- 'driver' or 'admin'
    message TEXT,
    is_emergency BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'Open',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Default System Seeds
INSERT INTO bookings (pickup_loc, dropoff_loc, weight_kg, fare_pkr, status) VALUES 
('Lahore HQ', 'Faisalabad Industrial', 5000, 25000, 'Pending'),
('Karachi Port', 'Hyderabad Terminal', 8000, 45000, 'Pending'),
('Islamabad Dry Port', 'Peshawar Hub', 3500, 18500, 'Pending');