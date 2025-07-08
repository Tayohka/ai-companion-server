# external_ai_server.py (Example using Flask and Google Gemini API - for Local PC)
from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import urllib.parse

# CORRECTED LINE: Use __name__ to initialize the Flask app.
app = Flask(__name__)

# Configure Google Gemini API
# IMPORTANT: Replace with your actual Gemini API Key from Google AI Studio.
# It's best practice to store this in an environment variable, but for personal local use,
# you can place it directly here for simplicity (though still less secure).
# For example: GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Recommended: Set this as an environment variable
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please set it or hardcode it for local use.")

genai.configure(api_key=GEMINI_API_KEY)
#try:
#    print("--- Listing available Gemini models (DEBUG INFO) ---")
#    for m in genai.list_models():
#        # Check if the model supports content generation (for chat)
#        if 'generateContent' in m.supported_generation_methods:
#            print(f"Model Name: {m.name}, Supported Methods: {m.supported_generation_methods}")
#    print("--- End of Model List ---")
#except Exception as e:
#    print(f"Error while trying to list models: {e}")
# Initialize the Gemini Pro model for conversational chat
model = genai.GenerativeModel('models/gemini-1.5-flash')
chat = model.start_chat(history=[]) # Start a chat session to maintain context

@app.route('/chat', methods=['POST'])
def handle_chat():
    try:
        data = request.get_json()
        owner_message_encoded = data.get('owner_message', '')
        
        # Unescape the URL-encoded message from LSL
        owner_message = urllib.parse.unquote(owner_message_encoded)

        print(f"Received message from LSL: {owner_message}")

        # Send message to Gemini and get response
        response = chat.send_message(owner_message)
        ai_response = response.text

        print(f"Gemini response: {ai_response}")

        # Return the AI's response directly
        return ai_response, 200

    except Exception as e:
        print(f"Error processing request: {e}")
        return str(e), 500

if __name__ == '__main__':
    # Listen on all available interfaces (0.0.0.0) on port 5000.
    app.run(host='0.0.0.0', port=5000)