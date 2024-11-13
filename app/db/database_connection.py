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
            # Initialize questions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    question_id UUID PRIMARY KEY,
                    qns TEXT NOT NULL,
                    difficulty INT NOT NULL,
                    topic TEXT,
                    answer_keywords TEXT
                );
            """)

            # Initialize app_info table with a quiz_mode column
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_info (
                    id SERIAL PRIMARY KEY,
                    description TEXT,
                    quiz_mode BOOLEAN DEFAULT TRUE
                );
            """)
            # Add student logs
            cur.execute("""
            CREATE TABLE IF NOT EXISTS student_logs (
                student_name TEXT,
                question_id UUID,
                understanding_level TEXT,
                response TEXT,
                is_correct BOOLEAN,
                timestamp TIMESTAMP DEFAULT (current_timestamp AT TIME ZONE 'Asia/Singapore')
            );
            """)
            conn.commit()
            # Initialize instructions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS instructions (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT (current_timestamp AT TIME ZONE 'Asia/Singapore')
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


        conn.commit()
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

def insert_question(question_id, qns, difficulty, topic, keywords):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return
                            
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO questions (question_id, qns, difficulty, topic, answer_keywords)
                VALUES (%s, %s, %s, %s, %s);
            """, (question_id, qns, difficulty, topic, keywords))
            conn.commit()
    except Exception as e:
        logging.error(f"Error inserting question: {e}")
    finally:
        if conn:
            conn.close()


def get_app_description():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return "Default app description here."

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

def log_student_interaction(student_name, question_id, understanding_level, response, is_correct):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO student_logs (student_name, question_id, understanding_level, response, is_correct)
                VALUES (%s, %s, %s, %s, %s);
            """, (student_name, question_id, understanding_level, response, is_correct))
            conn.commit()
            logging.info(f"Logged interaction for {student_name} on question {question_id}.")
    except Exception as e:
        logging.error(f"Error logging student interaction: {e}")
    finally:
        if conn:
            conn.close()

def get_app_title():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return "Default app title here."

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

def set_quiz_mode(enabled):
    conn = connect_to_db()
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE app_info SET quiz_mode = %s WHERE id = 1;", (enabled,))
        conn.commit()
    except Exception as e:
        logging.error(f"Error setting quiz mode: {e}")
    finally:
        if conn:
            conn.close()

def get_quiz_mode():
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT quiz_mode FROM app_info WHERE id = 1;")
            result = cur.fetchone()
            return result[0] if result else False
    except Exception as e:
        logging.error(f"Error getting quiz mode: {e}")
        return False
    finally:
        if conn:
            conn.close()

def check_schema():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return
    try:
        with conn.cursor() as cur:
            # Get schema details for each table
            for table_name in ["questions", "app_info", "student_logs", "instructions", "app_title"]:
                cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}';")
                columns = cur.fetchall()
                print(f"Table: {table_name}")
                for column in columns:
                    print(f"Column: {column[0]}, Type: {column[1]}")
                print("\n")
    except Exception as e:
        logging.error(f"Error checking schema: {e}")
    finally:
        if conn:
            conn.close()

# check_schema()