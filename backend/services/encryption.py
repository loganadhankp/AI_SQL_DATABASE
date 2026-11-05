"""
Symmetric encryption utility for securing sensitive database credentials at rest.
Uses AES-CBC with HMAC via cryptography.fernet.Fernet.
Derives a safe 32-byte Fernet key from the application's SECRET_KEY.
"""

import base64
import hashlib
from cryptography.fernet import Fernet
from backend.config import get_settings


def _get_fernet() -> Fernet:
    """
    Derives a deterministic 32-byte url-safe base64 key from SECRET_KEY.
    Guarantees compatibility regardless of secret key string length.
    """
    settings = get_settings()
    # Hash SECRET_KEY using SHA-256 to get 32 bytes, then base64 encode for Fernet
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_password(plain_password: str) -> str:
    """
    Encrypts a plain-text database password.
    Returns a secure base64-encoded encrypted token.
    """
    if not plain_password:
        return ""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(plain_password.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypts an encrypted database password token back to plain text.
    Returns plain-text password for in-memory engine connection.
    If the string is already plain text (not a valid Fernet token), falls back safely.
    """
    if not encrypted_password:
        return ""
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(encrypted_password.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception:
        # Fallback if input is already plain text (e.g. testing or raw dev config)
        return encrypted_password
