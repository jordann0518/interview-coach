# interview-coach 🎯

An AI-powered technical interview prep app. Paste a job description → get
tailored practice questions (behavioral + technical) → answer them → get
each answer scored with specific feedback and improvement tips. Built by
Jordan Nix to prep for Summer 2027 internship interviews.

## Quick start

```bash
cd interview-coach
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Optional: enable AI mode (otherwise the app runs in offline mode)
export ANTHROPIC_API_KEY="sk-ant-..."
# ...or put it in a .env file (git-ignored):  ANTHROPIC_API_KEY=sk-ant-...

.venv/bin/python seed.py        # create a demo session (works with no API key)
.venv/bin/python run.py         # → http://127.0.0.1:5000
```

Environment variables:

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | No | Enables AI question generation + scoring. Without it, the app runs in **offline mode**. |
| `ANTHROPIC_MODEL` | No | Model override (default: `claude-sonnet-4-5`). |
| `INTERVIEW_COACH_DB` | No | SQLite path (default: `~/.interview_coach.db`). |

⚠️ **Never commit an API key.** `.env` is git-ignored; the key is read only
from the environment at runtime.

## Features

1. **JD → questions**: paste a job description; the app generates 6 tailored
   questions (3 behavioral, 3 technical matched to the role's stack), saved to SQLite.
2. **Answer scoring**: type an answer; get a 1–10 score, 2–3 sentences of
   specific feedback, and one concrete improvement tip.
3. **Session history**: the home page lists past sessions with questions
   answered and average scores; each session page shows per-question results.
4. **Offline mode**: with no API key, the app still runs end-to-end using a
   built-in question bank (lightly tailored by JD keywords) and honest
   rule-based feedback — always labeled "offline mode" in the UI.
5. **Graceful degradation**: if an API call fails mid-session, the app falls
   back to offline mode for that step instead of crashing.

## Architecture

```
interview-coach/
├── run.py              # entry point; loads .env, starts Flask
├── seed.py             # seeds a demo session (no API key needed)
├── app/
│   ├── __init__.py     # create_app factory
│   ├── routes.py       # /, POST /sessions, /sessions/<id>, answer scoring
│   ├── db.py           # SQLite layer (stdlib sqlite3)
│   ├── ai.py           # Anthropic question-gen + scoring prompts
│   ├── offline.py      # offline question bank + rule-based scoring
│   └── templates/ static/
```

**Data model** (SQLite): `sessions` → `questions` → `answers` (one scored
answer per question; re-submitting replaces the previous attempt so the
average score always reflects your latest try).

**Prompt design** (`app/ai.py`):
- *Question generation*: the full JD is embedded in the prompt with explicit
  instructions to match technical questions to the role's stack and calibrate
  difficulty for a college underclassman. The model must reply with a strict
  JSON array (`[{"type": ..., "text": ...}]`); the parser tolerates markdown
  fences and validates that exactly 6 questions came back.
- *Scoring*: the question, its type, and the candidate's answer are embedded
  with a 1–10 rubric (9–10 exceptional … 1–2 poor). The model must reply with
  strict JSON `{"score", "feedback", "tip"}`. Scores are clamped to 1–10.

**Scoring rubric** (shared by both modes): 9–10 exceptional, 7–8 strong,
5–6 adequate, 3–4 weak, 1–2 poor. The offline scorer is a transparent
heuristic (answer length + concrete specifics + structure signals, capped for
one-liners) — useful for demos, not a substitute for real feedback.

## Cost & latency notes (honest)

- AI mode makes ~1 API call per session creation (question gen, ~1200 max
  tokens) and ~1 call per submitted answer (~600 max tokens). With a Sonnet-
  class model that's a few cents per full practice session.
- Typical latency: 5–20 seconds per generation/scoring call. The UI is
  synchronous, so the browser waits — fine for personal use, not for production.
- Offline mode costs nothing and responds instantly.
- If you change `ANTHROPIC_MODEL` to a cheaper/faster model (e.g. a Haiku-
  class model), costs and latency drop proportionally; question quality drops
  a bit too. Worth experimenting with.
