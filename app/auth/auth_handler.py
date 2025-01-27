
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from jose import jwt
import streamlit as st
from datetime import datetime, timedelta

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
        api_key = os.environ.get('SENDGRID_API_KEY')
        from_email = os.environ.get('SENDGRID_FROM_EMAIL')
        
        # Debug logging
        st.write(f"Sending to: {email}")
        st.write(f"From email: {from_email}")
        st.write(f"Magic link: {magic_link}")
        
        if not api_key:
            st.error("SendGrid API key not found in environment variables")
            return False
        if not from_email:
            st.error("SendGrid from email not found in environment variables")
            return False
            
        sg = SendGridAPIClient(api_key)
        message = Mail(
            from_email=from_email,
            to_emails=email,
            subject='Your Login Link',
            html_content=f'Click <a href="{magic_link}">here</a> to login to CherGPT.'
        )
        response = sg.send(message)
        
        # Detailed logging
        st.write("SendGrid Details:")
        st.write(f"From Email: {from_email}")
        st.write(f"To Email: {email}")
        st.write(f"Status Code: {response.status_code}")
        st.write(f"Response Headers: {response.headers}")
        st.write(f"Response Body: {response.body.decode() if response.body else 'No body'}")
        
        # Log basic sending details without checking verification
        st.write("Email sending attempt completed.")
        st.info("Note: Please ensure the sender email (info@string.sg) is verified in SendGrid to improve delivery.")
            
        return response.status_code == 202
    except Exception as e:
        st.error(f"SendGrid Error: {str(e)}")
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
