"""
Main application file for CherGPT - A custom chat assistant.
Handles initialization and core application flow.
"""
import os
import streamlit as st
from openai import OpenAI
from app.chatlog.chatlog_handler import initialize_chatlog_table
from app.chat.chat_handler import (initialize_chat_state, display_chat_history,
                                   handle_chat_interaction)
from app.db.database_connection import (get_app_description, get_app_title,
                                        initialize_db)
from app.instructions.instructions_handler import get_latest_instructions
from sidebar import setup_sidebar

from app.auth.auth_handler import is_valid_email_domain, generate_magic_link, send_magic_link, verify_token


def main():
    # Check authentication
    if 'authenticated_email' not in st.session_state:
        st.session_state.authenticated_email = None

    # Check for shared session first
    session_id = st.query_params.get('session')
    if session_id:
        st.session_state.current_session = session_id
        
    # Then check authentication
    token = st.query_params.get('token', None)
    if token:
        email = verify_token(token)
        if email:
            st.session_state.authenticated_email = email
            st.query_params.clear()
            st.rerun()

    dev_mode = os.environ.get('DEVELOPMENT_MODE', 'false').lower() == 'true'
    
    # Only require login if no session is present
    if not st.session_state.authenticated_email and not session_id:
        st.title("CherGPT")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Login")
            email = st.text_input("Enter your MOE email")
            
            if dev_mode:
                if st.button("Dev Login"):
                    st.session_state.authenticated_email = email
                    st.rerun()
            else:
                if st.button("Send Login Link"):
                    if email and is_valid_email_domain(email):
                        magic_link = generate_magic_link(email)
                        if send_magic_link(email, magic_link):
                            st.success("Login link sent! Please check your email.")
                        else:
                            st.error("Failed to send login link.")
                    else:
                        st.error("Please use a valid MOE email address.")

        with col2:
            st.subheader("Your chat assistant ")
            st.write("for teaching and learning")
            st.write("✅ custom prompts and chatlog export")
            st.write("❌ custom prompts and chatlog export")
        return

    # Initialize app state
    app_title = get_app_title()
    app_description = get_app_description(
    ) or "Chatbot to support teaching and learning"
    st.title(app_title)

    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False

    # Set up components
    setup_sidebar()
    st.markdown(app_description, unsafe_allow_html=True)
    initialize_db()
    initialize_chatlog_table()
    initialize_chat_state()

    # Initialize chat client and settings
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    # Check for shared session
    session_id = st.query_params.get('session')
    if session_id:
        session_prompt = get_session_prompt(session_id)
        if session_prompt:
            existing_instructions = session_prompt
        else:
            existing_instructions = get_latest_instructions()
    else:
        existing_instructions = get_latest_instructions()

    # Display and handle chat
    display_chat_history()
    handle_chat_interaction(client, existing_instructions)


if __name__ == "__main__":
    main()
