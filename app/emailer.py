from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional
from jinja2 import Template
from .config import settings

BOOKING_TEMPLATE = Template(
    """
    Hi {{ name or 'there' }},

    Thanks for reaching out about cosmetic dentistry. We'd love to help with {{ services or 'your smile goals' }}.

    You can book a consultation here: {{ booking_link }}

    If you have any questions, just reply to this email.

    Best,
    Cosmetic Dentistry Team
    """
)


def send_email(to_email: str, subject: str, body_text: str, from_name: str = "Cosmetic Dentistry") -> Optional[str]:
    if not (settings.smtp_host and settings.smtp_username and settings.smtp_password and settings.email_from):
        return "SMTP not configured"

    msg = MIMEText(body_text)
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, settings.email_from))
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        return None
    except Exception as e:
        return str(e)


def send_booking_email(name: Optional[str], to_email: str, services: Optional[str]) -> Optional[str]:
    booking_link = settings.booking_link or "https://cal.com/"
    body = BOOKING_TEMPLATE.render(name=name, services=services, booking_link=booking_link)
    return send_email(to_email=to_email, subject="Your Cosmetic Dentistry Consultation", body_text=body)