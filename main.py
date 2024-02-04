import datetime
import csv
import psycopg2
from openai import OpenAI
import logging
import streamlit as st
from sidebar import setup_sidebar
from app.db.db import initialize_db, connect_to_db
from utils import get_latest_instructions, update_instructions, export_chat_logs_to_csv, delete_all_chatlogs, custom_instructions, existing_instructions

# from chatbot import process_chat_input
# from admin_panel import handle_admin_actions

st.title("CherGPT Basic")
"""Teaching and learning companion"""
# Initialize session state for admin
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False


# Set up the sidebar and initialize DB
setup_sidebar()
initialize_db()

# Tech debt to refactor admin panel actions
# handle_admin_actions()
# Chatbot interaction
# process_chat_input()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# insert chatlog into DB
def insert_chat_log(prompt, response):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_logs (prompt, response)
                VALUES (%s, %s)
            """, (prompt, response))
            conn.commit()
            logging.info("Chat log inserted successfully.")
    except Exception as e:
        logging.error(f"Error inserting chat log: {e}")
    finally:
        if conn is not None:
            conn.close()

# fetch chatlog
def fetch_chat_logs():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database for fetching logs.")
        return []
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM chat_logs")
            chat_logs = cur.fetchall()
            logging.info(f"Fetched {len(chat_logs)} chat log records.")
            return chat_logs
    except Exception as e:
        logging.error(f"Error fetching chat logs: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()

# fetch past hour chatlog


def fetch_recent_chat_logs(hours=1):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database for fetching logs.")
        return []

    one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=hours)
    logging.info(f"Fetching logs from: {one_hour_ago}")

    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM chat_logs 
                WHERE timestamp >= %s
            """, (one_hour_ago,))
            chat_logs = cur.fetchall()
            logging.info(f"Fetched {len(chat_logs)} chat log records.")
            return chat_logs
    except Exception as e:
        logging.error(f"Error fetching recent chat logs: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()

# export chatlog



# insights
def generate_insights_with_openai(chat_logs):
    # Constructing the conversation context for GPT-3.5-turbo
    conversation_context = [
        {"role": "system", "content": "Analyze the following chat logs and provide the top 5 insights on how students' questioning techniques could be improved:"}]
    for log in chat_logs:
        conversation_context.append({"role": "user", "content": log[2]})
        conversation_context.append({"role": "assistant", "content": log[3]})

    # Sending the context to OpenAI's GPT-3.5-turbo model using the 'client' object
    try:
        response = client.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_context
        )
        return response.choices[0].message['content']
    except Exception as e:
        logging.error(f"Error generating insights with OpenAI: {e}")
        # Consider also logging the conversation context to debug further
        logging.debug(f"Failed conversation context: {conversation_context}")
        return "Error generating insights."








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
        insert_chat_log(prompt, full_response)
        message_placeholder.markdown(full_response)

    # Append the assistant's response to the messages for display
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})
