import logging
import random
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
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO instructions (content)
                VALUES (%s)
                ON CONFLICT (id)
                DO UPDATE SET content = EXCLUDED.content;
            """, (new_instructions,))
            conn.commit()
            logging.info("Instructions updated successfully.")
    except Exception as e:
        logging.error(f"Error updating instructions: {e}")
    finally:
        conn.close()


def retrieve_question_by_difficulty(difficulty_level):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return None

    try:
        with conn.cursor() as cur:
            # Query to select questions with the specified difficulty level
            cur.execute("""
                SELECT question_id, content, answer_keywords, difficulty, topic
                FROM questions
                WHERE difficulty = %s
                ORDER BY RANDOM() LIMIT 1;
            """, (difficulty_level,))
            
            question = cur.fetchone()
            if question:
                return {
                    "question_id": question[0],
                    "content": question[1],
                    "answer_keywords": question[2],
                    "difficulty": question[3],
                    "topic": question[4]
                }
            else:
                logging.warning(f"No questions found for difficulty level {difficulty_level}.")
                return None
    except Exception as e:
        logging.error(f"Error retrieving question by difficulty: {e}")
        return None
    finally:
        conn.close()


def log_understanding(student_name, question_id, understanding_level):
    conn = connect_to_db()
    if conn is None:
        logging.error("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO student_logs (student_name, question_id, understanding_level)
                VALUES (%s, %s, %s);
            """, (student_name, question_id, understanding_level))
            conn.commit()
            logging.info(f"Logged understanding level for {student_name} on question {question_id}.")
    except Exception as e:
        logging.error(f"Error logging understanding level: {e}")
    finally:
        conn.close()
