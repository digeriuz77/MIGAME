import json
from pathlib import Path
import streamlit as st

def load_session(session_dir: Path):
    query_session = st.experimental_get_query_params().get("s")
    if query_session:
        query_session = query_session[0]
        path = session_dir / (query_session + ".json")
        if path.exists():
            loaded_session_data = json.loads(path.read_text())
            for k, v in loaded_session_data.items():
                if k not in st.session_state:
                    st.session_state[k] = v

def save_session(session_dir: Path):
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / (st.session_state.session_id + ".json")
    session_data = {k: v for k, v in st.session_state.items() if isinstance(v, (str, int, float, bool, list, dict))}
    path.write_text(json.dumps(session_data))
    st.experimental_set_query_params(s=st.session_state.session_id)

def item_paginator(title, items, item_handler_fn, **kwargs):
    st.title(title)
    
    if "page_number" not in st.session_state:
        st.session_state.page_number = 0

    def next_page():
        st.session_state.page_number += 1

    def prev_page():
        st.session_state.page_number -= 1

    col1, col2, col3, _ = st.columns([0.1, 0.1, 0.1, 0.7])

    if st.session_state.page_number < len(items) - 1:
        col3.button(">", on_click=next_page)
    else:
        col3.write("")  # this makes the empty column show up on mobile

    if st.session_state.page_number > 0:
        col1.button("<", on_click=prev_page)
    else:
        col1.write("")  # this makes the empty column show up on mobile

    col2.write(f"{1+st.session_state.page_number}/{len(items)}")

    item_handler_fn(items[st.session_state.page_number], **kwargs)
