import openai
import streamlit as st

class AIInterface:
    """
    Handles interactions with the OpenAI API for text and image generation.
    """
    def __init__(self):
        if "openai_api_key" not in st.secrets:
            st.error("OpenAI API key not found. Please set it in your Streamlit secrets.")
            st.stop()
        openai.api_key = st.secrets["openai_api_key"]

    def generate_scenario(self, game_state, is_first_scenario=False):
        """Generate a new scenario based on the current game state."""
        # Implementation here

    def generate_image(self, prompt):
        """Generate an image based on the given prompt."""
        # Implementation here
