from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configure Gemini model
genai.configure(api_key="AIzaSyDveJ_WAvjV6-QdbVRO4XYqsDpfp5OizdM")
model = genai.GenerativeModel("models/gemini-1.5-flash")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("owner_message")  # Match key from LSL script

        if not user_input:
            return jsonify({"error": "Missing owner_message"}), 400

        response = model.generate_content(user_input)
        return response.text, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Make sure Gunicorn finds this
if __name__ == "__main__":
    app.run(debug=True)