import time
import logging
import requests
from custom_langchain_model.core.config import settings

logger = logging.getLogger(__name__)

token_data = {
    "access_token": None,
    "expires_at": 0
}


def get_access_token():
    """Fetch a new access token if expired"""
    global token_data
    
    now = time.time()
    
    if token_data["access_token"] and token_data["expires_at"] > now + 10:
        logger.info("Using cached access token")
        return token_data["access_token"]

    resp = requests.post(
        settings.API_OAUTH_URL,
        data={"grant_type": "client_credentials"},
        auth=(settings.API_KEY, settings.API_SECRET),
        timeout=10.0
    )
    resp.raise_for_status()
    data = resp.json()
    
    # Store token and expiration
    token_data["access_token"] = data["access_token"]
    token_data["expires_at"] = now + data.get("expires_in", 3600)
    
    logger.info("Fetched new access token")
    
    return token_data["access_token"]