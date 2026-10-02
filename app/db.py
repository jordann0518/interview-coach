"""SQLite persistence layer (stdlib sqlite3 only)."""
import os
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    job_description TEXT NOT NULL,
    mode TEXT NOT NULL,            -- 'ai' or 'offline'
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    qtype TEXT NOT NULL,           -- 'behavioral' or 'technical'
    text TEXT NOT NULL,
    position INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    score INTEGER NOT NULL,        -- 1..10
    feedback TEXT NOT NULL,
    tip TEXT NOT NULL,
    mode TEXT NOT NULL,            -- 'ai' or 'offline'
    created_at TEXT NOT NULL
);
"""


def db_path():
    return os.environ.get(
        "INTERVIEW_COACH_DB",
        os.path.join(os.path.expanduser("~"), ".interview_coach.db"),
    )


def _connect():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db():
    conn = _connect()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def create_session(title, job_description, mode):
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO sessions (title, job_description, mode, created_at)"
        " VALUES (?, ?, ?, ?)",
        (title, job_description, mode, _now()),
    )
    sid = cur.lastrowid
    conn.commit()
    conn.close()
    return sid


def add_questions(session_id, questions):
    """questions: list of (qtype, text)."""
    conn = _connect()
    for pos, (qtype, text) in enumerate(questions):
        conn.execute(
            "INSERT INTO questions (session_id, qtype, text, position)"
            " VALUES (?, ?, ?, ?)",
            (session_id, qtype, text, pos),
        )
    conn.commit()
    conn.close()


def list_sessions():
    conn = _connect()
    rows = conn.execute(
        """
        SELECT s.id, s.title, s.mode, s.created_at,
               COUNT(a.id) AS answered,
               (SELECT COUNT(*) FROM questions q WHERE q.session_id = s.id) AS total,
               ROUND(AVG(a.score), 1) AS avg_score
        FROM sessions s
        LEFT JOIN questions q ON q.session_id = s.id
        LEFT JOIN answers a ON a.question_id = q.id
        GROUP BY s.id
        ORDER BY s.id DESC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session(session_id):
    conn = _connect()
    s = conn.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    if s is None:
        conn.close()
        return None
    questions = conn.execute(
        """
        SELECT q.id, q.qtype, q.text, q.position,
               a.answer_text, a.score, a.feedback, a.tip, a.mode AS answer_mode
        FROM questions q
        LEFT JOIN answers a ON a.question_id = q.id
        WHERE q.session_id = ?
        ORDER BY q.position
        """,
        (session_id,),
    ).fetchall()
    conn.close()
    session = dict(s)
    session["questions"] = [dict(q) for q in questions]
    answered = [q for q in session["questions"] if q["score"] is not None]
    session["avg_score"] = (
        round(sum(q["score"] for q in answered) / len(answered), 1)
        if answered
        else None
    )
    return session


def save_answer(question_id, answer_text, score, feedback, tip, mode):
    conn = _connect()
    # One scored answer per question: replace any previous attempt.
    conn.execute("DELETE FROM answers WHERE question_id = ?", (question_id,))
    conn.execute(
        "INSERT INTO answers (question_id, answer_text, score, feedback, tip, mode, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (question_id, answer_text, score, feedback, tip, mode, _now()),
    )
    conn.commit()
    conn.close()


def get_question(question_id):
    conn = _connect()
    row = conn.execute(
        "SELECT q.*, s.title FROM questions q JOIN sessions s ON s.id = q.session_id"
        " WHERE q.id = ?",
        (question_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
