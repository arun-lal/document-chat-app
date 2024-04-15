# Adapted from https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps#build-a-simple-chatbot-gui-with-streaming

import os
import tempfile
from llama_index.core import Settings
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import PromptTemplate
from llama_index.llms.cohere import Cohere
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.postprocessor.cohere_rerank import CohereRerank

import streamlit as st

from src.helper import initialize_session_state
from src.utils import reset_chat, display_pdf
from src.prompt import *


class DocumentChatApp:
    """Document Chat App"""

    def __init__(self):
        initialize_session_state()
        self.session_id = st.session_state.id
        self.client = None
        self.api_key = None
        self.file_cache = st.session_state.file_cache
        self.query_engine = None

    def load_llm_model(self):
        """Function to load the LLM model"""
        return Cohere(api_key=self.api_key, model="command")

    def load_embed_model(self):
        """Function to load the embedding model"""
        return CohereEmbedding(
            cohere_api_key=self.api_key,
            model_name="embed-english-v3.0",
            input_type="search_query",
        )
    
    def create_query_engine(self, docs):
        """Function to create a query engine for the uploaded documents"""
        # Setup llm & embedding model
        llm = self.load_llm_model()
        embed_model = self.load_embed_model()

        # Creating an index over loaded data
        Settings.embed_model = embed_model
        index = VectorStoreIndex.from_documents(docs, show_progress=True)

        # Create a cohere reranker 
        cohere_rerank = CohereRerank(api_key=self.api_key)
        Settings.llm = llm
        query_engine = index.as_query_engine(streaming=True, node_postprocessors=[cohere_rerank])
        
        prompt = prompt_template
        qa_prompt_tmpl = PromptTemplate(prompt)
        query_engine.update_prompts({"response_synthesizer:text_qa_template": qa_prompt_tmpl})
        
        return query_engine

    def main(self):
        """ main function"""
        with st.sidebar:
            st.header("Set your Cohere API Key")
            st.link_button("get one @ Cohere 🔗", "https://dashboard.cohere.com/api-keys")
            self.api_key = st.text_input("password", type="password", label_visibility="collapsed")

            uploaded_file = st.file_uploader("Choose your `.pdf` file", type="pdf")

            if uploaded_file and self.api_key:
                st.session_state.uploaded_file = uploaded_file
                try:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        file_path = os.path.join(temp_dir, uploaded_file.name)
                        
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getvalue())
                        
                        file_key = f"{self.session_id}-{uploaded_file.name}"
                        st.write("Indexing your document...")

                        if file_key not in st.session_state.get('file_cache', {}):

                            if os.path.exists(temp_dir):
                                    loader = SimpleDirectoryReader(
                                        input_dir = temp_dir,
                                        required_exts=[".pdf"],
                                        recursive=True
                                    )
                            else:    
                                st.error('Could not find the file you uploaded, please check again...')
                                st.stop()
                            
                            docs = loader.load_data()

                            query_engine = self.create_query_engine(docs)
                            
                            st.session_state.file_cache[file_key] = query_engine
                        else:
                            query_engine = st.session_state.file_cache[file_key]

                        # Inform the user that the file is processed and Display the PDF uploaded
                        st.success("Ready to Chat!")
                        # display_pdf(uploaded_file)

                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.stop()     

        col1, col2 = st.columns([2, 1])

        with col1:
            st.header(f"DocumentChatApp- Chat with your document")
            uploaded_file = st.session_state.get('uploaded_file')
            if uploaded_file:
                display_pdf(uploaded_file)

        with col2:
            st.button("Clear ↺", on_click=reset_chat)

            # Initialize chat history
            if "messages" not in st.session_state:
                reset_chat()


            # Display chat messages from history on app rerun
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])


            # Accept user input
            if prompt := st.chat_input("What's up?"):
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                # Display user message in chat message container
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    # Simulate stream of response with milliseconds delay
                    streaming_response = query_engine.query(prompt)
                    
                    for chunk in streaming_response.response_gen:
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")

                    # full_response = query_engine.query(prompt)

                    message_placeholder.markdown(full_response)
                    # st.session_state.context = ctx

                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": full_response})


if __name__ == "__main__":
    app = DocumentChatApp()
    app.main()