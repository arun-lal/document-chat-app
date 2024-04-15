import base64
import gc
import streamlit as st


def reset_chat():
    """reset chat"""
    st.session_state.messages = []
    st.session_state.context = None
    gc.collect()

def display_pdf(file):
    """display pdf"""
    if file is not None:
        st.markdown("### PDF Preview")
        base64_pdf = base64.b64encode(file.read()).decode("utf-8")

        # Embedding PDF in HTML
        pdf_display = f"""<iframe src="data:application/pdf;base64,{base64_pdf}" width="800" height="100%" type="application/pdf"
                            style="height:100vh; width:100%">
                        </iframe>"""
        
        # Displaying File
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.warning("No PDF file uploaded.")
