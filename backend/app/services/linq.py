import httpx
from ..config import get_settings


async def notify_founder(message: str) -> bool:
    settings = get_settings()
    if not settings.linq_api_key or not settings.linq_from_number or not settings.linq_to_number:
        return False
    payload = {"from": settings.linq_from_number, "to": [settings.linq_to_number], "message": {"parts": [{"type": "text", "value": message[:10000]}]}}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://api.linqapp.com/api/partner/v3/chats", headers={"Authorization": f"Bearer {settings.linq_api_key}"}, json=payload)
    response.raise_for_status()
    return True
