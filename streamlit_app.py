import streamlit as st
import random
from pathlib import Path
from utils.game_state import GameState
from utils.chat_session import ChatSession

st.set_page_config("Motivational Interviewing Journey", layout="wide")

SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(parents=True, exist_ok=True)

def init_state():
    if "journey_in_progress" not in st.session_state:
        st.session_state.journey_in_progress = False
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(random.randint(1000, 9999))
    if "game_state" not in st.session_state:
        st.session_state.game_state = GameState()
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = ChatSession()
    if "current_scenario" not in st.session_state:
        st.session_state.current_scenario = ""

def get_journey_prompt_view():
    st.title("Start Your Change Journey")
    st.write("What area of your life would you like to focus on for change?")
    
    areas_of_change = ["Health", "Relationships", "Career", "Personal Growth", "Habits"]
    selected_area = st.selectbox("Choose an area:", areas_of_change)

    if st.button("Begin Journey"):
        st.session_state.game_state.set_focus_area(selected_area)
        st.session_state.journey_in_progress = True
        generate_scenario()

def generate_scenario():
    game_state = st.session_state.game_state
    chat_session = st.session_state.chat_session

    prompt = f"Generate a scenario for someone in the {game_state.get_current_stage()} stage of change, focusing on {game_state.focus_area}."
    response = chat_session.get_ai_response(prompt)
    
    st.session_state.current_scenario = response

def main_view():
    game_state = st.session_state.game_state

    st.title(f"Your Change Journey: {game_state.focus_area}")
    st.write(f"Current Stage: {game_state.get_current_stage()}")

    st.write(st.session_state.current_scenario)

    choices = game_state.get_current_choices()
    choice = st.radio("What will you do?", choices)

    if st.button("Make Choice"):
        result = game_state.process_choice(choice)
        st.session_state.current_scenario = result
        generate_scenario()  # Generate a new scenario after each choice

    st.sidebar.title("Your Progress")
    for resource, value in game_state.resources.items():
        st.sidebar.progress(value / 100, text=resource)

def main():
    init_state()

    if not st.session_state.journey_in_progress:
        get_journey_prompt_view()
    else:
        main_view()

    if st.button("Reset Journey"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_state()

if __name__ == "__main__":
    main()
