import csv
import io
import logging
from app.db.database_connection import connect_to_db
from datetime import datetime
from zoneinfo import ZoneInfo
import openai
import uuid
from openai import OpenAI
import streamlit as st

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

def fetch_and_batch_chatlogs():
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database for fetching logs.")
        return {}

    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT conversation_id, prompt, response FROM chat_logs")
            chat_logs = cur.fetchall()
            batches = {}
            for log in chat_logs:
                uuid = str(log[0])
                if uuid not in batches:
                    batches[uuid] = []
                batches[uuid].append(log[1] + " " + log[2])  # Combine prompt and response
            return batches
    except Exception as e:
        logging.error(f"Error fetching and batching chat logs: {e}")
        return {}
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


def generate_summary_for_each_group(batches):
    summaries = {}
    for idx, (uuid, logs) in enumerate(batches.items(), start=1):
        if not logs:  # Skip empty conversations
            continue
            
        combined_logs = "\n".join(logs)
        system_message = "You are an assistant that summarizes conversations. Create a concise summary of the key points discussed."
        
        try:
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": combined_logs}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            summary_text = response.choices[0].message.content.strip()
            summaries[uuid] = summary_text if summary_text else "No meaningful content to summarize."
            
        except Exception as e:
            logging.error(f"Summary generation failed for UUID {uuid}: {str(e)}")
            summaries[uuid] = f"Failed to generate summary: {str(e)}"
            
    return summaries

def compile_summaries(summaries):
    if not summaries:
        return "No chat conversations found to summarize."
        
    compiled_output = "# Chat Summaries\n\n"
    for idx, (uuid, summary) in enumerate(summaries.items(), start=1):
        compiled_output += f"### Conversation {idx}\n"
        compiled_output += f"_{summary}_\n\n"
    return compiled_output


# Fetch and batch the chat logs by UUID
batches = fetch_and_batch_chatlogs()

# Generate a summary for each group
group_summaries = generate_summary_for_each_group(batches)

# Compile the individual group summaries into a structured format
final_summary_output = compile_summaries(group_summaries)
