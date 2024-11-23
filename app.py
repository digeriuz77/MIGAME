import streamlit as st
from openai import OpenAI
from PIL import Image
from io import BytesIO
import base64
import os
from fpdf import FPDF
import time
import hashlib
import json
from functools import lru_cache

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))
if not st.secrets.get("OPENAI_API_KEY"):
    st.error("Please set your OpenAI API key in Streamlit secrets.")
    st.stop()

# Initialize session state for token tracking
if 'token_usage' not in st.session_state:
    st.session_state.token_usage = {
        'total_prompt_tokens': 0,
        'total_completion_tokens': 0,
        'total_cost': 0,
        'image_generations': 0
    }

# Initialize game state if not exists
if 'game_state' not in st.session_state:
    st.session_state['game_state'] = {
        'stages': [
            "The Ordinary World", "The Call to Adventure", "Refusal of the Call",
            "Meeting the Mentor", "Crossing the Threshold", "Tests, Allies, and Enemies",
            "Approach to the Inmost Cave", "The Ordeal", "Reward (Seizing the Sword)",
            "The Road Back", "Resurrection", "Return with the Elixir"
        ],
        'current_stage': 0,
        'character_name': "",
        'character_type': "",
        'distinguishing_feature': "",
        'challenge': "",
        'specific_goal': "",
        'steps_taken': 0,
        'art_style': "Digital painting",
        'story_elements': [],
        'awaiting_choice': True,
        'current_choices': [],
        'age': 10,
        'title': "",
        'cover_generated': False,
        'cover_image': "",
        'image_seed': None
    }

def inject_custom_css():
    """Inject custom CSS for magical animations"""
    st.markdown("""
        <style>
        @keyframes sparkle {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        
        @keyframes fadeInScale {
            0% { 
                opacity: 0;
                transform: scale(0.95);
            }
            100% { 
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .magical-text {
            background: linear-gradient(
                90deg,
                #ffd700,
                #ff69b4,
                #87ceeb,
                #ffd700
            );
            background-size: 300% 300%;
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: sparkle 4s ease infinite;
            font-size: 1.2em;
            padding: 10px;
            text-align: center;
        }
        
        .story-text {
            animation: fadeInScale 1s ease-out;
            padding: 20px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            margin: 10px 0;
        }
        
        .magical-image {
            animation: fadeInScale 1s ease-out;
            border-radius: 15px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            animation: float 3s ease-in-out infinite;
        }
        
        .magical-loader {
            width: 80px;
            height: 80px;
            position: relative;
        }
        
        .magical-loader:before,
        .magical-loader:after {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: linear-gradient(45deg, #ff69b4, #87ceeb, #ffd700);
            animation: pulse 2s ease-out infinite;
        }
        
        .magical-loader:after {
            animation-delay: -1s;
        }
        
        @keyframes pulse {
            0% {
                transform: scale(0);
                opacity: 1;
            }
            100% {
                transform: scale(1.5);
                opacity: 0;
            }
        }
        
        .choice-button {
            transition: all 0.3s ease;
            border-radius: 10px;
            border: 2px solid transparent;
            background: linear-gradient(45deg, #ff69b4, #87ceeb);
            background-size: 200% 200%;
            animation: sparkle 4s ease infinite;
            color: white;
            padding: 10px 20px;
            margin: 5px;
            cursor: pointer;
            width: 100%;
            text-align: left;
        }
        
        .choice-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .input-container {
            animation: fadeInScale 0.5s ease-out;
            margin: 10px 0;
            padding: 15px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.05);
        }
        </style>
    """, unsafe_allow_html=True)

def update_token_usage(usage):
    """Update token usage statistics"""
    st.session_state.token_usage['total_prompt_tokens'] += usage.prompt_tokens
    st.session_state.token_usage['total_completion_tokens'] += usage.completion_tokens
    st.session_state.token_usage['total_cost'] += (
        (usage.prompt_tokens * 0.01 / 1000) +  # Adjust costs as needed
        (usage.completion_tokens * 0.02 / 1000)
    )

@st.cache_data(ttl=3600)
def generate_scenario(game_state, is_first_scenario=False):
    """Generate a new scenario with caching"""
    character_select = f"{game_state['character_name']} the {game_state['character_type']} with {game_state['distinguishing_feature']}"
    current_stage = game_state['stages'][game_state['current_stage']]
    
    # Compile story so far
    story_so_far = "\n".join(
        f"{content}" if element_type == 'SCENARIO' else f"Choice made: {content}"
        for element_type, content in game_state['story_elements']
        if element_type in ('SCENARIO', 'CHOICE')
    )

    # Age-appropriate adjustments
    if game_state['age'] <= 7:
        complexity = "Use simple words and short sentences suitable for a 5-7 year old."
        num_choices = 2
    elif game_state['age'] <= 10:
        complexity = "Use language appropriate for an 8-10 year old."
        num_choices = 3
    else:
        complexity = "Use language appropriate for an 11-14 year old."
        num_choices = 3

    prompt = (
        f"{'Create an opening scenario' if is_first_scenario else 'Continue the story'} "
        f"for {character_select} in "
        f"{'their ordinary world' if is_first_scenario else current_stage}, "
        f"facing the challenge of {game_state['challenge']} "
        f"with the goal of {game_state['specific_goal']}.\n\n"
        f"Story so far:\n{story_so_far}\n\n{complexity}\n\n"
        f"Provide a scenario description followed by {num_choices} choices.\n"
        f"Format exactly as:\n\nScenario description\n\n" + 
        "\n".join(f"{i+1}. Choice {i+1}" for i in range(num_choices))
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a master storyteller crafting an engaging hero's journey for children."},
                {"role": "user", "content": prompt}
            ]
        )
        update_token_usage(response.usage)
        content = response.choices[0].message.content
        return process_scenario_response(content, num_choices)
    except Exception as e:
        st.error(f"Error in generating scenario: {str(e)}")
        return None, []

def process_scenario_response(response, num_choices=3):
    """Process the scenario response into parts"""
    parts = response.strip().split("\n\n")
    scenario = parts[0].strip()
    choices = []
    if len(parts) > 1:
        choices = [choice.strip() for choice in parts[1].split("\n") if choice.strip()]
        choices = choices[:num_choices]
    return scenario, choices

@st.cache_data(ttl=3600)
def generate_image(scenario, character_select, art_style):
    """Generate an image with shorter, focused prompt"""
    prompt = (
        f"A child-friendly illustration in {art_style} style: "
        f"{character_select}, shown in full body view, "
        f"in scene: {scenario}. "
        f"Maintain consistent character appearance throughout the story."
    )

    try:
        response = client.images.generate(
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="b64_json"
        )
        
        st.session_state.token_usage['image_generations'] += 1
        st.session_state.token_usage['total_cost'] += 0.04
        
        return response.data[0].b64_json
    except Exception as e:
        st.error(f"Error in generating image: {str(e)}")
        return None

def display_magical_loading(placeholder):
    """Display a magical loading animation"""
    placeholder.markdown("""
        <div class="loading-container">
            <div class="magical-loader"></div>
            <div class="magical-text">✨ Weaving your story magic... ✨</div>
        </div>
    """, unsafe_allow_html=True)

def display_scenario_text(scenario, placeholder=None):
    """Display scenario text with magical animation"""
    if not placeholder:
        placeholder = st.empty()
    
    words = scenario.split()
    full_text = ""
    for word in words:
        full_text += word + " "
        placeholder.markdown(f"""
            <div class="story-text">
                <span class="magical-text">{full_text}</span>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(0.05)

def display_image_with_magical_loading(image_b64):
    """Display image with magical loading effects"""
    placeholder = st.empty()
    display_magical_loading(placeholder)
    
    try:
        time.sleep(1)
        placeholder.markdown(f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{image_b64}"
                     class="magical-image"
                     style="max-width: 100%; height: auto;">
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        placeholder.error(f"✨ The magic fizzled a bit: {str(e)} ✨")

def display_usage_stats():
    """Display token usage and cost statistics"""
    st.sidebar.subheader("✨ Magic Usage ✨")
    st.sidebar.markdown("""
        <div class="magical-text">
            <p>Magical Energy Spent:</p>
            <ul>
                <li>Story Tokens: {}</li>
                <li>Response Tokens: {}</li>
                <li>Images Created: {}</li>
                <li>Total Cost: ${:.4f}</li>
            </ul>
        </div>
    """.format(
        st.session_state.token_usage['total_prompt_tokens'],
        st.session_state.token_usage['total_completion_tokens'],
        st.session_state.token_usage['image_generations'],
        st.session_state.token_usage['total_cost']
    ), unsafe_allow_html=True)

def start_view():
    """Initial view for story setup"""
    inject_custom_css()
    
    st.markdown("<h1 class='magical-text'>✨ Create Your Magical Story ✨</h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='input-container'>", unsafe_allow_html=True)
        title = st.text_input("📚 Story Title", value=st.session_state.game_state.get('title', ''))
        character_name = st.text_input("🦸‍♂️ Hero's Name", value=st.session_state.game_state['character_name'])
        character_type = st.text_input("🎭 Hero's Type (e.g., dragon, unicorn)", value=st.session_state.game_state['character_type'])
        distinguishing_feature = st.text_input("✨ Distinguishing Feature", value=st.session_state.game_state['distinguishing_feature'])
        art_style = st.selectbox("🎨 Art Style", ["Digital painting", "Watercolor", "Oil painting", "Pencil sketch"])
        age = st.number_input("🎈 Age", min_value=5, max_value=14, value=st.session_state.game_state['age'])
        challenge = st.text_input("⚔️ Challenge", value=st.session_state.game_state['challenge'])
        specific_goal = st.text_input("🎯 Specific Goal", value=st.session_state.game_state['specific_goal'])
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("✨ Begin Your Adventure ✨"):
            if not all([title, character_name, character_type, challenge, specific_goal]):
                st.warning("🌟 Please fill in all the magical details! 🌟")
                return
                
            st.session_state.game_state.update({
                'title': title,
                'character_name': character_name,
                'character_type': character_type,
                'distinguishing_feature': distinguishing_feature,
                'art_style': art_style,
                'challenge': challenge,
                'specific_goal': specific_goal,
                'age': age,
                'awaiting_choice': True
            })
            st.rerun()
            
def adventure_view():
    """Main adventure view with proper story progression"""
    game_state = st.session_state['game_state']
    
    st.title(f"✨ {game_state['title']} ✨")
    st.write(f"**Current Stage:** {game_state['stages'][game_state['current_stage']]}")
    st.write(f"**Your Goal:** {game_state['specific_goal']}")

    # Generate new scenario and choices only when needed
    if game_state['awaiting_choice']:
        scenario, choices = generate_scenario(
            game_state,
            is_first_scenario=(len(game_state['story_elements']) == 0)
        )
        
        if scenario and choices:
            # Add new scenario
            game_state['story_elements'].append(('SCENARIO', scenario))
            
            # Generate and add image
            image_b64 = generate_image(
                scenario,
                f"{game_state['character_name']} the {game_state['character_type']}",
                game_state['art_style']
            )
            if image_b64:
                game_state['story_elements'].append(('IMAGE', image_b64))
            
            # Set up choices for user
            game_state['current_choices'] = choices
            game_state['awaiting_choice'] = False
            st.session_state['game_state'] = game_state
            st.rerun()

    # Display current story and choices
    display_story()
    display_choices()

    # Check for story completion
    if game_state['current_stage'] == len(game_state['stages']) - 1:
        st.success("🎉 Congratulations! You've completed your adventure.")
        download_story()


def display_story():
    """Display story elements without overwriting"""
    game_state = st.session_state['game_state']
    
    st.markdown("---")
    st.subheader("📖 Story So Far")

    # Display all story elements in sequence
    for element_type, content in game_state['story_elements']:
        if element_type == 'SCENARIO':
            st.markdown(f"""
                <div class="story-text">
                    <span class="magical-text">{content}</span>
                </div>
            """, unsafe_allow_html=True)
        elif element_type == 'IMAGE':
            st.markdown(f"""
                <div style="text-align: center;">
                    <img src="data:image/png;base64,{content}"
                         class="magical-image"
                         style="max-width: 100%; height: auto;">
                </div>
            """, unsafe_allow_html=True)
        elif element_type == 'CHOICE':
            st.markdown(f"""
                <div class="story-text">
                    <em>You chose:</em> {content}
                </div>
            """, unsafe_allow_html=True)

def display_choices():
    """Display interactive choices with proper styling"""
    game_state = st.session_state['game_state']
    
    if game_state['current_choices']:
        st.markdown("---")
        st.markdown("<h3 class='magical-text'>🌟 What happens next?</h3>", unsafe_allow_html=True)
        
        # Create columns for better choice layout
        cols = st.columns(len(game_state['current_choices']))
        
        for i, (choice, col) in enumerate(zip(game_state['current_choices'], cols)):
            with col:
                if st.button(
                    choice,
                    key=f"choice_{i}",
                    use_container_width=True,
                ):
                    # Update game state with the chosen path
                    game_state['story_elements'].append(('CHOICE', choice))
                    game_state['current_stage'] = min(
                        game_state['current_stage'] + 1,
                        len(game_state['stages']) - 1
                    )
                    game_state['awaiting_choice'] = True
                    game_state['current_choices'] = []  # Clear current choices
                    st.session_state['game_state'] = game_state
                    st.rerun()

def download_story():
    game_state = st.session_state.game_state  # Get reference to game state
    
    if st.button("📥 Download Your Story as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 24)

        # Add cover page with title and image
        title = game_state.get('title', f"{game_state['character_name']}'s Adventure")
        pdf.multi_cell(0, 20, title, align='C')

        if 'cover_image' in game_state:
            image_data = base64.b64decode(game_state['cover_image'])
            image = Image.open(BytesIO(image_data))
            image_path = f"cover_image_{os.getpid()}.png"
            image.save(image_path)
            pdf.image(image_path, x=10, w=190)
            os.remove(image_path)

        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for element_type, content in game_state['story_elements']:
            if element_type == 'SCENARIO':
                pdf.multi_cell(0, 10, content)
            elif element_type == 'CHOICE':
                pdf.multi_cell(0, 10, f"Decision: {content}")
            elif element_type == 'IMAGE':
                image_data = base64.b64decode(content)
                image = Image.open(BytesIO(image_data))
                image_path = f"temp_image_{os.getpid()}.png"
                image.save(image_path)
                pdf.image(image_path, x=10, w=190)
                os.remove(image_path)

        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        st.download_button("Download PDF", data=pdf_output, file_name=f"{title}.pdf", mime="application/pdf")

# Main application flow
if not st.session_state['game_state']['character_name']:
    start_view()
else:
    adventure_view()
