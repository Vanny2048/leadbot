# Cosmetic Dentistry Lead Gen + AI Outbound Calling (Streamlit)

An end-to-end lead capture and follow-up system tailored for Cosmetic Dentistry in Greater Los Angeles. Includes:

- AI qualification using LLM (defaults to Groq free tier)
- Lead capture, storage, and activity log (SQLite)
- Automated booking email and SMS follow-up
- Outbound AI phone assistant via Twilio (webhook served by FastAPI)
- Streamlit dashboard to manage leads and automations

## Live Components

- Streamlit App: lead capture, qualification, follow-ups, and call triggers
- FastAPI Server: Twilio webhook endpoints for voice calls

## Requirements

- Python 3.10+
- Optional but recommended: Accounts/keys
  - Groq API key (free) for LLM: create at `https://console.groq.com/keys`
  - Twilio Account SID/Auth Token and a voice/SMS-enabled number
  - SMTP (Gmail app password or SendGrid/SMTP) for outbound emails
  - Public URL for webhooks (ngrok) if using phone calls

## Quickstart (Local)

1. Clone or open this repo, then install dependencies:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the database and Streamlit UI:

```bash
source .venv/bin/activate || true
streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

3. Optionally, run the FastAPI webhook server (for Twilio Voice):

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

4. If using Twilio, expose your local server with ngrok and set the public base URL:

```bash
# Install ngrok then:
ngrok http 8000
# Copy the https URL and set it as PUBLIC_BASE_URL in the app Settings and in your environment
```

5. Configure credentials inside the Streamlit Settings tab, or export environment variables:

```bash
export GROQ_API_KEY=your_key
export LLM_PROVIDER=groq
export LLM_MODEL=llama-3.1-8b-instant

export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your.email@gmail.com
export SMTP_PASSWORD=your_app_password
export EMAIL_FROM=your.email@gmail.com
export BOOKING_LINK=https://cal.com/your-handle/consultation

export TWILIO_ACCOUNT_SID=ACxxxx
export TWILIO_AUTH_TOKEN=xxxx
export TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
export PUBLIC_BASE_URL=https://your-ngrok-url.ngrok.io
```

6. In Twilio Console, set the Voice webhook URL for your phone number to:

- Voice & Fax -> A Call Comes In: `POST` to `{PUBLIC_BASE_URL}/twilio/voice/outbound`

Or rely on programmatic call initiation from the Streamlit Outbound Calls tab, which calls the same endpoint as the call URL.

## How It Works

- Lead is captured in Streamlit -> LLM classifies qualification and surfaces services of interest.
- If qualified, you can automatically send a booking email (enable in Automations) and/or SMS.
- Outbound call: when triggered, Twilio dials the lead and interacts via the webhook. Twilio converts speech to text, and the LLM generates a concise next response. This repeats until the call ends.

## Free Options and Notes

- LLM: Groq provides a free API tier suitable for development. Alternatively, plug in OpenAI if preferred.
- Email: You can use Gmail SMTP with an App Password (free) or SendGrid's free tier.
- SMS/Voice: Telephony requires a paid provider (Twilio/Plivo/Vonage). There is no truly free PSTN calling. The app works without telephony, but call features will be disabled.
- Booking: Use any external booking link (Cal.com/Calendly). Enter it in Settings; the email template uses it.

## Customization for Cosmetic Dentistry

- Targeted geographies and service keywords tailored to Greater Los Angeles and cosmetic procedures.
- Qualification logic considers services, budget intent, and timeline.

## Run Both Servers Together

Two terminals:

- Terminal A:

```bash
source .venv/bin/activate || true
streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

- Terminal B:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

## Project Structure

- `app/config.py`: loads configuration
- `app/db.py`: SQLite models and helpers
- `app/llm.py`: LLM wrapper (Groq/OpenAI)
- `app/qualify.py`: qualification logic
- `app/emailer.py`: SMTP email sender and booking email
- `app/sms.py`: Twilio SMS sender
- `app/telephony.py`: Twilio call start helper
- `server.py`: FastAPI Twilio webhook for voice calls
- `app/streamlit_app.py`: Streamlit UI

## Deleting Unnecessary Files

This repo is minimal and only includes required files. Add integration keys via environment variables or the Settings tab; secrets are not committed.

## Security

- Use environment variables in production.
- Avoid committing secrets.

## Troubleshooting

- If LLM responses are empty: verify `GROQ_API_KEY` or `OPENAI_API_KEY`.
- If emails fail: confirm SMTP host/port and app password; try less-secure app settings or SendGrid.
- If SMS/Calls fail: verify Twilio credentials, phone number formatting, and that your `PUBLIC_BASE_URL` is reachable.
- For webhook logs: check `uvicorn` console output and Twilio debugger.