import re
import os
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import firestore_db # Assuming firestore_db.py is in the same directory

# --- 1. Load the Local AI Model and Tokenizer ---
MODEL_ID = "microsoft/Phi-3-mini-4k-instruct"

# Using environment variables or a check for system memory might be better, but sticking to 
# previous configuration for consistency.
print("--- Creating 4-bit Quantization Config ---")
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

print("--- Loading Local Model and Tokenizer... ---")
# Adjust device mapping if needed based on your machine
model_load_args = {
    "quantization_config": quantization_config,
    "device_map": "auto",
}

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **model_load_args)
    try:
        model = torch.compile(model)
        print("--- Model compiled with torch.compile for extra speed ---")
    except Exception:
        print("--- torch.compile not available or failed. ---")
    print("--- Model and Tokenizer Loaded Successfully ---")

except Exception as e:
    print(f"--- Failed to load model: {e}. Running in degraded mode or exiting. ---")
    # Set to None if loading fails
    model = None
    tokenizer = None


# --- 2. Define System Prompts ---
CLASSIFICATION_PROMPT = {
    "role": "system",
    "content": (
        "You are a classification expert. Analyze the user's message and respond with ONLY ONE of the following tags that best fits the user's current emotion. Do not add any other text. "
        "The available tags are: [mood: happy], [mood: neutral], [mood: sad], [mood: anxious], [intent: seeking_community], [intent: serious_distress]."
        "\n\nHere are some examples:\n"
        "User: I'm so happy today, everything is going great!\nAssistant: [mood: happy]\n"
        "User: what's up\nAssistant: [mood: neutral]\n"
        "Your response must strictly contain ONLY the tag, e.g., [mood: happy]."
    )
}

# 🛠️ CHANGE APPLIED HERE: Explicitly reinforcing 'Serenity' and forbidding 'Aura'.
CONVERSATION_PROMPT = {
    "role": "system",
    "content": "You are Serenity, a compassionate and supportive mental health chatbot. Never refer to yourself as Aura or any other name. You are NOT a therapist. DO NOT provide medical advice. Keep your responses concise, warm, and non-judgemental. Use less than 50 words."
}


# --- 3. Core AI Inference Logic (Refactored to accept history) ---

def classify_intent(user_input, history):
    """
    First call to the AI: Classify the user's most recent message using limited history for context.
    """
    if not model or not tokenizer:
        print("Model not loaded, skipping classification.")
        return "neutral"
        
    # Use the last 4 messages (2 user, 2 assistant) for context, plus the current prompt
    recent_history = history[-4:]
    messages = [CLASSIFICATION_PROMPT] + recent_history + [{"role": "user", "content": user_input}]
    
    input_ids = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt"
    ).to(model.device)
    
    with torch.inference_mode():
        outputs = model.generate(
            input_ids, max_new_tokens=15, eos_token_id=tokenizer.eos_token_id, 
            do_sample=False, temperature=0.0 # Force deterministic output
        )
    
    response_ids = outputs[0][input_ids.shape[-1]:]
    raw_response = tokenizer.decode(response_ids, skip_special_tokens=True).strip()
    
    match = re.search(r'\[(mood|intent):\s*([^\]]+)\]', raw_response)
    tag = match.group(2).strip() if match else "neutral"
    
    print(f"--- Classified Intent: {tag} ---")
    return tag


def generate_conversational_response(user_input, history):
    """
    Second call to the AI: Generate a conversational reply based on full history.
    """
    if not model or not tokenizer:
        return "Sorry, the AI model is currently offline. Please try again later."
        
    messages = [CONVERSATION_PROMPT] + history + [{"role": "user", "content": user_input}]
    
    input_ids = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt"
    ).to(model.device)
    
    with torch.inference_mode():
        outputs = model.generate(
            input_ids,
            max_new_tokens=128,
            temperature=0.7,
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id,
        )
        
    response_ids = outputs[0][input_ids.shape[-1]:]
    clean_message = tokenizer.decode(response_ids, skip_special_tokens=True).strip()
    return clean_message


def get_response(user_input, history):
    """ Orchestrates the two-step process: classify then respond. """
    mood = classify_intent(user_input, history)
    clean_message = generate_conversational_response(user_input, history)

    # Update history for saving
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": clean_message})

    return mood, clean_message, history


# --- 4. Flask Application Setup and Routing ---
app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication
DB = firestore_db.init_db() # Initialize Firestore

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """ Handles new chat messages, persistence, and AI interaction. """
    try:
        data = request.json
        user_input = data.get('prompt')
        session_id = data.get('session_id')
        
        if not user_input or not session_id:
            return jsonify({"error": "Missing prompt or session_id"}), 400

        user_ref = firestore_db.get_or_create_user(DB, session_id)
        
        # Load history and update daily activity before running inference
        history = firestore_db.get_chat_history(user_ref)
        firestore_db.update_daily_activity(user_ref) 
        
        mood, clean_message, updated_history = get_response(user_input, history)

        firestore_db.add_mood_log(user_ref, mood) 
        firestore_db.save_chat_history(user_ref, updated_history)

        return jsonify({
            "response": clean_message, 
            "mood": mood,
            "session_id": session_id
        })
    
    except Exception as e:
        print(f"An error occurred in chat_endpoint: {e}")
        return jsonify({"error": "Internal server error during chat processing."}), 500

@app.route('/history', methods=['GET'])
def history_endpoint():
    """ Endpoint to retrieve the entire chat history. """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({"error": "Missing session_id parameter"}), 400

        user_ref = firestore_db.get_or_create_user(DB, session_id)
        history = firestore_db.get_chat_history(user_ref)
        
        # The history format is suitable for the frontend (role: user/assistant, content: text)
        return jsonify({"history": history})
        
    except Exception as e:
        print(f"An error occurred in history_endpoint: {e}")
        return jsonify({"error": "Internal server error retrieving history."}), 500


if __name__ == '__main__':
    # Ensure your firestore-credentials.json is in the config/ directory
    # Run with: python bot.py
    # Debug mode is helpful but may cause issues with model loading on some systems
    app.run(host='0.0.0.0', port=5000)