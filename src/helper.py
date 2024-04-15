import uuid
import streamlit as st

def initialize_session_state():
    """initialize_session_state"""
    if "id" not in st.session_state:
        st.session_state.id = uuid.uuid4()
    if "file_cache" not in st.session_state:
        st.session_state.file_cache = {}
