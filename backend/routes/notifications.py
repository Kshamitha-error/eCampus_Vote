from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Notification
from extensions import db

notification_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

@notification_bp.route("", methods=["GET"])
@jwt_required()
def get_notifications():
    identity = get_jwt_identity()
    if str(identity).startswith("admin:"):
        return jsonify({"notifications": [], "unread_count": 0}), 200
    student_id = int(identity)
    notifs = Notification.query.filter_by(student_id=student_id).order_by(Notification.created_at.desc()).all()
    unread = sum(1 for n in notifs if not n.is_read)
    return jsonify({"notifications": [n.to_dict() for n in notifs], "unread_count": unread}), 200

@notification_bp.route("/<int:nid>/read", methods=["PATCH"])
@jwt_required()
def mark_read(nid):
    n = Notification.query.get_or_404(nid)
    n.is_read = True
    db.session.commit()
    return jsonify({"message": "Marked as read."}), 200

@notification_bp.route("/read-all", methods=["PATCH"])
@jwt_required()
def mark_all_read():
    identity = get_jwt_identity()
    if str(identity).startswith("admin:"):
        return jsonify({"message": "Done."}), 200
    student_id = int(identity)
    Notification.query.filter_by(student_id=student_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "All marked as read."}), 200