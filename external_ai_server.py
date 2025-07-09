from flask import Flask, request, jsonify
import requests
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
genai.configure(api_key="AIzaSyDveJ_WAvjV6-QdbVRO4XYqsDpfp5OizdM")
model = genai.GenerativeModel("models/gemini-1.5-flash")

GOOGLE_API_KEY = "AIzaSyA3H_LBsDvBJQZOwyY3C2P9hlFclpAUfBc"
SEARCH_ENGINE_ID = "e1a9a5befafb84223"

# --- Utility Functions ---

def google_search(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query
    }
    response = requests.get(url, params=params).json()
    items = response.get("items", [])

    # Basic relevance scan
    for item in items:
        snippet = item.get("snippet", "").lower()
        title = item.get("title", "").lower()
        if any(kw in snippet + title for kw in ["president", "today is", "release date", "new game", "weather", "down", "status", "event", "happened", "news"]):
            return f"{item['title']}\n{item['link']}\n{item.get('snippet', '')}"

    if items:
        # If nothing matched, return top result
        top = items[0]
        return f"{top['title']}\n{top['link']}\n{top.get('snippet', '')}"

    return None

def ping_site(domain):
    try:
        response = requests.get(f"https://{domain}", timeout=5)
        if response.ok:
            return f"The website '{domain}' is up and responding with status code {response.status_code}."
        else:
            return f"The website '{domain}' responded but with an error: status code {response.status_code}."
    except requests.exceptions.RequestException:
        return f"The website '{domain}' appears to be down or unreachable."

def extract_domain(text):
    # Simple domain extractor from a query like "is wikipedia.org up?"
    words = text.split()
    for word in words:
        if "." in word and not word.startswith("http"):
            return word.strip("?.")
    return None

def route_tool(query):
    query_lower = query.lower()

    if "date" in query_lower or "today" in query_lower:
        return datetime.now().strftime("%A, %B %d, %Y")

    elif "website" in query_lower and ("up" in query_lower or "down" in query_lower):
        domain = extract_domain(query)
        if domain:
            return ping_site(domain)
        return "I couldn't find a domain name in your question."

    elif any(kw in query_lower for kw in ["president", "game release", "news", "weather", "event", "happening", "current", "latest"]):
        return google_search(query)

    return None  # No special routing; fallback to Gemini

# --- Main Chat Endpoint ---

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("owner_message", "").strip()

    if not user_input:
        return jsonify({"error": "Missing input"}), 400

    try:
        dynamic_data = route_tool(user_input)
        if dynamic_data:
            # Gemini adds personality to real-time info
            gemini_output = model.generate_content(f"User asked: '{user_input}'\nUse this information to answer:\n{dynamic_data}")
            return gemini_output.text, 200

        # No tool match — use Gemini directly
        fallback_response = model.generate_content(user_input)
        return fallback_response.text, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)