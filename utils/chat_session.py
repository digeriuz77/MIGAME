class ChatSession:
    def __init__(self):
        self.history = []
        self.client = OpenAI(api_key=st.secrets["openai_api_key"])

    def get_ai_response(self, prompt):
        self.history.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a storytelling expert specializing in the hero's journey narrative structure."},
                *self.history
            ]
        )
        ai_response = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": ai_response})
        return ai_response
