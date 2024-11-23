import streamlit as st
from PIL import Image
from io import BytesIO
import base64
import os
import openai
from fpdf import FPDF
import time

# Set your OpenAI API key
openai.api_key = st.secrets.get("openai_api_key", None)
if not openai.api_key:
    st.error("Please set your OpenAI API key in Streamlit secrets.")
    st.stop()

# Helper functions for AI interactions
def generate_scenario(game_state, is_first_scenario=False):
    character_select = f"{game_state['character_name']} the {game_state['character_type']} with {game_state['distinguishing_feature']}"
    current_stage = game_state['stages'][game_state['current_stage']]
    age = game_state['age']

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

    # Adjust complexity based on age
    if age <= 7:
        complexity = "Use simple words and short sentences suitable for a 5-7 year old."
        num_choices = 2
    elif age <= 10:
        complexity = "Use language appropriate for an 8-10 year old."
        num_choices = 3
    else:
        complexity = "Use language appropriate for an 11-14 year old."
        num_choices = 3

    # Include complexity instructions in the prompt
    prompt += f"\n\n{complexity}"
    prompt += (
        "\n\nProvide a vivid, engaging scenario description followed by choices. "
        "Do not include labels. Format the response as:\n\n"
        "Scenario description\n\n1. First choice\n2. Second choice"
    )
    if num_choices == 3:
        prompt += "\n3. Third choice"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a master storyteller crafting an engaging hero's journey for children."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response['choices'][0]['message']['content']
        return process_scenario_response(content, num_choices)
    except Exception as e:
        st.error(f"Error in generating scenario: {str(e)}")
        return None, []

def process_scenario_response(response, num_choices=3):
    parts = response.strip().split("\n\n")
    scenario = parts[0].strip()
    choices = []
    if len(parts) > 1:
        choices = [choice.strip() for choice in parts[1].split("\n") if choice.strip()]
        choices = choices[:num_choices]
    return scenario, choices

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

def display_scenario_text(scenario):
    placeholder = st.empty()
    words = scenario.split()
    full_text = ""
    for word in words:
        full_text += word + " "
        placeholder.markdown(full_text)
        time.sleep(0.05)  # Adjust the speed as desired

def display_image_with_effect(image_b64):
    image_data = base64.b64decode(image_b64)
    image = Image.open(BytesIO(image_data))
    st.image(image, use_column_width=True)
    time.sleep(0.5)  # Pause after displaying the image

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
        'current_choices': [],
        'age': 10,
        'title': ""
    }

game_state = st.session_state['game_state']

# Start of the app
def start_view():
    st.title("📖 Create Your Own Adventure Book")
    st.subheader("Enter your hero's details:")
    character_name = st.text_input("Hero's Name", value=game_state['character_name'])
    character_type = st.text_input("Hero's Type (e.g., dragon, unicorn)", value=game_state['character_type'])
    distinguishing_feature = st.text_input("Distinguishing Feature (e.g., golden scales)", value=game_state['distinguishing_feature'])
    art_style = st.selectbox("Art Style", ["Digital painting", "Watercolor", "Oil painting", "Pencil sketch"])
    age = st.number_input("Enter your age:", min_value=5, max_value=14, value=game_state['age'])
    challenge = st.text_input("Challenge (e.g., overcoming fear)", value=game_state['challenge'])
    specific_goal = st.text_input("Specific Goal (e.g., to fly over the mountains)", value=game_state['specific_goal'])

    if st.button("✨ Start Adventure ✨"):
        if not character_name or not character_type or not challenge or not specific_goal:
            st.warning("Please fill in all the required fields.")
            return
        game_state['character_name'] = character_name
        game_state['character_type'] = character_type
        game_state['distinguishing_feature'] = distinguishing_feature
        game_state['art_style'] = art_style
        game_state['challenge'] = challenge
        game_state['specific_goal'] = specific_goal
        game_state['age'] = age
        game_state['awaiting_choice'] = True
        st.session_state['game_state'] = game_state
        st.rerun()

def adventure_view():
    st.title(f"✨ {game_state['character_name']}'s Magical Adventure ✨")
    st.write(f"**Current Stage:** {game_state['stages'][game_state['current_stage']]}")
    st.write(f"**Your Goal:** {game_state['specific_goal']}")

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

    if game_state['current_stage'] == len(game_state['stages']) - 1:
        st.success("🎉 Congratulations! You've completed your adventure.")
        title = st.text_input("Choose a title for your story:", value=f"{game_state['character_name']}'s Adventure")
        game_state['title'] = title
        st.session_state['game_state'] = game_state
        download_story()

def display_story():
    st.markdown("---")
    st.subheader("📖 Story So Far")
    for element_type, content in game_state['story_elements']:
        if element_type == 'SCENARIO':
            display_scenario_text(content)
        elif element_type == 'IMAGE':
            display_image_with_effect(content)
        elif element_type == 'CHOICE':
            st.write(f"**Decision:** {content}")

def display_choices():
    st.markdown("---")
    st.subheader("🌟 What happens next?")
    choices = game_state['current_choices']
    if choices:
        for i, choice in enumerate(choices):
            if st.button(choice, key=f"choice_{i}"):
                game_state['story_elements'].append(('CHOICE', choice))
                game_state['current_stage'] = min(game_state['current_stage'] + 1, len(game_state['stages']) - 1)
                game_state['awaiting_choice'] = True
                st.session_state['game_state'] = game_state
                st.rerun()
    else:
        st.error("No choices available. Please restart the story.")
        if st.button("🔄 Restart Story"):
            st.session_state['game_state'] = None
            st.rerun()

def download_story():
    if st.button("📥 Download Your Story as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 24)

        # Add cover page with title and an image
        title = game_state.get('title', f"{game_state['character_name']}'s Adventure")
        pdf.multi_cell(0, 20, title, align='C')

        # Optionally, include a cover image
        cover_image_b64 = generate_image(
            f"A cover image for the story titled '{title}' featuring {game_state['character_name']} the {game_state['character_type']}",
            f"{game_state['character_name']} the {game_state['character_type']}",
            game_state['art_style']
        )

        if cover_image_b64:
            image_data = base64.b64decode(cover_image_b64)
            image = Image.open(BytesIO(image_data))
            image_path = f"cover_image_{os.getpid()}.png"
            image.save(image_path)
            pdf.image(image_path, x=10, w=190)
            os.remove(image_path)

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
        st.download_button("Download PDF", data=pdf_output, file_name=f"{title}.pdf", mime="application/pdf")

# Main application flow
if not game_state['character_name']:
    start_view()
else:
    adventure_view()
