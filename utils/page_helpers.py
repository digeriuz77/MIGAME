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
                st.session_state[k] = v

def save_session(session_dir: Path):
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / (st.session_state.session_id + ".json")
    path.write_text(json.dumps(st.session_state.to_dict()))
    st.experimental_set_query_params(s=st.session_state.session_id)

def item_paginator(title, items, item_handler_fn, **kwargs):
    # Implement if needed for your app
    pass
