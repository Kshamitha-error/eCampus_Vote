import bcrypt, random, string, re, threading
from datetime import datetime, timedelta

_otp_store = {}

def generate_otp():
    return "".join(random.choices(string.digits, k=6))

def set_otp(student):
    otp = generate_otp()
    _otp_store[student.id] = {"otp":otp, "expires":datetime.now()+timedelta(minutes=2)}
    return otp

store_otp = set_otp

def verify_otp(student, otp):
    record = _otp_store.get(student.id)
    if not record:             return False, "OTP not found. Please request a new one."
    if datetime.now() > record["expires"]:
        _otp_store.pop(student.id, None)
        return False, "OTP has expired. Please request a new one."
    if record["otp"] != otp:  return False, "Invalid OTP."
    _otp_store.pop(student.id, None)
    return True, "OTP verified."

def validate_password_strength(password):
    if len(password)<8 or len(password)>12: return False, "Password must be 8-12 characters."
    if not re.search(r"[A-Z]", password):   return False, "Must contain uppercase letter."
    if not re.search(r"[a-z]", password):   return False, "Must contain lowercase letter."
    if not re.search(r"\d",    password):   return False, "Must contain a number."
    if not re.search(r"[@$!%*?&_#]", password): return False, "Must contain special character (@$!%*?&_#)."
    return True, "Strong."

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(plain, hashed):
    try:    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except: return False

def _send_async(app, msg):
    with app.app_context():
        try:
            from extensions import mail
            mail.send(msg)
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")

def send_otp_email(to_email, name, otp):
    from flask import current_app
    from flask_mail import Message
    app = current_app._get_current_object()
    msg = Message(
        subject="eCampus Vote — Your OTP",
        sender=app.config["MAIL_USERNAME"],
        recipients=[to_email]
    )
    msg.body = f"""Hello {name or 'Student'},

Your One-Time Password for eCampus Vote is:

  {otp}

Valid for 2 minutes. Do not share this with anyone.

— eCampus Vote Team"""
    threading.Thread(target=_send_async, args=(app,msg), daemon=True).start()

def send_result_email(app, to_email, student_name, election_title, winner_name, branch, year):
    from flask_mail import Message
    msg = Message(
        subject=f"Results: {election_title}",
        sender=app.config["MAIL_USERNAME"],
        recipients=[to_email]
    )
    msg.body = f"""Hello {student_name},

Results for '{election_title}' are out!

Winner: {winner_name}
Branch: {branch}  |  Year: {year}

Thank you for participating.
— eCampus Vote Team"""
    threading.Thread(target=_send_async, args=(app,msg), daemon=True).start()

def send_election_notification_email(app, to_email, student_name, title, message):
    from flask_mail import Message
    msg = Message(
        subject=f"eCampus Vote — {title}",
        sender=app.config["MAIL_USERNAME"],
        recipients=[to_email]
    )
    msg.body = f"""Hello {student_name},

{message}

— eCampus Vote Team"""
    threading.Thread(target=_send_async, args=(app,msg), daemon=True).start()