
"""
Handles chat-related functionality including state management and message processing.
"""
import streamlit as st
from openai import OpenAI
import uuid
from app.chatlog.chatlog_handler import insert_chat_log

def initialize_chat_state():
    """Initialize chat-related session state variables."""
    defaults = {
        "openai_model": "gpt-4o-mini",
        "messages": [],
        "conversation_id": str(uuid.uuid4())
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def display_chat_history():
    """Display all messages in the chat history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_chat_interaction(client: OpenAI, custom_instructions: str):
    """Handle user chat input and generate AI response."""
    if prompt := st.chat_input("What's on your mind?"):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare conversation context
        conversation_context = []
        if custom_instructions:
            conversation_context.append({
                "role": "system",
                "content": custom_instructions
            })
        conversation_context.extend(st.session_state.messages)

        # Generate and display AI response
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
            
            # Save chat log and update display
            insert_chat_log(
                prompt,
                full_response,
                st.session_state["conversation_id"]
            )
            message_placeholder.markdown(full_response)
            
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response
        })
