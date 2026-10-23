from fastapi import Header, HTTPException, Depends
from app.core.config import settings

def admin_api_key(x_admin_api_key: str = Header(None, alias="X-Admin-API-Key")):
    """Validate admin API key for protected endpoints.

    The key is taken from the `X-Admin-API-Key` header and compared against the
    ``ADMIN_API_KEY`` environment variable configured in :pymod:`app.core.config`.
    If the key is missing or does not match, a *401 Unauthorized* error is raised.
    """
    expected = settings.ADMIN_API_KEY
    if not expected:
        # No key configured – treat as misconfiguration rather than allowing access
        raise HTTPException(status_code=500, detail="Admin API key not configured on server")
    if x_admin_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return True
