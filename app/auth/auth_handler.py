import os
from jose import jwt
import streamlit as st
from datetime import datetime, timedelta
from app.db.database_connection import connect_to_db

# Try importing resend, fallback to basic error if not available
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

ALLOWED_DOMAINS = [
    'moe.edu.sg', 'moe.gov.sg', 'schools.gov.sg', 'string.sg', 'hci.edu.sg'
]


def is_valid_email_domain(email):
    domain = email.split('@')[-1].lower()
    return domain in ALLOWED_DOMAINS


def generate_magic_link(email):
    jwt_secret = os.environ.get('JWT_SECRET_KEY')
    if not jwt_secret:
        st.error("JWT_SECRET_KEY not found in environment variables")
        return None

    expiration = datetime.utcnow() + timedelta(minutes=5)
    try:
        token = jwt.encode({
            'email': email,
            'exp': expiration
        },
                           jwt_secret,
                           algorithm='HS256')
        base_url = os.environ.get('BASE_URL', 'https://your-repl-url.repl.co')
        return f"{base_url}?verify={token}"
    except Exception as e:
        st.error(f"Error generating magic link: {str(e)}")
        return None


def send_magic_link(email, magic_link):
    try:
        if not RESEND_AVAILABLE:
            st.error(
                "Resend package not installed. Please run 'pip install resend' or contact administrator."
            )
            return False

        api_key = os.environ.get('RESEND_API_KEY')
        from_email = os.environ.get('RESEND_FROM_EMAIL', 'info@string.sg')

        if not api_key:
            st.error("Resend API key not found in environment variables")
            return False

        resend.api_key = api_key
        response = resend.Emails.send({
            "from":
            from_email,
            "to":
            email,
            "subject":
            "Your Login Link",
            "html":
            f'Click <a href="{magic_link}">here</a> to login to CherGPT.'
        })
        return True
    except Exception as e:
        st.error(f"Resend Error: {str(e)}")
        return False


def log_auth_attempt(email, success, ip_address=None, user_agent=None):
    conn = connect_to_db()
    if conn is None:
        return
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO auth_logs (email, success, ip_address, user_agent)
                VALUES (%s, %s, %s, %s)
            """, (email, success, ip_address, user_agent))
    except Exception as e:
        st.error(f"Error logging auth attempt: {str(e)}")
    finally:
        if conn:
            conn.close()


def verify_token(token):
    try:
        payload = jwt.decode(token,
                             os.environ.get('JWT_SECRET_KEY'),
                             algorithms=['HS256'])
        email = payload['email']
        log_auth_attempt(email, True)
        return email
    except:
        if token:  # Only log failed attempts if token was provided
            log_auth_attempt("unknown", False)
        return None
