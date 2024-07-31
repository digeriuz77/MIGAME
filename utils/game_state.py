class GameState:
    def __init__(self):
        self.stages = [
            "The Ordinary World", "The Call to Adventure", "Refusal of the Call",
            "Meeting the Mentor", "Crossing the Threshold", "Tests, Allies, and Enemies",
            "Approach to the Inmost Cave", "The Ordeal", "Reward (Seizing the Sword)",
            "The Road Back", "Resurrection", "Return with the Elixir"
        ]
        self._current_stage = 0
        self.challenge = ""
        self.specific_goal = ""
        self.progress = 0
        self.steps_taken = 0
        self.character_name = ""
        self.character_type = ""
        self.distinguishing_feature = ""

    def set_character(self, name, char_type, feature):
        self.character_name = name
        self.character_type = char_type
        self.distinguishing_feature = feature

    def set_challenge(self, challenge):
        self.challenge = challenge

    def set_specific_goal(self, goal):
        self.specific_goal = goal

    def get_current_stage(self):
        return self.stages[self._current_stage]

    def increment_progress(self, change_score):
        self.progress += change_score
        self.steps_taken += 1
        if self.progress < 0:
            self.progress = 0
        elif self.progress > 100:
            self.progress = 100

    def advance_stage(self):
        if self._current_stage < len(self.stages) - 1:
            self._current_stage += 1
