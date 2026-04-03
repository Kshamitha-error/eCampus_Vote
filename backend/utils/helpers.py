# -*- coding: utf-8 -*-
import bcrypt, random, string, re, os, smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

_otp_store = {}

def generate_otp():
    return "".join(random.choices(string.digits, k=6))

def set_otp(student):
    otp = generate_otp()
    _otp_store[student.id] = {"otp": otp, "expires": datetime.now() + timedelta(minutes=2)}
    return otp

store_otp = set_otp

def verify_otp(student, otp):
    record = _otp_store.get(student.id)
    if not record:
        return False, "OTP not found. Please request a new one."
    if datetime.now() > record["expires"]:
        _otp_store.pop(student.id, None)
        return False, "OTP has expired. Please request a new one."
    if record["otp"] != otp:
        return False, "Invalid OTP."
    _otp_store.pop(student.id, None)
    return True, "OTP verified."

def validate_password_strength(password):
    if len(password) < 8 or len(password) > 12: return False, "Password must be 8-12 characters."
    if not re.search(r"[A-Z]", password):        return False, "Must contain uppercase letter."
    if not re.search(r"[a-z]", password):        return False, "Must contain lowercase letter."
    if not re.search(r"\d",    password):        return False, "Must contain a number."
    if not re.search(r"[@$!%*?&_#]", password):  return False, "Must contain special character (@$!%*?&_#)."
    return True, "Strong."

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(plain, hashed):
    try:    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except: return False


# ── Gmail SMTP ────────────────────────────────────────────────────────────────

def _send_email(to_email, to_name, subject, body_text):
    mail_username = os.environ.get("MAIL_USERNAME", "")
    mail_password = os.environ.get("MAIL_PASSWORD", "")
    if not mail_username or not mail_password:
        print("[EMAIL ERROR] MAIL_USERNAME or MAIL_PASSWORD not set in .env")
        return
    try:
        msg = MIMEMultipart()
        msg["From"]    = f"eCampus Vote <{mail_username}>"
        msg["To"]      = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_username, to_email, msg.as_string())
        print(f"[EMAIL SUCCESS] Sent to {to_email}")
    except Exception as e:
        print(f"[EMAIL ERROR] {str(e)}")


# ── Public functions (no 'app' param) ─────────────────────────────────────────

def send_otp_email(to_email, name, otp):
    subject = "eCampus Vote - Your OTP"
    body = f"""Hello {name or 'Student'},

Your One-Time Password for eCampus Vote is:

  {otp}

Valid for 2 minutes. Do not share this with anyone.

- eCampus Vote Team"""
    _send_email(to_email, name, subject, body)


def send_result_email(to_email, student_name, election_title, winner_name, branch, year):
    subject = f"Results: {election_title}"
    body = f"""Hello {student_name},

Results for '{election_title}' are out!

Winner: {winner_name}
Branch: {branch}  |  Year: {year}

Thank you for participating.
- eCampus Vote Team"""
    _send_email(to_email, student_name, subject, body)


def send_election_notification_email(to_email, student_name, title, message):
    subject = f"eCampus Vote - {title}"
    body = f"""Hello {student_name},

{message}

- eCampus Vote Team"""
    _send_email(to_email, student_name, subject, body)