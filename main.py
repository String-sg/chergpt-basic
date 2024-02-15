from openai import OpenAI
import streamlit as st
from app.chatlog.chatlog_handler import insert_chat_log
from app.db.database_connection import initialize_db
from sidebar import setup_sidebar
# from app.db.database_connection import drop_instructions_table, initialize_db
from app.instructions.instructions_handler import get_latest_instructions

# Title for now, no need subtitles. Can consider loading title/ subtitle from DB and enable users to edit
st.title("CherGPT Basic")

# Set up the sidebar and initialize DB
if 'db_initialized' not in st.session_state:
    initialize_db()
    st.session_state['db_initialized'] = True
    
# if st.button("Drop Instructions Table"):
#    drop_instructions_table()

# Ensure get_latest_instructions is called once and stored
def setup_app():
    if 'existing_instructions' not in st.session_state:
        st.session_state['existing_instructions'] = get_latest_instructions()
    setup_sidebar()

setup_app()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

#chatbot
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

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

    conversation_context = []
    if 'existing_instructions' in st.session_state:
        conversation_context.append(
            {"role": "system", "content": st.session_state['existing_instructions']})

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
        insert_chat_log(prompt, full_response)
        message_placeholder.markdown(full_response)

    # Append the assistant's response to the messages for display
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})
