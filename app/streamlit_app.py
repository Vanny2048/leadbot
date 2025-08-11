import os
import streamlit as st
from typing import Optional
from app.db import init_db, SessionLocal, Lead, Interaction, set_setting, get_setting
from app.config import settings
from app.qualify import qualify_from_text
from app.emailer import send_booking_email
from app.sms import send_sms
from app.telephony import start_outbound_call

st.set_page_config(page_title="Cosmetic Dentistry - Lead Automation", layout="wide")
init_db()

def load_setting(key: str, default: Optional[str] = None) -> str:
    db = SessionLocal()
    try:
        v = get_setting(db, key)
        return v if v is not None else (default or "")
    finally:
        db.close()


def save_setting(key: str, value: str) -> None:
    db = SessionLocal()
    try:
        set_setting(db, key, value)
    finally:
        db.close()


st.title("AI Lead Gen + Outbound Calling (Cosmetic Dentistry)")

tabs = st.tabs(["Leads", "Outbound Calls", "Automations", "Settings"]) 

with tabs[0]:
    st.subheader("Capture Lead")
    with st.form("lead_form"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        source = st.selectbox("Source", ["website", "social", "dm", "manual"]) 
        notes = st.text_area("Notes or message")
        submitted = st.form_submit_button("Save & Qualify")
    if submitted:
        db = SessionLocal()
        try:
            lead = Lead(name=name, phone=phone, email=email, source=source, notes=notes)
            db.add(lead)
            db.commit()
            db.refresh(lead)

            q = qualify_from_text(" ".join([name or "", phone or "", email or "", notes or ""]))
            qualified = q.get("qualified", False)
            services = q.get("extracted", {}).get("services") or []
            lead.status = "qualified" if qualified else "unqualified"
            lead.interested_services = ",".join(services)
            db.add(lead)
            db.add(Interaction(lead_id=lead.id, channel="system", direction="system", content=f"Qualification: {q}"))
            db.commit()

            # Automations
            auto_email = load_setting("auto_email_booking", "false") == "true"
            auto_sms = load_setting("auto_sms_ack", "false") == "true"
            if qualified and auto_email and lead.email:
                err = send_booking_email(lead.name, lead.email, lead.interested_services)
                if err:
                    st.warning(f"Email not sent: {err}")
                else:
                    db.add(Interaction(lead_id=lead.id, channel="email", direction="outbound", content="Booking email sent"))
                    db.commit()
            if auto_sms and lead.phone:
                err = send_sms(lead.phone, "Thanks for reaching out to our Cosmetic Dentistry team. We will follow up shortly.")
                if err:
                    st.warning(f"SMS not sent: {err}")
                else:
                    db.add(Interaction(lead_id=lead.id, channel="sms", direction="outbound", content="Ack SMS sent"))
                    db.commit()

            st.success(f"Lead saved. Qualified: {qualified}")
            st.json(q)
        finally:
            db.close()

    st.divider()
    st.subheader("Leads Table")
    db = SessionLocal()
    try:
        leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
        rows = [
            {
                "id": l.id,
                "created_at": l.created_at.strftime("%Y-%m-%d %H:%M"),
                "name": l.name or "",
                "phone": l.phone or "",
                "email": l.email or "",
                "status": l.status or "",
                "services": l.interested_services or "",
                "source": l.source or "",
            }
            for l in leads
        ]
        if rows:
            headers = list(rows[0].keys())
            header_line = " | ".join(headers)
            separator_line = " | ".join(["---"] * len(headers))
            data_lines = [" | ".join(str(row[h]) for h in headers) for row in rows]
            table_md = "\n".join([header_line, separator_line, *data_lines])
            st.markdown(table_md)
        else:
            st.info("No leads yet.")
    finally:
        db.close()

with tabs[1]:
    st.subheader("Outbound Call")
    st.write("Trigger an AI-led outbound call via Twilio. Requires Twilio + public URL (ngrok) configured in Settings.")
    lead_id = st.number_input("Lead ID", min_value=1, step=1)
    if st.button("Call Lead"):
        db = SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.id == int(lead_id)).first()
            if not lead:
                st.error("Lead not found")
            else:
                err = start_outbound_call(lead.phone, lead_id=lead.id)
                if err:
                    st.error(err)
                else:
                    st.success("Call initiated. Check Twilio console.")
        finally:
            db.close()

with tabs[2]:
    st.subheader("Automations")
    st.write("Configure automatic follow-ups.")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("When lead is qualified, send email with booking link")
        enabled = st.toggle("Enable Booking Email", value=load_setting("auto_email_booking", "false") == "true")
        if st.button("Save Email Automation"):
            save_setting("auto_email_booking", "true" if enabled else "false")
            st.success("Saved")
    with col2:
        st.caption("Send SMS confirmation when lead saved")
        enabled_sms = st.toggle("Enable SMS Acknowledgment", value=load_setting("auto_sms_ack", "false") == "true")
        if st.button("Save SMS Automation"):
            save_setting("auto_sms_ack", "true" if enabled_sms else "false")
            st.success("Saved")

    st.divider()
    st.subheader("Test Automations")
    test_lead_id = st.number_input("Lead ID to act on", min_value=1, step=1, key="test_lead_id")
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        if st.button("Send Booking Email Now"):
            db = SessionLocal()
            try:
                lead = db.query(Lead).filter(Lead.id == int(test_lead_id)).first()
                if not lead or not lead.email:
                    st.error("Lead not found or missing email")
                else:
                    err = send_booking_email(lead.name, lead.email, lead.interested_services)
                    if err:
                        st.error(err)
                    else:
                        st.success("Email sent")
            finally:
                db.close()
    with act_col2:
        if st.button("Send SMS Now"):
            db = SessionLocal()
            try:
                lead = db.query(Lead).filter(Lead.id == int(test_lead_id)).first()
                if not lead or not lead.phone:
                    st.error("Lead not found or missing phone")
                else:
                    err = send_sms(lead.phone, "Thanks for reaching out to our Cosmetic Dentistry team. We will follow up shortly.")
                    if err:
                        st.error(err)
                    else:
                        st.success("SMS sent")
            finally:
                db.close()

with tabs[3]:
    st.subheader("Settings")
    st.caption("Store credentials locally in SQLite; for production, use env vars.")

    with st.expander("LLM Settings", expanded=True):
        provider = st.selectbox("LLM Provider", ["groq", "openai"], index=0 if settings.llm_provider == "groq" else 1)
        groq_key = st.text_input("GROQ_API_KEY", type="password", value=load_setting("GROQ_API_KEY", settings.groq_api_key or ""))
        openai_key = st.text_input("OPENAI_API_KEY", type="password", value=load_setting("OPENAI_API_KEY", settings.openai_api_key or ""))
        model = st.text_input("LLM_MODEL", value=load_setting("LLM_MODEL", settings.llm_model))
        if st.button("Save LLM"):
            save_setting("LLM_PROVIDER", provider)
            save_setting("GROQ_API_KEY", groq_key)
            save_setting("OPENAI_API_KEY", openai_key)
            save_setting("LLM_MODEL", model)
            st.success("Saved LLM settings")

    with st.expander("Email (SMTP)", expanded=True):
        smtp_host = st.text_input("SMTP_HOST", value=load_setting("SMTP_HOST", settings.smtp_host or ""))
        smtp_port = st.number_input("SMTP_PORT", value=int(load_setting("SMTP_PORT", str(settings.smtp_port))), step=1)
        smtp_user = st.text_input("SMTP_USERNAME", value=load_setting("SMTP_USERNAME", settings.smtp_username or ""))
        smtp_pass = st.text_input("SMTP_PASSWORD", type="password", value=load_setting("SMTP_PASSWORD", settings.smtp_password or ""))
        email_from = st.text_input("EMAIL_FROM", value=load_setting("EMAIL_FROM", settings.email_from or ""))
        booking_link = st.text_input("BOOKING_LINK", value=load_setting("BOOKING_LINK", settings.booking_link or ""))
        if st.button("Save Email Settings"):
            save_setting("SMTP_HOST", smtp_host)
            save_setting("SMTP_PORT", str(int(smtp_port)))
            save_setting("SMTP_USERNAME", smtp_user)
            save_setting("SMTP_PASSWORD", smtp_pass)
            save_setting("EMAIL_FROM", email_from)
            save_setting("BOOKING_LINK", booking_link)
            st.success("Saved Email settings")

    with st.expander("Twilio (SMS/Voice)", expanded=True):
        sid = st.text_input("TWILIO_ACCOUNT_SID", value=load_setting("TWILIO_ACCOUNT_SID", settings.twilio_account_sid or ""))
        tok = st.text_input("TWILIO_AUTH_TOKEN", type="password", value=load_setting("TWILIO_AUTH_TOKEN", settings.twilio_auth_token or ""))
        num = st.text_input("TWILIO_PHONE_NUMBER", value=load_setting("TWILIO_PHONE_NUMBER", settings.twilio_phone_number or ""))
        pub = st.text_input("PUBLIC_BASE_URL", value=load_setting("PUBLIC_BASE_URL", settings.public_base_url or ""))
        if st.button("Save Twilio"):
            save_setting("TWILIO_ACCOUNT_SID", sid)
            save_setting("TWILIO_AUTH_TOKEN", tok)
            save_setting("TWILIO_PHONE_NUMBER", num)
            save_setting("PUBLIC_BASE_URL", pub)
            st.success("Saved Twilio settings")

    st.info("Note: Settings saved here are used by the app runtime but do not override environment variables expected by server.py (FastAPI). Set env vars or run server with --env-file.")