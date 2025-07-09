from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Safely check for the 'tool' decorator
tool = getattr(genai, "tool", None)

# Initialize model
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("gemini-pro")

# Optional tool-decorated function (only if available)
if tool:
    @tool
    def echo_tool(input_text: str) -> str:
        return f"Echo: {input_text}"

@app.route("/ask", methods=["POST"])
def ask_ai():
    data = request.json
    user_input = data.get("input", "")

    if not user_input:
        return jsonify({"error": "No input received"}), 400

    try:
        response = model.generate_content(user_input)
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Required for Gunicorn entry point
if __name__ == "__main__":
    app.run(debug=True)