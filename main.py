import logging
from openai import OpenAI
import streamlit as st
import psycopg2
import csv

st.title("CherGPT Basic")

# Initialize session state for admin
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

# Initialize variables for custom and existing instructions
custom_instructions = ""
existing_instructions = ""

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

with st.sidebar:
    st.title("Settings")
    with st.expander("Admin config"):
        admin_password = st.text_input("Enter Admin Password", type="password")

        if admin_password == st.secrets["ADMIN_PASSWORD"]:
            st.session_state["is_admin"] = True
            st.success("Authenticated as Admin")
        elif admin_password:  # Only display message if something was entered
            st.error("Incorrect password")
            st.session_state["is_admin"] = False


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


# fetch chatlog
def fetch_chat_logs():
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM chat_logs")
            chat_logs = cur.fetchall()
            return chat_logs
    except Exception as e:
        logging.error(f"Error fetching chat logs: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()

# export chatlog


def export_chat_logs_to_csv(filename='chat_logs.csv'):
    chat_logs = fetch_chat_logs()
    if not chat_logs:
        print("No chat logs to export.")
        return

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        # Writing headers
        writer.writerow(['ID', 'Timestamp', 'Prompt', 'Response'])
        writer.writerows(chat_logs)

    print(f"Chat logs exported to {filename}")

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

# Admin panel for custom instructions
if st.session_state.get("is_admin"):
    with st.sidebar:
        st.title("Admin Panel")
        existing_instructions = get_latest_instructions()
        custom_instructions = st.text_area(
            "Custom Instructions", value=existing_instructions,
            height=custominstructions_area_height)

        if st.button("Save Instructions"):
            update_instructions(custom_instructions)
            st.success("Instructions updated successfully")
            st.experimental_rerun()

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
        message_placeholder.markdown(full_response)

    # Append the assistant's response to the messages for display
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})
