import csv
import io
import logging
from app.db.database_connection import connect_to_db
from datetime import datetime
from zoneinfo import ZoneInfo


def insert_chat_log(prompt, response):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    # Get current time in GMT+8 timezone
    now_in_sgt = datetime.now(ZoneInfo("Asia/Singapore"))

    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO chat_logs (prompt, response, timestamp)
                VALUES (%s, %s, %s)
            """, (prompt, response, now_in_sgt))
            conn.commit()
            logging.info("Chat log inserted successfully.")
    except Exception as e:
        logging.error(f"Error inserting chat log: {e}")
    finally:
        if conn is not None:
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

    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    # Writing headers
    writer.writerow(['ID', 'Timestamp', 'Prompt', 'Response'])
    writer.writerows(chat_logs)
    return output.getvalue()


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

