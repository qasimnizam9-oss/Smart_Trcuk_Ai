-- Smart Truck System - Full MySQL Schema

CREATE DATABASE IF NOT EXISTS smart_truck_db;
USE smart_truck_db;

-- 1. Admins Table
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100),
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- 2. Drivers Table
CREATE TABLE drivers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    password VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT FALSE,
    current_status VARCHAR(50) DEFAULT 'Pending Verification',
    earnings INT DEFAULT 0,
    rating FLOAT DEFAULT 5.0,
    lat FLOAT DEFAULT 31.5204,
    lon FLOAT DEFAULT 74.3587,
    capacity INT DEFAULT 5000,
    year INT DEFAULT 2024,
    trips INT DEFAULT 0
);

-- 3. Users/Shippers Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password VARCHAR(255) NOT NULL,
    company_name VARCHAR(100)
);

-- 4. Bookings/Shipments Table
CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pickup_loc VARCHAR(255),
    dropoff_loc VARCHAR(255),
    weight FLOAT,
    fare FLOAT,
    status VARCHAR(50) DEFAULT 'Pending',
    payment_status VARCHAR(50) DEFAULT 'Pending',
    user_id INT,
    driver_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE SET NULL
);

-- 5. System Logs Table (Audit Trail)
CREATE TABLE logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_name VARCHAR(100),
    action VARCHAR(255),
    module VARCHAR(50),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip VARCHAR(50)
);

-- Insert a Mock Admin for Testing
INSERT INTO admins (full_name, username, password) VALUES ('Qasim Nizam', 'admin', 'password123');
