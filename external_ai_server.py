from flask import Flask, request, jsonify
import requests
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel("gemini-pro")

GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
SEARCH_ENGINE_ID = "YOUR_SEARCH_ENGINE_ID"

# --- Core Utilities ---

def google_search(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query
    }
    response = requests.get(url, params=params).json()
    results = response.get("items", [])

    # Scan for relevance using keyword priority
    priority_keywords = [
        "president", "date", "weather", "release date",
        "game", "event", "switch 2", "happening", "today",
        "current", "time", "announcement", "upcoming", "schedule"
    ]
    trusted_domains = ["cnn.com", "bbc.com", "nintendo.com", "ign.com", "reuters.com", "whitehouse.gov", "nytimes.com"]

    for item in results:
        title = item.get("title", "").lower()
        snippet = item.get("snippet", "").lower()
        link = item.get("link", "")
        domain = link.split("/")[2] if "/" in link else ""

        # Confidence boost if trusted source + priority keyword match
        if any(kw in title + snippet for kw in priority_keywords) and any(src in domain for src in trusted_domains):
            return f"{item['title']}\n{item['link']}\n{item.get('snippet', '')}"

    # Fallback to top result if nothing matched
    if results:
        top = results[0]
        return f"{top['title']}\n{top['link']}\n{top.get('snippet', '')}"

    return None

def ping_site(domain):
    try:
        response = requests.get(f"https://{domain}", timeout=5)
        if response.ok:
            return f"The website '{domain}' is online. Status code: {response.status_code}."
        else:
            return f"Site responded with error status code: {response.status_code}."
    except Exception:
        return f"The website '{domain}' appears to be down or unreachable."

def extract_domain(text):
    words = text.split()
    for word in words:
        if "." in word and not word.startswith("http"):
            return word.strip(".,?!")
    return None

def get_weather_stub():
    # Placeholder — replace with live weather API later
    return "It's partly cloudy with mild temperatures in Columbus, GA."

def route_tool(query):
    query_lower = query.lower()

    if "date" in query_lower or "today" in query_lower:
        return datetime.now().strftime("%A, %B %d, %Y")

    if "time" in query_lower:
        return datetime.now().strftime("%I:%M %p %Z")

    if "website" in query_lower and ("up" in query_lower or "down" in query_lower):
        domain = extract_domain(query)
        return ping_site(domain) if domain else "I couldn’t find a domain name in your question."

    if "weather" in query_lower or "temperature" in query_lower:
        return get_weather_stub()

    if any(k in query_lower for k in ["president", "news", "release", "event", "game", "switch 2", "who is", "what happened", "current"]):
        return google_search(query)

    return None  # Route to Gemini normally

# --- Primary Route ---

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("owner_message", "").strip()

    if not user_input:
        return jsonify({"error": "Missing input"}), 400

    try:
        dynamic_data = route_tool(user_input)

        if dynamic_data:
            gemini_reply = model.generate_content(f"User asked: '{user_input}'\nUse this information to respond naturally:\n{dynamic_data}")
            return gemini_reply.text, 200

        # Gemini handles non-dynamic questions
        fallback = model.generate_content(user_input)
        return fallback.text, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)