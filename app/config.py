import os
from pydantic import BaseModel


class AppSettings(BaseModel):
    # General
    app_env: str = os.getenv("APP_ENV", "dev")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # LLM
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")  # groq|openai
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    llm_model: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

    # Email (SMTP)
    smtp_host: str | None = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("SMTP_USERNAME")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")
    email_from: str | None = os.getenv("EMAIL_FROM")

    # SMS/Voice (Twilio)
    twilio_account_sid: str | None = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token: str | None = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone_number: str | None = os.getenv("TWILIO_PHONE_NUMBER")
    public_base_url: str | None = os.getenv("PUBLIC_BASE_URL")  # e.g. https://your-ngrok-url.ngrok.io

    # Booking
    booking_link: str | None = os.getenv("BOOKING_LINK")


settings = AppSettings()