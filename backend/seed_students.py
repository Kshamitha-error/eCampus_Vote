# Run once to add initial students: py -3.11 seed_students.py
# Going forward, use Admin panel CSV upload instead.

from app import create_app
from models.models import Student
from extensions import db

STUDENTS = [   
{"email":"kshamitha1612@gmail.com","roll_no":"23UP1A05O1"},
{"email":"vrevathi240@gmail.com","roll_no":"23UP1A05O3"},
{"email":"manushajalike@gmail.com","roll_no":"23UP1A05L2"},
{"email":"nallaashritha96@gmail.com","roll_no":"23UP1A05M8"},
{"email":"indlavarshitha73@gmail.com","roll_no":"23UP1A05L0"},
{"email":"abhinayasangepu6@gmail.com","roll_no":"23UP1A05O0"},
{"email":"bhargaviburi@gmail.com","roll_no":"23UP1A05J0"},
{"email":"kshamithasogala@gmail.com","roll_no":"23UP1A05Z2"},
]
app = create_app()
with app.app_context():
    for s in STUDENTS:
        if not Student.query.filter_by(email=s["email"]).first():
            db.session.add(Student(email=s["email"], roll_no=s["roll_no"]))
            print(f"  Added: {s['email']} / {s['roll_no']}")
        else:
            print(f"  Skipped (exists): {s['email']}")
    db.session.commit()
    print("Done seeding students.")