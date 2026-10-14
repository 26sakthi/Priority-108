from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.ambulance import Ambulance

# Ensure tables exist
Base.metadata.create_all(bind=engine)

DEMO_FLEET = [
    {
        "vehicle_code": "AMB-ALS-01",
        "ambulance_type": "ALS",
        "status": "AVAILABLE",
        "latitude": 11.233500,
        "longitude": 78.872100  # Central Perambalur Depot
    },
    {
        "vehicle_code": "AMB-ALS-02",
        "ambulance_type": "ALS",
        "status": "AVAILABLE",
        "latitude": 11.242000,
        "longitude": 78.881000  # Near Medical College
    },
    {
        "vehicle_code": "AMB-BLS-01",
        "ambulance_type": "BLS",
        "status": "AVAILABLE",
        "latitude": 11.231000,
        "longitude": 78.869000  # Old Bus Stand
    },
    {
        "vehicle_code": "AMB-BLS-02",
        "ambulance_type": "BLS",
        "status": "AVAILABLE",
        "latitude": 11.250500,
        "longitude": 78.892000  # North Bypass Junction
    },
    {
        "vehicle_code": "AMB-BLS-03",
        "ambulance_type": "BLS",
        "status": "AVAILABLE",
        "latitude": 11.220100,
        "longitude": 78.861000  # South Sector Depot
    },
    {
        "vehicle_code": "AMB-ALS-03",
        "ambulance_type": "ALS",
        "status": "OFFLINE",   # In maintenance
        "latitude": 11.234000,
        "longitude": 78.874000
    }
]

def seed_ambulances():
    db: Session = SessionLocal()
    try:
        added_count = 0
        for data in DEMO_FLEET:
            existing = db.query(Ambulance).filter(Ambulance.vehicle_code == data["vehicle_code"]).first()
            if not existing:
                amb = Ambulance(**data)
                db.add(amb)
                added_count += 1
            else:
                # Reset status to available for demo repeatability
                existing.status = data["status"]
                existing.latitude = data["latitude"]
                existing.longitude = data["longitude"]
        db.commit()
        print(f"Successfully seeded/refreshed {len(DEMO_FLEET)} ambulances (newly added: {added_count}).")
    finally:
        db.close()

if __name__ == "__main__":
    seed_ambulances()
