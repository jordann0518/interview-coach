"""Offline mode: generic question bank + rule-based scoring.

Used whenever ANTHROPIC_API_KEY is not set (or the API call fails), so the
app always demos end-to-end. Everything here is clearly labeled "offline"
in the UI so nobody mistakes rule-based feedback for AI feedback.
"""

BEHAVIORAL = [
    "Tell me about yourself and why you're interested in this internship.",
    "Describe a challenging bug or technical problem you faced on a project. "
    "What did you do, and what was the outcome?",
    "Tell me about a time you had to learn a new technology quickly. How did you approach it?",
    "Describe a disagreement you had while working on a team project. How did you resolve it?",
    "Tell me about a time you missed a deadline or made a mistake. What did you learn?",
    "Why do you want this role, and what do you hope to learn from it?",
]

TECHNICAL_POOLS = {
    "python": [
        "Explain the difference between a list and a tuple in Python. When would you choose one over the other?",
        "What is a dictionary in Python, and how would you count the frequency of words in a paragraph with one?",
        "Describe how you would find duplicates in a list of one million integers efficiently. "
        "What is the time complexity of your approach?",
    ],
    "sql": [
        "Explain the difference between INNER JOIN and LEFT JOIN, with an example.",
        "How would you find the top 5 customers by total order value in a SQL database?",
    ],
    "web": [
        "Explain the difference between GET and POST requests. When would you use each?",
        "Walk me through what happens when a user submits a form on a website, from browser to database.",
    ],
    "general": [
        "How do you approach debugging when a program crashes with no clear error message?",
        "Explain Big-O notation and give the time complexity of binary search.",
        "What is version control, and describe a typical Git workflow for a small team.",
    ],
}

TECHNICAL_KEYWORDS = {
    "python": ["python", "backend", "software"],
    "sql": ["sql", "database", "data"],
    "web": ["web", "frontend", "react", "javascript", "full-stack", "full stack"],
}


def pick_offline_questions(job_description):
    """Choose 3 behavioral + 3 technical questions, lightly tailored by JD keywords.

    Technical pools are round-robined so a JD mentioning several stacks (e.g.
    Python + SQL) gets a mix instead of one pool dominating.
    """
    jd = (job_description or "").lower()
    pools = []
    for pool, keywords in TECHNICAL_KEYWORDS.items():
        if any(k in jd for k in keywords):
            pools.append(list(TECHNICAL_POOLS[pool]))
    pools.append(list(TECHNICAL_POOLS["general"]))
    tech, seen = [], set()
    while len(tech) < 3 and any(pools):
        for pool in pools:
            if pool and len(tech) < 3:
                q = pool.pop(0)
                if q not in seen:
                    seen.add(q)
                    tech.append(q)
        pools = [p for p in pools if p]
    behavioral = BEHAVIORAL[:3]
    return [("behavioral", q) for q in behavioral] + [("technical", q) for q in tech]


BEHAVIORAL_SIGNALS = ["situation", "task", "action", "result", "learned",
                      "for example", "for instance", "because", "led to"]
TECHNICAL_SIGNALS = ["because", "trade-off", "tradeoff", "complexity", "o(n",
                     "def ", "example", "instead", "however", "first,"]

OFFLINE_TIPS = {
    "short": "Your answer is very brief. Aim for 4-6 sentences: add what you did, "
             "why you chose that approach, and what the outcome was.",
    "specifics": "Add concrete specifics — numbers, tool names, and measurable outcomes. "
                 "Interviewers remember details like 'cut load time by 40%' far more than generalities.",
    "structure": "Use a clear structure: state your approach first, then walk through it step by step, "
                 "then close with the result or takeaway.",
}


def score_offline(question_text, qtype, answer):
    """Rule-based 1-10 scoring. Honest heuristic, labeled as offline feedback."""
    text = (answer or "").strip()
    words = text.split()
    n = len(words)
    lowered = text.lower()

    score = 2
    if n >= 150:
        score += 3
    elif n >= 80:
        score += 2
    elif n >= 30:
        score += 1

    has_number = any(ch.isdigit() for ch in text)
    if has_number:
        score += 1

    signals = BEHAVIORAL_SIGNALS if qtype == "behavioral" else TECHNICAL_SIGNALS
    hits = sum(1 for s in signals if s in lowered)
    score += min(hits, 2)

    if n < 10:  # one-liners can't score well no matter what
        score = min(score, 4)
    score = max(1, min(10, score))

    parts = []
    if n >= 80:
        parts.append(f"Good depth at {n} words — you gave the answer room to breathe.")
    elif n >= 30:
        parts.append(f"At {n} words this is a reasonable length, but there's room to expand.")
    else:
        parts.append(f"At only {n} words, this answer is too thin to be convincing.")
    if has_number:
        parts.append("Nice use of concrete numbers — specifics make answers credible.")
    else:
        parts.append("No concrete specifics (numbers, names, outcomes) — those are what make answers memorable.")
    if hits >= 2:
        parts.append("The answer has a clear narrative structure, which is easy to follow.")
    else:
        parts.append("The structure is hard to follow; a clear beginning-middle-end would help.")

    if n < 30:
        tip = OFFLINE_TIPS["short"]
    elif not has_number:
        tip = OFFLINE_TIPS["specifics"]
    else:
        tip = OFFLINE_TIPS["structure"]

    feedback = " ".join(parts[:3])
    return score, "[Offline mode] " + feedback, tip
