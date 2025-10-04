import re
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file (ensures key is available)
load_dotenv()

# --- Configuration ---
# API Key and Model ID are read from the environment
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
# Falls back to a reasonable chat model if HF_MODEL_ID isn't set in .env
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")

# Construct the API URL using the model ID from the .env file
API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL_ID}" 

if not HF_API_KEY:
    print("--- WARNING: HUGGINGFACE_API_KEY environment variable not set. API calls will fail. ---")
    
# --- 2. Define System Prompts (UNCHANGED per your requirements) ---
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

CONVERSATION_PROMPT = {
    "role": "system",
    "content": "You are Serenity, a compassionate and supportive mental health chatbot. Never refer to yourself as Aura or any other name. You are NOT a therapist. DO NOT provide medical advice. Keep your responses concise, warm, and non-judgemental. Use less than 50 words."
}


# --- 3. Core API Inference Logic ---

def make_hf_api_call(messages, is_classification=False):
    """
    Makes an authenticated POST request to the Hugging Face Chat Completion API.
    """
    if not HF_API_KEY:
        return "API service is unavailable due to missing key."

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Configure parameters based on task type
    if is_classification:
        params = {
            # Low temperature and sampling for deterministic classification
            "temperature": 0.01,
            "max_new_tokens": 15,
            "do_sample": False,
        }
    else:
        # Higher temperature and sampling for conversational variety
        params = {
            "temperature": 0.7,
            "max_new_tokens": 128,
            "do_sample": True,
        }

    payload = {
        "messages": messages,
        "parameters": params,
        "stream": False 
    }

    try:
        # Use a timeout for robust network operations
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        result = response.json()
        
        if result and 'choices' in result and result['choices']:
            return result['choices'][0]['message']['content'].strip()
        else:
            print(f"API Response Error: No content in result: {result}")
            return "Could not generate a valid response from the API."

    except requests.exceptions.RequestException as e:
        print(f"Request Error during API call to {API_URL}: {e}")
        return "The external AI service is currently unreachable or timed out."
    except Exception as e:
        print(f"An unexpected error occurred processing API response: {e}")
        return "An internal error occurred while processing the AI response."


def classify_intent(user_input, history):
    """ Orchestrates the classification API call using the classification prompt. """
    # Use only recent history for context to save tokens and focus classification
    recent_history = history[-4:]
    messages = [CLASSIFICATION_PROMPT] + recent_history + [{"role": "user", "content": user_input}]
    
    raw_response = make_hf_api_call(messages, is_classification=True)

    # Parse the response to extract the mood tag
    match = re.search(r'\[(mood|intent):\s*([^\]]+)\]', raw_response)
    tag = match.group(2).strip() if match else "neutral"
    
    print(f"--- Classified Intent: {tag} ---")
    return tag


def generate_conversational_response(user_input, history):
    """ Orchestrates the conversational API call using the conversation prompt. """
    # Use full history for conversational context
    messages = [CONVERSATION_PROMPT] + history + [{"role": "user", "content": user_input}]
    
    clean_message = make_hf_api_call(messages, is_classification=False)
    
    # Clean up model prefixing if necessary (some models prepend the persona name)
    return clean_message.replace("Serenity:", "").strip()


def get_response(user_input, history):
    """ Orchestrates the two-step process: classify then respond. """
    mood = classify_intent(user_input, history)
    clean_message = generate_conversational_response(user_input, history)

    # Update history for saving
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": clean_message})

    return mood, clean_message, history
