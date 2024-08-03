# game_logic.py

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
        self.story_elements = []
        self.awaiting_choice = True
        self.current_choices = []

    def advance_stage(self):
        if self.current_stage < len(self.stages) - 1:
            self.current_stage += 1
            self.steps_taken += 1
        self.awaiting_choice = True

    def is_journey_complete(self):
        return self.current_stage == len(self.stages) - 1

    def get_progress(self):
        return (self.current_stage / (len(self.stages) - 1)) * 100

    def add_to_story(self, element_type, content):
        self.story_elements.append((element_type, content))

    def set_choices(self, choices):
        self.current_choices = choices
