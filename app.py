# app.py

import streamlit as st
import random
import time
import plotly.graph_objects as go
from openai import OpenAI

# Configuration
st.set_page_config(page_title="Choose Your Own Plan - Coaching Game", layout="wide")

# OpenAI setup
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Resource Management
class ResourceManager:
    def __init__(self):
        self.resources = {
            "Motivation": 50,
            "Self-efficacy": 50,
            "Knowledge": 50,
            "Support": 50
        }
        self.history = {resource: [] for resource in self.resources}

    def update_from_interaction(self, user_input, ai_response):
        for resource in self.resources:
            change = random.randint(-5, 10)
            self.update_resource(resource, change)

    def update_resource(self, resource, change):
        if resource in self.resources:
            self.resources[resource] = max(0, min(100, self.resources[resource] + change))
            self.history[resource].append(self.resources[resource])

    def get_resources(self):
        return self.resources

    def get_resource_history(self):
        return self.history

# Event Management
class EventManager:
    def __init__(self):
        self.events = [
            ("You faced an unexpected challenge.", lambda journey: journey.resources.update_resource("Motivation", -5)),
            ("You had a moment of clarity about your goals.", lambda journey: journey.resources.update_resource("Self-efficacy", 10)),
            ("You learned a new coping strategy.", lambda journey: journey.resources.update_resource("Knowledge", 5)),
            ("A friend offered support.", lambda journey: journey.resources.update_resource("Support", 10)),
        ]

    def check_for_events(self, journey):
        if random.random() < 0.2:  # 20% chance of an event occurring
            event, action = random.choice(self.events)
            action(journey)
            return event
        return None

# Milestone Management
class MilestoneManager:
    def __init__(self):
        self.milestones = [
            ("You've made significant progress!", lambda journey: sum(journey.resources.get_resources().values()) > 250),
            ("You've been consistent with your new habits.", lambda journey: journey.interaction_count > 10),
            ("You've inspired others with your progress.", lambda journey: journey.resources.get_resources()["Support"] > 75),
        ]
        self.achieved_milestones = set()

    def check_for_milestones(self, journey):
        achieved = []
        for milestone, condition in self.milestones:
            if milestone not in self.achieved_milestones and condition(journey):
                self.achieved_milestones.add(milestone)
                achieved.append(milestone)
        return achieved

    def should_advance_stage(self, journey):
        return all(value > 70 for value in journey.resources.get_resources().values())

# Milestone Decisions
class MilestoneDecision:
    def __init__(self, question, options, outcomes):
        self.question = question
        self.options = options
        self.outcomes = outcomes

    def present(self):
        st.write(self.question)
        choice = st.radio("Choose an option:", self.options)
        if st.button("Confirm"):
            return self.outcomes[self.options.index(choice)]

# AI Character
class AICharacter:
    def __init__(self, name, base_personality):
        self.name = name
        self.base_personality = base_personality
        self.traits = character_traits.get(name.lower(), ["supportive"])  # Default trait if not found
        self.mood = 0  # Range from -1 (negative) to 1 (positive)

    def generate_response(self, user_input, change_score, current_topic, conversation_history):
        self.mood = max(-1, min(1, self.mood + (change_score - 50) / 100))
        
        if self.mood > 0.5:
            current_personality = f"{self.base_personality}, encouraging"
        elif self.mood < -0.5:
            current_personality = f"{self.base_personality}, concerned"
        else:
            current_personality = self.base_personality
        
        relevant_trait = random.choice(self.traits)  # Simplified trait selection
        
        prompt = self._construct_prompt(user_input, current_personality, relevant_trait, current_topic, change_score, conversation_history)
        
        return get_ai_response(prompt)

    # ... rest of the class remains the same

    def _construct_prompt(self, user_input, current_personality, relevant_trait, current_topic, change_score, conversation_history):
        prompt = f"You are a {current_personality} {self.name} using motivational interviewing techniques. "
        prompt += f"Your current mood is {'positive' if self.mood > 0 else 'negative' if self.mood < 0 else 'neutral'}. "
        prompt += f"A relevant trait of yours is: {relevant_trait}. "
        prompt += f"The current topic is {current_topic}, and the user's change score is {change_score}/100. "
        prompt += f"Recent conversation history: {conversation_history[-3:]}. "
        prompt += f"Respond to '{user_input}' using OARS techniques (Open questions, Affirmations, Reflections, Summaries). "
        prompt += "Avoid advice-giving or judgement. "
        prompt += f"If the change score is below 30, focus on developing discrepancy and expressing empathy. "
        prompt += f"If the change score is between 30 and 70, focus on eliciting change talk and supporting self-efficacy. "
        prompt += f"If the change score is above 70, focus on affirming positive change and planning next steps. "
        return prompt

# Change Journey
class ChangeJourney:
    def __init__(self):
        self.stages = ["Pre-contemplation", "Contemplation", "Preparation", "Action", "Maintenance"]
        self.current_stage = 0
        self.resources = ResourceManager()
        self.events = EventManager()
        self.milestones = MilestoneManager()
        self.interaction_count = 0
        self.conversation_starters = conversation_starters
        self.topics = list(topics)
        self.current_topic = random.choice(self.topics)
        self.change_score = 50  # Start at midpoint
        self.current_character = AICharacter("Coach", "supportive")
        self.conversation_history = []

    def process_interaction(self, user_input):
        if not self.check_for_milestone_decision():
            change_talk_score = self.analyze_change_talk(user_input)
            self.change_score = max(0, min(100, self.change_score + change_talk_score))
            
            ai_response = self.current_character.generate_response(
                user_input, 
                self.change_score, 
                self.current_topic, 
                self.conversation_history
            )
            
            self.conversation_history.append((user_input, ai_response))
            
            if random.random() < 0.2:  # 20% chance to change topic
                self.current_topic = random.choice(self.topics)
            
            self.interaction_count += 1
            self.resources.update_from_interaction(user_input, ai_response)
            self.events.check_for_events(self)
            self.milestones.check_for_milestones(self)
            self.check_stage_progress()
            return ai_response
        return None

    def check_for_milestone_decision(self):
        if self.current_stage == 1 and self.resources.get_resources()["Motivation"] > 60:
            decision = MilestoneDecision(
                "You're feeling more motivated. What's your next step?",
                ["A. Set a specific goal", "B. Learn more about the change process", "C. Talk to someone about your plans"],
                [
                    lambda: self.resources.update_resource("Self-efficacy", 10),
                    lambda: self.resources.update_resource("Knowledge", 10),
                    lambda: self.resources.update_resource("Support", 10)
                ]
            )
            outcome = decision.present()
            if outcome:
                outcome()
                return True
        return False

    def check_stage_progress(self):
        if self.milestones.should_advance_stage(self):
            self.advance_stage()

    def advance_stage(self):
        if self.current_stage < len(self.stages) - 1:
            self.current_stage += 1
            return True
        return False

    def is_complete(self):
        return self.current_stage == len(self.stages) - 1

    def get_progress(self):
        return self.current_stage / (len(self.stages) - 1)

    def get_current_stage(self):
        return self.stages[self.current_stage]

    def analyze_change_talk(self, user_input):
        # This function would use NLP to analyze the user's input for change talk
        # For now, let's return a random score between -5 and 5
        return random.randint(-5, 5)

# OpenAI Interface
def get_ai_response(prompt):
    assistant_id = st.secrets["ASSISTANT_ID"]
    
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )
    
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id
    )
    
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )
        if run_status.status == 'completed':
            break
        elif run_status.status == 'failed':
            st.error(f"Run failed: {run_status.last_error}")
            return None
        time.sleep(1)
    
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    return messages.data[0].content[0].text.value

def stream_response(response):
    full_response = ""
    for chunk in response.split():
        full_response += chunk + " "
        yield full_response

# UI Components
def render_progress_bar(journey):
    st.progress(journey.get_progress())
    st.write(f"Current Stage: {journey.get_current_stage()}")

def render_resource_charts(journey):
    resources = journey.resources.get_resources()
    history = journey.resources.get_resource_history()
    
    # Current resources bar chart
    fig_current = go.Figure(data=[go.Bar(x=list(resources.keys()), y=list(resources.values()))])
    fig_current.update_layout(title_text='Current Resources')
    st.plotly_chart(fig_current)
    
    # Resource history line chart
    fig_history = go.Figure()
    for resource, values in history.items():
        fig_history.add_trace(go.Scatter(y=values, name=resource))
    fig_history.update_layout(title_text='Resource History')
    st.plotly_chart(fig_history)

# Global variables
character_traits = {
    "coach": ["empathetic", "motivating", "patient", "knowledgeable"]
}

conversation_starters = [
    "What brings you here today?",
    "How do you feel about making a change in your life?",
    "What would you like to accomplish?"
]

topics = ["health", "relationships", "career", "personal growth"]

# Main application
def main():
    st.title("Choose Your Own Plan - Coaching Game")

    if "journey" not in st.session_state:
        st.session_state.journey = ChangeJourney()
        starter = random.choice(conversation_starters) if conversation_starters else "Welcome to your coaching session. How can I assist you today?"
        ai_response = st.session_state.journey.current_character.generate_response(
            starter, 50, st.session_state.journey.current_topic, []
        )
        st.session_state.journey.conversation_history.append((starter, ai_response))

    journey = st.session_state.journey

    render_progress_bar(journey)

    for coach_input, user_response in journey.conversation_history:
        st.text(f"Coach: {coach_input}")
        st.text(f"You: {user_response}")

    user_input = st.text_input("Your response:")
    if user_input:
        ai_response = journey.process_interaction(user_input)
        if ai_response:
            st.text(f"Coach: {ai_response}")

    render_resource_charts(journey)

    if st.button("Start Over"):
        st.session_state.journey = ChangeJourney()
        st.experimental_rerun()

if __name__ == "__main__":
    main()
