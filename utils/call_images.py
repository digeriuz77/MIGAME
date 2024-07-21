import openai
from .chat_session import ChatSession

import openai
import logging

logging.basicConfig(level=logging.INFO)

def create_image(prompt):
    try:
        logging.info(f"Attempting to create image with prompt: {prompt}")
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="b64_json",
            model="dall-e-3",
        )
        logging.info("Image creation successful")
        return response['data'][0]['b64_json']
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error creating image: {str(e)}")
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

def create_image_prompt(chat_history: ChatSession, character_select: str):
    try:
        story_ending = "\n\n".join(
            [x["content"] for x in chat_history.history if x["role"] != "system"][-3:]
        )
        prompt = f"{GENERATE_IMAGE_DESCRIPTION_PROMPT.format(character_select=character_select)}\n\n{story_ending}"
        image_chat = ChatSession()
        image_chat.user_says(prompt)
        return image_chat.get_ai_response()
    except Exception as e:
        print(f"Error creating image prompt: {e}")
        return None
