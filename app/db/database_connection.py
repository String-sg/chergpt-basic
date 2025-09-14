# for database connection and initialization
import psycopg2
import logging
import streamlit as st
from functools import lru_cache

@st.cache_resource
def get_db_connection():
    """Get cached database connection using Streamlit's connection pooling"""
    try:
        conn = st.connection("neon_db", type="sql", url=st.secrets["DB_CONNECTION"])
        logging.info("Successfully connected to the database using st.connection")
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        return None

def connect_to_db():
    """Legacy function - returns raw psycopg2 connection for backwards compatibility"""
    try:
        conn = psycopg2.connect(st.secrets["DB_CONNECTION"])
        logging.info("Successfully connected to the database. This is NeonDB if you followed the setup instructions")
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        return None

def get_connection():
    """Get connection from pool - preferred method"""
    db_conn = get_db_connection()
    if db_conn is None:
        return None
    return db_conn._instance

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

            # Initialize ingested_files table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ingested_files (
                    id SERIAL PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size BIGINT,
                    file_hash VARCHAR(64) UNIQUE,
                    chunks_count INTEGER DEFAULT 0,
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed' CHECK (status IN ('processing', 'completed', 'failed')),
                    error_message TEXT
                );
            """)

            # Initialize file_selections table for user preferences
            cur.execute("""
                CREATE TABLE IF NOT EXISTS file_selections (
                    id SERIAL PRIMARY KEY,
                    user_name TEXT NOT NULL,
                    file_id INTEGER REFERENCES ingested_files(id) ON DELETE CASCADE,
                    is_selected BOOLEAN DEFAULT true,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_name, file_id)
                );
            """)


        conn.commit()
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_app_description():
    conn = get_connection()
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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_app_title():
    conn = get_connection()
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

def insert_ingested_file(file_name, file_path, file_size, file_hash, status='processing'):
    """Insert a new ingested file record"""
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return None

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ingested_files (file_name, file_path, file_size, file_hash, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (file_name, file_path, file_size, file_hash, status))
            file_id = cur.fetchone()[0]
            conn.commit()
            logging.info(f"Ingested file record created with ID: {file_id}")
            return file_id
    except Exception as e:
        logging.error(f"Error inserting ingested file: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_ingested_file_status(file_id, status, chunks_count=None, error_message=None):
    """Update the status of an ingested file"""
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return False

    try:
        with conn.cursor() as cur:
            if chunks_count is not None:
                cur.execute("""
                    UPDATE ingested_files
                    SET status = %s, chunks_count = %s, error_message = %s
                    WHERE id = %s;
                """, (status, chunks_count, error_message, file_id))
            else:
                cur.execute("""
                    UPDATE ingested_files
                    SET status = %s, error_message = %s
                    WHERE id = %s;
                """, (status, error_message, file_id))
            conn.commit()
            logging.info(f"Updated ingested file {file_id} status to {status}")
            return True
    except Exception as e:
        logging.error(f"Error updating ingested file status: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_ingested_files():
    """Get all ingested files"""
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return []

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, file_name, file_path, file_size, chunks_count,
                       ingested_at, status, error_message
                FROM ingested_files
                ORDER BY ingested_at DESC;
            """)
            files = cur.fetchall()
            return [{
                'id': row[0],
                'file_name': row[1],
                'file_path': row[2],
                'file_size': row[3],
                'chunks_count': row[4],
                'ingested_at': row[5],
                'status': row[6],
                'error_message': row[7]
            } for row in files]
    except Exception as e:
        logging.error(f"Error fetching ingested files: {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_ingested_file(file_id):
    """Delete an ingested file record and its associated chunks"""
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return False

    try:
        with conn.cursor() as cur:
            # First get the file info
            cur.execute("SELECT file_name FROM ingested_files WHERE id = %s", (file_id,))
            result = cur.fetchone()
            if not result:
                logging.warning(f"File with ID {file_id} not found")
                return False

            # Delete associated RAG chunks (you may want to add a file_id foreign key later)
            # For now, we'll keep the chunks as they might be shared

            # Delete the file record (CASCADE will handle file_selections)
            cur.execute("DELETE FROM ingested_files WHERE id = %s", (file_id,))
            conn.commit()
            logging.info(f"Deleted ingested file record: {result[0]}")
            return True
    except Exception as e:
        logging.error(f"Error deleting ingested file: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_user_file_selections(user_name):
    """Get user's file selections with file details"""
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return []

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    f.id, f.file_name, f.chunks_count, f.status,
                    COALESCE(fs.is_selected, true) as is_selected
                FROM ingested_files f
                LEFT JOIN file_selections fs ON f.id = fs.file_id AND fs.user_name = %s
                WHERE f.status = 'completed'
                ORDER BY f.ingested_at DESC;
            """, (user_name,))

            files = cur.fetchall()
            return [{
                'id': row[0],
                'file_name': row[1],
                'chunks_count': row[2],
                'status': row[3],
                'is_selected': row[4]
            } for row in files]
    except Exception as e:
        logging.error(f"Error fetching user file selections: {e}")
        return []
    finally:
        if conn:
            conn.close()

def update_user_file_selection(user_name, file_id, is_selected):
    """Update user's selection for a specific file"""
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO file_selections (user_name, file_id, is_selected, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_name, file_id)
                DO UPDATE SET
                    is_selected = EXCLUDED.is_selected,
                    updated_at = EXCLUDED.updated_at;
            """, (user_name, file_id, is_selected))
            conn.commit()
            logging.info(f"Updated file selection for user {user_name}, file {file_id}: {is_selected}")
            return True
    except Exception as e:
        logging.error(f"Error updating file selection: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_selected_file_ids(user_name):
    """Get list of file IDs selected by user for RAG queries"""
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return []

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT f.id
                FROM ingested_files f
                LEFT JOIN file_selections fs ON f.id = fs.file_id AND fs.user_name = %s
                WHERE f.status = 'completed'
                AND COALESCE(fs.is_selected, true) = true;
            """, (user_name,))

            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Error fetching selected file IDs: {e}")
        return []
    finally:
        if conn:
            conn.close()
