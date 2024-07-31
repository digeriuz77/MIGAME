import streamlit as st
import random
from pathlib import Path
from utils.game_state import GameState
from utils.chat_session import ChatSession
from utils.call_images import create_image, create_image_prompt
from fpdf import FPDF
import base64
from io import BytesIO
from PIL import Image

st.set_page_config("Heroes' journey", layout="wide")

SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(parents=True, exist_ok=True)

ART_STYLES = [
    "Digital painting", "Watercolor", "Oil painting", "Pencil sketch", 
    "Comic book art", "Pixel art", "3D render", "Storybook illustration", 
    "Vector art", "Charcoal drawing", "Pastel drawing", "Collage", 
    "Low poly", "Isometric 3D", "Claymation", "Anime", "Vintage Disney", 
    "Studio Ghibli", "Pop Art", "Art Nouveau"
]

HERO_JOURNEY_STAGES = [
    "The Ordinary World",
    "The Call to Adventure",
    "Refusal of the Call",
    "Meeting the Mentor",
    "Crossing the Threshold",
    "Tests, Allies, and Enemies",
    "Approach to the Inmost Cave",
    "The Ordeal",
    "Reward (Seizing the Sword)",
    "The Road Back",
    "Resurrection",
    "Return with the Elixir"
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
    if "hero_journey_stage" not in st.session_state:
        st.session_state.hero_journey_stage = 0

def get_journey_prompt_view():
    st.title("Start Your Hero's Journey")
    
    character_name = st.text_input("Enter your character's name:")
    character_type = st.text_input("What avatar would you like to have? (It works best if you pick a creature)")
    
    st.write("Choose an art style for your journey:")
    art_style = st.selectbox("Art style:", ART_STYLES)
    
    st.write("What area of your character's life would you like to focus on to change? (to make them succeed!)")
    
    areas_of_change = ["Feeling good about body and mind", "Making friends", "Getting better at stuff", "Stop doing something"]
    selected_area = st.selectbox("Choose an area:", areas_of_change)
    
    specific_goal = st.text_input("What specific goal do you have in mind for this area?")

    if st.button("Begin Journey"):
        st.session_state.game_state.set_character(character_name, character_type)
        st.session_state.game_state.set_focus_area(selected_area)
        st.session_state.game_state.set_specific_goal(specific_goal)
        st.session_state.art_style = art_style
        st.session_state.journey_in_progress = True
        st.session_state.hero_journey_stage = 0  # Reset hero journey stage
        generate_scenario()
        st.rerun()

def generate_scenario():
    game_state = st.session_state.game_state
    chat_session = st.session_state.chat_session
    hero_journey_stage = HERO_JOURNEY_STAGES[st.session_state.hero_journey_stage]

    character_select = f"{game_state.character_name} the {game_state.character_type}"

    context = "\n".join([f"{item[0]}: {item[1]}" for item in st.session_state.conversation_history[-5:]])

    prompt = f"""
    Previous context:
    {context}

    Generate a young adult scenario for {character_select} who is in the {game_state.get_current_stage()} stage of change, 
    focusing on {game_state.focus_area} with the specific goal of {game_state.specific_goal}. 
    The scenario should align with the hero's journey stage: {hero_journey_stage}.
    Present a situation where the character faces a decision related to their change process and hero's journey.
    
    Also, provide 3 possible choices for the user, each representing a different approach to the hero's journey:
    1. A choice representing hesitation or retreat (but not complete inaction)
    2. A choice representing a cautious step forward
    3. A choice representing a bold, heroic action

    Each choice should give the hero a chance to change and progress in their journey.
    
    Format the response as follows:
    Scenario: [Your scenario here]
    Choices:
    1. [Choice 1]
    2. [Choice 2]
    3. [Choice 3]
    
    Keep the entire response under 300 words.
    """
    response = chat_session.get_ai_response(prompt)
    
    try:
        scenario, choices = response.split("Choices:")
        st.session_state.current_scenario = scenario.strip()
        choices = [choice.strip() for choice in choices.split("\n") if choice.strip()]
        if len(choices) != 3:
            raise ValueError("Expected 3 choices, but got a different number.")
        
        # Shuffle the choices
        random.shuffle(choices)
        st.session_state.current_choices = choices
        
        st.session_state.conversation_history.append(("SCENARIO", st.session_state.current_scenario))
    except Exception as e:
        st.error(f"An error occurred while processing the AI response: {str(e)}")
        st.session_state.current_scenario = "Error generating scenario. Please try again."
        st.session_state.current_choices = ["Retry", "Continue with caution", "End journey"]
        st.session_state.conversation_history.append(("ERROR", "Error in scenario generation"))

def main_view():
    game_state = st.session_state.game_state
    chat_session = st.session_state.chat_session
    character_select = f"{game_state.character_name} the {game_state.character_type}"
    art_style = st.session_state.art_style
    hero_journey_stage = HERO_JOURNEY_STAGES[st.session_state.hero_journey_stage]

    st.title(f"{character_select}'s Hero Journey: {game_state.focus_area}")
    st.write(f"Current Stage of Change: {game_state.get_current_stage()}")
    st.write(f"Hero's Journey Stage: {hero_journey_stage}")
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
                        st.session_state.conversation_history.append(("IMAGE", image_b64))
                    else:
                        st.warning("Unable to generate image for this scenario.")
                else:
                    st.warning("Unable to generate image prompt.")
        except Exception as e:
            st.error(f"An error occurred while generating the image: {str(e)}")
        
        # Reset the flag
        st.session_state.generate_image_next_turn = False

    # Display conversation history and images
    for item_type, content in st.session_state.conversation_history:
        if item_type == "SCENARIO":
            st.write(content)
        elif item_type == "CHOICE":
            st.write(f"- {content}")
        elif item_type == "OUTCOME":
            st.write(f"Outcome: {content}")
        elif item_type == "IMAGE":
            st.image(f"data:image/png;base64,{content}")
        elif item_type == "ERROR":
            st.error(content)
            
# Check if current_choices exists in session_state
    if "current_choices" not in st.session_state or not st.session_state.current_choices:
        # If not, generate an initial scenario
        generate_scenario()
        st.rerun()
            
    # Choice selection and Make Choice button
    with st.form(key='choice_form'):
        choices = st.session_state.current_choices
        choice = st.radio("What will you do?", choices)
        submit_button = st.form_submit_button(label='Make Choice')

if submit_button:
            change_scores = [1, 2, 3]  # Adjusted to fit the 12-part structure
            choice_index = choices.index(choice)
            change_score = change_scores[choice_index]
            
            game_state.increment_progress(change_score)
            st.session_state.game_state = game_state  # Update the session state

            # Progress the hero's journey stage
            st.session_state.hero_journey_stage = min(st.session_state.hero_journey_stage + 1, len(HERO_JOURNEY_STAGES) - 1)

            context = "\n".join([f"{item[0]}: {item[1]}" for item in st.session_state.conversation_history[-5:]])
            hero_journey_stage = HERO_JOURNEY_STAGES[st.session_state.hero_journey_stage]

            prompt = f"""
            Previous context:
            {context}

            {character_select} chose: "{choice}" in response to the previous scenario. 
            They are in the {game_state.get_current_stage()} stage of change for {game_state.focus_area}, 
            with the specific goal of {game_state.specific_goal}. 
            The current hero's journey stage is: {hero_journey_stage}.

            Generate a brief (110 words max) response describing the outcome of this choice, 
            their feelings about it, and what the character learned or how they grew.

            Then, provide a new scenario and 3 new choices based on this outcome, following the same format as before.
            Ensure the new scenario and choices align with the current hero's journey stage and the character's goal.

            Format the response as follows:
            Outcome: [Your outcome here]
            New Scenario: [Your new scenario here]
            Choices:
            1. [Choice representing hesitation or retreat]
            2. [Choice representing a cautious step forward]
            3. [Choice representing a bold, heroic action]

            Keep the entire response under 350 words.
            """

            try:
                response = chat_session.get_ai_response(prompt)

                outcome, new_content = response.split("New Scenario:")
                new_scenario, new_choices = new_content.split("Choices:")

                # Append choice and outcome to conversation history
                st.session_state.conversation_history.append(("CHOICE", choice))
                st.session_state.conversation_history.append(("OUTCOME", outcome.strip()))

                # Set flag to generate image on next turn
                st.session_state.generate_image_next_turn = True

                # Append new scenario
                st.session_state.conversation_history.append(("SCENARIO", new_scenario.strip()))

                # Update current choices
                new_choices_list = [choice.strip() for choice in new_choices.split("\n") if choice.strip()]
                if len(new_choices_list) != 3:
                    raise ValueError("Expected 3 choices, but got a different number.")
                
                # Shuffle the new choices
                random.shuffle(new_choices_list)
                st.session_state.current_choices = new_choices_list

            except Exception as e:
                st.error(f"An error occurred while processing the AI response: {str(e)}")
                st.session_state.conversation_history.append(("ERROR", "Error in generating new scenario"))
                st.session_state.current_choices = ["Retry", "Continue with caution", "End journey"]

            st.rerun()  # Rerun the app to update the display

    # Move progress bar to the bottom
    st.write("---")  # Add a separator
    progress = game_state.progress / 100
    st.progress(value=progress, text=f"Overall Progress: {game_state.progress}%")
    st.write(f"Stage of Change: {game_state.get_current_stage()}")
    st.write(f"Hero's Journey Stage: {hero_journey_stage}")
    st.write(f"Steps taken: {game_state.steps_taken}")

    # Add "Print My Story" button when progress reaches 10%
    if progress >= 0.1:
        if st.button("Print My Story"):
            print_story()

def print_story():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"{st.session_state.game_state.character_name}'s Hero Journey", ln=True, align='C')
    pdf.ln(10)

    # Reset font for body text
    pdf.set_font("Arial", size=12)

    for item_type, content in st.session_state.conversation_history:
        if item_type == "SCENARIO":
            pdf.multi_cell(0, 10, txt=content)
            pdf.ln(5)
        elif item_type == "CHOICE":
            pdf.multi_cell(0, 10, txt=f"Choice: {content}")
            pdf.ln(5)
        elif item_type == "OUTCOME":
            pdf.multi_cell(0, 10, txt=f"Outcome: {content}")
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
                pdf.multi_cell(0, 10, txt=f"Error loading image: {str(e)}")

    # Save the PDF
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    # Provide the PDF for download
    st.download_button(
        label="Download Story PDF",
        data=pdf_output,
        file_name=f"{st.session_state.game_state.character_name}_hero_journey.pdf",
        mime="application/pdf"
    )

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
