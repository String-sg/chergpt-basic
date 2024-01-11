import logging
from openai import OpenAI
import streamlit as st
import psycopg2

st.title("CherGPT for IMH")

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


def create_instructions_table_if_not_exists():
    conn = connect_to_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS instructions (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT current_timestamp
                );
            """)
            conn.commit()
            print("Checked for 'instructions' table; created if not exists.")
    except Exception as e:
        print(f"Error creating 'instructions' table: {e}")
    finally:
        conn.close()


create_instructions_table_if_not_exists()


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
    conversation_context = [
        {"role": "system", "content": custom_instructions}] if existing_instructions else []
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
