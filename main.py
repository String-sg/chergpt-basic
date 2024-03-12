# main.py
import datetime
import io
import csv
import psycopg2
from openai import OpenAI
import logging
import streamlit as st
from app.chatlog.chatlog_handler import insert_chat_log
from sidebar import setup_sidebar
from app.db.database_connection import initialize_db
from app.instructions.instructions_handler import get_latest_instructions

st.title("CherGPT Basic")

# Initialize session state for admin
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False


# Set up the sidebar
setup_sidebar()

# Admin panel actions
# handle_admin_actions()

# Chatbot interaction
# process_chat_input()


# Initialize variables for custom and existing instructions
custom_instructions = ""
existing_instructions = ""

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def connect_to_db():
    try:
        conn = psycopg2.connect(
            st.secrets["DB_CONNECTION"]
        )
        logging.info("Successfully connected to the database.")
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        return None


def initialize_db():
    conn = connect_to_db()
    if conn is None:
        return
    try:
        with conn, conn.cursor() as cur:
            # Create custom_instructions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS custom_instructions (
                    id SERIAL PRIMARY KEY,
                    instructions TEXT,
                    timestamp TIMESTAMP DEFAULT current_timestamp
                );
            """)

            # Create chat_logs table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT current_timestamp,
                    prompt TEXT,
                    response TEXT
                );
            """)
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        if conn is not None:
            conn.close()


# Call the initialization function at the appropriate place in your application
initialize_db()


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

# test datetime conversion


def test_timestamp_conversion():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT timestamp FROM chat_logs LIMIT 1")
            record = cur.fetchone()
            if record:
                print("Timestamp type:", type(record[0]))
            else:
                print("No records found.")
    except Exception as e:
        logging.error(f"Error fetching a timestamp: {e}")
    finally:
        if conn is not None:
            conn.close()


test_timestamp_conversion()


# export chatlog


def export_chat_logs_to_csv(filename='chat_logs.csv'):
    chat_logs = fetch_chat_logs()
    if not chat_logs:
        print("No chat logs to export.")
        return

    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    # Writing headers
    writer.writerow(['ID', 'Timestamp', 'Prompt', 'Response'])
    writer.writerows(chat_logs)
    return output.getvalue()


# delete chatlog
def delete_all_chatlogs():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return
    try:
        with conn, conn.cursor() as cur:
            cur.execute("DELETE FROM chat_logs")
            conn.commit()
            logging.info("All chat logs deleted successfully.")
    except Exception as e:
        logging.error(f"Error deleting chat logs: {e}")
    finally:
        if conn is not None:
            conn.close()

# insights


def generate_insights_with_openai(chat_logs):
    # Constructing the conversation context for GPT-3.5-turbo
    conversation_context = [
        {"role": "system", "content": "Analyze the following chat logs and provide the top 5 insights on how students' questioning techniques could be improved:"}]
    for log in chat_logs:
        conversation_context.append({"role": "user", "content": log[2]})
        conversation_context.append({"role": "assistant", "content": log[3]})

    # Sending the context to OpenAI's GPT-3.5-turbo model
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_context
    )

    return response.choices[0].message['content']


# Create update instructions


def update_instructions(new_instructions):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO instructions (content)
                VALUES (%s)
                ON CONFLICT (id)
                DO UPDATE SET content = EXCLUDED.content;
            """, (new_instructions,))
            conn.commit()
            logging.info("Instructions updated successfully.")
    except Exception as e:
        logging.error(f"Error updating instructions: {e}")
    finally:
        conn.close()


def get_latest_instructions():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return ""

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT content FROM instructions ORDER BY id DESC LIMIT 1")
            latest_instructions = cur.fetchone()
            return latest_instructions[0] if latest_instructions else ""
    except Exception as e:
        logging.error(f"Error fetching latest instructions: {e}")
        return ""
    finally:
        conn.close()


existing_instructions = get_latest_instructions()
custom_instructions = existing_instructions


custominstructions_area_height = 300


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
if prompt := st.chat_input("What is up?"):
    # Process the prompt and get the response...

    # Append only the new message and response to the UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response})

    for message in st.session_state.messages[-2:]:  # Render only the last two messages
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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