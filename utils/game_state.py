import random

class GameState:
    def __init__(self):
        self.stages = ["Pre-contemplation", "Contemplation", "Preparation", "Action", "Maintenance"]
        self.current_stage = 0
        self.focus_area = ""
        self.resources = {
            "Motivation": 50,
            "Confidence": 50,
            "Knowledge": 50,
            "Support": 50
        }

    def set_focus_area(self, area):
        self.focus_area = area

    def get_current_stage(self):
        return self.stages[self.current_stage]

    def get_current_choices(self):
        # This would be more sophisticated in a real implementation
        return [
            "Learn more about the benefits of change",
            "Take a small step towards your goal",
            "Seek support from others",
            "Reflect on your progress"
        ]

    def process_choice(self, choice):
        # Update resources based on choice
        for resource in self.resources:
            self.resources[resource] += random.randint(-5, 10)
            self.resources[resource] = max(0, min(100, self.resources[resource]))

        # Check for stage progression
        if all(value > 70 for value in self.resources.values()):
            self.advance_stage()

        # Generate new scenario based on choice
        return f"You chose to {choice.lower()}. [AI-generated continuation would go here]"

    def advance_stage(self):
        if self.current_stage < len(self.stages) - 1:
            self.current_stage += 1
