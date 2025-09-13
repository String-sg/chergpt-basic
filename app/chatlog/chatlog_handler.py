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

def insert_chat_log(prompt, response, conversation_id, user_name=None):
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
                INSERT INTO chat_logs (prompt, response, timestamp, conversation_id, user_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (prompt, response, now_in_sgt, conversation_uuid, user_name))
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
                    conversation_id UUID,
                    user_name TEXT
                );
            """)
            
            # Add user_name column if it doesn't exist (for existing databases)
            cur.execute("""
                DO $$ 
                BEGIN 
                    BEGIN
                        ALTER TABLE chat_logs ADD COLUMN user_name TEXT;
                    EXCEPTION
                        WHEN duplicate_column THEN
                        -- Column already exists, do nothing
                    END;
                END $$;
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
    # Ensure headers match the database columns, including 'ConversationID' and 'UserName'
    writer.writerow(['ID', 'Timestamp', 'Prompt', 'Response', 'ConversationID', 'UserName'])
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
        combined_logs = "\n".join(logs)
        # Structuring the system message to include the task for summarization explicitly
        system_message = "You are a highly intelligent assistant. Your task is to summarize the conversation."

        # Preparing the messages for the chat completion API call
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": combined_logs}
        ]
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            if response and 'choices' in response and len(response['choices']) > 0:
                summary_text = response.choices[0].message['content'].strip()
                summaries[uuid] = summary_text  # Store just the summary text here
            else:
                summaries[uuid] = "No summary could be generated for this group."
        except Exception as e:
            summaries[uuid] = "Failed to generate summary due to an error: " + str(e)
    return summaries

def compile_summaries(summaries):
    compiled_output = "Top level summary:\n"
    for idx, (uuid, summary) in enumerate(summaries.items(), start=1):
        compiled_output += f"\nGroup {idx} summary (UUID {uuid}):\n{summary}\n"
    return compiled_output


# Fetch and batch the chat logs by UUID
batches = fetch_and_batch_chatlogs()

# Generate a summary for each group
group_summaries = generate_summary_for_each_group(batches)

# Compile the individual group summaries into a structured format
final_summary_output = compile_summaries(group_summaries)
