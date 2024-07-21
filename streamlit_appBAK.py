import streamlit as st
import random
from pathlib import Path
from utils.game_state import GameState
from utils.chat_session import ChatSession

st.set_page_config("Motivational Interviewing Journey", layout="wide")

SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(parents=True, exist_ok=True)

def init_state():
    if "openai_api_key" not in st.secrets:
        st.error("OpenAI API key not found. Please set it in your Streamlit secrets.")
        st.stop()
    
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
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "current_choices" not in st.session_state:
        st.session_state.current_choices = []

def get_journey_prompt_view():
    st.title("Start Your Change Journey")
    st.write("What area of your life would you like to focus on for change?")
    
    areas_of_change = ["Making Friends", "Relationships", "Jobs and Career", "Doing something different", "Trying to stop doing something"]
    selected_area = st.selectbox("Choose an area:", areas_of_change)
    
    specific_goal = st.text_input("What specific goal do you have in mind for this area?")

    if st.button("Begin Journey"):
        st.session_state.game_state.set_focus_area(selected_area)
        st.session_state.game_state.set_specific_goal(specific_goal)
        st.session_state.journey_in_progress = True
        generate_scenario()
        st.rerun()

def generate_scenario():
    game_state = st.session_state.game_state
    chat_session = st.session_state.chat_session

    prompt = f"""
    Generate a friendly scenario for young adults in the {game_state.get_current_stage()} stage of change, 
    focusing on {game_state.focus_area} with the specific goal of {game_state.specific_goal}. 
    The scenario should present a situation where a creature is facing a decision related to the change process. It should be easy to read with simple language. Avoid unethical situations.
    Also, provide 3 possible choices for the user, tailored to their current stage of change which will encourage either: taking responsibility, asking for help, or an aspect of avoidance - (like procrastination, unnecessary resting etc)
    Format the response as follows:
    Scenario: [Your scenario here]
    Choices:
    1. [First choice]
    2. [Second choice]
    3. [Third choice]
    Keep the entire response under 150 words.
    """
    response = chat_session.get_ai_response(prompt)
    
    scenario, choices = response.split("Choices:")
    st.session_state.current_scenario = scenario.strip()
    st.session_state.current_choices = [choice.strip() for choice in choices.split("\n") if choice.strip()]
    st.session_state.conversation_history.append(("AI", st.session_state.current_scenario))

def main_view():
    if 'game_state' not in st.session_state:
        st.error("Game state not initialized. Please reset your journey.")
        return

    game_state = st.session_state.game_state

    st.title(f"Your Change Journey: {game_state.focus_area}")
    st.write(f"Current Stage: {game_state.get_current_stage()}")
    
    try:
        st.write(f"Your Goal: {game_state.specific_goal}")
    except AttributeError:
        st.error("Specific goal not set. Please reset your journey and set a goal.")
        return

    for speaker, message in st.session_state.conversation_history:
        if speaker == "AI":
            st.write(f"AI: {message}")
        else:
            st.write(f"You: {message}")

    if 'current_choices' not in st.session_state or not st.session_state.current_choices:
        st.warning("No choices available. Generating new scenario...")
        generate_scenario()
        st.rerun()

    choice = st.radio("What will you do?", st.session_state.current_choices)

    if st.button("Make Choice"):
        result = game_state.process_choice(choice)
        st.session_state.conversation_history.append(("You", choice))
        
        chat_session = st.session_state.chat_session
        prompt = f"""
        The user chose: "{choice}" in response to the previous scenario. 
        They are in the {game_state.get_current_stage()} stage of change for {game_state.focus_area}, 
        with the specific goal of {game_state.specific_goal}.
        Generate a brief and simple (50 words max) response describing the outcome of this choice.
        Remembering this choice, then provide a new scenario and 3 new choices based on this outcome. Remember each choice should advocate taking responsibility, asking for help or avoidance in some respect.
        Format the response as follows:
        Outcome: [Your outcome here]
        New Scenario: [Your new scenario here]
        Choices:
        1. [First choice]
        2. [Second choice]
        3. [Third choice]
        Keep the entire response under 200 words.
        """
        response = chat_session.get_ai_response(prompt)
        
        try:
            outcome, new_scenario = response.split("New Scenario:")
            new_scenario, new_choices = new_scenario.split("Choices:")
        except ValueError:
            st.error("Error parsing AI response. Generating new scenario...")
            generate_scenario()
            st.rerun()
        
        st.session_state.conversation_history.append(("AI", outcome.strip()))
        st.session_state.current_scenario = new_scenario.strip()
        st.session_state.current_choices = [choice.strip() for choice in new_choices.split("\n") if choice.strip()]
        st.session_state.conversation_history.append(("AI", st.session_state.current_scenario))
        
        game_state.increment_progress()
        
        st.rerun()

    st.sidebar.title("Your Progress")
    st.sidebar.write(f"Stage: {game_state.get_current_stage()}")
    st.sidebar.write(f"Steps taken: {game_state.steps_taken}")
    st.sidebar.progress(game_state.progress / 100, text=f"Overall Progress: {game_state.progress}%")

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
        st.rerun()

if __name__ == "__main__":
    main()

    
