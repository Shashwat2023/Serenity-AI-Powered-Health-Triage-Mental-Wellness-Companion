⚕️ Serenity: AI-Powered Health Triage & Mental Wellness Companion
Project Overview

Serenity is a multi-faceted application designed to provide crucial, preliminary health and mental wellness guidance, serving as an essential first point of contact for users, particularly in areas with limited access to immediate medical professionals.

The application acts as a triage bot, taking user-inputted symptoms (both physical and emotional) and generating:

    Preliminary Insights: Possible health conditions (physical) or emotional states (mental health).

    Immediate Recommendations: Clear guidance for triage: Home Remedy / Self-Care vs. Doctor Visit vs. Emergency Contact.

    Wellness Tools: Access to guided exercises, mood tracking, and direct links to live counselors and community support.

This project uses a Python backend (Flask) for the AI logic and database communication, and a lightweight HTML/CSS/JS frontend for accessibility.
✨ Features

    Symptom Triage (AI Chatbot): Uses the AI model to analyze symptoms and provide non-diagnostic conditions and next-step recommendations (triage).

    Real-time Mood Analysis: Detects the user's emotional state from chat inputs and logs it to Firestore.

    Grounding Exercises: Offers guided breathing and 5-4-3-2-1 exercises for users experiencing anxiety or distress (guiding ex.html).

    Counselor Integration: A mock interface for finding and booking live mental health counselors (talktocouncler.html).

    Data Persistence: Utilizes Google Firestore to store chat history and mood logs, maintaining session context.

    Responsive Web Interface: Accessible on both desktop and mobile devices.

🛠️ Technology Stack

Component
	

Technology
	

Role

Backend
	

Python (Flask)
	

RESTful API server, handling chat requests and database interactions.

AI/ML
	

Hugging Face Transformers / Phi-3-mini
	

Local LLM inference for text generation, mood detection, and triage logic (bot.py).

Database
	

Google Firestore
	

Persistent storage for user profiles, chat history, and mood logs.

Frontend
	

HTML, JavaScript, Tailwind CSS
	

Single-page web application for the user interface and chat client.
⚙️ Setup and Installation

Follow these steps to get the Serenity application running on your local machine.
Prerequisites

    Python: Python 3.8+ installed.

    Git: Installed to clone the repository.

    Google Cloud Project: A project with Firestore enabled.

Step 1: Clone the Repository

git clone <your-repository-url>
cd serenity-triage-bot

Step 2: Set up the Python Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies.

# Create a virtual environment (Linux/macOS)
python3 -m venv venv 
source venv/bin/activate

# Create a virtual environment (Windows)
python -m venv venv
.\venv\Scripts\activate

# Install required Python packages
pip install -r requirements.txt
# NOTE: The dependency file is not provided, so you need to manually install them:
# pip install flask flask-cors google-cloud-firestore firebase-admin transformers torch

Step 3: Configure Firestore Credentials

Your application needs a service account key to connect to Firestore.

    Generate Service Account Key: In your Google Cloud Project, navigate to IAM & Admin > Service Accounts. Create a new service account with the Cloud Datastore User or Firebase Admin SDK role.

    Download JSON Key: Generate a new key and download the JSON file.

    Place Key File: Create a directory named config in the project root and place the downloaded JSON file inside it. Rename the file to firestore-credentials.json.

serenity-triage-bot/
├── config/
│   └── firestore-credentials.json  <-- PLACE YOUR KEY HERE
├── api.py
├── bot.py
├── firestore_db.py
├── mainfile.html
...

Step 4: Run the Backend Server (API)

The api.py file exposes the /chat endpoint which the frontend calls.

Important Note on LLM: The bot.py file is configured to load the microsoft/Phi-3-mini-4k-instruct model using Hugging Face Transformers and 4-bit quantization. This requires a machine with a powerful GPU (like an NVIDIA card with CUDA) and sufficient VRAM. If you encounter memory issues, you may need to modify bot.py to use a cloud-based API like Google's Gemini API instead (which is recommended for general deployment).

# Ensure your virtual environment is active
python api.py

The server will start, typically running on http://127.0.0.1:5000/.
Step 5: Run the Frontend (Web App)

Since the frontend consists of static HTML files, you only need to open mainfile.html in your web browser.

    Locate the file mainfile.html.

    Right-click on it and choose "Open with" > [Your preferred web browser].

The frontend will automatically attempt to connect to the backend running on localhost:5000.
🚀 Usage

    Start the Chat: On the main screen (mainfile.html), interact with the AI Chatbot.

    Input Symptoms: Type your symptoms or feelings, e.g., "I have a headache and a slight fever" or "I feel very overwhelmed and sad today."

    Receive Triage: The bot will respond with possible conditions/moods and a clear recommendation (Self-Care, Doctor, or Emergency).

    Explore Wellness: Use the navigation to access:

        Guided Exercises: For immediate stress or anxiety relief (guiding ex.html).

        Live Counselors: To browse and book professional support (talktocouncler.html).

📁 Project File Structure

File
	

Description

api.py
	

The main Flask application entry point. Defines the /chat endpoint and handles request routing, bot interaction, and data persistence.

bot.py
	

Contains the core AI logic, including loading the LLM (Phi-3-mini) and the get_response function for generating triage responses and detecting mood.

firestore_db.py
	

Utility functions for initializing Firestore and performing all CRUD operations (get/create user, get/save history, add mood log).

mainfile.html
	

The main chat interface and the hub for the entire application, serving as the user's primary point of interaction.

guiding ex.html
	

A separate page dedicated to guided mental health exercises (e.g., breathing, grounding).

talktocouncler.html
	

A mock-up page for viewing and scheduling sessions with live professional counselors.

app.py
	

(Likely an alternative Streamlit application, not used by api.py). It shows how the same Python logic can be used in a different framework.

config/
	

Directory for secure configuration files (e.g., firestore-credentials.json).

os
	

(This file appears to be a PostScript document and is likely irrelevant to the application's core logic. It can be ignored or deleted.)
Only use VS code to run the Program
