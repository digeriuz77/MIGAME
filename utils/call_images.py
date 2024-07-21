import openai
from .chat_session import ChatSession

def create_image(prompt):
    return openai.images.generate(
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="b64_json",
        model="dall-e-3",
    ).model_dump()

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
    story_ending = "\n\n".join(
        [x["content"] for x in chat_history.history if x["role"] != "system"][-3:]
    )
    prompt = f"{GENERATE_IMAGE_DESCRIPTION_PROMPT.format(character_select=character_select)}\n\n{story_ending}"
    image_chat = ChatSession()
    image_chat.user_says(prompt)
    return image_chat.get_ai_response()
