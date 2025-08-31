from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pyjokes
import wikipedia
import re

# Configure Wikipedia
wikipedia.set_lang("en")

app = Flask(
    __name__,
    static_folder="static",
    static_url_path=""
)
CORS(app)

# ---- Helper functions --------------------------------------------------------

def get_time_reply():
    now = datetime.now()
    return f"It's {now.strftime('%I:%M %p')}."

def get_date_reply():
    now = datetime.now()
    # Example: Sunday, 31 August 2025
    return f"Today is {now.strftime('%A, %-d %B %Y') if hasattr(now, 'strftime') else now.strftime('%A, %d %B %Y')}"

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()

def wiki_summary(query: str) -> str:
    # Try a direct summary; on disambiguation or page error, fall back to search.
    try:
        return wikipedia.summary(query, sentences=2, auto_suggest=True)
    except wikipedia.DisambiguationError as e:
        try:
            return wikipedia.summary(e.options[0], sentences=2, auto_suggest=True)
        except Exception:
            pass
        return f"I found multiple results for {query}. Please be more specific."
    except wikipedia.PageError:
        results = wikipedia.search(query)
        if results:
            try:
                return wikipedia.summary(results[0], sentences=2, auto_suggest=True)
            except Exception:
                return f"I couldn't fetch a summary for {results[0]}."
        return f"I couldn't find anything for {query}."
    except Exception:
        return "I'm having trouble reaching Wikipedia right now."

SITE_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "wikipedia": "https://www.wikipedia.org",
    "stack overflow": "https://stackoverflow.com",
    "linkedin": "https://www.linkedin.com"
}

def parse_open_site(text: str):
    # Check for phrases like "open X" or "launch X"
    m = re.search(r"(open|launch)\s+(.+)", text)
    if not m:
        return None
    site_name = m.group(2).strip().lower()

    # Exact mapping first
    if site_name in SITE_MAP:
        return SITE_MAP[site_name]

    # If it looks like a domain, prepend https://
    if re.match(r"^[a-z0-9\-\.]+\.[a-z]{2,}$", site_name):
        return f"https://{site_name}"

    # If user says "open youtube music", try partials
    for key, url in SITE_MAP.items():
        if key in site_name:
            return url

    return None

def handle_command(raw_text: str):
    text = normalize(raw_text)

    # Greetings
    if any(kw in text for kw in ["hello", "hi ", "hey ", "namaste", "kaal"]):
        return {"reply": "Hello! I am KAAL. How can I assist you?"}

    # Time / Date
    if "time" in text:
        return {"reply": get_time_reply()}
    if "date" in text or "day" in text:
        return {"reply": get_date_reply()}

    # Jokes
    if "joke" in text:
        return {"reply": pyjokes.get_joke()}

    # Open sites
    if text.startswith("open") or text.startswith("launch"):
        url = parse_open_site(text)
        if url:
            return {"reply": f"Opening {url}", "action": "open_url", "url": url}
        return {"reply": "I couldn't identify that site. Try: open YouTube, open GitHub, open Google."}

    # Wikipedia: who/what/tell me about/search wikipedia
    wiki_triggers = [
        r"who is (.+)",
        r"what is (.+)",
        r"tell me about (.+)",
        r"search wikipedia for (.+)",
        r"wikipedia (.+)"
    ]
    for pattern in wiki_triggers:
        m = re.search(pattern, text)
        if m:
            query = m.group(1).strip()
            summary = wiki_summary(query)
            return {"reply": summary}

    # Fallback
    return {
        "reply": (
            "I didn't get that. Try:\n"
            "• What is the time?\n"
            "• Tell me a joke\n"
            "• Who is Ada Lovelace\n"
            "• Open YouTube"
        )
    }

# ---- Routes ------------------------------------------------------------------

@app.route("/")
def root():
    return send_from_directory("static", "index.html")

@app.route("/api/command", methods=["POST"])
def api_command():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"reply": "Please say something for me to process."}), 400
    result = handle_command(text)
    return jsonify(result)

# ---- Entry point -------------------------------------------------------------

if __name__ == "__main__":
    # Run Flask dev server
    app.run(host="127.0.0.1", port=5000, debug=False)
