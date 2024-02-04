# for database connection and initialization
import psycopg2
import logging
import streamlit as st

def connect_to_db():
    try:
        conn = psycopg2.connect(st.secrets["DB_CONNECTION"])
        logging.info("Successfully connected to the database. This is NeonDB if you followed the setup instructions")
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        return None

def initialize_db():
    conn = connect_to_db()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS custom_instructions (id SERIAL PRIMARY KEY, instructions TEXT, timestamp TIMESTAMP DEFAULT current_timestamp);""")
            cur.execute("""CREATE TABLE IF NOT EXISTS chat_logs (id SERIAL PRIMARY KEY, timestamp TIMESTAMP DEFAULT current_timestamp, prompt TEXT, response TEXT);""")
        conn.commit()
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()