import streamlit as st
import random
from pathlib import Path
from utils.game_state import GameState
from utils.chat_session import ChatSession
from utils.call_images import create_image, create_image_prompt
from utils.helpers import add_character_names
from utils.page_helpers import load_session, save_session
from fpdf import FPDF
import base64
from io import BytesIO
from PIL import Image

# Constants
ART_STYLES = [
    "Digital painting", "Watercolor", "Oil painting", "Pencil sketch", 
    "Comic book art", "Pixel art", "3D render", "Storybook illustration", 
    "Vector art", "Charcoal drawing", "Pastel drawing", "Collage", 
    "Low poly", "Isometric 3D", "Claymation", "Anime", "Vintage Disney", 
    "Studio Ghibli", "Pop Art", "Art Nouveau"
]

HERO_JOURNEY_STAGES = [
    "The Ordinary World", "The Call to Adventure", "Refusal of the Call",
    "Meeting the Mentor", "Crossing the Threshold", "Tests, Allies, and Enemies",
    "Approach to the Inmost Cave", "The Ordeal", "Reward (Seizing the Sword)",
    "The Road Back", "Resurrection", "Return with the Elixir"
]

# Streamlit page configuration
st.set_page_config("Hero's Journey", layout="wide")

SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(parents=True, exist_ok=True)

def init_state():
    """Initialize the application state."""
    if "openai_api_key" not in st.secrets:
        st.error("OpenAI API key not found. Please set it in your Streamlit secrets.")
        st.stop()
    
    state_vars = {
        "journey_in_progress": False,
        "session_id": str(random.randint(1000, 9999)),
        "game_state": GameState(),
        "chat_session": ChatSession(),
        "current_scenario": "",
        "conversation_history": [],
        "current_choices": [],
        "art_style": "Digital painting",
        "hero_journey_stage": 0
    }
    
    for key, value in state_vars.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_journey_prompt_view():
    """Display the initial view for starting a hero's journey."""
    st.title("Start Your Hero's Journey")
    
    character_name = st.text_input("Enter your character's name:")
    character_type = st.text_input(
        "What kind of creature is your hero? (e.g., dragon, unicorn, elf)"
    )
    distinguishing_feature = st.text_input(
        "What's a unique feature of your hero? (e.g., glowing eyes, rainbow mane)"
    )
    
    st.write("Choose an art style for your journey:")
    art_style = st.selectbox("Art style:", ART_STYLES)
    
    st.write("What challenge will your hero face?")
    challenge_areas = [
        "Overcoming fear", "Making new friends", 
        "Learning a new skill", "Helping others"
    ]
    selected_challenge = st.selectbox("Choose a challenge:", challenge_areas)
    
    specific_goal = st.text_input(
        "What specific goal does your hero have for this challenge?"
    )

    if st.button("Begin Journey"):
        game_state = st.session_state.game_state
        game_state.set_character(character_name, character_type, distinguishing_feature)
        game_state.set_challenge(selected_challenge)
        game_state.set_specific_goal(specific_goal)
        st.session_state.art_style = art_style
        st.session_state.journey_in_progress = True
        generate_scenario()
        save_session(SESSION_DIR)
        st.rerun()

def generate_scenario():
    """Generate a new scenario for the hero's journey."""
    game_state = st.session_state.game_state
    chat_session = st.session_state.chat_session
    hero_journey_stage = HERO_JOURNEY_STAGES[st.session_state.hero_journey_stage]
    character_select = (f"{game_state.character_name} the {game_state.character_type} "
                        f"with {game_state.distinguishing_feature}")

    prompt = create_scenario_prompt(game_state, hero_journey_stage, character_select)
    response = chat_session.get_ai_response(prompt)
    
    process_scenario_response(response)

def create_scenario_prompt(game_state, hero_journey_stage, character_select):
    """Create the prompt for generating a new scenario."""
    return (f"Generate a scenario for {character_select} who is in the "
            f"{hero_journey_stage} stage of their hero's journey, "
            f"facing the challenge of {game_state.challenge} with the specific "
            f"goal of {game_state.specific_goal}. "
            f"The scenario should present a situation where the hero faces "
            f"a decision related to their journey. "
            f"Provide 3 possible choices for the hero: "
            f"1. A cautious or hesitant choice "
            f"2. A balanced or neutral choice "
            f"3. A brave or bold choice "
            f"Format the response as follows: "
            f"[Your scenario here] "
            f"1. [Choice 1] "
            f"2. [Choice 2] "
            f"3. [Choice 3] "
            f"Keep the entire response under 250 words and maintain a story-like feel.")

def process_scenario_response(response):
    """Process the AI-generated scenario and choices."""
    scenario, choices = response.split("\n1.")
    st.session_state.current_scenario = scenario.strip()
    choices = "1." + choices
    st.session_state.current_choices = [
        choice.strip() for choice in choices.split("\n") if choice.strip()
    ]
    st.session_state.conversation_history.append(
        ("SCENARIO", st.session_state.current_scenario)
    )

def main_view():
    """Display the main view of the hero's journey."""
    game_state = st.session_state.game_state
    character_select = f"{game_state.character_name} the {game_state.character_type}"
    hero_journey_stage = HERO_JOURNEY_STAGES[st.session_state.hero_journey_stage]

    st.title(f"{character_select}'s Hero Journey: {game_state.challenge}")
    st.write(f"Current Stage: {hero_journey_stage}")
    st.write(f"Goal: {game_state.specific_goal}")

    display_conversation_history()
    display_choices()
    display_progress()

def display_conversation_history():
    """Display the conversation history, including scenarios and images."""
    for item_type, content in st.session_state.conversation_history:
        if item_type == "SCENARIO":
            st.write(content)
        elif item_type == "CHOICE":
            st.write(f"- {content}")
        elif item_type == "OUTCOME":
            st.write(content)
        elif item_type == "IMAGE":
            st.image(f"data:image/png;base64,{content}")

def display_choices():
    """Display and process the hero's choices."""
    with st.form(key='choice_form'):
        choice = st.radio("What will our hero do?", st.session_state.current_choices)
        submit_button = st.form_submit_button(label='Choose')

    if submit_button:
        process_user_choice(choice)
        save_session(SESSION_DIR)
        st.rerun()

def process_user_choice(choice):
    """Process the user's choice and generate the next part of the story."""
    game_state = st.session_state.game_state
    chat_session = st.session_state.chat_session
    character_select = (f"{game_state.character_name} the {game_state.character_type} "
                        f"with {game_state.distinguishing_feature}")
    hero_journey_stage = HERO_JOURNEY_STAGES[st.session_state.hero_journey_stage]

    change_scores = [1, 2, 3]
    choice_index = st.session_state.current_choices.index(choice)
    change_score = change_scores[choice_index]
    
    game_state.increment_progress(change_score)

    prompt = create_choice_prompt(game_state, hero_journey_stage, character_select, choice)
    response = chat_session.get_ai_response(prompt)
    process_choice_response(response, choice)

    game_state.advance_stage()

def create_choice_prompt(game_state, hero_journey_stage, character_select, choice):
    """Create the prompt for processing a user's choice."""
    return (f"{character_select} chose: '{choice}' in the {hero_journey_stage} "
            f"stage of their journey, facing the challenge of {game_state.challenge} "
            f"with the goal of {game_state.specific_goal}. "
            f"Describe the outcome of this choice (max 100 words) and provide "
            f"a new scenario with 3 new choices. "
            f"Format the response as follows: "
            f"[Outcome description] "
            f"[New scenario] "
            f"1. [New choice 1] "
            f"2. [New choice 2] "
            f"3. [New choice 3] "
            f"Keep the entire response under 300 words and maintain a story-like feel.")

def process_choice_response(response, choice):
    """Process the AI response to the hero's choice."""
    try:
        # First, try to split by "Outcome:" and "New Scenario:"
        parts = response.split("New Scenario:")
        if len(parts) == 2:
            outcome = parts[0].replace("Outcome:", "").strip()
            new_content = parts[1]
        else:
            # If that fails, just consider everything before the first number as the outcome
            outcome = response.split("1.")[0].strip()
            new_content = response[len(outcome):].strip()

        # Split the new content into scenario and choices
        choices_start = new_content.find("1.")
        if choices_start != -1:
            new_scenario = new_content[:choices_start].strip()
            new_choices = new_content[choices_start:].strip()
        else:
            # If no numbered choices found, consider everything as the new scenario
            new_scenario = new_content
            new_choices = ""

        st.session_state.conversation_history.append(("CHOICE", choice))
        st.session_state.conversation_history.append(("OUTCOME", outcome))
        st.session_state.generate_image_next_turn = True
        st.write("Debug: Setting generate_image_next_turn to True")
        st.session_state.conversation_history.append(("SCENARIO", new_scenario))

        # Process new choices
        choice_list = [c.strip() for c in new_choices.split("\n") if c.strip()]
        if len(choice_list) < 3:
            # If less than 3 choices, generate some generic ones
            choice_list = [
                "Proceed cautiously",
                "Take a balanced approach",
                "Act boldly and decisively"
            ]
        st.session_state.current_choices = choice_list[:3]  # Ensure only 3 choices

    except Exception as e:
        st.error(f"Error processing AI response: {str(e)}")
        st.session_state.conversation_history.append(("ERROR", "Error processing the story. Please try again."))
        st.session_state.current_choices = ["Retry", "Continue cautiously", "End journey"]

def display_progress():
    """Display the hero's journey progress."""
    game_state = st.session_state.game_state
    hero_journey_stage = HERO_JOURNEY_STAGES[st.session_state.hero_journey_stage]

    st.write("---")
    progress = game_state.progress / 100
    st.progress(value=progress, text=f"Journey Progress: {game_state.progress}%")
    st.write(f"Current Stage: {hero_journey_stage}")
    st.write(f"Steps taken: {game_state.steps_taken}")

    if progress >= 0.1:
        if st.button("Print My Story"):
            print_story()

def generate_and_display_image():
    if st.session_state.get('generate_image_next_turn', False):
        st.write("Debug: generate_image_next_turn is True, generating image...")
        game_state = st.session_state.game_state
        chat_session = st.session_state.chat_session
        character_select = (f"{game_state.character_name} the {game_state.character_type} "
                            f"with {game_state.distinguishing_feature}")
        art_style = st.session_state.art_style

        try:
            with st.spinner("Creating an image of your hero's journey..."):
                image_prompt = create_image_prompt(chat_session, character_select, art_style)
                st.write(f"Debug: Generated image prompt: {image_prompt}")
                if image_prompt:
                    full_prompt = f"{art_style} style image of {image_prompt}"
                    image_b64 = create_image(chat_session, full_prompt)
                    if image_b64:
                        st.session_state.conversation_history.append(("IMAGE", image_b64))
                    else:
                        st.warning("Unable to create an image for this part of the journey.")
                else:
                    st.warning("Unable to generate an image description.")
        except Exception as e:
            st.error(f"An error occurred while creating the image: {str(e)}")
        
        st.session_state.generate_image_next_turn = False
    """Generate and display an image for the current part of the journey."""
    if st.session_state.get('generate_image_next_turn', False):
        game_state = st.session_state.game_state
        chat_session = st.session_state.chat_session
        character_select = (f"{game_state.character_name} the {game_state.character_type} "
                            f"with {game_state.distinguishing_feature}")
        art_style = st.session_state.art_style

        try:
            with st.spinner("Creating an image of your hero's journey..."):
                image_prompt = create_image_prompt(chat_session, character_select, art_style)
                if image_prompt:
                    full_prompt = f"{art_style} style image of {image_prompt}"
                    image_b64 = create_image(chat_session, full_prompt)
                    if image_b64:
                        st.session_state.conversation_history.append(("IMAGE", image_b64))
                    else:
                        st.warning("Unable to create an image for this part of the journey.")
                else:
                    st.warning("Unable to generate an image description.")
        except Exception as e:
            st.error(f"An error occurred while creating the image: {str(e)}")
        
        st.session_state.generate_image_next_turn = False

def print_story():
    """Generate a PDF of the hero's journey story."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"{st.session_state.game_state.character_name}'s Hero Journey", 
             ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)

    for item_type, content in st.session_state.conversation_history:
        if item_type == "SCENARIO":
            pdf.multi_cell(0, 10, txt=content)
            pdf.ln(5)
        elif item_type == "CHOICE":
            pdf.multi_cell(0, 10, txt=f"Our hero chose to {content}")
            pdf.ln(5)
        elif item_type == "OUTCOME":
            pdf.multi_cell(0, 10, txt=content)
            pdf.ln(5)
        elif item_type == "IMAGE":
            try:
                image_data = base64.b64decode(content)
                image = Image.open(BytesIO(image_data))
                image_path = f"temp_image_{pdf.page_no()}.png"
                image.save(image_path)
                pdf.image(image_path, x=10, w=190)
                pdf.ln(5)
            except Exception as e:
                pdf.multi_cell(0, 10, txt="[An image of the hero's journey would be here]")

    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    st.download_button(
        label="Download Your Hero's Journey Story",
        data=pdf_output,
        file_name=f"{st.session_state.game_state.character_name}_hero_journey.pdf",
        mime="application/pdf"
    )

def main():
    """Main function to run the Streamlit app."""
    load_session(SESSION_DIR)
    init_state()

    if not st.session_state.journey_in_progress:
        get_journey_prompt_view()
    else:
        main_view()
        generate_and_display_image()

    if st.button("Start a New Journey"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_state()
        save_session(SESSION_DIR)
        st.rerun()

if __name__ == "__main__":
    main()
