class GameState:
    def __init__(self):
        self.stages = HERO_JOURNEY_STAGES  # Use the constant from the main file
        self._current_stage = 0
        self.focus_area = ""
        self.specific_goal = ""
        self.progress = 0
        self.steps_taken = 0
        self.character_name = ""
        self.character_type = ""

    def set_focus_area(self, area):
        self.focus_area = area

    def set_specific_goal(self, goal):
        self.specific_goal = goal

    def set_character(self, name, char_type):
        self.character_name = name
        self.character_type = char_type

    def get_current_stage(self):
        return self.stages[self._current_stage]

    def process_choice(self, choice):
        self.steps_taken += 1
        return f"You chose to {choice.lower()}."

   def increment_progress(self, change_score):
        self.progress += change_score
        if self.progress < 0:
            self.progress = 0
        elif self.progress > 100:
            self.progress = 100
        
        # Check for stage advancement
        stage_threshold = 100 / len(self.stages)
        if self.progress >= (self._current_stage + 1) * stage_threshold:
            self.advance_stage()

    def advance_stage(self):
        if self._current_stage < len(self.stages) - 1:
            self._current_stage += 1
