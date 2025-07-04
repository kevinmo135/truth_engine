import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def send_email_report(subject, content, to_address):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_USERNAME")
    msg["To"] = to_address
    msg.set_content(content)

    with smtplib.SMTP_SSL(os.getenv("EMAIL_SMTP_SERVER"), 465) as smtp:
        smtp.login(os.getenv("EMAIL_USERNAME"), os.getenv("EMAIL_PASSWORD"))
        smtp.send_message(msg)
        print("Email sent successfully.")
