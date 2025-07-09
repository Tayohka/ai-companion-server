from flask import Flask, request, jsonify
import requests
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)

# --- Gemini setup ---
genai.configure(api_key="AIzaSyDveJ_WAvjV6-QdbVRO4XYqsDpfp5OizdM")
model = genai.GenerativeModel("models/gemini-1.5-flash")

# --- Google Programmable Search setup ---
GOOGLE_API_KEY = "AIzaSyA3H_LBsDvBJQZOwyY3C2P9hlFclpAUfBc"
SEARCH_ENGINE_ID = "e1a9a5befafb84223"

def google_search(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "items" in data:
        top_result = data["items"][0]
        summary = f"Title: {top_result['title']}\nLink: {top_result['link']}\nSnippet: {top_result.get('snippet', '')}"
        return summary
    return None

def is_fresh_query(text):
    keywords = ["today", "date", "weather", "news", "current", "latest", "update"]
    return any(word in text.lower() for word in keywords)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("owner_message", "")

    if not user_input:
        return jsonify({"error": "Missing input"}), 400

    try:
        # Check for freshness needs
        if is_fresh_query(user_input):
            # Get fresh info from Google Search
            search_result = google_search(user_input)
            if search_result:
                # Summarize result with Gemini
                gemini_response = model.generate_content(f"Summarize this for a user in Second Life:\n\n{search_result}")
                return gemini_response.text, 200
            else:
                return "I couldn’t find anything up-to-date on that topic right now.", 200

        # For normal questions, use Gemini directly
        response = model.generate_content(user_input)
        return response.text, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)