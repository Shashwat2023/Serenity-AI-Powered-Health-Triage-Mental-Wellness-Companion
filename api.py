from flask import Flask, request, jsonify
from flask_cors import CORS
from bot import get_response
from firestore_db import init_db, get_or_create_user, get_chat_history, save_chat_history, add_mood_log

# Initialize our Flask app and the database
app = Flask(__name__)
CORS(app)  # This allows your HTML/JS front-end to talk to this server
db = init_db()

@app.route('/chat', methods=['POST'])
def chat():
    """
    This is the main API endpoint. It receives a user's message and session ID,
    gets a response from the bot, saves everything to the database,
    and returns the bot's reply.
    """
    try:
        # Get data from the front-end's request
        data = request.get_json()
        prompt = data.get('prompt')
        session_id = data.get('session_id')
        
        if not prompt or not session_id:
            return jsonify({"error": "Prompt and session_id are required."}), 400

        # Use our existing database and bot logic
        user_ref = get_or_create_user(db, session_id)
        history = get_chat_history(user_ref)
        
        mood, response, updated_history = get_response(prompt, history)
        
        # Save the new conversation turn and mood log
        save_chat_history(user_ref, updated_history)
        add_mood_log(user_ref, mood)
        
        # Send the bot's response and the detected mood back to the front-end
        return jsonify({
            "response": response,
            "mood": mood
        })

    except Exception as e:
        print(f"--- API Error: {e} ---")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == '__main__':
    # Run the API server with debug mode OFF to prevent double-loading the model
    app.run(port=5000, debug=False)

