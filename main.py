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

hide_decoration_bar_style = '''
    <style>
        header {visibility: hidden;}
    </style>
'''
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)


def main():
    # Check authentication
    if 'authenticated_email' not in st.session_state:
        st.session_state.authenticated_email = None

    # Handle both /verify and direct token parameter
    token = st.query_params.get('token', None)
    if not token and 'verify' in st.query_params:
        token = st.query_params.get('verify', None)

    if token:
        email = verify_token(token)
        if email:
            st.session_state.authenticated_email = email
            st.query_params.clear()
            st.rerun()

    dev_mode = os.environ.get('DEVELOPMENT_MODE', 'false').lower() == 'true'

    # Check for public chat link
    public_chat_id = st.query_params.get('chat_id', None)
    if public_chat_id:
        st.session_state.authenticated_email = "public_user"
        existing_instructions = get_latest_instructions()
        st.title("CherGPT Public Chat")
        initialize_chat_state()
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        display_chat_history()
        handle_chat_interaction(client, existing_instructions)
        return

    if not st.session_state.authenticated_email:
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&family=Montserrat:wght@400;600&display=swap');

        * {
            font-family: 'Montserrat', sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Space Grotesk', sans-serif !important;
            color: white !important;
        }

        div, p, span, input, button, textarea, .element-container {
            font-family: 'Montserrat', sans-serif !important;
            color: white !important;
        }
        </style>
        """,
                    unsafe_allow_html=True)

        import streamlit_shadcn_ui as ui
        st.title("CherGPT")
        st.caption("Your chat assistant for teaching and learning")

        with ui.card(key="card1"):
            ui.element("span",
                       children=["Email"],
                       className="text-gray-400 text-sm font-m")
            email_input = ui.element("input",
                                     key="email_input",
                                     placeholder="@moe, @school or @string.sg")
    if dev_mode:
        if st.button("Dev Login", key="dev_login", use_container_width=True):
            email = email_input.value
            if email and isinstance(email, str) and email.strip():
                st.session_state.authenticated_email = email.strip()
                st.session_state.email_input = email.strip()
                st.rerun()
            else:
                st.error("Please enter an email address")
    else:
        if st.button("Send Magic Link",
                     key="send_link",
                     help="Send login link to the provided email address",
                     use_container_width=True):
            if email and is_valid_email_domain(email):
                magic_link = generate_magic_link(email)
                if magic_link and send_magic_link(email, magic_link):
                    st.success("Login link sent! Please check your email.")
                else:
                    st.error("Failed to send login link.")
            else:
                st.error("Please use a valid MOE email address.")
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
    existing_instructions = get_latest_instructions()

    # Display and handle chat
    display_chat_history()
    handle_chat_interaction(client, existing_instructions)


if __name__ == "__main__":
    main()
