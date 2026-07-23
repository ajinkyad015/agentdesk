import hashlib
import secrets


def generate_api_key() -> str:
    """
    Generate a secure random API key with prefix 'ad_'.
    """
    return f"ad_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """
    Compute SHA-256 hash of an API key for storage/lookup.
    """
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
