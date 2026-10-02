"""Flask routes."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from . import ai, db, offline

bp = Blueprint("main", __name__)


def _derive_title(jd):
    first = (jd or "").strip().split("\n")[0].strip()
    return (first[:60] + "…") if len(first) > 60 else (first or "Practice Session")


@bp.route("/", methods=["GET"])
def index():
    sessions = db.list_sessions()
    return render_template("index.html", sessions=sessions, ai_mode=ai.has_api_key())


@bp.route("/sessions", methods=["POST"])
def create_session():
    jd = (request.form.get("job_description") or "").strip()
    if len(jd) < 20:
        flash("Paste a job description (at least a few sentences) to start.")
        return redirect(url_for("main.index"))

    if ai.has_api_key():
        try:
            questions = ai.generate_questions(jd)
            mode = "ai"
        except Exception as e:  # API failure -> graceful offline fallback
            flash(f"AI question generation failed ({e}); using offline question bank instead.")
            questions = offline.pick_offline_questions(jd)
            mode = "offline"
    else:
        questions = offline.pick_offline_questions(jd)
        mode = "offline"

    sid = db.create_session(_derive_title(jd), jd, mode)
    db.add_questions(sid, questions)
    return redirect(url_for("main.session_detail", session_id=sid))


@bp.route("/sessions/<int:session_id>", methods=["GET"])
def session_detail(session_id):
    session = db.get_session(session_id)
    if session is None:
        flash("Session not found.")
        return redirect(url_for("main.index"))
    return render_template("session.html", session=session, ai_mode=ai.has_api_key())


@bp.route("/questions/<int:question_id>/answer", methods=["POST"])
def answer_question(question_id):
    q = db.get_question(question_id)
    if q is None:
        flash("Question not found.")
        return redirect(url_for("main.index"))
    answer = (request.form.get("answer") or "").strip()
    if len(answer) < 5:
        flash("Write a real answer first (at least a sentence).")
        return redirect(url_for("main.session_detail", session_id=q["session_id"]))

    if ai.has_api_key():
        try:
            score, feedback, tip = ai.score_answer(q["text"], q["qtype"], answer)
            mode = "ai"
        except Exception as e:
            flash(f"AI scoring failed ({e}); used offline scoring instead.")
            score, feedback, tip = offline.score_offline(q["text"], q["qtype"], answer)
            mode = "offline"
    else:
        score, feedback, tip = offline.score_offline(q["text"], q["qtype"], answer)
        mode = "offline"

    db.save_answer(question_id, answer, score, feedback, tip, mode)
    return redirect(url_for("main.session_detail", session_id=q["session_id"]))
