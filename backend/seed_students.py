# Run once to add initial students: py -3.11 seed_students.py
# Going forward, use Admin panel CSV upload instead.

from app import create_app
from models.models import Student
from extensions import db

STUDENTS = [   
{"email":"kshamitha@gmail.com","roll_no":"23UP1A05Z8"},
{"email":"vrevathi@gmail.com","roll_no":"23UP1A05Z9"},
{"email":"manushaje@gmail.com","roll_no":"23UP1A05Z6"},
{"email":"nallaashrith@gmail.com","roll_no":"23UP1A05Z5"},
{"email":"indlavarshith3@gmail.com","roll_no":"23UP1A05Z3"},
{"email":"abhinayas6@gmail.com","roll_no":"23UP1A05Z0"},
{"email":"bharuri@gmail.com","roll_no":"23UP1A05Z1"},
{"email":"ithasogala@gmail.com","roll_no":"23UP1A05Z2"},
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
