# streamlit_app.py

import streamlit as st
from PIL import Image
from io import BytesIO
import base64
import os
import openai
from fpdf import FPDF

# Set your OpenAI API key
openai.api_key = st.secrets.get("openai_api_key", "your-api-key")

# Helper functions for AI interactions
def generate_scenario(game_state, is_first_scenario=False):
    character_select = f"{game_state['character_name']} the {game_state['character_type']} with {game_state['distinguishing_feature']}"
    current_stage = game_state['stages'][game_state['current_stage']]

    if is_first_scenario:
        prompt = (
            f"Create an opening scenario for {character_select} in their "
            f"ordinary world, facing the challenge of {game_state['challenge']} "
            f"with the goal of {game_state['specific_goal']}. "
        )
    else:
        last_choice = game_state['story_elements'][-1][1] if game_state['story_elements'] else "No previous choice"
        prompt = (
            f"Continue the story for {character_select} in the "
            f"{current_stage} stage of their journey to "
            f"overcome {game_state['challenge']} and achieve {game_state['specific_goal']}. "
            f"Their last choice was: {last_choice}. "
        )

    prompt += (
        "Provide a vivid, engaging scenario description followed by 3 possible choices. "
        "Do not include labels. Format the response as:\n\n"
        "Scenario description\n\n1. First choice\n2. Second choice\n3. Third choice"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a master storyteller crafting an engaging hero's journey for children."},
                {"role": "user", "content": prompt}
            ]
        )
        return process_scenario_response(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error in generating scenario: {str(e)}")
        return None, []

def process_scenario_response(response):
    parts = response.strip().split("\n\n")
    scenario = parts[0].strip()
    choices = [choice.strip() for choice in parts[1].split("\n") if choice.strip()]
    while len(choices) < 3:
        choices.append(f"{len(choices) + 1}. [Generate another choice]")
    return scenario, choices[:3]

def generate_image(scenario, character_select, art_style):
    prompt = f"An illustration of {character_select} in the following scene: {scenario}. Art style: {art_style}."
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512",
            response_format="b64_json"
        )
        image_b64 = response['data'][0]['b64_json']
        return image_b64
    except Exception as e:
        st.error(f"Error in generating image: {str(e)}")
        return None

# Initialize game state
if 'game_state' not in st.session_state:
    st.session_state['game_state'] = {
        'stages': [
            "The Ordinary World", "The Call to Adventure", "Refusal of the Call",
            "Meeting the Mentor", "Crossing the Threshold", "Tests, Allies, and Enemies",
            "Approach to the Inmost Cave", "The Ordeal", "Reward (Seizing the Sword)",
            "The Road Back", "Resurrection", "Return with the Elixir"
        ],
        'current_stage': 0,
        'character_name': "",
        'character_type': "",
        'distinguishing_feature': "",
        'challenge': "",
        'specific_goal': "",
        'steps_taken': 0,
        'art_style': "Digital painting",
        'story_elements': [],
        'awaiting_choice': True,
        'current_choices': []
    }

game_state = st.session_state['game_state']

# Start of the app
def start_view():
    st.title("Create Your Own Adventure Book")
    st.subheader("Enter your hero's details:")
    character_name = st.text_input("Hero's Name", value=game_state['character_name'])
    character_type = st.text_input("Hero's Type (e.g., dragon, unicorn)", value=game_state['character_type'])
    distinguishing_feature = st.text_input("Distinguishing Feature (e.g., golden scales)", value=game_state['distinguishing_feature'])
    art_style = st.selectbox("Art Style", ["Digital painting", "Watercolor", "Oil painting", "Pencil sketch"])
    challenge = st.text_input("Challenge (e.g., overcoming fear)", value=game_state['challenge'])
    specific_goal = st.text_input("Specific Goal (e.g., to fly over the mountains)", value=game_state['specific_goal'])

    if st.button("Start Adventure"):
        game_state['character_name'] = character_name
        game_state['character_type'] = character_type
        game_state['distinguishing_feature'] = distinguishing_feature
        game_state['art_style'] = art_style
        game_state['challenge'] = challenge
        game_state['specific_goal'] = specific_goal
        game_state['awaiting_choice'] = True
        st.session_state['game_state'] = game_state
        st.experimental_rerun()

def adventure_view():
    st.title(f"{game_state['character_name']}'s Adventure")
    st.write(f"Current Stage: {game_state['stages'][game_state['current_stage']]}")

    if game_state['awaiting_choice']:
        scenario, choices = generate_scenario(game_state, is_first_scenario=(len(game_state['story_elements']) == 0))
        if scenario and choices:
            game_state['story_elements'].append(('SCENARIO', scenario))
            image_b64 = generate_image(scenario, f"{game_state['character_name']} the {game_state['character_type']}", game_state['art_style'])
            if image_b64:
                game_state['story_elements'].append(('IMAGE', image_b64))
            game_state['current_choices'] = choices
            game_state['awaiting_choice'] = False
            st.session_state['game_state'] = game_state
        else:
            st.error("Failed to generate scenario or choices.")
            return

    display_story()
    display_choices()

def display_story():
    st.subheader("Story So Far")
    for element_type, content in game_state['story_elements']:
        if element_type == 'SCENARIO':
            st.write(content)
        elif element_type == 'IMAGE':
            st.image(base64.b64decode(content), use_column_width=True)
        elif element_type == 'CHOICE':
            st.write(f"**Decision:** {content}")

def display_choices():
    st.subheader("What happens next?")
    choices = game_state['current_choices']
    for i, choice in enumerate(choices):
        if st.button(choice, key=f"choice_{i}"):
            game_state['story_elements'].append(('CHOICE', choice))
            game_state['current_stage'] = min(game_state['current_stage'] + 1, len(game_state['stages']) - 1)
            game_state['awaiting_choice'] = True
            st.session_state['game_state'] = game_state
            st.experimental_rerun()

def download_story():
    if st.button("Download Your Story as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for element_type, content in game_state['story_elements']:
            if element_type == 'SCENARIO':
                pdf.multi_cell(0, 10, content)
            elif element_type == 'CHOICE':
                pdf.multi_cell(0, 10, f"Decision: {content}")
            elif element_type == 'IMAGE':
                image_data = base64.b64decode(content)
                image = Image.open(BytesIO(image_data))
                image_path = f"temp_image_{os.getpid()}.png"
                image.save(image_path)
                pdf.image(image_path, x=10, w=190)
                os.remove(image_path)

        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        st.download_button("Download PDF", data=pdf_output, file_name=f"{game_state['character_name']}_adventure.pdf", mime="application/pdf")

# Main application flow
if not game_state['character_name']:
    start_view()
else:
    adventure_view()
    if game_state['current_stage'] == len(game_state['stages']) - 1:
        st.success("Congratulations! You've completed your adventure.")
        download_story()
