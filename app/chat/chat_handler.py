
import streamlit as st
from openai import OpenAI
from app.chatlog.chatlog_handler import insert_chat_log

def initialize_chat_state():
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o-mini"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state["conversation_id"] = str(uuid.uuid4())

from streamlit_chat_ui_improvement import chat_ui

def display_chat_history():
    for message in st.session_state.messages:
        avatar = "🧑‍🎓" if message["role"] == "user" else "🤖"
        chat_ui.message(message["content"], avatar=avatar, is_user=message["role"] == "user")

def handle_chat_interaction(client, custom_instructions):
    if prompt := chat_ui.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        chat_ui.message(prompt, avatar="🧑‍🎓", is_user=True)

        conversation_context = []
        if custom_instructions:
            conversation_context.append({"role": "system", "content": custom_instructions})

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

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response})
