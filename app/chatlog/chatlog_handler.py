import csv
import io
import logging
from app.db.database_connection import connect_to_db
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid

def insert_chat_log(prompt, response, conversation_id):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
    # Get current time in GMT+8 timezone
    now_in_sgt = datetime.now(ZoneInfo("Asia/Singapore"))
    conversation_uuid = str(uuid.UUID(conversation_id)) 
    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_logs (prompt, response, timestamp, conversation_id)
                VALUES (%s, %s, %s, %s)
            """, (prompt, response, now_in_sgt, conversation_uuid))
            conn.commit()
            logging.info("Chat log inserted successfully.")
    except Exception as e:
        logging.error(f"Error inserting chat log: {e}")
    finally:
        if conn is not None:
            conn.close()

def initialize_chatlog_table():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT current_timestamp,
                    prompt TEXT,
                    response TEXT,
                    conversation_id UUID
                );
            """)
            conn.commit()
            logging.info("Chatlog table (re)created successfully.")
    except Exception as e:
        logging.error(f"Error (re)creating chatlog table: {e}")
    finally:
        if conn:
            conn.close()


# fetch chatlog
def fetch_chat_logs():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database for fetching logs.")
        return []
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM chat_logs")
            chat_logs = cur.fetchall()
            logging.info(f"Fetched {len(chat_logs)} chat log records.")
            return chat_logs
    except Exception as e:
        logging.error(f"Error fetching chat logs: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()

# fetch past hour chatlog


def fetch_recent_chat_logs(hours=1):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database for fetching logs.")
        return []

    # Ensure the current time is in GMT+8
    now_in_sgt = datetime.now(ZoneInfo("Asia/Singapore"))
    one_hour_ago = now_in_sgt - datetime.timedelta(hours=hours)
    logging.info(f"Fetching logs from: {one_hour_ago}")

    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM chat_logs 
                WHERE timestamp >= %s
            """, (one_hour_ago,))
            chat_logs = cur.fetchall()
            logging.info(f"Fetched {len(chat_logs)} chat log records.")
            return chat_logs
    except Exception as e:
        logging.error(f"Error fetching recent chat logs: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()

# fetch past hour chatlog
def fetch_recent_chat_logs(hours=1):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database for fetching logs.")
        return []

    one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=hours)
    logging.info(f"Fetching logs from: {one_hour_ago}")

    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM chat_logs 
                WHERE timestamp >= %s
            """, (one_hour_ago,))
            chat_logs = cur.fetchall()
            logging.info(f"Fetched {len(chat_logs)} chat log records.")
            return chat_logs
    except Exception as e:
        logging.error(f"Error fetching recent chat logs: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()


def export_chat_logs_to_csv(filename='chat_logs.csv'):
    chat_logs = fetch_chat_logs()
    if not chat_logs:
        print("No chat logs to export.")
        return
    # Create a CSV in memory with UTF-8 encoding
    output = io.StringIO()
    writer = csv.writer(output)
    # Ensure headers match the database columns, including 'ConversationID'
    writer.writerow(['ID', 'Timestamp', 'Prompt', 'Response', 'ConversationID'])
    # Iterate through each chat log entry and write to CSV
    for log in chat_logs:
        writer.writerow(log)  # Directly write the log as it should match the headers

    # Return the CSV content encoded in UTF-8
    return output.getvalue().encode('utf-8-sig')

chat_logs = fetch_chat_logs()
# print(chat_logs[0])

# delete chatlog
def delete_all_chatlogs():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return
    try:
        with conn, conn.cursor() as cur:
            cur.execute("DELETE FROM chat_logs")
            conn.commit()
            logging.info("All chat logs deleted successfully.")
    except Exception as e:
        logging.error(f"Error deleting chat logs: {e}")
    finally:
        if conn is not None:
            conn.close()

def drop_chatlog_table():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS chat_logs;")
            conn.commit()
            logging.info("Chatlog table dropped successfully.")
    except Exception as e:
        logging.error(f"Error dropping chatlog table: {e}")
    finally:
        if conn is not None:
            conn.close()