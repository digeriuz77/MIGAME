import logging
import streamlit as st
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

def get_openai_client():
    if "openai_api_key" not in st.secrets:
        st.error("OpenAI API key not found in Streamlit secrets. Please set it in your secrets.toml file.")
        st.stop()
    
    return OpenAI(api_key=st.secrets["openai_api_key"])

def create_image(chat_session, prompt):
    if not prompt:
        logging.error("Image prompt is None or empty")
        return None
    try:
        logging.info(f"Attempting to create image with prompt: {prompt}")
        client = get_openai_client()
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
Given the following section of a story about {character_select} 
write a very brief single-line description summarizing the main plot element. 
Focus on what the {character_select} is doing, describe the setting. 
Include any specific objects mentioned in the chat to that point.
The characters should be simply described, not named.
This description will be used to generate a picture to accompany the text. 
The description should be suitable for creating an image in the style of {art_style}.
Story text begins now:
"""

def create_image_prompt(chat_session, character_select: str, art_style: str):
    try:
        # Get the last few messages from the chat history
        story_ending = "\n\n".join(
            [msg["content"] for msg in chat_session.history[-3:] if msg["role"] != "system"]
        )
        prompt = f"{GENERATE_IMAGE_DESCRIPTION_PROMPT.format(character_select=character_select, art_style=art_style)}\n\n{story_ending}"
        
        # Use the existing ChatSession to get the AI response
        image_prompt = chat_session.get_ai_response(prompt)
        
        logging.info(f"Generated image prompt: {image_prompt}")
        return image_prompt.strip()  # Ensure there's no leading/trailing whitespace
    except Exception as e:
        logging.error(f"Error creating image prompt: {str(e)}")
        return None
