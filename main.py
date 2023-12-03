from openai import OpenAI
import streamlit as st
import psycopg2

st.title("CherGPT Basic")

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
    # Use psycopg2 or another PostgreSQL-compatible connector
    # The connection details should be stored in secrets.toml
    conn = psycopg2.connect(
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        database=st.secrets["DB_NAME"]
    )
    return conn


def get_latest_instructions():
    conn = connect_to_db()
    with conn.cursor() as cur:
        # Assuming there's an 'id' column
        cur.execute("SELECT content FROM instructions ORDER BY id DESC LIMIT 1")
        latest_instructions = cur.fetchone()
    conn.close()
    return latest_instructions[0] if latest_instructions else ""


# Admin panel for custom instructions
if st.session_state.get("is_admin"):
    with st.sidebar:
        st.title("Admin Panel")
        existing_instructions = get_latest_instructions()
        custom_instructions = st.text_area(
            "Custom Instructions", value=existing_instructions)

        if st.button("Save Instructions"):
            update_instructions(custom_instructions)
            st.success("Instructions updated successfully")


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for response in client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        ):
            full_response += (response.choices[0].delta.content or "")
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})
