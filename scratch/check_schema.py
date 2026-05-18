from app import app, db, BookingModel
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = inspector.get_columns('bookings')
    print("Columns in 'bookings' table:")
    for col in columns:
        print(f" - {col['name']} ({col['type']})")
