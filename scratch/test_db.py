from app import app, db, DriverModel
with app.app_context():
    drivers = DriverModel.query.all()
    print(f"Total drivers: {len(drivers)}")
    for d in drivers:
        print(f"ID: {d.id}, Name: {d.name}, Verified: {d.is_verified}, Available: {d.is_available}, City: {d.lat}, {d.lon}")
