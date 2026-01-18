import requests
import os
import logging
from enum import Enum
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

"""Email service for sending templated emails using Mailgun."""
class Template(Enum):
    LOGIN = "login.html"
    EMAIL_CONFIRMATION = "welcome.html"
    MAX_LOGIN_ATTEMPTS = "notification.html"
    FORGOT_PASSWORD = "forgot_password.html"

"""Subject lines for different email types."""
class Subject(Enum):
    LOGIN= "Login Notification"
    EMAIL_CONFIRMATION = "Please Confirm Your Email Address"
    MAX_LOGIN_ATTEMPTS = "Maximum Login Attempts Reached"
    FORGOT_PASSWORD = "Password Reset Request"
    

MAILGUN_API_KEY = os.getenv("EMAIL_API_KEY")
MAILGUN_DOMAIN = os.getenv("EMAIL_DOMAIN")
MAILGUN_EMAIL_SENDER = os.getenv("EMAIL_SENDER")
auth = ("api", MAILGUN_API_KEY)


def send_email(to_email: str, subject: Subject, template: Template, context: dict[str, str]):
    """Send an email using Mailgun."""
  
    body = read_template(str(template.value), context)
    print("Email body generated.")
    data = {
        "from": MAILGUN_EMAIL_SENDER,
        "to": [to_email],
        "subject": str(subject.value),
        "html": body,

    }
    print("Sending email...")
    response = requests.post(
        MAILGUN_DOMAIN,
        auth=auth,
        data=data
    )
    if response.status_code == 200:
        print(f"Email sent to {to_email} successfully.")
    else:
        logging.error(f"Failed to send email to {to_email}. Status code: {response.status_code}, Response: {response.text}")
        print(f"Failed to send email to {to_email}. Check logs for details.")


def read_template(path: str, context: dict[str,str]) -> str:
    """Read an email template from a file."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(path)
    return template.render(context)


