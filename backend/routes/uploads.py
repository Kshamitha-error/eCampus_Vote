import os, uuid, csv, io
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Student, Vote, Notification
from extensions import db

upload_bp = Blueprint("uploads", __name__, url_prefix="/api/uploads")

ALLOWED = {"png", "jpg", "jpeg", "gif", "webp"}

def is_admin():
    return str(get_jwt_identity()).startswith("admin:")

def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED


# ─── Image Upload ────────────────────────────────────────────────────────────

@upload_bp.route("/image", methods=["POST"])
@jwt_required()
def upload_image():
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400
    f = request.files["file"]
    if not f.filename or not allowed(f.filename):
        return jsonify({"error": "Only image files allowed (jpg, png, gif, webp)."}), 400

    ext = f.filename.rsplit(".", 1)[1].lower()
    if ext == "jpeg":
        ext = "jpg"
    filename  = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    try:
        from PIL import Image
        import io as _io
        img = Image.open(f)
        if img.mode in ("RGBA", "P"):
            img  = img.convert("RGB")
            ext  = "jpg"
            filename  = f"{uuid.uuid4().hex}.jpg"
            save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        img.thumbnail((800, 800), Image.LANCZOS)
        img.save(save_path, quality=85, optimize=True)
    except ImportError:
        f.seek(0); f.save(save_path)
    except Exception:
        f.seek(0); f.save(save_path)

    host = request.host_url.rstrip("/")
    return jsonify({"url": f"{host}/uploads/{filename}"}), 201


# ─── CSV Upload (merge) ───────────────────────────────────────────────────────

@upload_bp.route("/students-csv", methods=["POST"])
@jwt_required()
def upload_students_csv():
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400
    f = request.files["file"]
    if not f.filename.endswith(".csv"):
        return jsonify({"error": "Only CSV files allowed."}), 400

    stream = io.StringIO(f.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    added, skipped, errors = [], [], []
    for i, row in enumerate(reader, start=2):
        email   = (row.get("email")   or row.get("Email")   or "").strip().lower()
        roll_no = (row.get("roll_no") or row.get("Roll No") or row.get("rollno") or "").strip()
        branch  = (row.get("branch")  or row.get("Branch")  or "").strip()
        year_raw= (row.get("year")    or row.get("Year")    or "").strip()

        if not email or not roll_no:
            errors.append(f"Row {i}: missing email or roll_no")
            continue

        # parse year safely
        year = None
        if year_raw:
            try:
                year = int(year_raw)
                if year not in (1, 2, 3, 4):
                    errors.append(f"Row {i}: year must be 1–4, got {year_raw}")
                    continue
            except ValueError:
                errors.append(f"Row {i}: invalid year value '{year_raw}'")
                continue

        existing = Student.query.filter_by(email=email).first()
        if existing:
            skipped.append(email)
            continue

        db.session.add(Student(email=email, roll_no=roll_no, branch=branch or None, year=year))
        added.append(email)

    db.session.commit()
    return jsonify({
        "message": f"{len(added)} added, {len(skipped)} already existed, {len(errors)} errors.",
        "added":   added,
        "skipped": skipped,
        "errors":  errors,
    }), 200


# ─── Student Stats ────────────────────────────────────────────────────────────

@upload_bp.route("/students/stats", methods=["GET"])
@jwt_required()
def student_stats():
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    total      = Student.query.count()
    registered = Student.query.filter_by(is_registered=True).count()
    return jsonify({
        "total":          total,
        "registered":     registered,
        "not_registered": total - registered,
    }), 200


# ─── List Students (paginated + search) ──────────────────────────────────────

@upload_bp.route("/students", methods=["GET"])
@jwt_required()
def list_students():
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403

    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    search   = request.args.get("search", "").strip()

    query = Student.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Student.name.ilike(like),
                Student.roll_no.ilike(like),
                Student.email.ilike(like),
            )
        )

    pagination = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "students":    [s.to_dict() for s in pagination.items],
        "total":       pagination.total,
        "page":        page,
        "pages":       pagination.pages,
        "per_page":    per_page,
    }), 200


# ─── Delete Single Student ────────────────────────────────────────────────────

@upload_bp.route("/students/<int:student_id>", methods=["DELETE"])
@jwt_required()
def delete_student(student_id):
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found."}), 404
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": f"Student {student.email} deleted."}), 200


# ─── Delete Multiple Students ─────────────────────────────────────────────────

@upload_bp.route("/students/bulk-delete", methods=["POST"])
@jwt_required()
def bulk_delete_students():
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    data = request.get_json()
    ids  = data.get("ids", [])
    if not ids:
        return jsonify({"error": "No student IDs provided."}), 400

    deleted = Student.query.filter(Student.id.in_(ids)).all()
    count   = len(deleted)
    for s in deleted:
        db.session.delete(s)
    db.session.commit()
    return jsonify({"message": f"{count} student(s) deleted."}), 200


# ─── Year Rollover ────────────────────────────────────────────────────────────

@upload_bp.route("/students/rollover/preview", methods=["GET"])
@jwt_required()
def rollover_preview():
    """Returns counts per year so admin can preview before confirming."""
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    result = {}
    for y in (1, 2, 3, 4):
        result[str(y)] = Student.query.filter_by(year=y).count()
    return jsonify(result), 200


@upload_bp.route("/students/rollover/remove-passouts", methods=["POST"])
@jwt_required()
def remove_passouts():
    """Step 1: Delete all 4th year students."""
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    passouts = Student.query.filter_by(year=4).all()
    count    = len(passouts)
    for s in passouts:
        db.session.delete(s)
    db.session.commit()
    return jsonify({"message": f"{count} 4th year students removed."}), 200


@upload_bp.route("/students/rollover/upgrade-years", methods=["POST"])
@jwt_required()
def upgrade_years():
    """Step 2: Upgrade 1→2, 2→3, 3→4."""
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403

    upgraded = 0
    # Must go highest first to avoid double-upgrading
    for current_year in (3, 2, 1):
        students = Student.query.filter_by(year=current_year).all()
        for s in students:
            s.year = current_year + 1
            upgraded += 1

    db.session.commit()
    return jsonify({"message": f"{upgraded} students upgraded.", "upgraded": upgraded}), 200


# ─── Hard Reset (danger zone) ─────────────────────────────────────────────────

@upload_bp.route("/students/reset-all", methods=["DELETE"])
@jwt_required()
def reset_all_students():
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    data    = request.get_json()
    confirm = data.get("confirm", "")
    if confirm != "DELETE":
        return jsonify({"error": "Send confirm: 'DELETE' to proceed."}), 400

    count = Student.query.count()
    # Delete votes and notifications first (FK constraints)
    Notification.query.delete()
    Vote.query.delete()
    Student.query.delete()
    db.session.commit()
    return jsonify({"message": f"All {count} students deleted."}), 200