#!/usr/bin/env python3
"""
Smart Truck - Create REAL Demo Data for User Dashboard
Creates customer user=1 + 8 realistic bookings + chats + transactions
Runs activate_real_drivers.py automatically
Dashboard loader will be replaced with REAL data after this runs!
"""
import sys
sys.path.append('.')

from app import app, db, DriverModel, CustomerModel, BookingModel, TransactionModel, ChatModel
from activate_real_drivers import *  # Auto-run driver activation

with app.app_context():
    print("🔄 Creating dashboard demo data for user=1...")
    
    # Step 1: Create Demo Customer (userId=1) if missing
    customer = CustomerModel.query.get(1)
    if not customer:
        customer = CustomerModel(
            id=1,
            name="Qasim Nizam",
            email="qasim@smarttruck.pk",
            phone="+923001234567",
            password="user123"
        )
        db.session.add(customer)
        print("✅ Created demo user: Qasim Nizam (ID=1)")
    
    # Step 2: Ensure 5+ verified drivers exist (via activate_real_drivers)
    activate_real_drivers()  # Auto-verifies first 5 drivers
    
    # Step 3: Get 5 verified drivers for bookings
    verified_drivers = DriverModel.query.filter_by(is_verified=True, is_available=True).limit(5).all()
    if not verified_drivers:
        print("❌ No verified drivers! Run 'python activate_real_drivers.py' first.")
        sys.exit(1)
    
    # Step 4: Create 8 REALISTIC bookings for user=1 (various statuses)
    booking_data = [
        {"pickup": "Lahore Cantt", "dropoff": "Faisalabad", "weight": 4500, "fare": 28500, "status": "Completed", "driver_id": verified_drivers[0].id},
        {"pickup": "Karachi Port", "dropoff": "Hyderabad", "weight": 7200, "fare": 42500, "status": "In Transit", "driver_id": verified_drivers[1].id},
        {"pickup": "Islamabad", "dropoff": "Rawalpindi", "weight": 3200, "fare": 15200, "status": "Pending", "driver_id": None},
        {"pickup": "Multan", "dropoff": "Bahawalpur", "weight": 5800, "fare": 34200, "status": "Assigned", "driver_id": verified_drivers[2].id},
        {"pickup": "Peshawar", "dropoff": "Nowshera", "weight": 2800, "fare": 16800, "status": "Confirmed", "driver_id": verified_drivers[3].id},
        {"pickup": "Quetta", "dropoff": "Sibi", "weight": 6500, "fare": 39200, "status": "Completed", "driver_id": verified_drivers[4].id},
        {"pickup": "Gujranwala", "dropoff": "Sialkot", "weight": 4100, "fare": 24600, "status": "In Transit", "driver_id": verified_drivers[0].id},
        {"pickup": "Sargodha", "dropoff": "Faisalabad", "weight": 3700, "fare": 22200, "status": "Pending", "driver_id": None},
    ]
    
    existing_count = BookingModel.query.filter_by(customer_id=1).count()
    if existing_count == 0:
        for data in booking_data:
            booking = BookingModel(
                customer_id=1,
                pickup_loc=data["pickup"],
                dropoff_loc=data["dropoff"],
                weight_kg=data["weight"],
                fare_pkr=data["fare"],
                status=data["status"],
                driver_id=data["driver_id"]
            )
            db.session.add(booking)
        db.session.commit()
        print(f"✅ Created {len(booking_data)} bookings for user=1")
    else:
        print(f"ℹ️  {existing_count} bookings already exist for user=1 (skipped)")
    
    # Step 5: Create sample chats for first 3 bookings
    chat_data = [
        (1, "user", "When will the shipment arrive in Faisalabad?", "14:22"),
        (1, "driver", "ETA 18:30. Currently on M-4 Motorway.", "14:25"),
        (2, "user", "Please confirm pickup from Karachi Port tomorrow.", "09:15"),
        (2, "driver", "Confirmed for 10 AM. Vehicle ready.", "09:18"),
        (3, "user", "Can you handle 3200kg load?", "11:45"),
        (3, "driver", "Yes, my capacity is 8000kg.", "11:47"),
    ]
    
    for booking_id, sender, message, time_str in chat_data:
        chat = ChatModel(
            booking_id=booking_id,
            sender=sender,
            message=message
        )
        db.session.add(chat)
    db.session.commit()
    print("✅ Created sample chat messages")
    
    # Step 6: Create transactions for completed bookings
    completed_bookings = BookingModel.query.filter_by(customer_id=1, status="Completed").all()
    for booking in completed_bookings[:3]:  # First 3 completed
        txn = TransactionModel(
            booking_id=booking.id,
            amount=booking.fare_pkr,
            payment_method="Online Card",
            admin_commission=round(booking.fare_pkr * 0.10, 2),
            driver_payout=round(booking.fare_pkr * 0.85, 2),
            payment_status="Paid"
        )
        db.session.add(txn)
    db.session.commit()
    print("✅ Created transactions for completed bookings")
    
    # Final verification
    bookings_count = BookingModel.query.filter_by(customer_id=1).count()
    verified_drivers_count = DriverModel.query.filter_by(is_verified=True, is_available=True).count()
    
    print("\n🎉 DASHBOARD READY!")
    print(f"📊 User=1 has {bookings_count} bookings")
    print(f"🚚 {verified_drivers_count} verified drivers available")
    print("\n🚀 Run server: python app.py")
    print("🌐 Visit: http://localhost:5000/user/dashboard")
    print("✅ Loader gone → REAL bookings/chats/drivers will load!")

