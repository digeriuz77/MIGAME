# utils.py

import streamlit as st

def init_state():
    """Initialize the application state."""
    if "journey_in_progress" not in st.session_state:
        st.session_state.journey_in_progress = False
    if "game_state" not in st.session_state:
        st.session_state.game_state = None

def reset_state():
    """Reset the application state for a new journey."""
    st.session_state.journey_in_progress = False
    st.session_state.game_state = None
