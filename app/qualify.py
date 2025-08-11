from __future__ import annotations
from typing import Dict, Any
from .llm import generate_response

SYSTEM = (
    "You are a qualification assistant for a cosmetic dentistry practice in Greater Los Angeles. "
    "Decide if a lead is QUALIFIED based on: (1) interest in cosmetic procedures (veneers, whitening, Invisalign, smile makeover), "
    "(2) location within LA core areas (Beverly Hills, West Hollywood, Santa Monica, Pasadena, Glendale, Burbank, Culver City; optionally Malibu/Calabasas), "
    "(3) timeline within 0-90 days, (4) rough budget willingness ($1,000+), (5) intent to book consultation. "
    "Return a compact JSON with fields: qualified (true/false), reasons (string), extracted: {name, phone, email, services (array), timeline, budget}."
)


def qualify_from_text(text: str) -> Dict[str, Any]:
    user = f"Lead message:\n{text}\nFollow the instructions strictly."
    reply = generate_response(SYSTEM, user)

    # Basic robust parse
    import json, re
    json_text = None
    candidates = re.findall(r"\{[\s\S]*\}", reply)
    if candidates:
        for c in candidates:
            try:
                json_text = json.loads(c)
                break
            except Exception:
                continue
    if not json_text:
        # Fallback heuristic
        lowered = text.lower()
        services = [s for s in ["veneers", "invisalign", "whitening", "smile makeover"] if s in lowered]
        qualified = any(s in lowered for s in ["veneers", "invisalign", "whitening", "smile"]) and any(
            loc in lowered for loc in [
                "beverly hills",
                "west hollywood",
                "santa monica",
                "pasadena",
                "glendale",
                "burbank",
                "culver city",
                "malibu",
                "calabasas",
            ]
        )
        json_text = {
            "qualified": bool(qualified),
            "reasons": "Heuristic fallback",
            "extracted": {
                "name": None,
                "phone": None,
                "email": None,
                "services": services,
                "timeline": None,
                "budget": None,
            },
        }
    return json_text