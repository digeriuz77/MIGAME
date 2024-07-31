import streamlit as st
from openai import OpenAI

def get_openai_client():
    if "openai_api_key" not in st.secrets:
        st.error("OpenAI API key not found in Streamlit secrets. Please set it in your secrets.toml file.")
        st.stop()
    
    return OpenAI(api_key=st.secrets["openai_api_key"])

def create_image(chat_session, prompt):
    if not prompt:
        st.error("Image prompt is empty")
        return None
    try:
        client = get_openai_client()
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="b64_json"
        )
        return response.data[0].b64_json
    except Exception as e:
        st.error(f"Error creating image: {str(e)}")
        return None

def create_image_prompt(chat_session, character_select: str, art_style: str):
    prompt = f"""
    Given the current state of the hero's journey for {character_select}, 
    write a brief, single-paragraph description for an image that captures 
    a key moment in the story. Focus on the hero's actions, the setting, 
    and any important objects or characters. The description should be 
    suitable for creating an image in the style of {art_style}.
    Keep the description under 50 words and make it visually evocative.
    """
    
    image_prompt = chat_session.get_ai_response(prompt)
    return image_prompt.strip() if image_prompt else None
