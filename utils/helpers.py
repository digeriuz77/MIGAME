import streamlit as st

def init_state():
    if 'game_state' not in st.session_state:
        from utils.game_state import GameState
        st.session_state.game_state = GameState()

def reset_state():
    if 'game_state' in st.session_state:
        del st.session_state.game_state
    init_state()

def add_character_names(input_text, names):
    # Implement character name substitution if needed
    return input_text
