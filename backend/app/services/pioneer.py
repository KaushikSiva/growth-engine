import json
import httpx
from ..config import get_settings
from ..schemas import CEOResponse


SYSTEM_PROMPT = """You are the CEO of ReproClip, an open-source screen recording and automatic demo editing product. Make one bounded growth decision from real supplied metrics. Return one JSON object matching the supplied schema. Never invent payments, conversions, Terac responses, social metrics, or costs. Budget cannot exceed current_terac_budget. Use reasoning_summary for a concise business rationale only; never reveal private chain-of-thought. Prefer before/after workflow demonstrations when evidence supports them. The support CTA is voluntary: 'Support ReproClip — $5'."""


async def run_ceo(state: dict) -> CEOResponse:
    settings = get_settings()
    if not settings.pioneer_api_key:
        raise RuntimeError("PIONEER_API_KEY is not configured. No CEO decision was generated.")
    schema = CEOResponse.model_json_schema()
    payload = {
        "model": settings.pioneer_model,
        "temperature": 0.15,
        "schema": schema,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"response_schema": schema, "business_state": state}, default=str)},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.pioneer_api_key}", "X-API-Key": settings.pioneer_api_key, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(f"{settings.pioneer_base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
    if response.status_code >= 400:
        raise RuntimeError(f"Pioneer CEO unavailable ({response.status_code}): {response.text[:500]}")
    body = response.json()
    content = body.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        raise RuntimeError("Pioneer returned no CEO decision JSON.")
    decision = CEOResponse.model_validate_json(content)
    if decision.budget > settings.terac_budget_usd:
        raise RuntimeError("Pioneer decision exceeded the configured Terac budget and was blocked.")
    return decision
