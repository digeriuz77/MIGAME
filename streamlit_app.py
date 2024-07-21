import streamlit as st
import random
from pathlib import Path
from utils.game_state import GameState
from utils.chat_session import ChatSession
from utils.call_images import create_image, create_image_prompt

st.set_page_config("Motivational Interviewing Journey", layout="wide")

SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(parents=True, exist_ok=True)

ART_STYLES = [
    "Digital painting", "Watercolor", "Oil painting", "Pencil sketch", 
    "Comic book art", "Pixel art", "3D render", "Storybook illustration", 
    "Vector art", "Charcoal drawing", "Pastel drawing", "Collage", 
    "Low poly", "Isometric 3D", "Claymation", "Anime", "Vintage Disney", 
    "Studio Ghibli", "Pop Art", "Art Nouveau"
]

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
    if "art_style" not in st.session_state:
        st.session_state.art_style = "Digital painting"

def get_journey_prompt_view():
    st.title("Start Your Change Journey")
    
    character_name = st.text_input("Enter your character's name:")
    character_type = st.text_input("What avatar would you like to have? (It works best if you pick a creature)")
    
    st.write("Choose an art style for your journey:")
    art_style = st.selectbox("Art style:", ART_STYLES)
    
    st.write("What area of your life would you like to focus on for change?")
    
    areas_of_change = ["Feeling good about my body and mind", "Making friends", "Getting better at stuff", "Stop doing something"]
    selected_area = st.selectbox("Choose an area:", areas_of_change)
    
    specific_goal = st.text_input("What specific goal do you have in mind for this area?")

    if st.button("Begin Journey"):
        st.session_state.game_state.set_character(character_name, character_type)
        st.session_state.game_state.set_focus_area(selected_area)
        st.session_state.game_state.set_specific_goal(specific_goal)
        st.session_state.art_style = art_style
        st.session_state.journey_in_progress = True
        generate_scenario()
        st.rerun()

def generate_scenario():
    game_state = st.session_state.game_state
    chat_session = st.session_state.chat_session

    character_select = f"{game_state.character_name} the {game_state.character_type}"

    prompt = f"""\
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
    chat_session = st.session_state.chat_session
    character_select = f"{game_state.character_name} the {game_state.character_type}"
    art_style = st.session_state.art_style

    st.title(f"{character_select}'s Change Journey: {game_state.focus_area}")
    st.write(f"Current Stage: {game_state.get_current_stage()}")
    st.write(f"Your Goal: {game_state.specific_goal}")

    # Display conversation history and images
    for i in range(0, len(st.session_state.conversation_history), 4):
        # Opening Description or Scenario
        st.write(st.session_state.conversation_history[i][1])

        # Display choices, their images, and outcomes
        for j in range(3):
            if i + j + 1 < len(st.session_state.conversation_history):
                choice = st.session_state.conversation_history[i + j + 1]
                st.write(f"Choice {j + 1}: {choice[1]}")
                
                if 'story_images' in st.session_state and i + j < len(st.session_state.story_images):
                    _, image_b64 = st.session_state.story_images[i + j]
                    st.image(f"data:image/png;base64,{image_b64}")
                
                if i + j + 2 < len(st.session_state.conversation_history):
                    outcome = st.session_state.conversation_history[i + j + 2]
                    if outcome[0] == "Outcome":
                        st.write(outcome[1])

    # Choice selection and Make Choice button
    with st.form(key='choice_form'):
        choices = [choice[1] for choice in st.session_state.current_choices]
        choice = st.radio("What will you do?", choices)
        submit_button = st.form_submit_button(label='Make Choice')

    if submit_button:
        change_scores = [-5, 0, 10]
        choice_index = choices.index(choice)
        change_score = change_scores[choice_index]
        
        game_state.increment_progress(change_score)
        st.session_state.game_state = game_state  # Update the session state

        prompt = f"{character_select} chose: \"{choice}\" in response to the previous scenario. They are in the {game_state.get_current_stage()} stage of change for {game_state.focus_area}, with the specific goal of {game_state.specific_goal}. Generate a brief (50 words max) response describing the outcome of this choice. Then, provide a new scenario and 3 new choices based on this outcome. Format the response as follows: Outcome: [Your outcome here] New Scenario: [Your new scenario here] Choices: 1. [Choice 1] 2. [Choice 2] 3. [Choice 3] Keep the entire response under 250 words."

        response = chat_session.get_ai_response(prompt)

        outcome, new_content = response.split("New Scenario:")
        new_scenario, choices_text = new_content.split("Choices:")
        new_choices = [choice.strip() for choice in choices_text.split("\n") if choice.strip()]

        # Append the chosen choice and its outcome
        st.session_state.conversation_history.append(("Choice", choice))
        st.session_state.conversation_history.append(("Outcome", outcome.replace("Outcome:", "").strip()))
        
        # Generate and append image for the choice
        image_prompt = create_image_prompt(chat_session, f"{character_select} - {choice}", art_style)
        if image_prompt:
            full_prompt = f"{art_style} of {image_prompt}"
            image_b64 = create_image(chat_session, full_prompt)
            if image_b64:
                if 'story_images' not in st.session_state:
                    st.session_state.story_images = []
                st.session_state.story_images.append((full_prompt, image_b64))

        # Append the new scenario
        st.session_state.conversation_history.append(("Scenario", new_scenario.strip()))
        
        # Append the new choices
        st.session_state.current_choices = [("Choice", choice) for choice in new_choices]

        st.rerun()  # Rerun the app to update the display

    # Move progress bar to the bottom
    st.write("---")  # Add a separator
    progress = game_state.progress / 100
    st.progress(value=progress, text=f"Overall Progress: {game_state.progress}%")
    st.write(f"Stage: {game_state.get_current_stage()}")
    st.write(f"Steps taken: {game_state.steps_taken}")

    # Add "Print My Story" button when progress reaches 100%
    if progress >= 1.0:
        if st.button("Print My Story"):
            print_story()
            
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
