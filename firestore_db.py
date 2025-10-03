import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
from google.cloud.firestore import Transaction, Increment

# Global DB instance for use across the application
db = None

def init_db():
    """
    Initializes the Firestore database connection using credentials.
    Returns the database client instance.
    """
    global db
    if db is None:
        if not firebase_admin._apps:
            # IMPORTANT: Replace "config/firestore-credentials.json" with the actual path 
            # to your service account key file.
            try:
                cred = credentials.Certificate("config/firestore-credentials.json")
                firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"ERROR: Could not initialize Firebase Admin SDK. Check 'config/firestore-credentials.json' file path and content. {e}")
                return None
        db = firestore.client()
        print("--- Firestore DB Initialized Successfully ---")
    return db

def get_or_create_user(db, session_id):
    """
    Finds a user's document by their session ID, or creates a new one 
    with initial profile data.
    Returns the user's document reference.
    """
    user_ref = db.collection('users').document(session_id)
    
    # Check if user exists, if not, create initial profile data
    if not user_ref.get().exists:
        print(f"--- Creating new user document ---")
        user_ref.set({
            'created_at': firestore.SERVER_TIMESTAMP,
            'chat_history': [],
            'sessions_completed': 0,
            'days_active': 0,
            'progress_score': 0,
            'last_active': None,
            'name': 'Serenity User',
            'email': f'user_{session_id[:8]}@serenity.app'
        })
    return user_ref

def get_chat_history(user_ref):
    """
    Retrieves the chat history for a given user.
    """
    user_doc = user_ref.get()
    return user_doc.to_dict().get('chat_history', []) if user_doc.exists else []

def save_chat_history(user_ref, updated_history):
    """
    Saves the entire updated chat history to the user's document.
    """
    user_ref.update({'chat_history': updated_history})
    print("--- Chat history saved successfully. ---")

def add_mood_log(user_ref, mood):
    """
    Adds a new mood entry to a 'mood_logs' subcollection for the user.
    """
    if mood and mood != 'neutral':
        mood_logs_ref = user_ref.collection('mood_logs')
        mood_logs_ref.add({'mood': mood, 'timestamp': firestore.SERVER_TIMESTAMP})
        print(f"--- Mood log added: {mood} ---")

def update_daily_activity(user_ref):
    """
    Updates the days_active count only if the user hasn't been active today.
    Uses a transaction for atomic and safe read-modify-write.
    """
    @firestore.transactional
    def transaction_update(transaction: Transaction, ref):
        snapshot = ref.get(transaction=transaction)
        
        last_active = snapshot.get('last_active')
        
        today_utc = datetime.now(timezone.utc).date()
        was_active_today = False
        
        if last_active and isinstance(last_active, datetime):
            if last_active.astimezone(timezone.utc).date() == today_utc:
                was_active_today = True

        if not was_active_today:
            updates = {
                'days_active': Increment(1),
                'last_active': firestore.SERVER_TIMESTAMP
            }
            transaction.update(ref, updates)
            print("--- Daily activity streak updated. ---")
            return True
        return False

    db_client = user_ref.firestore
    transaction = db_client.transaction()
    try:
        transaction_update(transaction, user_ref)
    except Exception as e:
        print(f"Transaction failed: {e}")
        

def get_mood_logs(user_ref):
    """
    Retrieves all mood logs for a user, ordered by timestamp.
    """
    mood_logs_ref = user_ref.collection('mood_logs').order_by(
        'timestamp', direction=firestore.Query.DESCENDING
    ).limit(10) # Get the 10 most recent logs
    
    logs = []
    for doc in mood_logs_ref.stream():
        logs.append(doc.to_dict())
    return logs
    
# This function is not currently integrated into the backend but provides
# the necessary structure for the profile feature later.
def get_user_profile(user_ref):
    """Retrieves core user profile data."""
    user_doc = user_ref.get()
    if not user_doc.exists:
        return None 
        
    data = user_doc.to_dict()
    
    # Placeholder for calculating mood entries count (needs a more efficient query if many users)
    # For now, we rely on data stored in the main document or simple stream count.
    
    if 'created_at' in data and data['created_at']:
        data['joinDate'] = data['created_at'].strftime('%B %Y')
        
    return {
        'name': data.get('name', 'Serenity User'),
        'email': data.get('email', ''),
        'joinDate': data.get('joinDate', 'Unknown'),
        'sessionsCompleted': data.get('sessions_completed', 0),
        'daysActive': data.get('days_active', 0),
        'moodEntries': len(get_mood_logs(user_ref)), # Re-fetch count
        'progress': data.get('progress_score', 0)
    }
