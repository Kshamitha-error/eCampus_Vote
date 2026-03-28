from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.models import Election, Candidate, Student, Notification, Vote
from extensions import db

election_bp = Blueprint("elections", __name__, url_prefix="/api/elections")


def is_admin():
    return str(get_jwt_identity()).startswith("admin:")


def broadcast(title, message):
    try:
        from utils.helpers import send_election_notification_email
        students = Student.query.filter_by(is_registered=True).all()
        for s in students:
            if not Notification.query.filter_by(student_id=s.id, title=title).first():
                db.session.add(Notification(student_id=s.id, title=title, message=message))
                try:
                    send_election_notification_email(s.email, s.name or "", title, message)
                except Exception as e:
                    print(f"[NOTIFY ERROR] {e}")
        db.session.commit()
    except Exception as e:
        print(f"[BROADCAST ERROR] {e}")


def tally(election):
    return sorted(
        [{"candidate_id": c.id, "name": c.name, "branch": c.branch, "year": c.year,
          "photo_url": c.photo_url, "votes": len(c.votes)}
         for c in election.candidates],
        key=lambda x: x["votes"], reverse=True,
    )


def sync_all_statuses():
    now = datetime.now()
    changed = False
    for e in Election.query.filter(Election.status == "upcoming", Election.start_time <= now).all():
        e.status = "ongoing"
        changed = True
    for e in Election.query.filter(Election.status == "ongoing", Election.end_time <= now).all():
        e.status = "ended"
        changed = True
    if changed:
        db.session.commit()


# ─── Create Election ──────────────────────────────────────────────────────────

@election_bp.route("/", methods=["POST"])
@jwt_required()
def create_election():
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    data = request.get_json()
    title = data.get("title", "").strip()
    if not title or not data.get("start_time") or not data.get("end_time"):
        return jsonify({"error": "Title, start_time, and end_time are required."}), 400
    try:
        start_str = data["start_time"].replace("T", " ").split(".")[0][:16]
        end_str   = data["end_time"].replace("T", " ").split(".")[0][:16]
        start_dt  = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        end_dt    = datetime.strptime(end_str,   "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Invalid date format."}), 400
    if end_dt <= start_dt:
        return jsonify({"error": "end_time must be after start_time."}), 400
    e = Election(
        title=title,
        description=data.get("description", ""),
        start_time=start_dt,
        end_time=end_dt
    )
    db.session.add(e)
    db.session.commit()
    try:
        broadcast(
            f"New Election: {title}",
            f"A new election '{title}' is scheduled from "
            f"{start_dt.strftime('%d %b %Y %H:%M')} to {end_dt.strftime('%d %b %Y %H:%M')}."
        )
    except Exception as ex:
        print(f"[BROADCAST ERROR] {ex}")
    return jsonify({"message": "Election created.", "election_id": e.id, "election": e.to_dict()}), 201


# ─── Get / Edit / Delete Election ────────────────────────────────────────────

@election_bp.route("/", methods=["GET"])
@jwt_required()
def list_elections():
    sync_all_statuses()
    status = request.args.get("status")
    q = Election.query
    if status:
        q = q.filter_by(status=status)
    elections = q.order_by(Election.start_time.desc()).all()
    return jsonify([e.to_dict() for e in elections]), 200


@election_bp.route("/<int:eid>", methods=["GET"])
@jwt_required()
def get_election(eid):
    sync_all_statuses()
    e = Election.query.get_or_404(eid)
    d = e.to_dict()
    d["candidates"] = [c.to_dict() for c in e.candidates]
    return jsonify(d), 200


@election_bp.route("/<int:eid>", methods=["PUT"])
@jwt_required()
def edit_election(eid):
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    e = Election.query.get_or_404(eid)
    if e.status == "ended":
        return jsonify({"error": "Ended elections cannot be edited."}), 400
    data = request.get_json()
    e.title       = data.get("title",       e.title).strip()
    e.description = data.get("description", e.description)
    if e.status == "upcoming":
        try:
            if data.get("start_time"):
                start_str = data["start_time"].replace("T"," ").split(".")[0][:16]
                e.start_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
            if data.get("end_time"):
                end_str = data["end_time"].replace("T"," ").split(".")[0][:16]
                e.end_time = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
            if e.end_time <= e.start_time:
                return jsonify({"error": "End time must be after start time."}), 400
        except ValueError:
            return jsonify({"error": "Invalid date format."}), 400
    db.session.commit()
    return jsonify({"message": "Election updated.", "election": e.to_dict()}), 200


@election_bp.route("/<int:eid>/delete", methods=["DELETE"])
@jwt_required()
def delete_election(eid):
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    e = Election.query.get_or_404(eid)
    db.session.delete(e)
    db.session.commit()
    return jsonify({"message": "Election deleted."}), 200


# ─── Candidates — BY ELECTION ID (new routes frontend needs) ─────────────────

@election_bp.route("/<int:eid>/candidates", methods=["GET"])
@jwt_required()
def get_candidates_by_election(eid):
    """GET /api/elections/<eid>/candidates — list all candidates for an election."""
    e = Election.query.get_or_404(eid)
    return jsonify({"candidates": [c.to_dict() for c in e.candidates]}), 200


@election_bp.route("/<int:eid>/candidates", methods=["POST"])
@jwt_required()
def add_candidate_by_election(eid):
    """POST /api/elections/<eid>/candidates — add candidate to an election."""
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    Election.query.get_or_404(eid)
    data = request.get_json()
    if not data.get("name", "").strip():
        return jsonify({"error": "Candidate name is required."}), 400
    if not data.get("photo_url", ""):
        return jsonify({"error": "Candidate photo is required."}), 400
    if not data.get("symbol_url", "") and not data.get("logo_url", ""):
        return jsonify({"error": "Candidate symbol/logo is required."}), 400
    c = Candidate(
        election_id=eid,
        name=data["name"].strip(),
        branch=data.get("branch", ""),
        year=data.get("year", ""),
        photo_url=data.get("photo_url", ""),
        symbol_url=data.get("symbol_url", data.get("logo_url", "")),
        manifesto=data.get("manifesto", ""),
        achievements=data.get("achievements", ""),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"message": "Candidate added.", "candidate": c.to_dict()}), 201


@election_bp.route("/<int:eid>/candidates/<int:cid>", methods=["PUT"])
@jwt_required()
def edit_candidate_by_election(eid, cid):
    """PUT /api/elections/<eid>/candidates/<cid> — edit a candidate."""
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    c = Candidate.query.filter_by(id=cid, election_id=eid).first_or_404()
    data = request.get_json()
    c.name         = data.get("name",         c.name)
    c.branch       = data.get("branch",       c.branch)
    c.year         = data.get("year",         c.year)
    c.photo_url    = data.get("photo_url",    c.photo_url)
    c.symbol_url   = data.get("symbol_url",   data.get("logo_url", c.symbol_url))
    c.manifesto    = data.get("manifesto",    c.manifesto)
    c.achievements = data.get("achievements", c.achievements)
    db.session.commit()
    return jsonify({"message": "Candidate updated.", "candidate": c.to_dict()}), 200


@election_bp.route("/<int:eid>/candidates/<int:cid>", methods=["DELETE"])
@jwt_required()
def delete_candidate_by_election(eid, cid):
    """DELETE /api/elections/<eid>/candidates/<cid> — remove a candidate."""
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    c = Candidate.query.filter_by(id=cid, election_id=eid).first_or_404()
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Candidate deleted."}), 200


# ─── Old flat candidate routes (kept for backward compatibility) ──────────────

@election_bp.route("/candidates", methods=["POST"])
@jwt_required()
def add_candidate():
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    data = request.get_json()
    eid = data.get("election_id")
    if not eid:
        return jsonify({"error": "election_id required."}), 400
    Election.query.get_or_404(eid)
    if not data.get("name", "").strip():
        return jsonify({"error": "Candidate name is required."}), 400
    if not data.get("photo_url", ""):
        return jsonify({"error": "Candidate photo is required."}), 400
    if not data.get("logo_url", "") and not data.get("symbol_url", ""):
        return jsonify({"error": "Candidate symbol/logo is required."}), 400
    c = Candidate(
        election_id=eid,
        name=data["name"].strip(),
        branch=data.get("branch", ""),
        year=data.get("year"),
        photo_url=data.get("photo_url", ""),
        symbol_url=data.get("logo_url", data.get("symbol_url", "")),
        manifesto=data.get("manifesto", ""),
        achievements=data.get("achievements", ""),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"message": "Candidate added.", "candidate": c.to_dict()}), 201


@election_bp.route("/candidates/<int:cid>", methods=["GET"])
@jwt_required()
def get_candidate(cid):
    c = Candidate.query.get_or_404(cid)
    return jsonify(c.to_dict()), 200


@election_bp.route("/candidates/<int:cid>", methods=["PUT"])
@jwt_required()
def edit_candidate(cid):
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    c = Candidate.query.get_or_404(cid)
    data = request.get_json()
    c.name         = data.get("name",         c.name)
    c.branch       = data.get("branch",       c.branch)
    c.year         = data.get("year",         c.year)
    c.photo_url    = data.get("photo_url",    c.photo_url)
    c.symbol_url   = data.get("logo_url",     data.get("symbol_url", c.symbol_url))
    c.manifesto    = data.get("manifesto",    c.manifesto)
    c.achievements = data.get("achievements", c.achievements)
    db.session.commit()
    return jsonify({"message": "Candidate updated.", "candidate": c.to_dict()}), 200


@election_bp.route("/candidates/<int:cid>", methods=["DELETE"])
@jwt_required()
def delete_candidate(cid):
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    c = Candidate.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Candidate deleted."}), 200


# ─── Election Actions ─────────────────────────────────────────────────────────

@election_bp.route("/<int:eid>/start", methods=["POST", "PATCH"])
@jwt_required()
def start_election(eid):
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    e = Election.query.get_or_404(eid)
    if e.status != "upcoming":
        return jsonify({"error": f"Election is '{e.status}', not upcoming."}), 400
    e.status = "ongoing"
    db.session.commit()
    broadcast(f"Election Started: {e.title}",
              f"'{e.title}' is now LIVE! Vote before {e.end_time.strftime('%d %b %Y %H:%M')}.")
    return jsonify({"message": "Election started.", "election": e.to_dict()}), 200


@election_bp.route("/<int:eid>/end", methods=["POST", "PATCH"])
@jwt_required()
def end_election(eid):
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    e = Election.query.get_or_404(eid)
    if e.status != "ongoing":
        return jsonify({"error": "Only ongoing elections can be ended."}), 400
    e.status = "ended"
    db.session.commit()
    results = tally(e)
    winner  = results[0] if results else None
    for s in Student.query.filter_by(is_registered=True).all():
        msg = (f"Winner of '{e.title}': {winner['name']} with {winner['votes']} votes."
               if winner else f"'{e.title}' ended with no votes.")
        db.session.add(Notification(student_id=s.id, title=f"Results: {e.title}", message=msg))
    db.session.commit()
    return jsonify({"message": "Election ended.", "election": e.to_dict(), "results": results}), 200


@election_bp.route("/<int:eid>/cancel", methods=["POST", "PATCH"])
@jwt_required()
def cancel_election(eid):
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    e = Election.query.get_or_404(eid)
    if e.status == "ended":
        return jsonify({"error": "Cannot cancel an ended election."}), 400
    e.status = "cancelled"
    db.session.commit()
    broadcast(f"Election Cancelled: {e.title}", f"The election '{e.title}' has been cancelled.")
    return jsonify({"message": "Election cancelled.", "election": e.to_dict()}), 200


# ─── Voting ───────────────────────────────────────────────────────────────────

@election_bp.route("/<int:eid>/check-voted", methods=["GET"])
@jwt_required()
def check_voted(eid):
    identity = get_jwt_identity()
    if str(identity).startswith("admin:"):
        return jsonify({"voted": False}), 200
    vote = Vote.query.filter_by(student_id=int(identity), election_id=eid).first()
    if vote:
        candidate = Candidate.query.get(vote.candidate_id)
        return jsonify({"voted": True, "candidate_name": candidate.name if candidate else "Unknown"}), 200
    return jsonify({"voted": False}), 200


@election_bp.route("/<int:eid>/vote", methods=["POST"])
@jwt_required()
def cast_vote(eid):
    identity = get_jwt_identity()
    if str(identity).startswith("admin:"):
        return jsonify({"error": "Admins cannot vote."}), 403
    student_id = int(identity)
    e = Election.query.get_or_404(eid)
    if e.status != "ongoing":
        return jsonify({"error": "Voting is not open for this election."}), 400
    if Vote.query.filter_by(student_id=student_id, election_id=eid).first():
        return jsonify({"error": "You have already voted in this election."}), 409
    cid = request.get_json().get("candidate_id")
    c = Candidate.query.filter_by(id=cid, election_id=eid).first()
    if not c:
        return jsonify({"error": "Invalid candidate."}), 400
    db.session.add(Vote(student_id=student_id, election_id=eid, candidate_id=cid))
    db.session.commit()
    return jsonify({"message": f"Vote cast for {c.name}."}), 201


@election_bp.route("/<int:eid>/results", methods=["GET"])
@jwt_required()
def get_results(eid):
    e = Election.query.get_or_404(eid)
    if e.status != "ended":
        return jsonify({"error": "Results available only after election ends."}), 400
    return jsonify({"election": e.title, "results": tally(e)}), 200


# ─── Turnout ──────────────────────────────────────────────────────────────────

@election_bp.route("/<int:eid>/turnout", methods=["GET"])
@jwt_required()
def voter_turnout(eid):
    if not is_admin():
        return jsonify({"error": "Admin access required."}), 403
    e = Election.query.get_or_404(eid)
    total = Student.query.filter_by(is_registered=True).count()
    cast  = len(e.votes)
    return jsonify({
        "election":                  e.title,
        "total_registered_students": total,
        "votes_cast":                cast,
        "turnout_percentage":        round(cast / total * 100, 2) if total else 0,
        "results":                   tally(e),
    }), 200