class GameState:
    def __init__(self):
        self.stages = [
            "The Ordinary World", "The Call to Adventure", "Refusal of the Call",
            "Meeting the Mentor", "Crossing the Threshold", "Tests, Allies, and Enemies",
            "Approach to the Inmost Cave", "The Ordeal", "Reward (Seizing the Sword)",
            "The Road Back", "Resurrection", "Return with the Elixir"
        ]
        self.current_stage = 0
        self.character_name = ""
        self.character_type = ""
        self.distinguishing_feature = ""
        self.challenge = ""
        self.specific_goal = ""
        self.steps_taken = 0
        self.art_style = "Digital painting"
        self.conversation_history = []

    def advance_stage(self):
        if self.current_stage < len(self.stages) - 1:
            self.current_stage += 1
            self.steps_taken += 1

    def is_journey_complete(self):
        return self.current_stage == len(self.stages) - 1

    def get_progress(self):
        return (self.current_stage / (len(self.stages) - 1)) * 100

    def add_to_history(self, item_type, content):
        self.conversation_history.append((item_type, content))
