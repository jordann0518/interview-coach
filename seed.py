"""Seed a demo session so the app works out of the box.

Usage: .venv/bin/python seed.py
Creates one offline-mode session ("Sample: Software Engineering Intern")
with 6 built-in questions. Safe to run multiple times.
"""
from app import db, offline

JD = """Software Engineering Intern (Summer 2027)

We are looking for a Computer Science student with experience in Python.
You will work with our backend team on web services, write SQL queries
against production databases, and participate in code reviews. Strong
problem-solving skills and eagerness to learn required."""


def main():
    db.init_db()
    sid = db.create_session("Sample: Software Engineering Intern", JD, "offline")
    db.add_questions(sid, offline.pick_offline_questions(JD))
    print(f"Seeded demo session id={sid}. Open http://127.0.0.1:5000/sessions/{sid}")


if __name__ == "__main__":
    main()
