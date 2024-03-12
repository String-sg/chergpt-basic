# databaseconnection.py
import psycopg2
import psycopg2.pool
import logging
import streamlit as st

# Initialize a connection pool globally
db_pool = None

def init_db_connection_pool():
    global db_pool
    if db_pool is None:
        try:
            db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, st.secrets["DB_CONNECTION"])
            logging.info("Database connection pool was successfully created.")
        except Exception as e:
            logging.error(f"Failed to create a database connection pool: {e}")
            db_pool = None

def get_db_connection():
    if db_pool:
        return db_pool.getconn()
    else:
        logging.error("Database connection pool is not available.")
        return None

def release_db_connection(conn):
    if db_pool and conn:
        db_pool.putconn(conn)

# Amend existing functions to use get_db_connection and release_db_connection
def connect_to_db():
    conn = get_db_connection()
    if not conn:
        logging.error("Failed to connect to the database via connection pool.")
    return conn

def drop_instructions_table():
    conn = get_db_connection()  # Use the updated method to get a db connection
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
        release_db_connection(conn)  # Release the connection back to the pool


def initialize_db():
    conn = get_db_connection()  
    if conn is None:
        return
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
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        release_db_connection(conn) 

