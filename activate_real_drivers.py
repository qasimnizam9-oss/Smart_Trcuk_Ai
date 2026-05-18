#!/usr/bin/env python3
"""
Smart Truck - Admin Driver Activation
VERIFIES and ACTIVATES 5+ drivers for Instant Booking (admin approval simulation)
Only these drivers will appear in /api/drivers/nearby (per user requirement)
"""
from app import app, db, DriverModel

with app.app_context():
    # Get all recently seeded drivers
    all_drivers = DriverModel.query.all()
    
    if not all_drivers:
        print("❌ No drivers found. Run 'python seed_drivers.py' first!")
        exit(1)
    
    # Admin approves FIRST 5 drivers (production simulation)
    approved_count = 0
    for driver in all_drivers[:5]:  # First 5 get verified/activated
        if not driver.is_verified:
            driver.is_verified = True
            driver.is_available = True
            driver.current_status = "Online - Ready for Loads"
            driver.rating = 4.8 + (approved_count * 0.04)  # 4.8 to 5.0
            approved_count += 1
    
    # Update locations to be spread across Pakistan (realistic for testing)
    locations = [
        (31.5204, 74.3587, "Lahore"),    # Ahmed Khan
        (33.6844, 73.0479, "Islamabad"), # Usman Ali
        (24.8607, 67.0011, "Karachi"),   # Bilal Ahmed
        (30.1575, 71.5249, "Multan"),    # Rizwan Butt
        (34.0151, 71.5249, "Peshawar")   # Imran Wazir
    ]
    
    for i, driver in enumerate(all_drivers[:5]):
        driver.lat, driver.lon = locations[i]
        driver.current_status = f"Verified - Available in {locations[i][2]}"
    
    db.session.commit()
    
    # Count verified/available drivers
    verified_online = DriverModel.query.filter_by(is_verified=True, is_available=True).count()
    
    print(f"✅ ADMIN VERIFIED {approved_count} drivers!")
    print(f"📊 {verified_online} drivers now available for Instant Booking")

    print("\n🚀 Instant Booking should now show REAL ADMIN-VERIFIED DRIVERS!")
