import os
import time
import json
import subprocess
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

# Optional: Twilio auto-config
try:
    from twilio.rest import Client as TwilioClient
except Exception:
    TwilioClient = None

# Optional: ngrok tunnel
try:
    from pyngrok import ngrok
except Exception:
    ngrok = None

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(ENV_PATH)

st.set_page_config(page_title="Cosmetic Dental Lead Concierge", layout="wide")

st.title("Cosmetic Dental Lead Concierge")

# Backend controls
with st.sidebar:
    st.header("Backend")
    backend_port = st.number_input("Backend Port", min_value=1024, max_value=65535, value=int(os.getenv("PORT", 3000)))
    base_url = st.text_input("Backend Base URL", value=f"http://localhost:{backend_port}")
    node_running_flag = st.empty()

    def is_backend_up() -> bool:
        try:
            r = requests.get(f"{base_url}/health", timeout=2)
            return r.ok
        except Exception:
            return False

    def start_backend():
        env = os.environ.copy()
        env['PORT'] = str(backend_port)
        # Use node directly; dotenv in server.js loads .env automatically
        subprocess.Popen(["node", "server.js"], cwd=str(BASE_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # wait until up
        for _ in range(30):
            if is_backend_up():
                return True
            time.sleep(0.5)
        return is_backend_up()

    if st.button("Start Backend"):
        ok = start_backend()
        st.toast("Backend started" if ok else "Failed to start backend", icon="✅" if ok else "❌")

    node_running_flag.markdown(f"**Backend status:** {'🟢 Up' if is_backend_up() else '🔴 Down'}")

    st.divider()
    st.header("Public URL (ngrok)")
    tunnel_url = st.text_input("Public Base URL", value=os.getenv("PUBLIC_BASE_URL", ""))

    if ngrok and st.button("Create ngrok tunnel"):
        try:
            # Close previous tunnels
            for t in ngrok.get_tunnels():
                ngrok.disconnect(t.public_url)
        except Exception:
            pass
        try:
            public_url = ngrok.connect(backend_port, "http").public_url
            st.session_state["public_url"] = public_url
            st.success(f"Tunnel: {public_url}")
        except Exception as e:
            st.error(f"ngrok failed: {e}")

    if "public_url" in st.session_state and not tunnel_url:
        tunnel_url = st.session_state["public_url"]

    st.caption("Note: ngrok may require an auth token on some environments.")

    st.divider()
    st.header("Twilio Auto-Config")
    acc_sid = st.text_input("Twilio Account SID", value=os.getenv("TWILIO_ACCOUNT_SID", ""))
    auth_token = st.text_input("Twilio Auth Token", value=os.getenv("TWILIO_AUTH_TOKEN", ""), type="password")
    phone_number = st.text_input("Twilio Phone Number", value=os.getenv("TWILIO_CALLER_ID", ""))

    def configure_twilio_webhooks():
        if not (TwilioClient and acc_sid and auth_token and phone_number and tunnel_url):
            st.error("Missing fields or Twilio client not installed")
            return
        try:
            client = TwilioClient(acc_sid, auth_token)
            numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
            if not numbers:
                st.error("Phone number not found in Twilio account")
                return
            num = numbers[0]
            num.update(
                voice_url=f"{tunnel_url}/twilio/voice/inbound",
                voice_method="POST",
                status_callback=f"{tunnel_url}/twilio/voice/status",
                status_callback_method="POST",
            )
            st.success("Twilio number configured for voice webhooks")
        except Exception as e:
            st.error(f"Twilio config failed: {e}")

    if st.button("Configure Twilio Webhooks"):
        configure_twilio_webhooks()

st.write(":shield: Use this panel to manage and test lead capture, calls, and follow-ups.")

# Tabs
lead_tab, calls_tab, chat_tab, admin_tab = st.tabs(["Submit Lead", "Calls & Webhooks", "Chat", "Admin / Leads"]) 

with lead_tab:
    st.subheader("Submit a Lead")
    with st.form("lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name", "Test Lead")
            email = st.text_input("Email", "lead@example.com")
        with col2:
            phone = st.text_input("Phone (+1…)", "+12135550123")
            interest = st.selectbox("Interest", ["", "veneers", "invisalign", "whitening", "smile makeover"], index=1)
        submitted = st.form_submit_button("Submit & Trigger Outbound Call")
    if submitted:
        try:
            r = requests.post(f"{base_url}/leads", json={
                "fullName": full_name,
                "phoneE164": phone,
                "email": email,
                "interest": interest or None,
                "source": "streamlit",
            }, timeout=10)
            st.write(r.status_code, r.text)
            if r.ok:
                st.success("Lead created. If Twilio is configured, an outbound call is being placed.")
        except Exception as e:
            st.error(f"Failed: {e}")

with calls_tab:
    st.subheader("Simulate Twilio Flows")
    lead_id = st.number_input("Lead ID", min_value=1, value=1)
    colA, colB = st.columns(2)
    with colA:
        if st.button("Fetch Outbound TwiML"):
            try:
                r = requests.post(f"{base_url}/twilio/voice/outbound", params={"leadId": lead_id}, timeout=10)
                st.code(r.text, language="xml")
            except Exception as e:
                st.error(str(e))
        speech = st.text_input("Simulated SpeechResult", "I want veneers")
        if st.button("Post Qualify Webhook"):
            try:
                r = requests.post(f"{base_url}/twilio/voice/qualify", params={"leadId": lead_id}, data={"SpeechResult": speech}, timeout=10)
                st.code(r.text, language="xml")
            except Exception as e:
                st.error(str(e))
    with colB:
        st.caption("Inbound Test TwiML")
        if st.button("Fetch Inbound TwiML"):
            try:
                r = requests.post(f"{base_url}/twilio/voice/inbound", timeout=10)
                st.code(r.text, language="xml")
            except Exception as e:
                st.error(str(e))

with chat_tab:
    st.subheader("Website/Social Chat Test")
    user_message = st.text_input("Message", "Hi, I want a smile makeover")
    if st.button("Send Chat"):
        try:
            r = requests.post(f"{base_url}/chat", json={"message": user_message}, timeout=10)
            if r.ok:
                st.success(r.json().get("reply"))
            else:
                st.error(r.text)
        except Exception as e:
            st.error(str(e))

with admin_tab:
    st.subheader("Leads")
    try:
        r = requests.get(f"{base_url}/leads", timeout=10)
        leads = r.json() if r.ok else []
    except Exception:
        leads = []
    if leads:
        st.dataframe(leads, use_container_width=True)
        lead_select = st.selectbox("Lead Detail", [l['id'] for l in leads])
        if lead_select:
            try:
                detail = requests.get(f"{base_url}/leads/{lead_select}", timeout=10).json()
                st.json(detail)
            except Exception as e:
                st.error(str(e))
    else:
        st.info("No leads yet.")