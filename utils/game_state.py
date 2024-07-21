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
        self.choices_made = 0

    def set_focus_area(self, area):
        self.focus_area = area

    def get_current_stage(self):
        return self.stages[self.current_stage]

    def get_current_choices(self):
        choices = [
            "Learn more about the benefits of change",
            "Take a small step towards your goal",
            "Seek support from others",
            "Reflect on your progress"
        ]
        return choices

    def process_choice(self, choice):
        self.choices_made += 1
        
        if choice == "Learn more about the benefits of change":
            self.resources["Knowledge"] += random.randint(5, 15)
            self.resources["Motivation"] += random.randint(0, 10)
        elif choice == "Take a small step towards your goal":
            self.resources["Confidence"] += random.randint(5, 15)
            self.resources["Motivation"] += random.randint(0, 10)
        elif choice == "Seek support from others":
            self.resources["Support"] += random.randint(5, 15)
            self.resources["Motivation"] += random.randint(0, 10)
        elif choice == "Reflect on your progress":
            self.resources["Motivation"] += random.randint(5, 15)
            self.resources["Confidence"] += random.randint(0, 10)

        for resource in self.resources:
            self.resources[resource] = max(0, min(100, self.resources[resource]))

        if self.choices_made >= 3:
            self.check_stage_progress()
            self.choices_made = 0

        return f"You chose to {choice.lower()}."

    def check_stage_progress(self):
        if all(value > 70 for value in self.resources.values()):
            self.advance_stage()

    def advance_stage(self):
        if self.current_stage < len(self.stages) - 1:
            self.current_stage += 1
            return True
        return False
