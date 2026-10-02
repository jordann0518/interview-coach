"""Entry point. Loads .env (if present) then starts the dev server.

Set ANTHROPIC_API_KEY to enable AI question generation and scoring;
without it the app runs in offline mode with a built-in question bank.
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv():
    path = os.path.join(BASE, ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    mode = "AI" if os.environ.get("ANTHROPIC_API_KEY") else "OFFLINE"
    print(f"interview-coach starting in {mode} mode → http://127.0.0.1:5000")
    app.run(debug=True)
