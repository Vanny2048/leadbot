from __future__ import annotations
from typing import Optional
from .config import settings

try:
    from twilio.rest import Client
except Exception:  # pragma: no cover
    Client = None  # type: ignore


def start_outbound_call(to_phone: str, lead_id: int | None = None) -> Optional[str]:
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_phone_number and settings.public_base_url):
        return "Twilio or PUBLIC_BASE_URL not configured"
    if Client is None:
        return "Twilio SDK not available"
    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        # Webhook to handle call flow
        url = f"{settings.public_base_url}/twilio/voice/outbound"
        client.calls.create(
            to=to_phone,
            from_=settings.twilio_phone_number,
            url=url,
            method="POST",
        )
        return None
    except Exception as e:
        return str(e)