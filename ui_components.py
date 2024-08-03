# ui_components.py

import streamlit as st
from game_logic import GameState
from ai_interface import AIInterface
from fpdf import FPDF
import base64
from io import BytesIO
from PIL import Image
import os

def start_view():
    st.title("Begin Your Hero's Journey")
    
    col1, col2 = st.columns(2)
    with col1:
        character_name = st.text_input("Your hero's name:")
        character_type = st.text_input("Type of creature (e.g., dragon, unicorn, elf):")
    with col2:
        distinguishing_feature = st.text_input("A unique feature (e.g., glowing eyes, rainbow mane):")
        art_style = st.selectbox("Choose an art style:", [
            "Digital painting", "Watercolor", "Oil painting", "Pencil sketch", 
            "Comic book art", "Pixel art", "3D render", "Storybook illustration"
        ])
    
    challenge_areas = ["Overcoming fear", "Making new friends", "Learning a new skill", "Helping others"]
    selected_challenge = st.selectbox("What challenge will your hero face?", challenge_areas)
    specific_goal = st.text_input("What specific goal does your hero have for this challenge?")

    if st.button("Embark on the Journey"):
        game_state = GameState()
        game_state.character_name = character_name
        game_state.character_type = character_type
        game_state.distinguishing_feature = distinguishing_feature
        game_state.art_style = art_style
        game_state.challenge = selected_challenge
        game_state.specific_goal = specific_goal
        game_state.awaiting_choice = True
        
        st.session_state.game_state = game_state
        st.session_state.journey_in_progress = True
        st.rerun()

def game_view():
    game_state = st.session_state.game_state
    ai_interface = AIInterface()

    st.title(f"{game_state.character_name}'s Hero Journey")
    st.subheader(f"Challenge: {game_state.challenge}")
    st.write(f"Current Stage: {game_state.stages[game_state.current_stage]}")

    if game_state.awaiting_choice:
        scenario, choices = ai_interface.generate_scenario(game_state, is_first_scenario=(len(game_state.story_elements) == 0))
        
        if scenario and choices:
            game_state.add_to_story("SCENARIO", scenario)
            image_b64 = ai_interface.generate_image(scenario, f"{game_state.character_name} the {game_state.character_type}", game_state.art_style)
            if image_b64:
                game_state.add_to_story("IMAGE", image_b64)
            game_state.set_choices(choices)
            game_state.awaiting_choice = False

    display_current_page(game_state)
    display_choices(game_state)
    display_progress(game_state)

def display_choices(game_state):
    if game_state.current_choices:
        st.subheader("What will our hero do next?")
        cols = st.columns(3)
        for i, choice in enumerate(game_state.current_choices):
            if cols[i].button(choice.split(". ", 1)[1], key=f"choice_{i}"):
                game_state.add_to_story("CHOICE", choice.split(". ", 1)[1])
                game_state.advance_stage()
                st.rerun()
                

def display_current_page(game_state):
    if not game_state.story_elements:
        return

    st.markdown("---")
    st.subheader("Current Scene")

    for element_type, content in game_state.story_elements[-3:]:  # Display last 3 elements (scenario, image, choice)
        if element_type == "SCENARIO":
            st.write(content)
        elif element_type == "IMAGE":
            st.image(f"data:image/png;base64,{content}")
        elif element_type == "CHOICE" and not game_state.awaiting_choice:
            st.write(f"Our hero decided to: {content}")
            
def display_progress(game_state):
    st.markdown("---")
    progress = game_state.get_progress()
    st.progress(progress / 100)
    st.write(f"Journey Progress: {progress:.1f}%")
    st.write(f"Steps taken: {game_state.steps_taken}")

    if progress >= 10:
        if st.button("Print My Story"):
            pdf_bytes = print_story(game_state)
            st.download_button(
                label="Download Your Hero's Journey Story",
                data=pdf_bytes,
                file_name=f"{game_state.character_name}_hero_journey.pdf",
                mime="application/pdf"
            )

def end_view():
    st.title("Journey Complete!")
    st.write("Congratulations! You've completed your hero's journey.")
    game_state = st.session_state.game_state
    display_current_page(game_state)
    if st.button("Print My Story"):
        pdf_bytes = print_story(game_state)
        st.download_button(
            label="Download Your Hero's Journey Story",
            data=pdf_bytes,
            file_name=f"{game_state.character_name}_hero_journey.pdf",
            mime="application/pdf"
        )

def print_story(game_state):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"{game_state.character_name}'s Hero Journey", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)

    for element_type, content in game_state.story_elements:
        if element_type == "SCENARIO":
            pdf.multi_cell(0, 10, txt=content)
            pdf.ln(5)
        elif element_type == "CHOICE":
            pdf.multi_cell(0, 10, txt=f"Our hero decided to: {content}")
            pdf.ln(5)
        elif element_type == "IMAGE":
            try:
                image_data = base64.b64decode(content)
                image = Image.open(BytesIO(image_data))
                image_path = f"temp_image_{pdf.page_no()}.png"
                image.save(image_path)
                pdf.image(image_path, x=10, w=190)
                pdf.ln(5)
                os.remove(image_path)  # Clean up the temporary image file
            except Exception as e:
                pdf.multi_cell(0, 10, txt="[An image of the hero's journey would be here]")

    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output.getvalue()
