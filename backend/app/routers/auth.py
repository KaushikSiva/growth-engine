import hmac
from fastapi import Header, HTTPException
from ..config import get_settings


def require_founder(x_founder_token: str = Header(default="")) -> None:
    expected = get_settings().founder_approval_token
    if not expected:
        raise HTTPException(503, "FOUNDER_APPROVAL_TOKEN is not configured; financial founder actions are disabled.")
    if not hmac.compare_digest(x_founder_token, expected):
        raise HTTPException(403, "Financial Human Approval Required")
