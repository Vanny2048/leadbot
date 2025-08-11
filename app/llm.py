from __future__ import annotations
from typing import Literal, Optional
from .config import settings

try:
    from groq import Groq
except Exception:  # pragma: no cover
    Groq = None  # type: ignore

try:
    import openai
except Exception:  # pragma: no cover
    openai = None  # type: ignore


def generate_response(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
    provider: Literal["groq", "openai"] = settings.llm_provider  # type: ignore

    if provider == "groq":
        if not settings.groq_api_key:
            # Fallback simple rule-based response if no key available
            return _fallback_response(user_prompt)
        client = Groq(api_key=settings.groq_api_key)
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    if provider == "openai":
        if not settings.openai_api_key:
            return _fallback_response(user_prompt)
        openai.api_key = settings.openai_api_key
        resp = openai.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    return _fallback_response(user_prompt)


def _fallback_response(user_prompt: str) -> str:
    # Minimal fallback if no API key set
    if any(k in user_prompt.lower() for k in ["veneer", "invisalign", "whitening", "smile"]):
        return "Thanks for your interest! We can help with cosmetic dentistry, including veneers, whitening, and Invisalign. May I have your name, best phone number, and preferred time for a consultation?"
    return "Thanks for reaching out! May I have your name, phone, and what cosmetic goal you have in mind?"