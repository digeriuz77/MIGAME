import streamlit as st
from openai import OpenAI
import base64
from io import BytesIO

class AIInterface:
    def __init__(self):
        if "openai_api_key" not in st.secrets:
            st.error("OpenAI API key not found. Please set it in your Streamlit secrets.")
            st.stop()
        self.client = OpenAI(api_key=st.secrets["openai_api_key"])

    def generate_scenario(self, game_state, is_first_scenario=False):
        character_select = (f"{game_state.character_name} the {game_state.character_type} "
                            f"with {game_state.distinguishing_feature}")
        current_stage = game_state.stages[game_state.current_stage]

        if is_first_scenario:
            prompt = (f"Create an opening scenario for {character_select} in their "
                      f"ordinary world, facing the challenge of {game_state.challenge} "
                      f"with the goal of {game_state.specific_goal}. ")
        else:
            prompt = (f"Create the next scenario for {character_select} in the "
                      f"{current_stage} stage, continuing their journey to "
                      f"overcome {game_state.challenge} and achieve {game_state.specific_goal}. ")

        prompt += ("Provide a vivid scenario description and 3 possible choices "
                   "that fit naturally with the story. Format: [Scenario description]"
                   "\n1. [Choice 1]\n2. [Choice 2]\n3. [Choice 3]")

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a storytelling expert specializing in the hero's journey narrative structure for children."},
                    {"role": "user", "content": prompt}
                ]
            )
            return self.process_scenario_response(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Error in generating scenario: {str(e)}")
            return None, []

    def process_scenario_response(self, response):
        parts = response.split("\n1.")
        scenario = parts[0].strip()
        choices = ["1." + choice.strip() for choice in parts[1:]]
        return scenario, choices

    def generate_image(self, scenario, character_select, art_style):
        prompt = self.create_image_prompt(scenario, character_select, art_style)
        if not prompt:
            st.error("Failed to create image prompt")
            return None

        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json"
            )
            return response.data[0].b64_json
        except Exception as e:
            st.error(f"Error in generating image: {str(e)}")
            return None

    def create_image_prompt(self, scenario, character_select, art_style):
        prompt = f"""
        Create a brief, single-paragraph description for an image that captures 
        a key moment in this scenario:
        
        {scenario}
        
        The image should feature {character_select}. Focus on the hero's actions, 
        the setting, and any important objects or characters. The description should be 
        suitable for creating an image in the style of {art_style}.
        Keep the description under 50 words and make it visually evocative.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at creating vivid, concise image descriptions for illustrations."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"Error in creating image prompt: {str(e)}")
            return None
