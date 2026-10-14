import uuid
from datetime import datetime
from db.database import SessionLocal, Base, engine
from app.models.models import Hospital, Ambulance, Incident, CallReport

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Hospital).count() > 0:
            print("[INFO] Database already seeded.")
            return

        print("[INFO] Seeding Hospitals...")
        hospitals = [
            Hospital(
                hospital_id=str(uuid.uuid4()),
                name="Dhanalakshmi Srinivasan Medical College Hospital",
                latitude=11.244123,
                longitude=78.884123,
                specialties=["TRAUMA_LEVEL_1", "CARDIAC_CATH_LAB", "NEUROLOGY", "GENERAL_EMERGENCY"],
                icu_beds_available=6,
                general_beds_available=40,
                is_accepting_emergencies=True,
                contact_phone="+91-4328-254500"
            ),
            Hospital(
                hospital_id=str(uuid.uuid4()),
                name="Perambalur District Government Hospital",
                latitude=11.231123,
                longitude=78.871123,
                specialties=["GENERAL_EMERGENCY", "PEDIATRIC_ICU"],
                icu_beds_available=1,
                general_beds_available=20,
                is_accepting_emergencies=True,
                contact_phone="+91-4328-222100"
            ),
            Hospital(
                hospital_id=str(uuid.uuid4()),
                name="Trichy Govt Medical College Hospital",
                latitude=10.834123,
                longitude=78.694123,
                specialties=["TRAUMA_LEVEL_1", "CARDIAC_CATH_LAB", "BURN_CARE", "NEUROLOGY", "GENERAL_EMERGENCY"],
                icu_beds_available=8,
                general_beds_available=50,
                is_accepting_emergencies=True,
                contact_phone="+91-431-2410111"
            ),
            Hospital(
                hospital_id=str(uuid.uuid4()),
                name="Samayapuram Emergency Care Clinic",
                latitude=11.214123,
                longitude=78.854123,
                specialties=["GENERAL_EMERGENCY"],
                icu_beds_available=0,
                general_beds_available=8,
                is_accepting_emergencies=True,
                contact_phone="+91-431-2670200"
            )
        ]
        db.add_all(hospitals)
        db.commit()

        print("[INFO] Seeding Ambulances...")
        ambulances = [
            Ambulance(
                ambulance_id=str(uuid.uuid4()),
                vehicle_code="AMB-ALS-01",
                ambulance_type="ALS",
                status="AVAILABLE",
                latitude=11.214123,
                longitude=78.854123,
                base_station_name="Samayapuram Toll Plaza Post",
                staff_qualifications=["PARAMEDIC_ADVANCED", "VENTILATOR_CERTIFIED"],
                onboard_equipment=["DEFIBRILLATOR", "VENTILATOR", "TRAUMA_KIT", "OXYGEN"]
            ),
            Ambulance(
                ambulance_id=str(uuid.uuid4()),
                vehicle_code="AMB-ALS-02",
                ambulance_type="ALS",
                status="AVAILABLE",
                latitude=11.254123,
                longitude=78.894123,
                base_station_name="Perambalur North Depot",
                staff_qualifications=["PARAMEDIC_ADVANCED", "ICU_SPECIALIST"],
                onboard_equipment=["DEFIBRILLATOR", "VENTILATOR", "TRAUMA_KIT", "CARDIAC_MONITOR"]
            ),
            Ambulance(
                ambulance_id=str(uuid.uuid4()),
                vehicle_code="AMB-BLS-01",
                ambulance_type="BLS",
                status="AVAILABLE",
                latitude=11.234123,
                longitude=78.874123,
                base_station_name="Perambalur Town Center Post",
                staff_qualifications=["EMT_BASIC", "FIRST_AID_TRAINER"],
                onboard_equipment=["DEFIBRILLATOR", "OXYGEN", "FIRST_AID", "CERVICAL_COLLAR"]
            ),
            Ambulance(
                ambulance_id=str(uuid.uuid4()),
                vehicle_code="AMB-BLS-02",
                ambulance_type="BLS",
                status="AVAILABLE",
                latitude=11.231123,
                longitude=78.871123,
                base_station_name="GH Perambalur Station",
                staff_qualifications=["EMT_BASIC"],
                onboard_equipment=["OXYGEN", "FIRST_AID", "STRETCHER"]
            ),
            Ambulance(
                ambulance_id=str(uuid.uuid4()),
                vehicle_code="AMB-PTS-01",
                ambulance_type="PTS",
                status="AVAILABLE",
                latitude=11.240000,
                longitude=78.880000,
                base_station_name="Ariyalur Fork Depot",
                staff_qualifications=["FIRST_RESPONDER"],
                onboard_equipment=["WHEELCHAIR", "STRETCHER", "FIRST_AID"]
            )
        ]
        db.add_all(ambulances)
        db.commit()

        print("[INFO] Seeding Initial Incident...")
        initial_incident_id = str(uuid.uuid4())
        initial_incident = Incident(
            incident_id=initial_incident_id,
            incident_number="INC-20261014-0010",
            incident_type="CARDIAC_CHEST_PAIN",
            description="Elderly male with sudden chest pressure and sweating near New Bus Stand.",
            latitude=11.234123,
            longitude=78.874123,
            address_landmark="New Bus Stand, Perambalur",
            status="TRIAGED",
            priority_tier="P2_HIGH_URGENCY",
            urgency_score=75,
            affected_casualty_count=1,
            is_trapped=False,
            scene_hazards=[],
            call_count=1,
            created_at=datetime.utcnow()
        )
        db.add(initial_incident)
        db.commit()

        initial_call = CallReport(
            call_id=str(uuid.uuid4()),
            incident_id=initial_incident_id,
            caller_phone_hash="a1b2c3d4e5f6...",
            caller_name="Ramesh Kumar",
            reported_latitude=11.234123,
            reported_longitude=78.874123,
            reported_landmark="New Bus Stand Shop #4",
            reported_casualties=1,
            caller_statement="Grandfather has severe chest pain, conscious but sweating heavily.",
            call_start_time=datetime.utcnow()
        )
        db.add(initial_call)
        db.commit()

        print("[SUCCESS] PriorityCare demo database successfully seeded!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
