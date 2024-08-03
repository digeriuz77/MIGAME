import streamlit as st

def init_state():
    if "journey_in_progress" not in st.session_state:
        st.session_state.journey_in_progress = False
    if "game_state" not in st.session_state:
        st.session_state.game_state = None

def reset_state():
    st.session_state.journey_in_progress = False
    st.session_state.game_state = None
