# Cosmetic Dental Lead Concierge

A minimal AI-powered lead capture and calling assistant for cosmetic dentistry practices (LA area). Includes:
- Lead form endpoint with outbound call attempt
- Twilio voice IVR + qualification
- Email + SMS booking follow-up if qualified
- Simple chat endpoint for site/social automation

## Quickstart

1) Copy env

```
cp .env.example .env
```

2) Fill in Twilio and SMTP details (optional for local).

3) Run

```
npm run dev
```

Open http://localhost:3000 and submit the form.

## Endpoints
- POST /leads
- POST /chat
- POST /twilio/voice/inbound (Twilio webhook)
- POST /twilio/voice/outbound (TwiML for outbound)
- POST /twilio/voice/qualify (TwiML qualification)
- POST /twilio/voice/status

Set your Twilio Voice number webhooks to your PUBLIC_BASE_URL equivalents.

## One-click UI (Streamlit)

```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Use the sidebar to:
- Start backend
- Create an ngrok tunnel (optional)
- Auto-configure your Twilio number

The tabs let you submit leads, simulate Twilio flows, chat, and view leads.