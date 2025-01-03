
import streamlit as st
from openai import OpenAI
from app.chatlog.chatlog_handler import initialize_chatlog_table
from app.chat.chat_handler import initialize_chat_state, display_chat_history, handle_chat_interaction
from sidebar import setup_sidebar
from app.db.database_connection import get_app_description, get_app_title, initialize_db
from app.instructions.instructions_handler import get_latest_instructions

def main():
    # Initialize app state
    app_title = get_app_title()
    app_description = get_app_description() or "Chatbot to support teaching and learning"
    st.title(app_title)

    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False

    # Set up components
    setup_sidebar()
    st.markdown(app_description, unsafe_allow_html=True)
    initialize_db()
    initialize_chatlog_table()
    initialize_chat_state()

    # Initialize chat components
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    existing_instructions = get_latest_instructions()
    
    # Display and handle chat
    display_chat_history()
    handle_chat_interaction(client, existing_instructions)

if __name__ == "__main__":
    main()
