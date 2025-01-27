import logging
from app.db.database_connection import connect_to_db

def get_latest_instructions(email=None):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return ""

    try:
        with conn.cursor() as cur:
            query = "SELECT content FROM instructions ORDER BY id DESC LIMIT 1"
            if email:
                query = "SELECT content FROM instructions WHERE email = %s ORDER BY id DESC LIMIT 1"
                cur.execute(query, (email,))
            else:
                cur.execute(query)
            latest_instructions = cur.fetchone()
            return latest_instructions[0] if latest_instructions else ""
    except Exception as e:
        logging.error(f"Error fetching latest instructions: {e}")
        return ""
    finally:
        conn.close()

def update_instructions(email, new_instructions):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO instructions (email, content)
                VALUES (%s, %s)
                ON CONFLICT (id)
                DO UPDATE SET content = EXCLUDED.content;
            """, (new_instructions,))
            conn.commit()
            logging.info("Instructions updated successfully.")
    except Exception as e:
        logging.error(f"Error updating instructions: {e}")
    finally:
        conn.close()