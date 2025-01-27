import logging
from app.db.database_connection import connect_to_db

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

def update_instructions(new_instructions):
    if not new_instructions:
        logging.error("Instructions content is empty")
        return False
        
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO instructions (id, content)
                VALUES (1, %s)
                ON CONFLICT (id)
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    timestamp = current_timestamp
                RETURNING id;
            """, (new_instructions,))
            result = cur.fetchone()
            if not result:
                logging.error("No rows were affected by the update")
            conn.commit()
            logging.info("Instructions updated successfully.")
            return result is not None
    except Exception as e:
        logging.error(f"Error updating instructions: {str(e)}")
        if hasattr(e, 'pgerror'):
            logging.error(f"PostgreSQL error: {e.pgerror}")
        return False
    finally:
        if conn:
            conn.close()