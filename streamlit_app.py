import streamlit as st
import random
from pathlib import Path
from utils.chat_session import ChatSession
from utils.call_images import create_image, create_image_prompt
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

AREAS_OF_CHANGE = [
    "Feeling good about body and mind", "Making friends",
    "Getting better at stuff", "Stop doing something"
]

# Embedded GameState class
class GameState:
    def __init__(self):
        self.stages = HERO_JOURNEY_STAGES
        self._current_stage = 0
        self.focus_area = ""
        self.specific_goal = ""
        self.progress = 0
        self.steps_taken = 0
        self.character_name = ""
        self.character_type = ""

    def set_focus_area(self, area):
        self.focus_area = area

    def set_specific_goal(self, goal):
        self.specific_goal = goal

    def set_character(self, name, char_type):
        self.character_name = name
        self.character_type = char_type

    def get_current_stage(self):
        return self.stages[self._current_stage]

    def process_choice(self, choice):
        self.steps_taken += 1
        return f"You chose to {choice.lower()}."

    def increment_progress(self, change_score):
        self.progress += change_score
        if self.progress < 0:
            self.progress = 0
        elif self.progress > 100:
            self.progress = 100
        
        # Check for stage advancement
        stage_threshold = 100 / len(self.stages)
        if self.progress >= (self._current_stage + 1) * stage_threshold:
            self.advance_stage()

    def advance_stage(self):
        if self._current_stage < len(self.stages) - 1:
            self._current_stage += 1

# Rest of your Streamlit app code...

# Setup
st.set_page_config("Heroes' journey", layout="wide")
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
        "What avatar would you like to have? (It works best if you pick a creature)"
    )
    
    st.write("Choose an art style for your journey:")
    art_style = st.selectbox("Art style:", ART_STYLES)
    
    st.write("What area of your character's life would you like to focus on to change?")
    selected_area = st.selectbox("Choose an area:", AREAS_OF_CHANGE)
    
    specific_goal = st.text_input("What specific goal do you have in mind for this area?")

    if st.button("Begin Journey"):
        st.session_state.game_state.set_character(character_name, character_type)
        st.session_state.game_state.set_focus_area(selected_area)
        st.session_state.game_state.set_specific_goal(specific_goal)
        st.session_state.art_style = art_style
        st.session_state.journey_in_progress = True
        st.session_state.hero_journey_stage = 0
        generate_scenario()
        st.rerun()

def generate_scenario():
    """Generate a new scenario for the hero's journey."""
    game_state = st.session_state.game_state
    chat_session = st.session_state.chat_session
    hero_journey_stage = HERO_JOURNEY_STAGES[st.session_state.hero_journey_stage]
    character_select = f"{game_state.character_name} the {game_state.character_type}"

    context = "\n".join(
        f"{item[0]}: {item[1]}"
        for item in st.session_state.conversation_history[-5:]
    )

    prompt = create_scenario_prompt(game_state, hero_journey_stage, context, character_select)
    response = chat_session.get_ai_response(prompt)
    
    try:
        scenario, choices = response.split("Choices:")
        st.session_state.current_scenario = scenario.strip()
        choices = [choice.strip() for choice in choices.split("\n") if choice.strip()]
        if len(choices) != 3:
            raise ValueError("Expected 3 choices, but got a different number.")
        
        random.shuffle(choices)
        st.session_state.current_choices = choices
        
        st.session_state.conversation_history.append(
            ("SCENARIO", st.session_state.current_scenario)
        )
    except Exception as e:
        handle_scenario_generation_error(e)

def create_scenario_prompt(game_state, hero_journey_stage, context, character_select):
    """Create the prompt for generating a new scenario."""
    return (
        f"Previous context:\n{context}\n\n"
        f"Generate a young adult scenario for {character_select} who is in the "
        f"{game_state.get_current_stage()} stage of change, focusing on "
        f"{game_state.focus_area} with the specific goal of {game_state.specific_goal}. "
        f"The scenario should align with the hero's journey stage: {hero_journey_stage}. "
        f"Present a situation where the character faces a decision related to "
        f"their change process and hero's journey.\n\n"
        f"Also, provide 3 possible choices for the user, each representing a "
        f"different approach to the hero's journey:\n"
        f"1. A choice representing hesitation or retreat (but not complete inaction)\n"
        f"2. A choice representing a cautious step forward\n"
        f"3. A choice representing a bold, heroic action\n\n"
        f"Each choice should give the hero a chance to change and progress in their journey.\n\n"
        f"Format the response as follows:\n"
        f"Scenario: [Your scenario here]\n"
        f"Choices:\n"
        f"1. [Choice 1]\n"
        f"2. [Choice 2]\n"
        f"3. [Choice 3]\n\n"
        f"Keep the entire response under 300 words."
    )

def handle_scenario_generation_error(error):
    """Handle errors that occur during scenario generation."""
    st.error(f"An error occurred while processing the AI response: {str(error)}")
    st.session_state.current_scenario = "Error generating scenario. Please try again."
    st.session_state.current_choices = ["Retry", "Continue with caution", "End journey"]
    st.session_state.conversation_history.append(("ERROR", "Error in scenario generation"))

def display_hero_info(character_select, game_state, hero_journey_stage):
    """Display the hero's information at the top of the page."""
    st.title(f"{character_select}'s Hero Journey: {game_state.focus_area}")
    st.write(f"Current Stage of Change: {game_state.get_current_stage()}")
    st.write(f"Hero's Journey Stage: {hero_journey_stage}")
    st.write(f"Your Goal: {game_state.specific_goal}")

def generate_and_display_image(chat_session, character_select, art_style):
    """Generate and display an image based on the current scenario."""
    if st.session_state.get('generate_image_next_turn', False):
        try:
            with st.spinner("Generating image..."):
                image_prompt = create_image_prompt(
                    chat_session, character_select, art_style
                )
                if image_prompt:
                    full_prompt = f"{art_style} of {image_prompt}"
                    image_b64 = create_image(chat_session, full_prompt)
                    if image_b64:
                        st.session_state.conversation_history.append(
                            ("IMAGE", image_b64)
                        )
                    else:
                        st.warning("Unable to generate image for this scenario.")
                else:
                    st.warning("Unable to generate image prompt.")
        except Exception as e:
            st.error(f"An error occurred while generating the image: {str(e)}")
        
        st.session_state.generate_image_next_turn = False

def display_conversation_history():
    """Display the conversation history and images."""
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

def process_user_choice(choice, game_state, chat_session, character_select):
    """Process the user's choice and generate a new scenario."""
    change_scores = [1, 2, 3]
    choice_index = st.session_state.current_choices.index(choice)
    change_score = change_scores[choice_index]
    
    game_state.increment_progress(change_score)
    st.session_state.game_state = game_state

    hero_journey_stage = HERO_JOURNEY_STAGES[game_state._current_stage]

    context = "\n".join(
        f"{item[0]}: {item[1]}"
        for item in st.session_state.conversation_history[-5:]
    )

    prompt = create_choice_prompt(game_state, hero_journey_stage, context, character_select, choice)

    try:
        response = chat_session.get_ai_response(prompt)
        outcome, new_content = response.split("New Scenario:")
        new_scenario, new_choices = new_content.split("Choices:")

        st.session_state.conversation_history.append(("CHOICE", choice))
        st.session_state.conversation_history.append(("OUTCOME", outcome.strip()))
        st.session_state.generate_image_next_turn = True
        st.session_state.conversation_history.append(
            ("SCENARIO", new_scenario.strip())
        )

        new_choices_list = [
            choice.strip() for choice in new_choices.split("\n") if choice.strip()
        ]
        if len(new_choices_list) != 3:
            raise ValueError("Expected 3 choices, but got a different number.")
        
        random.shuffle(new_choices_list)
        st.session_state.current_choices = new_choices_list

    except Exception as e:
        handle_choice_processing_error(e)

    # Ensure we always set this flag to generate a new image
    st.session_state.generate_image_next_turn = True

def create_choice_prompt(game_state, hero_journey_stage, context, character_select, choice):
    """Create the prompt for processing a user's choice."""
    return (
        f"Previous context:\n{context}\n\n"
        f"{character_select} chose: '{choice}' in response to the previous "
        f"scenario. They are in the {game_state.get_current_stage()} stage of "
        f"change for {game_state.focus_area}, with the specific goal of "
        f"{game_state.specific_goal}. The current hero's journey stage is: "
        f"{hero_journey_stage}.\n\n"
        f"Generate a brief (110 words max) response describing the outcome of "
        f"this choice, their feelings about it, and what the character learned "
        f"or how they grew.\n\n"
        f"Then, provide a new scenario and 3 new choices based on this outcome, "
        f"following the same format as before. Ensure the new scenario and "
        f"choices align with the current hero's journey stage and the "
        f"character's goal.\n\n"
        f"Format the response as follows:\n"
        f"Outcome: [Your outcome here]\n"
        f"New Scenario: [Your new scenario here]\n"
        f"Choices:\n"
        f"1. [Choice representing hesitation or retreat]\n"
        f"2. [Choice representing a cautious step forward]\n"
        f"3. [Choice representing a bold, heroic action]\n\n"
        f"Keep the entire response under 350 words."
    )

def handle_choice_processing_error(error):
    """Handle errors that occur during choice processing."""
    st.error(f"An error occurred while processing the AI response: {str(error)}")
    st.session_state.conversation_history.append(
        ("ERROR", "Error in generating new scenario")
    )
    st.session_state.current_choices = [
        "Retry", "Continue with caution", "End journey"
    ]

def display_progress(game_state, hero_journey_stage):
    """Display the progress bar and related information."""
    st.write("---")
    progress = game_state.progress / 100
    st.progress(value=progress, text=f"Overall Progress: {game_state.progress}%")
    st.write(f"Stage of Change: {game_state.get_current_stage()}")
    st.write(f"Hero's Journey Stage: {hero_journey_stage}")
    st.write(f"Steps taken: {game_state.steps_taken}")

def main_view():
    """Main view of the hero's journey application."""
    game_state = st.session_state.game_state
    chat_session = st.session_state.chat_session
    character_select = f"{game_state.character_name} the {game_state.character_type}"
    art_style = st.session_state.art_style
    hero_journey_stage = HERO_JOURNEY_STAGES[st.session_state.hero_journey_stage]

    display_hero_info(character_select, game_state, hero_journey_stage)
    generate_and_display_image(chat_session, character_select, art_style)
    display_conversation_history()

    if "current_choices" not in st.session_state or not st.session_state.current_choices:
        generate_scenario()
        st.rerun()

    with st.form(key='choice_form'):
        choice = st.radio("What will you do?", st.session_state.current_choices)
        submit_button = st.form_submit_button(label='Make Choice')

        if submit_button:
            process_user_choice(choice, game_state, chat_session, character_select)
            st.rerun()

    display_progress(game_state, hero_journey_stage)

    if game_state.progress / 100 >= 0.1:
        if st.button("Print My Story"):
            print_story()

def print_story():
    """Generate and provide a PDF of the hero's journey story."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"{st.session_state.game_state.character_name}'s Hero Journey", ln=True, align='C')
    pdf.ln(10)

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

    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

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

if __name__ == "__main__":
    main()
