import openai
from openai import OpenAI
import logging
import streamlit as st

logging.basicConfig(level=logging.INFO)

def get_openai_client():
    if "openai_api_key" not in st.secrets:
        st.error("OpenAI API key not found in Streamlit secrets. Please set it in your secrets.toml file.")
        st.stop()
    
    return OpenAI(api_key=st.secrets["openai_api_key"])

def create_image(prompt):
    if not prompt:
        logging.error("Image prompt is None or empty")
        return None
    try:
        client = get_openai_client()
        logging.info(f"Attempting to create image with prompt: {prompt}")
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="b64_json"
        )
        logging.info("Image creation successful")
        return response.data[0].b64_json
    except Exception as e:
        logging.error(f"Error creating image: {str(e)}")
        return None

GENERATE_IMAGE_DESCRIPTION_PROMPT = """
Given the following section of a short children's story about {character_select} 
write a very brief single-line description summarizing the main plot element. 
Focus on what the {character_select} is doing, describe the setting. 
Include any specific objects mentioned in the chat to that point.
The characters should be simply described, not named.
This description will be used to generate a picture to accompany the text. 
Each description should start with "A suitable for a young audience cartoon drawing of..."
Story text begins now:
"""

def create_image_prompt(chat_history, character_select: str):
    try:
        story_ending = "\n\n".join(
            [x.content for x in chat_history.messages if x.role != "system"][-3:]
        )
        prompt = f"{GENERATE_IMAGE_DESCRIPTION_PROMPT.format(character_select=character_select)}\n\n{story_ending}"
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        image_prompt = response.choices[0].message.content
        logging.info(f"Generated image prompt: {image_prompt}")
        return image_prompt
    except Exception as e:
        logging.error(f"Error creating image prompt: {str(e)}")
        return None
