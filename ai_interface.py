# ai_interface.py

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
        self.image_cache = {}

    def generate_scenario(self, game_state, is_first_scenario=False):
        character_select = (f"{game_state.character_name} the {game_state.character_type} "
                            f"with {game_state.distinguishing_feature}")
        current_stage = game_state.stages[game_state.current_stage]

        if is_first_scenario:
            prompt = (f"Create an opening scenario for {character_select} in their "
                      f"ordinary world, facing the challenge of {game_state.challenge} "
                      f"with the goal of {game_state.specific_goal}. ")
        else:
            prompt = (f"Continue the story for {character_select} in the "
                      f"{current_stage} stage of their journey to "
                      f"overcome {game_state.challenge} and achieve {game_state.specific_goal}. ")

        prompt += ("Provide a vivid, engaging scenario description followed by 3 possible choices. "
                   "Do not include labels like '[Scenario Description]' or '[Choice 1]'. "
                   "Format the response as:\n\nScenario description\n\n1. First choice\n2. Second choice\n3. Third choice")

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a master storyteller crafting an engaging hero's journey for children."},
                    {"role": "user", "content": prompt}
                ]
            )
            return self.process_scenario_response(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Error in generating scenario: {str(e)}")
            return None, []

    def process_scenario_response(self, response):
        parts = response.split("\n\n")
        scenario = parts[0].strip()
        choices = [choice.strip() for choice in parts[1].split("\n") if choice.strip()]
        return scenario, choices

    def generate_image(self, scenario, character_select, art_style):
        cache_key = f"{scenario[:50]}_{character_select}_{art_style}"
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]

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
            image_b64 = response.data[0].b64_json
            self.image_cache[cache_key] = image_b64
            return image_b64
        except Exception as e:
            st.error(f"Error in generating image: {str(e)}")
            return None

    def create_image_prompt(self, scenario, character_select, art_style):
        prompt = f"""
        Create a vivid, single-paragraph description for an illustration capturing 
        a key moment in this scenario:
        
        {scenario}
        
        The image should feature {character_select}. Focus on the hero's actions, 
        the setting, and any important elements. The description should be 
        suitable for creating an image in the style of {art_style}.
        Keep the description under 50 words and make it visually compelling.
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
