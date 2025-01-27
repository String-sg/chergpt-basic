
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
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        message = Mail(
            from_email=os.environ.get('SENDGRID_FROM_EMAIL'),
            to_emails=email,
            subject='Your Login Link',
            html_content=f'Click <a href="{magic_link}">here</a> to login to CherGPT.'
        )
        sg.send(message)
        return True
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
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
