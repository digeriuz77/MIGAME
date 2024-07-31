class ChatSession:
    def __init__(self):
        self.history = []
        self.client = None
        self.initialize_client()

    def initialize_client(self):
        if "openai_api_key" in st.secrets:
            self.client = OpenAI(api_key=st.secrets["openai_api_key"])
        else:
            st.error("OpenAI API key not found. Please set it in your Streamlit secrets.")
            st.stop()

    def get_ai_response(self, prompt):
        if not self.client:
            self.initialize_client()
        
        self.history.append({"role": "user", "content": prompt})
        try:
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
        except Exception as e:
            logging.error(f"Error in get_ai_response: {str(e)}")
            return None
