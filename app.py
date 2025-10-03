import streamlit as st
from bot import get_response
from firestore_db import (
    init_db, get_or_create_user, get_chat_history, save_chat_history, 
    add_mood_log, get_mood_logs
)
import uuid
import time
from datetime import datetime, timezone

# Initialize DB
db = init_db()

# Page Config
st.set_page_config(page_title="Aura Chatbot", page_icon="🧠", layout="centered")

# User Session Management
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
user_ref = get_or_create_user(db, st.session_state.session_id)

# State Management for Exercises
if 'in_exercise' not in st.session_state:
    st.session_state.in_exercise = False
if 'exercise_step' not in st.session_state:
    st.session_state.exercise_step = 0
if 'in_panic_mode' not in st.session_state:
    st.session_state.in_panic_mode = False
if 'panic_step' not in st.session_state:
    st.session_state.panic_step = 0

# Content for the Exercises
GROUNDING_EXERCISE = [
    {"step": "Start", "text": "Let's begin. Take a slow, deep breath. In through your nose... and out through your mouth."},
    {"step": "5 Senses: Sight", "text": "Look around you. Name **5** things you can see."},
    {"step": "5 Senses: Touch", "text": "Now, focus on touch. Name **4** things you can feel."},
    {"step": "5 Senses: Hearing", "text": "Listen closely. Name **3** things you can hear."},
    {"step": "5 Senses: Smell", "text": "Take a moment to notice scents. Name **2** things you can smell."},
    {"step": "5 Senses: Taste", "text": "Finally, focus on taste. Name **1** thing you can taste."},
    {"step": "Finish", "text": "Great job. You've completed the exercise. Take one more deep breath."}
]
PANIC_EXERCISE = [
    {"step": "Step 1: Prepare", "text": "We'll do a simple breathing exercise. Find a comfortable position and try to relax your shoulders.", "duration": 4},
    {"step": "Step 2: Breathe In", "text": "Slowly breathe **in** through your nose...", "duration": 4},
    {"step": "Step 3: Hold", "text": "Now, gently **hold** your breath...", "duration": 4},
    {"step": "Step 4: Breathe Out", "text": "Slowly breathe **out** through your mouth...", "duration": 4},
    {"step": "Step 5: Hold", "text": "Gently **hold** again...", "duration": 4},
    {"step": "Repeat", "text": "You're doing great. Let's continue. **In**... **hold**... **out**... **hold**...", "duration": 8},
    {"step": "Finish", "text": "You are in control. The exercise is complete. You can return to the chat when you're ready.", "duration": 0}
]

# --- Sidebar UI ---
with st.sidebar:
    st.header("Tools")
    if st.button("🚨 I'm Panicking", use_container_width=True):
        st.session_state.in_panic_mode = True
        st.session_state.panic_step = 0
        st.rerun()

    st.divider()
    
    st.header("🧠 Your Mood Log")
    mood_logs = get_mood_logs(user_ref)
    if not mood_logs:
        st.info("Your mood log is empty.")
    else:
        for log in mood_logs:
            log_time = log['timestamp'].strftime("%B %d, %Y")
            st.markdown(f"- **{log['mood'].capitalize()}** on *{log_time}*")


# --- Main App Interface ---
st.title("Aura: Your Support Chatbot")
st.write("A safe space to share what's on your mind. I'm here to listen.")

if st.session_state.in_panic_mode:
    step_data = PANIC_EXERCISE[st.session_state.panic_step]
    st.subheader(f"Calm Down: {step_data['step']}")
    st.markdown(f"## {step_data['text']}")
    
    if st.session_state.panic_step == len(PANIC_EXERCISE) - 1:
        if st.button("Finish"):
            st.session_state.in_panic_mode = False
            st.session_state.panic_step = 0
            st.success("You did a great job! Returning to chat.")
            time.sleep(1)
            st.rerun()
    else:
        with st.spinner(f"Pausing for {step_data['duration']} seconds..."):
            time.sleep(step_data['duration'])
        st.session_state.panic_step += 1
        st.rerun()

elif st.session_state.in_exercise:
    step_data = GROUNDING_EXERCISE[st.session_state.exercise_step]
    st.subheader(f"Grounding Exercise: {step_data['step']}")
    st.markdown(f"### {step_data['text']}")
    
    if st.session_state.exercise_step < len(GROUNDING_EXERCISE) - 1:
        if st.button("Next Step"):
            st.session_state.exercise_step += 1
            st.rerun()
    else:
        if st.button("Finish Exercise"):
            st.session_state.in_exercise = False
            st.session_state.exercise_step = 0
            st.success("Exercise complete! Returning to chat.")
            time.sleep(1)
            st.rerun()

else:
    if 'history' not in st.session_state:
        st.session_state.history = get_chat_history(user_ref)

    for turn in st.session_state.history:
        role = "user" if turn["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(turn["content"])

    if prompt := st.chat_input("How are you feeling today?"):
        with st.chat_message("user"):
            st.markdown(prompt)

        mood, response, updated_history = get_response(prompt, st.session_state.history)
        st.session_state.history = updated_history
        save_chat_history(user_ref, st.session_state.history)
        add_mood_log(user_ref, mood)
        
        with st.chat_message("assistant"):
            st.markdown(response)

        if mood in ['sad', 'anxious']:
            with st.container(border=True):
                st.info("It sounds like you're going through a tough moment. Sometimes a grounding exercise can help.", icon="🧘‍♀️")
                if st.button("Start 5-4-3-2-1 Grounding Exercise"):
                    st.session_state.in_exercise = True
                    st.rerun()
        
        elif mood == 'seeking_community':
            st.success("You're not alone. Connecting with others can be a great source of comfort.", icon="🤝")
        elif mood == 'serious_distress':
            st.warning("It sounds like you are in a lot of pain. Remember, the panic button is available in the sidebar. Please also consider reaching out to a professional.", icon="⚠️")

        if mood != 'neutral':
            st.rerun()
