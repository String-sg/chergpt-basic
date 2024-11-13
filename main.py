import datetime
from openai import OpenAI
import logging
import streamlit as st
from app.chatlog.chatlog_handler import insert_chat_log, initialize_chatlog_table
from sidebar import setup_sidebar
from app.db.database_connection import connect_to_db, get_app_description, get_app_title, initialize_db
from app.instructions.instructions_handler import get_latest_instructions, retrieve_question_by_difficulty, log_understanding
import uuid

# Basic setup and app title
app_title = get_app_title()
app_description = get_app_description() or "Chatbot to support teaching and learning"
st.title(app_title)
setup_sidebar()  # Set up the sidebar with quiz mode toggle
initialize_db()  # Initialize the database

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set quiz_mode to True by default if it's not already in session state
if "quiz_mode" not in st.session_state:
    st.session_state["quiz_mode"] = True

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

def start_quiz():
    # Set quiz session state variables
    st.session_state["difficulty_level"] = 1
    st.session_state["question_index"] = 0
    st.session_state["quiz_started"] = True
    st.rerun()  # Force rerun to update UI immediately

def assess_response(response, question):
    expected_keywords = question.get("answer_keywords", "").split(",")  # Assume keywords are comma-separated
    keywords_matched = sum(1 for keyword in expected_keywords if keyword.lower() in response.lower())
    is_correct = keywords_matched >= len(expected_keywords) / 2 and len(response.split()) > 5
    return is_correct

# Function to load and display the next question
def load_next_question():
    current_question = retrieve_question_by_difficulty(st.session_state["difficulty_level"])
    if current_question:
        st.session_state["current_question_id"] = current_question["question_id"]
        st.session_state["current_question_content"] = current_question["content"]
        st.markdown(f"**Question:** {current_question['content']}")
        
        # Understanding Level Selection
        understanding_level = st.selectbox(
            "How well do you understand this question?",
            ["Select", "Fully understand", "Partially understand", "Do not understand"]
        )
        
        if understanding_level != "Select":
            # Log understanding level
            log_understanding(st.session_state["conversation_id"], st.session_state["current_question_id"], understanding_level)
            
            # Text area for student's response
            student_response = st.text_area("Your answer:")
            
            if st.button("Submit Answer"):
                is_correct = assess_response(student_response, current_question)
                st.session_state["difficulty_level"] += 1 if is_correct else max(1, st.session_state["difficulty_level"] - 1)
                
                # Log response
                insert_chat_log(st.session_state["conversation_id"], student_response, is_correct)
                
                # Move to the next question or end quiz if completed
                st.session_state["question_index"] += 1
                if st.session_state["question_index"] >= 10:  # Adjust total question count as needed
                    st.markdown("### Quiz Complete! Here’s your feedback:")
                    display_performance_feedback()
                else:
                    st.rerun()  # Refresh to load the next question

# Immediately start the quiz if quiz mode is enabled
if st.session_state["quiz_mode"]:
    if not st.session_state.get("quiz_started", False):
        # Start the quiz if it hasn't started yet
        start_quiz()
    else:
        # Load the next question if the quiz is already started
        load_next_question()
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

        conversation_context = []
        instructions = get_latest_instructions()
        if instructions:
            conversation_context.append({"role": "system", "content": instructions})

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

        st.session_state.messages.append({"role": "assistant", "content": full_response})

def display_performance_feedback():
    # Retrieve responses and calculate feedback
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT is_correct FROM student_logs
                    WHERE conversation_id = %s
                """, (st.session_state["conversation_id"],))
                results = cur.fetchall()

            correct_answers = sum(1 for result in results if result[0])
            total_questions = len(results)
            accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

            st.markdown(f"### Quiz Summary")
            st.write(f"Correct Answers: {correct_answers} out of {total_questions}")
            st.write(f"Accuracy: {accuracy:.2f}%")

            # Provide custom feedback based on performance
            if accuracy >= 80:
                st.success("Great job! You have a strong understanding of the material.")
            elif accuracy >= 50:
                st.info("Good effort! Some areas may need more review.")
            else:
                st.warning("Consider reviewing the material. Practice will improve your understanding.")
                
        except Exception as e:
            logging.error(f"Error retrieving performance feedback: {e}")
        finally:
            conn.close()
