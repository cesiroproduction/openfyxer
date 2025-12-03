"""Encryption utilities for sensitive data."""

import base64
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


def _get_fernet_key() -> bytes:
    """Derive a Fernet key from the encryption key."""
    # Use PBKDF2 to derive a proper key from the encryption key
    salt = b"openfyxer_salt_v1"  # Fixed salt for consistency
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.ENCRYPTION_KEY.encode()))
    return key


def _get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    return Fernet(_get_fernet_key())


def encrypt_value(value: str) -> str:
    """Encrypt a string value."""
    if not value:
        return ""

    fernet = _get_fernet()
    encrypted = fernet.encrypt(value.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_value(encrypted_value: str) -> Optional[str]:
    """Decrypt an encrypted string value."""
    if not encrypted_value:
        return None

    try:
        fernet = _get_fernet()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception:
        return None


def encrypt_dict_values(data: dict, keys_to_encrypt: list) -> dict:
    """Encrypt specific keys in a dictionary."""
    result = data.copy()
    for key in keys_to_encrypt:
        if key in result and result[key]:
            result[key] = encrypt_value(result[key])
    return result


def decrypt_dict_values(data: dict, keys_to_decrypt: list) -> dict:
    """Decrypt specific keys in a dictionary."""
    result = data.copy()
    for key in keys_to_decrypt:
        if key in result and result[key]:
            result[key] = decrypt_value(result[key])
    return result
