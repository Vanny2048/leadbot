from __future__ import annotations
from typing import Optional
from .config import settings

try:
    from twilio.rest import Client
except Exception:  # pragma: no cover
    Client = None  # type: ignore


def send_sms(to_phone: str, message: str) -> Optional[str]:
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_phone_number):
        return "Twilio not configured"
    if Client is None:
        return "Twilio SDK not available"
    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(from_=settings.twilio_phone_number, to=to_phone, body=message)
        return None
    except Exception as e:
        return str(e)