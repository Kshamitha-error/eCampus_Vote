import os
from flask import Flask, send_from_directory, request, Response
from dotenv import load_dotenv
from extensions import db, mail, jwt, cors, limiter

load_dotenv(override=True)


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///voting.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    secret = os.getenv("JWT_SECRET_KEY", "ecampusvote_secret_key_2026_secure_key")
    app.config["JWT_SECRET_KEY"] = secret if len(secret) >= 32 else secret.ljust(32, "0")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False

    app.config["MAIL_SERVER"]   = os.getenv("MAIL_SERVER",   "smtp.gmail.com")
    app.config["MAIL_PORT"]     = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"]  = os.getenv("MAIL_USE_TLS",  "True") == "True"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")

    upload_folder = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["CORS_HEADERS"]  = "Content-Type"

    db.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})
    limiter.init_app(app)

    # FIX: PATCH added to allowed methods in both handlers
    ALLOWED_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    ALLOWED_HEADERS = "Content-Type, Authorization, ngrok-skip-browser-warning"

    @app.before_request
    def handle_before():
        if request.method == "OPTIONS":
            r = Response()
            r.headers["Access-Control-Allow-Origin"]  = "*"
            r.headers["Access-Control-Allow-Headers"] = ALLOWED_HEADERS
            r.headers["Access-Control-Allow-Methods"] = ALLOWED_METHODS
            return r, 200

    @app.after_request
    def add_headers(response):
        response.headers["ngrok-skip-browser-warning"]   = "true"
        response.headers["Access-Control-Allow-Origin"]  = "*"
        response.headers["Access-Control-Allow-Headers"] = ALLOWED_HEADERS
        response.headers["Access-Control-Allow-Methods"] = ALLOWED_METHODS
        return response

    from routes.student_auth  import student_auth_bp
    from routes.admin_auth    import admin_auth_bp
    from routes.elections     import election_bp
    from routes.notifications import notification_bp
    from routes.uploads       import upload_bp

    app.register_blueprint(student_auth_bp)
    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(election_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(upload_bp)

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        response = send_from_directory(app.config["UPLOAD_FOLDER"], filename)
        response.headers["ngrok-skip-browser-warning"] = "true"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"]  = "no-cache"
        response.headers["Expires"] = "0"
        return response

    with app.app_context():
        db.create_all()
        _seed_admin()

    from scheduler import start_scheduler
    start_scheduler(app)

    return app


def _seed_admin():
    from models.models import Admin
    from utils.helpers import hash_password, check_password

    email    = os.getenv("ADMIN_EMAIL",    "admin@college.edu")
    password = os.getenv("ADMIN_PASSWORD", "Admin@123456")

    print(f"[SEED] env  →  ADMIN_EMAIL='{email}'  ADMIN_PASSWORD='{password}'")

    if not email or not password:
        print("[SEED] ✗ ADMIN_EMAIL or ADMIN_PASSWORD missing from .env — skipping seed.")
        return

    existing = Admin.query.filter_by(email=email).first()
    new_hash = hash_password(password)

    if not existing:
        db.session.add(Admin(email=email, password_hash=new_hash))
        print(f"[SEED] Created new admin: {email}")
    else:
        existing.password_hash = new_hash
        print(f"[SEED] Updated existing admin: {email}")

    db.session.commit()

    saved = Admin.query.filter_by(email=email).first()
    ok    = check_password(password, saved.password_hash)
    print(f"[SEED] Hash verification: {'✓ OK — login will work' if ok else '✗ FAIL — check .env quoting'}")


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)