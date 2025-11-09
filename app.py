import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import pandas as pd
import random
import pyttsx3
import speech_recognition as sr
import threading

from datetime import datetime
import datetime as dt
from google_calendar import create_event

# MODEL SETUP 
st.title("Vireum AI Assistant Prototype")
st.write("Talk or type to describe your AI project idea and get an estimate!")

@st.cache_resource
def load_model():
    model_name = "distilgpt2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)
    chatbot = pipeline("text-generation", model=model, tokenizer=tokenizer)
    return chatbot

chatbot = load_model()

# DATA STORAGE 
DATA_FILE = "data/users.csv"
try:
    users = pd.read_csv(DATA_FILE)
except:
    #users = pd.DataFrame(columns=["name", "email", "project", "estimate", "schedule"])
    users = pd.DataFrame(columns=[
        "timestamp", "name", "email", "project", "voice_input",
        "estimate", "schedule"
    ])


# SPEECH FUNCTIONS 
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def listen():
    """Capture voice input and return recognized text."""
    with sr.Microphone() as source:
        st.info("Listening... please speak clearly")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
    try:
        text = recognizer.recognize_google(audio)
        st.success(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        st.warning("Sorry, I could not understand that.")
        return ""
    except sr.RequestError:
        st.error("Speech recognition service unavailable.")
        return ""

def speak(text):
    """Speak text in a background thread to avoid Streamlit loop errors."""
    def _speak():
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"Speech error: {e}")
    threading.Thread(target=_speak).start()

# UI INPUT 
name = st.text_input("Your Name")
email = st.text_input("Your Email")
project = st.text_area("Describe your AI project idea")
#voice_input = ""

# Initialize session variable for voice_input
if "voice_input" not in st.session_state:
    st.session_state.voice_input = ""

if st.button("Use Voice Input"):
    voice_text = listen()
    if voice_text:
        st.session_state.voice_input = voice_text
        project += " " + voice_text
        st.text_area("Your updated project idea", value=project, height=100)

if st.button("Get Estimate"):
    voice_input = st.session_state.voice_input  # retrieve it here 
    if name and email and project:
        words = len(project.split())
        cost = round(500 + (words * random.uniform(2, 5)), 2)
        weeks = random.randint(2, 8)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        estimate_text = f"Estimated cost: €{cost} and duration: {weeks} weeks."
        st.success(estimate_text)

        # Save data with timestamp and voice input
        new_entry = {
            "timestamp": timestamp, 
            "name": name, 
            "email": email, 
            "project": project,
            "voice_input" : voice_input,
            "estimate": cost, 
            "schedule": f"{weeks} weeks"
        }
        users = pd.concat([users, pd.DataFrame([new_entry])])
        users.to_csv(DATA_FILE, index=False)

        # AI suggestion
        suggestion = chatbot(
            f"Suggest a simple AI solution for: {project}",
            max_length=50, 
            do_sample=True
        )[0]['generated_text']
        st.info("Suggested AI idea: " + suggestion)

        speak(f"The estimated cost is {cost} euros and duration is {weeks} weeks.")
        st.success("Data saved successfully!")

        # Clear the voice input after saving
        st.session_state.voice_input = ""
    else:
        st.warning("Please fill all fields before getting an estimate.")

# Integrate Booking in Streamlit'
st.subheader("Schedule a Meeting with Vireum Expert")

meeting_date = st.date_input("Select a date", min_value=dt.date.today())
meeting_time = st.time_input("Select a time", value=dt.time(hour=10, minute=0))

if st.button("Book Meeting"):
    start_datetime = dt.datetime.combine(meeting_date, meeting_time)
    end_datetime = start_datetime + dt.timedelta(hours=1)  # 1-hour meeting
    summary = f"Meeting with {name} about AI project"
    description = project

    try:
        meeting_link = create_event(summary, start_datetime.isoformat(), end_datetime.isoformat(), description)
        st.success(f"Meeting booked! View it here: [Google Calendar]({meeting_link})")
    except Exception as e:
        st.error(f"Failed to book meeting: {e}")


# VIEW SAVED ENTRIES 
st.markdown("---")
st.subheader("View Saved Projects")

if st.button("Show Saved Entries"):
    try:
        users = pd.read_csv(DATA_FILE)
        if not users.empty:
            st.dataframe(users, use_container_width=True)
            st.success(f"Showing {len(users)} saved entries.")
        else:
            st.info("No saved entries found yet.")
    except FileNotFoundError:
        st.warning("No saved data file found yet.")

