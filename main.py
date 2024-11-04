# main.py
import datetime
import io
import csv
from openai import OpenAI
import logging
import streamlit as st
from app.chatlog.chatlog_handler import insert_chat_log, initialize_chatlog_table
from sidebar import setup_sidebar
from app.db.database_connection import connect_to_db, get_app_description, initialize_db, update_app_description
from app.instructions.instructions_handler import get_latest_instructions
import uuid

st.title("CherGPT Basic")
app_description = get_app_description() or "Chatbot to support teaching and learning"
# Initialize session state for admin
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

# Set up the sidebar
setup_sidebar()

# Display the app description to all users
st.markdown(app_description, unsafe_allow_html=True)

initialize_chatlog_table()

# Admin panel actions
# handle_admin_actions()

# Chatbot interaction
# process_chat_input()


# Initialize variables for custom and existing instructions
custom_instructions = ""
existing_instructions = ""

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# Call the initialization function at the appropriate place in your application
initialize_db()



# Create update instructions
existing_instructions = get_latest_instructions()
custom_instructions = existing_instructions


custominstructions_area_height = 300


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append(
        {"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)


    # Prepend custom instructions to the conversation context for processing
    conversation_context = []
    if existing_instructions:
        conversation_context.append(
            {"role": "system", "content": custom_instructions})

    conversation_context += [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for response in client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=conversation_context,
            stream=True,
        ):
            full_response += (response.choices[0].delta.content or "")
            message_placeholder.markdown(full_response + "▌")
        insert_chat_log(prompt, full_response, st.session_state["conversation_id"])
        message_placeholder.markdown(full_response)

    # Append the assistant's response to the messages for display
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})
