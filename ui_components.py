# ui_components.py

import streamlit as st
from game_logic import GameState
from ai_interface import AIInterface

def start_view():
    st.title("Start Your Hero's Journey")
    
    character_name = st.text_input("Enter your character's name:")
    character_type = st.text_input("What kind of creature is your hero? (e.g., dragon, unicorn, elf)")
    distinguishing_feature = st.text_input("What's a unique feature of your hero? (e.g., glowing eyes, rainbow mane)")
    
    art_styles = [
        "Digital painting", "Watercolor", "Oil painting", "Pencil sketch", 
        "Comic book art", "Pixel art", "3D render", "Storybook illustration"
    ]
    art_style = st.selectbox("Choose an art style for your journey:", art_styles)
    
    challenge_areas = ["Overcoming fear", "Making new friends", "Learning a new skill", "Helping others"]
    selected_challenge = st.selectbox("Choose a challenge:", challenge_areas)
    
    specific_goal = st.text_input("What specific goal does your hero have for this challenge?")

    if st.button("Begin Journey"):
        game_state = GameState()
        game_state.character_name = character_name
        game_state.character_type = character_type
        game_state.distinguishing_feature = distinguishing_feature
        game_state.art_style = art_style
        game_state.challenge = selected_challenge
        game_state.specific_goal = specific_goal
        
        st.session_state.game_state = game_state
        st.session_state.journey_in_progress = True
        st.rerun()

def game_view():
    game_state = st.session_state.game_state
    ai_interface = AIInterface()

    st.title(f"{game_state.character_name}'s Hero Journey: {game_state.challenge}")
    st.write(f"Current Stage: {game_state.stages[game_state.current_stage]}")
    st.write(f"Goal: {game_state.specific_goal}")

    if not game_state.conversation_history:
        scenario, choices = ai_interface.generate_scenario(game_state, is_first_scenario=True)
        if scenario and choices:
            game_state.add_to_history("SCENARIO", scenario)
            image_b64 = ai_interface.generate_image(scenario, f"{game_state.character_name} the {game_state.character_type}", game_state.art_style)
            if image_b64:
                game_state.add_to_history("IMAGE", image_b64)
            game_state.add_to_history("CHOICES", choices)

    display_story(game_state)
    display_choices(game_state, ai_interface)
    display_progress(game_state)

def display_story(game_state):
    for item_type, content in game_state.conversation_history:
        if item_type == "SCENARIO":
            st.write(content)
        elif item_type == "IMAGE":
            st.image(f"data:image/png;base64,{content}")
        elif item_type == "CHOICE":
            st.write(f"Our hero chose to: {content}")

def display_choices(game_state, ai_interface):
    choices = next((content for item_type, content in reversed(game_state.conversation_history) if item_type == "CHOICES"), None)
    if choices:
        with st.form(key='choice_form'):
            choice = st.radio("What will our hero do next?", choices)
            submit_button = st.form_submit_button(label='Choose')

        if submit_button:
            game_state.add_to_history("CHOICE", choice)
            game_state.advance_stage()
            scenario, new_choices = ai_interface.generate_scenario(game_state)
            if scenario and new_choices:
                game_state.add_to_history("SCENARIO", scenario)
                image_b64 = ai_interface.generate_image(scenario, f"{game_state.character_name} the {game_state.character_type}", game_state.art_style)
                if image_b64:
                    game_state.add_to_history("IMAGE", image_b64)
                game_state.add_to_history("CHOICES", new_choices)
            st.rerun()

def display_progress(game_state):
    progress = game_state.get_progress()
    st.progress(progress / 100)
    st.write(f"Journey Progress: {progress:.1f}%")
    st.write(f"Steps taken: {game_state.steps_taken}")

def end_view():
    st.title("Journey Complete!")
    st.write("Congratulations! You've completed your hero's journey.")
    # Implement story summary or recap here
