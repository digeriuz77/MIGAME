class GameState:
    """
    Manages the state of the hero's journey game.
    """
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

    def advance_stage(self):
        """Advance to the next stage of the hero's journey."""
        if self.current_stage < len(self.stages) - 1:
            self.current_stage += 1
            self.steps_taken += 1

    def is_journey_complete(self):
        """Check if the hero's journey is complete."""
        return self.current_stage == len(self.stages) - 1

    def get_progress(self):
        """Calculate the current progress of the journey."""
        return (self.current_stage / (len(self.stages) - 1)) * 100
