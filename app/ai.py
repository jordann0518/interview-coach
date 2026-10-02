"""Anthropic-powered question generation and answer scoring.

The API key is NEVER hardcoded: it comes from the ANTHROPIC_API_KEY
environment variable (optionally via a .env file loaded by the caller).
If the key is missing or a call fails, callers fall back to offline mode.
"""
import json
import os

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")


def _client():
    import anthropic  # imported lazily so offline mode needs no key/package init
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=api_key)


def _parse_json(text):
    """Tolerate ```json fences around the model's JSON output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[: -3]
    return json.loads(text.strip())


def has_api_key():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


QUESTION_PROMPT = """You are an interview coach. Read this job description and write 6 interview
practice questions tailored to the role: 3 behavioral and 3 technical.

Job description:
\"\"\"
{jd}
\"\"\"

Rules:
- Technical questions must match the role's actual stack/skills (e.g. Python questions
  for a Python role, SQL for a data role). Calibrate difficulty for a college
  freshman/sophomore CS student applying to an internship.
- Behavioral questions should probe teamwork, problem-solving, and motivation.
- Reply with ONLY a JSON array of objects like:
  [{{"type": "behavioral", "text": "..."}}, {{"type": "technical", "text": "..."}}]
- No markdown, no commentary, just the JSON array."""


def generate_questions(job_description):
    """Returns list of (qtype, text). Raises on API failure (caller falls back)."""
    client = _client()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": QUESTION_PROMPT.format(jd=job_description[:4000])}],
    )
    items = _parse_json(resp.content[0].text)
    questions = []
    for item in items[:6]:
        qtype = item.get("type", "technical")
        if qtype not in ("behavioral", "technical"):
            qtype = "technical"
        questions.append((qtype, item["text"].strip()))
    if len(questions) < 6:
        raise RuntimeError("Model returned fewer than 6 questions")
    return questions


SCORE_PROMPT = """You are a strict but fair interview coach scoring a practice answer.

Question ({qtype}): {question}

Candidate's answer:
\"\"\"
{answer}
\"\"\"

Rubric (score 1-10):
- 9-10: exceptional — specific, well-structured, shows depth
- 7-8: strong — clear and mostly specific
- 5-6: adequate — vague in places, thin on specifics
- 3-4: weak — rambling or off-topic
- 1-2: poor — empty or nonsensical

Reply with ONLY a JSON object, no markdown:
{{"score": <int 1-10>, "feedback": "<2-3 sentences of SPECIFIC feedback referencing what they actually wrote>", "tip": "<one concrete improvement tip>"}}"""


def score_answer(question_text, qtype, answer):
    """Returns (score, feedback, tip). Raises on API failure (caller falls back)."""
    client = _client()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": SCORE_PROMPT.format(
                qtype=qtype, question=question_text, answer=answer[:2000]),
        }],
    )
    data = _parse_json(resp.content[0].text)
    score = int(data["score"])
    score = max(1, min(10, score))
    return score, data["feedback"].strip(), data["tip"].strip()
