# external_ai_server.py (Updated with a 'get_current_datetime' tool for real-time date/time)
from flask import Flask, request, jsonify
import google.generativeai as genai
from google.generativeai import GenerativeModel, tool # Import 'tool' decorator
import os
import urllib.parse
from datetime import datetime # Import datetime module for current time

app = Flask(__name__)

# Configure Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please set it or hardcode it for local use.")

genai.configure(api_key=GEMINI_API_KEY)

# --- NEW: Define the 'get_current_datetime' tool ---
@tool # This decorator tells Gemini that the following function is a tool it can use
def get_current_datetime():
    """
    Returns the current date and time in a human-readable format.
    The model can call this tool when it needs up-to-date time information.
    """
    now = datetime.now()
    # Format the date and time beautifully
    return now.strftime("The current date and time is: %A, %B %d, %Y at %I:%M:%S %p %Z")

# Initialize the Gemini Model and register our new tool
# We pass the tool function to the 'tools' parameter when creating the model.
model = GenerativeModel(
    'models/gemini-1.5-flash', # Keeping this model as it's working for your key
    tools=[get_current_datetime] # Register our new tool here!
)
# Start a chat session (history is maintained automatically by the 'chat' object)
chat = model.start_chat(history=[])

@app.route('/chat', methods=['POST'])
def handle_chat():
    try:
        data = request.get_json()
        owner_message_encoded = data.get('owner_message', '')
        owner_message = urllib.parse.unquote(owner_message_encoded)

        print(f"Received message from LSL: {owner_message}")

        # Send the user's message to the chat model
        # The model will decide whether to use the tool or respond directly
        response = chat.send_message(owner_message)

        ai_response_text = ""
        # Process the model's response parts
        for part in response.parts:
            if part.text:
                # If the model directly generates text, append it
                ai_response_text += part.text
            elif part.function_call:
                # If the model decides to call a tool
                tool_name = part.function_call.name
                tool_args = part.function_call.args # Arguments the model wants to pass to the tool (none for our date tool)

                print(f"Model called tool: {tool_name} with args: {tool_args}")

                if tool_name == "get_current_datetime":
                    # Execute our Python function for the tool
                    tool_result = get_current_datetime() 
                    print(f"Tool '{tool_name}' returned: {tool_result}")

                    # Send the tool's result BACK to the model
                    # The model will then use this result to formulate its final, intelligent response
                    final_response_after_tool = chat.send_message(genai.tool_result(tool_result))
                    ai_response_text += final_response_after_tool.text
                else:
                    # Handle any other unexpected tool calls gracefully
                    print(f"Unknown tool called: {tool_name}. This should not happen with current setup.")
                    ai_response_text += f"I attempted to use a tool, but encountered an unexpected issue with: {tool_name}. Mrow!"
        
        # In case the model responds with only a tool call and no initial text
        if not ai_response_text and response.text:
            ai_response_text = response.text

        print(f"Gemini response: {ai_response_text}")

        # Return the AI's response to Second Life
        return ai_response_text, 200

    except Exception as e:
        print(f"Error processing request: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)