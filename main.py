import datetime
import io
import csv
from openai import OpenAI
import logging
import streamlit as st
from app.chatlog.chatlog_handler import insert_chat_log, initialize_chatlog_table
from sidebar import setup_sidebar
from app.db.database_connection import get_app_description, get_app_title, initialize_db
from app.instructions.instructions_handler import get_latest_instructions, retrieve_question_by_difficulty, log_understanding
import uuid

# Basic setup and app title
app_title = get_app_title()
app_description = get_app_description() or "Chatbot to support teaching and learning"
st.title(app_title)
setup_sidebar()  # Set up the sidebar with quiz mode toggle
initialize_db()  # Initialize the database

# Initialize session states for admin and conversation
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display app description
st.markdown(app_description, unsafe_allow_html=True)

# Check if quiz mode is enabled
if st.session_state.get("quiz_mode", False):
    # Step 2: Quiz-Specific Initialization
    # Prompt for student name as the first step in quiz mode
    if "student_name" not in st.session_state:
        st.session_state["student_name"] = st.text_input("Please enter your name:")
        
    if st.session_state["student_name"]:
        # Step 3: Quiz Question Initialization
        if "current_question_id" not in st.session_state:
            st.session_state["difficulty_level"] = 1
            st.session_state["question_index"] = 0
            st.session_state.messages = []  # Clear previous messages for a fresh quiz experience

        # Fetch a question based on the current difficulty level
        current_question = retrieve_question_by_difficulty(st.session_state["difficulty_level"])

        if current_question:
            st.session_state["current_question_id"] = current_question["question_id"]
            st.markdown(f"**Question:** {current_question['content']}")
            
            # Understanding Level Selection
            understanding_level = st.selectbox(
                "How well do you understand this question?",
                ["Select", "Fully understand", "Partially understand", "Do not understand"]
            )
            
            # Step 4: Log Understanding Level and Capture Response
            if understanding_level != "Select":
                # Log understanding level in the backend
                log_understanding(st.session_state["student_name"], st.session_state["current_question_id"], understanding_level)

                # Text area for student’s response
                student_response = st.text_area("Your answer:")
                
                if st.button("Submit Answer"):
                    is_correct = assess_response(student_response, current_question)  # Implement assess_response function
                    
                    # Adjust difficulty level based on response quality
                    if is_correct:
                        st.session_state["difficulty_level"] += 1  # Increase difficulty
                    else:
                        st.session_state["difficulty_level"] = max(1, st.session_state["difficulty_level"] - 1)
                    
                    # Log response in chat log
                    insert_chat_log(st.session_state["student_name"], student_response, is_correct)

                    # Check if more questions are available or end quiz
                    st.session_state["question_index"] += 1
                    if st.session_state["question_index"] >= total_questions:
                        st.markdown("### Quiz Complete! Here’s your feedback:")
                        display_performance_feedback(st.session_state["student_name"])  # Define feedback display function
else:
    # Regular Chatbot Interaction (If quiz mode is off)
    initialize_chatlog_table()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare conversation context with custom instructions if available
        conversation_context = []
        if existing_instructions:
            conversation_context.append({"role": "system", "content": custom_instructions})

        conversation_context += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        # Assistant response using OpenAI API
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

        # Append assistant response to messages
        st.session_state.messages.append({"role": "assistant", "content": full_response})
