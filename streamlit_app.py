```python
import streamlit as st
from game_logic import GameState
from ai_interface import AIInterface
from ui_components import start_view, game_view, end_view
from utils import init_state, reset_state

def main():
    """
    Main function to run the Hero's Journey app.
    """
    st.set_page_config("Hero's Journey", layout="wide")
    
    init_state()
    
    if not st.session_state.journey_in_progress:
        start_view()
    elif st.session_state.game_state.is_journey_complete():
        end_view()
    else:
        game_view()
    
    if st.button("Start a New Journey"):
        reset_state()
        st.rerun()

if __name__ == "__main__":
    main()
