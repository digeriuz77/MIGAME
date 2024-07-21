import streamlit as st
import random
from pathlib import Path
from utils.game_state import GameState
from utils.chat_session import ChatSession
from utils.call_images import create_image, create_image_prompt

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
    
    character_name = st.text_input("Enter your character's name:")
    character_type = st.selectbox("Choose your character type:", ["Rabbit", "Bear", "Eagle", "Salamander", "Octopus"])
    
    st.write("What area of your life would you like to focus on for change?")
    
    areas_of_change = ["Feeling good about my body and mind", "Making friends", "Getting better at stuff", "Stop doing something"]
    selected_area = st.selectbox("Choose an area:", areas_of_change)
    
    specific_goal = st.text_input("What specific goal do you have in mind for this area?")

    if st.button("Begin Journey"):
        st.session_state.game_state.set_character(character_name, character_type)
        st.session_state.game_state.set_focus_area(selected_area)
        st.session_state.game_state.set_specific_goal(specific_goal)
        st.session_state.journey_in_progress = True
        generate_scenario()
        st.rerun()

def generate_scenario():
    game_state = st.session_state.game_state
    chat_session = st.session_state.chat_session

    character_select = f"{game_state.character_name} the {game_state.character_type}"

    prompt = f"""
    Generate a young adult scenario for {character_select} who is in the {game_state.get_current_stage()} stage of change, 
    focusing on {game_state.focus_area} with the specific goal of {game_state.specific_goal}. 
    The scenario should present a situation where the character is facing a decision related to their change process which will be connected to being {character_select}.
    Also, provide 3 possible choices for the user, tailored to their current stage of change.
    Each choice should use language from change talk, representing different levels of readiness to change:
    1. A choice representing sustain talk (negative change score)
    2. A neutral choice (no change score)
    3. A choice representing strong change talk (positive change score)
    Format the response as follows:
    Scenario: [Your scenario here]
    Choices:
    1. [Sustain talk choice] 
    2. [Neutral choice]
    3. [Strong change talk choice]
    Keep the entire response under 200 words.
    """
    response = chat_session.get_ai_response(prompt)
    
    scenario, choices = response.split("Choices:")
    st.session_state.current_scenario = scenario.strip()
    st.session_state.current_choices = [choice.strip().split(') ')[0] + ')' for choice in choices.split("\n") if choice.strip()]
    st.session_state.conversation_history.append(("AI", st.session_state.current_scenario))

def main_view():
    game_state = st.session_state.game_state
    character_select = f"{game_state.character_name} the {game_state.character_type}"

    st.title(f"{character_select}'s Change Journey: {game_state.focus_area}")
    st.write(f"Current Stage: {game_state.get_current_stage()}")
    st.write(f"Your Goal: {game_state.specific_goal}")

    for speaker, message in st.session_state.conversation_history:
        if speaker == "AI":
            st.write(f"AI: {message}")
        else:
            st.write(f"You: {message}")

    choice = st.radio("What will you do?", st.session_state.current_choices)

    if st.button("Make Choice"):
        change_scores = [-5, 0, 10]
        choice_index = st.session_state.current_choices.index(choice)
        change_score = change_scores[choice_index]
        
        game_state.increment_progress(change_score)
        st.session_state.conversation_history.append(("You", choice))
        
        chat_session = st.session_state.chat_session
        prompt = f"""
        {character_select} chose: "{choice}" in response to the previous scenario. 
        They are in the {game_state.get_current_stage()} stage of change for {game_state.focus_area}, 
        with the specific goal of {game_state.specific_goal}.
        Generate a brief (50 words max) response describing the outcome of this choice.
        Then, provide a new scenario and 3 new choices based on this outcome, following the same format as before.
        Format the response as follows:
        Outcome: [Your outcome here]
        New Scenario: [Your new scenario here]
        Choices:
        1. [Sustain talk choice] 
        2. [Neutral choice] 
        3. [Strong change talk choice]
        Keep the entire response under 250 words.
        """
        response = chat_session.get_ai_response(prompt)
        
        outcome, new_scenario = response.split("New Scenario:")
        new_scenario, new_choices = new_scenario.split("Choices:")
        
        st.session_state.conversation_history.append(("AI", outcome.strip()))
        st.session_state.current_scenario = new_scenario.strip()
        st.session_state.current_choices = [choice.strip().split(') ')[0] + ')' for choice in new_choices.split("\n") if choice.strip()]
        st.session_state.conversation_history.append(("AI", st.session_state.current_scenario))
        
        # Generate and display image
        image_prompt = create_image_prompt(chat_session, character_select)
        if image_prompt:
            image_data = create_image(image_prompt)
            if image_data:
                image_b64 = image_data["data"][0]["b64_json"]
                st.image(f"data:image/png;base64,{image_b64}")
        
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
