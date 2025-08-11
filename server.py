from __future__ import annotations
from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from typing import Optional
from xml.etree.ElementTree import Element, tostring, SubElement
from app.llm import generate_response

app = FastAPI()


TWILIO_INTRO_SYSTEM = (
    "You are a friendly but efficient phone assistant for a cosmetic dentistry practice in the Greater Los Angeles area. "
    "Goals: identify interest (veneers, whitening, Invisalign, smile makeover), confirm location is within target areas, assess timeframe and budget willingness, and try to book consultation. Keep responses short and conversational."
)


def build_twiml_say_gather(prompt: str) -> str:
    response = Element("Response")
    gather = SubElement(response, "Gather", input="speech", action="/twilio/voice/gather", method="POST", timeout="5")
    say = SubElement(gather, "Say", voice="Polly.Joanna")
    say.text = prompt
    # Fallback say if no input
    SubElement(response, "Say").text = "Sorry, I didn't catch that."
    SubElement(response, "Redirect").text = "/twilio/voice/outbound"
    return tostring(response, encoding="unicode")


@app.post("/twilio/voice/outbound")
async def voice_outbound(request: Request):
    # Initial prompt
    prompt = (
        "Hi, this is the Cosmetic Dentistry team. You recently reached out. "
        "We help with veneers, whitening, Invisalign, and smile makeovers. "
        "What are you interested in and when are you hoping to start?"
    )
    return Response(content=build_twiml_say_gather(prompt), media_type="text/xml")


@app.post("/twilio/voice/gather")
async def voice_gather(
    SpeechResult: Optional[str] = Form(default=None),
    From: Optional[str] = Form(default=None),
    CallSid: Optional[str] = Form(default=None),
):
    user_utterance = SpeechResult or ""
    if not user_utterance:
        return build_twiml_say_gather("Sorry, could you repeat that?")

    reply = generate_response(
        TWILIO_INTRO_SYSTEM,
        f"Caller said: {user_utterance}. Respond briefly and ask the next most useful question to qualify and book.",
        temperature=0.5,
    )
    return Response(content=build_twiml_say_gather(reply), media_type="text/xml")