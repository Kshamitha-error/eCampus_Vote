from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: _check(app),
        "interval",
        minutes=1,
        id="election_checker",
        replace_existing=True
    )
    scheduler.start()
    return scheduler


def _check(app):
    with app.app_context():
        from models.models import Election, Student, Notification
        from extensions import db
        from utils.helpers import send_election_notification_email, send_result_email
        now = datetime.now()

        # Auto-start
        for e in Election.query.filter(Election.status=="upcoming", Election.start_time<=now).all():
            e.status = "ongoing"
            db.session.commit()
            _broadcast(app, f"Election Live: {e.title}",
                f"'{e.title}' is now LIVE! Vote before {e.end_time.strftime('%d %b %Y %H:%M')}.")

        # Auto-end
        for e in Election.query.filter(Election.status=="ongoing", Election.end_time<=now).all():
            e.status = "ended"
            db.session.commit()
            results = sorted(
                [{"name":c.name,"votes":len(c.votes),"branch":c.branch or "","year":str(c.year or "")}
                 for c in e.candidates],
                key=lambda x: x["votes"], reverse=True
            )
            winner = results[0] if results else None
            for s in Student.query.filter_by(is_registered=True).all():
                msg = (f"Winner of '{e.title}': {winner['name']} with {winner['votes']} votes."
                       if winner else f"'{e.title}' ended with no votes.")
                db.session.add(Notification(student_id=s.id, title=f"Results: {e.title}", message=msg))
                if winner:
                    send_result_email(app, s.email, s.name or "", e.title,
                                      winner["name"], winner["branch"], winner["year"])
            db.session.commit()

        # 1-hour reminder
        soon = now + timedelta(hours=1)
        for e in Election.query.filter(
            Election.status=="upcoming",
            Election.start_time>=now,
            Election.start_time<=soon
        ).all():
            _broadcast(app, f"Reminder: '{e.title}' starts soon!",
                f"The election '{e.title}' starts at {e.start_time.strftime('%d %b %Y %H:%M')}.")


def _broadcast(app, title, message):
    with app.app_context():
        from models.models import Student, Notification
        from extensions import db
        from utils.helpers import send_election_notification_email
        for s in Student.query.filter_by(is_registered=True).all():
            if not Notification.query.filter_by(student_id=s.id, title=title).first():
                db.session.add(Notification(student_id=s.id, title=title, message=message))
                try:
                    send_election_notification_email(app, s.email, s.name or "", title, message)
                except Exception as ex:
                    print(f"[NOTIFY ERROR] {ex}")
        db.session.commit()