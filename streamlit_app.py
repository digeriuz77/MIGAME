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

    # Generate and add image if flag is set
    if st.session_state.get('generate_image_next_turn', False):
        try:
            with st.spinner("Generating image..."):
                image_prompt = create_image_prompt(chat_session, character_select, art_style)
                if image_prompt:
                    full_prompt = f"{art_style} of {image_prompt}"
                    image_b64 = create_image(chat_session, full_prompt)
                    if image_b64:
                        st.session_state.conversation_history.append(("IMAGE", image_b64, False))
                    else:
                        st.warning("Unable to generate image for this scenario.")
                else:
                    st.warning("Unable to generate image prompt.")
        except Exception as e:
            st.error(f"An error occurred while generating the image: {str(e)}")
        
        # Reset the flag
        st.session_state.generate_image_next_turn = False

    # Display conversation history and images
    for item in st.session_state.conversation_history:
        if isinstance(item, tuple) and len(item) == 3:
            item_type, content, show_label = item
            if item_type == "SCENARIO":
                st.write(content)
            elif item_type == "CHOICE":
                st.write(f"Choice: {content}" if show_label else content)
            elif item_type == "OUTCOME":
                st.write(f"Outcome: {content}" if show_label else content)
            elif item_type == "IMAGE":
                st.image(f"data:image/png;base64,{content}")
        else:
            st.write(item)  # Fallback for any items that don't match the expected format

    # Choice selection and Make Choice button
    with st.form(key='choice_form'):
        choices = [choice.split(': ', 1)[-1].strip() for choice in st.session_state.current_choices]
        choice = st.radio("What will you do?", choices)
        submit_button = st.form_submit_button(label='Make Choice')

    if submit_button:
        change_scores = [-5, 0, 10]
        choice_index = choices.index(choice)
        change_score = change_scores[choice_index]
        
        game_state.increment_progress(change_score)
        st.session_state.game_state = game_state  # Update the session state

        prompt = f"{character_select} chose: \"{choice}\" in response to the previous scenario. They are in the {game_state.get_current_stage()} stage of change for {game_state.focus_area}, with the specific goal of {game_state.specific_goal}. Generate a brief (50 words max) response describing the outcome of this choice. Then, provide a new scenario and 3 new choices based on this outcome, following the same format as before. Format the response as follows: Outcome: [Your outcome here] New Scenario: [Your new scenario here] Choices: 1. 2. 3. Keep the entire response under 250 words."

        response = chat_session.get_ai_response(prompt)

        outcome, new_scenario = response.split("New Scenario:")
        new_scenario, new_choices = new_scenario.split("Choices:")

        # Append choice and outcome to conversation history
        st.session_state.conversation_history.append(("CHOICE", choice, False))
        st.session_state.conversation_history.append(("OUTCOME", outcome.strip(), False))

        # Set flag to generate image on next turn
        st.session_state.generate_image_next_turn = True

        # Append new scenario
        st.session_state.conversation_history.append(("SCENARIO", new_scenario.strip(), False))

        # Update current choices
        st.session_state.current_choices = [choice.strip() for choice in new_choices.split("\n") if choice.strip()]

        st.rerun()  # Rerun the app to update the display

    # Move progress bar to the bottom
    st.write("---")  # Add a separator
    progress = game_state.progress / 100
    st.progress(value=progress, text=f"Overall Progress: {game_state.progress}%")
    st.write(f"Stage: {game_state.get_current_stage()}")
    st.write(f"Steps taken: {game_state.steps_taken}")

    # Add "Print My Story" button when progress reaches 10%
    if progress >= 0.1:
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
