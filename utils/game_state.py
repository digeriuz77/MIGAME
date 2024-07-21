class GameState:
    def __init__(self):
        self.stages = ["Pre-contemplation", "Contemplation", "Preparation", "Action", "Maintenance"]
        self._current_stage = 0
        self.focus_area = ""
        self.specific_goal = ""
        self.progress = 0
        self.steps_taken = 0

    def set_focus_area(self, area):
        self.focus_area = area

    def set_specific_goal(self, goal):
        self.specific_goal = goal

    def get_current_stage(self):
        return self.stages[self._current_stage]

    def process_choice(self, choice):
        self.steps_taken += 1
        return f"You chose to {choice.lower()}."

    def increment_progress(self):
        self.progress += 5
        if self.progress >= 100:
            self.progress = 100
        
        # Check for stage advancement
        if self.progress >= (self._current_stage + 1) * 20:
            self.advance_stage()

    def advance_stage(self):
        if self._current_stage < len(self.stages) - 1:
            self._current_stage += 1
