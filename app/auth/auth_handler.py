
import os
from jose import jwt
import streamlit as st
from datetime import datetime, timedelta

# Try importing resend, fallback to basic error if not available
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

ALLOWED_DOMAINS = ['moe.edu.sg', 'moe.gov.sg', 'schools.gov.sg']

def is_valid_email_domain(email):
    domain = email.split('@')[-1].lower()
    return domain in ALLOWED_DOMAINS

def generate_magic_link(email):
    expiration = datetime.utcnow() + timedelta(minutes=15)
    token = jwt.encode(
        {'email': email, 'exp': expiration},
        os.environ.get('JWT_SECRET_KEY'),
        algorithm='HS256'
    )
    base_url = os.environ.get('BASE_URL', 'https://your-repl-url.repl.co')
    return f"{base_url}/verify?token={token}"

def send_magic_link(email, magic_link):
    try:
        if not RESEND_AVAILABLE:
            st.error("Resend package not installed. Please run 'pip install resend' or contact administrator.")
            return False
            
        api_key = os.environ.get('RESEND_API_KEY')
        from_email = os.environ.get('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
        
        # Debug logging
        st.write(f"Sending to: {email}")
        st.write(f"From email: {from_email}")
        st.write(f"Magic link: {magic_link}")
        
        if not api_key:
            st.error("Resend API key not found in environment variables")
            return False
            
        resend.api_key = api_key
        response = resend.Emails.send({
            "from": from_email,
            "to": email,
            "subject": "Your Login Link",
            "html": f'Click <a href="{magic_link}">here</a> to login to CherGPT.'
        })
        
        # Detailed logging
        st.write("Resend Details:")
        st.write(f"From Email: {from_email}")
        st.write(f"To Email: {email}")
        
        # Log basic sending details
        st.write("Email sending attempt completed.")
        return True
    except Exception as e:
        st.error(f"Resend Error: {str(e)}")
        return False

def verify_token(token):
    try:
        payload = jwt.decode(
            token,
            os.environ.get('JWT_SECRET_KEY'),
            algorithms=['HS256']
        )
        return payload['email']
    except:
        return None
