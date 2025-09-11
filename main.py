# main.py
import datetime
import io
import csv
from openai import OpenAI
import logging
import streamlit as st
from app.chatlog.chatlog_handler import insert_chat_log, initialize_chatlog_table
from sidebar import setup_sidebar
from app.db.database_connection import get_app_description, get_app_title, initialize_db, update_app_description
from app.instructions.instructions_handler import get_latest_instructions
from app.rag.rag_handler import rag_handler
import uuid

app_title = get_app_title()
app_description = get_app_description() or "Chatbot to support teaching and learning"
st.title(app_title)
# Initialize session state for admin
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

# Initialize user name in session state
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

# Initialize RAG settings
if "use_rag" not in st.session_state:
    st.session_state["use_rag"] = True

# Set up the sidebar
setup_sidebar()

# Display the app description to all users
st.markdown(app_description, unsafe_allow_html=True)

# Name input section - show only if name is not set
if not st.session_state["user_name"]:
    st.subheader("Welcome! Please enter your name to start chatting:")
    name_input = st.text_input("Your name:", placeholder="Enter your name here...")
    if st.button("Start Chatting", key="start_chat_button"):
        if name_input.strip():
            st.session_state["user_name"] = name_input.strip()
            st.rerun()
        else:
            st.error("Please enter your name before starting.")
    
    # Stop here if name is not provided
    st.stop()

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


    # Prepend custom instructions and RAG context to the conversation context for processing
    conversation_context = []
    
    # Add custom instructions first
    if existing_instructions:
        conversation_context.append(
            {"role": "system", "content": custom_instructions})
    
    # Add RAG context if enabled and relevant
    rag_context = ""
    if st.session_state.get("use_rag", True):
        try:
            # Check if query might benefit from economics context
            if rag_handler.is_economics_related(prompt):
                with st.spinner("🔍 Searching course materials..."):
                    rag_context = rag_handler.retrieve_context(prompt, top_k=4, similarity_threshold=0.6)
                    
                if rag_context:
                    st.info("📚 Found relevant content from your Economics materials")
                    conversation_context.append(
                        {"role": "system", "content": rag_context})
                else:
                    st.info("🔍 Searched course materials but found no highly relevant content")
        except Exception as e:
            logging.error(f"RAG retrieval failed: {e}")
            st.warning("⚠️ Could not search course materials, proceeding without context")
    else:
        # RAG is disabled - check if this was an economics question
        if rag_handler.is_economics_related(prompt):
            st.info("📚 Course material search is currently disabled by your educator")

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
        insert_chat_log(prompt, full_response, st.session_state["conversation_id"], st.session_state.get("user_name"))
        message_placeholder.markdown(full_response)

    # Append the assistant's response to the messages for display
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})
