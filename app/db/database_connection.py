# for database connection and initialization
import os
import psycopg2
import logging
import streamlit as st

def connect_to_db():
    try:
        conn = psycopg2.connect(os.environ["DB_CONNECTION"])
        logging.info("Successfully connected to the database. This is NeonDB if you followed the setup instructions")
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        return None

def drop_instructions_table():
    conn = connect_to_db()
    if conn is None:
        st.error("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS instructions;")
            conn.commit()
            st.success("Instructions table dropped successfully.")
    except Exception as e:
        logging.error(f"Error dropping instructions table: {e}")
        st.error(f"Error dropping instructions table: {e}")
    finally:
        if conn:
            conn.close()

def initialize_db():
    conn = connect_to_db()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            # Initialize instructions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS instructions (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT current_timestamp
                );
            """)

            # Initialize app_info table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_info (
                    id SERIAL PRIMARY KEY,
                    description TEXT
                );
            """)
            
            # Ensure there is always one row in app_info to update
            cur.execute("""
                INSERT INTO app_info (id, description)
                VALUES (1, 'Chatbot to support teaching and learning.')
                ON CONFLICT (id) DO NOTHING;
            """)

            # Initialize app_title table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_title (
                    id SERIAL PRIMARY KEY,
                    description TEXT
                );
            """)
            
            # Ensure there is always one row in app_title to update
            cur.execute("""
                INSERT INTO app_title (id, description)
                VALUES (1, 'CherGPT')
                ON CONFLICT (id) DO NOTHING;
            """)

            # Initialize user_prompts table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_prompts (
                    id SERIAL PRIMARY KEY,
                    email TEXT NOT NULL,
                    prompt_name TEXT NOT NULL,
                    prompt_content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT current_timestamp
                );
            """)

            # Initialize sessions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email TEXT NOT NULL,
                    prompt_id INTEGER REFERENCES user_prompts(id),
                    created_at TIMESTAMP DEFAULT current_timestamp,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT true
                );
            """)

        conn.commit()
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()


def get_app_description():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return "Chatbot to support teaching and learning."

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT description FROM app_info WHERE id = 1;")
            description = cur.fetchone()
            if description:
                return description[0]
            else:
                return "Chatbot to support teaching and learning."
    except Exception as e:
        logging.error(f"Error fetching app description: {e}")
        return "Chatbot to support teaching and learning."
    finally:
        if conn:
            conn.close()

def get_app_title():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return "CherGPT"

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT description FROM app_title WHERE id = 1;")
            description = cur.fetchone()
            if description:
                return description[0]
            else:
                return "CherGPT"

    except Exception as e:
        logging.error(f"Error fetching app title: {e}")
        return "CherGPT"
    finally:
        if conn:
            conn.close()

def update_app_title(new_title):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE app_title SET description = %s WHERE id = 1;
            """, (new_title,))
            conn.commit()
            logging.info("App description updated successfully.")
    except Exception as e:
        logging.error(f"Error updating app title: {e}")
    finally:
        if conn:
            conn.close()


def update_app_description(new_description):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE app_info SET description = %s WHERE id = 1;
            """, (new_description,))
            conn.commit()
            logging.info("App description updated successfully.")
    except Exception as e:
        logging.error(f"Error updating app description: {e}")
    finally:
        if conn:
            conn.close()
def save_user_prompt(email, prompt_name, prompt_content):
    conn = connect_to_db()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_prompts (email, prompt_name, prompt_content)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (email, prompt_name, prompt_content))
            prompt_id = cur.fetchone()[0]
            conn.commit()
            return prompt_id
    finally:
        if conn:
            conn.close()

def get_user_prompts(email):
    conn = connect_to_db()
    if conn is None:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, prompt_name, prompt_content FROM user_prompts WHERE email = %s", (email,))
            return cur.fetchall()
    finally:
        if conn:
            conn.close()

def create_session(email, prompt_id):
    conn = connect_to_db()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sessions (email, prompt_id, expires_at)
                VALUES (%s, %s, current_timestamp + interval '24 hours')
                RETURNING id;
            """, (email, prompt_id))
            session_id = cur.fetchone()[0]
            conn.commit()
            return session_id
    finally:
        if conn:
            conn.close()

def get_session_prompt(session_id):
    conn = connect_to_db()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT up.prompt_content, up.prompt_name
                FROM sessions s 
                JOIN user_prompts up ON s.prompt_id = up.id 
                WHERE s.id::text = %s AND s.is_active = true AND s.expires_at > current_timestamp;
            """, (session_id,))
            result = cur.fetchone()
            return result if result else None
    finally:
        if conn:
            conn.close()
