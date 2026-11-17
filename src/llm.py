"""LLM interface with caching, model fallback, and robust JSON parsing."""

import json
import re
from typing import Optional, Dict, Any
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL, FALLBACK_MODEL

_LLM_CACHE: Dict[tuple, str] = {}
_client: Optional[Groq] = None


def get_client() -> Groq:
    """Lazily initialize the Groq client."""
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set. Please set it in your .env file or environment variables."
            )
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def clean_json_text(text: str) -> str:
    """Strip markdown code fences and extraneous text from JSON response."""
    text = text.strip()
    # Check for markdown code fences
    fence_pattern = r"^```(?:json)?\s*([\s\S]*?)\s*```$"
    match = re.search(fence_pattern, text, re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    return text


def llm(
    system_instruction: str,
    prompt: str,
    json_mode: bool = False,
    model: Optional[str] = None,
    use_cache: bool = True,
) -> str:
    """Execute a chat completion request via Groq with fallback handling and optional caching."""
    chosen_model = model or GROQ_MODEL
    cache_key = (system_instruction, prompt, json_mode, chosen_model)

    if use_cache and cache_key in _LLM_CACHE:
        return _LLM_CACHE[cache_key]

    client = get_client()
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt},
    ]

    response_format = {"type": "json_object"} if json_mode else None

    # Try primary model first, fallback to secondary model on failure
    models_to_try = [chosen_model]
    if chosen_model != FALLBACK_MODEL:
        models_to_try.append(FALLBACK_MODEL)

    last_error = None
    for m in models_to_try:
        try:
            completion = client.chat.completions.create(
                model=m,
                messages=messages,
                temperature=0.0,
                response_format=response_format,
            )
            output_text = completion.choices[0].message.content or ""
            output_text = output_text.strip()
            if json_mode:
                output_text = clean_json_text(output_text)
            if use_cache:
                _LLM_CACHE[cache_key] = output_text
            return output_text
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Groq API call failed across models {models_to_try}: {last_error}") from last_error


def clear_cache():
    """Clear the LLM memory cache."""
    global _LLM_CACHE
    _LLM_CACHE.clear()
