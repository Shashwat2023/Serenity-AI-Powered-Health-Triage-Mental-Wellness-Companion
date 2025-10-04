from flask import Flask, render_template, request, jsonify
import requests
import json
import time
import random
import os
from typing import Dict, List

app = Flask(__name__)

class MentalHealthChatbot:
    def __init__(self, huggingface_api_key: str):
        self.api_key = huggingface_api_key
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
        self.user_mood_indicators = {
            'stress_keywords': ['stress', 'stressed', 'overwhelmed', 'pressure', 'anxious', 'anxiety', 'worried', 'nervous'],
            'sad_keywords': ['sad', 'depressed', 'unhappy', 'miserable', 'hopeless', 'empty', 'lonely', 'down'],
            'anger_keywords': ['angry', 'mad', 'furious', 'irritated', 'frustrated', 'annoyed'],
            'calm_keywords': ['better', 'good', 'calm', 'peaceful', 'relaxed', 'happy', 'great', 'fine']
        }
        
        # Fallback responses for when API is unavailable
        self.fallback_responses = [
            "I'm here to listen to you. Could you tell me more about what you're experiencing?",
            "Thank you for sharing that with me. How has that been affecting you?",
            "I understand this might be difficult to talk about. Take your time.",
            "Your feelings are completely valid. Would you like to explore this further?",
            "I'm listening carefully. Please continue when you feel comfortable."
        ]

    def query_huggingface(self, user_input: str, conversation_history: list) -> str:
        """Send query to Hugging Face API and get response"""
        try:
            if not self.api_key or self.api_key == "dummy_key":
                return random.choice(self.fallback_responses)
                
            # Prepare conversation context
            past_user_inputs = [msg['user'] for msg in conversation_history[-4:] if msg['user']]
            generated_responses = [msg['bot'] for msg in conversation_history[-4:] if msg['bot']]
            
            payload = {
                "inputs": {
                    "text": user_input,
                    "past_user_inputs": past_user_inputs,
                    "generated_responses": generated_responses
                }
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0]['generated_text']
            
            return random.choice(self.fallback_responses)
            
        except Exception as e:
            print(f"API Error: {e}")
            return random.choice(self.fallback_responses)

    def analyze_user_mood(self, user_input: str) -> str:
        """Analyze user input to detect mood and emotional state"""
        input_lower = user_input.lower()
        
        # Count keyword occurrences
        stress_count = sum(1 for word in self.user_mood_indicators['stress_keywords'] if word in input_lower)
        sad_count = sum(1 for word in self.user_mood_indicators['sad_keywords'] if word in input_lower)
        anger_count = sum(1 for word in self.user_mood_indicators['anger_keywords'] if word in input_lower)
        calm_count = sum(1 for word in self.user_mood_indicators['calm_keywords'] if word in input_lower)
        
        # Determine predominant mood
        mood_scores = {
            'stressed': stress_count,
            'sad': sad_count,
            'angry': anger_count,
            'calm': calm_count
        }
        
        predominant_mood = max(mood_scores, key=mood_scores.get)
        
        # Only return mood if significant indicators found
        if mood_scores[predominant_mood] > 0:
            return predominant_mood
        return "neutral"

    def get_coping_suggestions(self, mood: str) -> List[str]:
        """Provide appropriate coping suggestions based on detected mood"""
        suggestions = {
            'stressed': [
                "Let's try some deep breathing together. Breathe in slowly for 4 counts, hold for 4, exhale for 6.",
                "Would you like to try a quick mindfulness exercise? Focus on 5 things you can see around you.",
                "Sometimes breaking tasks into smaller steps can help reduce feeling overwhelmed.",
                "A short walk in nature can do wonders for stress relief. Even 5 minutes can help.",
                "Try placing a hand on your chest and taking three slow, deep breaths."
            ],
            'sad': [
                "It's okay to feel sad. Would you like to share what's on your mind?",
                "Listening to calming music or a favorite podcast might help lift your spirits.",
                "Remember to be kind to yourself. You're doing the best you can.",
                "Sometimes writing down thoughts in a journal can help process emotions.",
                "A warm cup of tea and some gentle stretching might bring some comfort."
            ],
            'angry': [
                "Let's pause for a moment. Count slowly to 10 and take some deep breaths.",
                "Physical activity like stretching or walking can help release angry energy.",
                "Try the 5-4-3-2-1 technique: notice 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste.",
                "Expressing your feelings through writing might help organize your thoughts.",
                "Splash some cool water on your face and take a moment to regroup."
            ],
            'neutral': [
                "I'm glad you're checking in with yourself. Maintaining this balance is wonderful.",
                "Regular mindfulness practice can help maintain emotional equilibrium.",
                "Remember to take breaks throughout your day for self-care.",
                "Staying connected with supportive people can help maintain this positive state."
            ],
            'calm': [
                "It's wonderful that you're feeling calm. Enjoy this peaceful moment.",
                "This is a great time to practice gratitude or meditation.",
                "Your calm state is something to cherish. Perhaps share what helped you reach this peace?",
                "Consider using this peaceful time for some gentle reflection or creative expression."
            ]
        }
        return suggestions.get(mood, suggestions['neutral'])

    def format_response(self, ai_response: str, mood: str, user_input: str) -> Dict:
        """Format the response with appropriate tone and suggestions"""
        
        # Polite and calm opening phrases
        calm_openings = [
            "I understand...",
            "Thank you for sharing...",
            "I hear what you're saying...",
            "That sounds challenging...",
            "I appreciate you telling me this...",
            "It takes courage to share that..."
        ]
        
        # Build response
        formatted_response = f"{random.choice(calm_openings)} {ai_response}"
        
        # Add coping suggestion if mood is detected and not calm/neutral
        coping_suggestion = ""
        if mood in ['stressed', 'sad', 'angry']:
            suggestions = self.get_coping_suggestions(mood)
            coping_suggestion = random.choice(suggestions)
        
        return {
            'response': formatted_response,
            'suggestion': coping_suggestion,
            'mood': mood,
            'timestamp': time.strftime('%H:%M:%S')
        }

# Initialize chatbot with environment variable or default
api_key = os.environ.get('HUGGINGFACE_API_KEY', 'dummy_key')
chatbot = MentalHealthChatbot(api_key)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_history = data.get('history', [])
        
        if not user_message:
            return jsonify({
                'response': "I'm here when you're ready to share. Take your time.",
                'suggestion': "",
                'mood': 'neutral',
                'timestamp': time.strftime('%H:%M:%S')
            })
        
        # Analyze user mood
        mood = chatbot.analyze_user_mood(user_message)
        
        # Get AI response
        ai_response = chatbot.query_huggingface(user_message, conversation_history)
        
        # Format final response
        formatted_response = chatbot.format_response(ai_response, mood, user_message)
        
        return jsonify(formatted_response)
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'response': "I'm here to listen. Could you tell me more about how you're feeling?",
            'suggestion': "",
            'mood': 'neutral',
            'timestamp': time.strftime('%H:%M:%S')
        })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'Mental Health Chatbot is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
